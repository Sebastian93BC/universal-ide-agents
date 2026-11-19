#!/usr/bin/env python3
"""Validador y Compilador Multi-IDE para universal-ide-agents.

Responsabilidades:
1. Validar todos los activos canónicos en `core/` (agents, skills, rules, playbooks, mcp):
   - Frontmatter YAML válido (`name`, `description`).
   - Límite de longitud de Antigravity (<= 12,000 caracteres por archivo SKILL.md / rule / agent).
   - Prohibición estricta de diagramas Mermaid (```mermaid).
   - Ausencia de términos prohibidos de clientes, rutas personales (/Users/...) y secretos hardcodeados
     (a menos que sea el archivo de configuración de reglas de sanitización).
2. Compilar / Sincronizar hacia los 3 ecosistemas destino:
   - `.agents/` (Google Antigravity / Gemini CLI: `.agents/skills/`, `.agents/rules/`, `.agents/agents/`, `.agents/mcp_config.example.json`)
   - `.claude/` (Claude Code: `.claude/skills/`, `.claude/agents/`, `.claude/rules/`, `.claude/settings.example.json`)
   - `.github/` (VS Code GitHub Copilot: `.github/agents/`, `.github/skills/`, `.github/instructions/`, manteniendo retrocompatibilidad con los agentes y hooks existentes)
"""

import argparse
import json
from pathlib import Path
import re
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = REPO_ROOT / "core"
SCHEMA_FILE = REPO_ROOT / "harvester" / "schema" / "sanitization_rules.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
MERMAID_RE = re.compile(r"```\s*mermaid\b", re.IGNORECASE)


def parse_frontmatter(text: str) -> dict[str, str]:
  match = FRONTMATTER_RE.match(text)
  if not match:
    return {}
  fm_text = match.group(1)
  data: dict[str, str] = {}
  for line in fm_text.splitlines():
    if ":" in line:
      key, val = line.split(":", 1)
      data[key.strip()] = val.strip().strip('"').strip("'")
  return data


def load_sanitization_rules() -> dict:
  if not SCHEMA_FILE.exists():
    return {
        "platformLimits": {"antigravityMaxSkillChars": 12000},
        "forbiddenClientTerms": [],
        "forbiddenSecretPatterns": [],
        "forbiddenPathPatterns": [],
    }
  return json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))


def validate_core_assets(rules: dict) -> tuple[list[str], dict[str, int]]:
  errors: list[str] = []
  max_chars = rules.get("platformLimits", {}).get("antigravityMaxSkillChars", 12000)

  client_regexes = [
      re.compile(rf"\b{pat}\b", re.IGNORECASE)
      for pat in rules.get("forbiddenClientTerms", [])
  ]
  secret_regexes = [
      re.compile(pat) for pat in rules.get("forbiddenSecretPatterns", [])
  ]
  path_regexes = [
      re.compile(pat) for pat in rules.get("forbiddenPathPatterns", [])
  ]

  counts = {"agents": 0, "skills": 0, "rules": 0, "playbooks": 0}

  # 1. Validate Agents
  for agent_file in sorted((CORE_DIR / "agents").rglob("*.agent.md")):
    counts["agents"] += 1
    _validate_markdown_file(
        agent_file,
        kind="agent",
        max_chars=max_chars,
        client_regexes=client_regexes,
        secret_regexes=secret_regexes,
        path_regexes=path_regexes,
        errors=errors,
    )

  # 2. Validate Skills
  for skill_file in sorted((CORE_DIR / "skills").rglob("SKILL.md")):
    counts["skills"] += 1
    fm = _validate_markdown_file(
        skill_file,
        kind="skill",
        max_chars=max_chars,
        client_regexes=client_regexes,
        secret_regexes=secret_regexes,
        path_regexes=path_regexes,
        errors=errors,
    )
    expected_name = skill_file.parent.name
    if fm.get("name") and fm["name"] != expected_name:
      errors.append(
          f"[{skill_file.relative_to(REPO_ROOT)}] frontmatter name '{fm['name']}' "
          f"no coincide con carpeta '{expected_name}'."
      )

  # 3. Validate Rules
  for rule_file in sorted((CORE_DIR / "rules").rglob("*.rule.md")):
    counts["rules"] += 1
    _validate_markdown_file(
        rule_file,
        kind="rule",
        max_chars=max_chars,
        client_regexes=client_regexes,
        secret_regexes=secret_regexes,
        path_regexes=path_regexes,
        errors=errors,
    )

  # 4. Validate Playbooks
  for pb_file in sorted((CORE_DIR / "playbooks").rglob("*.md")):
    counts["playbooks"] += 1
    _validate_markdown_file(
        pb_file,
        kind="playbook",
        max_chars=max_chars * 3,
        client_regexes=client_regexes,
        secret_regexes=secret_regexes,
        path_regexes=path_regexes,
        errors=errors,
        require_frontmatter=False,
    )

  return errors, counts


def _validate_markdown_file(
    path: Path,
    kind: str,
    max_chars: int,
    client_regexes: list[re.Pattern],
    secret_regexes: list[re.Pattern],
    path_regexes: list[re.Pattern],
    errors: list[str],
    require_frontmatter: bool = True,
) -> dict[str, str]:
  rel = path.relative_to(REPO_ROOT)
  text = path.read_text(encoding="utf-8")

  if len(text) > max_chars:
    errors.append(
        f"[{rel}] Excede límite de {max_chars} caracteres ({len(text)} chars)."
    )

  if MERMAID_RE.search(text):
    errors.append(
        f"[{rel}] Contiene bloque Mermaid prohibido. Usa SVG o tablas Markdown."
    )

  fm: dict[str, str] = {}
  if require_frontmatter:
    fm = parse_frontmatter(text)
    if not fm.get("name") or not fm.get("description"):
      errors.append(
          f"[{rel}] Frontmatter YAML incompleto: requiere 'name' y 'description'."
      )

  # Skip client term check on the knowledge-harvester skill if it only documents examples?
  # Even better: enforce zero client terms across ALL core/ files!
  for rx in client_regexes:
    m = rx.search(text)
    if m:
      errors.append(
          f"[{rel}] Contiene término de cliente prohibido: '{m.group(0)}'."
      )

  for rx in secret_regexes:
    m = rx.search(text)
    if m:
      errors.append(
          f"[{rel}] Posible credencial o URI con secreto detectada: '{m.group(0)}'."
      )

  for rx in path_regexes:
    m = rx.search(text)
    if m:
      errors.append(
          f"[{rel}] Contiene ruta local absoluta prohibida: '{m.group(0)}'."
      )

  return fm


def build_multi_ide_targets() -> None:
  """Compila los activos de core/ hacia .agents/, .claude/ y .github/."""
  agents_dir = REPO_ROOT / ".agents"
  claude_dir = REPO_ROOT / ".claude"
  github_dir = REPO_ROOT / ".github"

  # Prepare target subdirectories (clean all managed compiled folders before copy)
  for target_sub in [
      agents_dir / "skills",
      agents_dir / "rules",
      agents_dir / "agents",
      claude_dir / "skills",
      claude_dir / "rules",
      claude_dir / "agents",
      github_dir / "skills",
      github_dir / "instructions",
      github_dir / "agents",
  ]:
    if target_sub.exists():
      shutil.rmtree(target_sub)
    target_sub.mkdir(parents=True, exist_ok=True)

  # 1. Compile Skills (<skill-name>/SKILL.md + scripts/ + references/)
  for skill_file in sorted((CORE_DIR / "skills").rglob("SKILL.md")):
    skill_src_dir = skill_file.parent
    skill_name = skill_src_dir.name
    for dest_root in [
        agents_dir / "skills" / skill_name,
        claude_dir / "skills" / skill_name,
        github_dir / "skills" / skill_name,
    ]:
      shutil.copytree(skill_src_dir, dest_root, dirs_exist_ok=True)

  # 2. Compile Agents
  for agent_file in sorted((CORE_DIR / "agents").rglob("*.agent.md")):
    base_name = agent_file.name.replace(".agent.md", "")
    content = agent_file.read_text(encoding="utf-8")

    # .agents/agents/<name>.md
    (agents_dir / "agents" / f"{base_name}.md").write_text(
        content, encoding="utf-8"
    )
    # .claude/agents/<name>.md
    (claude_dir / "agents" / f"{base_name}.md").write_text(
        content, encoding="utf-8"
    )
    # .github/agents/<name>.agent.md
    (github_dir / "agents" / f"{base_name}.agent.md").write_text(
        content, encoding="utf-8"
    )

  # 3. Compile Rules / Instructions
  for rule_file in sorted((CORE_DIR / "rules").rglob("*.rule.md")):
    base_name = rule_file.name.replace(".rule.md", "")
    content = rule_file.read_text(encoding="utf-8")

    # .agents/rules/<name>.md
    (agents_dir / "rules" / f"{base_name}.md").write_text(
        content, encoding="utf-8"
    )
    # .claude/rules/<name>.md
    (claude_dir / "rules" / f"{base_name}.md").write_text(
        content, encoding="utf-8"
    )
    # .github/instructions/<name>.instructions.md
    (github_dir / "instructions" / f"{base_name}.instructions.md").write_text(
        content, encoding="utf-8"
    )

  # 4. Copy MCP Template Examples
  mcp_template = CORE_DIR / "mcp" / "templates" / "data-eng-full.mcp.json"
  if mcp_template.exists():
    shutil.copy2(mcp_template, agents_dir / "mcp_config.example.json")
    shutil.copy2(mcp_template, claude_dir / "mcp.example.json")


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      "--check-only",
      action="store_true",
      help="Solo validar core/ sin recompilar .agents/, .claude/ y .github/",
  )
  args = parser.parse_args()

  rules = load_sanitization_rules()
  errors, counts = validate_core_assets(rules)

  print(
      f"=== Validación de core/: {counts['agents']} agentes, "
      f"{counts['skills']} skills, {counts['rules']} reglas, "
      f"{counts['playbooks']} playbooks ==="
  )

  if errors:
    print(f"\n[FALLO] Se detectaron {len(errors)} errores de validación:", file=sys.stderr)
    for err in errors:
      print(f"  - {err}", file=sys.stderr)
    return 1

  print("[OK] Todos los activos en core/ cumplen YAML, límites <=12k chars, cero Mermaid y cero términos prohibidos.")

  if not args.check_only:
    build_multi_ide_targets()
    print("[OK] Activos compilados exitosamente hacia .agents/, .claude/ y .github/.")

  return 0


if __name__ == "__main__":
  sys.exit(main())
