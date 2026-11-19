---
name: mongodb-csfle-governance
description: Gobernanza criptográfica y Client-Side Field Level Encryption (CSFLE) en MongoDB. Cubre la arquitectura de triple campo (_PLAIN, _HASH, _ENCRYPTED), particionamiento por prefijos Base64 de hashes deterministas y resolución de errores críticos de crypt_shared (31127, 9710000, 17217).
---

# MongoDB CSFLE & Cryptographic Data Governance

## Cuándo Activar esta Skill
- Al diseñar o mantener colecciones MongoDB con **Client-Side Field Level Encryption (CSFLE)** o `crypt_shared` (Enterprise / Atlas).
- Al implementar seudonimización y cifrado a nivel de aplicación para PII, identificadores fiscales (RIF/NIT/DNI), tarjetas o cuentas bancarias.
- Al diagnosticar errores `31127`, `9710000` o `17217` en pipelines de agregación sobre colecciones cifradas.

## 1. Arquitectura de Triple Campo (`_PLAIN` / `_HASH` / `_ENCRYPTED`)

Para conciliar confidencialidad estricta con rendimiento analítico y joins en Big Data:

| Sufijo de Campo | Algoritmo / Tipo | Propósito Permitido | ¿Persistido en Producción? |
| :--- | :--- | :--- | :--- |
| **`*_PLAIN`** | Texto claro original | Solo validación de formato en memoria durante la ingesta. | **NUNCA** (Prohibido en disco y logs). |
| **`*_HASH`** | Determinista (`AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic` o `HMAC-SHA256` en Base64) | Igualdad (`$match`), joins (`$lookup`), agrupación (`$group`), deduplicación, *shard key* e índices únicos. | **SÍ (Indexado)**. |
| **`*_ENCRYPTED`** | Aleatorio (`AEAD_AES_256_CBC_HMAC_SHA_512-Random` o `AES-256-GCM`) | Recuperación del valor original exclusivamente en la capa de presentación autorizada. | **SÍ (Nunca indexado)**. |

## 2. Resolución de los 3 Errores Críticos de `crypt_shared` en Agregaciones

1. **Error `31127` — Prohibición de `$$ROOT` en Colecciones con Esquema CSFLE**:
   - **Causa**: El analizador estático de `crypt_shared` rechaza cualquier pipeline que referencie `$$ROOT` (p. ej. `$group: { _id: "$k", doc: { $first: "$$ROOT" } }`) porque no puede garantizar estáticamente qué subcampos cifrados fluirán a etapas posteriores.
   - **Solución**: Reemplaza `$$ROOT` por un objeto explícito con los campos requeridos (`{ $first: { id: "$_id", campoHash: "$campo_HASH", monto: "$montoCents" } }`).
2. **Error `9710000` — Fallo de `$merge` hacia Colección Destino sin Mapa Criptográfico**:
   - **Causa**: Un cliente conectado con `AutoEncryptionOpts` activo falla al ejecutar `$merge` hacia una colección analítica o de staging que no está declarada en el `schemaMap` local.
   - **Solución**: Dado que las agregaciones analíticas operan únicamente sobre `*_HASH` y métricas numéricas (sin necesitar desencriptar `*_ENCRYPTED`), ejecuta los jobs batch de `$merge` usando un `MongoClient` estándar **sin `AutoEncryptionOpts`**, o registra explícitamente el esquema vacío del destino.
3. **Error `17217` — `distinct()` Excede el Límite BSON de 16 MB**:
   - **Causa**: `db.coll.distinct("entity_HASH")` devuelve un único documento BSON con un array; como cada hash Base64/BinData ocupa ~44–88 bytes, con pocos cientos de miles de valores únicos revienta el límite de 16 MB.
   - **Solución**: Usa siempre un cursor de agregación: `db.coll.aggregate([{ $group: { _id: "$entity_HASH" } }], { allowDiskUse: true })`.
