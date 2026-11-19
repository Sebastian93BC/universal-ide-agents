---
name: dbt-transactional-microbatch
description: Modelado incremental en dbt (1.8 / 1.9+) para tablas transaccionales de alto volumen: estrategia microbatch (event_time, batch_size, lookback para eventos tardíos), delete+insert vs merge, y snapshots SCD Tipo 2 en staging.
---

# dbt for High-Volume Transactional Data (`microbatch` & SCD2)

## Cuándo Activar esta Skill
- Al construir modelos incrementales en **dbt** sobre millones o miles de millones de transacciones, eventos CDC o logs.
- Al manejar datos tardíos (*late-arriving facts*) o historización de dimensiones mutables (SCD Tipo 2).

## 1. Estrategia Incremental `microbatch` (dbt 1.9+)

En lugar de escribir bloques manuales frágiles con `{% if is_incremental() %} WHERE event_ts >= (SELECT max(event_ts) FROM {{ this }}) {% endif %}`, utiliza `incremental_strategy='microbatch'` para procesar y re-intentar ventanas discretas de forma atómica:

```sql
{{
    config(
        materialized='incremental',
        incremental_strategy='microbatch',
        event_time='transaction_ts',
        begin='2025-01-01',
        batch_size='day',
        lookback=2,
        unique_key='transaction_id'
    )
}}

SELECT
    transaction_id,
    account_hash,
    transaction_ts,
    CAST(ROUND(amount * 100, 0) AS BIGINT) AS amount_cents,
    status
FROM {{ ref('stg_transactions_cdc') }}
```

- **`lookback=2`**: Re-procesa automáticamente los últimos 2 días en cada ejecución incremental para absorber transacciones que llegaron con retraso sin necesidad de backfills manuales.
- **Reprocesamiento Quirúrgico**: Permite ejecutar `dbt run --select fct_transactions --event-time-start "2026-11-01" --event-time-end "2026-11-05"` de forma totalmente idempotente.

## 2. Regla para Slowly Changing Dimensions (SCD Tipo 2) con `dbt snapshot`

- **Dónde aplicar `snapshot`**: Ejecuta `dbt snapshot` directamente sobre la **capa de entrada / fuente limpia** (antes de los joins complejos de negocio).
- **Configuración recomendada**:
  - Usa `strategy='timestamp'` con `updated_at` cuando la fuente sea confiable; usa `strategy='check'` con lista explícita de columnas críticas (`check_cols=['tier', 'status', 'credit_limit_cents']`) cuando la fuente no actualice `updated_at` consistentemente.
  - Activa `hard_deletes='invalidate'` (o `invalidate_hard_deletes=True`) para cerrar `dbt_valid_to` cuando un registro desaparece de la fuente.
