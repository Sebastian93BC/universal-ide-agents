#!/usr/bin/env python3
"""Guardián de límites en tres niveles para Claude Code (hook PreToolUse).

Aplica las comprobaciones de la regla `limites-tres-niveles`:

- Nunca (deny): leer `.env`/`.env.*` (salvo `.env.example`), imprimir secretos,
  borrar colecciones o tablas.
- Preguntar primero (ask): escribir en bases de ambientes del cliente,
  desplegar, `git commit` / `git push`.
- Siempre (ask si no se cumple): editar archivos solo en la rama `local`
  cuando esa rama existe.

Lee el evento JSON de stdin y, si hay algo que decir, escribe en stdout
`{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": ..., ...}}`.
Es una segunda capa, no una frontera de seguridad. Solo biblioteca estándar.

Se conecta desde `.claude/settings.json` del proyecto:

  "hooks": {"PreToolUse": [{"matcher": "Bash|Read|Grep|Edit|Write|MultiEdit|NotebookEdit",
    "hooks": [{"type": "command",
      "command": "python3 \\"$CLAUDE_PROJECT_DIR\\"/.claude/hooks/universal-ide-agents-guard.py"}]}]}
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# --- Nunca: credenciales -----------------------------------------------------

ENV_FILE_RE = re.compile(r"^\.env(\.[A-Za-z0-9_.-]+)?$")
ENV_ALLOWED = {".env.example"}
ENV_IN_COMMAND_RE = re.compile(
    r"(?:^|[\s'\"=/<>:(])(\.env(?:\.[A-Za-z0-9_-]+)*)(?=$|[\s'\";|&)<>])"
)
# Comandos que mencionan .env sin revelar su contenido.
ENV_SAFE_COMMANDS = {"ls", "test", "[", "stat"}
ENV_SAFE_GIT = {"check-ignore", "status"}

PRINTENV_RE = re.compile(r"(?:^|[;&|(]\s*|\s)(printenv)\b")
ENV_ALONE_RE = re.compile(r"(?:^|[;&|(]\s*)env\s*(?:$|[;&|)])")
SECRET_VAR = r"[A-Za-z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|PASS|URI)[A-Za-z0-9_]*"
ECHO_SECRET_RE = re.compile(
    r"\b(?:echo|printf)\b[^;&|]*\$\{?" + SECRET_VAR + r"\}?", re.IGNORECASE
)

# --- Nunca: borrar colecciones o tablas -------------------------------------

DROP_RES = [
    re.compile(r"\.drop\(\s*\)"),
    re.compile(r"\bdropCollection\b"),
    re.compile(r"\bdropDatabase\b"),
    re.compile(r"\bDROP\s+(?:TABLE|SCHEMA|DATABASE|COLLECTION|VIEW)\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
]

# --- Preguntar primero -------------------------------------------------------

CLIENT_ENV_RE = re.compile(r"--env(?:\s+|=)['\"]?(development|quality|production)\b")
DB_CLIENT_RE = re.compile(r"(?:^|[\s;&|(])(mongosh|mongo|psql)(?=\s|$)")
DB_URI_RE = re.compile(r"(?:mongodb(?:\+srv)?|postgres(?:ql)?)://([^/\s'\"?]+)")
HOST_FLAG_RE = re.compile(r"(?:--host(?:\s+|=)|\s-h\s+)['\"]?([^\s'\";|&]+)")
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]", "0.0.0.0"}

DEPLOY_RES = [
    re.compile(r"\bdfa\s+deploy\b"),
    re.compile(r"\bdeploy_n8n(?:\.sh)?\b"),
    re.compile(r"\bkubectl\s+(?:apply|replace|rollout|delete)\b"),
    re.compile(r"\bhelm\s+(?:install|upgrade)\b"),
    re.compile(r"\bdocker\s+push\b"),
    re.compile(r"\bdg\s+deploy\b"),
]
GIT_WRITE_RE = re.compile(
    r"\bgit\b(?:\s+(?:-[Cc]\s+\S+|--?[A-Za-z][\w-]*(?:=\S+)?))*\s+(commit|push)\b"
)

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
PATH_TOOLS = {"Read", "Grep", "Glob"} | EDIT_TOOLS


def _is_env_path(path: str) -> bool:
  name = os.path.basename(path.rstrip("/"))
  return bool(ENV_FILE_RE.match(name)) and name not in ENV_ALLOWED


def _segments(command: str) -> list[str]:
  return [s.strip() for s in re.split(r"&&|\|\||[;|\n]", command) if s.strip()]


def _env_read_in_command(command: str) -> str | None:
  for segment in _segments(command):
    hits = [m.group(1) for m in ENV_IN_COMMAND_RE.finditer(segment)]
    hits = [h for h in hits if h not in ENV_ALLOWED]
    if not hits:
      continue
    words = segment.split()
    first = words[0] if words else ""
    if first in ENV_SAFE_COMMANDS:
      continue
    if first == "git" and len(words) > 1 and words[1] in ENV_SAFE_GIT:
      continue
    return hits[0]
  return None


def _remote_db(command: str) -> str | None:
  if not DB_CLIENT_RE.search(command):
    return None
  for host_part in DB_URI_RE.findall(command):
    host = host_part.split("@")[-1].split(",")[0]
    host = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    if host not in LOCAL_HOSTS:
      return f"servidor '{host}'"
  for host in HOST_FLAG_RE.findall(command):
    if host.split(":")[0] not in LOCAL_HOSTS:
      return f"servidor '{host}'"
  if re.search(r"(?:mongosh|mongo|psql)\s+[^|;&]*\$", command):
    return "una URI tomada de una variable"
  return None


def _git(cwd: str, *args: str) -> str | None:
  try:
    out = subprocess.run(
        ["git", "-C", cwd, *args], capture_output=True, text=True, timeout=3
    )
  except (OSError, subprocess.SubprocessError):
    return None
  return out.stdout.strip() if out.returncode == 0 else None


def evaluate(event: dict) -> tuple[str, str] | None:
  """Devuelve (decisión, razón) o None si no hay nada que objetar."""
  tool = event.get("tool_name", "")
  tool_input = event.get("tool_input") or {}
  cwd = event.get("cwd") or os.getcwd()
  deny: list[str] = []
  ask: list[str] = []

  if tool in PATH_TOOLS:
    for key in ("file_path", "path", "notebook_path"):
      value = tool_input.get(key)
      if isinstance(value, str) and _is_env_path(value):
        deny.append(f"Nunca leas credenciales: '{value}' es un archivo de entorno. De .env.example lee solo los nombres.")
    pattern = tool_input.get("glob") or tool_input.get("pattern")
    if tool in {"Grep", "Glob"} and isinstance(pattern, str) and re.search(r"(^|/)\.env(\b|\*)", pattern) and ".env.example" not in pattern:
      deny.append("Nunca leas credenciales: el patrón incluye archivos .env.")

  if tool == "Bash":
    command = str(tool_input.get("command", ""))
    env_hit = _env_read_in_command(command)
    if env_hit:
      deny.append(f"Nunca leas credenciales: el comando abre '{env_hit}'. Usa los comandos de dfa, que usan la credencial sin mostrarla.")
    if PRINTENV_RE.search(command) or ENV_ALONE_RE.search(command) or ECHO_SECRET_RE.search(command):
      deny.append("Nunca imprimas un secreto: el comando muestra variables de entorno.")
    for rx in DROP_RES:
      m = rx.search(command)
      if m:
        deny.append(f"Nunca borres una colección o tabla existente ('{m.group(0)}'). Crea una nueva y migra.")
        break
    m = CLIENT_ENV_RE.search(command)
    if m:
      ask.append(f"Preguntar primero: el comando actúa sobre el ambiente del cliente '{m.group(1)}'.")
    remote = _remote_db(command)
    if remote:
      ask.append(f"Preguntar primero: cliente de base de datos contra {remote}, que no es local.")
    for rx in DEPLOY_RES:
      m = rx.search(command)
      if m:
        ask.append(f"Preguntar primero: '{m.group(0)}' es un despliegue.")
        break
    m = GIT_WRITE_RE.search(command)
    if m:
      ask.append(f"Preguntar primero: 'git {m.group(1)}' lo decide el usuario.")

  if tool in EDIT_TOOLS and not deny:
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    has_local = _git(cwd, "rev-parse", "--verify", "--quiet", "refs/heads/local")
    if branch and has_local and branch != "local":
      ask.append(f"Siempre en la rama local: la rama activa es '{branch}'.")

  if deny:
    return "deny", " ".join(deny)
  if ask:
    return "ask", " ".join(ask)
  return None


def main() -> int:
  try:
    event = json.load(sys.stdin)
  except (json.JSONDecodeError, ValueError) as exc:
    print(f"universal-ide-agents-guard: evento no válido ({exc})", file=sys.stderr)
    return 0
  result = evaluate(event)
  if result:
    decision, reason = result
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
        ensure_ascii=False,
    )
  return 0


if __name__ == "__main__":
  sys.exit(main())
