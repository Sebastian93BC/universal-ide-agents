---
name: airflow-dagster-interoperability
description: Guía de interoperabilidad y traducción arquitectónica entre Dagster (Software-Defined Assets) y Apache Airflow (TaskFlow API @task, Datasets/Assets en Airflow 2.8+/3.x y Astronomer Cosmos para dbt).
---

# Airflow <-> Dagster Interoperability & Migration Guide

## Cuándo Activar esta Skill
- Cuando necesitas traducir un pipeline diseñado bajo el paradigma *Asset-Centric* de **Dagster** hacia **Apache Airflow** (estándar corporativo en muchas empresas LatAm/Enterprise) o viceversa.
- Al integrar proyectos **dbt** dentro de Apache Airflow evitando el anti-patrón de ejecutar todo `dbt run` como una única caja negra `BashOperator`.

## 1. Tabla de Equivalencia Arquitectónica (`Dagster <-> Airflow 2.8+ / 3.x`)

| Concepto de Ingeniería | Implementación en **Dagster** | Implementación Equivalente en **Apache Airflow** |
| :--- | :--- | :--- |
| **Unidad de Datos / Nodo del Grafo** | `@dg.asset` (centrado en el activo de datos producido). | `@task` (TaskFlow API) emitiendo a un `Dataset("s3://.../tabla")` (Data-aware scheduling). |
| **Integración con `dbt`** | `@dbt_assets` (`dagster-dbt`) — cada modelo/test de dbt es un asset/check nativo. | **Astronomer Cosmos (`DbtTaskGroup` / `DbtDag`)** — convierte cada modelo dbt en un `TaskGroup` nativo con `dbt_run` + `dbt_test` por nodo. |
| **Inyección de Configuración / Secretos** | `ConfigurableResource` + `dg.EnvVar("VAR")`. | **Airflow Connections & Variables** accedidas dentro del `@task` o vía Secrets Backend (Vault / AWS Secrets Manager / GCP Secret Manager). |
| **Ventana de Partición (Backfills)** | `context.partition_time_window` (`start`, `end`). | `data_interval_start` y `data_interval_end` (nunca usar `datetime.now()` ni `execution_date` legado). |
| **Control de Concurrencia (ej. DuckDB lock)** | `op_tags={"dagster/concurrency_key": "duckdb_writer"}`. | **Airflow Pools** (`pool="duckdb_writer_pool"`, `slots=1`, `pool_slots=1`). |
| **Compuerta de Calidad (Quality Gate)** | `@dg.asset_check(..., blocking=True)`. | Operadores **SQLColumnCheckOperator / SQLTableCheckOperator** (`apache-airflow-providers-common-sql`) o `GreatExpectationsOperator`. |

## 2. Reglas Críticas en Airflow para Datos Transaccionales

1. **Prohibido Pasar DataFrames por XCom**:
   - XCom está diseñado solo para metadatos livianos (rutas de archivos Parquet/S3, IDs de snapshot, conteos). Persistir datos siempre en almacenamiento intermedio (S3/GCS/Parquet/DuckLake) o usar un *Custom XCom Backend* en Object Storage.
2. **Idempotencia Basada en `data_interval_start` / `data_interval_end`**:
   - Todo `@task` debe poder re-ejecutarse (`Clear Task`) sobre cualquier ventana histórica reemplazando limpiamente la partición destino sin duplicar filas.
