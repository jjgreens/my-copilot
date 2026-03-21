# my-copilot

Personal GitHub Copilot customizations — agents, skills, instructions, and workflows.

## Structure

```
agents/          ← custom agents (.agent.md) — source of truth
skills/          ← agent skills (folder + SKILL.md + assets) — source of truth
instructions/    ← instruction files (.instructions.md) — standalone install only
workflows/       ← agentic workflows (.md → .lock.yml via gh aw)
plugins/         ← generated artifacts (do not edit directly)
eng/             ← build scripts
```

`plugins/` is populated by build scripts from the top-level source directories.
Never edit files inside `plugins/` directly.

## Installing a Plugin

```bash
/plugin install jjgreens/my-copilot@pr-review-workflow
/plugin install jjgreens/my-copilot@1source-inventory-analyst
```

## Installing an Instruction (standalone)

Download and add to your workspace's `.github/instructions/` folder:

- `instructions/git-workflow.instructions.md` — git workflow rules
- `instructions/copilot-behavior.instructions.md` — verification and inference standards

## Available Plugins

| Plugin | Contents | Description |
|--------|----------|-------------|
| `pr-review-workflow` | 1 skill | Drive PRs through the Copilot review cycle to merge-ready |
| `1source-inventory-analyst` | 1 agent | Search Intel 1Source GHE inventory for BKMs |

## Building Plugins

After editing source files, regenerate the `plugins/` artifacts:

```bash
npm run plugin:clean
npm run plugin:build
```

Then commit the updated `plugins/` directory and open a PR.

## Adding New Content

- **Agent**: add `agents/<name>.agent.md`, create `plugins/<name>/.github/plugin/plugin.json`
- **Skill**: add `skills/<name>/SKILL.md` (+ assets), reference `./skills/<name>` in a plugin.json
- **Instruction**: add `instructions/<name>.instructions.md` (standalone — not bundled in plugins)

Run `npm run plugin:build` after adding agents or skills.
