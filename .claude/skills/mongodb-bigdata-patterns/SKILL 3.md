---
name: mongodb-bigdata-patterns
description: Patrones de procesamiento masivo y agregación en MongoDB: reglas de fusión segura con $merge (evitando pérdida de subdocumentos por shallow merge), paginación por cursor (_id > lastId vs skip), bulkWrite ordenado/desordenado y paralelización por cubetas deterministas.
---

# MongoDB Big Data & High-Throughput Patterns

## Cuándo Activar esta Skill
- Al diseñar pipelines de agregación que materializan resultados con `$merge` o `$out` sobre millones de documentos.
- Al implementar jobs de actualización masiva (`bulkWrite`), backfills históricos o particionamiento paralelo por workers.

## 1. Regla de Fusión Segura en `$merge` (Evitar Pérdida de Datos por *Shallow Merge*)

**Peligro Crítico**: En MongoDB, `$merge` con `whenMatched: "merge"` ejecuta una **fusión superficial a nivel raíz** (*top-level field replacement*).
- Si el documento destino tiene `{ _id: "1", metricas: { ene: 100, feb: 200 } }` y tu pipeline emite `{ _id: "1", metricas: { mar: 300 } }`, `whenMatched: "merge"` **borrará `ene` y `feb`**, dejando solo `{ _id: "1", metricas: { mar: 300 } }`.

**Soluciones Seguras**:
1. **Pipeline explícito en `whenMatched` (Recomendado)**:
   ```javascript
   {
     $merge: {
       into: "target_collection",
       on: ["_id"],
       whenMatched: [
         {
           $set: {
             "metricas.mar": "$$new.metricas.mar",
             updatedAt: "$$NOW"
           }
         }
       ],
       whenNotMatched: "insert"
     }
   }
   ```
2. **Fusión profunda con `$mergeObjects`**:
   ```javascript
   whenMatched: [
     {
       $set: {
         metricas: { $mergeObjects: ["$metricas", "$$new.metricas"] }
       }
     }
   ]
   ```

## 2. Idempotencia Diaria en Colecciones Shardeadas (`deleteMany` + `$merge`)

Cuando se materializa un corte diario en una colección shardeada donde la clave única de negocio difiere de la *shard key* hashed:
1. Ejecuta primero una limpieza idempotente acotada por la ventana del día (`deleteMany({ processDate: targetDate })`) usando un índice que cubra `processDate`.
2. Ejecuta el pipeline con `$merge` (`whenMatched: "replace"` o `"keepExisting"` según contrato) incluyendo siempre los campos de la *shard key* en el documento emitido.

## 3. Paralelización Determinista por Cubetas (`0..9` o `00..99`)

Para dividir una colección de 100M+ documentos entre `N` workers concurrentes sin colisiones de bloqueo en WiredTiger:
- Si el identificador es un hash en Base64 (`campo_HASH`), calcula un `parallelizationBucket` determinista a partir del primer carácter o de un módulo entero (`0..9` o `00..99`) al momento de la ingesta.
- Crea un índice compuesto cuyo prefijo incluya `{ processDate: 1, parallelizationBucket: 1 }`.
- Lanza `N` workers independientes donde cada worker procesa exclusivamente su cubeta `{ processDate: targetDate, parallelizationBucket: k }` con `bulkWrite(..., { ordered: false })` en lotes de `1,000–5,000` operaciones.
