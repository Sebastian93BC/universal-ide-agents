# Playbook de Producción: Ingeniería de Datos para Big Data y Datos Transaccionales

Este playbook consolida los invariantes arquitectónicos, soluciones a incidentes reales de producción y patrones de alto rendimiento extraídos de tus proyectos (**MongoDB Sharded Clusters, DuckDB/DuckLake, Dagster, dbt, Parquet, n8n, PySpark/Delta/Iceberg y Kafka/Debezium**).

---

## 1. Compendio de Incidentes Reales y Soluciones Definitivas

| ID | Dominio / Motor | Síntoma o Fallo en Producción | Causa Raíz Verificada | Patrón de Solución Estándar |
| :--- | :--- | :--- | :--- | :--- |
| **`INC-01`** | **MongoDB `$merge`** | Pérdida silenciosa de métricas de meses anteriores al actualizar un documento de resumen. | `whenMatched: "merge"` ejecuta una fusión superficial (*top-level replacement*), sobrescribiendo todo el subdocumento `metricas`. | Usar siempre pipeline explícito en `whenMatched: [ { $set: { "metricas.mesActual": "$$new.valor" } } ]` o `$mergeObjects`. |
| **`INC-02`** | **MongoDB BSON** | Documentos sin el campo `flag` o con valores inesperados pasan o fallan filtros `$match`. | En `$match`, `MISSING != null`; además, en comparaciones BSON `Array > Number`. | Filtrar explícitamente `{ campo: { $exists: true, $ne: null } }` y validar tipos con `$jsonSchema`. |
| **`INC-03`** | **MongoDB Sharding** | Consultas que deberían ser `PROJECTION_COVERED` hacen `FETCH` de millones de documentos desde disco. | Se colocó `$addFields` antes de `$project`, o el índice secundario no incluía la *Shard Key* (obligando a hacer `FETCH` para la etapa `SHARDING_FILTER`). | Colocar `$project` (`_id: 0` + solo campos del índice) inmediatamente después de `$match` e incluir la *Shard Key* en el índice. |
| **`INC-04`** | **MongoDB Sharding** | Ingesta inicial de decenas de millones de documentos tarda horas y satura un único shard. | Colección shardeada sin pre-split: todos los documentos entran al shard primario y la velocidad de migración queda limitada por ese único shard origen. | Ejecutar **Pre-Split en 2 Fases sobre la colección vacía** (`splitAt` + `moveChunk` round-robin en milisegundos) antes de insertar. |
| **`INC-05`** | **MongoDB CSFLE (`crypt_shared`)** | Fallo de pipelines de agregación con códigos `31127`, `9710000` o `17217`. | `31127`: uso de `$$ROOT` prohibido en CSFLE. `9710000`: `$merge` hacia colección no declarada en `schemaMap`. `17217`: `distinct()` supera 16 MB BSON. | Proyectar campos explícitos (sin `$$ROOT`), correr `$merge` sobre campos `*_HASH` con cliente sin auto-encryption, y usar `$group` con cursor en lugar de `distinct()`. |
| **`INC-06`** | **MongoDB Ventanas Móviles** | Cálculo diario de métricas de 30d/90d/180d tarda horas al escanear meses de transacciones crudas. | Re-lectura diaria de la colección transaccional cruda (`raw_transactions`) y costo de escritura aleatorio de múltiples `$merge`. | **Pre-cálculo diario incremental**: leer solo el día `D` del crudo hacia una colección diaria reducida (`sum`, `sumSq`, histograma para `P95` con `$setWindowFields`, mapa `lastSeen` para distincts) y consolidar un único `$merge`. |
| **`INC-07`** | **Dagster + DuckDB + dbt** | Fallo `IO Error: Could not set lock on file` al ejecutar assets en paralelo. | Un archivo `.duckdb` solo admite un único proceso escritor sin lectores externos concurrentes. | Persistir capas intermedias en **Parquet / DuckLake**, serializar escritores al `.duckdb` con `op_tags={"dagster/concurrency_key": "duckdb_single_writer"}` y abrir herramientas MCP con `--read-only`. |
| **`INC-08`** | **Parquet + DuckDB** | Consultas lentas sobre Parquet a pesar de estar particionado en miles de subcarpetas. | Hiper-particionamiento Hive genera miles de archivos pequeños (`< 10 MB`). | Escribir archivos Parquet de `100–512 MB` (`ZSTD`) **ordenados físicamente (`ORDER BY fecha, entidad_id`)** para salto de bloques vía *Min-Max Zone Maps*. |
| **`INC-09`** | **Docker + Motores de Datos** | Contenedor muere abruptamente con `exit code 137` durante agregaciones pesadas. | El motor interno (DuckDB / WiredTiger / JVM) intenta usar toda la RAM del host y supera el `mem_limit` del contenedor (`OOMKilled`). | Fijar el límite interno del motor (`SET memory_limit`, `--wiredTigerCacheSizeGB`, `-Xmx`) al **75–80%** del `mem_limit` del contenedor. |
| **`INC-10`** | **Inferencia ML en Producción** | Predicciones erráticas o nulas al pasar lotes pequeños o filas individuales en producción. | El script de inferencia llamaba a `scaler.fit_transform(X_new)` en lugar de reutilizar las estadísticas de entrenamiento. | Serializar un `sklearn.pipeline.Pipeline` completo con `joblib.dump` en entrenamiento y llamar exclusivamente a `pipeline.predict(X_new)` en producción. |

---

## 2. Checklist de Pase a Producción para Pipelines de Datos

1. **[ ] Seguridad y Criptografía**: ¿Todos los campos PII cumplen la separación `*_PLAIN` (no persistido) / `*_HASH` (indexado) / `*_ENCRYPTED` (aleatorio), y todas las credenciales usan `${ENV_VAR}` o `dg.EnvVar`?
2. **[ ] Precisión Financiera**: ¿Todos los montos monetarios se almacenan y suman como enteros de 64 bits en centavos (`BIGINT` / `NumberLong`) o `Decimal128`?
3. **[ ] Los 5 Medallion Safety Guards**: ¿Están activos el *Freshness/Lag Guard*, *Writer `.tmp` Guard*, *Lineage Consistency Guard*, *Row Regression Guard* y el modo `--dry-run`?
4. **[ ] Contratos y Pruebas**: ¿Los marts Gold tienen `contract: {enforced: true}`, `unit_tests:` en dbt / expectativas en Great Expectations y `AssetChecks` con `blocking=True`?
5. **[ ] Observabilidad OpenTelemetry**: ¿Se emiten los 3 niveles de Spans (`Módulo -> Proceso -> Operación`) sin filtrar PII en los atributos?
