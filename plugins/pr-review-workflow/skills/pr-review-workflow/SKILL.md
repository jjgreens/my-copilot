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

Scripts live in `.github/skills/pr-review-workflow/scripts/` and require `gh` CLI, `jq`, and Python 3.
All commands below assume the repo root as the working directory.
**These paths assume the skill is installed to `.github/skills/pr-review-workflow/` in the consuming repo,
which is the standard installation location.**

| Script | Purpose |
|--------|---------|
| `.github/skills/pr-review-workflow/scripts/request_copilot_review.sh <owner/repo> <pr>` | Request Copilot review — skips if already queued/in-progress (idempotent) |
| `.github/skills/pr-review-workflow/scripts/monitor_ci_pr.sh <owner/repo> <pr>` | Poll CI runs + Copilot review; exit when all done |
| `.github/skills/pr-review-workflow/scripts/show_pr_review_comments.py <owner/repo> <pr>` | List **all** active review threads with numbers (full GraphQL pagination) |
| `.github/skills/pr-review-workflow/scripts/show_ci_annotations.py <owner/repo> <pr>` | Per-run check output summaries (e.g. MegaLinter analysis) **and** file/line annotations for the HEAD commit |
| `.github/skills/pr-review-workflow/scripts/show_pr_comments.py <owner/repo> <pr>` | List ALL general PR comments (bot and human) from the Conversation tab — MegaLinter, GHAS, and any reviewer comments outside a formal review |
| `.github/skills/pr-review-workflow/scripts/pr_thread.py <owner/repo> <pr> fix <N...> "msg"` | Reply with message + resolve (auto-prefixes [FIXED] if previously deferred) |
| `.github/skills/pr-review-workflow/scripts/pr_thread.py <owner/repo> <pr> reply <N> "msg"` | Reply asking for clarification, leaves thread open |
| `.github/skills/pr-review-workflow/scripts/pr_thread.py <owner/repo> <pr> defer <N> ["context"]` | Reply with [DEFERRED] context + resolve; shows in list-deferred |
| `.github/skills/pr-review-workflow/scripts/pr_thread.py <owner/repo> <pr> list-deferred` | List deferred threads not yet marked [FIXED] |

## Workflow

> **⚠️ One commit per round — no exceptions.**
> Collect ALL issues from ALL sources before touching a single file.
> If you fix something and then discover another issue, that is a skill violation.
> The correct per-round sequence (each round is one full loop iteration):
> **fix → single commit → push → request review → resolve threads → monitor → collect.**
> Push always comes *before* requesting review so Copilot reviews the fixed code.

Repeat this loop until the Copilot review comes back clean with no issues:

### Step 1: Request Copilot Review (if needed)

```bash
.github/skills/pr-review-workflow/scripts/request_copilot_review.sh <owner/repo> <pr>
```

This script checks whether a Copilot review is already queued or in progress for the current
HEAD commit before requesting one. Repos with automatic review settings trigger a review on
every push — requesting a second one is redundant. The script is idempotent: safe to call
unconditionally regardless of whether auto-review is enabled.

### Step 2: Resolve Open Threads

For every active thread from the previous review round, take **exactly one** action.
On the first pass there are no threads — skip to Step 3.

**Fixed in code → fix (reply + resolve):**

```bash
.github/skills/pr-review-workflow/scripts/pr_thread.py <owner/repo> <pr> fix 26 27 36 "Fixed in <sha>: <description>."
```

**Must revisit before merge → defer (reply [DEFERRED] + resolve):**

```bash
.github/skills/pr-review-workflow/scripts/pr_thread.py <owner/repo> <pr> defer 77 "Tag cleanup — review before merge."
```

**Need clarification from reviewer → reply (leaves thread open):**

```bash
.github/skills/pr-review-workflow/scripts/pr_thread.py <owner/repo> <pr> reply 31 "Can you clarify expected behavior when X is nil?"
```

**Never resolve a thread without either fixing the code or leaving an explanatory reply.**

### Step 3: Monitor CI + Review

```bash
.github/skills/pr-review-workflow/scripts/monitor_ci_pr.sh <owner/repo> <pr>
```

Exits when all CI checks reach a terminal state AND the Copilot review for the current HEAD commit is submitted.

### Step 4: COLLECT — Gather ALL Issues Before Touching Any File

> **Do not modify any file until you have run all three commands below and compiled
> a complete issue list.** Fixing after seeing only one source is the most common
> cause of extra commits in a round.

GitHub PRs have three distinct issue surfaces, each requiring a separate check:

| Surface | What lives here | Script |
|---------|----------------|--------|
| Review threads | Inline Copilot code comments | `show_pr_review_comments.py` |
| CI check-run output | Per-run tool reports (MegaLinter analysis, linter summaries) **and** file/line annotations — tied to HEAD, never stale | `show_ci_annotations.py` |
| PR comments | Bot tool summaries (MegaLinter, GHAS, Dependabot) **and** human reviewer comments outside a formal review | `show_pr_comments.py` |

```bash
# 1. Copilot review threads
.github/skills/pr-review-workflow/scripts/show_pr_review_comments.py <owner/repo> <pr>

# 2. CI check-run output summaries and annotations
.github/skills/pr-review-workflow/scripts/show_ci_annotations.py <owner/repo> <pr>

# 3. General PR comments (bot and human, Conversation tab)
.github/skills/pr-review-workflow/scripts/show_pr_comments.py <owner/repo> <pr>
```

Read all output. Write down every actionable item. Only when the complete list is in hand
should you proceed to Step 5.

If all three return no issues → **done, PR is merge-ready.** Break the loop.

### Step 5: FIX — Address Every Issue From the Complete List

Fix every item collected in Step 4 in one pass. Do not commit partial fixes — if you
discover a new issue while implementing a fix, add it to the current batch, do not
commit and loop back.

If the repo has a required pre-commit build or generation step (e.g. `npm run build`,
`npm run generate`), run it now so generated artifacts stay in sync with source changes.

### Step 6: Single Commit and Push

One commit per review round (include any generated artifacts). Then repeat from Step 1.

> ⚠️ **Order matters**: always push the fix commit *before* requesting the next review.
> Requesting review before pushing means Copilot reviews the unfixed code.

## Pre-Merge Checklist

Before merging, check for deferred items:

```bash
.github/skills/pr-review-workflow/scripts/pr_thread.py <owner/repo> <pr> list-deferred
```

For each deferred item: either fix and mark `[FIXED]`, or create a follow-up issue.

If any changes are made during the pre-merge checklist (e.g. CHANGELOG update, deferred fixes),
commit and push them, then request a new Copilot review and get a clean result before merging.
