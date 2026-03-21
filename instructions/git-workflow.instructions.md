---
description: 'Git workflow rules that apply to all git operations and GitHub API usage.'
applyTo: '**'
---

# Git Workflow

- **Always work through a local clone.** Do not use the GitHub API (`push_files`, `create_or_update_file`, etc.) to commit directly to a remote. Make edits locally, commit with `git commit`, and push with `git push`.
- **Never use `git push --force` or `git push --force-with-lease`.** If a push is rejected due to diverged history, recreate a clean branch: fetch origin, create a new branch from the updated upstream base, cherry-pick your commits, delete the old branch, rename the new one, then push.
- **Always pull before starting new work.** Run `git fetch` and `git pull` before creating a new branch or beginning changes.
