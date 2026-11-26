# AGENTS.md — `universal-ide-agents`

Fuente única de agentes, skills, reglas, hook y plantillas MCP de ingeniería de datos, compilada para Antigravity (`.agents/`), Claude Code (`.claude/`) y VS Code Copilot (`.github/`). Es la capa genérica de los proyectos que genera `template-data-flow-automation`. `CLAUDE.md`, `GEMINI.md` y `.github/copilot-instructions.md` son punteros de una línea a este archivo.

## Comandos

- `make check`: el verificador único. Valida `core/`, el compilado, los punteros, el índice de documentos y los datos sensibles, y corre las pruebas. Ejecútalo antes de dar algo por terminado.
- `python3 scripts/validate_and_build.py`: valida `core/` y compila hacia `.agents/`, `.claude/` y `.github/`. Con `--check-only` solo valida.
- `scripts/deploy-to-project.sh --dry-run --profile data-eng-n8n /ruta/al/proyecto`: despliega en un proyecto (quita `--dry-run` para escribir). Después, `python3 scripts/check.py --project /ruta/al/proyecto`.
- `python3 scripts/scan_sensitive.py`: escáner de datos sensibles.
- `python3 scripts/harvest.py`: cosecha periódica de conocimiento (skill `knowledge-harvester`).

## Mapa

| Ruta | Qué es |
| :--- | :--- |
| `core/agents/`, `core/skills/`, `core/rules/` | La fuente. Categoría `hub`: solo para este repositorio, nunca se despliega. |
| `core/hooks/` | El guardián de límites (`PreToolUse` de Claude Code). |
| `core/mcp/` | El catálogo y la plantilla de servidores MCP. |
| `profiles/*.json` | Qué se despliega. `data-eng-base` (núcleo, MongoDB, modelado) más una herramienta (`data-eng-n8n`, `data-eng-dagster-duckdb`), unidos con `extends`. |
| `scripts/` | `uia_lib.py` (inventario y compilación compartidos), `validate_and_build.py`, `deploy.py`, `check.py`, `scan_sensitive.py`. |
| `.agents/`, `.claude/`, `.github/{agents,skills,instructions}` | Compilado. No se editan a mano. |
| `docs/` | Catálogo de activos, guía multi-IDE y contrato con la plantilla. |
| `plans/` | Registro de tareas de este repositorio (`registry.md`) y su conocimiento. |

## Reglas de este repositorio

1. **Se edita `core/`, nunca el compilado.** Después: `python3 scripts/validate_and_build.py` y `make check`. Razón: el compilado se regenera y se pierde lo editado a mano.
2. **El despliegue escribe solo en `.agents/`, `.claude/` y `.github/`.** Nunca toca `AGENTS.md`, `CLAUDE.md` ni `GEMINI.md` del proyecto: son de la plantilla y del cliente. Lo comprueban `deploy.py` y `check.py --project`.
3. **Nada de clientes en lo que se publica.** El repositorio es público. Nombres de cliente, correos, URL de tenant, GUID, tokens y rutas `/Users/...` los bloquea `scan_sensitive.py`; los términos están en `harvester/schema/sanitization_rules.json`.
4. **Sin Mermaid.** Diagramas en SVG (`docs/img/`) o tablas Markdown. Razón: el visor de Antigravity no los renderiza.
5. **Evidencia antes de afirmar.** Cada hallazgo lleva `[VERIFICADO]` o `[INFERIDO]` y una clase: `DEFECTO`, `CONDICIONAL`, `ENDURECIMIENTO` o `PROPUESTA`.
6. **Cada regla en `core/rules/` lleva un `trigger` válido** (`always_on`, `model_decision`, `glob`, `manual`). Razón: Antigravity descarta en silencio la que no lo tiene.
7. **Planes en `plans/`.** Cada tarea mayor se registra en `plans/registry.md` (slug `AAAA-MM-DD-tema`) y su plan va en `plans/{slug}_plan.md`, con secciones `## `. Al cerrar, el plan pasa a `plans/historyPlans/`, el informe a `plans/walkthroughs/` y hay entrada en `CHANGELOG.md`. Ignora `TO_DO.md`.
8. **Antes de cerrar una sesión con trabajo a medias**, deja la nota de traspaso en el plan activo (skill `session-handoff`).
9. **JSON de configuración en `camelCase`.** Conserva `PREPROCESS_CONFIG` donde exista (ver `plans/knowledge/knowledge_base.md`).

## Lo que cargan los IDE

- **Claude Code** (comprobado el 2026-11-25 en una sesión real): `CLAUDE.md` (que importa este archivo con `@AGENTS.md`), `.claude/rules/`, `.claude/skills/`, `.claude/agents/`.
- **Antigravity** (comprobado el 2026-11-25 en su documentación): `AGENTS.md` y `GEMINI.md` (siempre activos, sin frontmatter), `.agents/rules/*.md` (un nivel, con `trigger`), `.agents/skills/<name>/SKILL.md`, `.agents/agents/` y `.agents/mcp_config.json`. En `GEMINI.md`, `@AGENTS.md` es una referencia y no duplica el contenido.
- **Copilot (VS Code)** (sin comprobar en esta revisión, `[INFERIDO]`): `AGENTS.md`, `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` (según `applyTo`), `.github/agents/` y `.github/skills/`.

Detalle y fuentes: [docs/multi-ide-consumption.md](docs/multi-ide-consumption.md). Catálogo: [docs/asset-catalog.md](docs/asset-catalog.md). Contrato con la plantilla: [docs/contrato-template-dfa.md](docs/contrato-template-dfa.md).
