# Contributing

## Making Changes

Source files live under `agents/`, `skills/`, and `instructions/`.  
**Never edit files under `plugins/` directly** — they are generated artifacts.

After editing any source agent or skill, regenerate the materialized copies:

```bash
npm run plugin:build
```

Include the updated `plugins/` output in the same commit as your source changes.

## PR Workflow

This repo uses the `pr-review-workflow` skill to drive PRs to merge-ready state.

When fixing review threads (Step 5 of the workflow), remember to:

1. Fix the source files under `agents/`, `skills/`, etc.
2. Run `npm run plugin:build` to sync the materialized copies in `plugins/`.
3. Commit both source and plugin changes together before pushing.

Skipping step 2 means the next Copilot review will flag the same issues in the
materialized copies, adding unnecessary review rounds.
