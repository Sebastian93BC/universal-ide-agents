#!/usr/bin/env sh
# deploy-to-project.sh — Deploy universal-ide-agents assets to a consumer project.
#
# This script is the canonical deployment tool and supersedes install-vscode-assets.sh.
# Run with --help for usage and path mapping details.

set -eu

usage() {
  cat <<'EOF'
Usage: deploy-to-project.sh [--dry-run] [--clean] [target-directory]

Deploy the universal-ide-agents VS Code & Antigravity assets into a consumer project.

Path mapping applied during deployment:
  .github/agents/                      -> <target>/.github/agents/
  .github/hooks/                       -> <target>/.github/hooks/
  .github/instructions/                -> <target>/.github/instructions/
  .github/prompts/                     -> <target>/.github/prompts/
  .github/skills/                      -> <target>/.github/skills/
  .github/copilot-instructions.md      -> <target>/.github/copilot-instructions.md
  .github/antigravity-instructions.md  -> <target>/.github/antigravity-instructions.md
  .antigravity-instructions.md         -> <target>/.antigravity-instructions.md
  CLAUDE.md                            -> <target>/CLAUDE.md
  docs/                                -> <target>/.github/docs/
  scripts/                             -> <target>/.github/scripts/

Note: .github/sessions/ is never deployed to preserve the consumer session history.
Instead, the target project's plans/ directory is initialized/scaffolded safely:
  - Creating plans/knowledge/, plans/walkthroughs/, plans/historyPlans/ if not present.
  - Copying plans/README.md standard.
  - Initializing plans/registry.md only if it does not already exist, preserving existing consumer task registry history.

After copying, the hook path inside <target>/.github/hooks/context.json is
rewritten from ./scripts/inject-context.sh to ./.github/scripts/inject-context.sh
so that the hook resolves correctly inside the consumer project.

Options:
  --dry-run   Print the planned operations without writing or deleting any files.
  --clean     Remove files inside managed target directories that no longer exist
              in the source. Only affects the directories listed above.
  --help      Show this help message.

If no target directory is provided, the current working directory is used.

Typical workflow (submodule at .githubconfig/universal-ide-agents/):

  # First-time setup
  git submodule add git@github.com:Sebastian93BC/universal-ide-agents.git \
    .githubconfig/universal-ide-agents

  # Deploy assets
  .githubconfig/universal-ide-agents/scripts/deploy-to-project.sh "$PWD"

  # Preview without writing
  .githubconfig/universal-ide-agents/scripts/deploy-to-project.sh --dry-run "$PWD"

  # Remove obsolete agent files and redeploy
  .githubconfig/universal-ide-agents/scripts/deploy-to-project.sh --clean "$PWD"

  # Update the submodule to the latest main, then redeploy
  git submodule update --remote --merge
  .githubconfig/universal-ide-agents/scripts/deploy-to-project.sh --clean "$PWD"
EOF
}

script_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
target_dir="${PWD}"
dry_run=0
clean=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) dry_run=1 ;;
    --clean)   clean=1 ;;
    --help|-h) usage; exit 0 ;;
    -*)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
    *)
      target_dir="$1"
      ;;
  esac
  shift
done

if [ ! -d "$target_dir" ]; then
  printf 'Error: target directory does not exist: %s\n' "$target_dir" >&2
  exit 1
fi

target_dir=$(CDPATH= cd -- "$target_dir" && pwd)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

deploy_dir() {
  src="$1"
  dst="$2"

  if [ ! -d "$src" ]; then
    printf '[warn]    source directory not found: %s\n' "$src" >&2
    return 0
  fi

  if [ "$dry_run" -eq 1 ]; then
    printf '[dry-run] copy dir   %s -> %s\n' "$src" "$dst"
    return 0
  fi

  mkdir -p "$dst"
  cp -R "$src/." "$dst/"
  printf '[copy]    %s -> %s\n' "$src" "$dst"
}

deploy_file() {
  src="$1"
  dst="$2"

  if [ ! -f "$src" ]; then
    printf '[warn]    source file not found: %s\n' "$src" >&2
    return 0
  fi

  if [ "$dry_run" -eq 1 ]; then
    printf '[dry-run] copy file  %s -> %s\n' "$src" "$dst"
    return 0
  fi

  mkdir -p "$(dirname -- "$dst")"
  cp "$src" "$dst"
  printf '[copy]    %s -> %s\n' "$src" "$dst"
}

rewrite_hook_path() {
  hook_json="$target_dir/.github/hooks/context.json"
  [ -f "$hook_json" ] || return 0

  tmp_file=$(mktemp)
  trap 'rm -f "$tmp_file"' EXIT HUP INT TERM
  sed -e 's|./scripts/inject-context\.sh|./.github/scripts/inject-context.sh|g' \
      -e 's|./scripts/save-session-output\.sh|./.github/scripts/save-session-output.sh|g' \
    "$hook_json" > "$tmp_file" && mv "$tmp_file" "$hook_json"
  printf '[patch]   hook commands -> ./.github/scripts/ (inject-context.sh, save-session-output.sh)\n'
}

clean_dir() {
  src="$1"
  dst="$2"

  [ -d "$dst" ] || return 0

  # Normalize paths by removing trailing slashes to prevent comparison bugs
  src_norm=$(printf '%s' "$src" | sed 's|/*$||')
  dst_norm=$(printf '%s' "$dst" | sed 's|/*$||')

  find "$dst_norm" -type f | while IFS= read -r dst_file; do
    rel="${dst_file#${dst_norm}/}"
    if [ ! -e "$src_norm/$rel" ]; then
      if [ "$dry_run" -eq 1 ]; then
        printf '[dry-run] delete     %s\n' "$dst_file"
      else
        printf '[clean]   delete     %s\n' "$dst_file"
        rm -f "$dst_file"
      fi
    fi
  done
}

scaffold_plans() {
  printf '\n--- scaffolding plans directory ---\n'
  
  if [ "$dry_run" -eq 1 ]; then
    printf '[dry-run] create directories target/plans/{knowledge,walkthroughs,historyPlans}\n'
    if [ ! -f "$target_dir/plans/registry.md" ]; then
      printf '[dry-run] create file target/plans/registry.md\n'
    fi
    printf '[dry-run] copy plans/README.md -> target/plans/README.md\n'
    return 0
  fi

  mkdir -p "$target_dir/plans/knowledge" "$target_dir/plans/walkthroughs" "$target_dir/plans/historyPlans"
  printf '[scaffold] created target/plans/ folders (knowledge, walkthroughs, historyPlans)\n'

  # Copy the README.md standard
  cp "$script_root/plans/README.md" "$target_dir/plans/README.md"
  printf '[scaffold] copied plans/README.md -> target/plans/README.md\n'

  # Create registry.md if not exists, to prevent overwriting consumer registry
  if [ ! -f "$target_dir/plans/registry.md" ]; then
    cat <<'EOF' > "$target_dir/plans/registry.md"
# Registro de Planes y Tareas

Este archivo centraliza el estado y el historial de todas las tareas y planes de desarrollo ejecutados en este repositorio por los agentes de IA (Google Antigravity, Claude Code, Copilot) y desarrolladores humanos.

## Control de Tareas y Estados

| ID | Plan / Tarea | Estado | Creado | Modificado | Enlace al Plan | Enlace al Reporte (Walkthrough) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |

---

## Estados Disponibles
- `En Progreso`: La tarea está siendo activamente investigada, planificada o implementada.
- `Completado`: El plan ha sido ejecutado, verificado y archivado.
- `Pausado`: La tarea está detenida temporalmente a la espera de definiciones o aprobación.
EOF
    printf '[scaffold] initialized target/plans/registry.md (empty)\n'
  else
    printf '[scaffold] target/plans/registry.md already exists. Preserving consumer history.\n'
  fi
}

# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------

deploy_dir  "$script_root/.github/agents"                "$target_dir/.github/agents"
deploy_dir  "$script_root/.github/hooks"                 "$target_dir/.github/hooks"
deploy_dir  "$script_root/.github/instructions"          "$target_dir/.github/instructions"
deploy_dir  "$script_root/.github/prompts"               "$target_dir/.github/prompts"
deploy_dir  "$script_root/.github/skills"                "$target_dir/.github/skills"
deploy_file "$script_root/.github/copilot-instructions.md" \
            "$target_dir/.github/copilot-instructions.md"
deploy_file "$script_root/.github/antigravity-instructions.md" \
            "$target_dir/.github/antigravity-instructions.md"
deploy_file "$script_root/.antigravity-instructions.md" \
            "$target_dir/.antigravity-instructions.md"
deploy_file "$script_root/CLAUDE.md" \
            "$target_dir/CLAUDE.md"
deploy_dir  "$script_root/docs"                          "$target_dir/.github/docs"
deploy_dir  "$script_root/scripts"                       "$target_dir/.github/scripts"
scaffold_plans

if [ "$dry_run" -eq 0 ]; then
  rewrite_hook_path
fi

# ---------------------------------------------------------------------------
# Clean (optional)
# ---------------------------------------------------------------------------

if [ "$clean" -eq 1 ]; then
  printf '\n--- running --clean ---\n'
  clean_dir "$script_root/.github/agents"      "$target_dir/.github/agents"
  clean_dir "$script_root/.github/hooks"       "$target_dir/.github/hooks"
  clean_dir "$script_root/.github/instructions" "$target_dir/.github/instructions"
  clean_dir "$script_root/.github/prompts"     "$target_dir/.github/prompts"
  clean_dir "$script_root/.github/skills"      "$target_dir/.github/skills"
  clean_dir "$script_root/docs"                "$target_dir/.github/docs"
  clean_dir "$script_root/scripts"             "$target_dir/.github/scripts"
fi

printf '\nDeployed universal-ide-agents assets to: %s\n' "$target_dir"
