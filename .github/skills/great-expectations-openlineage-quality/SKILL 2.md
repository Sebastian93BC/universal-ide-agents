---
name: great-expectations-openlineage-quality
description: Gobernanza de calidad de datos y linaje extremo a extremo con Great Expectations (GX 1.3+ Python API), Open Data Contract Standard (ODCS) y emisión de eventos OpenLineage para análisis de impacto (blast radius).
---

# Great Expectations + OpenLineage Data Quality Governance

## Cuándo Activar esta Skill
- Al implementar compuertas automatizadas de calidad de datos (**Great Expectations**) y trazabilidad de linaje (**OpenLineage**) en pipelines de Dagster, Airflow, Spark o DuckDB/SQL.
- Al traducir un **Contrato de Datos (ODCS)** en validaciones ejecutables que bloqueen datos corruptos antes de llegar a los consumidores.

## 1. Las 4 Dimensiones de Validación Obligatorias en Contratos de Datos

Toda suite de **Great Expectations (GX)** sobre una tabla Silver o Gold debe cubrir:
1. **Integridad Estructural (Schema & Types)**: `expect_table_columns_to_match_ordered_list` y verificación de tipos de columna esperados.
2. **Unicidad y Completitud de Claves**: `expect_column_values_to_not_be_null` y `expect_compound_columns_to_be_unique` sobre la clave primaria o compuesta `(date, entity_hash)`.
3. **Validez Semántica y Financiera**: `expect_column_values_to_be_between` (montos en centavos no negativos cuando aplique) y `expect_column_values_to_be_in_set` para códigos de operación/estado.
4. **Volumetría y No-Regresión**: `expect_table_row_count_to_be_between` parametrizado dinámicamente según el histórico de la ventana.

## 2. Propagación de Estado de Calidad vía OpenLineage (`Blast Radius`)

No basta con que una validación falle en un log aislado; el fallo debe emitirse como una faceta **OpenLineage (`DataQualityMetricsInputDatasetFacet` / `DataQualityAssertionsDatasetFacet`)** hacia el catálogo (Marquez / OpenMetadata / Atlan / Dagster Asset Graph):

- **Integración en Checkpoints**:
  - Configura `OpenLineageValidationAction` dentro del Checkpoint de Great Expectations (o el `@dg.asset_check(blocking=True)` en Dagster).
  - Cuando una expectativa de severidad `CRITICAL` falla:
    1. El pipeline detiene la etapa `Seal -> Publish` (los consumidores siguen leyendo el último snapshot sano).
    2. El evento OpenLineage marca los datasets aguas abajo como `UNTRUSTED / STALE` y dispara el agente de triaje (`pipeline-incident-triage`) con el grafo exacto de dependencias afectadas.
