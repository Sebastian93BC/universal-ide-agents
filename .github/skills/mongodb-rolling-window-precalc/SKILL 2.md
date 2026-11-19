---
name: mongodb-rolling-window-precalc
description: Arquitectura de pre-cálculo diario incremental para métricas de ventanas móviles (7d, 15d, 30d, 90d, 180d) sobre datos transaccionales masivos en MongoDB. Evita re-escanear meses de transacciones crudas mediante colecciones reducidas, histogramas para P95 exacto ($setWindowFields) y estado monótono lastSeen para conteos distintos.
---

# MongoDB Rolling Window Daily Pre-Calculation Architecture

## Cuándo Activar esta Skill
- Cuando un sistema transaccional (banca, pagos, fraude, retail, telemetría) necesita calcular indicadores sobre **ventanas móviles** (`7d`, `15d`, `30d`, `90d`, `180d`) como sumas, promedios, desviación estándar, percentiles (`P95`) o conteos distintos (`distinct devices/beneficiaries`).
- Cuando consultar la colección transaccional cruda (`raw_transactions`) para 90 o 180 días en cada corrida diaria provoca saturación de I/O, agotamiento de caché WiredTiger o tiempos de ejecución de horas.

## 1. Principio Arquitectónico: Lectura Única del Crudo + Colección Diaria Reducida

**Regla de Oro**: La colección transaccional cruda (`raw_transactions`) **solo se lee 1 vez por día** (únicamente para el día de corte `D`). Jamás escanees 30, 90 o 180 días sobre `raw_transactions`.

1. **Etapa 1 — Compresión Diaria (`raw_transactions[D] -> daily_entity_summary[D]`)**:
   - Lee únicamente las transacciones del día `D` y agrupa por `(entityId, date: D)` reduciendo el volumen entre `10x` y `100x`.
   - Guarda en `daily_entity_summary` las componentes aditivas y de estado del día `D`:
     - `txCount`: conteo entero del día.
     - `sumAmountCents`: suma exacta en centavos enteros (`$toLong`).
     - `sumSqAmountCents`: suma de cuadrados (`\sum x^2`) para poder calcular varianza/desviación estándar poblacional en cualquier ventana móvil sin guardar las transacciones individuales.
     - `amountHistogram`: mapa o array compacto de frecuencias por tramo/valor para percentiles.
     - `seenTargets`: lista deduplicada del día de contrapartes/dispositivos vistos en `D`.
2. **Etapa 2 — Agregación de Ventana Móvil sobre la Colección Reducida (`daily_entity_summary[D-180..D] -> entity_rolling_profiles`)**:
   - Todas las ventanas (`7d`, `15d`, `30d`, `90d`, `180d`) se calculan leyendo exclusivamente `daily_entity_summary` (que es órdenes de magnitud más pequeña y cabe en RAM).

## 2. Tres Patrones Matemáticos de Estado Incremental

### A. Percentil 95 (`P95`) Exacto sin Re-leer Transacciones Crudas
- Los percentiles no son linealmente aditivos (`P95(día 1) + P95(día 2) != P95(2 días)`).
- **Patrón**: En `daily_entity_summary`, almacena un histograma compacto `{ bucketValueCents, freq }` del día. Para calcular el `P95` de 30 o 90 días, suma las frecuencias de los histogramas en la ventana y utiliza `$setWindowFields` con frecuencia acumulada para localizar el primer bucket donde `cumFreq >= 0.95 * totalCount`.

### B. Conteos Distintos (`Distinct`) en Ventanas Móviles vía Estado Monótono `lastSeen`
- Hacer `$addToSet` sobre 90 días de transacciones crudas explota memoria.
- **Patrón**: Mantén en el perfil de la entidad un mapa compacto `lastSeenByTarget: { "<targetHash>": ISODate("2026-11-18") }` actualizado monótonamente con `$max` solo con los elementos vistos en el día `D`.
- El conteo de distintos en `7d`, `30d` o `90d` se reduce a contar cuántas entradas del mapa tienen `lastSeen >= (D - ventana)` y podar periódicamente las entradas con `lastSeen < (D - maxWindow)`.

### C. Dominancia del Costo de Escritura en `$merge`
- En pipelines de pre-cálculo, el cuello de botella real suele ser el `70–85%` del tiempo invertido en las escrituras aleatorias de `$merge` sobre índices secundarios del destino.
- **Mitigación**: Minimiza el número de índices secundarios en la colección destino de perfiles, agrupa múltiples ventanas (`7d`, `30d`, `90d`) en un **único `$merge` consolidado por entidad** en lugar de ejecutar 5 pipelines con 5 `$merge` separados, y proyecta estrictamente los campos modificados.
