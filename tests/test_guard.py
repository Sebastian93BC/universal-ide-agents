"""U4: cada límite de la regla three-level-limits tiene su comprobación."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import unittest

from tests._helpers import make_project, run_git

GUARD = __import__("uia_lib").GUARD_HOOK
spec = importlib.util.spec_from_file_location("guard", GUARD)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def bash(cmd: str, cwd: str = "/tmp"):
  return guard.evaluate({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd})


def decision(result):
  return result[0] if result else None


class NuncaTest(unittest.TestCase):
  def test_leer_env_por_herramienta(self):
    for path in (".env", "/p/.env", "/p/.env.local", "/p/config/.env.production"):
      self.assertEqual(decision(guard.evaluate({"tool_name": "Read", "tool_input": {"file_path": path}})), "deny", path)
    self.assertIsNone(guard.evaluate({"tool_name": "Read", "tool_input": {"file_path": "/p/.env.example"}}))
    self.assertIsNone(guard.evaluate({"tool_name": "Read", "tool_input": {"file_path": "/p/environment.md"}}))

  def test_grep_sobre_env(self):
    self.assertEqual(decision(guard.evaluate({"tool_name": "Grep", "tool_input": {"pattern": "URI", "glob": ".env*"}})), "deny")

  def test_leer_env_por_comando(self):
    for cmd in ("cat .env", "source .env && run", "grep KEY .env.local", "cp .env /tmp/x", "python3 -c 'open(\".env\")'"):
      self.assertEqual(decision(bash(cmd)), "deny", cmd)
    for cmd in ("cat .env.example", "ls -la .env", "test -f .env && echo hay", "git check-ignore .env", "echo hola > notes.env.md"):
      self.assertNotEqual(decision(bash(cmd)), "deny", cmd)

  def test_imprimir_secretos(self):
    for cmd in ("printenv", "env", "env | sort", "echo $MONGO_URI", "echo ${N8N_API_KEY}", "printf '%s' $DB_PASSWORD"):
      self.assertEqual(decision(bash(cmd)), "deny", cmd)
    for cmd in ("env FOO=1 python3 x.py", "echo $HOME", "echo hola"):
      self.assertNotEqual(decision(bash(cmd)), "deny", cmd)

  def test_borrar_colecciones_o_tablas(self):
    for cmd in ("mongosh --eval 'db.ventas.drop()'", "mongosh --eval 'db.dropDatabase()'",
                "duckdb x.duckdb 'DROP TABLE ventas'", "psql -c 'drop schema s cascade'", "psql -c 'TRUNCATE ventas'"):
      self.assertEqual(decision(bash(cmd)), "deny", cmd)


class PreguntarPrimeroTest(unittest.TestCase):
  def test_ambientes_del_cliente(self):
    for cmd in ("dfa mongo explain --env quality x", "dfa run --env=production", "dfa run --env development"):
      self.assertEqual(decision(bash(cmd)), "ask", cmd)
    self.assertIsNone(bash("dfa run --env local"))

  def test_base_remota(self):
    remote_uri = "mongodb+srv://" + "app" + "@" + "cluster.ejemplo.net/db"
    self.assertEqual(decision(bash(f"mongosh '{remote_uri}'")), "ask")
    self.assertEqual(decision(bash("mongosh \"$MONGO_URI\"")), "ask")
    self.assertEqual(decision(bash("psql -h db.ejemplo.net -U app")), "ask")
    self.assertIsNone(bash("mongosh mongodb://localhost:27017/dummy"))
    self.assertIsNone(bash("mongosh --host 127.0.0.1"))

  def test_despliegues(self):
    for cmd in ("dfa deploy --env quality", "./deploy_n8n.sh", "kubectl apply -f k8s/", "docker push img:1", "helm upgrade x ."):
      self.assertEqual(decision(bash(cmd)), "ask", cmd)

  def test_commit_y_push(self):
    for cmd in ("git commit -m x", "git -C repo push origin local", "git add . && git commit -am y"):
      self.assertEqual(decision(bash(cmd)), "ask", cmd)
    for cmd in ("git status", "git log --oneline", "git diff"):
      self.assertIsNone(bash(cmd), cmd)


class SiempreTest(unittest.TestCase):
  def setUp(self) -> None:
    self.project = make_project(git=True)

  def tearDown(self) -> None:
    shutil.rmtree(self.project, ignore_errors=True)

  def edit(self):
    return guard.evaluate({"tool_name": "Edit", "tool_input": {"file_path": str(self.project / "README.md")}, "cwd": str(self.project)})

  def test_sin_rama_local_no_pregunta(self):
    self.assertIsNone(self.edit())

  def test_fuera_de_local_pregunta_y_en_local_no(self):
    run_git(self.project, "branch", "local")
    self.assertEqual(decision(self.edit()), "ask")
    run_git(self.project, "checkout", "-q", "local")
    self.assertIsNone(self.edit())


class ProtocoloTest(unittest.TestCase):
  def test_salida_json_de_claude_code(self):
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": "cat .env"}, "cwd": "/tmp"})
    out = subprocess.run([sys.executable, str(GUARD)], input=event, capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)["hookSpecificOutput"]
    self.assertEqual(data["hookEventName"], "PreToolUse")
    self.assertEqual(data["permissionDecision"], "deny")

  def test_sin_objecion_no_imprime_nada(self):
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": "/tmp"})
    out = subprocess.run([sys.executable, str(GUARD)], input=event, capture_output=True, text=True, check=True)
    self.assertEqual(out.stdout, "")


if __name__ == "__main__":
  unittest.main()
