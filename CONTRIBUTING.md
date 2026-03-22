# Contributing

## Branch and PR Policy

**Never push directly to `main`.** All changes must go through a pull request.

**Always start from an up-to-date `main`:**

```bash
git checkout main && git pull
git checkout -b <branch-name>
# make changes
git push -u origin <branch-name>
gh pr create
```

Use the `pr-review-workflow` skill to drive PRs to merge-ready state. See `instructions/git-workflow.instructions.md` for the full PR review cycle order, pre-merge checklist, and merge process.

## Making Changes

Source files live under `agents/`, `skills/`, and `instructions/`.  
**Never edit files under `plugins/` or `.github/instructions/` directly** — they are generated artifacts.

After editing any source agent, skill, or instruction, regenerate the materialized copies:

```bash
npm run plugin:build
```

Include the updated `plugins/` and `.github/instructions/` output in the same commit as your source changes.

## PR Workflow

This repo uses the `pr-review-workflow` skill to drive PRs to merge-ready state.

When fixing review threads, remember to:

1. Fix the source files under `agents/`, `skills/`, etc.
2. Run `npm run plugin:build` to sync the materialized copies.
3. Commit both source and generated output together before pushing.

Skipping step 2 means the next Copilot review will flag the same issues in the
materialized copies, adding unnecessary review rounds.
