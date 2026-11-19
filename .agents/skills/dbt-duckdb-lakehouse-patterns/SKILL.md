---
name: dbt-duckdb-lakehouse-patterns
description: Configuración avanzada de dbt-duckdb para arquitecturas Lakehouse sobre Parquet, S3/GCS y DuckLake: external materializations, plugins, macros de lectura tolerantes a evolución de esquema (union_by_name=true) y optimización de memoria.
---

# `dbt-duckdb` Lakehouse & External Parquet Patterns

## Cuándo Activar esta Skill
- Al configurar o escalar un proyecto **dbt** que utiliza el adaptador **`dbt-duckdb`** sobre archivos Parquet locales, S3/GCS o un catálogo **DuckLake**.

## 1. Materializaciones Externas (`external`) y Ordenamiento Físico

En lugar de almacenar tablas pesadas dentro del archivo binario `.duckdb`, configura los modelos Silver y Gold con `materialized='external'` para que `dbt-duckdb` escriba archivos Parquet optimizados y registre vistas ligeras en el catálogo:

```sql
{{
    config(
        materialized='external',
        location='data/gold/fct_daily_metrics.parquet',
        options={
            'format': 'parquet',
            'compression': 'zstd',
            'row_group_size': 122880
        }
    )
}}

SELECT
    metric_date,
    entity_hash,
    tx_count,
    total_amount_cents
FROM {{ ref('int_entity_metrics') }}
ORDER BY metric_date, entity_hash -- Maximiza el pruning por Zone Maps
```

## 2. Lectura Tolerante a Evolución de Esquema (`union_by_name = true`)

Cuando la capa Bronze contiene archivos Parquet generados en distintas fechas donde se añadieron columnas nuevas, la lectura estándar por posición de columna falla. Define siempre las fuentes externas con `union_by_name=true` y `filename=true` para auditoría de linaje:

```sql
SELECT
    *,
    filename AS _source_parquet_file
FROM read_parquet(
    'data/bronze/transactions/**/*.parquet',
    union_by_name = true,
    filename = true
)
```

## 3. Configuración Recomendada en `profiles.yml`

```yaml
lakehouse_duckdb:
  target: prod
  outputs:
    prod:
      type: duckdb
      path: 'data/catalog/warehouse.duckdb'
      threads: 4
      extensions:
        - parquet
        - httpfs
        - json
      settings:
        memory_limit: '6GB'
        temp_directory: '/tmp/duckdb_dbt_spill'
        preserve_insertion_order: false
```
