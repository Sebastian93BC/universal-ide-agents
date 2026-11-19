---
name: dagster-asset-architecture
description: Diseño de Software-Defined Assets en Dagster: recursos configurables con dg.EnvVar, validación estática dg check defs, particionamiento temporal/dinámico, Asset Checks con bloqueo de downstream y aislamiento de código por code locations.
---

# Dagster Software-Defined Assets Architecture

## Cuándo Activar esta Skill
- Al crear o refactorizar pipelines en **Dagster** (`@asset`, `@multi_asset`, `@asset_check`, `ConfigurableResource`, `ScheduleDefinition`, `SensorDefinition`).
- Al preparar backfills particionados o diagnosticar variables de entorno que no se actualizan entre ejecuciones.

## 1. Cinco Reglas de Oro en Dagster

1. **`dg.EnvVar("...")` Obligatorio en Recursos Configurables**:
   - **Anti-patrón**: Usar `os.getenv("DB_URI")` al instanciar un `ConfigurableResource`. `os.getenv` se evalúa una sola vez cuando el servidor gRPC carga el módulo Python, congelando el valor y exponiéndolo en metadatos.
   - **Patrón correcto**:
     ```python
     import dagster as dg


     class DuckLakeResource(dg.ConfigurableResource):
       catalog_uri: str
       data_path: str


     defs = dg.Definitions(
         resources={
             "ducklake": DuckLakeResource(
                 catalog_uri=dg.EnvVar("DUCKLAKE_CATALOG_URI"),
                 data_path=dg.EnvVar("DUCKLAKE_DATA_PATH"),
             )
         }
     )
```
2. **Validación Estática (`dg check defs`) Antes de Levantar o Commitear**:
   - Ejecuta siempre `dg check defs` tras cualquier cambio en assets, jobs o schedules para capturar ciclos en el DAG, dependencias rotas o errores de importación antes de correr `dg dev` o `dg launch`.
3. **Particionamiento Explícito (`DailyPartitionsDefinition` / `TimeWindowPartitionsDefinition`)**:
   - Lee la ventana exacta desde `context.partition_time_window` en lugar de usar `datetime.now()` dentro del asset. Esto garantiza que un backfill histórico de hace 6 meses sea 100% determinista e idempotente.
4. **Asset Checks con Bloqueo de Downstream (`blocking=True`)**:
   - Vincula validaciones críticas (cero nulos en PK, no-regresión de conteo de filas, balance contable) mediante `@dg.asset_check(asset=..., blocking=True)` para impedir que una capa Gold consuma una capa Silver corrupta.
5. **Telemetría Estructurada en `context.add_output_metadata`**:
   - Reporta siempre en cada materialización: `row_count`, `duration_ms`, `partition_key`, `min_event_ts`, `max_event_ts` y `output_path` para trazabilidad visual en la UI de Dagster.
