# AGENTS.md — Constitución Multi-IDE de Ingeniería de Datos (`universal-ide-agents`)

Este repositorio es la **Fuente Única de Verdad** de agentes, subagentes, skills (`SKILL.md`), reglas, configuraciones MCP y playbooks de producción para **Ingeniería de Datos (Big Data y Datos Transaccionales)**, compilado automáticamente para **Antigravity / Gemini CLI** (`.agents/`), **Claude Code** (`.claude/`) y **VS Code GitHub Copilot** (`.github/`).

---

## 1. Stack y Dominios Cubiertos

- **Motores Transaccionales y Documentales**: **MongoDB** (Sharding, `$merge` seguro, `PROJECTION_COVERED`, pre-cálculo de ventanas móviles, CSFLE / `crypt_shared`), **PostgreSQL**.
- **Lakehouse Analítico y Formato Abierto**: **DuckDB / DuckLake**, **Parquet** (*Min-Max Zone Maps*), **PySpark + Delta Lake / Apache Iceberg** (*Liquid Clustering*, *AQE*, *Deletion Vectors*, *CDF*).
- **Orquestación, Transformación y Streaming**: **Dagster** (`@asset`, `@dbt_assets`, `AssetChecks`, `dg.EnvVar`, `dg check defs`), **Apache Airflow** (TaskFlow + `Cosmos`), **dbt (1.9+)** (`microbatch`, `contract: {enforced: true}`, `unit_tests:`), **Apache Kafka + Debezium CDC**, **n8n** (*Hub-and-Spoke* sin estado).
- **Calidad, Linaje y Observabilidad**: **5 Medallion Safety Guards**, **Great Expectations (GX 1.3+) + OpenLineage**, **OpenTelemetry (3 niveles de Spans: `Módulo -> Proceso -> Operación`)**.

---

## 2. Reglas Globales Inquebrantables

1. **Fuente Canónica y Compilación**:
   - Edita siempre los activos dentro de `core/` (`core/agents/`, `core/skills/`, `core/rules/`, `core/mcp/`, `core/playbooks/`).
   - Ejecuta `python3 scripts/validate_and_build.py` para validar YAML, límites (`<= 12,000` chars), ausencia de términos de clientes y compilar hacia `.agents/`, `.claude/` y `.github/`.
2. **Prohibición Estricta de Mermaid**:
   - **NUNCA** generes bloques de código `mermaid`. Usa archivos `.svg` independientes en `docs/img/` o tablas Markdown nativas.
3. **Protocolo Anti-Falsos-Positivos y Evidencia**:
   - Verifica siempre esquemas, migraciones e índices antes de afirmar que algo falta. Etiqueta cada hallazgo como `[VERIFICADO]` o `[INFERIDO]` bajo la taxonomía `DEFECTO` | `CONDICIONAL` | `ENDURECIMIENTO` | `PROPUESTA`.
4. **Seguridad, Idempotencia y `--dry-run`**:
   - Cero credenciales, URIs o rutas personales en código. Todo script que mute datos debe soportar `--dry-run` y escritura atómica vía `.tmp`.
5. **Control Room (`plans/`)**:
   - Registra planes en `plans/registry.md`, consulta `plans/knowledge/` e ignora `TO_DO.md`.

---

## 3. Índice de Progressive Disclosure (Dónde Consultar Detalles)

- **Agentes Especializados**: `core/agents/data-engineering/` (`data-engineer`, `data-modeling-architect`, `data-security-auditor`, `pipeline-reviewer`, `pipeline-incident-triage`) y `core/agents/core/` (`planner`, `implementer`, `code-reviewer`, `docs-steward`, `tdd-cycle`, `knowledge-harvester`).
- **Catálogo de 25 Skills (`SKILL.md`)**: `core/skills/` (y espejos en `.agents/skills/`, `.claude/skills/`, `.github/skills/`).
- **Catálogo y Plantillas MCP**: [core/mcp/catalog.md](./core/mcp/catalog.md).
- **Playbook de Incidentes Reales (`INC-01..INC-10`)**: [core/playbooks/data-engineering-production-playbook.md](./core/playbooks/data-engineering-production-playbook.md).
- **Motor Periódico de Cosecha de Conocimiento**: `python3 scripts/harvest.py` (ver skill `knowledge-harvester`).
