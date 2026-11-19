---
name: dagster-duckdb-dbt-integration
description: Integración de producción entre Dagster, DuckDB/DuckLake y dbt (dagster-dbt): resolución del bloqueo single-writer de DuckDB mediante concurrency_key o Parquet intermedio, sincronización de particiones Dagster -> dbt --vars y exposición de dbt tests como Asset Checks.
---

# Dagster + DuckDB / DuckLake + dbt Integration

## Cuándo Activar esta Skill
- Al orquestar un proyecto **dbt** con motor **DuckDB / DuckLake** dentro de **Dagster** (`@dbt_assets`, `DbtCliResource`).
- Al resolver errores de bloqueo de archivo `.duckdb` cuando Dagster ejecuta múltiples procesos en paralelo.

## 1. Solución al Bloqueo Single-Writer de DuckDB en Dagster

Cuando Dagster usa `multiprocess_executor` (por defecto), cada step se ejecuta en un proceso OS separado. Si dos procesos intentan abrir el mismo archivo `warehouse.duckdb` en modo escritura simultáneamente, DuckDB lanza `IO Error: Could not set lock on file`.

**Tres Patrones de Solución**:
1. **Ejecución Unificada dentro de `@dbt_assets` + `concurrency_key` Global**:
   - Deja que una única invocación `dbt.cli(["build"], context=context)` gestione los hilos internos (`threads: 4` en `profiles.yml` dentro del mismo proceso) y etiqueta cualquier otro asset Python que escriba al archivo `.duckdb` con la misma clave de concurrencia:
   ```python
   @dg.asset(op_tags={"dagster/concurrency_key": "duckdb_single_writer"})
   def ingest_bronze_to_duckdb(context: dg.AssetExecutionContext):
     ...
```
2. **Almacenamiento Intermedio en Parquet / DuckLake (Recomendado para Alta Concurrencia)**:
   - Los assets de ingesta en Python escriben archivos Parquet inmutables por partición (`data/bronze/date=YYYY-MM-DD/part.parquet`) sin abrir ningún archivo `.duckdb`.
   - Luego, `dbt-duckdb` lee esos Parquet con `read_parquet()` o los registra en el catálogo **DuckLake**.

## 2. Sincronización de Particiones `Dagster -> dbt` (`partition_time_window`)

Pasa los límites exactos de la partición de Dagster hacia `dbt` mediante `--vars` para backfills idempotentes (compatible tanto con modelos incrementales clásicos como con `microbatch`):

```python
import json
import dagster as dg
from dagster_dbt import DbtCliResource, dbt_assets

daily_partitions = dg.DailyPartitionsDefinition(start_date="2026-01-01")


@dbt_assets(
    manifest=MANIFEST_PATH,
    partitions_def=daily_partitions,
    op_tags={"dagster/concurrency_key": "duckdb_single_writer"},
)
def lakehouse_dbt_assets(
    context: dg.AssetExecutionContext, dbt: DbtCliResource
):
  time_window = context.partition_time_window
  dbt_vars = {
      "min_date": time_window.start.strftime("%Y-%m-%d"),
      "max_date": time_window.end.strftime("%Y-%m-%d"),
  }
  yield from dbt.cli(
      ["build", "--vars", json.dumps(dbt_vars)],
      context=context,
  ).stream()
```
