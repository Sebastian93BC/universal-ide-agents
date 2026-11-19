# CLAUDE.md — Guía Operativa para Claude Code (`universal-ide-agents`)

Lee primero [AGENTS.md](./AGENTS.md), que actúa como la constitución multi-IDE del repositorio.

## 1. Comandos Esenciales del Repositorio

- **Validar `core/` y compilar hacia `.agents/`, `.claude/` y `.github/`**:
  ```bash
  python3 scripts/validate_and_build.py
  ```
- **Ejecutar cosecha periódica de conocimientos desde proyectos y cursos locales**:
  ```bash
  python3 scripts/harvest.py
  ```
- **Desplegar activos hacia un proyecto consumidor (con previsualización `--dry-run`)**:
  ```bash
  ./scripts/deploy-to-project.sh --dry-run --target all --profile data-eng-full /ruta/al/proyecto
  ```

## 2. Estructura Compilada para Claude Code (`.claude/`)

- **Subagentes Especializados**: `.claude/agents/` (`data-engineer.md`, `data-modeling-architect.md`, `data-security-auditor.md`, `pipeline-reviewer.md`, `pipeline-incident-triage.md`, `planner.md`, `implementer.md`, `code-reviewer.md`, `docs-steward.md`, `tdd-cycle.md`, `knowledge-harvester.md`).
- **Skills Bajo Demanda (`SKILL.md`)**: `.claude/skills/<skill-name>/SKILL.md` (25 skills cubriendo MongoDB, DuckDB/DuckLake, Dagster, dbt, PySpark/Delta/Iceberg, Kafka/Debezium, Great Expectations/OpenLineage, Modelado Políglota, Docker, n8n, OTel y ML Inference).
- **Reglas Modulares**: `.claude/rules/*.md`.
- **Plantilla de Servidores MCP**: `.claude/mcp.example.json` (copiar a `.mcp.json` y definir variables de entorno `${DBT_PROJECT_DIR}`, `${DUCKDB_WAREHOUSE_PATH}`, `${MONGODB_READONLY_URI}`).

## 3. Restricciones Críticas

1. **No edites directamente `.claude/`, `.agents/` ni `.github/skills/`**: son directorios compilados. Edita `core/` y ejecuta `python3 scripts/validate_and_build.py`.
2. **Prohibido usar diagramas Mermaid**: usa SVG en `docs/img/` o tablas Markdown.
3. **Ignora `TO_DO.md`**: usa exclusivamente `plans/registry.md` y `CHANGELOG.md`.
