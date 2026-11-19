---
name: mongodb-schema-design
description: Diseño de esquemas MongoDB para cargas transaccionales y analíticas de alto volumen. Cubre reglas de embedding vs referencing por cardinalidad, Bucket Pattern, Computed Pattern, validación $jsonSchema gradual y migración zero-downtime.
---

# MongoDB Schema Design — Modelado Transaccional y de Alto Volumen

## Cuándo Activar esta Skill
- Al diseñar nuevas colecciones MongoDB o auditar esquemas existentes.
- Al diagnosticar documentos que se acercan al límite BSON de `16 MB` o sufren degradación de escritura en WiredTiger por arrays no acotados.
- Al definir validadores `$jsonSchema` en bases de datos compartidas con datos legados.

## 1. Matriz de Decisión por Cardinalidad y Patrón de Acceso

| Relación / Cardinalidad | Estrategia Recomendada | Regla de Ingeniería |
| :--- | :--- | :--- |
| **`1:1` / `1:Few` (`< 100` subdocumentos)** | **Embedding directo** | Anidar cuando el hijo no se consulta independientemente y el array tiene una cota física estricta. |
| **`1:Many` (`100 – 10,000` elementos)** | **Extended Reference** o **Bucket Pattern** | En *Extended Reference*, incrusta solo los 2–4 campos leídos en listados (`{ customerId, name, taxId }`) y mantén la colección maestra separada. En *Bucket Pattern* (series de tiempo / logs / transacciones por cuenta), agrupa p. ej. `200–500` eventos o 1 día por documento con `count`, `sumAmountCents`, `minTs`, `maxTs`. |
| **`1:Squillions` (`> 10,000` o sin límite)** | **Referencing estricto ("Hijo apunta al Padre")** | Prohibido mantener un array de IDs en el documento padre. Coloca `parentId` e índice compuesto `{ parentId: 1, createdAt: -1 }` en la colección hija. |

## 2. Reglas de Gobernanza `$jsonSchema` en Producción

1. **Validador Mínimo de Seguridad (Baseline)**:
   - Toda colección productiva debe tener al menos un validador que exija existencia y tipo de la clave de partición/negocio y campos de auditoría, evitando documentos huérfanos vacíos `{}`.
2. **Despliegue Gradual Sin Caída**:
   - **Fase 1**: `validationLevel: "moderate"`, `validationAction: "warn"` (monitorear logs de rechazo sin romper escrituras legadas).
   - **Fase 2**: `validationLevel: "moderate"`, `validationAction: "error"` (protege todas las inserciones nuevas y documentos ya conformes, ignorando históricos no tocados).
   - **Fase 3**: Backfill de históricos + `validationLevel: "strict"`, `validationAction: "error"`.

## 3. Invariantes de Tipos BSON y Exportación

- **Montos Financieros**: Usa siempre enteros de 64 bits en centavos (`NumberLong` / `bsonType: "long"`) o `Decimal128` (`bsonType: "decimal"`). Nunca uses `double` para saldos o contabilidad.
- **Exportación / Migración sin Corrupción de Tipos**:
  - `mongoexport` en modo *Relaxed JSON* serializa `210.0` (double) como `210` (entero), provocando fallos de `$jsonSchema` al reimportar en colecciones que exigen `bsonType: ["double"]`.
  - **Solución**: Exportar con `--jsonFormat=canonical` (Canonical Extended JSON) o declarar tipos numéricos tolerantes `bsonType: ["double", "int", "long", "decimal"]` cuando la semántica lo permita.
