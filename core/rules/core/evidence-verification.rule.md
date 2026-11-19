---
name: evidence-verification
description: Protocolo anti-falsos-positivos con etiquetado obligatorio de evidencia ([VERIFICADO] vs [INFERIDO]) y taxonomía de hallazgos (DEFECTO, CONDICIONAL, ENDURECIMIENTO, PROPUESTA).
trigger: always_on
applyTo: "**/*"
---

# Protocolo de Evidencia y Anti-Falsos-Positivos

1. **Verificación Previa Obligatoria**: Nunca afirmes que un campo, índice, tabla, variable de entorno o archivo "no existe" o "está roto" sin haber inspeccionado antes las definiciones reales en el repositorio (`schema.yml`, `$jsonSchema`, migraciones, recursos Dagster, nodos upstream).
2. **Etiquetado de Evidencia**:
   - `[VERIFICADO]`: Confirmado directamente en archivo y línea del repositorio.
   - `[INFERIDO]`: Deducción dependiente de estado externo (p. ej. base de datos en vivo); debe indicar explícitamente qué comando o consulta confirma la hipótesis.
3. **Taxonomía de Revisión**:
   - `DEFECTO`: Error garantizado o pérdida de datos bajo el contrato actual.
   - `CONDICIONAL`: Fallo si ocurre una condición de borde plausible.
   - `ENDURECIMIENTO`: Guardarraíl operativo recomendado (timeout, `--dry-run`, índice cubierto, control de regresión).
   - `PROPUESTA`: Mejora opcional de estilo o mantenibilidad.
