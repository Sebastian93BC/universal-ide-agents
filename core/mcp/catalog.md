# Catálogo Maestro de Servidores MCP para Ingeniería de Datos Multi-IDE

Este directorio centraliza las plantillas y lineamientos de **Model Context Protocol (MCP)** para **Antigravity / Gemini CLI**, **Claude Code** y **VS Code GitHub Copilot**.

## 1. Mapeo de Rutas de Configuración por IDE

| IDE / Agente | Archivo a Nivel de Proyecto | Archivo Global de Usuario | Clave Raíz JSON |
| :--- | :--- | :--- | :--- |
| **Antigravity / Gemini CLI** | `.agents/mcp_config.json` | `~/.gemini/config/mcp_config.json` | `"mcpServers": { ... }` |
| **Claude Code** | `.mcp.json` | `~/.claude.json` | `"mcpServers": { ... }` |
| **VS Code / GitHub Copilot** | `.vscode/mcp.json` | Settings de perfil de VS Code | `"servers": { ... }` |

---

## 2. Servidores MCP Esenciales para Ingeniería de Datos

| Servidor MCP | Paquete / Comando | Casos de Uso en Ingeniería de Datos | Regla de Seguridad Obligatoria |
| :--- | :--- | :--- | :--- |
| **`dbt-mcp`** (Oficial dbt Labs) | `uvx dbt-mcp` | Inspeccionar modelos, linaje upstream/downstream, manifiesto (`manifest.json`), contratos de columnas, ejecutar `dbt show` / `dbt test` y consultar la Capa Semántica. | Apuntar a target `dev` o `ci`; prohibido habilitar mutaciones sobre el target `prod`. |
| **`mcp-server-dagster`** (`dg mcp`) | `uvx dagster-dg-cli mcp serve` | Consultar el grafo de *Software-Defined Assets*, estado de runs, logs de fallos de materialización, particiones y `AssetChecks`. | Modo lectura para diagnóstico y triaje (`pipeline-incident-triage`). |
| **`mcp-server-duckdb`** | `uvx mcp-server-duckdb --db-path ${DUCKDB_PATH} --read-only` | Perfilar archivos Parquet (`read_parquet`), inspeccionar tablas Silver/Gold y verificar Zone Maps sin bloquear pipelines. | **Obligatorio** incluir siempre el flag `--read-only` para no provocar bloqueos *single-writer* contra Dagster/dbt. |
| **`mongodb-mcp-server`** (Oficial MongoDB) | `npx -y mongodb-mcp-server` | Inspeccionar esquemas inferidos (`collection-schema`), planes de ejecución `explain("executionStats")`, índices parciales y distribución de chunks. | Usar variable `${MONGODB_MCP_URI}` con usuario de **solo lectura (`read` / `readAnyDatabase`)** y `readPreference=secondaryPreferred`. |
| **`postgres-mcp`** | `npx -y @modelcontextprotocol/server-postgres ${POSTGRES_MCP_URI}` | Inspeccionar el catálogo relacional (metadatos de **DuckLake**, tablas transaccionales, `pg_stat_activity`, slots de replicación CDC). | Conectar con rol PostgreSQL `default_transaction_read_only = on`. |
| **`docker-mcp`** | `npx -y @modelcontextprotocol/server-docker` | Diagnosticar contenedores caídos, `OOMKilled` (`exit 137`), logs de servicios y estado de `healthchecks`. | No exponer el socket de Docker en hosts remotos sin TLS. |
| **`context7`** | `npx -y @upstash/context7-mcp` | Consultar documentación oficial actualizada al día de DuckDB, Dagster, dbt, MongoDB, PySpark y Delta Lake. | Sin acceso a datos locales. |

---

## 3. Regla de Listas Curadas por Agente Especialista

Siguiendo el principio de **Registros Curados de Herramientas** (AgentOps):
- No habilites más de **5 a 7 servidores MCP simultáneamente** en una misma sesión para evitar inflar la ventana de contexto con cientos de esquemas JSON de herramientas.
- Usa los perfiles de `core/mcp/templates/` según el proyecto activo (`data-eng-full.mcp.json`, `data-eng-mongodb.mcp.json`, `data-eng-lakehouse.mcp.json`).
