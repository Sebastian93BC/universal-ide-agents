<!-- markdownlint-disable MD033 -->

# Changelog

Release journal for `universal-ide-agents`.

This file follows Semantic Versioning and records meaningful changes to the shared VS Code asset library.

---

## 0.1.0 · 2026-03-27

<div>

[![Release](https://img.shields.io/badge/release-bootstrap-0F766E?style=for-the-badge)](./README.md) [![Target](https://img.shields.io/badge/target-VS%20Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)](https://code.visualstudio.com/) [![Stage](https://img.shields.io/badge/stage-initial%20public%20baseline-1D4ED8?style=for-the-badge)](./docs/vscode-consumption.md)

</div>

### Added

- Root repository identity with `README.md`, `LICENSE`, `.gitignore`, and this changelog.
- A VS Code-first consumption guide for using the repository as a secondary configuration source.
- An asset catalog that documents the current agents, skills, prompts, instructions, hooks, and scripts.
- `scripts/install-vscode-assets.sh` for copying shared assets into target repositories.
- `scripts/inject-context.sh` for hook-driven context injection.
- A roadmap document that captures the next evolution of the repository.

### Changed

- Rewrote `.github/copilot-instructions.md` so it reflects the actual purpose of the repository.
- Improved the metadata and operating rules for the core agents: `Feature Builder`, `Planner`, `Plan Architect`, `Implementer`, and `Reviewer`.
- Upgraded the documentation prompt and documentation instruction guidance for repository consistency.

### Fixed

- Removed naming drift and stale project references inherited from unrelated work.
- Removed accidental workspace artifacts from source control scope.

### Notes

- `v0.1.0` supports VS Code only.
- Support for other editors should land as explicit future milestones, not as implied compatibility.

---

## Tag Convention

- Stable releases: `vMAJOR.MINOR.PATCH`
- Example: `v0.1.0`

## Branch Intent

- `main`: stable baseline
- `dev`: active development
- `test`: controlled validation
