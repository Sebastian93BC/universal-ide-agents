"""Utilidades compartidas por las pruebas: ruta a scripts/ y un proyecto de ejemplo."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
  sys.path.insert(0, str(SCRIPTS))

ROOT_FILES = {
    "AGENTS.md": "# Instrucciones para agentes\n\n## Capa del cliente\n\n- Escrita por el proyecto.\n",
    "CLAUDE.md": "@AGENTS.md\n",
    "GEMINI.md": "@AGENTS.md\n",
    ".claude/settings.json": '{"permissions": {"deny": ["Read(**/.env)"]}}\n',
    "README.md": "# Proyecto\n",
}


def make_project(git: bool = False) -> Path:
  root = Path(tempfile.mkdtemp(prefix="uia-proyecto-"))
  for rel, content in ROOT_FILES.items():
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
  if git:
    run_git(root, "init", "-q", "-b", "development")
    run_git(root, "add", ".")
    run_git(root, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
  return root


def run_git(root: Path, *args: str) -> None:
  subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def snapshot(root: Path) -> dict[str, bytes]:
  return {
      p.relative_to(root).as_posix(): p.read_bytes()
      for p in sorted(root.rglob("*"))
      if p.is_file() and ".git" not in p.relative_to(root).parts
  }


def quiet(fn, *args, **kwargs):
  """Ejecuta fn capturando stdout/stderr; devuelve (resultado, salida)."""
  buf = io.StringIO()
  with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    result = fn(*args, **kwargs)
  return result, buf.getvalue()
