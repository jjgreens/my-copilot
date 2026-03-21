#!/usr/bin/env python3
"""
Act on GitHub PR review threads by their display number.

Thread numbers match the [N] output from show_pr_review_comments.py.

Usage:
  pr_thread.py <owner/repo> <pr> fix    <N> [<N> ...] "Fixed in <sha>: <description>"
  pr_thread.py <owner/repo> <pr> reply  <N> "question or clarification request"
  pr_thread.py <owner/repo> <pr> defer  <N> ["context"]
  pr_thread.py <owner/repo> <pr> list-deferred

Works on all review threads regardless of reviewer (Copilot or human).

Actions:
  fix           Reply with the provided message then resolve. Use for any thread
                where the code was addressed. Never resolve silently.
                If the thread was previously deferred, auto-prefixes message with
                [FIXED] so list-deferred no longer shows it.
                Accepts multiple thread numbers; all get the same message.
  reply         Reply to request more information or seek clarification from the
                reviewer. Leaves the thread open. Use when you need input before
                you can act (works for both Copilot and human reviews).
  defer         Reply with "[DEFERRED] <context>", then resolve.
                Use for anything that must be revisited before merge
                (e.g. "re-enable X before merge", "follow-up issue needed").
  list-deferred List deferred threads that have not yet been marked [FIXED].
                Run before merge to review and selectively create issues.

Examples:
  pr_thread.py intel-innersource/my-repo 1 fix 26 27 28 "Fixed in abc1234: added error handling."
  pr_thread.py intel-innersource/my-repo 1 reply 31 "Can you clarify expected behavior when X is nil?"
  pr_thread.py intel-innersource/my-repo 1 defer 77 "Tag cleanup — review before merge."
  pr_thread.py intel-innersource/my-repo 1 list-deferred

Requires GH_TOKEN, GITHUB_TOKEN, or a valid `gh auth` session.
"""
import json, os, sys, urllib.request, urllib.error, subprocess

def usage():
    print(__doc__)
    sys.exit(1)

if len(sys.argv) < 4:
    usage()

repo   = sys.argv[1]
try:
    pr_num = int(sys.argv[2])
except ValueError:
    print(f"Invalid PR number: {sys.argv[2]!r} — expected an integer.")
    usage()
action = sys.argv[3]

if action not in ("fix", "reply", "defer", "list-deferred"):
    print(f"Unknown action: {action!r}.")
    usage()

if action == "fix" and len(sys.argv) < 6:
    print("fix requires at least one thread number and a message.")
    usage()
if action == "reply" and len(sys.argv) != 6:
    print("reply requires exactly one thread number and a message.")
    usage()
if action == "defer" and len(sys.argv) < 5:
    print("defer requires exactly one thread number.")
    usage()
if action == "defer" and len(sys.argv) > 6:
    print("defer takes one thread number and an optional context string — did you mean to quote the context?")
    usage()

token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not token:
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        token = result.stdout.strip() if result.returncode == 0 else None
    except FileNotFoundError:
        print("Error: gh CLI not found and no GH_TOKEN/GITHUB_TOKEN set.")
        sys.exit(1)

headers = {
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
}
if token:
    headers["Authorization"] = f"token {token}"

def graphql(query, variables):
    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)

# Fetch all threads.
# originalComment(first:1): the thread's first comment (path, line, issue text).
# recentComments(last:100): recent replies for DEFERRED/FIXED detection.
LIST_QUERY = """
query($owner: String!, $repo: String!, $pr: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          originalComment: comments(first: 1) {
            nodes { path line body author { login } url }
          }
          recentComments: comments(last: 100) {
            nodes { body author { login } }
          }
        }
      }
    }
  }
}
"""

owner, name = repo.split("/", 1)
all_threads = []
after = None

while True:
    data = graphql(LIST_QUERY, {"owner": owner, "repo": name, "pr": pr_num, "after": after})
    if data.get("errors"):
        print(f"GraphQL errors: {data['errors']}")
        sys.exit(1)
    pr = (data.get("data") or {}).get("repository", {}).get("pullRequest")
    if pr is None:
        print(f"PR not found: {repo}#{pr_num}")
        sys.exit(1)
    nodes = pr["reviewThreads"]
    all_threads.extend(nodes["nodes"])
    if not nodes["pageInfo"]["hasNextPage"]:
        break
    after = nodes["pageInfo"]["endCursor"]

numbered = {i + 1: t for i, t in enumerate(all_threads)}

RESOLVE_MUTATION = """
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { id isResolved }
  }
}
"""

REPLY_MUTATION = """
mutation($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $threadId, body: $body}) {
    comment { id }
  }
}
"""

def _is_deferred(thread):
    """Return True if thread has a [DEFERRED] comment with no subsequent [FIXED]."""
    recent = thread["recentComments"]["nodes"]
    deferred = [c for c in recent if (c.get("body") or "").startswith("[DEFERRED]")]
    if not deferred:
        return False
    last_idx = recent.index(deferred[-1])
    return not any((c.get("body") or "").startswith("[FIXED]") for c in recent[last_idx + 1:])

def do_resolve(num, thread):
    node_id = thread["id"]
    c = thread["originalComment"]["nodes"][0] if thread["originalComment"]["nodes"] else {}
    path = c.get("path", "?")
    preview = (c.get("body") or "")[:60]
    if thread["isResolved"]:
        print(f"[{num}] Already resolved — {path}: {preview}")
        return
    result = graphql(RESOLVE_MUTATION, {"threadId": node_id})
    if result.get("data", {}).get("resolveReviewThread"):
        print(f"[{num}] ✅ Resolved — {path}: {preview}")
    else:
        print(f"[{num}] ❌ Failed — {result.get('errors', [])}")

def do_reply(num, thread, body):
    node_id = thread["id"]
    c = thread["originalComment"]["nodes"][0] if thread["originalComment"]["nodes"] else {}
    path = c.get("path", "?")
    preview = (c.get("body") or "")[:60]
    result = graphql(REPLY_MUTATION, {"threadId": node_id, "body": body})
    if result.get("data", {}).get("addPullRequestReviewThreadReply"):
        print(f"[{num}] ✅ Replied — {path}: {preview}")
    else:
        print(f"[{num}] ❌ Failed — {result.get('errors', [])}")

if action == "fix":
    # Last arg is the message; all preceding args after action are thread numbers
    message = sys.argv[-1]
    nums = [int(x) for x in sys.argv[4:-1]]
    if not nums:
        print("fix requires at least one thread number before the message.")
        usage()
    for num in nums:
        thread = numbered.get(num)
        if not thread:
            print(f"[{num}] Thread not found (max: {max(numbered)})")
            continue
        body = f"[FIXED] {message}" if _is_deferred(thread) else message
        do_reply(num, thread, body)
        do_resolve(num, thread)

elif action == "reply":
    num = int(sys.argv[4])
    thread = numbered.get(num)
    if not thread:
        print(f"[{num}] Thread not found (max: {max(numbered)})")
        sys.exit(1)
    do_reply(num, thread, sys.argv[5])

elif action == "defer":
    num = int(sys.argv[4])
    context = sys.argv[5] if len(sys.argv) > 5 else ""
    thread = numbered.get(num)
    if not thread:
        print(f"[{num}] Thread not found (max: {max(numbered)})")
        sys.exit(1)
    body = f"[DEFERRED] {context}".strip()
    do_reply(num, thread, body)
    do_resolve(num, thread)

elif action == "list-deferred":
    found = []
    for i, t in enumerate(all_threads):
        if _is_deferred(t):
            original = t["originalComment"]["nodes"]
            first = original[0] if original else {}
            recent = t["recentComments"]["nodes"]
            deferred_replies = [c for c in recent if (c.get("body") or "").startswith("[DEFERRED]")]
            found.append((i + 1, t, first, deferred_replies[-1]))

    if not found:
        print("No deferred threads found.")
    else:
        print(f"Deferred threads ({len(found)}) — review before merge:\n")
        for num, t, first, deferred in found:
            path = first.get("path", "?")
            line = first.get("line") or ""
            issue_text = (first.get("body") or "")[:120]
            context = (deferred.get("body") or "")[len("[DEFERRED]"):].strip()
            status = "resolved" if t["isResolved"] else "OPEN"
            print(f"[{num}] {path}:{line} ({status})")
            print(f"  Issue: {issue_text}")
            if context:
                print(f"  Context: {context}")
            print()
