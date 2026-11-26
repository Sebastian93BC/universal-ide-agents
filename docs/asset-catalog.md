# Catálogo Maestro de Activos (`universal-ide-agents` v3.0.0)

Todos los activos de este catálogo tienen su fuente canónica en `core/` y son compilados y validados por `scripts/validate_and_build.py` hacia **Antigravity (`.agents/`)**, **Claude Code (`.claude/`)** y **VS Code GitHub Copilot (`.github/`)**. Qué llega a cada proyecto lo decide su perfil (sección 3); los activos de la categoría **Hub** solo existen en este repositorio.

---

## 1. Agentes Especializados (11 Agentes Canónicos)

| Categoría | Agente (`core/agents/`) | Rol Principal | Modo de Herramientas |
| :--- | :--- | :--- | :--- |
| **Data Engineering** | `data-engineer` | Arquitectura Medallion, pipelines batch/CDC, concurrencia DuckDB, particionamiento, backfills idempotentes y 5 Safety Guards. | Lectura y Análisis (`read`, `search`) |
| **Data Engineering** | `data-modeling-architect` | Modelado Relacional, Dimensional Kimball, Documental MongoDB, Columnar Parquet/Delta/Iceberg, Contratos ODCS/dbt y MDM. | Lectura y Análisis (`read`, `search`) |
| **Data Engineering** | `data-security-auditor` | Gobernanza criptográfica (`_PLAIN`, `_HASH`, `_ENCRYPTED`), MongoDB CSFLE (`crypt_shared`), protección PII y auditoría MCP/Docker. | Lectura y Análisis (`read`, `search`) |
| **Data Engineering** | `pipeline-reviewer` | Revisor forense anti-falsos-positivos (`DEFECTO` / `CONDICIONAL` / `ENDURECIMIENTO` / `PROPUESTA`) con evidencia `[VERIFICADO]` vs `[INFERIDO]`. | Lectura y Análisis (`read`, `search`) |
| **Data Engineering** | `pipeline-incident-triage` | Triaje inteligente de alertas y fallos de pipelines sobre OTel Spans, OpenLineage (*blast radius*) y MCP en modo read-only. | Lectura y Análisis (`read`, `search`) |
| **Core Lifecycle** | `planner` | Planificación arquitectónica bajo el patrón *Research Before Implementation*; el plan va donde indique el `AGENTS.md` del proyecto. | Lectura y Planeación (`read`, `search`, `edit`) |
| **Core Lifecycle** | `implementer` | Ejecución quirúrgica de planes aprobados, soporte `--dry-run`, escrituras `.tmp` y generación de walkthroughs. | Completo (`read`, `search`, `edit`, `execute`) |
| **Core Lifecycle** | `code-reviewer` | Revisión de código general y de datos con citas `archivo:línea` y taxonomía estricta de 4 niveles. | Lectura y Análisis (`read`, `search`) |
| **Core Lifecycle** | `docs-steward` | Gobernanza documental, sincronización de catálogos, CHANGELOG y diagramación estricta en SVG / tablas (cero Mermaid). | Documentación (`read`, `search`, `edit`) |
| **Core Lifecycle** | `tdd-cycle` | Ciclo disciplinado Red-Green-Refactor (`pytest`, `dbt unit_tests:`, `Great Expectations`). | Completo (`read`, `search`, `edit`, `execute`) |
| **Core Lifecycle** | `knowledge-harvester` | Dos modos. **Cierre de tarea** (proyecto): consolida el conocimiento de la tarea en el del proyecto, con las tres rutas recibidas por argumento (contrato con `dfa`, [contrato-template-dfa.md](./contrato-template-dfa.md)). **Hub**: procesa los reportes de `scripts/harvest.py` y consolida en `core/` (`CREATE`/`UPDATE`/`INVALIDATE`). | Completo (`read`, `search`, `edit`, `execute`) |

---

## 2. Catálogo de 36 Skills Modulares (`SKILL.md`)

| Categoría | Skill (`core/skills/<cat>/<name>/SKILL.md`) | Tecnologías y Problemas que Resuelve |
| :--- | :--- | :--- |
| **MongoDB Big Data & Transaccional** | `mongodb-schema-design` | Reglas de embedding vs referencing por cardinalidad, Bucket Pattern, `$jsonSchema` gradual, montos en centavos y Canonical Extended JSON. |
| **MongoDB Big Data & Transaccional** | `mongodb-query-optimizer` | Regla ESR, `PROJECTION_COVERED` + `SHARDING_FILTER`, índices parciales (`partialFilterExpression`), `MISSING != null` y `Array > Number`. |
| **MongoDB Big Data & Transaccional** | `mongodb-sharding-operations` | Selección de shard key, **Pre-Split en 2 fases sobre colección vacía**, rebalanceo trimestral (`splitFind`, `moveChunk`). |
| **MongoDB Big Data & Transaccional** | `mongodb-bigdata-patterns` | Prevención de pérdida de datos por *shallow merge* en `$merge`, idempotencia `deleteMany` + `$merge` y paralelización por cubetas `00..99`. |
| **MongoDB Big Data & Transaccional** | `mongodb-rolling-window-precalc` | Pre-cálculo diario de ventanas móviles (`7d..180d`) con lectura única del crudo, histogramas para `P95` exacto (`$setWindowFields`) y mapa `lastSeen`. |
| **MongoDB Big Data & Transaccional** | `mongodb-csfle-governance` | Triple campo (`_PLAIN`, `_HASH`, `_ENCRYPTED`) y solución a errores `crypt_shared` (`31127` `$$ROOT`, `9710000` `$merge`, `17217` `distinct`). |
| **DuckDB, Lakehouse & Streaming CDC** | `duckdb-parquet-optimization` | *Min-Max Zone Maps* (`ORDER BY` físico) vs hiper-particionamiento Hive, regla *Single-Writer*, `memory_limit` y spill-to-disk. |
| **DuckDB, Lakehouse & Streaming CDC** | `ducklake-medallion-architecture` | Arquitectura de 5 etapas (`Bronze -> Silver -> Gold -> Seal -> Publish`) con catálogo transaccional SQL **DuckLake** sobre Parquet. |
| **DuckDB, Lakehouse & Streaming CDC** | `mongodb-to-duckdb-cdc-offload` | Offload analítico desde MongoDB Change Streams/Debezium a Parquet + deduplicación vectorizada `QUALIFY ROW_NUMBER()` y *tombstones*. |
| **DuckDB, Lakehouse & Streaming CDC** | `pyspark-delta-iceberg-lakehouse` | Escala distribuida (`>250 GB`): *Liquid Clustering* / *Hidden Partitioning*, *AQE* obligatorio, prohibición de `.cache()`, *Deletion Vectors* y *CDF*. |
| **DuckDB, Lakehouse & Streaming CDC** | `kafka-debezium-cdc-streaming` | CDC basado en logs (WAL/Oplog), particionado por PK, `tombstones.on.delete`, Schema Registry `BACKWARD_TRANSITIVE`, *Outbox Pattern* y *DLQ*. |
| **Dagster & Orquestación** | `dagster-asset-architecture` | Software-Defined Assets, `dg.EnvVar` vs `os.getenv`, `dg check defs`, `DailyPartitionsDefinition` y `AssetChecks` con `blocking=True`. |
| **Dagster & Orquestación** | `dagster-duckdb-dbt-integration` | Coordinación `dagster-dbt`, serialización `concurrency_key: duckdb_single_writer` y mapeo `partition_time_window` -> `--vars`. |
| **Dagster & Orquestación** | `medallion-safety-guards` | Implementación de los **5 Medallion Safety Guards** (Freshness/Lag, Concurrency `.tmp`, Lineage Consistency, Row Regression `0.98`, Dry-Run Judge). |
| **Dagster & Orquestación** | `airflow-dagster-interoperability` | Equivalencia arquitectónica entre Dagster y Apache Airflow 2.8+/3.x (TaskFlow `@task`, Datasets, `Astronomer Cosmos` para dbt, Pools). |
| **Dagster & Orquestación** | `ai-pipeline-incident-triage` | Diseño de alertas inteligentes y triaje con agentes LLM en modo `--read-only` conectando OTel, OpenLineage y servidores MCP. |
| **dbt & Calidad de Datos** | `dbt-transactional-microbatch` | Estrategia incremental `microbatch` (dbt 1.9+) con `event_time`, `batch_size`, `lookback` para eventos tardíos y `dbt snapshot` (SCD2). |
| **dbt & Calidad de Datos** | `dbt-contracts-and-unit-tests` | Contratos exigidos (`contract: {enforced: true}`) en marts Gold y pruebas unitarias SQL nativas (`unit_tests:`). |
| **dbt & Calidad de Datos** | `dbt-duckdb-lakehouse-patterns` | Materializaciones `external` en Parquet ordenado, lectura con `union_by_name=true` y tuning de `profiles.yml`. |
| **dbt & Calidad de Datos** | `great-expectations-openlineage-quality` | Suites Great Expectations (GX 1.3+), contratos ODCS y emisión de facetas **OpenLineage** para cálculo de *blast radius*. |
| **Modelado de Datos & MDM** | `sql-to-nosql-modeling` | Heurísticas y script `audit_relational_schema.py` para transformar DDL relacional a documental o Lakehouse columnar. |
| **Modelado de Datos & MDM** | `attribute-pattern-eav` | Consolidación de decenas de campos dispersos bajo `attributes: [{k, v, u}]` e índice único con `$elemMatch`. |
| **Modelado de Datos & MDM** | `polymorphic-schema-design` | Esquemas polimórficos gobernados con discriminador `entityType`, `schemaVersion`, `$jsonSchema` (`oneOf`) e índices parciales. |
| **Modelado de Datos & MDM** | `schema-evolution-versioning` | Migración sin caída (*Expand-and-Contract*) en 3 fases y lectura tolerante entre versiones de esquema. |
| **Modelado de Datos & MDM** | `extended-reference-optimizer` | Eliminación de `$lookup` en caliente duplicando 2–4 atributos estables con política de sincronización *point-in-time* vs eventual. |
| **Modelado de Datos & MDM** | `polyglot-persistence-strategy` | Matriz de asignación de cargas entre MongoDB, PostgreSQL, DuckDB/DuckLake/Parquet, PySpark/Delta y Kafka. |
| **Modelado de Datos & MDM** | `data-mesh-and-mdm-governance` | Algoritmo tripartito de consolidación `2:1` sin pérdida contable (*Safe Delete*, *Metadata Upgrade*, *Complex Merge*) y checklist *Data as a Product*. |
| **Automatización, Infra & Core** | `parallel-processing-patterns` | Clientes BD *fork-safe* por worker, particionado por cubetas sin colisión, *bounded batching* y dimensionamiento de pools. |
| **Automatización, Infra & Core** | `docker-data-stack` | Regla del 75% de RAM contra OOM (`exit 137`), `service_healthy` real, persistencia de volúmenes y cero secretos en capas Docker. |
| **Automatización, Infra & Core** | `n8n-workflow-engineering` | Orquestación *Hub-and-Spoke* sin estado, directivas `@only:dev`/`@only:n8n` y checklist de validación estática `S01..S05`. |
| **Automatización, Infra & Core** | `ml-inference-pipeline-safety` | Prohibición de `fit_transform` en producción, serialización de `sklearn.pipeline.Pipeline` con `joblib` y validación de contrato de features. |
| **Automatización, Infra & Core** | `otel-pipeline-observability` | Jerarquía de 3 niveles de Spans OpenTelemetry (`Módulo -> Proceso -> Operación`), sanitización PII y paneles Sistema vs Calidad. |
| **Automatización, Infra & Core** | `subagent-orchestration-patterns` | Los 5 patrones de orquestación multi-agente y aislamiento de contexto (*Context Engineering*). |
| **Core** | `session-handoff` | Nota de traspaso al cerrar una sesión: dónde quedó, qué se decidió (incluido lo rechazado), siguiente paso y preguntas abiertas, escrita en la tarea para la siguiente sesión o el otro IDE. |
| **Hub (solo este repositorio)** | `knowledge-harvester` | Operación del motor periódico `scripts/harvest.py` y consolidación ETL de memoria procedural (`CREATE`/`UPDATE`/`INVALIDATE`). |
| **Hub (solo este repositorio)** | `skill-creator` | Estándar de creación de skills multi-IDE (`<= 12,000` chars, YAML frontmatter, progressive disclosure). |

---

## 3. Reglas, Perfiles, Hook, MCP y Playbooks

- **Reglas (`core/rules/`)**: núcleo `diagramming-svg`, `evidence-verification` y `limites-tres-niveles` (siete límites en tres niveles, cada uno con su comprobación en el guardián); ingeniería de datos `mongodb-bson-and-merge-invariants`, `duckdb-dagster-dbt-invariants` y `python-env-and-pipeline-safety`; hub `planning-and-versioning`.
- **Hook (`core/hooks/`)**: `universal-ide-agents-guard.py`, guardián `PreToolUse` de Claude Code que aplica `limites-tres-niveles`. Se despliega en `.claude/hooks/` y lo conecta el `.claude/settings.json` del proyecto.
- **Perfiles de despliegue (`profiles/`)**: `core`, `data-eng-base` (núcleo, MongoDB y modelado, sin herramienta de ETL), `data-eng-n8n`, `data-eng-dagster-duckdb`, `data-eng-lakehouse` y `data-eng-full`. Detalle en [multi-ide-consumption.md](./multi-ide-consumption.md), sección 2.
- **Catálogo y plantillas MCP**: [core/mcp/catalog.md](../core/mcp/catalog.md) y `core/mcp/templates/data-eng-full.mcp.json`, filtrada por perfil al desplegar.
- **Playbook de producción**: [core/playbooks/data-engineering-production-playbook.md](../core/playbooks/data-engineering-production-playbook.md).
