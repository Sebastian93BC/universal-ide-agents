# VS Code Consumption Guide

This repository is designed to be consumed as a secondary configuration source for other VS Code projects.

## Recommended model

Keep this repository as a Git submodule at `.config/universal-ide-agents/` and use `deploy-to-project.sh` to copy the shared assets into the consumer project. The deploy script handles the full path mapping, overwrites managed files on every run, and keeps consumer-owned files untouched.

Why this model:
- The shared source stays versioned and auditable.
- No manual copy-paste drift.
- Each consumer project can pin to a known asset version via the submodule.

## Path mapping

The deploy script applies this mapping on every run:

| Source in `universal-ide-agents` | Destination in consumer project |
| --- | --- |
| `.github/agents/` | `.github/agents/` |
| `.github/hooks/` | `.github/hooks/` |
| `.github/instructions/` | `.github/instructions/` |
| `.github/prompts/` | `.github/prompts/` |
| `.github/skills/` | `.github/skills/` |
| `.github/copilot-instructions.md` | `.github/copilot-instructions.md` |
| `docs/` | `.github/docs/` |
| `scripts/` | `.github/scripts/` |

`.github/sessions/` is never deployed. Consumer session history is always preserved.

## Hook path rewriting

The hook file `context.json` references `./scripts/inject-context.sh` in the source repository. After copying, the deploy script rewrites that path to `./.github/scripts/inject-context.sh` so the hook resolves correctly inside the consumer project on every run.

## Recommended path layout

```text
target-project/
├── .config/
│   └── universal-ide-agents/       # submodule
├── .github/
│   ├── agents/
│   ├── docs/
│   ├── hooks/
│   ├── instructions/
│   ├── prompts/
│   ├── scripts/
│   ├── skills/
│   └── copilot-instructions.md
└── project code
```

## First-time setup

Add the submodule:

```bash
git submodule add git@github.com:Sebastian93BC/universal-ide-agents.git .config/universal-ide-agents
```

Deploy assets to the current project:

```bash
./.config/universal-ide-agents/scripts/deploy-to-project.sh "$PWD"
```

## Ongoing updates

Pull the latest changes from the shared source and redeploy:

```bash
git submodule update --remote --merge
./.config/universal-ide-agents/scripts/deploy-to-project.sh --clean "$PWD"
```

Use `--clean` to also remove files that were deleted from the source since the last deploy.

## Flags

| Flag | Effect |
| --- | --- |
| `--dry-run` | Print all planned operations without writing or deleting any files. |
| `--clean` | After copying, delete files inside managed target directories that no longer exist in the source. |

Preview what would happen before committing:

```bash
./.config/universal-ide-agents/scripts/deploy-to-project.sh --dry-run "$PWD"
```

## What is not touched

The deploy script only writes inside the managed directories listed in the path mapping table. Everything outside that surface — `src/`, `notebooks/`, `data/`, `config/`, `scripts/` at the project root, `README.md`, `pyproject.toml`, and any other consumer-owned `.github/` directories such as `workflows/` — is never modified.

## Operating model

1. Develop all shared behavior in `universal-ide-agents`. Do not edit deployed copies directly.
2. When a consumer project needs to diverge from the shared baseline, document it explicitly and decide whether it belongs back in the shared source.
3. Update the submodule and redeploy when you want a newer shared baseline.

## Deferred alternatives

Other models, such as git subtree or package-style distribution, are possible but are not the primary path for `v0.1.0`.