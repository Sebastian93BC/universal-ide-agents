# Guía de uso: instalar y mantener la capa en un proyecto

Esta guía es para quien instala `universal-ide-agents` en un proyecto. Cubre el submódulo, el perfil, el despliegue, la verificación y el mantenimiento. Para el detalle de cada IDE, ver [multi-ide-consumption.md](./multi-ide-consumption.md). Para la integración con `template-data-flow-automation`, ver [template-dfa-contract.md](./template-dfa-contract.md).

## 1. Qué llega al proyecto y cuándo

Hay dos pasos distintos, y no hacen lo mismo:

| Paso | Qué hace | Qué cambia en el proyecto |
| :--- | :--- | :--- |
| Añadir el submódulo | Descarga el repositorio completo en `.modules/universal-ide-agents/`. | Nada de agentes ni skills. Solo aparece la carpeta del submódulo. |
| Desplegar con un perfil | Copia a `.agents/`, `.claude/` y `.github/` lo que incluye ese perfil. | Aparecen los agentes, skills, reglas y ejemplos MCP del perfil, y el manifiesto `.agents/universal-ide-agents.json`. |

Desplegar no toca `AGENTS.md`, `CLAUDE.md` ni `GEMINI.md`. Esos archivos son del proyecto.

## 2. Instalar

Desde la raíz del proyecto, con `git` y `python3` (3.9 o superior):

```bash
git submodule add https://github.com/Sebastian93BC/universal-ide-agents.git .modules/universal-ide-agents
```

El repositorio es público, así que funciona por HTTPS sin llave SSH.

## 3. Elegir el perfil

El perfil decide qué se copia. Cada perfil extiende a los anteriores:

| Perfil | Incluye | Usar cuando |
| :--- | :--- | :--- |
| `core` | Agentes y skills del núcleo, reglas básicas y los límites del agente. | Cualquier proyecto, sin datos. |
| `data-eng-base` | `core` más MongoDB y modelado de datos. Sin herramienta de orquestación. | Proyecto de datos sin herramienta todavía. Es el valor por defecto. |
| `data-eng-n8n` | `data-eng-base` más la skill de n8n. | Proyecto que orquesta con n8n. |
| `data-eng-dagster-duckdb` | `data-eng-base` más Dagster, DuckDB, Parquet y las guardas Medallion. | Proyecto que orquesta con Dagster y DuckDB. |
| `data-eng-lakehouse` | `data-eng-dagster-duckdb` más dbt, Spark, Kafka y Airflow. | Lakehouse completo. |
| `data-eng-full` | Todo lo anterior. | Explorar. No es para un proyecto real. |

Cifras actuales, medidas sobre el repositorio:

| Perfil | Agentes | Skills | Reglas | Servidores MCP |
| :--- | :---: | :---: | :---: | :--- |
| `core` | 6 | 6 | 3 | context7 |
| `data-eng-base` | 11 | 19 | 5 | context7, mongodb |
| `data-eng-n8n` | 11 | 20 | 5 | context7, mongodb |
| `data-eng-dagster-duckdb` | 11 | 25 | 6 | context7, dagster, duckdb, mongodb |
| `data-eng-lakehouse` | 11 | 33 | 6 | además dbt, postgres |
| `data-eng-full` | 11 | 37 | 6 | todos |

Los perfiles de herramienta no se excluyen entre sí. Si un proyecto usa dos, se combinan.

Los perfiles disponibles están en `.modules/universal-ide-agents/profiles/`.

## 4. Desplegar

Primero, una prueba sin escribir nada:

```bash
.modules/universal-ide-agents/scripts/deploy-to-project.sh --dry-run --profile data-eng-n8n .
```

Muestra lo que crearía, actualizaría y borraría. Después, el despliegue real:

```bash
.modules/universal-ide-agents/scripts/deploy-to-project.sh --profile data-eng-n8n .
```

El punto final es la carpeta del proyecto. Si ejecutas el comando desde otro sitio, pon la ruta del proyecto en su lugar.

Si omites `--profile`, se usa `data-eng-base`. Si escribes un perfil que no existe, el comando falla, no escribe nada y muestra la lista de perfiles válidos.

## 5. Verificar

```bash
python3 .modules/universal-ide-agents/scripts/check.py --project .
```

Comprueba que el manifiesto existe y está completo, que `AGENTS.md`, `CLAUDE.md` y `GEMINI.md` no han cambiado desde el despliegue, que cada archivo instalado sigue igual, que los punteros tienen una línea y que cada skill tiene el mismo nombre que su carpeta. Sale con código 1 si algo falla.

## 6. Cambiar de perfil

Vuelve a desplegar con el perfil nuevo:

```bash
.modules/universal-ide-agents/scripts/deploy-to-project.sh --profile data-eng-dagster-duckdb .
```

Lo que pertenecía al perfil anterior y ya no corresponde se borra. Lo que hayas editado a mano se conserva y el despliegue lo avisa. Antes de cambiar, usa `--dry-run` para ver la lista de borrados.

## 7. Varios perfiles a la vez

Sepáralos con comas, sin espacios:

```bash
.modules/universal-ide-agents/scripts/deploy-to-project.sh --profile data-eng-n8n,data-eng-dagster-duckdb .
```

Repetir el flag también funciona: `--profile data-eng-n8n --profile data-eng-dagster-duckdb`. Se instala la unión de ambos.

## 8. Instalar solo para un IDE

Por defecto se instala para los tres. Con `--target` eliges uno o varios:

```bash
.modules/universal-ide-agents/scripts/deploy-to-project.sh --target claude --profile data-eng-n8n .
```

Valores válidos: `antigravity`, `claude`, `vscode` (o `copilot`), y `all` para los tres. Puedes separar varios con comas.

## 9. Actualizar

```bash
git submodule update --remote .modules/universal-ide-agents
.modules/universal-ide-agents/scripts/deploy-to-project.sh --profile data-eng-n8n .
python3 .modules/universal-ide-agents/scripts/check.py --project .
```

Si el resultado es "Sin cambios", el proyecto ya estaba al día. Después, confirma el nuevo puntero del submódulo con tu propio commit; el despliegue no hace commits.

## 10. Qué hacer si algo falla

| Mensaje | Qué significa | Qué hacer |
| :--- | :--- | :--- |
| `perfil 'xxxx' no existe` | El nombre del perfil está mal. | Usa uno de la lista que muestra el mensaje. |
| `[conflicto] ...: existe y no lo desplegó universal-ide-agents` | Ya hay un archivo con ese nombre que no es de la capa. | Revísalo. Si puedes renombrarlo, hazlo. Si no, `--force` lo sobrescribe. |
| `[conflicto] ...: editado localmente desde el último despliegue` | Editaste un archivo instalado. | Muévele tus cambios a otro sitio, o usa `--force` si quieres la versión del repositorio. |
| `AGENTS.md, CLAUDE.md o GEMINI.md cambiaron durante el despliegue` (código 3) | No debería pasar. | Revisa el proyecto con `git status` antes de seguir. |
| `check.py` avisa de que `AGENTS.md` cambió | La capa del proyecto se editó desde el último despliegue, o la plantilla la actualizó. | No es un error. No hace falta acción. |

El despliegue sale con código 2 cuando hay conflictos y no escribe nada en ese caso.

## 11. Activar el guardián en Claude Code

El archivo `.claude/hooks/universal-ide-agents-guard.py` se instala solo. Para que Claude Code lo use, añade a `.claude/settings.json` del proyecto el bloque `hooks` que aparece en [template-dfa-contract.md](./template-dfa-contract.md), sección 5. El guardián pide confirmación antes de desplegar, de hacer commit o de escribir en una base de un ambiente del cliente, y bloquea la lectura de `.env` y el borrado de colecciones.

## 12. Servidores MCP

El despliegue deja un ejemplo filtrado por perfil: `.claude/mcp.example.json` y `.agents/mcp_config.example.json`. Copia el que corresponda a la ruta de tu IDE:

- Claude Code: `.mcp.json` en la raíz del proyecto.
- Antigravity: `.agents/mcp_config.json`.
- VS Code: `.vscode/mcp.json`, con la clave `"servers"` en lugar de `"mcpServers"`.

Define las variables de entorno que pide cada servidor. No escribas credenciales en el archivo.

## 13. Quitar la capa

Borra los archivos que lista `.agents/universal-ide-agents.json` en su campo `files`, después ese manifiesto y, si quieres, el submódulo:

```bash
git submodule deinit -f .modules/universal-ide-agents
git rm -f .modules/universal-ide-agents
rm -rf .git/modules/.modules/universal-ide-agents
```
