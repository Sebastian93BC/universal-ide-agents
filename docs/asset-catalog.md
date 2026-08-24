# Asset Catalog

This catalog documents the reusable VS Code & Antigravity assets currently shipped by `universal-ide-agents`.

## Agents

| File | Purpose |
| --- | --- |
| `.github/agents/Feature Builder.agent.md` | Coordinates end-to-end feature delivery using planning, architecture validation, implementation, documentation sync, and review |
| `.github/agents/Documentation Steward.agent.md` | Synchronizes README, changelog, and license-sensitive documentation from the current source control state and available worktree context |
| `.github/agents/Planner.agent.md` | Researches the codebase via Explore subagent, designs structured plans, and persists to session folders |
| `.github/agents/Reviewer.agent.md` | Reviews VS Code assets for correctness, safety, portability, and configuration quality |
| `.github/agents/Code Reviewer.agent.md` | Performs deep audits of code changes for quality, patterns, security (OWASP), and accessibility |
| `.github/agents/Scientific Paper Research.agent.md` | Searches and synthesizes scientific papers using the bgpt MCP server |
| `.github/agents/Data Science Developer.agent.md` | Guides the 6-phase experimental notebook development, extraction, diagnosis, and promotion lifecycle |

## Skills

| Skill | Purpose |
| --- | --- |
| `.github/skills/add-social-media-header/` | Adds reusable social badge headers to documentation |
| `.github/skills/add-social-media-footer/` | Adds community-oriented footer sections to documentation |
| `.github/skills/github-actions-debugging/` | Guides debugging of failing GitHub Actions workflows |
| `.github/skills/github-repo-setup/` | Documents GitHub repository bootstrap and metadata configuration |
| `.github/skills/skill-creator/` | Guides the creation of new skills and packaged workflows |

## Instructions

| File | Scope | Purpose |
| --- | --- | --- |
| `.github/instructions/Documentation.instructions.md` | `docs/**/*.md` | Keeps documentation concise, active, and VS Code-first |
| `.github/instructions/Testing.instructions.md` | `tests/**` | Keeps tests focused, isolated, and easy to understand |
| `.github/instructions/Versioning.instructions.md` | `CHANGELOG.md` | Rules for tag formats, semantic versioning, and changelog format |
| `.github/instructions/Planning.instructions.md` | `plans/**/*` | Rules for planning, structuring, and persisting plans to the plans/ directory |
| `.github/instructions/NotebookMethodology.instructions.md` | `**/*.ipynb` | Enforces modular folder structures and the 6-phase notebook lifecycle |
| `.github/instructions/SyncAndConflicts.instructions.md` | `.githubconfig/universal-ide-agents/**/*` | Guidelines for managing updates, submodules, and resolving deployment or git conflicts |

## Prompts

| File | Purpose |
| --- | --- |
| `.github/prompts/Documentation Guidelines.prompt.md` | Produces polished documentation for asset repositories, guides, and catalogs |

## Hooks

| File | Purpose |
| --- | --- |
| `.github/hooks/context.json` | Configures IDE lifecycle hooks (`SessionStart` to inject context, `on_complete` to run `save-session-output.sh`) |

## Scripts

| File | Purpose |
| --- | --- |
| `scripts/deploy-to-project.sh` | Canonical deploy script mapping agents, instructions, docs, scripts, and CLAUDE.md to consumer projects |
| `scripts/save-session-output.sh` | Persists session plans, reviews, and walkthroughs from .github/sessions/ to the plans/ directory |
| `scripts/scaffold-experimental-module.sh` | Initializes directory structures and files for a new modular notebook project |
| `scripts/clean-notebook-outputs.py` | Python CLI to strip cells output, execution count, and metadata from Jupyter Notebooks |
| `scripts/inject-context.sh` | Prints a lightweight project snapshot that hook runners can inject into agent context |
| `scripts/install-vscode-assets.sh` | (Deprecated — use deploy-to-project.sh) Copies shared VS Code assets into a target repository |

## Sessions

| Path | Purpose |
| --- | --- |
| `.github/sessions/index.md` | Cumulative trace of all Feature Builder sessions — used as historical context by Planner and Feature Builder |
| `.github/sessions/trace-db.jsonl` | Local database logging executed agents, queries, thoughts, and outputs for historical analysis |
| `.github/sessions/{slug}/query.md` | Original user request for the session |
| `.github/sessions/{slug}/plan.md` | Approved implementation plan produced by Planner |
| `.github/sessions/{slug}/implementation.md` | Step-by-step log of changes made during implementation (optional) |
| `.github/sessions/{slug}/review.md` | Reviewer findings for the session |
| `.github/sessions/{slug}/code-review.md` | Code Reviewer findings for the session |
| `.github/sessions/{slug}/walkthrough.md` | Comprehensive walkthrough of completed changes, verification steps, and validation results |

## Root Guidance

| File | Purpose |
| --- | --- |
| `CLAUDE.md` | Claude Code CLI integration rules and compatibility instructions |
| `plans/README.md` | Central control room and dashboard index of all development plans |
| `plans/knowledge_base.md` | Repository of technical decisions, legacy code reasons, and architecture guidelines |
| `.github/copilot-instructions.md` | Repository-wide conventions for authoring and evolving shared IDE assets |
| `.github/antigravity-instructions.md` | Repository-wide conventions for authoring and playing agent roles in Antigravity |
| `.antigravity-instructions.md` | Root-level duplicate of Antigravity instructions for automatic discovery |
| `docs/vscode-consumption.md` | Integration and setup guide for VS Code / Copilot Pro environments |
| `docs/antigravity-consumption.md` | Integration and setup guide for Antigravity agentic environment |
| `README.md` | Editorial landing page for the repository |
| `CHANGELOG.md` | Release history and versioning log |

## What is intentionally absent

This release does not define editor-specific assets for anything outside VS Code and Antigravity. When future support is added (e.g., JetBrains, Zed, Cursor), it should be introduced with explicit folders, docs, and version notes instead of being implied.