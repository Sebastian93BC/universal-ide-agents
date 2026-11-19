---
name: ducklake-medallion-architecture
description: Diseño e implementación de arquitectura Medallion Lakehouse (Bronze -> Silver -> Gold -> Seal -> Publish) con DuckDB y formato abierto DuckLake (catálogo SQL + almacenamiento Parquet).
---

# DuckLake & Medallion Lakehouse Architecture

## Cuándo Activar esta Skill
- Al construir un Lakehouse local, híbrido o en la nube utilizando **DuckDB + DuckLake** (extensión `ducklake` donde el catálogo transaccional ACID reside en PostgreSQL/SQLite/DuckDB y los datos en archivos Parquet sobre disco o S3/GCS).
- Al estructurar las capas `Bronze -> Silver -> Gold` con aislamiento de publicación (`Seal -> Publish`).

## 1. Arquitectura de 5 Etapas Medallion (`Bronze -> Silver -> Gold -> Seal -> Publish`)

| Etapa | Responsabilidad | Formato y Regla de Mutación |
| :--- | :--- | :--- |
| **1. Bronze (Raw / Ingest)** | Captura fiel 1:1 del origen (archivos planos, APIs, dumps o eventos CDC). | Parquet append-only particionado por fecha de ingesta (`_ingested_at`, `_source_file`, `_batch_id`). Nunca se edita ni sobreescribe. |
| **2. Silver (Cleaned & Conformed)** | Tipado estricto, deduplicación, estandarización de claves, conversión de montos a centavos (`BIGINT`) y manejo de borrados. | Tablas **DuckLake** o Parquet particionado con escritura atómica vía `.tmp`. |
| **3. Gold (Marts & Aggregations)** | Modelos dimensionales (Hechos y Dimensiones) y pre-agregados de negocio listos para BI / ML. | Contratos de datos estrictos (`NOT NULL`, tipos fijos, claves únicas verificadas). |
| **4. Seal (Compuerta de Calidad)** | Verificación de los 5 *Medallion Safety Guards* y Asset Checks antes de exponer datos a consumidores. | Si algún guard falla, el snapshot nuevo no se promueve. |
| **5. Publish (Exposición Atómica)** | Actualización del puntero de catálogo DuckLake o vista de consumo (`READ_ONLY`). | Los consumidores nunca ven tablas a medio construir. |

## 2. Patrón de Inicialización de DuckLake en DuckDB

```sql
INSTALL ducklake;
LOAD ducklake;

-- Conectar catálogo transaccional (ej. Postgres o archivo local) con storage en Parquet
ATTACH 'ducklake:postgres:dbname=lakehouse_catalog host=localhost' AS lakehouse (
    DATA_PATH 's3://bucket-lakehouse/data/' -- o ruta local './data/lakehouse/'
);

-- Transacción ACID con Time Travel y Snapshots sobre archivos Parquet
BEGIN TRANSACTION;
INSERT INTO lakehouse.silver_transactions
SELECT * FROM read_parquet('data/bronze/tx_2026_11_18.parquet');
COMMIT;
```

## 3. Ventajas de DuckLake frente a un `.duckdb` Monolítico
- **Desacoplamiento Cómputo/Almacenamiento**: Múltiples procesos de Dagster o nodos pueden escribir nuevos archivos Parquet y registrar el commit de metadatos en PostgreSQL en milisegundos, eliminando el cuello de botella del bloqueo *single-writer* de un archivo `.duckdb` único.
- **Snapshots y Time Travel**: Permite auditar el estado exacto de una tabla antes y después de una corrida diaria y revertir instantáneamente sin restaurar backups pesados.
