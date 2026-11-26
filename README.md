# universal-ide-agents

Agentes, skills y reglas de ingeniería de datos que se escriben una vez y se instalan en cualquier proyecto para Claude Code, Antigravity y GitHub Copilot a la vez. La instalación copia los archivos donde cada IDE los busca y no toca las instrucciones propias del proyecto (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`).

## Qué trae

- **Agentes**, 11: un planificador, un implementador, revisores de código y de pipelines, un auditor de seguridad de datos, un especialista en TDD, uno de documentación, uno de triaje de incidentes, uno de modelado de datos, un ingeniero de datos y un curador de conocimiento que, al cerrar una tarea, pasa lo aprendido al conocimiento del proyecto.
- **Skills**, 39: instrucciones que el agente carga solo cuando el tema aparece. Hay de MongoDB, modelado de datos, n8n, Dagster, DuckDB/Parquet, dbt, Spark, Kafka y Docker, además de la nota de traspaso entre sesiones.
- **Reglas**, 7: se aplican siempre o según el tipo de archivo. Entre ellas, **los límites del agente**: trabajar en la rama `local`; preguntar antes de escribir en una base del cliente, desplegar o hacer commit; nunca leer credenciales ni borrar una colección. Un **guardián** para Claude Code las hace cumplir.
- **Plantillas de servidores MCP** de solo lectura (MongoDB, DuckDB, Dagster, dbt, PostgreSQL), sin credenciales escritas.

Qué hace cada uno está en [docs/asset-catalog.md](docs/asset-catalog.md); qué incluye cada perfil, en [docs/multi-ide-consumption.md](docs/multi-ide-consumption.md).

## Instalarlo en un proyecto

Hace falta `git` y `python3`, 3.9 o superior. No se instala ningún paquete.

**1. Añádelo como submódulo**, desde la raíz de tu proyecto. Funciona por HTTPS, sin llave SSH:

```bash
git submodule add https://github.com/Sebastian93BC/universal-ide-agents.git .modules/universal-ide-agents
```

Si no quieres un submódulo, clónalo en cualquier carpeta y usa esa ruta en los comandos siguientes.

**2. Elige el perfil.** Decide qué llega a tu proyecto. Parte del base y añade la herramienta con la que orquestas; si usas varias, sepáralas con comas.

| Perfil | Para qué proyecto |
| :--- | :--- |
| `core` | Cualquiera: ciclo de trabajo, revisión, límites. |
| `data-eng-base` | Datos sin herramienta de orquestación todavía: `core` más MongoDB y modelado. |
| `data-eng-n8n` | El base más n8n. |
| `data-eng-dagster-duckdb` | El base más Dagster, DuckDB y Parquet. |
| `data-eng-lakehouse` | El de Dagster más dbt, Spark, Kafka y Airflow. |
| `data-eng-full` | Todo; útil para explorar, no para un proyecto real. |

**3. Mira lo que haría y después instálalo:**

```bash
.modules/universal-ide-agents/scripts/deploy-to-project.sh --dry-run --profile data-eng-n8n .
.modules/universal-ide-agents/scripts/deploy-to-project.sh --profile data-eng-n8n .
```

Solo escribe bajo `.agents/` (Antigravity), `.claude/` (Claude Code) y `.github/` (Copilot), y deja la lista de lo que instaló en `.agents/universal-ide-agents.json`. Si encuentra un archivo que no es suyo, o uno suyo que alguien editó, se detiene sin escribir nada; `--force` lo sobrescribe. Con `--target claude` (o `antigravity`, `vscode`) instala solo para un IDE.

**4. Comprueba que quedó bien:**

```bash
python3 .modules/universal-ide-agents/scripts/check.py --project .
```

Verifica la lista, que cada archivo instalado sigue igual y que `AGENTS.md`, `CLAUDE.md` y `GEMINI.md` no cambiaron.

**5. Opcional: activa el guardián en Claude Code.** El archivo `.claude/hooks/universal-ide-agents-guard.py` ya está instalado; para activarlo, añade el bloque `hooks` de [docs/template-dfa-contract.md](docs/template-dfa-contract.md), sección 5, a tu `.claude/settings.json`. Para los servidores MCP, copia el ejemplo instalado (`.claude/mcp.example.json` o `.agents/mcp_config.example.json`) a la ruta de tu IDE y define las variables de entorno.

**Actualizar:** `git submodule update --remote .modules/universal-ide-agents` y repite el paso 3. Lo que ya no corresponde al perfil se borra; lo que editaste se conserva y se avisa.

**Quitarlo:** borra los archivos que lista `.agents/universal-ide-agents.json`, el propio archivo y el submódulo.

## Cómo está organizado este repositorio

| Carpeta | Qué es | ¿Se edita? |
| :--- | :--- | :--- |
| `core/` | La fuente: agentes, skills, reglas, el guardián y la plantilla MCP, en un formato común a los tres IDE. | Sí, solo aquí. |
| `.agents/`, `.claude/`, `.github/` | Copias generadas desde `core/` con el nombre y la carpeta que espera cada IDE. Están en git para que el repositorio funcione en los tres IDE al abrirlo. | No; se regeneran. |
| `profiles/` | Qué incluye cada perfil. Un perfil puede extender otro (`extends`). | Sí. |
| `scripts/` | Compilar, instalar, verificar, buscar datos sensibles y cosechar conocimiento. | Sí. |
| `harvester/` | Configuración del harvester (ver más abajo). Lo tuyo va en archivos `*.local.json`, que git ignora. | Solo el ejemplo. |
| `docs/` | Catálogo, guía por IDE y contrato de integración. | Sí. |
| `plans/` | Registro local de tareas de quien mantiene el repositorio. Git lo ignora y no se publica. | Local. |

Por ejemplo, la regla `core/rules/core/three-level-limits.rule.md` se copia como `.agents/rules/three-level-limits.md`, `.claude/rules/three-level-limits.md` y `.github/instructions/three-level-limits.instructions.md`.

## Trabajar en este repositorio

1. Edita en `core/`. Una skill nueva va en `core/skills/<categoría>/<nombre>/SKILL.md`, y el campo `name` debe ser igual al nombre de la carpeta; si no, el IDE la ignora sin avisar. Añádela a un perfil y a `docs/asset-catalog.md`.
2. Genera las copias: `python3 scripts/validate_and_build.py`.
3. Verifica: `make check`. `make` es una herramienta que ya trae macOS y el `Makefile` solo guarda atajos. `make check` comprueba lo mecánico (formato, copias al día, enlaces, que no haya nombres de cliente, correos, tokens ni rutas personales) y corre las pruebas. Lo mismo se ejecuta en cada pull request.

Las instrucciones para los agentes que trabajan aquí están en [AGENTS.md](AGENTS.md).

Para instalar y mantener la capa en un proyecto, ver [docs/usage-guide.md](docs/usage-guide.md).

## Cosechar conocimiento de tus carpetas (harvester)

El harvester sirve para alimentar este repositorio con lo que aprendes en tus proyectos. Recorre las carpetas que le indiques (proyectos, cursos, memorias de los IDE) y encuentra los archivos de agentes, reglas o memorias nuevos o cambiados desde la última vez. Con eso escribe un informe en `harvester/inbox/<fecha>/harvest_report.md`, en el que marca los que mencionan a tus clientes. Después le pides al agente `knowledge-harvester` que generalice lo útil y lo lleve a `core/`.

```bash
python3 scripts/harvest.py --init            # crea harvester/sources.local.json desde el ejemplo
python3 scripts/harvest.py --check-config    # qué carpetas y cuántos archivos leería, sin escribir nada
python3 scripts/harvest.py                   # cosecha y escribe el informe
python3 scripts/harvest.py --mark-processed  # además recuerda lo visto, para informar solo de cambios
```

Qué lee y dónde se configura en `harvester/sources.local.json`. Si prefieres otro archivo, usa `--config RUTA` o la variable `UIA_HARVEST_CONFIG`.

| Campo | Qué hace |
| :--- | :--- |
| `watchRoots` | Las carpetas que recorre. Cada una lleva `id`, `path` (admite `~`), `category` (`projects`, `courses`, `research` o `agent-memory`) y `maxDepth`. |
| `includePatterns` | Qué archivos lee, como patrones (`AGENTS.md`, `.claude/**/*.md`, `**/memory/*.md`). Valen a cualquier profundidad, así una carpeta puede contener muchos proyectos. Cada carpeta puede tener los suyos. |
| `fileExtensions`, `excludeDirs` | Extensiones admitidas y carpetas que se saltan, como `node_modules` o `.venv`. |

Los nombres de tus clientes van en `harvester/sanitization.local.json` (`{"forbiddenClientTerms": ["ACME"]}`), que git ignora. Se suman a los de `harvester/schema/sanitization_rules.json` y los usan el informe, el validador y el escáner. El harvester nunca recorre este mismo repositorio.

## Más documentación

| Documento | Cuándo leerlo |
| :--- | :--- |
| [docs/usage-guide.md](docs/usage-guide.md) | Para instalar, elegir perfil, desplegar, verificar, actualizar y quitar la capa en un proyecto. |
| [docs/asset-catalog.md](docs/asset-catalog.md) | Para saber qué hace cada agente, skill y regla. |
| [docs/multi-ide-consumption.md](docs/multi-ide-consumption.md) | Para saber qué archivo va a qué carpeta en cada IDE y qué carga cada uno. |
| [docs/template-dfa-contract.md](docs/template-dfa-contract.md) | Si integras la instalación en una plantilla de proyectos: el manifiesto, la verificación, el guardián y el cierre de tarea. |
| [core/mcp/catalog.md](core/mcp/catalog.md) | Para configurar los servidores MCP con seguridad. |
| [core/playbooks/data-engineering-production-playbook.md](core/playbooks/data-engineering-production-playbook.md) | Para incidentes de producción ya resueltos: síntoma, causa y arreglo. |
| [CHANGELOG.md](CHANGELOG.md) | Para ver qué cambió en cada versión. |
