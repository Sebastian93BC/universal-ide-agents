---
name: mongodb-query-optimizer
description: Optimización de consultas y pipelines de agregación en MongoDB. Cubre regla ESR (Equality, Sort, Range), índices parciales (partialFilterExpression), Covered Queries en clusters sharded (PROJECTION_COVERED), lectura de explain("executionStats") y prevención de trampas BSON (MISSING != null, Array > Number).
---

# MongoDB Query & Aggregation Optimizer

## Cuándo Activar esta Skill
- Al optimizar consultas lentas (`COLLSCAN`, `FETCH` masivo, `SORT_KEY_GENERATOR` en memoria) o analizar salidas de `explain("executionStats")`.
- Al diseñar índices compuestos o índices parciales (`partialFilterExpression`) para colas operativas y ventanas de tiempo.
- Al escribir pipelines de agregación sobre colecciones shardeadas o transaccionales.

## 1. Regla ESR (Equality -> Sort -> Range) + Covered Queries

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

## 2. Índices Parciales (`partialFilterExpression`) para Alto Volumen

Reduce el tamaño del índice en RAM (WiredTiger cache) entre un 70% y 95% indexando solo el subconjunto activo:

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
3. **Ventana Operativa Reciente**:
   - Indexar con `partialFilterExpression: { fileDate: { $gte: cutoffDate }, opCode: { $gt: 0 } }` para acelerar consultas diarias sin penalizar el histórico.

## 3. Prevención de Trampas Semánticas BSON en Agregaciones

1. **`MISSING != null` en `$match` vs Expresiones de Agregación**:
   - En `$match`, `{ flag: { $ne: true } }` incluye documentos con `flag: false`, `flag: null` y documentos donde `flag` **no existe (`MISSING`)**.
   - Si necesitas distinguir `null` de `MISSING` dentro de una expresión de agregación, compara contra `$$REMOVE` o verifica `{ $ne: [{ $type: "$campo" }, "missing"] }`.
2. **`Array > Number` en Comparaciones BSON**:
   - Si un campo numérico se corrompió en algún documento como array (`[100]`), `{ monto: { $gt: 0 } }` evaluará el orden de tipos BSON donde `Array > Number`. Valida tipo o usa `$isArray` cuando la fuente no tenga `$jsonSchema` estricto.
