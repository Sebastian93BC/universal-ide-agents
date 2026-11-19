---
name: sql-to-nosql-modeling
description: Metodología e inspección automatizada para migrar esquemas relacionales (PostgreSQL/Oracle/SQL Server) hacia modelos documentales (MongoDB) o analíticos (DuckDB/Lakehouse). Clasifica tablas puente N:M, jerarquías recursivas y tablas de auditoría.
---

# SQL-to-NoSQL & Lakehouse Schema Transformation

## Cuándo Activar esta Skill
- Al migrar sistemas legados relacionales (3NF con decenas de tablas y `JOINs` costosos) hacia **MongoDB** o un Lakehouse **DuckDB/Parquet**.
- Al auditar un archivo `.sql` (DDL) o catálogo `information_schema` para decidir qué tablas deben incrustarse (*embed*), cuáles referenciarse y cuáles descargarse a almacenamiento columnar.

## 1. Reglas Heurísticas de Transformación Relacional -> Documental

1. **Tablas Puente Puras (`N:M` con solo 2 FKs y metadatos de vínculo)**:
   - No las migres como una colección independiente en MongoDB.
   - Si la cardinalidad de un lado es pequeña y acotada (`< 50` roles por usuario), incrusta un array de referencias o *Extended References* en la entidad principal (`user.roles = [{ roleId, assignedAt }]`).
2. **Tablas Hijas `1:Few` Débiles (Direcciones, Líneas de Factura `< 100`)**:
   - Incrústalas directamente como array de subdocumentos dentro de la entidad raíz (`invoice.lines`) para lograr atomicidad ACID en un único documento sin transacciones multi-documento.
3. **Tablas de Eventos / Movimientos / Logs (`1:Squillions`)**:
   - Manténlas en una colección independiente (o tabla Parquet/DuckLake) con la clave del padre indexada (`{ accountId: 1, txDate: -1 }`) y aplica el *Computed Pattern* o *Rolling Window Pre-calculation* para los saldos.
4. **Jerarquías Recursivas (`parent_id` auto-referenciado)**:
   - Reemplaza los `WITH RECURSIVE` de SQL por el patrón **Materialized Paths** (`path: ",root,deptA,team1,"` indexado con regex prefijo `^,root,deptA,`) o **Array of Ancestors** (`ancestors: ["root", "deptA"]` con índice multikey), permitiendo resolver todo un subárbol en una sola lectura sin `$graphLookup` costoso.
