# Copilot Instructions for my-copilot

## Plugin Build Requirement

This repo materializes plugin artifacts into `plugins/` via `npm run plugin:build`.
Source files live under `agents/`, `skills/`, and `instructions/`.

**After any change to source agents, skills, or instructions, always run:**

```bash
npm run plugin:build
```

Include the updated `plugins/` and `.github/instructions/` output in the same commit as the source changes.
**Never commit source changes without also committing the regenerated output.**

This applies during PR review fix rounds: fix the source, run `plugin:build`, then commit both together.
