#!/usr/bin/env sh
# deploy-to-project.sh — Deploy universal-ide-agents assets to a consumer project.
#
# This script is the canonical deployment tool and supersedes install-vscode-assets.sh.
# Run with --help for usage and path mapping details.

set -eu

usage() {
  cat <<'EOF'
Usage: deploy-to-project.sh [--dry-run] [--clean] [target-directory]

Deploy the universal-ide-agents VS Code assets into a consumer project.

Path mapping applied during deployment:
  .github/agents/                  -> <target>/.github/agents/
  .github/hooks/                   -> <target>/.github/hooks/
  .github/instructions/            -> <target>/.github/instructions/
  .github/prompts/                 -> <target>/.github/prompts/
  .github/skills/                  -> <target>/.github/skills/
  .github/copilot-instructions.md  -> <target>/.github/copilot-instructions.md
  docs/                            -> <target>/.github/docs/
  scripts/                         -> <target>/.github/scripts/

Note: .github/sessions/ is never deployed to preserve the consumer session history.

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
  sed 's|./scripts/inject-context\.sh|./.github/scripts/inject-context.sh|g' \
    "$hook_json" > "$tmp_file" && mv "$tmp_file" "$hook_json"
  printf '[patch]   hook command -> ./.github/scripts/inject-context.sh\n'
}

clean_dir() {
  src="$1"
  dst="$2"

  [ -d "$dst" ] || return 0

  find "$dst" -type f | while IFS= read -r dst_file; do
    rel="${dst_file#${dst}/}"
    if [ ! -e "$src/$rel" ]; then
      if [ "$dry_run" -eq 1 ]; then
        printf '[dry-run] delete     %s\n' "$dst_file"
      else
        printf '[clean]   delete     %s\n' "$dst_file"
        rm "$dst_file"
      fi
    fi
  done
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
deploy_dir  "$script_root/docs"                          "$target_dir/.github/docs"
deploy_dir  "$script_root/scripts"                       "$target_dir/.github/scripts"

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
