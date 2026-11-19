---
name: data-mesh-and-mdm-governance
description: Principios de Data Mesh (Data as a Product, contratos federados) y Master Data Management (MDM Golden Record, Survivorship y algoritmo tripartito de consolidación 2:1 sin pérdida de datos contables).
---

# Data Mesh & Master Data Management (MDM) Governance

## Cuándo Activar esta Skill
- Al diseñar **Productos de Datos (Data Mesh)** entre dominios o construir pipelines de reconciliación de entidades maestras (**MDM / Golden Record**).
- Al resolver duplicados (`2:1` o `N:1`) en tablas contables, fiscales o de clientes donde un simple `DELETE` o `DROP DUPLICATES` causaría pérdida de saldos o historial.

## 1. Algoritmo Tripartito de Consolidación 2:1 sin Pérdida de Datos (MDM Survivorship)

Cuando dos registros representan la misma entidad o período contable (p. ej. un registro con clave legada corrupta y otro con clave normalizada), **nunca ejecutes una eliminación ciega**. Clasifica cada par en una de estas 3 ramas deterministas:

1. **Rama A — `Safe Delete` (Duplicado Exacto o Vacío)**:
   - El registro obsoleto no aporta ningún atributo ni saldo adicional respecto al registro canónico (`saldo_obsoleto == 0` o idéntico byte a byte).
   - **Acción**: Respaldar en colección/tabla de auditoría `_archived_duplicates` y eliminar el obsoleto.
2. **Rama B — `Metadata Upgrade` (Supervivencia de Estado Rico)**:
   - El registro canónico tiene la clave correcta pero el registro obsoleto contiene metadatos más ricos o recientes (ej. teléfono verificado, estado de validación).
   - **Acción**: Copiar los atributos faltantes al registro canónico (`$set` selectivo) y luego archivar/eliminar el obsoleto.
3. **Rama C — `Complex Accounting Merge` (Fusión Aditiva de Saldos/Movimientos)**:
   - Ambos registros contienen movimientos o montos distintos que deben preservar la invariante de suma total (`Suma(Antes) == Suma(Después)`).
   - **Acción**: Sumar montos en centavos enteros (`$inc` o suma vectorizada), concatenar/deduplicar arrays de trazabilidad (`auditTrail`), verificar el invariante de suma antes del commit y archivar el registro absorbido.

## 2. Estándar de "Datos como Producto" (Data Mesh Checklist)

Un dataset Gold solo puede graduarse a **Data Product** si empaqueta en el mismo repositorio:
1. **Código de transformación determinista** (modelo `dbt` o asset `Dagster`).
2. **Contrato de Datos (`contract: {enforced: true}` / ODCS)** con propietario (`owner`), grano y SLA de frescura.
3. **Suite de Calidad Automatizada** (`dbt unit_tests` + `Great Expectations` / `Asset Checks`).
4. **Linaje OpenLineage y Telemetría OTel**.
