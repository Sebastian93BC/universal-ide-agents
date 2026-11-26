#!/usr/bin/env python3
"""Despliega la capa genérica de universal-ide-agents en un proyecto.

Garantías:

- Escribe **solo** bajo `.agents/`, `.claude/` y `.github/`. Nunca crea, cambia
  ni borra `AGENTS.md`, `CLAUDE.md` ni `GEMINI.md` (lo comprueba antes de terminar).
- Despliega solo lo que piden los perfiles (`--profile`, con `extends`).
- Es idempotente: volver a desplegar con la misma fuente no cambia ningún byte.
- Lleva la cuenta en `.agents/universal-ide-agents.json` (versión, perfiles,
  fecha, archivos desplegados y huella de los archivos raíz). Con ese manifiesto:
  borra lo que desplegó antes y ya no toca, y nunca pisa un archivo que no es
  suyo o que alguien editó (conflicto: no escribe nada, salvo con `--force`).
- `--dry-run` muestra el plan sin escribir.

Uso:
  deploy.py [--dry-run] [--force] [--target all|antigravity,claude,vscode]
            [--profile data-eng-n8n[,otro]] [directorio-del-proyecto]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys

import uia_lib

DEFAULT_PROFILE = "data-eng-base"
ALLOWED_ROOTS = tuple(f"{r}/" for r in uia_lib.TARGET_ROOTS.values())


def parse_args(argv: list[str]) -> argparse.Namespace:
  ap = argparse.ArgumentParser(
      description="Despliega agentes, skills, reglas, hook y plantillas MCP en un proyecto.",
      epilog="Perfiles: " + ", ".join(uia_lib.list_profiles()),
  )
  ap.add_argument("project", nargs="?", default=os.getcwd(), help="Directorio del proyecto (por defecto, el actual).")
  ap.add_argument("--profile", action="append", help=f"Perfil o perfiles separados por coma; repetible. Por defecto {DEFAULT_PROFILE}.")
  ap.add_argument("--target", default="all", help="all, o lista de antigravity, claude, vscode.")
  ap.add_argument("--dry-run", action="store_true", help="Muestra el plan sin escribir nada.")
  ap.add_argument("--force", action="store_true", help="Sobrescribe archivos ajenos o editados (conflictos).")
  ap.add_argument("--clean", action="store_true", help="Compatibilidad: la limpieza de lo desplegado antes ya es el comportamiento por defecto.")
  ap.add_argument("--quiet", action="store_true", help="Solo el resumen.")
  return ap.parse_args(argv)


def parse_targets(value: str) -> list[str]:
  if value == "all":
    return list(uia_lib.TARGETS)
  aliases = {"vscode": "vscode", "copilot": "vscode", "claude": "claude", "antigravity": "antigravity", "gemini": "antigravity"}
  out = []
  for t in value.split(","):
    t = t.strip()
    if t not in aliases:
      raise SystemExit(f"Error: --target desconocido '{t}' (usa all, antigravity, claude, vscode).")
    if aliases[t] not in out:
      out.append(aliases[t])
  return [t for t in uia_lib.TARGETS if t in out]


def load_manifest(project: Path) -> dict | None:
  path = project / uia_lib.MANIFEST_PATH
  if not path.is_file():
    return None
  try:
    return json.loads(path.read_text(encoding="utf-8"))
  except json.JSONDecodeError as exc:
    raise SystemExit(f"Error: {uia_lib.MANIFEST_PATH} no es JSON válido ({exc}); revísalo o bórralo.")


def build_manifest(profiles: list[str], selection: uia_lib.Selection, targets: list[str],
                   files: dict[str, bytes], root_hashes: dict, previous: dict | None, today: str) -> dict:
  manifest = {
      "schemaVersion": "1.0.0",
      "source": "universal-ide-agents",
      "sourceUrl": "https://github.com/Sebastian93BC/universal-ide-agents",
      "version": uia_lib.source_version(),
      "profiles": profiles,
      "resolvedProfiles": selection.resolved,
      "targets": targets,
      "deployedAt": today,
      "rootFiles": root_hashes,
      "files": {rel: uia_lib.sha256(data) for rel, data in sorted(files.items())},
  }
  # Idempotencia: si nada más cambió, se conserva la fecha del despliegue anterior.
  if previous and {k: v for k, v in previous.items() if k != "deployedAt"} == {k: v for k, v in manifest.items() if k != "deployedAt"}:
    manifest["deployedAt"] = previous.get("deployedAt", today)
  return manifest


def atomic_write(path: Path, data: bytes) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  tmp = path.with_name(path.name + ".tmp")
  tmp.write_bytes(data)
  os.replace(tmp, path)


def plan_deploy(project: Path, desired: dict[str, bytes], owned: dict[str, str], force: bool):
  create, update, unchanged, conflicts, delete, kept = [], [], [], [], [], []
  for rel, data in sorted(desired.items()):
    dest = project / rel
    if not dest.exists():
      create.append(rel)
      continue
    if dest.is_dir():
      conflicts.append((rel, "existe una carpeta con ese nombre"))
      continue
    current = uia_lib.sha256(dest.read_bytes())
    if current == uia_lib.sha256(data):
      unchanged.append(rel)
    elif rel in owned and owned[rel] == current:
      update.append(rel)
    elif force:
      update.append(rel)
    elif rel in owned:
      conflicts.append((rel, "editado localmente desde el último despliegue"))
    else:
      conflicts.append((rel, "existe y no lo desplegó universal-ide-agents"))
  for rel, old_hash in sorted(owned.items()):
    if rel in desired:
      continue
    dest = project / rel
    if not dest.is_file():
      continue
    if uia_lib.sha256(dest.read_bytes()) == old_hash or force:
      delete.append(rel)
    else:
      kept.append(rel)
  return create, update, unchanged, conflicts, delete, kept


def remove_empty_dirs(project: Path, rels: list[str]) -> None:
  roots = {project / r for r in uia_lib.TARGET_ROOTS.values()}
  for rel in rels:
    d = (project / rel).parent
    while d not in roots and project in d.parents:
      try:
        d.rmdir()
      except OSError:
        break
      d = d.parent


def main(argv: list[str] | None = None) -> int:
  args = parse_args(sys.argv[1:] if argv is None else argv)
  project = Path(args.project).expanduser().resolve()
  if not project.is_dir():
    print(f"Error: el directorio del proyecto no existe: {project}", file=sys.stderr)
    return 1
  if project == uia_lib.REPO_ROOT:
    print("Error: el destino es el propio universal-ide-agents; aquí se compila con validate_and_build.py.", file=sys.stderr)
    return 1

  profiles = [p.strip() for value in (args.profile or [DEFAULT_PROFILE]) for p in value.split(",") if p.strip()]
  targets = parse_targets(args.target)
  try:
    selection = uia_lib.resolve_profiles(profiles)
  except uia_lib.ProfileError as exc:
    print(f"Error de perfil: {exc}", file=sys.stderr)
    return 1

  files = uia_lib.render(selection, targets)
  bad = [rel for rel in files if not rel.startswith(ALLOWED_ROOTS)]
  if bad:  # salvaguarda: la compilación nunca debe producir rutas fuera de las tres raíces
    print(f"Error interno: rutas fuera de .agents/, .claude/, .github/: {bad}", file=sys.stderr)
    return 1

  previous = load_manifest(project)
  owned = dict((previous or {}).get("files", {}))
  root_before = uia_lib.root_file_hashes(project)
  today = dt.date.today().isoformat()
  manifest = build_manifest(profiles, selection, targets, files, root_before, previous, today)
  manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

  desired = dict(files)
  desired[uia_lib.MANIFEST_PATH] = manifest_bytes
  owned_with_manifest = dict(owned)
  manifest_path = project / uia_lib.MANIFEST_PATH
  if manifest_path.is_file():  # el manifiesto siempre es nuestro
    owned_with_manifest[uia_lib.MANIFEST_PATH] = uia_lib.sha256(manifest_path.read_bytes())

  create, update, unchanged, conflicts, delete, kept = plan_deploy(project, desired, owned_with_manifest, args.force)

  tag = "[dry-run] " if args.dry_run else ""
  print(f"{tag}universal-ide-agents {manifest['version']} -> {project}")
  print(f"{tag}perfiles: {', '.join(profiles)} (resueltos: {', '.join(selection.resolved)}); IDE: {', '.join(targets)}")
  print(f"{tag}{len(selection.agents)} agentes, {len(selection.skills)} skills, {len(selection.rules)} reglas, MCP: {', '.join(sorted(selection.mcp)) or '-'}")
  if not args.quiet:
    for label, items in (("crear", create), ("actualizar", update), ("borrar", delete)):
      for rel in items:
        print(f"{tag}{label:<11}{rel}")
    for rel in kept:
      print(f"{tag}[aviso] se conserva {rel}: ya no lo despliega el perfil, pero está editado localmente")
  if conflicts:
    for rel, why in conflicts:
      print(f"[conflicto] {rel}: {why}", file=sys.stderr)
    print(f"{len(conflicts)} conflicto(s): no se escribió nada. Revisa esos archivos o repite con --force.", file=sys.stderr)
    return 2

  print(f"{tag}resumen: {len(create)} nuevos, {len(update)} actualizados, {len(delete)} borrados, {len(unchanged)} sin cambios")
  if args.dry_run:
    return 0

  for rel in create + update:
    atomic_write(project / rel, desired[rel])
  for rel in delete:
    (project / rel).unlink()
  remove_empty_dirs(project, delete)

  root_after = uia_lib.root_file_hashes(project)
  if root_after != root_before:
    print("Error: AGENTS.md, CLAUDE.md o GEMINI.md cambiaron durante el despliegue.", file=sys.stderr)
    return 3
  if not create and not update and not delete:
    print("Sin cambios: el proyecto ya tenía esta versión y estos perfiles.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
