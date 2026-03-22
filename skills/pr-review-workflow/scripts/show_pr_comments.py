#!/usr/bin/env python3
"""
show_pr_comments.py <owner/repo> <pr>

Lists ALL general PR comments (bot and human) from the PR Conversation tab.
These are distinct from inline code review threads (show_pr_review_comments.py).

GitHub PRs have two comment surfaces:
  1. Review threads — inline code comments from a formal review submission
  2. PR comments    — general discussion on the PR timeline (this script)

Both must be checked each round. Bot tool summaries (MegaLinter, GHAS,
Dependabot, etc.) and human reviewer comments left outside a formal review
all appear here and would be missed by show_pr_review_comments.py alone.

Exit codes:
  0 — completed (comments may or may not be present)
  1 — usage / runtime error
"""

import json
import shutil
import subprocess
import sys


def gh(*args):
    if not shutil.which("gh"):
        print(
            "Error: 'gh' CLI is required but not found. "
            "Install it from https://cli.github.com/",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        result = subprocess.run(
            ["gh", "api", "--paginate"] + list(args),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: gh API call failed:\n{e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    pages = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            pages.append(json.loads(line))
    if len(pages) == 1:
        return pages[0]
    merged = []
    for page in pages:
        if isinstance(page, list):
            merged.extend(page)
        elif isinstance(page, dict):
            for v in page.values():
                if isinstance(v, list):
                    merged.extend(v)
    return merged


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <owner/repo> <pr>", file=sys.stderr)
        sys.exit(1)

    repo = sys.argv[1]
    pr_num = sys.argv[2]

    comments = gh(f"repos/{repo}/issues/{pr_num}/comments?per_page=100")
    if not isinstance(comments, list):
        comments = []

    if not comments:
        print("✅ No PR issue comments found.")
        return

    print(f"ℹ️  {len(comments)} PR issue comment(s) on PR #{pr_num}:\n")
    for c in comments:
        login = c.get("user", {}).get("login", "unknown")
        user_type = c.get("user", {}).get("type", "User")
        label = f"[BOT] @{login}" if user_type == "Bot" else f"@{login}"
        created = c.get("created_at", "")[:10]
        url = c.get("html_url", "")
        body_preview = (c.get("body") or "").replace("\n", " ").strip()[:400]
        print(f"  [{created}] {label}  {url}")
        print(f"  {body_preview}")
        print()


if __name__ == "__main__":
    main()
