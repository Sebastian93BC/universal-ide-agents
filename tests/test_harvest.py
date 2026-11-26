"""El harvester funciona para cualquiera: se configura qué y dónde lee, y lo comprueba."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tests._helpers import quiet

import harvest  # noqa: E402


class HarvestTest(unittest.TestCase):
  def setUp(self) -> None:
    self.tmp = Path(tempfile.mkdtemp(prefix="uia-harvest-"))
    self.saved = (harvest.HARVESTER_DIR, harvest.LOCAL_SOURCES, harvest.LOCAL_STATE)
    harvest.HARVESTER_DIR = self.tmp / "harvester"
    harvest.HARVESTER_DIR.mkdir()
    harvest.LOCAL_SOURCES = harvest.HARVESTER_DIR / "sources.local.json"
    harvest.LOCAL_STATE = harvest.HARVESTER_DIR / "state.local.json"
    self.projects = self.tmp / "proyectos"
    for rel, text in {
        "app/AGENTS.md": "# reglas\n",
        "app/.claude/skills/x/SKILL.md": "---\nname: x\n---\n",
        "app/src/main.py": "print(1)\n",
        "app/notas/memory/leccion.md": "lección\n",
        "app/node_modules/pkg/AGENTS.md": "no\n",
    }.items():
      path = self.projects / rel
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(text)

  def tearDown(self) -> None:
    harvest.HARVESTER_DIR, harvest.LOCAL_SOURCES, harvest.LOCAL_STATE = self.saved
    shutil.rmtree(self.tmp, ignore_errors=True)

  def write_config(self, **extra) -> Path:
    cfg = {"includePatterns": ["AGENTS.md", ".claude/**/*.md", "**/memory/*.md"],
           "watchRoots": [{"id": "p", "path": str(self.projects), "category": "projects", "maxDepth": 6}]}
    cfg.update(extra)
    harvest.LOCAL_SOURCES.write_text(json.dumps(cfg))
    return harvest.LOCAL_SOURCES

  def test_sin_configuracion_falla_y_explica(self):
    code, out = quiet(harvest.main, [])
    self.assertEqual(code, 2)
    self.assertIn("--init", out)

  def test_init_crea_la_configuracion_desde_el_ejemplo(self):
    code, _ = quiet(harvest.main, ["--init"])
    self.assertEqual(code, 0)
    self.assertEqual(json.loads(harvest.LOCAL_SOURCES.read_text()), json.loads(harvest.EXAMPLE_SOURCES.read_text()))

  def test_el_ejemplo_es_valido(self):
    harvest.load_config(harvest.EXAMPLE_SOURCES)

  def test_configuracion_invalida(self):
    harvest.LOCAL_SOURCES.write_text(json.dumps({"watchRoots": [{"id": "a"}]}))
    code, out = quiet(harvest.main, [])
    self.assertEqual(code, 2)
    self.assertIn("'path'", out)

  def test_patrones_eligen_los_archivos(self):
    cfg = harvest.load_config(self.write_config())
    found = sorted(m["relativePath"] for m in harvest.scan_watch_roots(cfg, warn=lambda m: None).values())
    self.assertEqual(found, ["app/.claude/skills/x/SKILL.md", "app/AGENTS.md", "app/notas/memory/leccion.md"])

  def test_target_patterns_es_alias(self):
    cfg = harvest.load_config(self._alias())
    found = [m["relativePath"] for m in harvest.scan_watch_roots(cfg, warn=lambda m: None).values()]
    self.assertEqual(found, ["app/src/main.py"])

  def _alias(self) -> Path:
    harvest.LOCAL_SOURCES.write_text(json.dumps({"targetPatterns": ["**/*.py"], "watchRoots": [{"id": "p", "path": str(self.projects)}]}))
    return harvest.LOCAL_SOURCES

  def test_carpeta_inexistente_avisa(self):
    cfg = harvest.load_config(self.write_config(watchRoots=[{"id": "no", "path": str(self.tmp / "nada")}]))
    warnings = []
    harvest.scan_watch_roots(cfg, warn=warnings.append)
    self.assertTrue(warnings and "no existe" in warnings[0])

  def test_nunca_se_cosecha_a_si_mismo(self):
    cfg = {"includePatterns": ["AGENTS.md"], "watchRoots": [{"id": "r", "path": str(harvest.REPO_ROOT.parent), "maxDepth": 2}]}
    found = harvest.scan_watch_roots(cfg, warn=lambda m: None)
    self.assertFalse([p for p in found if p.startswith(str(harvest.REPO_ROOT) + "/") or p == str(harvest.REPO_ROOT / "AGENTS.md")])

  def test_check_config_no_escribe(self):
    self.write_config()
    code, out = quiet(harvest.main, ["--check-config"])
    self.assertEqual(code, 0, out)
    self.assertIn("3 archivos", out)
    self.assertFalse((harvest.HARVESTER_DIR / "inbox").exists())

  def test_cosecha_incremental(self):
    self.write_config()
    code, out = quiet(harvest.main, ["--mark-processed"])
    self.assertEqual(code, 0, out)
    self.assertIn("3 nuevos", out)
    (self.projects / "app/AGENTS.md").write_text("# reglas nuevas\n")
    code, out = quiet(harvest.main, [])
    self.assertIn("0 nuevos, 1 modificados, 2 sin cambios", out)


if __name__ == "__main__":
  unittest.main()
