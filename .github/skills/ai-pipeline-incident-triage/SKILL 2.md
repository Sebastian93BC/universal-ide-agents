---
name: ai-pipeline-incident-triage
description: Arquitectura de alertas inteligentes y triaje automatizado de incidentes en pipelines de datos usando LLMs/Agentes en modo solo lectura sobre telemetría OpenTelemetry, OpenLineage, Great Expectations y servidores MCP (dagster-mcp, dbt-mcp, duckdb-mcp).
---

# AI-Powered Pipeline Incident Triage & Intelligent Alerting

## Cuándo Activar esta Skill
- Al construir sistemas de **alertas inteligentes y diagnóstico asistido por IA** sobre métricas y fallos de pipelines de datos (hito diferenciador de Ingeniería de Datos + Agentes LLM).
- Al conectar webhooks de fallo de **Dagster / Airflow / dbt / Great Expectations** con un agente de triaje basado en **LangGraph, Claude SDK o Google ADK**.

## 1. Arquitectura Segura de Triaje con Agentes (Read-Only Guardrail)

**Principio Inquebrantable**: Un agente LLM conectado a la plataforma de datos para triaje de incidentes opera con **permisos 100% de solo lectura (`--read-only`)**. El agente diagnostica, calcula el *blast radius* y redacta el comando exacto de remediación/backfill, pero **el humano es el árbitro** (HITL) que aprueba la ejecución en producción.

### Flujo de Eventos del Sistema de Alertas Inteligentes
1. **Disparador (Trigger Event)**:
   - Un run de Dagster/Airflow falla, un `AssetCheck` / `Great Expectations Checkpoint` se rompe o un *Medallion Safety Guard* aborta una promoción en `Seal`.
2. **Ensamblaje de Contexto Determinista (*Context Engineering*)**:
   - El colector adjunta al payload del incidente:
     - El rastro **OpenTelemetry** (`trace_id`, span `Module -> Process -> Operation` donde ocurrió el error).
     - El evento **OpenLineage** con las facetas `ErrorMessageRunFacet` y `DataQualityMetricsInputDatasetFacet`.
     - El diff reciente de Git en los modelos afectados (`git log -n 3`).
3. **Investigación del Agente vía Herramientas MCP Curadas**:
   - `mcp-server-dagster`: Consulta logs del step fallido e historial de las últimas 5 materializaciones.
   - `dbt-mcp`: Inspecciona el linaje upstream/downstream del modelo y los contratos en `schema.yml`.
   - `mcp-server-duckdb` (`--read-only`): Ejecuta consultas de perfilado rápido sobre la partición Bronze/Silver para verificar si llegaron nulos, duplicados o un cambio de esquema.
4. **Salida Estructurada hacia Slack / Teams / PagerDuty / PR**:
   - **Causa Raíz (`[VERIFICADA]` con consulta/evidencia vs `[HIPÓTESIS]`)**.
   - **Blast Radius**: Lista de marts Gold y dashboards bloqueados o en riesgo.
   - **Runbook de Remediación**: Comando CLI listo para copiar/ejecutar en modo `--dry-run` y comando de backfill particionado.
