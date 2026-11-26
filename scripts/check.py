#!/usr/bin/env python3
"""Verificador único de universal-ide-agents (lo mecánico, sin modelo).

Modo repositorio (por defecto, `make check`):
  core/ válido (YAML, 12k, Mermaid, términos, triggers), compilado sincronizado
  con core/, sin copias de conflicto (`SKILL 2.md`), punteros de una línea,
  tope de líneas de AGENTS.md, `name` de cada skill igual a su carpeta,
  perfiles resolubles, documentos indexados y enlaces vivos, y escáner de
  datos sensibles.

Modo proyecto (`--project DIR`, tras desplegar):
  manifiesto `.agents/universal-ide-agents.json` presente y completo,
  AGENTS.md / CLAUDE.md / GEMINI.md sin cambios respecto al despliegue,
  archivos desplegados presentes e intactos, punteros de una línea, tope de
  AGENTS.md, `name` de skill igual a carpeta y sin copias de conflicto.

Sale con 1 si algo falla. Los avisos no hacen fallar.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

import uia_lib

REPO = uia_lib.REPO_ROOT
POINTER = "@AGENTS.md"
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


class Report:
  def __init__(self) -> None:
    self.failures: list[str] = []
    self.warnings: list[str] = []

  def check(self, title: str, problems: list[str], warnings: list[str] | None = None) -> None:
    for w in warnings or []:
      self.warnings.append(f"{title}: {w}")
      print(f"[AVISO] {title}: {w}")
    if problems:
      for p in problems:
        self.failures.append(f"{title}: {p}")
        print(f"[FALLO] {title}: {p}")
    else:
      print(f"[OK]    {title}")


def max_root_lines() -> int:
  rules = json.loads((REPO / "harvester/schema/sanitization_rules.json").read_text(encoding="utf-8"))
  return int(rules.get("platformLimits", {}).get("rootInstructionMaxLines", 180))


# --- Comprobaciones compartidas ----------------------------------------------

def check_pointers(root: Path, names: list[str], required: bool) -> list[str]:
  problems = []
  for name in names:
    path = root / name
    if not path.is_file():
      if required:
        problems.append(f"falta {name} (debe contener solo '{POINTER}')")
      continue
    if path.read_text(encoding="utf-8").strip() != POINTER:
      lines = len(path.read_text(encoding="utf-8").splitlines())
      problems.append(f"{name} debe ser un puntero de una línea '{POINTER}' (tiene {lines} líneas)")
  return problems


def check_agents_md(root: Path) -> list[str]:
  path = root / "AGENTS.md"
  if not path.is_file():
    return ["falta AGENTS.md"]
  lines = path.read_text(encoding="utf-8").splitlines()
  problems = []
  cap = max_root_lines()
  if len(lines) > cap:
    problems.append(f"AGENTS.md tiene {len(lines)} líneas; el tope es {cap}")
  for i, line in enumerate(lines, 1):
    if re.search(r"\bTODO\b", line):
      problems.append(f"AGENTS.md:{i} contiene TODO")
  return problems


def check_skill_names(root: Path) -> list[str]:
  problems = []
  for top in (".agents", ".claude", ".github"):
    for skill_md in sorted((root / top / "skills").glob("*/SKILL.md")):
      fm = uia_lib.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
      if fm.get("name") != skill_md.parent.name:
        problems.append(f"{skill_md.relative_to(root)}: name '{fm.get('name')}' distinto de la carpeta (el IDE la ignora)")
  return problems


def check_sync_duplicates(root: Path, tops: tuple[str, ...]) -> list[str]:
  found = []
  for top in tops:
    base = root / top
    if not base.exists():
      continue
    for p in base.rglob("*"):
      if ".git" in p.relative_to(root).parts:
        continue
      if uia_lib.is_sync_duplicate(p.name):
        found.append(f"copia de conflicto de sincronización: {p.relative_to(root)}")
  return sorted(found)


# --- Modo repositorio ---------------------------------------------------------

def check_core_valid() -> list[str]:
  sys.path.insert(0, str(REPO / "scripts"))
  import validate_and_build  # noqa: E402

  errors, _ = validate_and_build.validate_core_assets(validate_and_build.load_sanitization_rules())
  return errors


def check_compiled_sync() -> list[str]:
  expected = uia_lib.render(uia_lib.full_selection())
  on_disk = uia_lib.managed_files_on_disk(REPO)
  problems = []
  for rel, data in sorted(expected.items()):
    path = REPO / rel
    if not path.is_file():
      problems.append(f"falta {rel}")
    elif path.read_bytes() != data:
      problems.append(f"{rel} no coincide con core/")
  for rel in sorted(set(on_disk) - set(expected)):
    problems.append(f"{rel} sobra (no sale de core/)")
  # En macOS el disco no distingue mayúsculas; git y Linux (el CI) sí.
  tracked = subprocess.run(["git", "-C", str(REPO), "ls-files", "--", ".agents", ".claude", ".github"],
                           capture_output=True, text=True).stdout.splitlines()
  managed = tuple(f"{uia_lib.TARGET_ROOTS[t]}/{s}/" for t in uia_lib.TARGETS for s in uia_lib.MANAGED_SUBDIRS[t])
  for rel in tracked:
    if (rel.startswith(managed) or rel in uia_lib.MCP_OUTPUTS.values()) and rel not in expected:
      problems.append(f"{rel} está en git pero no sale de core/ (¿mayúsculas distintas?)")
  if problems:
    problems.append("ejecuta: python3 scripts/validate_and_build.py")
  return problems


def check_profiles() -> list[str]:
  problems = []
  assets = uia_lib.inventory()
  for pid in uia_lib.list_profiles():
    try:
      uia_lib.resolve_profiles([pid], assets)
    except uia_lib.ProfileError as exc:
      problems.append(str(exc))
  return problems


def check_docs_indexed() -> tuple[list[str], list[str]]:
  problems = []
  readme = (REPO / "README.md").read_text(encoding="utf-8")
  for doc in sorted((REPO / "docs").glob("*.md")):
    if f"docs/{doc.name}" not in readme:
      problems.append(f"docs/{doc.name} no está enlazado desde README.md")

  sources = [REPO / "README.md", REPO / "AGENTS.md", REPO / "core/mcp/catalog.md", *sorted((REPO / "docs").glob("*.md"))]
  for src in sources:
    text = re.sub(r"```.*?```", "", src.read_text(encoding="utf-8"), flags=re.DOTALL)
    text = re.sub(r"`[^`\n]*`", "", text)  # el código no son enlaces
    for target in LINK_RE.findall(text):
      if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
        if target.startswith("file://"):
          problems.append(f"{src.relative_to(REPO)}: enlace absoluto a disco local {target}")
        continue
      path = (src.parent / target.split("#", 1)[0]).resolve()
      if not path.exists():
        problems.append(f"{src.relative_to(REPO)}: enlace roto {target}")

  catalog = (REPO / "docs/asset-catalog.md").read_text(encoding="utf-8")
  for kind, items in uia_lib.inventory().items():
    for name in items:
      if f"`{name}`" not in catalog:
        problems.append(f"{kind} '{name}' no figura en docs/asset-catalog.md")
  for pid in uia_lib.list_profiles():
    if f"`{pid}`" not in catalog:
      problems.append(f"perfil '{pid}' no figura en docs/asset-catalog.md")
  return problems, []


def check_sensitive() -> tuple[list[str], list[str]]:
  import scan_sensitive

  blocking, informative = scan_sensitive.scan(REPO)
  problems = [f"{rel}:{n}: {kind}" for rel, n, kind, _ in blocking]
  warnings = []
  if informative:
    files = sorted({h[0] for h in informative})
    warnings.append(f"{len(informative)} hallazgos en rutas solo informativas ({len(files)} archivos de plans/); ver scripts/scan_sensitive.py")
  return problems, warnings


def run_repo(report: Report) -> None:
  report.check("core/ válido", check_core_valid())
  report.check("compilado sincronizado con core/", check_compiled_sync())
  report.check("sin copias de conflicto (SKILL 2.md)",
               check_sync_duplicates(REPO, ("core", ".agents", ".claude", ".github", "docs", "scripts", "profiles")))
  report.check("punteros de una línea", check_pointers(REPO, ["CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md"], required=True))
  report.check("AGENTS.md dentro del tope", check_agents_md(REPO))
  report.check("name de skill igual a carpeta", check_skill_names(REPO))
  report.check("perfiles resolubles", check_profiles())
  problems, warnings = check_docs_indexed()
  report.check("documentos indexados y enlaces vivos", problems, warnings)
  problems, warnings = check_sensitive()
  report.check("sin datos sensibles en lo publicado", problems, warnings)


# --- Modo proyecto ------------------------------------------------------------

def run_project(report: Report, project: Path) -> None:
  manifest_path = project / uia_lib.MANIFEST_PATH
  manifest = None
  problems = []
  if not manifest_path.is_file():
    problems.append(f"falta {uia_lib.MANIFEST_PATH}: despliega con scripts/deploy-to-project.sh")
  else:
    try:
      manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
      problems.append(f"{uia_lib.MANIFEST_PATH} no es JSON válido ({exc})")
  if manifest is not None:
    for key in ("version", "profiles", "deployedAt", "rootFiles", "files"):
      if key not in manifest:
        problems.append(f"al manifiesto le falta '{key}'")
  report.check("manifiesto del despliegue", problems)
  if not manifest or problems:
    return

  # Informativo: estos archivos cambian legítimamente (la plantilla los actualiza con
  # copier update y el cliente edita su capa). Solo el propio despliegue debe no tocarlos,
  # y eso lo comprueba deploy.py con su código de salida 3.
  root_now = uia_lib.root_file_hashes(project)
  notes = [
      f"{name} cambió desde el despliegue del {manifest['deployedAt']} (no es un error: lo actualizan la plantilla o el cliente)"
      for name, recorded in manifest["rootFiles"].items()
      if root_now.get(name) != recorded
  ]
  report.check("AGENTS.md, CLAUDE.md y GEMINI.md (informativo)", [], notes)

  missing, edited = [], []
  for rel, digest in manifest["files"].items():
    path = project / rel
    if not path.is_file():
      missing.append(f"falta {rel}")
    elif uia_lib.sha256(path.read_bytes()) != digest:
      edited.append(f"{rel} editado localmente (el próximo despliegue lo marcará como conflicto)")
  report.check(f"archivos desplegados ({len(manifest['files'])})", missing, edited)

  report.check("punteros de una línea", check_pointers(project, ["CLAUDE.md", "GEMINI.md"], required=False))
  report.check("AGENTS.md dentro del tope", check_agents_md(project))
  report.check("name de skill igual a carpeta", check_skill_names(project))
  report.check("sin copias de conflicto (SKILL 2.md)", check_sync_duplicates(project, (".agents", ".claude", ".github")))


def main(argv: list[str] | None = None) -> int:
  ap = argparse.ArgumentParser(description="Verificador único de universal-ide-agents.")
  ap.add_argument("--project", help="Verifica un proyecto donde se desplegó la capa genérica.")
  args = ap.parse_args(argv)
  report = Report()
  if args.project:
    project = Path(args.project).expanduser().resolve()
    print(f"== Verificación del proyecto {project.name} ==")
    run_project(report, project)
  else:
    print("== Verificación de universal-ide-agents ==")
    run_repo(report)
  if report.failures:
    print(f"\n[FALLO] {len(report.failures)} problema(s), {len(report.warnings)} aviso(s).")
    return 1
  print(f"\n[OK] Todo en orden ({len(report.warnings)} aviso(s)).")
  return 0


if __name__ == "__main__":
  sys.exit(main())
