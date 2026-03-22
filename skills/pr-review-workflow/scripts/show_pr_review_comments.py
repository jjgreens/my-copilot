#!/usr/bin/env -S python3 -u
"""
Show active (not outdated, not resolved) GitHub PR review threads.

Usage:
  show_pr_review_comments.py <owner/repo> <pr_number>
  show_pr_review_comments.py intel-innersource/my-repo 42

Requires GH_TOKEN or GITHUB_TOKEN env var, or a valid `gh auth` session.
"""
import json, os, sys, urllib.request, urllib.error

def usage():
    print(__doc__)
    sys.exit(1)

if len(sys.argv) != 3:
    usage()

repo   = sys.argv[1]   # e.g. intel-innersource/my-repo
pr_num = sys.argv[2]   # e.g. 42

if "/" not in repo:
    print(f"Invalid repo format: {repo!r} — expected owner/repo")
    usage()

try:
    int(pr_num)
except ValueError:
    print(f"Invalid PR number: {pr_num!r} — expected an integer.")
    usage()

token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not token:
    import subprocess
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        token = result.stdout.strip() if result.returncode == 0 else None
    except FileNotFoundError:
        print("Error: gh CLI not found and no GH_TOKEN/GITHUB_TOKEN set.")
        sys.exit(1)
if not token:
    print("Error: no authentication token available — set GH_TOKEN/GITHUB_TOKEN or run 'gh auth login'.")
    sys.exit(1)

headers = {"Accept": "application/vnd.github+json", "Authorization": f"token {token}"}

# GraphQL query — returns all threads with pagination
QUERY = """
query($owner: String!, $repo: String!, $pr: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          isResolved
          isOutdated
          comments(first: 1) {
            nodes {
              path
              line
              originalCommit { abbreviatedOid }
              body
              author { login }
              createdAt
            }
          }
        }
      }
    }
  }
}
"""

owner, name = repo.split("/", 1)
threads = []
after = None

while True:
    payload = json.dumps({
        "query": QUERY,
        "variables": {"owner": owner, "repo": name, "pr": int(pr_num), "after": after}
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={**headers, "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}")
        sys.exit(1)

    if data.get("errors"):
        print(f"GraphQL errors: {data['errors']}")
        sys.exit(1)
    pr = (data.get("data") or {}).get("repository", {}).get("pullRequest")
    if pr is None:
        print(f"PR not found: {repo}#{pr_num}")
        sys.exit(1)
    nodes = pr["reviewThreads"]
    threads.extend(nodes["nodes"])
    pi = nodes["pageInfo"]
    if not pi["hasNextPage"]:
        break
    after = pi["endCursor"]

active            = [(i+1, t) for i, t in enumerate(threads) if not t["isOutdated"] and not t["isResolved"]]
outdated_unresolved = [(i+1, t) for i, t in enumerate(threads) if t["isOutdated"] and not t["isResolved"]]
outdated          = sum(1 for t in threads if t["isOutdated"])
resolved          = sum(1 for t in threads if t["isResolved"])

print(f"PR {repo}#{pr_num} — {len(threads)} threads total")
print(f"  Active: {len(active)}  Outdated: {outdated}  Resolved: {resolved}")
if outdated_unresolved:
    print(f"  ⚠️  Outdated but unresolved: {len(outdated_unresolved)} — these show as open in the web UI. Run: pr_thread.py {repo} {pr_num} fix <N...> \"<message>\"")
print()

for num, t in active:
    comment_nodes = t["comments"]["nodes"]
    if not comment_nodes:
        print(f"[{num}] (empty thread — no comments)")
        print()
        continue
    c = comment_nodes[0]
    sha  = (c.get("originalCommit") or {}).get("abbreviatedOid", "?")
    path = c.get("path", "")
    line = c.get("line") or ""
    author = (c.get("author") or {}).get("login", "?")
    body = c["body"][:300].replace("\n", " ")
    print(f"[{num}] {path}:{line}  (sha:{sha} by {author})")
    print(f"     {body}")
    print()

if not active:
    print("✅ No active review comments.")
