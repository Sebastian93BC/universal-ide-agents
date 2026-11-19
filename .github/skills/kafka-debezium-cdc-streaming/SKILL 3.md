---
name: kafka-debezium-cdc-streaming
description: Arquitectura de streaming y Change Data Capture (CDC) transaccional con Apache Kafka, Debezium y Schema Registry: captura basada en logs, particionado por PK, preservación de tombstones, compatibilidad BACKWARD_TRANSITIVE, Outbox Pattern y Dead Letter Queues (DLQ).
---

# Kafka + Debezium Transactional CDC & Streaming

## Cuándo Activar esta Skill
- Al diseñar ingestas en tiempo cuasi-real (NRT) desde bases transaccionales (**PostgreSQL WAL, MongoDB Oplog/Change Streams, MySQL Binlog, Oracle**) hacia Kafka y el Lakehouse.
- Al prevenir corrupción de orden de eventos, explosión de disco por slots de replicación o roturas por evolución de esquema (*schema drift*).

## 1. Cinco Invariantes de Producción para Debezium + Kafka

1. **Particionado Estricto por Clave Primaria (Garantía de Orden)**:
   - Todo tópico CDC de entidad debe usar la **Primary Key (`_id` / `id`) como Message Key de Kafka**.
   - Esto garantiza que todos los eventos de una misma fila (`INSERT -> UPDATE -> DELETE`) caigan en la misma partición en orden cronológico estricto.
2. **Protección del Log Transaccional de la Base Origen**:
   - En PostgreSQL, un conector Debezium detenido retiene el *Replication Slot*, pudiendo llenar el disco del primario con archivos WAL. Configura siempre `max_slot_wal_keep_size`, `slot.drop.on.stop=false` con alerta temprana de lag y usa **snapshots incrementales** (basados en watermark en lugar de bloquear tablas).
3. **Preservación de Tombstones para Borrados Físicos**:
   - Mantén `tombstones.on.delete=true` para que Kafka Log Compaction y las capas Silver del Lakehouse propaguen los borrados físicos (`op = 'd'`) antes de expirar la clave.
4. **Gobernanza con Schema Registry (`BACKWARD_TRANSITIVE`) y SMTs en Sharding**:
   - Serializa en **Avro** o **Protobuf** con compatibilidad `BACKWARD_TRANSITIVE` (permite que los nuevos consumidores lean todo el histórico desde el offset 0).
   - Si la fuente está shardeada (múltiples bases/colecciones con el mismo esquema), aplica una *Single Message Transform (SMT)* (`SetSchemaMetadata`) para unificar el namespace del esquema antes de registrarlo y evitar explosión de miles de esquemas idénticos.
5. **Transactional Outbox Pattern + Dead Letter Queue (DLQ)**:
   - Prohibido hacer *dual-writes* desde la aplicación (escribir en base de datos y publicar en Kafka por separado). Escribe el cambio de negocio y el evento en una tabla/colección `outbox` dentro de la **misma transacción local** y deja que Debezium capture `outbox`.
   - Configura `errors.tolerance=all` con envío automático de *poison pills* a un tópico `dlq.<entidad>` monitoreado para no detener el flujo en vivo.
