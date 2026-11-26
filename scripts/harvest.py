#!/usr/bin/env python3
"""Knowledge Harvester: busca conocimiento nuevo para universal-ide-agents en tus carpetas.

Recorre las carpetas que configures (proyectos, cursos, memorias de los IDE),
detecta por SHA-256 los archivos nuevos o cambiados desde la última cosecha,
marca los que contienen términos de cliente y escribe un informe en
`harvester/inbox/<AAAA-MM-DD>/harvest_report.md`. Después el agente
`knowledge-harvester` (modo hub) generaliza lo útil y lo lleva a `core/`.

Configuración (la primera que exista):
  1. `--config RUTA`
  2. la variable de entorno `UIA_HARVEST_CONFIG`
  3. `harvester/sources.local.json` (ignorado por git)

Uso:
  python3 scripts/harvest.py --init            # crea harvester/sources.local.json desde el ejemplo
  python3 scripts/harvest.py --check-config    # muestra qué leería, sin escribir nada
  python3 scripts/harvest.py                   # cosecha y escribe el informe
  python3 scripts/harvest.py --mark-processed  # además, guarda el estado para la próxima vez

Solo biblioteca estándar. Nunca recorre el propio universal-ide-agents.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import sys

import uia_lib

REPO_ROOT = uia_lib.REPO_ROOT
HARVESTER_DIR = REPO_ROOT / "harvester"
LOCAL_SOURCES = HARVESTER_DIR / "sources.local.json"
EXAMPLE_SOURCES = HARVESTER_DIR / "sources.example.json"
LOCAL_STATE = HARVESTER_DIR / "state.local.json"
CONFIG_ENV = "UIA_HARVEST_CONFIG"

DEFAULT_EXTENSIONS = [".md", ".py", ".json", ".txt", ".docx"]
DEFAULT_EXCLUDE_DIRS = ["node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build"]
CATEGORIES = {"projects", "courses", "research", "agent-memory"}


class ConfigError(ValueError):
  pass


# --- Configuración -----------------------------------------------------------

def config_path(cli_value: str | None) -> Path:
  if cli_value:
    return Path(cli_value).expanduser()
  if os.environ.get(CONFIG_ENV):
    return Path(os.environ[CONFIG_ENV]).expanduser()
  return LOCAL_SOURCES


def load_config(path: Path) -> dict:
  """Lee y valida la configuración. Falla con un mensaje que dice qué corregir."""
  if not path.exists():
    raise ConfigError(
        f"No hay configuración en {path}.\n"
        f"  Créala con: python3 scripts/harvest.py --init\n"
        f"  y edita 'watchRoots' con tus carpetas (o usa --config / {CONFIG_ENV})."
    )
  try:
    cfg = json.loads(path.read_text(encoding="utf-8"))
  except json.JSONDecodeError as exc:
    raise ConfigError(f"{path} no es JSON válido: {exc}") from exc

  roots = cfg.get("watchRoots")
  if not isinstance(roots, list) or not roots:
    raise ConfigError(f"{path}: 'watchRoots' debe ser una lista con al menos una carpeta.")
  seen = set()
  for i, root in enumerate(roots):
    where = f"{path}: watchRoots[{i}]"
    for key in ("id", "path"):
      if not isinstance(root.get(key), str) or not root[key].strip():
        raise ConfigError(f"{where} necesita '{key}'.")
    if root["id"] in seen:
      raise ConfigError(f"{where}: id '{root['id']}' repetido.")
    seen.add(root["id"])
    if root.get("category", "projects") not in CATEGORIES:
      raise ConfigError(f"{where}: category debe ser una de {sorted(CATEGORIES)}.")
  # `targetPatterns` es el nombre antiguo de `includePatterns`.
  if "includePatterns" not in cfg and "targetPatterns" in cfg:
    cfg["includePatterns"] = cfg["targetPatterns"]
  return cfg


def init_config() -> int:
  if LOCAL_SOURCES.exists():
    print(f"[info] {show(LOCAL_SOURCES)} ya existe; no se toca.")
    return 0
  LOCAL_SOURCES.write_text(EXAMPLE_SOURCES.read_text(encoding="utf-8"), encoding="utf-8")
  print(f"[OK] Creado {show(LOCAL_SOURCES)} (ignorado por git).")
  print("     Edita 'watchRoots' con tus carpetas y comprueba con: python3 scripts/harvest.py --check-config")
  return 0


# --- Selección de archivos -----------------------------------------------------

def matches(rel: str, pattern: str) -> bool:
  """Glob que vale a cualquier profundidad dentro de la carpeta vigilada.

  Una carpeta vigilada suele contener varios proyectos (`~/Proyectos/a`, `~/Proyectos/b`),
  así que `.claude/**/*.md` debe encontrar `a/.claude/skills/x/SKILL.md`. Se prueba el
  patrón contra la ruta y contra cada sufijo que empieza en una carpeta. '**/' también
  vale para cero carpetas.
  """
  pattern = pattern[3:] if pattern.startswith("**/") else pattern
  parts = rel.split("/")
  return any(fnmatch.fnmatchcase("/".join(parts[i:]), pattern) for i in range(len(parts)))


def show(path: Path) -> str:
  try:
    return str(path.relative_to(REPO_ROOT))
  except ValueError:
    return str(path)


def iter_candidates(root: dict, cfg: dict):
  """Rutas de los archivos que interesan dentro de una carpeta vigilada."""
  base = Path(os.path.expanduser(root["path"]))
  patterns = root.get("includePatterns") or cfg.get("includePatterns") or []
  extensions = [e.lower() for e in (root.get("fileExtensions") or cfg.get("fileExtensions") or DEFAULT_EXTENSIONS)]
  exclude = set(DEFAULT_EXCLUDE_DIRS) | set(cfg.get("excludeDirs", [])) | set(root.get("excludeDirs", []))
  max_depth = int(root.get("maxDepth", 5))
  repo = REPO_ROOT.resolve()
  base_depth = len(base.parts)
  for dirpath, dirnames, filenames in os.walk(base):
    current = Path(dirpath)
    if current.resolve() == repo:  # nunca se cosecha a sí mismo
      dirnames[:] = []
      continue
    if len(current.parts) - base_depth >= max_depth:
      dirnames[:] = []
      continue
    dirnames[:] = [d for d in dirnames if d not in exclude and not (current / d).resolve() == repo]
    for fname in filenames:
      fpath = current / fname
      if fpath.suffix.lower() not in extensions:
        continue
      rel = fpath.relative_to(base).as_posix()
      if patterns and not any(matches(rel, p) for p in patterns):
        continue
      yield fpath, rel


def scan_watch_roots(cfg: dict, warn=print) -> dict[str, dict]:
  discovered: dict[str, dict] = {}
  for root in cfg["watchRoots"]:
    base = Path(os.path.expanduser(root["path"]))
    try:
      if not base.is_dir():
        warn(f"[aviso] '{root['id']}': {base} no existe o no es una carpeta; se omite.")
        continue
    except PermissionError:
      warn(f"[aviso] '{root['id']}': sin permiso de lectura en {base}; se omite.")
      continue
    for fpath, rel in iter_candidates(root, cfg):
      try:
        digest = hashlib.sha256(fpath.read_bytes()).hexdigest()
        stat = fpath.stat()
      except OSError:
        continue
      discovered[str(fpath)] = {
          "rootId": root["id"],
          "category": root.get("category", "projects"),
          "relativePath": rel,
          "sha256": digest,
          "sizeBytes": stat.st_size,
          "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
      }
  return discovered


def client_terms_in(path: Path, regexes) -> list[str]:
  try:
    text = path.read_text(encoding="utf-8", errors="ignore")
  except OSError:
    return []
  return sorted({m.group(0) for rx in regexes for m in [rx.search(text)] if m})


# --- Órdenes ------------------------------------------------------------------

def check_config(cfg: dict, path: Path) -> int:
  rules = uia_lib.load_sanitization_rules()
  print(f"Configuración: {path}")
  print(f"Patrones globales: {', '.join(cfg.get('includePatterns') or []) or '(ninguno: toda extensión admitida)'}")
  print(f"Términos de cliente a marcar: {len(rules.get('forbiddenClientTerms', []))}"
        f" (públicos + {show(uia_lib.SANITIZATION_LOCAL)} si existe)")
  total = 0
  for root in cfg["watchRoots"]:
    base = Path(os.path.expanduser(root["path"]))
    if not base.is_dir():
      print(f"  [falta] {root['id']:<28} {base}")
      continue
    n = sum(1 for _ in iter_candidates(root, cfg))
    total += n
    print(f"  [ok]    {root['id']:<28} {base}  ->  {n} archivos ({root.get('category', 'projects')}, profundidad {root.get('maxDepth', 5)})")
  print(f"Total: {total} archivos candidatos. No se escribió nada.")
  return 0


def harvest(cfg: dict, mark_processed: bool) -> int:
  rules = uia_lib.load_sanitization_rules()
  regexes = uia_lib.client_term_regexes(rules)
  state = json.loads(LOCAL_STATE.read_text(encoding="utf-8")) if LOCAL_STATE.exists() else {"scannedFiles": {}}
  previous = state.get("scannedFiles", {})
  current = scan_watch_roots(cfg, warn=lambda m: print(m, file=sys.stderr))

  new_items, modified_items, unchanged = [], [], 0
  for fpath, meta in sorted(current.items()):
    prev = previous.get(fpath)
    if prev is None:
      new_items.append((fpath, meta))
    elif prev.get("sha256") != meta["sha256"]:
      modified_items.append((fpath, meta))
    else:
      unchanged += 1

  today = datetime.now().strftime("%Y-%m-%d")
  inbox = HARVESTER_DIR / "inbox" / today
  inbox.mkdir(parents=True, exist_ok=True)
  report = inbox / "harvest_report.md"
  lines = [
      f"# Informe del Knowledge Harvester — {today}",
      "",
      f"- Archivos revisados: `{len(current)}`",
      f"- Nuevos (`NEW`): `{len(new_items)}`",
      f"- Modificados (`MODIFIED`): `{len(modified_items)}`",
      f"- Sin cambios: `{unchanged}`",
      "",
      "## 1. Candidatos (`NEW` y `MODIFIED`)",
      "",
      "| Estado | Categoría | Raíz | Archivo | Términos de cliente a sanear |",
      "| :--- | :--- | :--- | :--- | :--- |",
  ]
  for label, group in (("NEW", new_items), ("MODIFIED", modified_items)):
    for fpath, meta in group[:250]:
      flagged = client_terms_in(Path(fpath), regexes)
      lines.append(f"| `{label}` | `{meta['category']}` | `{meta['rootId']}` | `{meta['relativePath']}` | {', '.join(flagged) or 'Limpio'} |")
  lines += [
      "",
      "## 2. Qué hacer con este informe",
      "",
      "1. Revisa los candidatos con el agente `knowledge-harvester` (modo hub).",
      "2. Sanea todo término marcado en la última columna.",
      "3. Lleva lo genérico a `core/skills/`, `core/rules/` o `core/playbooks/`.",
      "4. `make check` y después `python3 scripts/harvest.py --mark-processed`.",
  ]
  report.write_text("\n".join(lines) + "\n", encoding="utf-8")
  print(f"[OK] {len(current)} archivos ({len(new_items)} nuevos, {len(modified_items)} modificados, {unchanged} sin cambios).")
  print(f"[OK] Informe: {show(report)}")

  if mark_processed:
    LOCAL_STATE.write_text(json.dumps({
        "schemaVersion": "1.0.0",
        "lastHarvestAt": datetime.now(tz=timezone.utc).isoformat(),
        "scannedFiles": current,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Estado guardado en {show(LOCAL_STATE)}")
  return 0


def main(argv: list[str] | None = None) -> int:
  ap = argparse.ArgumentParser(description="Busca conocimiento nuevo en tus carpetas para universal-ide-agents.")
  ap.add_argument("--config", help=f"Archivo de configuración (por defecto ${CONFIG_ENV} o harvester/sources.local.json).")
  ap.add_argument("--init", "--init-local-config", dest="init", action="store_true", help="Crea harvester/sources.local.json desde el ejemplo.")
  ap.add_argument("--check-config", action="store_true", help="Muestra qué carpetas y cuántos archivos leería, sin escribir nada.")
  ap.add_argument("--mark-processed", action="store_true", help="Guarda el estado para que la próxima cosecha solo informe de cambios.")
  args = ap.parse_args(argv)
  if args.init:
    return init_config()
  path = config_path(args.config)
  try:
    cfg = load_config(path)
  except ConfigError as exc:
    print(f"[error] {exc}", file=sys.stderr)
    return 2
  if args.check_config:
    return check_config(cfg, path)
  return harvest(cfg, args.mark_processed)


if __name__ == "__main__":
  sys.exit(main())
