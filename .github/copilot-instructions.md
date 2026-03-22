# Copilot Instructions for my-copilot

## Plugin Build Requirement

This repo materializes plugin artifacts into `plugins/` via `npm run plugin:build`.
Source files live under `agents/`, `skills/`, and `instructions/`.

**After any change to source agents or skills, always run:**

```bash
npm run plugin:build
```

Include the updated `plugins/` output in the same commit as the source changes.
**Never commit source changes without also committing the regenerated `plugins/` output.**

This applies during PR review fix rounds: fix the source, run `plugin:build`, then commit both together.

## Branch and PR Policy

**Never push directly to `main`.** All changes must go through a PR:

1. Create a branch: `git checkout -b <branch-name>`
2. Commit changes
3. Push and open a PR
4. Drive to merge-ready using the `pr-review-workflow` skill



When driving a PR through the Copilot review cycle (using the `pr-review-workflow` skill),
the correct order within each round is:

1. **Fix** source issues identified in Step 4
2. **Run** `npm run plugin:build` to sync `plugins/`
3. **Commit and push** all changes together
4. **Request** Copilot review (only after the fix is live on the branch)
5. **Resolve** threads from the previous round
6. **Monitor** CI + review

> Never request a review before pushing the fix — Copilot will review the unfixed code.
