---
name: otel-pipeline-observability
description: Estándar de instrumentación y observabilidad OpenTelemetry (OTel) para pipelines de datos y agentes: jerarquía de 3 niveles de Spans (Módulo [Root Span] -> Proceso [Parent Span] -> Operación [Child Span]), atributos semánticos de datos y separación entre métricas de sistema y métricas de calidad.
---

# OpenTelemetry (OTel) 3-Level Pipeline & Agent Observability

## Cuándo Activar esta Skill
- Al instrumentar trazabilidad distribuida (**OpenTelemetry**) y logging estructurado JSON en pipelines de datos (**Dagster, Python, n8n, DuckDB, MongoDB**) o sistemas multi-agente.

## 1. Jerarquía Estándar de 3 Niveles de Spans (`Module -> Process -> Operation`)

Todo pipeline o flujo debe estructurar sus trazas respetando exactamente estos 3 niveles causales conectados por un único `trace_id`:

| Nivel | Rol del Span | Qué Representa | Atributos Obligatorios del Span |
| :--- | :--- | :--- | :--- |
| **Nivel 1: `Módulo`** | **`Root Span`** | La corrida completa del pipeline, DAG o workflow extremo a extremo. | `module.name`, `module.version`, `deployment.environment` (`dev`/`staging`/`prod`), `trigger.type` (`schedule`/`sensor`/`manual`), `partition.key`. |
| **Nivel 2: `Proceso`** | **`Parent Span`** (hijo de Módulo) | Una etapa lógica de negocio o capa Medallion (ej. `extract_bronze`, `dedup_silver`, `validate_contract`, `publish_gold`). | `process.name`, `process.stage` (`bronze`/`silver`/`gold`/`seal`), `rows.input`, `rows.output`, `rows.rejected`, `status.code`. |
| **Nivel 3: `Operación`** | **`Child Span`** (hijo de Proceso) | Una llamada atómica a un motor de datos, herramienta MCP o modelo LLM. | `db.system` (`mongodb`/`duckdb`/`postgresql`), `db.operation` (`aggregate`/`COPY`/`MERGE`), `db.collection.name`, `duration_ms`, `error.type` (si falla). |

## 2. Reglas de Higiene y Muestreo en Producción

1. **Redacción de PII Antes de Emitir Spans o Logs**:
   - Prohibido adjuntar documentos crudos con `*_PLAIN`, nombres, teléfonos o credenciales en los atributos de un Span. Registra únicamente identificadores seudonimizados (`entity_hash`) y métricas agregadas.
2. **Separación de Paneles (Salud del Sistema vs. Calidad de Datos/Agente)**:
   - **Métricas de Sistema**: Latencia `P50/P99`, tasa de error técnico, memoria consumida, costo/tokens por corrida.
   - **Métricas de Calidad**: Ratio de retención de filas (*Row Regression*), frescura (*Freshness Lag*), porcentaje de éxito de expectativas GX/dbt y adherencia a la trayectoria del agente.
