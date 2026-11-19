# GitHub Copilot & VS Code Instructions (`universal-ide-agents`)

Consulta [AGENTS.md](../AGENTS.md) en la raíz del repositorio para la constitución completa del sistema.

## 1. Activos Disponibles en `.github/`

- **Agentes Personalizados (`.github/agents/*.agent.md`)**:
  - Ingeniería de Datos: `@data-engineer`, `@data-modeling-architect`, `@data-security-auditor`, `@pipeline-reviewer`, `@pipeline-incident-triage`.
  - Ciclo de Vida Core: `@planner`, `@implementer`, `@code-reviewer`, `@docs-steward`, `@tdd-cycle`, `@knowledge-harvester` (además de los agentes clásicos retrocompatibles `Planner`, `Feature Builder`, `Reviewer`, `Code Reviewer`, `Documentation Steward`, `Data Science Developer`).
- **Skills Modulares (`.github/skills/<skill-name>/SKILL.md`)**: 25 skills especializadas en MongoDB, DuckDB/DuckLake, Dagster, dbt, PySpark/Delta/Iceberg, Kafka/Debezium, Great Expectations/OpenLineage, Modelado Políglota, Docker, n8n, OpenTelemetry y ML Inference.
- **Instrucciones por Tipo de Archivo (`.github/instructions/*.instructions.md`)**: Reglas automáticas para SQL, Python, MongoDB, Dagster, dbt y documentación Markdown.

## 2. Reglas Esenciales
- Edita siempre los activos fuente en `core/` y ejecuta `python3 scripts/validate_and_build.py`.
- Nunca generes bloques `mermaid`; usa SVG o tablas Markdown.
- Mantén `camelCase` en archivos JSON de configuración y preserva `PREPROCESS_CONFIG` en `.github/hooks/context.json`.
- Ignora `TO_DO.md`; gestiona todas las tareas en `plans/registry.md`.
