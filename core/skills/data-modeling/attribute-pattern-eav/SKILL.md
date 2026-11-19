---
name: attribute-pattern-eav
description: Implementación del Attribute Pattern (Entity-Attribute-Value optimizado) en MongoDB y JSON columnar para consolidar decenas de campos dispersos o dinámicos bajo un único índice compuesto determinista.
---

# Attribute Pattern (EAV Optimizador de Índices)

## Cuándo Activar esta Skill
- Cuando una entidad tiene decenas o cientos de atributos opcionales/dispersos (características por tipo de producto, indicadores por formulario fiscal, parámetros dinámicos por cliente) que obligarían a crear 50+ índices individuales o índices `wildcard` poco selectivos.

## 1. Transformación Estructural al Attribute Pattern

**Anti-patrón**:
```json
{
  "_id": "doc_1",
  "indicador_101": 4500,
  "indicador_205": 120,
  "fecha_corte_101": "2026-11-18"
}
```

**Patrón Correcto (`attributes: [{ k, v, u, d }]`)**:
```json
{
  "_id": "doc_1",
  "entityHash": "H123",
  "attributes": [
    { "k": "indicador_101", "v": 4500, "u": "CENTS", "updatedAt": "2026-11-18" },
    { "k": "indicador_205", "v": 120, "u": "COUNT", "updatedAt": "2026-11-18" }
  ]
}
```

## 2. Índice Compuesto Único y Consulta con `$elemMatch`

1. **Un solo índice compuesto cubre cualquier atributo presente o futuro**:
   ```javascript
   db.entities.createIndex(
     { entityHash: 1, "attributes.k": 1, "attributes.v": 1 },
     { name: "idx_entity_attributes_kv" }
   );
   ```
2. **Obligatoriedad de `$elemMatch` en predicados sobre el mismo atributo**:
   - **Incorrecto**: `{ "attributes.k": "indicador_101", "attributes.v": { $gt: 1000 } }` (coincide erróneamente si un elemento tiene `k="indicador_101"` y *otro* elemento distinto tiene `v=5000`).
   - **Correcto**:
     ```javascript
     db.entities.find({
       attributes: {
         $elemMatch: { k: "indicador_101", v: { $gt: 1000 } }
       }
     });
     ```
