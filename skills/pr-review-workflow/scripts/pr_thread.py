#!/usr/bin/env python3
"""
Act on GitHub PR review threads by their display number.

Thread numbers match the [N] output from show_pr_review_comments.py.

Usage:
  pr_thread.py <owner/repo> <pr> resolve <N> [<N> ...]
  pr_thread.py <owner/repo> <pr> reply   <N> "message"
  pr_thread.py <owner/repo> <pr> defer   <N> ["optional context"]
  pr_thread.py <owner/repo> <pr> fixed   <N> "Fixed in <sha>: <description>"
  pr_thread.py <owner/repo> <pr> list-deferred

Actions:
  resolve       Mark thread(s) resolved (code was fixed).
  reply         Reply to a thread (leaves it open).
  defer         Reply with "[DEFERRED] <context>", then resolve.
                Use this for items to revisit before merge.
  fixed         Reply with "[FIXED] <message>" to a previously-deferred thread.
                list-deferred will no longer show it. Thread stays resolved.
  list-deferred List deferred threads that have not yet been marked [FIXED].
                Run before merge to review and selectively create issues.

Examples:
  pr_thread.py intel-innersource/my-repo 1 resolve 26 27 36
  pr_thread.py intel-innersource/my-repo 1 reply 68 "Intentional — re-enabled before merge."
  pr_thread.py intel-innersource/my-repo 1 defer 77 "Tag cleanup — review before merge."
  pr_thread.py intel-innersource/my-repo 1 fixed 77 "Fixed in abc1234: added GHCR retention policy."
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
pr_num = int(sys.argv[2])
action = sys.argv[3]

if action not in ("resolve", "reply", "defer", "fixed", "list-deferred"):
    print(f"Unknown action: {action!r}.")
    usage()

if action == "resolve" and len(sys.argv) < 5:
    print("resolve requires at least one thread number.")
    usage()
if action == "reply" and len(sys.argv) != 6:
    print("reply requires exactly one thread number and a message.")
    usage()
if action == "defer" and len(sys.argv) < 5:
    print("defer requires at least one thread number.")
    usage()
if action == "fixed" and len(sys.argv) != 6:
    print("fixed requires exactly one thread number and a message.")
    usage()

token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not token:
    result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    token = result.stdout.strip() if result.returncode == 0 else None

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

# Fetch all threads with all comments (for list-deferred we need last comment)
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
          comments(last: 10) {
            nodes { path line body author { login } url }
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
    nodes = data["data"]["repository"]["pullRequest"]["reviewThreads"]
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

def do_resolve(num, thread):
    node_id = thread["id"]
    c = thread["comments"]["nodes"][0] if thread["comments"]["nodes"] else {}
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
    c = thread["comments"]["nodes"][0] if thread["comments"]["nodes"] else {}
    path = c.get("path", "?")
    preview = (c.get("body") or "")[:60]
    result = graphql(REPLY_MUTATION, {"threadId": node_id, "body": body})
    if result.get("data", {}).get("addPullRequestReviewThreadReply"):
        print(f"[{num}] ✅ Replied — {path}: {preview}")
    else:
        print(f"[{num}] ❌ Failed — {result.get('errors', [])}")

if action == "resolve":
    for num in [int(x) for x in sys.argv[4:]]:
        thread = numbered.get(num)
        if not thread:
            print(f"[{num}] Thread not found (max: {max(numbered)})")
            continue
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

elif action == "fixed":
    num = int(sys.argv[4])
    thread = numbered.get(num)
    if not thread:
        print(f"[{num}] Thread not found (max: {max(numbered)})")
        sys.exit(1)
    body = f"[FIXED] {sys.argv[5]}"
    do_reply(num, thread, body)

elif action == "list-deferred":
    found = []
    for i, t in enumerate(all_threads):
        comments = t["comments"]["nodes"]
        if not comments:
            continue
        # Find last reply that starts with [DEFERRED]; skip if a [FIXED] reply follows it
        deferred_replies = [c for c in comments if (c.get("body") or "").startswith("[DEFERRED]")]
        if deferred_replies:
            last_deferred = deferred_replies[-1]
            last_deferred_idx = comments.index(last_deferred)
            subsequent = comments[last_deferred_idx + 1:]
            already_fixed = any((c.get("body") or "").startswith("[FIXED]") for c in subsequent)
            if already_fixed:
                continue
            first = comments[0]
            found.append((i + 1, t, first, last_deferred))

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
