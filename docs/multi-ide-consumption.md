# Guía de Consumo e Integración Multi-IDE (`universal-ide-agents`)

Este documento unifica las instrucciones para consumir y sincronizar los activos de **Ingeniería de Datos** de `universal-ide-agents` en **Google Antigravity / Gemini CLI**, **Claude Code** y **VS Code / GitHub Copilot**.

---

## 1. Matriz de Mapeo de Rutas por IDE

El script de despliegue [deploy-to-project.sh](./scripts/deploy-to-project.sh) distribuye los activos compilados desde `core/` hacia el proyecto destino según el `--target` elegido (`all`, `antigravity`, `claude` o `vscode`):

| Ecosistema IDE | Origen en `universal-ide-agents` | Destino en el Proyecto Consumidor | Propósito |
| :--- | :--- | :--- | :--- |
| **Transversal (Todos)** | `AGENTS.md` | `AGENTS.md` | Constitución raíz multi-agente e índice de *Progressive Disclosure*. |
| **Transversal (Todos)** | `plans/README.md` | `plans/README.md` + `plans/{knowledge,walkthroughs,historyPlans}` | Inicialización segura del Control Room sin sobrescribir `plans/registry.md`. |
| **Antigravity / Gemini CLI** | `.agents/{agents,skills,rules}/` | `.agents/{agents,skills,rules}/` | Auto-discovery nativo de agentes, 25 skills (`<= 12,000` chars) y reglas en Antigravity. |
| **Antigravity / Gemini CLI** | `.antigravity-instructions.md` | `.antigravity-instructions.md` | Directrices base de Antigravity en raíz. |
| **Claude Code** | `.claude/{agents,skills,rules}/` | `.claude/{agents,skills,rules}/` | Subagentes, skills y reglas modulares para Claude Code. |
| **Claude Code** | `CLAUDE.md` | `CLAUDE.md` | Punto de entrada automático para Claude Code CLI. |
| **VS Code / GitHub Copilot** | `.github/{agents,skills,instructions,hooks}/` | `.github/{agents,skills,instructions,hooks}/` | Custom agents (`.agent.md`), skills (`SKILL.md`), instrucciones por glob y hooks de sesión. |
| **VS Code / GitHub Copilot** | `.github/copilot-instructions.md` | `.github/copilot-instructions.md` | Instrucciones globales de repositorio para GitHub Copilot. |

---

## 2. Flujo de Integración Recomendado

### Opción A — Despliegue Directo desde tu Hub Central Local
```bash
# 1. Previsualizar qué se copiará (--dry-run)
/ruta/a/universal-ide-agents/scripts/deploy-to-project.sh --dry-run --target all --profile data-eng-full "$PWD"

# 2. Desplegar hacia todos los IDEs (o filtrar con --target antigravity|claude|vscode)
/ruta/a/universal-ide-agents/scripts/deploy-to-project.sh --target all --profile data-eng-full "$PWD"

# 3. Sincronizar eliminando activos obsoletos (--clean)
/ruta/a/universal-ide-agents/scripts/deploy-to-project.sh --clean --target all --profile data-eng-full "$PWD"
```

### Opción B — Integración vía Submódulo Git (`.githubconfig/universal-ide-agents`)
```bash
# Configuración inicial en el proyecto consumidor
git submodule add git@github.com:Sebastian93BC/universal-ide-agents.git .githubconfig/universal-ide-agents
./.githubconfig/universal-ide-agents/scripts/deploy-to-project.sh "$PWD"

# Actualización periódica del submódulo
git submodule update --remote --merge
./.githubconfig/universal-ide-agents/scripts/deploy-to-project.sh --clean "$PWD"
```

---

## 3. Flujo de Trabajo Unificado entre IDEs (Planning -> Execution -> Review)

| Etapa | Rol / Agente Activo | Artefacto de Entrada / Salida | Regla de Gobernanza |
| :--- | :--- | :--- | :--- |
| **1. Investigación Previa** | `planner` / `data-engineer` / `data-modeling-architect` | Lectura de `plans/registry.md` y `plans/knowledge/` | Modo **100% solo lectura** para explorar esquemas, índices y contratos sin contaminar el contexto. |
| **2. Planificación** | `planner` (o Planning Mode en Antigravity) | `plans/YYYY-MM-DD-tarea_plan.md` | Registrar en `plans/registry.md` (`En Progreso`), usar secciones `## ` (Parser V5) y **cero diagramas Mermaid** (solo SVG o tablas Markdown). |
| **3. Implementación / TDD** | `implementer` / `tdd-cycle` | Código productivo + pruebas (`pytest`, `dbt unit_tests`, `GX`) | Todo script que mute datos debe incluir `--dry-run`, escritura atómica `.tmp` y los **5 Medallion Safety Guards**. |
| **4. Revisión Forense** | `pipeline-reviewer` / `code-reviewer` / `data-security-auditor` | Reporte clasificado por severidad y evidencia | Etiquetar cada hallazgo como `[VERIFICADO]` o `[INFERIDO]` bajo `DEFECTO` \| `CONDICIONAL` \| `ENDURECIMIENTO` \| `PROPUESTA`. |
| **5. Cierre y Cosecha** | `docs-steward` / `knowledge-harvester` | `plans/walkthroughs/*_walkthrough.md` + `CHANGELOG.md` | Archivar plan en `plans/historyPlans/` y ejecutar `python3 scripts/harvest.py` periódicamente para promover nuevos aprendizajes a `core/`. |

---

## 4. Activación de Servidores MCP por IDE

Copia la plantilla [data-eng-full.mcp.json](./core/mcp/templates/data-eng-full.mcp.json) a la ruta correspondiente de tu IDE y exporta las variables de entorno en tu `.env` local (nunca hardcodees credenciales):
- **Antigravity**: `.agents/mcp_config.json` o `~/.gemini/config/mcp_config.json`
- **Claude Code**: `.mcp.json` en la raíz del proyecto
- **VS Code**: `.vscode/mcp.json` (cambiando la clave raíz `"mcpServers"` por `"servers"`)
