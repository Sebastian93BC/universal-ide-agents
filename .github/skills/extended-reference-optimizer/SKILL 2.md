---
name: extended-reference-optimizer
description: Diseño y sincronización del Extended Reference Pattern en MongoDB para eliminar $lookup costosos en tiempo de lectura, definiendo qué campos duplicar y cómo actualizarlos de forma asíncrona/eventual.
---

# Extended Reference Pattern Optimizer

## Cuándo Activar esta Skill
- Cuando una consulta crítica en MongoDB ejecuta un `$lookup` sobre millones de documentos transaccionales solo para mostrar o filtrar por 2–3 atributos de una entidad maestra (ej. nombre, categoría o segmento del comercio/cliente).

## 1. Reglas de Selección de Campos a Incrustar

En el documento transaccional (`orders` / `transactions`), incrusta un subdocumento `customerSummary` o `merchantSummary` que contenga **exclusivamente**:
1. **El identificador inmutable (`_id` / `entityHash`)** para poder navegar al maestro cuando se requiera el detalle completo.
2. **Los 2 a 4 atributos de alta lectura y baja frecuencia de mutación** (ej. `categoryCode`, `regionCode`, `segment`).
3. **Prohibido incrustar**: Atributos que mutan en cada transacción (contadores, saldos, `lastLogin`) o listas largas.

## 2. Sincronización Controlada de Atributos Duplicados

Cuando un atributo del documento maestro cambia (ej. un cliente cambia de `segment`):
- **Si el histórico debe reflejar el estado en el momento de la transacción (Point-in-Time)**: **NO actualices** los documentos históricos; el valor incrustado actúa como fotografía inmutable (*snapshot*) del momento de la operación.
- **Si el atributo debe reflejar el valor actual**: Dispara una actualización asíncrona por lotes (`updateMany` paginado por cursor o vía Change Stream) solo sobre la ventana operativa activa.
