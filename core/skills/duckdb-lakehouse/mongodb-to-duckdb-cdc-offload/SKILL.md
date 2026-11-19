---
name: mongodb-to-duckdb-cdc-offload
description: Patrón de descarga analítica (Analytical Offload) desde MongoDB transaccional hacia Parquet y DuckDB/DuckLake mediante Change Streams o incrementales por marca de agua, con deduplicación vectorizada QUALIFY ROW_NUMBER() y manejo de tombstones.
---

# MongoDB to Parquet/DuckDB Analytical CDC Offload

## Cuándo Activar esta Skill
- Cuando necesitas ejecutar analítica pesada, cruces históricos o modelos `dbt` sobre datos originados en **MongoDB** sin degradar el cluster OLTP transaccional.
- Al diseñar un pipeline de sincronización incremental o CDC desde colecciones MongoDB hacia **Parquet + DuckDB/DuckLake**.

## 1. Arquitectura de Offload en 3 Pasos

1. **Extracción desde MongoDB (Change Streams o Marca de Agua Incremental)**:
   - Lee de un **nodo secundario (`readPreference=secondaryPreferred`)** o consume el *Change Stream* / *Debezium connector*.
   - Exporta lotes hacia archivos Parquet inmutables en **Bronze** conservando:
     - `_id` (serializado como string canónico).
     - `_op_type` (`'c'` create/insert, `'u'` update, `'d'` delete/tombstone, `'r'` snapshot read).
     - `_cluster_time` / `updatedAt` (marca temporal monotónica del evento).
     - Columnas críticas extraídas al nivel raíz (`entity_hash`, `amount_cents`, `process_date`) y subdocumentos variables serializados como `JSON` o `STRUCT`.
2. **Compactación y Deduplicación Vectorizada en Silver con DuckDB**:
   - Usa la cláusula `QUALIFY` de DuckDB para obtener el último estado de cada `_id` y descartar los registros eliminados (*tombstones* `_op_type = 'd'`):
   ```sql
   CREATE OR REPLACE TABLE silver.transactions_current AS
   SELECT
       _id AS transaction_id,
       entity_hash,
       CAST(amount_cents AS BIGINT) AS amount_cents,
       CAST(process_date AS DATE) AS process_date,
       payload_json,
       _cluster_time AS last_event_ts
   FROM read_parquet('data/bronze/mongodb_tx/**/*.parquet')
   QUALIFY ROW_NUMBER() OVER (
       PARTITION BY _id
       ORDER BY _cluster_time DESC
   ) = 1
   AND _op_type != 'd'
   ORDER BY process_date, entity_hash;
   ```
3. **Extracción Vectorizada de Subdocumentos JSON en DuckDB**:
   - En lugar de aplanar JSON fila por fila en Python (lento en CPU), delega el parsing JSON al motor vectorizado en C++ de DuckDB:
   ```sql
   SELECT
       transaction_id,
       json_extract_string(payload_json, '$.merchant.categoryCode') AS mcc,
       CAST(json_extract(payload_json, '$.feeCents') AS BIGINT) AS fee_cents
   FROM silver.transactions_current;
   ```
