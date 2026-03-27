#!/usr/bin/env sh

set -eu

workspace="${1:-$PWD}"

if [ ! -d "$workspace" ]; then
  echo "Workspace does not exist: $workspace" >&2
  exit 1
fi

detect_stack() {
  stack=""

  [ -f "$workspace/package.json" ] && stack="$stack Node.js"
  [ -f "$workspace/pyproject.toml" ] && stack="$stack Python"
  [ -f "$workspace/requirements.txt" ] && stack="$stack Python"
  [ -f "$workspace/go.mod" ] && stack="$stack Go"
  [ -f "$workspace/Cargo.toml" ] && stack="$stack Rust"
  [ -f "$workspace/pom.xml" ] && stack="$stack Java"

  if [ -n "$stack" ]; then
    printf 'Detected stack:%s\n' "$stack"
  else
    echo "Detected stack: not inferred from common manifests"
  fi
}

echo "Workspace snapshot"
echo "- Name: $(basename -- "$workspace")"
echo "- Path: $workspace"
detect_stack

if [ -f "$workspace/README.md" ]; then
  echo "- README: present"
fi

if [ -d "$workspace/.github" ]; then
  echo "- .github: present"
fi

echo "- Top-level entries:"
find "$workspace" \
  -mindepth 1 \
  -maxdepth 1 \
  ! -name '.git' \
  ! -name 'node_modules' \
  ! -name '.venv' \
  -exec basename {} \; | sort | head -n 12 | sed 's/^/  - /'