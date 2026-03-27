#!/usr/bin/env sh

set -eu

usage() {
  cat <<'EOF'
Usage: install-vscode-assets.sh [--dry-run] [--force] [target-directory]

Copy the shared VS Code assets from this repository into a target workspace.

Options:
  --dry-run   Show what would be copied without modifying files
  --force     Replace existing files with the shared version
  --help      Show this help message

If no target directory is provided, the current working directory is used.
EOF
}

script_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
target_dir="${PWD}"
dry_run=0
force=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      dry_run=1
      ;;
    --force)
      force=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      target_dir="$1"
      ;;
  esac
  shift
done

if [ ! -d "$target_dir" ]; then
  echo "Target directory does not exist: $target_dir" >&2
  exit 1
fi

copy_dir() {
  src="$1"
  dst="$2"

  if [ "$dry_run" -eq 1 ]; then
    echo "[dry-run] directory  $src -> $dst"
    return 0
  fi

  mkdir -p "$dst"

  if [ "$force" -eq 1 ]; then
    cp -R "$src/." "$dst/"
  else
    cp -Rn "$src/." "$dst/"
  fi
}

copy_file() {
  src="$1"
  dst="$2"

  if [ "$dry_run" -eq 1 ]; then
    echo "[dry-run] file       $src -> $dst"
    return 0
  fi

  mkdir -p "$(dirname -- "$dst")"

  if [ "$force" -eq 1 ] || [ ! -e "$dst" ]; then
    cp "$src" "$dst"
  else
    echo "[skip] existing file $dst"
  fi
}

copy_dir "$script_root/.github/agents" "$target_dir/.github/agents"
copy_dir "$script_root/.github/hooks" "$target_dir/.github/hooks"
copy_dir "$script_root/.github/instructions" "$target_dir/.github/instructions"
copy_dir "$script_root/.github/prompts" "$target_dir/.github/prompts"
copy_dir "$script_root/.github/skills" "$target_dir/.github/skills"
copy_file "$script_root/.github/copilot-instructions.md" "$target_dir/.github/copilot-instructions.md"

echo "VS Code assets installed into: $target_dir"