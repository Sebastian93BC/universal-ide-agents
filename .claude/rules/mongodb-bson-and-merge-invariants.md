---
name: mongodb-bson-and-merge-invariants
description: Invariantes críticos de MongoDB para Big Data y Datos Transaccionales: semántica BSON (MISSING != null, Array > Number), fusión superficial de $merge, aritmética en centavos y CSFLE.
trigger: model_decision
applyTo: "**/*.js,**/*.ts,**/*.py,**/*.json,**/*.md"
---

# Invariantes de MongoDB: BSON, `$merge`, Sharding y CSFLE

1. **`MISSING != null` en el Lenguaje de Consulta vs. Agregación**:
   - En filtros `$match`, `{ campo: { $ne: "X" } }` devuelve documentos donde `campo` es `null` o no existe (`MISSING`), pero expresiones de agregación como `$ifNull` tratan ambos por igual. Valida explícitamente `{ campo: { $exists: true, $ne: null } }`.
2. **Orden de Tipos BSON (`Array > Number`)**:
   - En el orden canónico BSON, un `Array` es mayor que un `Number`. Nunca apliques `$gt`/`$lt` numérico sobre campos polimórficos sin filtrar o desempaquetar arrays primero.
3. **`$merge` con `whenMatched: "merge"` es Superficial (Shallow Merge)**:
   - Reemplaza objetos anidados completos en la raíz del documento destino, causando pérdida de subcampos históricos. Usa siempre un pipeline en `whenMatched: [ { $set: { "subobjeto.campo": "$$new.subobjeto.campo" } } ]`.
4. **Aritmética Financiera en Centavos (`$toLong`)**:
   - Prohibido sumar montos monetarios en `double` IEEE 754. Convierte a centavos enteros con `$toLong: { $round: [{ $multiply: ["$monto", 100] }, 0] }` y divide entre `100` solo al presentar.
5. **Covered Queries en Clusters Sharded (`PROJECTION_COVERED` + `SHARDING_FILTER`)**:
   - Coloca `$project` inmediatamente después de `$match` (incluyendo `_id: 0` y solo campos del índice) y asegura que todo índice secundario contenga la *shard key* para que `mongos` filtre chunks huérfanos sin `FETCH`.
6. **Restricciones CSFLE / `crypt_shared`**:
   - Nunca uses `$$ROOT` en colecciones con esquema CSFLE (Error `31127`), evita `$merge` desde clientes auto-encrypted hacia colecciones sin mapa criptográfico (Error `9710000`), y reemplaza `distinct()` sobre campos masivos por `$group` con cursor (Error `17217`).
