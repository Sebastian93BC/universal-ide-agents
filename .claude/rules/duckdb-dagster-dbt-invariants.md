---
name: duckdb-dagster-dbt-invariants
description: Invariantes de producción para pipelines Lakehouse con DuckDB/DuckLake, Parquet, Dagster y dbt en contextos de Big Data y Datos Transaccionales.
trigger: model_decision
applyTo: "**/*.py,**/*.sql,**/*.yml,**/*.yaml"
---

# Invariantes de Lakehouse: DuckDB, Parquet, Dagster y dbt

1. **Concurrencia Single-Writer en DuckDB**:
   - Un archivo `.duckdb` no soporta escrituras multiproceso concurrentes. En Dagster, persiste salidas intermedias en **Parquet / DuckLake** o serializa los assets que escriben al mismo `.duckdb` mediante `op_tags={"dagster/concurrency_key": "duckdb_writer"}` (límite `1`).
2. **Zone Maps vs. Hiper-particionamiento en Parquet**:
   - Para datasets `< 100 GB`, no particiones en miles de carpetas por alta cardinalidad (evita archivos `< 10 MB`). Escribe archivos Parquet de `100–512 MB` (`ZSTD`) **ordenados físicamente (`ORDER BY fecha, entidad_id`)** para que DuckDB salte *row groups* vía *Min-Max Zone Maps*.
3. **Buenas Prácticas de Dagster (`dg check defs` y `dg.EnvVar`)**:
   - Ejecuta siempre `dg check defs` tras crear o editar assets/schedules/sensores.
   - Usa `dg.EnvVar("VAR")` en lugar de `os.getenv("VAR")` dentro de recursos configurables de Dagster para evaluación por corrida (*run-time*) y no en carga de módulo.
4. **dbt para Datos Transaccionales (`microbatch`, Contratos y Unit Tests)**:
   - En tablas transaccionales masivas (dbt 1.9+), prefiere `incremental_strategy='microbatch'` con `event_time`, `batch_size` y `lookback` para absorber eventos tardíos.
   - Exige `contract: {enforced: true}` en modelos Gold/Marts públicos y valida lógica de deduplicación/centavos con `unit_tests:` nativos de dbt.
5. **5 Medallion Safety Guards & `--dry-run`**:
   - Todo script de mutación o compactación debe soportar `--dry-run`, escribir a `.tmp` con renombrado atómico y verificar no-regresión de filas (`rows_after >= rows_before * min_ratio`).
