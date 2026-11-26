# Verificador único de universal-ide-agents. Solo necesita python3 (biblioteca estándar) y git.
PYTHON ?= python3

.PHONY: check build test scan check-project

check: ## Lo mecánico del repositorio y las pruebas
	$(PYTHON) scripts/check.py
	$(PYTHON) -m unittest discover -s tests -t . -q

build: ## Valida core/ y compila hacia .agents/, .claude/ y .github/
	$(PYTHON) scripts/validate_and_build.py

test:
	$(PYTHON) -m unittest discover -s tests -t . -v

scan: ## Escáner de datos sensibles, con detalle
	$(PYTHON) scripts/scan_sensitive.py

check-project: ## make check-project PROJECT=/ruta/al/proyecto
	$(PYTHON) scripts/check.py --project "$(PROJECT)"
