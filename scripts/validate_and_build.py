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

import uia_lib


REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = REPO_ROOT / "core"
SCHEMA_FILE = REPO_ROOT / "harvester" / "schema" / "sanitization_rules.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
MERMAID_RE = re.compile(r"```\s*mermaid\b", re.IGNORECASE)
VALID_TRIGGERS = {"always_on", "model_decision", "glob", "manual"}


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
  rules = uia_lib.load_sanitization_rules()
  rules.setdefault("platformLimits", {"antigravityMaxSkillChars": 12000})
  return rules


def validate_core_assets(rules: dict) -> tuple[list[str], dict[str, int]]:
  errors: list[str] = []
  max_chars = rules.get("platformLimits", {}).get("antigravityMaxSkillChars", 12000)

  client_regexes = uia_lib.client_term_regexes(rules)
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

  # 3b. Triggers válidos (Antigravity descarta en silencio una regla sin trigger válido)
  for rule_file in sorted((CORE_DIR / "rules").rglob("*.rule.md")):
    fm = parse_frontmatter(rule_file.read_text(encoding="utf-8"))
    rel = rule_file.relative_to(REPO_ROOT)
    trigger = fm.get("trigger")
    if trigger not in VALID_TRIGGERS:
      errors.append(f"[{rel}] trigger '{trigger}' no válido; usa uno de {sorted(VALID_TRIGGERS)}.")
    elif trigger == "glob" and not (fm.get("globs") or fm.get("glob")):
      errors.append(f"[{rel}] trigger 'glob' exige 'globs'.")

  # 3c. Nombres únicos entre categorías (el compilado los aplana por nombre)
  for kind, pattern, suffix in (("agente", "agents/*/*.agent.md", ".agent.md"),
                                ("skill", "skills/*/*/SKILL.md", None),
                                ("regla", "rules/*/*.rule.md", ".rule.md")):
    seen: dict[str, Path] = {}
    for f in sorted(CORE_DIR.glob(pattern)):
      name = f.parent.name if suffix is None else f.name[: -len(suffix)]
      if name in seen:
        errors.append(f"[{f.relative_to(REPO_ROOT)}] {kind} '{name}' repetido (ya está en {seen[name].relative_to(REPO_ROOT)}).")
      seen[name] = f

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


def build_multi_ide_targets() -> int:
  """Compila todo core/ (incluidos los activos del hub) hacia .agents/, .claude/ y .github/.

  Usa la misma función de compilación que deploy.py, así lo desplegado en un
  proyecto es idéntico a lo compilado aquí. Sincroniza por diferencias: solo
  escribe lo que cambió y borra lo que sobra (incluidas las copias de conflicto
  de iCloud, "SKILL 2.md"). No borra y recrea carpetas enteras, porque en un
  Escritorio sincronizado eso es lo que genera esas copias.
  """
  files = uia_lib.render(uia_lib.full_selection())
  written = 0
  for rel, data in sorted(files.items()):
    dest = REPO_ROOT / rel
    if dest.is_file() and dest.read_bytes() == data:
      continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
    written += 1

  removed = 0
  for rel, path in uia_lib.managed_files_on_disk(REPO_ROOT).items():
    if rel not in files:
      path.unlink()
      removed += 1
  for target in uia_lib.TARGETS:
    for sub in uia_lib.MANAGED_SUBDIRS[target]:
      base = REPO_ROOT / uia_lib.TARGET_ROOTS[target] / sub
      if base.is_dir():
        for d in sorted((p for p in base.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
          if not any(d.iterdir()):
            d.rmdir()
  print(f"[info] {written} archivos escritos, {removed} sobrantes borrados.")
  return len(files)


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
    n_files = build_multi_ide_targets()
    print(f"[OK] {n_files} archivos compilados hacia .agents/, .claude/ y .github/.")

  return 0


if __name__ == "__main__":
  sys.exit(main())
