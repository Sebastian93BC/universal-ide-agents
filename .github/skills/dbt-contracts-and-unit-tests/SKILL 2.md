---
name: dbt-contracts-and-unit-tests
description: Gobernanza de modelos dbt con Data Contracts (contract: enforced: true), restricciones de esquema y pruebas unitarias nativas (unit_tests:) para validar deduplicación, aritmética en centavos y lógica de ventanas móviles sin escanear datos productivos.
---

# dbt Data Contracts & Native Unit Tests

## Cuándo Activar esta Skill
- Al publicar modelos **Gold / Marts** consumidos por BI, ML u otros dominios de datos.
- Al probar transformaciones SQL complejas (deduplicación CDC, reconciliación contable 2:1, cálculo de ventanas móviles) antes de ejecutar sobre tablas masivas.

## 1. Contratos de Datos Obligatorios en Modelos Gold (`contract: {enforced: true}`)

Todo modelo Gold público debe declarar un contrato estricto en su archivo `.yml`. Si una transformación altera el nombre o tipo de dato de una columna, o introduce un `NULL` no permitido, `dbt build` aborta antes de corromper la tabla destino:

```yaml
version: 2

models:
  - name: fct_daily_account_balances
    config:
      contract:
        enforced: true
    constraints:
      - type: primary_key
        columns: [balance_date, account_hash]
    columns:
      - name: balance_date
        data_type: date
        constraints:
          - type: not_null
      - name: account_hash
        data_type: varchar
        constraints:
          - type: not_null
      - name: net_amount_cents
        data_type: bigint
        constraints:
          - type: not_null
```

## 2. Pruebas Unitarias Nativas de SQL (`unit_tests:` en dbt 1.8+)

Usa `unit_tests:` con filas simuladas en línea para verificar casos de borde (ej. deduplicación donde un evento `'d'` de borrado llega después de un `'u'`, o precisión en centavos):

```yaml
unit_tests:
  - name: test_cdc_deduplication_and_tombstone_filtering
    model: int_transactions_deduped
    given:
      - input: ref('stg_transactions_raw')
        rows:
          - {transaction_id: 'tx_1', cluster_ts: '2026-11-18 10:00:00', op_type: 'c', amount_cents: 1000}
          - {transaction_id: 'tx_1', cluster_ts: '2026-11-18 10:05:00', op_type: 'u', amount_cents: 1500}
          - {transaction_id: 'tx_2', cluster_ts: '2026-11-18 10:00:00', op_type: 'c', amount_cents: 2000}
          - {transaction_id: 'tx_2', cluster_ts: '2026-11-18 10:10:00', op_type: 'd', amount_cents: 2000}
    expect:
      rows:
        - {transaction_id: 'tx_1', amount_cents: 1500}
```
