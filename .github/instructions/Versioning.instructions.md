---
applyTo: CHANGELOG.md
description: Guidelines for versioning, tags, and updating the CHANGELOG.md file.
---

# Versioning & CHANGELOG Guidelines

Whenever you modify `CHANGELOG.md` or determine the next version of this repository, you must adhere to the following rules:

## 1. Versioning Rules (Semantic Versioning)
We follow standard Semantic Versioning (`vMAJOR.MINOR.PATCH`):
- **PATCH (`+0.0.1`)**: Backward-compatible bug fixes, minor prompt tweaks, documentation typos, or small script corrections.
- **MINOR (`+0.1.0`)**: Backward-compatible new features, such as adding a new agent, a new prompt file, or new modular instructions.
- **MAJOR (`+1.0.0`)**: Backward-incompatible API changes, directory restructurings, or breaking changes in hook execution models.

All tags must be prefixed with a `v` (e.g., `v0.1.2`).

## 2. CHANGELOG Format
We follow the "Keep a Changelog" convention. 

### Structure
The changelog contains:
- A header `# Changelog`.
- Grouped changes under version headers.
- An `## [Unreleased]` section at the top of the version list for changes that haven't been published in a release tag yet.
- Grouping headers under each version:
  - `### Added` for new features.
  - `### Changed` for changes in existing functionality.
  - `### Deprecated` for soon-to-be-removed features.
  - `### Removed` for now-removed features.
  - `### Fixed` for any bug fixes.
  - `### Security` in case of vulnerabilities.

### Writing Entries
- Keep entries clear, concise, and focused on the *value* to the user or developer consuming these agents.
- Reference changed files in markdown links where appropriate.
- Never use generic messages like "updated prompts". Instead, use "Refactored Reviewer.agent.md to separate code quality checks into Code Reviewer".
