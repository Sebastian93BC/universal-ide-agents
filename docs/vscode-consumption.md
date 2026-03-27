# VS Code Consumption Guide

This repository is designed to be consumed as a secondary configuration source for other VS Code projects.

## Recommended model

Use this repository as a Git submodule or a dedicated secondary checkout, then copy the shared assets into the target repository with the provided install script.

Why this is the primary model:
- It keeps the shared source versioned and auditable.
- It avoids manual copy-paste drift.
- It lets you pin a project to a known asset version.

## Recommended path layout

```text
target-project/
├── .config/
│   └── universal-ide-agents/   # submodule or secondary checkout
├── .github/
│   ├── agents/
│   ├── hooks/
│   ├── instructions/
│   ├── prompts/
│   ├── skills/
│   └── copilot-instructions.md
└── project code
```

## Setup

Add the secondary repository:

```bash
git submodule add git@github.com:Sebastian93BC/universal-ide-agents.git .config/universal-ide-agents
```

Install the shared assets into the current project:

```bash
./.config/universal-ide-agents/scripts/install-vscode-assets.sh "$PWD"
```

Preview changes without modifying files:

```bash
./.config/universal-ide-agents/scripts/install-vscode-assets.sh --dry-run "$PWD"
```

Replace existing shared assets with the version from this repository:

```bash
./.config/universal-ide-agents/scripts/install-vscode-assets.sh --force "$PWD"
```

## What gets installed

The install script copies these assets into the target repository:
- `.github/agents/`
- `.github/hooks/`
- `.github/instructions/`
- `.github/prompts/`
- `.github/skills/`
- `.github/copilot-instructions.md`

## Recommended operating model

1. Keep shared behavior in this repository.
2. Keep project-specific overrides minimal and clearly documented.
3. Update the submodule or secondary checkout when you want a newer shared baseline.
4. Re-run the install script after updating the shared source.

## Guardrails

- Do not edit the copied shared files casually in each project unless the project is intentionally diverging.
- If a project needs persistent custom behavior, document it clearly so you can decide later whether it belongs back in the shared source.
- Treat `--force` as an intentional promotion step, not a default habit.

## Deferred alternatives

Other models, such as git subtree or package-style distribution, are possible but are not the primary path for `v0.1.0`.