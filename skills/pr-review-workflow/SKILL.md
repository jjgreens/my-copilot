---
name: pr-review-workflow
description: 'Drive a GitHub PR through the Copilot review cycle to merge-ready: identify all issues, fix in one batch, commit, request review, resolve threads, and monitor CI. Use when working a PR toward merge readiness.'
---

# pr-review-workflow

Drive a GitHub pull request through the Copilot review cycle to merge-ready state.

## When to Use This Skill

Use this skill when:
- Starting a new Copilot review round on a PR
- Working a PR to merge-ready state
- Keywords: pr review, copilot review, merge ready, review cycle, resolve threads

## Tools

Scripts live in `scripts/` and require `gh` CLI and Python 3.

| Script | Purpose |
|--------|---------|
| `scripts/monitor_ci_pr.sh <owner/repo> <pr>` | Poll CI runs + Copilot review; exit when all done |
| `scripts/show_pr_review_comments.py <owner/repo> <pr>` | List **all** active review threads with numbers (full GraphQL pagination) |
| `scripts/pr_thread.py <owner/repo> <pr> resolve <N...>` | Resolve threads by number |
| `scripts/pr_thread.py <owner/repo> <pr> reply <N> "msg"` | Reply to a thread by number |
| `scripts/pr_thread.py <owner/repo> <pr> defer <N> ["context"]` | Defer a thread with context, then resolve |
| `scripts/pr_thread.py <owner/repo> <pr> fixed <N> "msg"` | Mark a deferred thread as fixed |
| `scripts/pr_thread.py <owner/repo> <pr> list-deferred` | List deferred threads not yet marked fixed |

## Workflow

Follow this order **exactly** for each review round:

### Step 1: Identify ALL Issues

Run **both** before touching any code:

```bash
scripts/show_pr_review_comments.py <owner/repo> <pr>
```

Check CI failures in parallel. Do **not** start fixing until you have the full picture.

### Step 2: Fix ALL Issues in One Batch

Address every actionable thread AND every CI failure together. Do not commit partial fixes.

### Step 3: Single Commit and Push

One commit per review round.

### Step 4: Request a New Copilot Review

Use `request_copilot_review` tool.

### Step 5: Resolve All Open Threads

For every active thread from the completed review round, take **exactly one** action:

**Fixed in code → resolve:**
```bash
scripts/pr_thread.py <owner/repo> <pr> resolve 26 27 36
```

**Deferred or accepted as-is → reply explaining the decision, leave open:**
```bash
scripts/pr_thread.py <owner/repo> <pr> reply 68 "Intentional — re-enable before merge."
```

**Deferred for pre-merge review → defer (replies + resolves):**
```bash
scripts/pr_thread.py <owner/repo> <pr> defer 77 "Tag cleanup — review before merge."
```

**Never resolve a thread without either fixing the code or leaving an explanatory reply.**

### Step 6: Monitor CI + New Review

```bash
scripts/monitor_ci_pr.sh <owner/repo> <pr>
```

Exits when all CI checks reach a terminal state AND the Copilot review for the current HEAD commit is submitted.

## Pre-Merge Checklist

Before merging, check for deferred items:

```bash
scripts/pr_thread.py <owner/repo> <pr> list-deferred
```

For each deferred item: either fix and mark `[FIXED]`, or create a follow-up issue.
