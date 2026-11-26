---
name: mongodb-query-optimizer
description: Optimización de consultas y pipelines de agregación en MongoDB. Cubre regla ESR (Equality, Sort, Range), índices parciales (partialFilterExpression), Covered Queries en clusters sharded (PROJECTION_COVERED), lectura de explain("executionStats") y prevención de trampas BSON (MISSING != null, Array > Number).
---

# MongoDB Query & Aggregation Optimizer

## Cuándo Activar esta Skill
- Al optimizar consultas lentas (`COLLSCAN`, `FETCH` masivo, `SORT_KEY_GENERATOR` en memoria) o analizar salidas de `explain("executionStats")`.
- Al diseñar índices compuestos o índices parciales (`partialFilterExpression`) para colas operativas. Para ventanas móviles, usar `mongodb-rolling-window-precalc`.
- Al escribir pipelines de agregación sobre colecciones shardeadas o transaccionales.

## 0. Estándar del proyecto primero
Si el proyecto tiene `docs/standards/mongodb-query-optimization.md`, ese documento manda. Léelo antes de proponer un índice o cambiar una consulta, y si esta skill dice algo distinto, sigue el del proyecto y dilo en la respuesta. Esta skill es la guía general; no sustituye a los estándares del proyecto.

## 1. Diagnóstico antes de optimizar
No propongas un índice sin medir. Con los comandos de solo lectura:

- **Plan de ejecución**: `db.<coleccion>.find(filtro).explain("executionStats")`. Compara `totalDocsExamined` con `nReturned`: si examina mucho más de lo que devuelve, hay un problema de índice. Busca `COLLSCAN`, `FETCH` sobre muchos documentos y `SORT` en memoria.
- **Operaciones en curso**: `db.currentOp({ "secs_running": { $gt: 5 } })` muestra lo que lleva más de cinco segundos. Revisa el plan de esas consultas antes de crear nada.
- **Estado de la colección**: `db.<coleccion>.aggregate([{ $collStats: { storageStats: {}, latencyStats: {} } }])` da tamaño, índices y latencia de lectura y escritura.
- **Uso de índices**: `db.<coleccion>.aggregate([{ $indexStats: {} }])` da cuántas veces se usó cada índice desde el último reinicio. Un índice con cero accesos después de un periodo representativo es candidato a borrar, con confirmación.

Una lectura de `$indexStats` es un contador desde el último reinicio del servidor, no un histórico: no concluyas que un índice sobra sin confirmar ese periodo.

## 2. Regla ESR (Equality -> Sort -> Range) + Covered Queries

1. **Orden de Claves en Índices Compuestos**:
   - **E (Equality)**: Campos con predicado exacto (`{ status: "ACTIVE", tenantId: 10 }`).
   - **S (Sort)**: Campos de ordenamiento (`{ createdAt: -1 }`) — evita la etapa `SORT` en memoria (límite 100 MB sin `allowDiskUse`).
   - **R (Range)**: Campos con `$gte`, `$lte`, `$in` de alta cardinalidad o `$ne`.
2. **Covered Queries en Clusters Sharded (`PROJECTION_COVERED` + `SHARDING_FILTER`)**:
   - Si después de `$match` colocas `$addFields`, `$set` o `$lookup` antes de `$project`, el optimizador de MongoDB pierde la capacidad de cubrir la consulta con el índice y ejecuta un `FETCH` completo desde disco.
   - **Patrón obligatorio**:
     ```javascript
     [
       { $match: { shardKey: "A", fileDate: { $gte: ISODate("2026-01-01") } } },
       { $project: { _id: 0, shardKey: 1, fileDate: 1, amountCents: 1 } } // Inmediatamente tras $match
     ]
     ```
   - **Regla en Sharding**: Todo índice secundario que pretenda ejecutar una consulta cubierta debe incluir los campos de la **Shard Key**; de lo contrario, el shard debe hacer `FETCH` del documento para ejecutar la etapa `SHARDING_FILTER` (descarte de documentos de chunks huérfanos).

## 3. Índices Parciales (`partialFilterExpression`) para Alto Volumen

Un índice parcial indexa solo los documentos que cumplen el filtro, así que ocupa menos. El filtro se fija al crear el índice, y una consulta solo lo usa si su propio filtro implica el del índice:

1. **Cola de Trabajo / Flag Booleano**:
   ```javascript
   db.transactions.createIndex(
     { processedFlag: 1, interfaceCode: 1, fileDate: -1, parallelBucket: 1 },
     { name: "idx_pending_queue", partialFilterExpression: { processedFlag: false } }
   );
   ```
2. **Unicidad Condicional sobre Campos Opcionales**:
   - A diferencia de `sparse: true`, `partialFilterExpression` permite combinar condiciones explícitas:
   ```javascript
   db.entities.createIndex(
     { taxId: 1 },
     { name: "uniq_tax_id_when_present", unique: true, partialFilterExpression: { taxId: { $exists: true } } }
   );
   ```
3. **Ventanas de tiempo: no usar fechas móviles en el filtro**:
   - Un `partialFilterExpression` con `fileDate: { $gte: cutoffDate }` queda congelado con la fecha de creación. Las consultas posteriores con una fecha más reciente no lo cumplen y el índice deja de servir sin avisar.
   - Para ventanas móviles (7, 30, 90 días) el patrón correcto es precalcular por día en una colección reducida, no indexar una ventana. Ver la skill `mongodb-rolling-window-precalc`.
   - Un índice parcial sí sirve con condiciones fijas, como el flag de cola de la sección anterior.

## 4. Prevención de Trampas Semánticas BSON en Agregaciones

1. **`MISSING != null` en `$match` vs Expresiones de Agregación**:
   - En `$match`, `{ flag: { $ne: true } }` incluye documentos con `flag: false`, `flag: null` y documentos donde `flag` **no existe (`MISSING`)**.
   - Si necesitas distinguir `null` de `MISSING` dentro de una expresión de agregación, compara contra `$$REMOVE` o verifica `{ $ne: [{ $type: "$campo" }, "missing"] }`.
2. **`Array > Number` en Comparaciones BSON**:
   - Si un campo numérico se corrompió en algún documento como array (`[100]`), `{ monto: { $gt: 0 } }` evaluará el orden de tipos BSON donde `Array > Number`. Valida tipo o usa `$isArray` cuando la fuente no tenga `$jsonSchema` estricto.
