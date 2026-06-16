---
applyTo: "plans/**/*"
description: Guidelines for structuring and persisting development plans.
---

# Planning Instructions

Whenever you generate a new development plan or edit an existing plan, you must strictly follow these instructions:

## 1. Single Source of Truth for Plans
All plans and active agent outputs must be managed inside the `plans/` directory at the project root.
- **Do not** write plans to temporary folders, session cache folders (like `.github/sessions/`), or custom scratchpad files.
- While a task is active, save its files in the root of `plans/` using the `{slug}` of the task (e.g., `plans/{slug}_plan.md`, `plans/{slug}_walkthrough.md`, `plans/{slug}_review.md`).
- At the start of a task, register it in the registry file: [registry.md](./plans/registry.md) with state `En Progreso`.

## 2. Plan Structure
Every plan must follow the standard structure:
- **Goal**: Clear, brief statement of what the change accomplishes.
- **User Review Required**: Alert boxes highlighting potential breaking changes, design trade-offs, or decisions needing human input.
- **Open Questions**: Outstanding questions that must be resolved.
- **Proposed Changes**: Files grouped by component, indicating whether they are modified (`[MODIFY]`), new (`[NEW]`), or deleted (`[DELETE]`).
- **Verification Plan**: Step-by-step instructions to verify the changes manually or via automated test suites.

## 3. Registry and Archiving Lifecycle
When a task is completed and verified:
1. **Archive the Plan**: Move/rename the plan file to `plans/historyPlans/{slug}_plan.md`.
2. **Archive the Walkthrough**: Move/rename the walkthrough/execution report to `plans/walkthroughs/{slug}_walkthrough.md`.
3. **Clean Up**: Remove any temporary files (like review reports) from the root of `plans/`.
4. **Update Registry**: Change the task status in [registry.md](./plans/registry.md) to `Completado`.

## 4. Technical Knowledge Base
Any key insights, architectural decisions, or discovered information must be persisted inside the `plans/knowledge/` directory as individual markdown files (e.g., `plans/knowledge/topic-details.md`) so that agents can load them for context in subsequent tasks. Avoid editing core instructions for session-specific decisions.
