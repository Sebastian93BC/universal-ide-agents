#!/usr/bin/env python3
"""Escáner de datos sensibles para lo que publica universal-ide-agents.

El repositorio es público y se despliega en proyectos de varios clientes: nada
de lo que se commitea puede llevar correos, URLs de tenant, GUID, cadenas con
forma de token, cadenas de conexión con credenciales, rutas personales ni
nombres de cliente.

Revisa los archivos versionados y los nuevos no ignorados (`git ls-files`),
salvo los excluidos en `harvester/schema/sanitization_rules.json`
(`sensitiveScan`). Las rutas de `reportOnlyPaths` se revisan e informan, pero no
hacen fallar el escáner.

Uso: scan_sensitive.py [--root DIR] [--strict-all] [archivos...]
Sale con 1 si hay hallazgos en rutas que bloquean.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

import uia_lib

REPO_ROOT = Path(__file__).resolve().parent.parent
RULES_FILE = REPO_ROOT / "harvester" / "schema" / "sanitization_rules.json"

BUILTIN_PATTERNS: list[tuple[str, str, int]] = [
    ("correo", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b", 0),
    ("url-tenant", r"\b[A-Za-z0-9-]+\.(?:sharepoint\.com|onmicrosoft\.com|atlassian\.net|app\.n8n\.cloud|n8n\.cloud|mongodb\.net|my\.salesforce\.com|zendesk\.com|slack\.com)\b", re.IGNORECASE),
    ("url-tenant", r"login\.microsoftonline\.com/[0-9a-fA-F-]{36}", 0),
    ("guid", r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", 0),
    ("token", r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b", 0),
    ("token", r"\bgithub_pat_[A-Za-z0-9_]{40,}\b", 0),
    ("token", r"\bglpat-[A-Za-z0-9_-]{20,}\b", 0),
    ("token", r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}\b", 0),
    ("token", r"\bAIza[0-9A-Za-z_-]{35}\b", 0),
    ("token", r"\bAKIA[0-9A-Z]{16}\b", 0),
    ("token", r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b", 0),
    ("token", r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", 0),
    ("clave-privada", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", 0),
]

BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".docx", ".xlsx", ".pptx", ".parquet", ".duckdb"}


def load_rules() -> dict:
  return uia_lib.load_sanitization_rules()


def compile_patterns(rules: dict) -> list[tuple[str, re.Pattern]]:
  pats = [(name, re.compile(rx, flags)) for name, rx, flags in BUILTIN_PATTERNS]
  pats += [("credencial-en-uri", re.compile(rx)) for rx in rules.get("forbiddenSecretPatterns", [])]
  pats += [("ruta-personal", re.compile(rx)) for rx in rules.get("forbiddenPathPatterns", [])]
  pats += [("cliente", rx) for rx in uia_lib.client_term_regexes(rules)]
  return pats


def git_files(root: Path) -> list[str]:
  out = subprocess.run(
      ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
      capture_output=True, check=True,
  ).stdout.decode("utf-8")
  return sorted({f for f in out.split("\0") if f})


def _allowed(kind: str, text: str, cfg: dict) -> bool:
  if kind == "correo":
    domain = text.rsplit("@", 1)[-1].lower()
    return text.lower() in {e.lower() for e in cfg.get("allowedEmails", [])} or domain in cfg.get("allowedEmailDomains", [])
  return any(re.fullmatch(a, text) for a in cfg.get("allowedMatches", []))


def scan_file(path: Path, rel: str, patterns, cfg: dict) -> list[tuple[str, int, str, str]]:
  if path.suffix.lower() in BINARY_SUFFIXES or not path.is_file():
    return []
  try:
    text = path.read_text(encoding="utf-8")
  except UnicodeDecodeError:
    return []
  hits = []
  for lineno, line in enumerate(text.splitlines(), 1):
    for kind, rx in patterns:
      for m in rx.finditer(line):
        if not _allowed(kind, m.group(0), cfg):
          hits.append((rel, lineno, kind, m.group(0)))
  return hits


def scan(root: Path, files: list[str] | None = None, strict_all: bool = False) -> tuple[list, list]:
  """Devuelve (hallazgos que bloquean, hallazgos solo informativos)."""
  rules = load_rules()
  cfg = rules.get("sensitiveScan", {})
  patterns = compile_patterns(rules)
  exclude = set(cfg.get("excludePaths", []))
  report_only = tuple(cfg.get("reportOnlyPaths", []))
  blocking, informative = [], []
  for rel in files if files is not None else git_files(root):
    if rel in exclude:
      continue
    hits = scan_file(root / rel, rel, patterns, cfg)
    if not strict_all and rel.startswith(report_only):
      informative += hits
    else:
      blocking += hits
  return blocking, informative


def _mask(kind: str, value: str) -> str:
  if kind in {"token", "credencial-en-uri", "clave-privada"} and len(value) > 8:
    return value[:6] + "…"
  return value


def main(argv: list[str] | None = None) -> int:
  ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  ap.add_argument("files", nargs="*", help="Archivos concretos (por defecto, todo lo versionado).")
  ap.add_argument("--root", default=str(REPO_ROOT))
  ap.add_argument("--strict-all", action="store_true", help="Trata también reportOnlyPaths como bloqueantes.")
  ap.add_argument("--summary", action="store_true", help="Muestra solo el conteo de los hallazgos informativos.")
  args = ap.parse_args(argv)
  root = Path(args.root).resolve()
  blocking, informative = scan(root, args.files or None, args.strict_all)
  for rel, lineno, kind, value in blocking:
    print(f"[sensible] {rel}:{lineno}: {kind}: {_mask(kind, value)}")
  if informative:
    files = sorted({h[0] for h in informative})
    print(f"[aviso] {len(informative)} hallazgos en rutas solo informativas ({', '.join(files)}).")
    if not args.summary:
      for rel, lineno, kind, value in informative:
        print(f"  {rel}:{lineno}: {kind}: {_mask(kind, value)}")
  if blocking:
    print(f"[FALLO] {len(blocking)} dato(s) sensible(s) en lo que se publica.")
    return 1
  print("[OK] Sin datos sensibles en lo que se publica.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
