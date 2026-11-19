---
name: polymorphic-schema-design
description: Diseño de esquemas polimórficos gobernados en MongoDB y Lakehouse: uso de discriminador (entityType) + schemaVersion, validación condicional con $jsonSchema (oneOf) e índices parciales por subtipo.
---

# Polymorphic Schema Design & Conditional Validation

## Cuándo Activar esta Skill
- Cuando múltiples variantes de una entidad de negocio (ej. personas naturales vs jurídicas, transacciones de tarjeta vs transferencia vs pago móvil, distintos tipos de documentos procesados por IA) se consultan juntas en el 70%+ de los casos pero poseen atributos específicos por subtipo.

## 1. Estructura Canónica de Documento Polimórfico

Todo documento polimórfico debe incluir en su raíz el **sobre canónico común**:
- `entityType`: Discriminador en mayúsculas (`"NATURAL_PERSON" | "LEGAL_ENTITY"`).
- `schemaVersion`: Entero o SemVer (`2`) para migración perezosa (*lazy migration*).
- Atributos transversales de búsqueda (`entityHash`, `status`, `createdAt`, `updatedAt`).
- Subdocumento o campos específicos validados condicionalmente según `entityType`.

## 2. Índices Parciales por Discriminador (`partialFilterExpression`)

Para indexar un campo que solo existe en uno de los subtipos sin desperdiciar RAM en el resto de la colección:
```javascript
db.parties.createIndex(
  { commercialRegistryCode: 1 },
  {
    name: "idx_legal_entity_registry",
    partialFilterExpression: {
      entityType: "LEGAL_ENTITY",
      commercialRegistryCode: { $exists: true }
    }
  }
);
```

## 3. Validación `$jsonSchema` por Subtipo (`oneOf`)

```javascript
{
  $jsonSchema: {
    bsonType: "object",
    required: ["entityType", "schemaVersion", "entityHash"],
    oneOf: [
      {
        properties: { entityType: { enum: ["NATURAL_PERSON"] } },
        required: ["birthDate"]
      },
      {
        properties: { entityType: { enum: ["LEGAL_ENTITY"] } },
        required: ["incorporationDate", "commercialRegistryCode"]
      }
    ]
  }
}
```
