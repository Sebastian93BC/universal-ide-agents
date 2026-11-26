"""U8: el escáner bloquea datos sensibles en lo publicado y solo informa en plans/."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from tests._helpers import run_git

import scan_sensitive  # noqa: E402

# Valores construidos en tiempo de ejecución para no publicar nada con forma de secreto.
TOKEN = "ghp_" + "A1b2C3d4" * 5
MAIL = "persona" + "@" + "empresa-real.com"
GUID = "123e4567-e89b-12d3-a456-" + "426614174000"
TENANT = "https://acme." + "sharepoint.com/x"
HOME = "/" + "Users/alguien/proyecto"
CONN = "mongodb+srv://usuario:" + "clave@cluster/db"
CLIENT = "CLIENTEFICTICIO"  # término de prueba inyectado en las reglas, no es un cliente real


class ScanTest(unittest.TestCase):
  def setUp(self) -> None:
    self.root = Path(tempfile.mkdtemp(prefix="uia-scan-"))
    run_git(self.root, "init", "-q")
    self._load_rules = scan_sensitive.load_rules
    rules = self._load_rules()
    rules["forbiddenClientTerms"] = rules.get("forbiddenClientTerms", []) + [CLIENT]
    scan_sensitive.load_rules = lambda: rules

  def tearDown(self) -> None:
    scan_sensitive.load_rules = self._load_rules
    shutil.rmtree(self.root, ignore_errors=True)

  def write(self, rel: str, text: str) -> None:
    path = self.root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

  def kinds(self, hits):
    return {h[2] for h in hits}

  def test_detecta_cada_clase(self):
    self.write("docs/a.md", f"token {TOKEN}\ncorreo {MAIL}\nid {GUID}\n{TENANT}\n")
    self.write("docs/b.md", f"ruta {HOME} y carpeta proyectos_{CLIENT.lower()}\n")
    self.write("docs/c.md", f"{CONN}\n")
    blocking, _ = scan_sensitive.scan(self.root)
    self.assertEqual(self.kinds(blocking), {"token", "correo", "guid", "url-tenant", "ruta-personal", "cliente", "credencial-en-uri"})

  def test_plans_solo_informa(self):
    self.write("plans/registro.md", f"cliente {CLIENT}\n")
    blocking, informative = scan_sensitive.scan(self.root)
    self.assertEqual(blocking, [])
    self.assertEqual(len(informative), 1)
    blocking, _ = scan_sensitive.scan(self.root, strict_all=True)
    self.assertEqual(len(blocking), 1)

  def test_permitidos(self):
    self.write("docs/a.md", "Co-Authored-By: x <noreply@anthropic.com>\nusuario@example.com\n")
    blocking, _ = scan_sensitive.scan(self.root)
    self.assertEqual(blocking, [])

  def test_ignora_lo_ignorado_por_git(self):
    self.write(".gitignore", "secreto.md\n")
    self.write("secreto.md", f"{TOKEN}\n")
    blocking, _ = scan_sensitive.scan(self.root)
    self.assertEqual(blocking, [])


if __name__ == "__main__":
  unittest.main()
