# Changelog

## [Unreleased]

---

## [1.0.3] - 2026-03-22

### Changed — fix: pr-review-workflow skill improvements (#5)

- `skills/pr-review-workflow/SKILL.md`: added install-path note to Tools section; simplified one-commit warning to plain constraint statements (removed ambiguous sequence line)
- `skills/pr-review-workflow/scripts/request_copilot_review.sh`: extended idempotency to also skip when a Copilot review check run is already `completed` for HEAD
- `skills/pr-review-workflow/scripts/show_ci_annotations.py`: use `output` from initial check-runs list response (no extra per-run API call); skip incomplete runs and count them separately; fix "all clean" message to only print when CI is fully done; update docstring to reflect filtered (actionable-only) reporting
- `skills/pr-review-workflow/scripts/show_pr_comments.py`: update docstring to name all three PR comment surfaces and clarify this script covers issue comments only
- `skills/pr-review-workflow/scripts/show_pr_review_comments.py`: make suggested `pr_thread.py` path dynamic via `__file__` + `shlex.quote` instead of hardcoded install path
- `plugins/pr-review-workflow/`: regenerated from `skills/` via `npm run plugin:build`

---

## [1.0.2] - 2026-03-22

### Added — docs: add msr-workflow instructions (#4)

- `instructions/msr-workflow.instructions.md`: end-of-session MSR update workflow — naming convention, active-file logic (next-month with Dec→Jan rollover), what sections to update, and upload steps
- `.github/instructions/msr-workflow.instructions.md`: materialized copy (generated via `plugin:build`)

---

## [1.0.1] - 2026-03-22

### Changed — docs: session learnings from PR #1 review cycle (#3)

- `instructions/git-workflow.instructions.md`: full workflow rules — pull-before-branch, PR review cycle order (via `pr-review-workflow` skill), pre-merge checklist, no-force-push with fetch+rename approach, and merge process (CHANGELOG in PR, concise squash body, pull after merge)
- `eng/materialize-plugins.mjs`: copy `instructions/` → `.github/instructions/` during `plugin:build`; always clean stale output even when source is empty
- `eng/clean-materialized-plugins.mjs`: also clean `.github/instructions/` on clean
- `.github/copilot-instructions.md`: trimmed to repo-specific plugin-build rule only
- `CONTRIBUTING.md`: simplified; branch example now includes commit step

---

## [1.0.0] - 2026-03-22

### Added — feat: add pr-review-workflow plugin and repo scaffolding (#1)

- `pr-review-workflow` skill: multi-round Copilot review cycle with CI monitoring, thread management (fix/defer/collapse), and pagination across reviews, runs, and comments
- `1source-inventory-analyst` agent: searches Intel 1Source GHE inventory for noteworthy repos
- `eng/materialize-plugins.mjs` + `eng/clean-materialized-plugins.mjs`: build tooling to copy source agents/skills into installable `plugins/` layout
- `.github/copilot-instructions.md`, `CONTRIBUTING.md`: repo policies (branch+PR workflow, plugin:build requirement, review cycle order)
- `instructions/`, `workflows/` scaffolding for future content
