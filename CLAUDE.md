# Claude Code — Repository Guidelines

This project uses a modular system of agents, prompts, and instructions to maintain code quality, streamline development, and automate workflows.

As Claude Code, you must align your behavior with the guidelines established for this repository.

## 1. Core Instructions
- Read and follow the rules in `.github/copilot-instructions.md` as the primary repository guide.
- Adhere to the defined folder structure:
  - `.github/agents/*.agent.md` — Declarations of agent roles and workflows.
  - `.github/instructions/*.instructions.md` — Modularity-specific rules (e.g., versioning).
  - `.github/prompts/*.prompt.md` — Prompts for on-demand use.
  - `plans/` — The single source of truth for planning and repository knowledge.

## 2. Simulating Agent Workflows
Claude Code does not natively support Copilot's `@agent` syntax. However, if the user requests you to act as one of our custom agents, or mentions them, you must load and simulate the workflow defined in their configuration:
- **Feature Builder**: Simulates the full workflow in `.github/agents/Feature Builder.agent.md`.
- **Planner**: Simulates research, plan creation, and user approval gates using `.github/agents/Planner.agent.md`.
- **Reviewer / Code Reviewer**: Performs reviews following `.github/agents/Reviewer.agent.md` or `.github/agents/Code Reviewer.agent.md`.
- **Data Science Developer**: Guides the 6-phase notebook development cycle following `.github/agents/Data Science Developer.agent.md`.

## 3. Passive Instruction Application
Whenever you edit files that match the `applyTo` patterns of our instructions under `.github/instructions/`, you must load and respect those instructions:
- When editing `CHANGELOG.md`, strictly apply the rules in `.github/instructions/Versioning.instructions.md`.
- When editing notebooks (`.ipynb`) or files under exploration folders, apply the rules in `.github/instructions/NotebookMethodology.instructions.md`.

## 4. Hook and Script Execution
- Respect the hooks defined in `.github/hooks/context.json`.
- Before executing commands, ensure you use the local scripts (e.g., `scripts/deploy-to-project.sh`, `scripts/scaffold-experimental-module.sh`) and respect the project's sandboxing limits.
- When finishing a task or session, trigger the logic in `scripts/save-session-output.sh` (usually triggered by the `on_complete` hook) to persist plans and outputs.
