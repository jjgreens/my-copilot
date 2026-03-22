---
name: pr-review-workflow
description: 'Drive a GitHub PR through the Copilot review cycle to merge-ready: request review, resolve threads, monitor CI, identify and fix issues, repeat until clean.'
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
| `scripts/pr_thread.py <owner/repo> <pr> fix <N...> "msg"` | Reply with message + resolve (auto-prefixes [FIXED] if previously deferred) |
| `scripts/pr_thread.py <owner/repo> <pr> reply <N> "msg"` | Reply asking for clarification, leaves thread open |
| `scripts/pr_thread.py <owner/repo> <pr> defer <N> ["context"]` | Reply with [DEFERRED] context + resolve; shows in list-deferred |
| `scripts/pr_thread.py <owner/repo> <pr> list-deferred` | List deferred threads not yet marked [FIXED] |

## Workflow

Repeat this loop until the Copilot review comes back clean with no issues:

### Step 1: Request Copilot Review

Use the `request_copilot_review` tool.

### Step 2: Resolve Open Threads

For every active thread from the previous review round, take **exactly one** action.
On the first pass there are no threads — skip to Step 3.

**Fixed in code → fix (reply + resolve):**
```bash
scripts/pr_thread.py <owner/repo> <pr> fix 26 27 36 "Fixed in <sha>: <description>."
```

**Must revisit before merge → defer (reply [DEFERRED] + resolve):**
```bash
scripts/pr_thread.py <owner/repo> <pr> defer 77 "Tag cleanup — review before merge."
```

**Need clarification from reviewer → reply (leaves thread open):**
```bash
scripts/pr_thread.py <owner/repo> <pr> reply 31 "Can you clarify expected behavior when X is nil?"
```

**Never resolve a thread without either fixing the code or leaving an explanatory reply.**

### Step 3: Monitor CI + Review

```bash
scripts/monitor_ci_pr.sh <owner/repo> <pr>
```

Exits when all CI checks reach a terminal state AND the Copilot review for the current HEAD commit is submitted.

### Step 4: Identify Remaining Issues

```bash
scripts/show_pr_review_comments.py <owner/repo> <pr>
```

Also check CI failures. If there are **no issues** → **done, PR is merge-ready.** Break the loop.

### Step 5: Fix ALL Issues in One Batch

Address every actionable thread AND every CI failure together. Do not commit partial fixes.

If the repo has a required pre-commit build or generation step (e.g. `npm run build`,
`npm run generate`), run it now so generated artifacts stay in sync with source changes.

### Step 6: Single Commit and Push

One commit per review round (include any generated artifacts). Then repeat from Step 1.

> ⚠️ **Order matters**: always push the fix commit *before* requesting the next review.
> Requesting review before committing means Copilot reviews the unfixed code.

## Pre-Merge Checklist

Before merging, check for deferred items:

```bash
scripts/pr_thread.py <owner/repo> <pr> list-deferred
```

For each deferred item: either fix and mark `[FIXED]`, or create a follow-up issue.
