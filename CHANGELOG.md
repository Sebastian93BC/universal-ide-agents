<!-- markdownlint-disable MD033 -->

# Changelog

Release journal for `universal-ide-agents`.

This file follows Semantic Versioning and records meaningful changes to the shared VS Code asset library.

---

## 0.2.0-dev · 2026-06-13

<div>

[![Release](https://img.shields.io/badge/release-0.2.0--dev-0F766E?style=for-the-badge)](./README.md) [![Target: Multi-IDE](https://img.shields.io/badge/target-VS%20Code%2C%20Claude%20Code%20%26%20Antigravity-4f46e5?style=for-the-badge&logo=google&logoColor=white)](./docs/antigravity-consumption.md) [![Stage](https://img.shields.io/badge/stage-multi--IDE%20expansion-1D4ED8?style=for-the-badge)](./docs/antigravity-consumption.md)

</div>

### Added

- **Claude Code Support**: Added `CLAUDE.md` to bridge repository instructions, agents, and modular scripts to the Claude Code CLI.
- **Data Science / Notebook Methodology**: Native support for the 6-phase experimental notebook lifecycle (Exploration → Extraction → Diagnosis → Lessons → Commits → Promotion).
- **New Agents**:
  - `.github/agents/Code Reviewer.agent.md` focusing on code quality, security (OWASP), accessibility, and design patterns.
  - `.github/agents/Data Science Developer.agent.md` to guide the 6-phase notebook cycle.
  - `.github/agents/Scientific Paper Research.agent.md` relying on the `bgpt` MCP server.
- **New Instructions**:
  - `.github/instructions/Versioning.instructions.md` for `CHANGELOG.md` edits.
  - `.github/instructions/Planning.instructions.md` to route plans to the `plans/` directory.
  - `.github/instructions/NotebookMethodology.instructions.md` for notebooks development.
- **New Automation Tools**:
  - `scripts/save-session-output.sh` to backup plans, walkthroughs, and reviews.
  - `scripts/scaffold-experimental-module.sh` to bootstrap new notebooks folders.
  - `scripts/clean-notebook-outputs.py` to strip cells outputs and metadata.
- **Plans & Traceability Centralization**:
  - `plans/README.md` (dashboard) and `plans/knowledge_base.md` (tech decisions log).
  - `.github/sessions/trace-db.jsonl` log file for agent execution traces.

### Changed

- `scripts/deploy-to-project.sh` expanded to copy `CLAUDE.md` and dynamically rewrite hook commands inside `context.json`.
- `.github/copilot-instructions.md` made IDE-agnostic and expanded to include Claude Code in its scope.
- `.github/agents/Reviewer.agent.md` refactored to focus solely on VS Code assets quality.
- `.github/agents/Feature Builder.agent.md` updated to include `Code Reviewer` in its pipeline.
- `.github/hooks/context.json` updated with `on_complete` hook to automatically save session outputs.

---

## 0.1.2-dev · 2026-05-27

<div>

[![Release](https://img.shields.io/badge/release-0.1.2--dev-0F766E?style=for-the-badge)](./README.md) [![Target: Multi-IDE](https://img.shields.io/badge/target-VS%20Code%20%26%20Antigravity-4f46e5?style=for-the-badge&logo=google&logoColor=white)](./docs/antigravity-consumption.md) [![Stage](https://img.shields.io/badge/stage-multi--IDE%20expansion-1D4ED8?style=for-the-badge)](./docs/antigravity-consumption.md)

</div>

### Added

- Native **Antigravity** compatibility layer to support the Google DeepMind agentic environment.
- `.github/antigravity-instructions.md` & `.antigravity-instructions.md` containing repository-wide instructions, visual standards, and native role configurations (Planner, Implementer, Reviewer, Documentation Steward, Feature Builder).
- `docs/antigravity-consumption.md` — a comprehensive guide detailing how to integrate, configure, and consume these assets inside the Antigravity agentic environment, leveraging standard planning mode files and interactive slash commands (`/grill-me`, `/goal`, `/schedule`).
- Added walkthrough generation to the VS Code custom agent pipeline (`Feature Builder`), creating a matching `.github/sessions/{slug}/walkthrough.md` report at the end of delivery cycles for symmetric parity with Antigravity sessions.

### Changed

- `scripts/deploy-to-project.sh` expanded to map and deploy Antigravity instructions files alongside VS Code custom assets, maintaining idempotency and dry-run safety. Hardened with a signals `trap` on exit for temporary file cleanup and path normalization to prevent double trailing slash comparison bugs.
- `scripts/inject-context.sh` maximum root listed files made configurable via the `MAX_ENTRIES` environment variable (defaulting to 20).
- `README.md` and `docs/asset-catalog.md` updated to reflect the expanded support matrix, target badges, simplified agent layer (Planner, Documentation Steward, Reviewer, Feature Builder), and deprecated install-vscode-assets.sh helper.
- `Feature Builder` orchestration streamlined: removed deleted subagents from core pipeline and updated orchestrator steps (Steps 3, 4, 5) to use native Copilot Plan/Agent Modes or Antigravity's Planning Mode directly with disk-based plan tracking (`.github/sessions/{slug}/plan.md`).
- `Planner` agent upgraded to absorb design self-validation constraints, acting as its own quality validator to check for duplication, portability, and naming convention compliance.
- `Reviewer` agent edit tool guidelines hardened to strictly prevent accidental repository asset edits (strictly limited to writing its own report).
- Corrected `docs/vscode-consumption.md` layout paths from `.config/` to `.githubconfig/` to reflect v0.1.1 rename convention.
- Added warning banner in both `.github/antigravity-instructions.md` and `.antigravity-instructions.md` to prevent future copy-drift.

### Removed

- **Removed `Plan Architect.agent.md`**: Delegated planning validation directly to native Copilot Plan Mode or manual verification.
- **Removed `Implementer.agent.md`**: Scoped execution rules directly into the `Feature Builder` orchestrator, transitioning implementation tasks to native Copilot Agent Mode or Antigravity's Planning Mode.

## 0.1.1 · 2026-03-31

<div>

[![Release](https://img.shields.io/badge/release-0.1.1-0F766E?style=for-the-badge)](./README.md) [![Target](https://img.shields.io/badge/target-VS%20Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)](https://code.visualstudio.com/) [![Stage](https://img.shields.io/badge/stage-agent%20evolution%20%26%20deploy%20system-1D4ED8?style=for-the-badge)](./docs/vscode-consumption.md)

</div>

### Added

- `Documentation Steward` agent for source-control-aware updates to `README.md`, `CHANGELOG.md`, and conditional `LICENSE` maintenance.
- Session tracking infrastructure under `.github/sessions/` with an `index.md` trace file for historical context across Feature Builder runs.
- `scripts/deploy-to-project.sh` — canonical deployment script that distributes the full asset surface to consumer projects with explicit path mapping: `.github/` → `.github/`, `docs/` → `.github/docs/`, `scripts/` → `.github/scripts/`. Supports `--dry-run` to preview operations and `--clean` to remove files inside managed directories that no longer exist in the source. Automatically rewrites the hook command path in `context.json` after copying so it resolves correctly inside the consumer project. POSIX-compatible and idempotent.

### Changed

- `Planner` reworked: added `Explore` subagent for codebase research, structured four-phase workflow (Discovery → Alignment → Design → Refinement), session persistence to `.github/sessions/{slug}/plan.md` and `/memories/session/plan.md`, plan style guide, and handoff to `Implementer`.
- `Implementer` reworked: now reads the approved plan from session memory, logs progress to `.github/sessions/{slug}/implementation.md`, and includes expanded tools (web, terminal, memory, GitHub issue/PR access).
- `Feature Builder` expanded to a nine-step workflow with session slug generation (step 0), `Documentation Steward` integration (step 6), and session index logging (step 9). Added `edit` tool.
- `Documentation Guidelines` prompt model updated to `GPT-5.4 (copilot)`.
- `README.md`, asset catalog, and VS Code consumption guide updated to reflect the deploy system, documentation stewardship workflow, and session tracking.
- `scripts/install-vscode-assets.sh` marked deprecated in favor of `scripts/deploy-to-project.sh`.
- Canonical submodule path renamed from `.config/universal-ide-agents/` to `.githubconfig/universal-ide-agents/` to avoid collision with `.config/` directories commonly used by Python, Node.js, and other project toolchains. Updated in `README.md`, `docs/vscode-consumption.md`, and the `deploy-to-project.sh` usage block.

### Fixed

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
