#!/usr/bin/env python3
"""Motor Periódico Knowledge & Skill Harvester para universal-ide-agents.

Escanea de forma incremental los directorios de proyectos, cursos y memorias configurados
en `harvester/sources.local.json` (o `harvester/sources.example.json`), compara hashes SHA-256
contra `harvester/state.local.json`, pre-evalúa términos sensibles de clientes y genera un
informe de candidatos a generalizar en `harvester/inbox/<YYYY-MM-DD>/harvest_report.md`.
"""

import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent
HARVESTER_DIR = REPO_ROOT / "harvester"
LOCAL_SOURCES = HARVESTER_DIR / "sources.local.json"
EXAMPLE_SOURCES = HARVESTER_DIR / "sources.example.json"
LOCAL_STATE = HARVESTER_DIR / "state.local.json"
SANITIZATION_SCHEMA = HARVESTER_DIR / "schema" / "sanitization_rules.json"

INTERESTING_FILENAME_KEYWORDS = (
    "skill",
    "agent",
    "claude",
    "agents",
    "gemini",
    "memory",
    "arquitectura",
    "fallo",
    "error",
    "standard",
    "rule",
    "instruction",
    "mcp",
    "duck",
    "dagster",
    "dbt",
    "mongo",
)


def load_json(path: Path, default: dict) -> dict:
  if not path.exists():
    return default
  return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
  h = hashlib.sha256()
  with path.open("rb") as f:
    for chunk in iter(lambda: f.read(65536), b""):
      h.update(chunk)
  return h.hexdigest()


def is_candidate_file(file_path: Path, rel_str: str) -> bool:
  if file_path.suffix.lower() not in (".md", ".py", ".json", ".docx", ".txt"):
    return False
  parts_lower = [p.lower() for p in file_path.parts]
  if any(
      skip in parts_lower
      for skip in ("node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build")
  ):
    return False
  if any(dot in parts_lower for dot in (".agents", ".claude", ".github", "memory", "fallos")):
    return True
  name_lower = file_path.name.lower()
  if name_lower in ("claude.md", "agents.md", "gemini.md", ".mcp.json", "mcp_config.json"):
    return True
  return any(kw in rel_str.lower() for kw in INTERESTING_FILENAME_KEYWORDS)


def scan_watch_roots(sources_cfg: dict) -> dict[str, dict]:
  discovered: dict[str, dict] = {}
  for root_entry in sources_cfg.get("watchRoots", []):
    root_id = root_entry["id"]
    category = root_entry.get("category", "projects")
    max_depth = int(root_entry.get("maxDepth", 5))
    exclude_dirs = set(root_entry.get("excludeDirs", []))
    expanded_path = Path(os.path.expanduser(root_entry["path"]))

    try:
      if not expanded_path.exists():
        continue
    except PermissionError:
      print(
          f"[WARN] Sin permiso de lectura para {expanded_path} (ejecuta fuera de sandbox para escanear esta ruta).",
          file=sys.stderr,
      )
      continue

    base_depth = len(expanded_path.parts)
    for dirpath, dirnames, filenames in os.walk(expanded_path):
      current_path = Path(dirpath)
      depth = len(current_path.parts) - base_depth
      if depth >= max_depth:
        dirnames[:] = []
        continue

      dirnames[:] = [
          d
          for d in dirnames
          if d not in exclude_dirs
          and d not in ("node_modules", ".git", ".venv", "venv", "__pycache__")
      ]

      for fname in filenames:
        fpath = current_path / fname
        rel_str = str(fpath.relative_to(expanded_path))
        if not is_candidate_file(fpath, rel_str):
          continue
        try:
          digest = sha256_file(fpath)
          stat = fpath.stat()
        except OSError:
          continue
        discovered[str(fpath)] = {
            "rootId": root_id,
            "category": category,
            "relativePath": rel_str,
            "sha256": digest,
            "sizeBytes": stat.st_size,
            "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }
  return discovered


def check_client_terms(file_path: Path, client_regexes: list[re.Pattern]) -> list[str]:
  if file_path.suffix.lower() not in (".md", ".py", ".json", ".txt"):
    return []
  try:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
  except OSError:
    return []
  found = []
  for rx in client_regexes:
    m = rx.search(text)
    if m:
      found.append(m.group(0))
  return sorted(set(found))


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      "--mark-processed",
      action="store_true",
      help="Actualiza harvester/state.local.json marcando todos los archivos actuales como procesados.",
  )
  parser.add_argument(
      "--init-local-config",
      action="store_true",
      help="Crea harvester/sources.local.json a partir de sources.example.json si no existe.",
  )
  args = parser.parse_args()

  if args.init_local_config and not LOCAL_SOURCES.exists():
    LOCAL_SOURCES.write_text(
        EXAMPLE_SOURCES.read_text(encoding="utf-8"), encoding="utf-8"
    )
    print(f"[OK] Creado {LOCAL_SOURCES.relative_to(REPO_ROOT)}")

  sources_path = LOCAL_SOURCES if LOCAL_SOURCES.exists() else EXAMPLE_SOURCES
  sources_cfg = load_json(sources_path, {"watchRoots": []})
  state_cfg = load_json(LOCAL_STATE, {"schemaVersion": "1.0.0", "scannedFiles": {}})
  sanitization_cfg = load_json(SANITIZATION_SCHEMA, {"forbiddenClientTerms": []})

  client_regexes = [
      re.compile(rf"\b{pat}\b", re.IGNORECASE)
      for pat in sanitization_cfg.get("forbiddenClientTerms", [])
  ]

  previous_files: dict[str, dict] = state_cfg.get("scannedFiles", {})
  current_files = scan_watch_roots(sources_cfg)

  new_items = []
  modified_items = []
  unchanged_count = 0

  for fpath_str, meta in sorted(current_files.items()):
    prev = previous_files.get(fpath_str)
    if prev is None:
      new_items.append((fpath_str, meta))
    elif prev.get("sha256") != meta["sha256"]:
      modified_items.append((fpath_str, meta))
    else:
      unchanged_count += 1

  today_str = datetime.now().strftime("%Y-%m-%d")
  inbox_dir = HARVESTER_DIR / "inbox" / today_str
  inbox_dir.mkdir(parents=True, exist_ok=True)
  report_path = inbox_dir / "harvest_report.md"

  lines = [
      f"# Reporte Incremental del Knowledge Harvester — {today_str}",
      "",
      f"- **Archivos escaneados totales**: `{len(current_files)}`",
      f"- **Archivos nuevos (`NEW`)**: `{len(new_items)}`",
      f"- **Archivos modificados (`MODIFIED`)**: `{len(modified_items)}`",
      f"- **Archivos sin cambios (`UNCHANGED`)**: `{unchanged_count}`",
      "",
      "## 1. Candidatos Detectados (`NEW` y `MODIFIED`)",
      "",
      "| Estado | Categoría | Raíz | Archivo Relativo | Términos de Cliente a Sanitizar |",
      "| :--- | :--- | :--- | :--- | :--- |",
  ]

  for status_label, group in [("NEW", new_items), ("MODIFIED", modified_items)]:
    for fpath_str, meta in group[:250]:
      flagged = check_client_terms(Path(fpath_str), client_regexes)
      flag_str = ", ".join(flagged) if flagged else "Limpio"
      lines.append(
          f"| `{status_label}` | `{meta['category']}` | `{meta['rootId']}` | "
          f"`{meta['relativePath']}` | {flag_str} |"
      )

  lines.extend([
      "",
      "## 2. Protocolo de Consolidación (CREATE / UPDATE / INVALIDATE)",
      "",
      "1. Revisa los archivos `NEW` y `MODIFIED` con el agente `knowledge-harvester`.",
      "2. Abstrae cualquier término listado en la columna **Términos de Cliente a Sanitizar**.",
      "3. Integra el conocimiento en `core/skills/`, `core/rules/` o `core/playbooks/`.",
      "4. Ejecuta `python3 scripts/validate_and_build.py` y luego `python3 scripts/harvest.py --mark-processed`.",
  ])

  report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
  print(
      f"[OK] Escaneo completado: {len(current_files)} archivos "
      f"({len(new_items)} nuevos, {len(modified_items)} modificados, {unchanged_count} sin cambios)."
  )
  print(f"[OK] Reporte generado en: {report_path.relative_to(REPO_ROOT)}")

  if args.mark_processed:
    new_state = {
        "schemaVersion": "1.0.0",
        "lastHarvestAt": datetime.now(tz=timezone.utc).isoformat(),
        "scannedFiles": current_files,
    }
    LOCAL_STATE.write_text(
        json.dumps(new_state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Estado incremental actualizado en: {LOCAL_STATE.relative_to(REPO_ROOT)}")

  return 0


if __name__ == "__main__":
  sys.exit(main())
