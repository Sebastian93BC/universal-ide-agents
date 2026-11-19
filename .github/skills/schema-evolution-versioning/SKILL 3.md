---
name: schema-evolution-versioning
description: Evolución de esquemas sin tiempo de inactividad (Zero-Downtime Schema Evolution) en MongoDB, DuckDB/Parquet, dbt y Kafka Schema Registry mediante campo schemaVersion, patrón Expand-and-Contract y lectura polimórfica.
---

# Zero-Downtime Schema Evolution & Versioning

## Cuándo Activar esta Skill
- Al renombrar campos, cambiar tipos de datos (ej. `double` a centavos `long`), dividir una columna en subestructura o evolucionar esquemas entre versiones de aplicación y pipelines batch/streaming.

## 1. El Patrón Expand-and-Contract en 3 Fases

Jamás renombres ni elimines una columna/campo en un solo despliegue. Ejecuta siempre:

1. **Fase 1 — EXPAND (Doble Escritura / Lectura Tolerante)**:
   - Incrementa `schemaVersion` en los nuevos registros (ej. de `1` a `2`).
   - El escritor emite tanto el campo nuevo (`amountCents`) como el legado (`amount`) o el lector lee con fallback:
     - En MongoDB: `$ifNull: ["$amountCents", { $toLong: { $round: [{ $multiply: ["$amount", 100] }, 0] } }]`
     - En DuckDB / Parquet: `read_parquet('...', union_by_name=true)` con `COALESCE(amount_cents, CAST(ROUND(amount * 100) AS BIGINT))`.
2. **Fase 2 — MIGRATE (Backfill Idempotente por Lotes)**:
   - Ejecuta un job en background por cubetas (`parallelizationBucket`) o particiones que transforme los documentos con `schemaVersion: 1` (o `{ schemaVersion: { $exists: false } }`) a `schemaVersion: 2`, con soporte `--dry-run`.
3. **Fase 3 — CONTRACT (Endurecimiento del Contrato)**:
   - Una vez verificado que `count({ schemaVersion: { $ne: 2 } }) == 0`, elimina la lectura legada y actualiza el `$jsonSchema` o contrato de `dbt` (`contract: {enforced: true}`).
