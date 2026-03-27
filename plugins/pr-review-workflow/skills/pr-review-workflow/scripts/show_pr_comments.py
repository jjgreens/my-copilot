#!/usr/bin/env python3
"""
show_pr_comments.py <owner/repo> <pr>

Lists PR issue comments (general discussion, not formal review submissions)
from the PR Conversation tab.

GitHub PRs have three comment surfaces:
  1. Review threads — inline code comments attached to specific lines
  2. Review submission bodies — top-level text submitted with a formal review
  3. PR issue comments — general Conversation-tab discussion (this script)

This script covers surface 3 only. Use show_pr_review_comments.py for
surfaces 1 and 2. All surfaces must be checked each round.

Bot tool summaries (MegaLinter, GHAS, Dependabot, etc.) and human
reviewer comments left outside a formal review all appear here.

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
            ["gh", "api", "--paginate", "--slurp"] + list(args),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: gh API call failed:\n{e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    # --slurp wraps all pages into a single JSON array; unwrap single-page results
    pages = json.loads(result.stdout)
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
        body = (c.get("body") or "").rstrip()
        print(f"  [{created}] {label}  {url}")
        print()
        for line in body.splitlines():
            print(f"  {line}")
        print()


if __name__ == "__main__":
    main()
