# Changelog

## [Unreleased]

---

## [0.1.0] - 2026-03-22

### Added — feat: add pr-review-workflow plugin and repo scaffolding (#1)

- `pr-review-workflow` skill: multi-round Copilot review cycle with CI monitoring, thread management (fix/defer/collapse), and pagination across reviews, runs, and comments
- `1source-inventory-analyst` agent: searches Intel 1Source GHE inventory for noteworthy repos
- `eng/materialize-plugins.mjs` + `eng/clean-materialized-plugins.mjs`: build tooling to copy source agents/skills into installable `plugins/` layout
- `.github/copilot-instructions.md`, `CONTRIBUTING.md`: repo policies (branch+PR workflow, plugin:build requirement, review cycle order)
- `instructions/`, `workflows/` scaffolding for future content
