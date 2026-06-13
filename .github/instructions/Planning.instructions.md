---
applyTo: "plans/**/*"
description: Guidelines for structuring and persisting development plans.
---

# Planning Instructions

Whenever you generate a new development plan or edit an existing plan, you must strictly follow these instructions:

## 1. Single Source of Truth for Plans
All plans must be saved and managed inside the `plans/` directory at the project root.
- **Do not** write plans to temporary folders, session cache folders, or custom scratchpad files.
- The canonical path for a plan is `plans/{slug}_plan.md`, where `{slug}` is the session slug or task identifier.

## 2. Plan Structure
Every plan must follow the standard structure:
- **Goal**: Clear, brief statement of what the change accomplishes.
- **User Review Required**: Alert boxes highlighting potential breaking changes, design trade-offs, or decisions needing human input.
- **Open Questions**: Outstanding questions that must be resolved.
- **Proposed Changes**: Files grouped by component, indicating whether they are modified (`[MODIFY]`), new (`[NEW]`), or deleted (`[DELETE]`).
- **Verification Plan**: Step-by-step instructions to verify the changes manually or via automated test suites.

## 3. Dashboard Integration
After creating or archiving a plan, you must update the dashboard in [README.md](./plans/README.md) at `plans/README.md` to index the new file, along with its status (`En Progreso`, `Completado`, `Pausado`).
