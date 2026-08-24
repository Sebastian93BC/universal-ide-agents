---
applyTo: ".githubconfig/universal-ide-agents/**/*"
description: Guidelines for managing updates, submodules, and resolving deployment or git conflicts.
---

# Conflict Resolution & Synchronization Instructions

Whenever a developer requests help to update the `universal-ide-agents` submodule, deploy assets, or resolve conflicts arising from updates, you must strictly follow these instructions:

## 1. Conflict Scenarios and Detection

There are two primary types of conflicts that occur during synchronization:

### A. Local Overwrite Conflicts (Consumer `.github/` vs Submodule)
Developers sometimes make local modifications directly in the deployed files under `.github/` (e.g., editing `.github/agents/Planner.agent.md` directly in the consumer project). Since `deploy-to-project.sh` overwrites these files, any local custom changes will be lost.
*   **Detection**: Run `git diff --name-only .github/` in the consumer project to identify modified files. Cross-reference them with the files copied by `deploy-to-project.sh`.

### B. Git Merge Conflicts (Submodule Level)
Conflicts inside the submodule folder (`.githubconfig/universal-ide-agents/`) when updating using `git submodule update --remote --merge`.
*   **Detection**: Run `git status` or `git submodule status` to check if the submodule is in a conflicted state or has detached head/diverged commits.

---

## 2. Resolution Protocols for Agents

### Protocol for Local Overwrite Conflicts

If the agent detects local modifications in `.github/` directories managed by the submodule:
1.  **Analyze the changes**: Run `git diff .github/` to inspect what changes the developer introduced locally.
2.  **Determine the scope**:
    *   *If the changes are general improvements* (reusable across all projects): Advise the user to port them upstream to the submodule repository, commit/push them there, and pull them back.
    *   *If the changes are project-specific overrides*: Explain that they will be overwritten by the next deploy. Suggest extracting the custom logic if possible, or back them up so they can be reapplied or documented as exceptions.
3.  **Perform safe cleanup (with approval)**: If the user approves discarding the local overrides to pull the latest shared version, run:
    ```bash
    git checkout -- .github/agents/ .github/instructions/ .github/prompts/ .github/skills/
    ```
    Then run the deploy script:
    ```bash
    ./.githubconfig/universal-ide-agents/scripts/deploy-to-project.sh "$PWD"
    ```

### Protocol for Submodule Git Conflicts

If the submodule update command (`git submodule update --remote --merge`) fails with merge conflicts:
1.  **Inspect the submodule status**: Run `git status` from the submodule directory (e.g., `.githubconfig/universal-ide-agents/`).
2.  **Guide the user or execute resolution**:
    *   If there are untracked files or uncommitted changes causing blocking: offer to stash or discard them (with confirmation).
    *   If there is a real merge conflict: run standard git merge resolution tools, or reset the submodule branch to the remote origin if local changes are not needed:
        ```bash
        # Reset the submodule to the remote main
        git checkout main
        git reset --hard origin/main
        ```
3.  **Finalize sync**: Re-run the update from the consumer project root:
    ```bash
    git submodule update --init --recursive
    ./.githubconfig/universal-ide-agents/scripts/deploy-to-project.sh --clean "$PWD"
    ```
