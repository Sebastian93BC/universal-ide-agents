"""U1 y U3: el despliegue no pisa la raíz, filtra por perfil y es idempotente."""

from __future__ import annotations

import json
import shutil
import unittest

from tests._helpers import ROOT_FILES, make_project, quiet, snapshot

import check  # noqa: E402
import deploy  # noqa: E402
import uia_lib  # noqa: E402

ALLOWED = (".agents/", ".claude/", ".github/")


class DeployTest(unittest.TestCase):
  def setUp(self) -> None:
    self.project = make_project()

  def tearDown(self) -> None:
    shutil.rmtree(self.project, ignore_errors=True)

  def deploy(self, *args: str) -> tuple[int, str]:
    return quiet(deploy.main, [*args, str(self.project)])

  def test_solo_escribe_bajo_las_tres_raices_y_no_toca_la_raiz(self):
    before = snapshot(self.project)
    code, out = self.deploy("--profile", "data-eng-n8n")
    self.assertEqual(code, 0, out)
    after = snapshot(self.project)
    for rel, data in before.items():
      self.assertEqual(after[rel], data, f"{rel} cambió")
    for rel in set(after) - set(before):
      self.assertTrue(rel.startswith(ALLOWED), rel)
    self.assertFalse((self.project / "plans").exists())

  def test_manifiesto_con_version_perfil_y_fecha(self):
    self.deploy("--profile", "data-eng-n8n")
    manifest = json.loads((self.project / ".agents/universal-ide-agents.json").read_text())
    self.assertEqual(manifest["version"], uia_lib.source_version())
    self.assertEqual(manifest["profiles"], ["data-eng-n8n"])
    self.assertRegex(manifest["deployedAt"], r"^\d{4}-\d{2}-\d{2}$")
    self.assertEqual(set(manifest["rootFiles"]), {"AGENTS.md", "CLAUDE.md", "GEMINI.md"})
    for rel in manifest["files"]:
      self.assertTrue((self.project / rel).is_file(), rel)

  def test_redesplegar_no_cambia_nada(self):
    self.deploy("--profile", "data-eng-n8n")
    first = snapshot(self.project)
    manifest = self.project / ".agents/universal-ide-agents.json"
    data = json.loads(manifest.read_text())
    data["deployedAt"] = "2000-01-01"  # una fecha anterior debe conservarse si nada cambió
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    first = snapshot(self.project)
    code, out = self.deploy("--profile", "data-eng-n8n")
    self.assertEqual(code, 0, out)
    self.assertIn("Sin cambios", out)
    self.assertEqual(snapshot(self.project), first)

  def test_perfil_n8n_filtra_de_verdad(self):
    self.deploy("--profile", "data-eng-n8n")
    skills = {p.name for p in (self.project / ".claude/skills").iterdir()}
    self.assertIn("n8n-workflow-engineering", skills)
    self.assertIn("mongodb-query-optimizer", skills)
    self.assertIn("sql-to-nosql-modeling", skills)
    self.assertIn("session-handoff", skills)
    for prefix in ("dagster", "dbt", "pyspark", "duckdb", "kafka", "airflow"):
      self.assertFalse([s for s in skills if s.startswith(prefix)], prefix)
    for hub in ("knowledge-harvester", "skill-creator"):
      self.assertNotIn(hub, skills)
    rules = {p.stem for p in (self.project / ".claude/rules").iterdir()}
    self.assertIn("three-level-limits", rules)
    self.assertNotIn("duckdb-dagster-dbt-invariants", rules)
    self.assertNotIn("planning-and-versioning", rules)
    mcp = json.loads((self.project / ".claude/mcp.example.json").read_text())["mcpServers"]
    self.assertEqual(set(mcp), {"mongodb", "context7"})
    self.assertTrue((self.project / ".claude/hooks/universal-ide-agents-guard.py").is_file())

  def test_cambiar_de_perfil_borra_lo_que_ya_no_toca(self):
    self.deploy("--profile", "data-eng-n8n")
    code, out = self.deploy("--profile", "data-eng-dagster-duckdb")
    self.assertEqual(code, 0, out)
    self.assertFalse((self.project / ".claude/skills/n8n-workflow-engineering").exists())
    self.assertTrue((self.project / ".claude/skills/dagster-asset-architecture/SKILL.md").is_file())

  def test_perfiles_combinados(self):
    code, out = self.deploy("--profile", "data-eng-n8n,data-eng-dagster-duckdb")
    self.assertEqual(code, 0, out)
    for skill in ("n8n-workflow-engineering", "dagster-asset-architecture"):
      self.assertTrue((self.project / ".agents/skills" / skill / "SKILL.md").is_file())

  def test_conflicto_con_archivo_ajeno_no_escribe_nada(self):
    foreign = self.project / ".claude/skills/n8n-workflow-engineering/SKILL.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("---\nname: n8n-workflow-engineering\ndescription: propia\n---\n")
    before = snapshot(self.project)
    code, out = self.deploy("--profile", "data-eng-n8n")
    self.assertEqual(code, 2, out)
    self.assertEqual(snapshot(self.project), before)
    code, out = self.deploy("--profile", "data-eng-n8n", "--force")
    self.assertEqual(code, 0, out)

  def test_archivo_desplegado_editado_es_conflicto(self):
    self.deploy("--profile", "data-eng-n8n")
    edited = self.project / ".claude/rules/three-level-limits.md"
    edited.write_text("editado\n")
    code, out = self.deploy("--profile", "data-eng-n8n")
    self.assertEqual(code, 2, out)
    self.assertEqual(edited.read_text(), "editado\n")

  def test_dry_run_no_escribe(self):
    before = snapshot(self.project)
    code, out = self.deploy("--dry-run", "--profile", "data-eng-n8n")
    self.assertEqual(code, 0, out)
    self.assertEqual(snapshot(self.project), before)

  def test_target_solo_claude(self):
    self.deploy("--target", "claude", "--profile", "core")
    self.assertTrue((self.project / ".claude/rules/three-level-limits.md").is_file())
    self.assertFalse((self.project / ".agents/skills").exists())
    self.assertFalse((self.project / ".github").exists())
    self.assertTrue((self.project / ".agents/universal-ide-agents.json").is_file())

  def test_perfil_inexistente_falla(self):
    code, out = self.deploy("--profile", "no-existe")
    self.assertEqual(code, 1, out)

  def test_verificador_de_proyecto(self):
    self.deploy("--profile", "data-eng-n8n")
    code, out = quiet(check.main, ["--project", str(self.project)])
    self.assertEqual(code, 0, out)
    (self.project / "AGENTS.md").write_text(ROOT_FILES["AGENTS.md"] + "- cambio\n")
    code, out = quiet(check.main, ["--project", str(self.project)])
    self.assertEqual(code, 0, out)  # un cambio en la raíz es aviso, no fallo
    self.assertIn("AGENTS.md cambió", out)
    self.assertIn("[AVISO]", out)

  def test_verificador_sin_manifiesto_falla(self):
    code, out = quiet(check.main, ["--project", str(self.project)])
    self.assertEqual(code, 1, out)


class ProfilesTest(unittest.TestCase):
  def test_todos_los_perfiles_resuelven(self):
    for pid in uia_lib.list_profiles():
      uia_lib.resolve_profiles([pid])

  def test_ningun_perfil_despliega_el_hub(self):
    assets = uia_lib.inventory()
    hub = {kind: {n for n, a in items.items() if a.category == "hub"} for kind, items in assets.items()}
    self.assertTrue(hub["skill"] and hub["rule"])
    for pid in uia_lib.list_profiles():
      sel = uia_lib.resolve_profiles([pid], assets)
      self.assertFalse(hub["skill"] & sel.skills, pid)
      self.assertFalse(hub["rule"] & sel.rules, pid)
      self.assertFalse(hub["agent"] & sel.agents, pid)

  def test_base_es_agnostica_de_la_herramienta(self):
    sel = uia_lib.resolve_profiles(["data-eng-base"])
    self.assertNotIn("n8n-workflow-engineering", sel.skills)
    self.assertFalse([s for s in sel.skills if "dagster" in s or "duckdb" in s or "dbt" in s])


if __name__ == "__main__":
  unittest.main()
