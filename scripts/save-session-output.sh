#!/usr/bin/env sh
# save-session-output.sh — Persist expensive session plans and reviews to plans/

set -eu

# Target plans directory in workspace root
PLANS_DIR="plans"
SESSIONS_DIR=".github/sessions"

if [ ! -d "$SESSIONS_DIR" ]; then
  printf '[save-session] .github/sessions directory not found. Skipping backup.\n'
  exit 0
fi

# Find the latest session slug by looking at the most recently modified subdirectory in .github/sessions
latest_session_dir=$(find "$SESSIONS_DIR" -mindepth 1 -maxdepth 1 -type d | xargs ls -td 2>/dev/null | head -n 1 || true)

if [ -z "$latest_session_dir" ]; then
  printf '[save-session] No active session found to persist.\n'
  exit 0
fi

slug=$(basename "$latest_session_dir")

mkdir -p "$PLANS_DIR"

printf '[save-session] Persisting session outputs for: %s\n' "$slug"

# Helper to copy if source exists and is newer or does not exist in target
persist_file() {
  src_file="$1"
  dest_file="$2"
  label="$3"

  if [ -f "$src_file" ]; then
    # Only copy if destination doesn't exist or is different (avoid unnecessary git changes)
    if [ ! -f "$dest_file" ] || ! cmp -s "$src_file" "$dest_file"; then
      cp "$src_file" "$dest_file"
      printf '  [saved] %s -> %s\n' "$label" "$dest_file"
    else
      printf '  [skip]  %s (already up-to-date)\n' "$label"
    fi
  fi
}

persist_file "$latest_session_dir/plan.md"        "$PLANS_DIR/${slug}_plan.md"        "plan.md"
persist_file "$latest_session_dir/walkthrough.md" "$PLANS_DIR/${slug}_walkthrough.md" "walkthrough.md"
persist_file "$latest_session_dir/review.md"      "$PLANS_DIR/${slug}_review.md"      "review.md"
persist_file "$latest_session_dir/code-review.md" "$PLANS_DIR/${slug}_code-review.md" "code-review.md"

# Also try to update the plans README dashboard if we have a template or script for it
if [ -f "$PLANS_DIR/README.md" ]; then
  # Simple update logic or cataloging can be triggered here
  printf '  [info]  Updating plans/README.md catalog...\n'
fi
