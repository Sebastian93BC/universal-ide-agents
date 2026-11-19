---
name: parallel-processing-patterns
description: Patrones de procesamiento paralelo y concurrente en Python, MongoDB y DuckDB: particionado por cubetas deterministas, multiprocessing vs asyncio, control de backpressure, manejo de conexiones por worker y prevención de OOM.
---

# Parallel & High-Concurrency Processing Patterns

## Cuándo Activar esta Skill
- Al diseñar scripts o pipelines Python que procesan decenas de millones de registros usando `multiprocessing`, `concurrent.futures`, `asyncio` o Dask.
- Al evitar saturación de conexiones en MongoDB/PostgreSQL o bloqueos por compartir clientes entre procesos `fork`.

## 1. Cuatro Invariantes de Concurrencia en Ingeniería de Datos

1. **Un Cliente de Base de Datos por Proceso Worker (`Fork-Safety`)**:
   - **`PyMongo` (`MongoClient`), `psycopg` y conexiones `DuckDB` NO son *fork-safe***.
   - Jamás pases un `MongoClient` abierto al `Pool` de `multiprocessing`. Inicializa la conexión dentro de la función `initializer` del worker (con `maxPoolSize` acotado, ej. `maxPoolSize=5` por worker) o crea el cliente al inicio de cada proceso hijo.
2. **Particionamiento sin Solapamiento (*Lock-Free Sharding*)**:
   - Dos workers nunca deben actualizar el mismo conjunto de documentos simultáneamente (evita *Write Conflicts* y *Deadlocks*).
   - Divide el trabajo por una clave ortogonal determinista: `(processDate, parallelizationBucket)` donde `parallelizationBucket` va de `0` a `N-1`.
3. **Procesamiento en Streaming por Lotes Acotados (*Bounded Batching*)**:
   - Prohibido hacer `list(cursor)` sobre millones de documentos.
   - Itera el cursor con `batch_size(2000)`, acumula hasta `2,000–5,000` operaciones `UpdateOne`/`InsertOne` y descarga con `bulk_write(ops, ordered=False)` liberando la lista inmediatamente.
4. **Fórmula de Dimensionamiento de Workers**:
   - **Cargas CPU-bound (parsing, hashing HMAC, compresión Parquet)**: `workers = min(cpu_count() - 1, 8)`.
   - **Cargas I/O-bound contra BD (bulkWrite MongoDB / queries)**: Limita la concurrencia total (`workers * threads_per_worker`) para no superar el `60%` de los tickets de escritura de WiredTiger (normalmente `8 a 16` escritores concurrentes máximos recomendados contra un mismo shard).
