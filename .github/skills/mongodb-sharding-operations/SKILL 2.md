---
name: mongodb-sharding-operations
description: Operaciones de Sharding en MongoDB para Big Data: selección de shard keys (ranged vs hashed vs compound), pre-split en 2 fases sobre colecciones vacías, rebalanceo trimestral de chunks (splitFind, moveChunk, zonas) e ingesta masiva paralela.
---

# MongoDB Sharding Operations — Pre-Split, Rebalanceo y Shard Keys

## Cuándo Activar esta Skill
- Al diseñar la *shard key* de una colección masiva o preparar una colección para una carga batch/CDC de decenas o cientos de millones de documentos.
- Al diagnosticar desbalance de chunks (*hot shards*), cuellos de botella de migración o errores de `$merge` en colecciones shardeadas.

## 1. Selección de Shard Key

| Patrón de Shard Key | Ventaja | Riesgo Crítico y Mitigación |
| :--- | :--- | :--- |
| **Ranged Monótono (`{ fecha: 1 }` o `{ _id: 1 }`)** | Excelente para consultas por rango de fechas (*targeted queries*). | **Hot Shard de escritura**: todas las inserciones nuevas caen en el último chunk de un único shard. **Mitigación**: Prefijar con un campo de distribución o usar *Compound Hashed*. |
| **Hashed Simple (`{ entityId: "hashed" }`)** | Escrituras perfectamente distribuidas desde el primer documento. | Consultas por rango hacen *scatter-gather* a todos los shards. Además, `$merge` con `on` sobre un campo que no incluye la clave exacta o conflictos con CSFLE requieren diseño especial. |
| **Compuesta (`{ periodMonth: 1, accountHash: 1 }`)** | Aísla las consultas al período activo y distribuye la carga entre todos los shards dentro del período. | Requiere **Pre-Split antes de la carga masiva** para no iniciar con todos los datos en el shard primario de la base de datos. |

## 2. Protocolo de Pre-Split en 2 Fases sobre Colección Vacía

**Invariante Crítico**: Si insertas 50M+ de documentos en una colección recién shardeada sin pre-split, **todos** los documentos entran inicialmente al shard primario y el balanceador tarda horas migrando chunks uno por uno (la velocidad de vaciado queda limitada por el único shard origen).

Ejecuta siempre el **Pre-Split en 2 Fases con la colección vacía**:
1. **Fase 1 — Creación de Puntos de Corte (`splitAt`)**:
   - Con la colección vacía y el balanceador detenido temporalmente para ese namespace, divide el espacio de claves en `N * M` chunks uniformes (ej. cubetas `00..99` o prefijos Base64):
     ```javascript
     sh.stopBalancer();
     for (const point of splitPoints) {
       db.adminCommand({ split: "dbName.collName", middle: point });
     }
     ```
2. **Fase 2 — Distribución Round-Robin en Vacío (`moveChunk`)**:
   - Mueve los chunks vacíos en *round-robin* hacia todos los shards del cluster (`moveChunk` de un chunk vacío es una operación de metadatos de milisegundos, sin copia de datos).
   - Reactiva el balanceador (`sh.startBalancer()`) e inicia la ingesta masiva: todos los shards escribirán en paralelo desde el segundo cero.

## 3. Rebalanceo Operativo de Chunks (Trimestral / Por Ventana)

- **Inspección Previa (`--dry-run`)**:
  - Consulta `config.chunks` y `db.coll.getShardDistribution()` para identificar *jumbo chunks* o asimetría `> 15%` entre shards.
- **División de Chunks Grandes**:
  - Usa `db.adminCommand({ splitFind: "db.coll", find: { shardKey: valor } })` para dividir exactamente por la mediana de un chunk pesado.
- **Restricción de Clientes**:
  - Nunca ejecutes bucles largos de `moveChunk` desde clientes GUI con timeout corto (como Compass); ejecútalos mediante `mongosh` en sesión `tmux`/`nohup` con verificación de `sh.isBalancerRunning()` y pausa controlada entre movimientos.
