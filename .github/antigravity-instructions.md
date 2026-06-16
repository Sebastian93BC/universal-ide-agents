# universal-ide-agents — Antigravity Instructions

> [!IMPORTANT]
> **ATENCIÓN / WARNING**: Este archivo se mantiene por duplicado en el repositorio para facilitar el auto-discovery del agente:
> 1. [/.antigravity-instructions.md](./.antigravity-instructions.md)
> 2. [/.github/antigravity-instructions.md](./.github/antigravity-instructions.md)
> 
> **Cualquier cambio que realices en uno de ellos DEBE ser replicado exactamente en el otro.**

---

## 1. Role Integration Framework
 
Antigravity operates as a single unified agent but can natively play the specialized roles defined in this project by utilizing its built-in **Planning Mode** (`implementation_plan.md`, `task.md`, `walkthrough.md` artifacts). 

To ensure full collaboration with other IDE agents (like VS Code Copilot and Claude Code) and keep a unified source of truth, Antigravity must integrate with the `plans/` workspace:

### A. Planner Role
- **Goal**: Research the codebase and design an actionable, detailed plan.
- **Workflow**:
  - Read [registry.md](./plans/registry.md) and check [plans/knowledge/](./plans/knowledge/) before starting research.
  - Register the task in `plans/registry.md` with status `En Progreso`.
  - Perform thorough, non-modifying research first using read and search tools.
  - Create or update the `implementation_plan.md` artifact.
  - Mirror the active plan to `plans/{slug}_plan.md` so it is visible to other agents in the workspace.
  - Document any ambiguity, risks, or key design decisions as **Open Questions** directly inside the plan.
  - Request feedback (`RequestFeedback: true`) and **STOP/wait for explicit user approval** before making any source code changes.
 
### B. Implementer Role
- **Goal**: Execute approved plans cleanly and systematically.
- **Workflow**:
  - Retrieve the approved plan and instantiate the `task.md` checklist artifact.
  - Keep edits highly focused, modular, and scoped strictly to the plan.
  - Mark checklist items as in progress `[/]` and completed `[x]` as you proceed.
  - Run build scripts or automated test commands to verify each step.
 
### C. Reviewer & Architect Role
- **Goal**: Ensure exceptional code quality, correctness, and architectural alignment.
- **Workflow**:
  - Verify changes against existing patterns, modules, and structure.
  - Ensure compatibility with VS Code/Copilot Pro, Claude Code, and Antigravity environments.
  - Conduct thorough visual/design audits if UI changes were introduced.
 
### D. Documentation Steward Role
- **Goal**: Keep repository documentation, changelogs, and catalogs up to date.
- **Workflow**:
  - Automatically update `README.md`, `docs/asset-catalog.md`, and `CHANGELOG.md` upon completing implementations.
  - Save any discovered general technical knowledge in `plans/knowledge/` as a standalone markdown file.
  - Maintain a clean, professional, and editorial tone.
 
### E. Feature Builder Role
- **Goal**: Orchestrate the end-to-end delivery lifecycle.
- **Workflow**:
  - Coordinate the transitions: **Planner** (Research & Plan) $\rightarrow$ User Approval $\rightarrow$ **Implementer** (Coding & Testing) $\rightarrow$ **Documentation Steward** (Docs Sync) $\rightarrow$ **Reviewer** (Final Validation & Walkthrough).
  - Generate a walkthrough in the `walkthrough.md` artifact, copy it to `plans/{slug}_walkthrough.md`, and perform the archiving lifecycle:
    1. Move `plans/{slug}_plan.md` to `plans/historyPlans/{slug}_plan.md`.
    2. Move `plans/{slug}_walkthrough.md` to `plans/walkthroughs/{slug}_walkthrough.md`.
    3. Update the entry in `plans/registry.md` to status `Completado` with links to the archived files.
    4. Clean up any other active/temporary review files in the root of `plans/`.

---

## 2. Coding and Design Standards


### Visual Excellence & UI
- **Rich Aesthetics**: Interfaces must be gorgeous, featuring modern HSL tailored colors, dark mode, smooth gradients, subtle animations, and modern typography (e.g., Google Fonts like Inter or Outfit).
- **Vanilla CSS**: Prioritize Vanilla CSS for styling. Avoid TailwindCSS unless explicitly requested by the user.
- **No Placeholders**: Never use placeholder images. If visual assets are needed, invoke the `generate_image` tool to create functioning demonstrations.

### Documentation & Artifact Rules
- **Concise Bullet Points**: Keep bullet points extremely short and punchy to prevent text wrapping.
- **File Links in Artifacts**: Always format file links in markdown using the absolute path syntax: `[filename](file:///absolute/path/to/file)`.
- **Link Text**: Use the file's basename for link text. Do not surround link text with backticks.
  - *Correct*: `[deploy-to-project.sh](file:///path/to/scripts/deploy-to-project.sh)`
  - *Incorrect*: `[\`deploy-to-project.sh\`](file:///path/to/scripts/deploy-to-project.sh)`
- **Alerts**: Strategic use of GitHub alerts (`> [!NOTE]`, `> [!IMPORTANT]`, etc.) to emphasize key decisions, warnings, or constraints. Do not stack them or nest them.

---

## 3. Contribution and Evolution

- Keep all shared assets project-agnostic, portable, and clean.
- Update `CHANGELOG.md` following Semantic Versioning whenever assets are modified.
