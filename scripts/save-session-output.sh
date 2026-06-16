#!/usr/bin/env sh
# save-session-output.sh — Archive plans, walkthroughs and update plans/registry.md

set -eu

PLANS_DIR="plans"
SESSIONS_DIR=".github/sessions"

# 1. Process active plans in plans/ root
active_plans=$(find "$PLANS_DIR" -maxdepth 1 -name "*_plan.md" -type f 2>/dev/null || true)

if [ -n "$active_plans" ]; then
  for plan_path in $active_plans; do
    plan_file=$(basename "$plan_path")
    # Extract slug from filename (e.g. 2026-06-16-reestructuracion-plans_plan.md -> 2026-06-16-reestructuracion-plans)
    slug=$(printf '%s' "$plan_file" | sed 's/_plan\.md$//')
    
    printf '[archive-session] Archiving active plan and reports for: %s\n' "$slug"
    
    # Target directories
    mkdir -p "$PLANS_DIR/historyPlans" "$PLANS_DIR/walkthroughs"
    
    # Archive Plan
    if [ -f "$PLANS_DIR/${slug}_plan.md" ]; then
      mv "$PLANS_DIR/${slug}_plan.md" "$PLANS_DIR/historyPlans/${slug}_plan.md"
      printf '  [archived] plan -> %s/historyPlans/%s_plan.md\n' "$PLANS_DIR" "$slug"
    fi
    
    # Archive Walkthrough
    if [ -f "$PLANS_DIR/${slug}_walkthrough.md" ]; then
      mv "$PLANS_DIR/${slug}_walkthrough.md" "$PLANS_DIR/walkthroughs/${slug}_walkthrough.md"
      printf '  [archived] walkthrough -> %s/walkthroughs/%s_walkthrough.md\n' "$PLANS_DIR" "$slug"
    fi
    
    # Clean up review files
    if [ -f "$PLANS_DIR/${slug}_review.md" ]; then
      rm -f "$PLANS_DIR/${slug}_review.md"
      printf '  [cleaned]  removed active review: %s/%s_review.md\n' "$PLANS_DIR" "$slug"
    fi
    if [ -f "$PLANS_DIR/${slug}_code-review.md" ]; then
      rm -f "$PLANS_DIR/${slug}_code-review.md"
      printf '  [cleaned]  removed active code review: %s/%s_code-review.md\n' "$PLANS_DIR" "$slug"
    fi
    
    # Update status and paths in registry.md
    if [ -f "$PLANS_DIR/registry.md" ]; then
      tmp_reg=$(mktemp)
      sed -e "/$slug/s/\`En Progreso\`/\`Completado\`/g" \
          -e "/$slug/s/plans\/$slug\_plan\.md/plans\/historyPlans\/$slug\_plan\.md/g" \
          -e "/$slug/s/plans\/$slug\_walkthrough\.md/plans\/walkthroughs\/$slug\_walkthrough\.md/g" \
          "$PLANS_DIR/registry.md" > "$tmp_reg"
      mv "$tmp_reg" "$PLANS_DIR/registry.md"
      printf '  [registry] Updated status and links for %s in plans/registry.md\n' "$slug"
    fi
  done
fi

# 2. Legacy check: Process .github/sessions if there are any active folders
if [ -d "$SESSIONS_DIR" ]; then
  latest_session_dir=$(find "$SESSIONS_DIR" -mindepth 1 -maxdepth 1 -type d | xargs ls -td 2>/dev/null | head -n 1 || true)
  if [ -n "$latest_session_dir" ]; then
    slug=$(basename "$latest_session_dir")
    printf '[archive-session] Found legacy active session folder: %s. Moving outputs...\n' "$slug"
    
    mkdir -p "$PLANS_DIR/historyPlans" "$PLANS_DIR/walkthroughs"
    
    if [ -f "$latest_session_dir/plan.md" ]; then
      mv "$latest_session_dir/plan.md" "$PLANS_DIR/historyPlans/${slug}_plan.md"
      printf '  [moved] plan.md -> %s/historyPlans/%s_plan.md\n' "$PLANS_DIR" "$slug"
    fi
    if [ -f "$latest_session_dir/walkthrough.md" ]; then
      mv "$latest_session_dir/walkthrough.md" "$PLANS_DIR/walkthroughs/${slug}_walkthrough.md"
      printf '  [moved] walkthrough.md -> %s/walkthroughs/%s_walkthrough.md\n' "$PLANS_DIR" "$slug"
    fi
    
    # Remove session directory
    rm -rf "$latest_session_dir"
    printf '  [cleaned] removed legacy directory %s\n' "$latest_session_dir"
  fi
fi
