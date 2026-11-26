"""Biblioteca común de universal-ide-agents: inventario de core/, perfiles y compilación.

La usan `validate_and_build.py` (compila todo hacia este repositorio),
`deploy.py` (compila el subconjunto de un perfil hacia un proyecto) y
`check.py` (verifica que lo compilado coincide con core/). Así las tres
herramientas producen exactamente los mismos archivos.

Solo biblioteca estándar.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = REPO_ROOT / "core"
PROFILES_DIR = REPO_ROOT / "profiles"
MCP_TEMPLATE = CORE_DIR / "mcp" / "templates" / "data-eng-full.mcp.json"
GUARD_HOOK = CORE_DIR / "hooks" / "universal-ide-agents-guard.py"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

# Categorías que solo sirven dentro de este repositorio y nunca se despliegan.
HUB_ONLY_CATEGORIES = {"hub"}

TARGETS = ("antigravity", "claude", "vscode")
TARGET_ROOTS = {"antigravity": ".agents", "claude": ".claude", "vscode": ".github"}

# Subcarpetas que la compilación gestiona por completo en cada raíz.
MANAGED_SUBDIRS = {
    "antigravity": ("skills", "rules", "agents"),
    "claude": ("skills", "rules", "agents", "hooks"),
    "vscode": ("skills", "instructions", "agents"),
}
MCP_OUTPUTS = {
    "antigravity": ".agents/mcp_config.example.json",
    "claude": ".claude/mcp.example.json",
}
GUARD_OUTPUT = ".claude/hooks/universal-ide-agents-guard.py"
MANIFEST_PATH = ".agents/universal-ide-agents.json"
ROOT_FILES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")

# Copias de conflicto de sincronización (iCloud, Finder): "SKILL 2.md", "init_skill 3.py".
SYNC_DUPLICATE_RE = re.compile(r" \d+(\.[^/]*)?$")
IGNORED_NAMES = {".DS_Store", "__pycache__"}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class ProfileError(ValueError):
  """Perfil inexistente, ciclo de `extends` o referencia a un activo que no existe."""


@dataclass(frozen=True)
class Asset:
  kind: str  # "agent" | "skill" | "rule"
  name: str
  category: str
  source: Path  # archivo (agente, regla) o carpeta (skill)


def is_sync_duplicate(name: str) -> bool:
  return bool(SYNC_DUPLICATE_RE.search(name))


def parse_frontmatter(text: str) -> dict[str, str]:
  match = FRONTMATTER_RE.match(text)
  if not match:
    return {}
  data: dict[str, str] = {}
  for line in match.group(1).splitlines():
    if ":" in line:
      key, val = line.split(":", 1)
      data[key.strip()] = val.strip().strip('"').strip("'")
  return data


def sha256(data: bytes) -> str:
  return "sha256:" + hashlib.sha256(data).hexdigest()


def source_version() -> str:
  """Primera versión `## X.Y.Z` del CHANGELOG."""
  if CHANGELOG.exists():
    m = re.search(r"^##\s+(\d+\.\d+\.\d+[\w.-]*)", CHANGELOG.read_text(encoding="utf-8"), re.MULTILINE)
    if m:
      return m.group(1)
  return "0.0.0"


# --- Inventario --------------------------------------------------------------

def inventory() -> dict[str, dict[str, Asset]]:
  """Todos los activos de core/, por tipo y nombre."""
  assets: dict[str, dict[str, Asset]] = {"agent": {}, "skill": {}, "rule": {}}
  for f in sorted((CORE_DIR / "agents").glob("*/*.agent.md")):
    name = f.name[: -len(".agent.md")]
    assets["agent"][name] = Asset("agent", name, f.parent.name, f)
  for f in sorted((CORE_DIR / "skills").glob("*/*/SKILL.md")):
    assets["skill"][f.parent.name] = Asset("skill", f.parent.name, f.parent.parent.name, f.parent)
  for f in sorted((CORE_DIR / "rules").glob("*/*.rule.md")):
    name = f.name[: -len(".rule.md")]
    assets["rule"][name] = Asset("rule", name, f.parent.name, f)
  return assets


def skill_files(skill_dir: Path) -> list[Path]:
  """Archivos de una skill, sin basura del sistema ni copias de conflicto."""
  files = []
  for p in sorted(skill_dir.rglob("*")):
    rel = p.relative_to(skill_dir)
    if any(part in IGNORED_NAMES or is_sync_duplicate(part) for part in rel.parts):
      continue
    if p.is_file() and not p.name.endswith((".pyc", ".pyo")):
      files.append(p)
  return files


# --- Perfiles ----------------------------------------------------------------

@dataclass
class Selection:
  profiles: list[str]
  resolved: list[str]
  agents: set[str]
  skills: set[str]
  rules: set[str]
  mcp: set[str]


def list_profiles() -> list[str]:
  return sorted(p.stem for p in PROFILES_DIR.glob("*.json"))


def _load_profile(pid: str) -> dict:
  path = PROFILES_DIR / f"{pid}.json"
  if not path.exists():
    raise ProfileError(f"perfil '{pid}' no existe (disponibles: {', '.join(list_profiles())})")
  data = json.loads(path.read_text(encoding="utf-8"))
  if data.get("profileId") != pid:
    raise ProfileError(f"profiles/{pid}.json declara profileId '{data.get('profileId')}'")
  return data


def resolve_profiles(profile_ids: list[str], assets: dict[str, dict[str, Asset]] | None = None) -> Selection:
  """Une uno o varios perfiles, siguiendo `extends`. Falla ante cualquier referencia rota."""
  assets = assets or inventory()
  sel = Selection(list(profile_ids), [], set(), set(), set(), set())
  mcp_available = set(json.loads(MCP_TEMPLATE.read_text(encoding="utf-8"))["mcpServers"])

  def pick(kind: str, categories: list[str], names: list[str], pid: str) -> set[str]:
    out: set[str] = set()
    known_cats = {a.category for a in assets[kind].values()}
    for cat in categories:
      if cat in HUB_ONLY_CATEGORIES:
        raise ProfileError(f"[{pid}] la categoría '{cat}' es solo de este repositorio y no se despliega")
      if cat not in known_cats:
        raise ProfileError(f"[{pid}] categoría de {kind} inexistente: '{cat}'")
      out |= {n for n, a in assets[kind].items() if a.category == cat}
    for n in names:
      if n not in assets[kind]:
        raise ProfileError(f"[{pid}] {kind} inexistente: '{n}'")
      if assets[kind][n].category in HUB_ONLY_CATEGORIES:
        raise ProfileError(f"[{pid}] '{n}' es solo de este repositorio y no se despliega")
      out.add(n)
    return out

  def visit(pid: str, stack: tuple[str, ...]) -> None:
    if pid in stack:
      raise ProfileError("ciclo en extends: " + " -> ".join(stack + (pid,)))
    if pid in sel.resolved:
      return
    data = _load_profile(pid)
    for parent in data.get("extends", []):
      visit(parent, stack + (pid,))
    sel.agents |= pick("agent", data.get("agentCategories", []), data.get("agents", []), pid)
    sel.skills |= pick("skill", data.get("skillCategories", []), data.get("skills", []), pid)
    sel.rules |= pick("rule", data.get("ruleCategories", []), data.get("rules", []), pid)
    for server in data.get("mcpTemplates", []):
      if server not in mcp_available:
        raise ProfileError(f"[{pid}] servidor MCP sin plantilla: '{server}'")
      sel.mcp.add(server)
    sel.resolved.append(pid)

  if not profile_ids:
    raise ProfileError("hace falta al menos un perfil")
  for pid in profile_ids:
    visit(pid, ())
  return sel


def full_selection(assets: dict[str, dict[str, Asset]] | None = None) -> Selection:
  """Todo core/, incluidos los activos del hub (para compilar este repositorio)."""
  assets = assets or inventory()
  mcp_all = set(json.loads(MCP_TEMPLATE.read_text(encoding="utf-8"))["mcpServers"])
  return Selection(["*"], ["*"], set(assets["agent"]), set(assets["skill"]), set(assets["rule"]), mcp_all)


# --- Compilación -------------------------------------------------------------

def render(selection: Selection, targets: tuple[str, ...] | list[str] = TARGETS,
           assets: dict[str, dict[str, Asset]] | None = None) -> dict[str, bytes]:
  """Archivos compilados {ruta relativa: contenido} para la selección y los IDE pedidos."""
  assets = assets or inventory()
  out: dict[str, bytes] = {}

  for name in sorted(selection.skills):
    sdir = assets["skill"][name].source
    for f in skill_files(sdir):
      rel = f.relative_to(sdir).as_posix()
      data = f.read_bytes()
      for t in targets:
        out[f"{TARGET_ROOTS[t]}/skills/{name}/{rel}"] = data

  for name in sorted(selection.agents):
    data = assets["agent"][name].source.read_bytes()
    if "antigravity" in targets:
      out[f".agents/agents/{name}.md"] = data
    if "claude" in targets:
      out[f".claude/agents/{name}.md"] = data
    if "vscode" in targets:
      out[f".github/agents/{name}.agent.md"] = data

  for name in sorted(selection.rules):
    data = assets["rule"][name].source.read_bytes()
    if "antigravity" in targets:
      out[f".agents/rules/{name}.md"] = data
    if "claude" in targets:
      out[f".claude/rules/{name}.md"] = data
    if "vscode" in targets:
      out[f".github/instructions/{name}.instructions.md"] = data

  if selection.mcp:
    template = json.loads(MCP_TEMPLATE.read_text(encoding="utf-8"))
    servers = {k: v for k, v in template["mcpServers"].items() if k in selection.mcp}
    data = (json.dumps({"mcpServers": servers}, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    for t, path in MCP_OUTPUTS.items():
      if t in targets:
        out[path] = data

  if "claude" in targets and GUARD_HOOK.exists():
    out[GUARD_OUTPUT] = GUARD_HOOK.read_bytes()

  return out


def managed_files_on_disk(root: Path, targets: tuple[str, ...] | list[str] = TARGETS) -> dict[str, Path]:
  """Archivos presentes en las subcarpetas gestionadas (y ejemplos MCP) de `root`."""
  found: dict[str, Path] = {}
  for t in targets:
    for sub in MANAGED_SUBDIRS[t]:
      base = root / TARGET_ROOTS[t] / sub
      if base.is_dir():
        for p in base.rglob("*"):
          if p.is_file() and p.name not in IGNORED_NAMES and "__pycache__" not in p.parts:
            found[p.relative_to(root).as_posix()] = p
    if t in MCP_OUTPUTS and (root / MCP_OUTPUTS[t]).is_file():
      found[MCP_OUTPUTS[t]] = root / MCP_OUTPUTS[t]
  return found


def root_file_hashes(project: Path) -> dict[str, str | None]:
  return {
      name: (sha256((project / name).read_bytes()) if (project / name).is_file() else None)
      for name in ROOT_FILES
  }
