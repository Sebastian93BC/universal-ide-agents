<!-- markdownlint-disable MD033 -->

# Changelog

Release journal for `universal-ide-agents`.

This file follows Semantic Versioning and records meaningful changes to the shared VS Code asset library.

---

## Unreleased

### Added in Unreleased

- `Documentation Steward` agent for source-control-aware updates to `README.md`, `CHANGELOG.md`, and conditional `LICENSE` maintenance.
- Session tracking infrastructure under `.github/sessions/` with an `index.md` trace file for historical context across Feature Builder runs.

### Changed in Unreleased

- `Planner` reworked: added `Explore` subagent for codebase research, structured four-phase workflow (Discovery → Alignment → Design → Refinement), session persistence to `.github/sessions/{slug}/plan.md` and `/memories/session/plan.md`, plan style guide, and handoff to `Implementer`.
- `Implementer` reworked: now reads the approved plan from session memory, logs progress to `.github/sessions/{slug}/implementation.md`, and includes expanded tools (web, terminal, memory, GitHub issue/PR access).
- `Feature Builder` expanded to a nine-step workflow with session slug generation (step 0), `Documentation Steward` integration (step 6), and session index logging (step 9). Added `edit` tool.
- `Documentation Guidelines` prompt model updated to `GPT-5.4 (copilot)`.
- `README.md` and asset catalog updated to reflect the documentation stewardship workflow and session tracking.

### Fixed in Unreleased

- Corrected `user-invokable` → `user-invocable` in frontmatter of `Feature Builder`, `Plan Architect`, and `Reviewer` agents.

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
