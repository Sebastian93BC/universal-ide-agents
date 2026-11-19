---
name: python-env-and-pipeline-safety
description: Aislamiento de entornos Python (.venv), prohibición de secretos/rutas locales, separación declarativa de entornos y seguridad en inferencia ML.
trigger: always_on
applyTo: "**/*.py,**/*.sh,**/*.json,**/*.yml,**/*.yaml"
---

# Seguridad Operativa en Scripts Python, Contenedores e Inferencia ML

1. **Intérprete del Entorno Virtual**:
   - Al ejecutar comandos Python, pytest, dbt o Dagster en un proyecto, usa siempre el ejecutable del entorno virtual local (`.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/dg`) en lugar del Python global del sistema.
2. **Cero Credenciales, URIs o Rutas Personales Hardcodeadas**:
   - Prohibido incluir URIs con usuario/contraseña, tokens o rutas absolutas locales (`/Users/...`) en código o configuraciones MCP. Usa variables de entorno (`${ENV_VAR}`).
3. **Idempotencia y `--dry-run` por Defecto**:
   - Cualquier script que elimine, migre, consolide o rebalancee datos en producción debe incluir un modo `--dry-run` que imprima el conteo e impacto antes de mutar estado.
4. **Prohibición de `fit()` / `fit_transform()` en Inferencia ML**:
   - En pipelines de inferencia o scoring productivo, jamás recalcules estadísticas con `scaler.fit_transform(X_new)`. Carga siempre el artefacto `sklearn.pipeline.Pipeline` serializado en entrenamiento (`joblib.load`) y llama exclusivamente a `pipeline.predict(X_new)` tras validar cardinalidad y orden de columnas.
