---
name: duckdb-parquet-optimization
description: Optimización de DuckDB y Parquet para procesamiento analítico de alto volumen: Zone Maps (Min-Max row group pruning) vs hiper-particionamiento Hive, control de memoria (memory_limit, temp_directory), escrituras atómicas y modelo de concurrencia single-writer.
---

# DuckDB & Parquet High-Volume Optimization

## Cuándo Activar esta Skill
- Al diseñar consultas analíticas, transformaciones batch o almacenamiento Parquet con **DuckDB** sobre millones de filas transaccionales.
- Al diagnosticar errores de bloqueo de archivo `.duckdb` (*IO Error: Could not set lock on file*) o errores de falta de memoria (OOM).

## 1. Zone Maps vs. Hiper-particionamiento Hive

**Anti-patrón**: Particionar archivos Parquet por columnas de alta cardinalidad o crear miles de archivos pequeños (`< 10 MB`). El sobrecosto de abrir metadatos de miles de archivos destruye el rendimiento de lectura de DuckDB.

**Patrón de Producción (*Sorted Parquet + Zone Maps*)**:
1. Mantén particiones de directorio gruesas (por ejemplo `year=YYYY/month=MM` o un archivo por corte diario si pesa entre `100 MB` y `512 MB`).
2. **Ordena físicamente los datos antes de escribir el Parquet**:
   ```sql
   COPY (
       SELECT *
       FROM staging_transactions
       ORDER BY transaction_date, entity_id
   ) TO 'data/silver/transactions_2026_11.parquet'
   (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 122880);
   ```
3. Gracias al `ORDER BY`, cada *Row Group* de Parquet almacena estadísticas `min/max` estrechas (*Zone Maps*). Cuando DuckDB ejecuta `WHERE entity_id = 'X' AND transaction_date = '2026-11-18'`, salta el 99% de los *row groups* sin leerlos de disco.

## 2. Modelo de Concurrencia de DuckDB (*Single-Writer Rule*)

- Un archivo `.duckdb` soporta:
  - **1 proceso en modo lectura/escritura (`READ_WRITE`)** y **0 procesos adicionales** (ni siquiera lectores externos), **O BIEN**
  - **N procesos concurrentes si TODOS abren la base con `READ_ONLY = TRUE`**.
- **Reglas Arquitectónicas**:
  1. Para pipelines con múltiples workers paralelos (ej. Dagster `multiprocess_executor`), usa DuckDB como **motor de cómputo en memoria (`:memory:`) que lee y escribe archivos Parquet inmutables** (o usa **DuckLake**), en lugar de compartir un archivo `.duckdb` monolítico de escritura.
  2. Para herramientas de exploración, BI o servidores MCP (`mcp-server-duckdb`), conecta **siempre en modo `--read-only`** o consulta directamente las vistas sobre archivos Parquet (`read_parquet('data/gold/*.parquet')`).

## 3. Control de Memoria y Spill-to-Disk en Cargas Big Data

Configura explícitamente cada conexión de procesamiento pesado para evitar que el contenedor muera por OOM (`exit code 137`):
```sql
SET memory_limit = '6GB';           -- 75-80% de la RAM asignada al contenedor
SET temp_directory = '/tmp/duckdb_spill';
SET preserve_insertion_order = false; -- Reduce drásticamente el uso de RAM en COPY/GROUP BY masivos
```
