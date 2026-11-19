---
name: medallion-safety-guards
description: Los 5 Medallion Safety & Integrity Guards para pipelines de datos productivos (Freshness/Lag Guard, Concurrency/Writer .tmp Guard, Lineage Consistency Guard, Row Regression Guard y AutoApply Dry-Run Judge).
---

# Medallion Architecture — The 5 Safety & Integrity Guards

## Cuándo Activar esta Skill
- Al diseñar o endurecer pipelines de datos batch o incrementales (`Bronze -> Silver -> Gold -> Seal -> Publish`) en **Dagster, Airflow, dbt, DuckDB o MongoDB**.
- Al investigar corrupciones silenciosas, pérdida de filas en compactaciones o lecturas de tablas a medio escribir.

## 1. Catálogo de los 5 Safety Guards Obligatorios

| Guard | Qué Verifica | Regla de Bloqueo (`FAIL / ABORT`) |
| :--- | :--- | :--- |
| **1. Freshness & Lag Guard** | Diferencia entre la fecha de corte (`cutoff_date`) y el `max(event_date)` real presente en la capa origen. | Abortar si `lag_days > max_allowed_lag` (ej. `> 1` día en pipelines diarios) o si la partición entrante está vacía (`row_count == 0`). |
| **2. Concurrency & Atomic Writer Guard (`.tmp`)** | Existencia de locks o archivos temporales `.tmp` antes de escribir, y atomicidad de publicación. | 1. Si existe `target.parquet.tmp` con antigüedad `< timeout`, abortar por ejecución concurrente activa.<br>2. Escribir siempre a `target.parquet.tmp`, validar integridad y ejecutar `os.replace(tmp, final)` (operación POSIX atómica). |
| **3. Lineage Consistency Guard** | Coherencia temporal entre capas padre e hijo (`Bronze -> Silver -> Gold`). | Una capa hija (`Gold`) nunca puede marcarse como válida si su `source_snapshot_ts` es anterior al último `commit_ts` de su capa padre (`Silver`). |
| **4. Row Regression Guard** | Ratio de retención de filas y sumas de control antes y después de actualizar/compactar una tabla. | Abortar la promoción en `Seal` si `rows_after < rows_before * min_retention_ratio` (por defecto `0.98` en tablas acumulativas) salvo que se pase explícitamente `allow_compaction_shrink=True`. |
| **5. AutoApply Dry-Run Judge** | Separación entre el diagnóstico/plan de mutación (`--dry-run`) y la ejecución física. | Toda rutina de mantenimiento, backfill o limpieza calcula primero el diff en modo `--dry-run`. Un juez determinista evalúa si el impacto está dentro de los umbrales seguros antes de aplicar cambios. |

## 2. Plantilla de Implementación en Python (Portable a Dagster / Airflow / CLI)

```python
from pathlib import Path
import shutil


def atomic_write_with_row_guard(
    temp_path: Path,
    final_path: Path,
    rows_before: int,
    rows_after: int,
    min_retention_ratio: float = 0.98,
    dry_run: bool = False,
) -> dict:
  if rows_before > 0 and (rows_after / rows_before) < min_retention_ratio:
    raise RuntimeError(
        f"[ROW_REGRESSION_GUARD] Abortado: rows_after ({rows_after}) < "
        f"{min_retention_ratio:.1%} de rows_before ({rows_before})."
    )
  if dry_run:
    return {
        "status": "DRY_RUN_OK",
        "rows_before": rows_before,
        "rows_after": rows_after,
    }
  if not temp_path.exists():
    raise FileNotFoundError(f"[WRITER_GUARD] No existe el archivo temporal {temp_path}")
  temp_path.replace(final_path)
  return {
      "status": "PUBLISHED",
      "final_path": str(final_path),
      "rows_after": rows_after,
  }
```
