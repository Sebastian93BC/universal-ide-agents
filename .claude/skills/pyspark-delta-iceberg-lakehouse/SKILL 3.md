---
name: pyspark-delta-iceberg-lakehouse
description: Mejores prácticas 2025-2026 para pipelines distribuidos con PySpark, Delta Lake y Apache Iceberg: Liquid Clustering vs Hive partitioning, Adaptive Query Execution (AQE), prohibición de df.cache() sobre tablas Lakehouse, Deletion Vectors y Change Data Feed (CDF).
---

# PySpark + Delta Lake / Apache Iceberg Lakehouse Patterns

## Cuándo Activar esta Skill
- Cuando el volumen de datos supera el umbral de procesamiento en un solo nodo (`> 100–250 GB` por partición activa) o el entorno corporativo opera sobre **Spark / Databricks / EMR / Dataproc** con **Delta Lake** o **Apache Iceberg**.

## 1. Layout de Tablas: Liquid Clustering y Hidden Partitioning

**Anti-patrón legado**: `PARTITIONED BY (year, month, day, country)` en estilo Hive tradicional. Genera miles de directorios con archivos diminutos (*small-file problem*) y obliga a reescribir toda la tabla si cambia el patrón de consulta.

- **En Delta Lake — Usa `Liquid Clustering` (`CLUSTER BY`)**:
  ```sql
  CREATE TABLE IF NOT EXISTS silver.transactions (
      transaction_id STRING,
      account_hash STRING,
      tx_date DATE,
      amount_cents BIGINT
  )
  USING DELTA
  CLUSTER BY (tx_date, account_hash);
  ```
  - *Ventaja*: Organiza los datos incrementalmente en curvas Hilbert/Z-Order sin directorios rígidos y permite cambiar las claves con `ALTER TABLE ... CLUSTER BY (...)` sin reescribir el histórico.
- **En Apache Iceberg — Usa `Hidden Partitioning`**:
  - Define transformaciones declarativas (`PARTITIONED BY (days(tx_timestamp), bucket(16, account_hash))`) para que los consumidores filtren directamente por `tx_timestamp` sin conocer columnas derivadas de partición.

## 2. Reglas de Cómputo PySpark: AQE Obligatorio y Prohibición de `.cache()`

1. **Activar siempre Adaptive Query Execution (AQE)**:
   ```python
   spark.conf.set("spark.sql.adaptive.enabled", "true")
   spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
   spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```
2. **NO usar `df.cache()` / `df.persist()` sobre lecturas Delta o Iceberg con filtros posteriores**:
   - Cachear un DataFrame en memoria de Spark **elimina las estadísticas de metadatos del formato de tabla**, impidiendo el *file pruning / data skipping* en filtros subsecuentes y arriesgando leer snapshots obsoletos.

## 3. Upserts de Alto Rendimiento (`MERGE INTO` + Deletion Vectors + CDF)

1. **Acotar siempre el predicado del `MERGE INTO` (*Partition/Cluster Pruning*)**:
   - Nunca ejecutes `ON target.id = source.id` a ciegas sobre toda la tabla histórica. Añade explícitamente la cota temporal en la condición `ON`:
   ```sql
   MERGE INTO silver.transactions AS t
   USING updates_batch AS s
   ON t.transaction_id = s.transaction_id
      AND t.tx_date >= current_date() - INTERVAL 7 DAYS
   WHEN MATCHED THEN UPDATE SET *
   WHEN NOT MATCHED THEN INSERT *;
   ```
2. **Habilitar Deletion Vectors (DVs) y Change Data Feed (CDF)**:
   - Con **Deletion Vectors** activos, un `UPDATE` o `DELETE` marca las filas borradas en un bitmap liviano sin reescribir el archivo Parquet completo en caliente, compactándolo luego en background (`OPTIMIZE`).
   - Con **Change Data Feed (`delta.enableChangeDataFeed = true`)**, las capas Gold leen únicamente los deltas (`readChangeFeed=true`) en lugar de re-escanear Silver.
