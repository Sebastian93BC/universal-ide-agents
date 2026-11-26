# Consumo multi-IDE de `universal-ide-agents`

Cómo llega la capa genérica a un proyecto y qué carga cada IDE. El contrato con la plantilla `template-data-flow-automation` (manifiesto, verificador, guardián y cierre de tarea) está en [template-dfa-contract.md](./template-dfa-contract.md).

## 1. Qué se despliega y dónde

`scripts/deploy-to-project.sh` (envoltorio de `scripts/deploy.py`) compila desde `core/` solo lo que piden los perfiles y lo escribe bajo tres raíces. Nunca toca `AGENTS.md`, `CLAUDE.md` ni `GEMINI.md`, ni crea `plans/`.

| IDE (`--target`) | Origen en `core/` | Destino en el proyecto |
| :--- | :--- | :--- |
| Antigravity (`antigravity`) | `agents/`, `skills/`, `rules/` | `.agents/agents/<n>.md`, `.agents/skills/<n>/`, `.agents/rules/<n>.md` |
| Antigravity | `mcp/templates/` (filtrado por perfil) | `.agents/mcp_config.example.json` |
| Claude Code (`claude`) | `agents/`, `skills/`, `rules/` | `.claude/agents/<n>.md`, `.claude/skills/<n>/`, `.claude/rules/<n>.md` |
| Claude Code | `hooks/universal-ide-agents-guard.py` | `.claude/hooks/universal-ide-agents-guard.py` |
| Claude Code | `mcp/templates/` (filtrado por perfil) | `.claude/mcp.example.json` |
| Copilot (`vscode`) | `agents/`, `skills/`, `rules/` | `.github/agents/<n>.agent.md`, `.github/skills/<n>/`, `.github/instructions/<n>.instructions.md` |
| Todos | — | `.agents/universal-ide-agents.json` (manifiesto) |

Ya no se despliegan `AGENTS.md`, `CLAUDE.md`, `.antigravity-instructions.md` (Antigravity no lo lee), `.github/copilot-instructions.md`, `.github/hooks/`, `docs/` ni `scripts/`.

## 2. Perfiles

| Perfil | Extiende | Añade |
| :--- | :--- | :--- |
| `core` | — | Agentes y skills del núcleo, reglas `diagramming-svg`, `evidence-verification` y `three-level-limits`; MCP `context7`. |
| `data-eng-base` | `core` | Agentes de ingeniería de datos, skills de MongoDB y de modelado, reglas de MongoDB y de entornos Python; MCP `mongodb`. |
| `data-eng-n8n` | `data-eng-base` | `n8n-workflow-engineering`. |
| `data-eng-dagster-duckdb` | `data-eng-base` | Dagster, guardas Medallion, DuckDB/DuckLake, offload MongoDB a DuckDB; regla de DuckDB/Dagster/dbt; MCP `dagster` y `duckdb`. |
| `data-eng-lakehouse` | `data-eng-dagster-duckdb` | dbt, PySpark/Delta/Iceberg, Kafka/Debezium, Airflow, triaje de incidentes; MCP `dbt` y `postgres`. |
| `data-eng-full` | `data-eng-n8n`, `data-eng-lakehouse` | Docker, ML, procesamiento paralelo y todas las reglas. Para explorar, no para un proyecto real. |

Los perfiles se combinan: `--profile data-eng-n8n,data-eng-dagster-duckdb`. La categoría `hub` (`knowledge-harvester` como skill, `skill-creator`, `planning-and-versioning`) es de este repositorio y ningún perfil la despliega.

## 3. Flujo en un proyecto

```bash
# Una vez: el submódulo por HTTPS (no hace falta llave SSH)
git submodule add https://github.com/Sebastian93BC/universal-ide-agents.git .modules/universal-ide-agents

# Previsualizar, desplegar y verificar
.modules/universal-ide-agents/scripts/deploy-to-project.sh --dry-run --profile data-eng-n8n .
.modules/universal-ide-agents/scripts/deploy-to-project.sh --profile data-eng-n8n .
python3 .modules/universal-ide-agents/scripts/check.py --project .

# Actualizar
git submodule update --remote .modules/universal-ide-agents
.modules/universal-ide-agents/scripts/deploy-to-project.sh --profile data-eng-n8n .
```

## 4. Qué carga cada IDE

**Antigravity**, según su documentación, leída el 2026-11-25 ([customization discovery](https://antigravity.google/docs/customization-discovery/), [rules](https://antigravity.google/docs/rules.md), [skills](https://antigravity.google/docs/skills.md)):

- Lee `AGENTS.md`, `GEMINI.md` y la carpeta `.agents/` de la carpeta de trabajo y de cada carpeta superior hasta la raíz del repositorio. `.agent/` sigue funcionando por compatibilidad, pero la recomendada es `.agents/`.
- `AGENTS.md` y `GEMINI.md` no llevan frontmatter y están siempre activos. En ellos, `@archivo` se reescribe como referencia a una ruta y no inserta el contenido; `@[etiqueta](ruta)` sí lo inserta. Por eso un `GEMINI.md` con `@AGENTS.md` no duplica nada.
- `.agents/rules/*.md` se lee a un solo nivel. Cada regla necesita frontmatter con `trigger` (`always_on`, `model_decision`, `glob` o `manual`); si falta o no es válido, **la descarta en silencio**. `validate_and_build.py` lo comprueba. El límite es de 24.000 bytes por regla y de 20.000 tokens entre todas las reglas activas. Este repositorio se impone 12.000 caracteres.
- `.agents/skills/<carpeta>/SKILL.md`, a un nivel; `description` es obligatoria y `name` toma por defecto el nombre de la carpeta. Agentes propios en `.agents/agents/<n>.md`. MCP en `.agents/mcp_config.json`.
- No lee `.antigravity-instructions.md`, que por eso se eliminó.

**Claude Code**, comprobado en una sesión real el 2026-11-25: `CLAUDE.md` importa `AGENTS.md` con `@AGENTS.md`, y carga `.claude/rules/*.md`, `.claude/skills/` y `.claude/agents/`. Los hooks se declaran en `.claude/settings.json` (ver el contrato, sección 5).

**Copilot (VS Code)**, sin comprobar en esta revisión (`[INFERIDO]`): `AGENTS.md`, `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` según `applyTo`, `.github/agents/` y `.github/skills/`.

## 5. Servidores MCP

Copia el ejemplo filtrado a la ruta del IDE y define las variables de entorno sin escribir credenciales en el archivo: Antigravity en `.agents/mcp_config.json`, Claude Code en `.mcp.json` en la raíz, y VS Code en `.vscode/mcp.json`, cambiando la clave `"mcpServers"` por `"servers"`. El catálogo está en [core/mcp/catalog.md](../core/mcp/catalog.md).
