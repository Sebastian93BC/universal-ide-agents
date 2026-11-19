---
name: planning-and-versioning
description: Ciclo de vida de planes en plans/registry.md, compatibilidad con Parser V5 y versionado semántico en CHANGELOG.md.
trigger: model_decision
applyTo: "plans/**/*.md,CHANGELOG.md,README.md"
---

# Gobernanza de Planes (`plans/`) y Versionado Semántico

1. **Ciclo de Vida en `plans/`**:
   - Toda tarea mayor o refactorización arquitectónica debe registrarse en `plans/registry.md` con identificador correlativo y slug `YYYY-MM-DD-{kebab-name}`.
   - Los planes activos residen en `plans/{slug}_plan.md` y usan encabezados de nivel 2 (`## `) para compatibilidad con **Parser V5**.
   - Al completar una tarea, archivar el plan en `plans/historyPlans/{slug}_plan.md`, escribir el reporte en `plans/walkthroughs/{slug}_walkthrough.md` y actualizar `plans/registry.md` a `Completado`.
2. **Convenciones JSON Legadas (`plans/knowledge/knowledge_base.md`)**:
   - Mantener `camelCase` estricto en archivos JSON de configuración y conservar la clave `PREPROCESS_CONFIG` en `.github/hooks/context.json`.
3. **Ignorar `TO_DO.md`**:
   - No modificar ni depender de `TO_DO.md` para seguimiento formal; usar exclusivamente `plans/registry.md` y `CHANGELOG.md`.
