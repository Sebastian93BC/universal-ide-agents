#!/usr/bin/env sh
# deploy-to-project.sh — Despliega la capa genérica de universal-ide-agents en un proyecto.
#
# Envoltorio compatible de scripts/deploy.py, que hace el trabajo. Escribe solo
# bajo .agents/, .claude/ y .github/; nunca toca AGENTS.md, CLAUDE.md ni GEMINI.md.
#
# Uso:
#   deploy-to-project.sh [--dry-run] [--force] [--target all|antigravity,claude,vscode]
#                        [--profile <perfil>[,<perfil>]] [directorio-del-proyecto]
#
# Desde un proyecto que lo tiene como submódulo en .modules/universal-ide-agents:
#   git submodule add https://github.com/Sebastian93BC/universal-ide-agents.git .modules/universal-ide-agents
#   .modules/universal-ide-agents/scripts/deploy-to-project.sh --dry-run --profile data-eng-n8n .
#   .modules/universal-ide-agents/scripts/deploy-to-project.sh --profile data-eng-n8n .
#   .modules/universal-ide-agents/scripts/check.py --project .
#
# Actualizar: git submodule update --remote .modules/universal-ide-agents y volver a desplegar.
# Más detalle: docs/multi-ide-consumption.md.

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if ! command -v python3 >/dev/null 2>&1; then
  printf 'Error: hace falta python3 para desplegar.\n' >&2
  exit 1
fi

exec python3 "$script_dir/deploy.py" "$@"
