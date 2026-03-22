---
description: 'Git workflow rules that apply to all git operations and GitHub API usage.'
applyTo: '**'
---

# Git Workflow

- **Always work through a local clone.** Do not use the GitHub API (`push_files`, `create_or_update_file`, etc.) to commit directly to a remote. Make edits locally, commit with `git commit`, and push with `git push`.
- **Never use `git push --force` or `git push --force-with-lease`.** If a branch needs to be replaced (e.g., rebased or recreated from a clean base), rename the stale remote branch first to archive it (`git fetch origin && git push origin origin/<old>:refs/heads/<old>-stale`), delete the original remote name (`git push origin --delete <old>`), then push the clean local branch normally.
- **Always start a new branch from an up-to-date `main`:** `git checkout main && git pull`, then `git checkout -b <branch-name>`.

## Branch and PR Policy

**Never push directly to `main`.** All changes must go through a PR:

```bash
git checkout main && git pull
git checkout -b <branch-name>
# make changes, commit, push
gh pr create
```

## PR Review Cycle Order

When driving a PR through the Copilot review cycle using the `pr-review-workflow` skill, the correct order within each round is:

1. **Fix** source issues identified in the review
2. **Run** any required build/generation steps (e.g. `npm run build`)
3. **Commit and push** all changes together
4. **Request** Copilot review (only after the fix is live on the branch)
5. **Resolve** threads from the previous round
6. **Monitor** CI + review

> Never request a review before pushing the fix — Copilot will review the unfixed code.

## Pre-Merge Checklist

Before merging, complete the pre-merge checklist from the `pr-review-workflow` skill, then update `CHANGELOG.md` with a brief summary of the changes (title, PR number, key changes) as a final commit in the PR.

## Merge Process

**During squash merge:** Write a concise commit body summarizing the key changes.

**After squash merge:** `git checkout main && git pull`, then start the next branch from this updated `main`.
