# Roadmap

This roadmap captures the next likely directions for `universal-ide-agents` after the VS Code-first baseline.

## Near-term priorities

### Better review workflows

- Expand the reviewer workflow with a stronger report format.
- Add an optional review artifact template for saving findings.
- Tighten the default severity model for shared-asset reviews.

### Planning discipline

- Keep explicit user approval as a hard boundary before implementation.
- Standardize plan handoff files when a workflow spans multiple agents.
- Strengthen verification sections for script and hook changes.

### Hook maturity

- Add documented hook patterns for `before_tool_call`, `after_tool_call`, and `on_complete`.
- Introduce sample hook recipes for logging, policy checks, and safe automation.

### Versioning rules

- Formalize release and tag conventions for new asset additions.
- Define when a change is patch, minor, or major in this repository.

## Later milestones

### Additional editor support

Future support may include other editors or agent runtimes, but it should land only when:
- the asset model is explicit,
- the directory structure is versioned clearly,
- the README and catalog explain the support matrix without ambiguity.

### Tooling expansion

Possible future additions:
- validation scripts for frontmatter and file placement,
- release scripts for tags and changelog updates,
- bootstrap helpers for repo-local overrides.

## Guardrail

Do not claim editor support before the assets, documentation, and installation flow are all present in the repository.