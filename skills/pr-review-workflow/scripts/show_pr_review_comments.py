#!/usr/bin/env python3
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

token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not token:
    # Try gh CLI token
    import subprocess
    result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    token = result.stdout.strip() if result.returncode == 0 else None

headers = {"Accept": "application/vnd.github+json"}
if token:
    headers["Authorization"] = f"token {token}"

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
          isCollapsed
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
        with urllib.request.urlopen(req) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)

    nodes = data["data"]["repository"]["pullRequest"]["reviewThreads"]
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
    print(f"  ⚠️  Outdated but unresolved: {len(outdated_unresolved)} — these show as open in the web UI. Run: pr_thread.py {repo} {pr_num} resolve <N...>")
print()

for num, t in active:
    c = t["comments"]["nodes"][0]
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
