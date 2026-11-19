# `universal-ide-agents` — Multi-IDE Data Engineering Agent & Skill Hub

Repositorio centralizado y **Fuente Única de Verdad** de **Agentes, Subagentes, Skills (`SKILL.md`), Reglas, Hooks, Configuraciones MCP y Playbooks de Producción**, diseñado específicamente para **Ingeniería de Datos (Big Data y Datos Transaccionales de Alto Volumen)** y compilado automáticamente para trabajar de forma simultánea en:

- **Google Antigravity / Gemini CLI** (`.agents/`, `AGENTS.md`, `.antigravity-instructions.md`)
- **Claude Code** (`.claude/`, `CLAUDE.md`, `.mcp.json`)
- **VS Code / GitHub Copilot** (`.github/agents/`, `.github/skills/`, `.github/instructions/`, `.github/hooks/`)

---

## 1. Stack Principal y Capacidades

| Dominio | Tecnologías Cubiertas | Activos Destacados |
| :--- | :--- | :--- |
| **Motores Transaccionales y Documentales** | **MongoDB (Replica Sets & Sharded Clusters)**, **PostgreSQL** | Pre-cálculo diario de ventanas móviles (`7d..180d`) con 1 lectura/día del crudo, histogramas para `P95` con `$setWindowFields`, mapa `lastSeen` para distincts, `$merge` seguro sin pérdida por *shallow merge*, `PROJECTION_COVERED` + `SHARDING_FILTER`, pre-split en 2 fases sobre colección vacía y gobernanza criptográfica **CSFLE / `crypt_shared`** (`_PLAIN`, `_HASH`, `_ENCRYPTED`). |
| **Lakehouse Columnar & Procesamiento Distribuido** | **DuckDB / DuckLake**, **Parquet**, **PySpark + Delta Lake / Apache Iceberg** | Offload analítico CDC `MongoDB -> Parquet -> DuckDB` con deduplicación vectorizada `QUALIFY ROW_NUMBER()`, salto de bloques por *Min-Max Zone Maps* (`ORDER BY` físico vs hiper-particionamiento), regla *Single-Writer* de DuckDB, *Liquid Clustering*, *Adaptive Query Execution (AQE)*, *Deletion Vectors* y *Change Data Feed (CDF)*. |
| **Orquestación, Transformación y Streaming** | **Dagster**, **Apache Airflow**, **dbt (1.9+)**, **Kafka + Debezium CDC**, **n8n** | Integración `Dagster + DuckDB + dbt` con `concurrency_key` y particiones sincronizadas, `dbt microbatch` con `lookback` para eventos tardíos, `contract: {enforced: true}`, `unit_tests:` nativos, equivalencia `Dagster <-> Airflow (Cosmos)`, *Outbox Pattern* + Schema Registry `BACKWARD_TRANSITIVE` y flujos n8n *Hub-and-Spoke* sin estado. |
| **Calidad, Linaje, Observabilidad e IA Operativa** | **5 Medallion Safety Guards**, **Great Expectations + OpenLineage**, **OpenTelemetry (OTel)** | Compuertas *Freshness/Lag*, *Writer `.tmp`*, *Lineage Consistency*, *Row Regression (`0.98`)* y *Dry-Run Judge*; trazas OTel en 3 niveles (`Módulo -> Proceso -> Operación`); y triaje inteligente de incidentes con el agente `pipeline-incident-triage` sobre servidores **MCP** en modo `--read-only`. |

---

## 2. Arquitectura del Repositorio

```text
universal-ide-agents/
├── core/                              # FUENTE ÚNICA DE VERDAD (editar siempre aquí)
│   ├── agents/                        # 11 agentes canónicos (Data Engineering + Core Lifecycle)
│   ├── skills/                        # 35 skills modulares (SKILL.md + scripts/)
│   ├── rules/                         # 6 reglas modulares de arquitectura, motores y diagramación SVG
│   ├── mcp/                           # Catálogo y plantillas MCP (dbt, dagster, duckdb, mongodb, postgres)
│   ├── hooks/                         # Hooks deterministas de validación pre/post herramienta
│   └── playbooks/                     # Playbook de incidentes reales de producción (INC-01..INC-10)
├── profiles/                          # Perfiles de despliegue (core, data-eng-full, data-eng-mongodb, data-eng-lakehouse, data-eng-n8n)
├── harvester/                         # Motor periódico Knowledge & Skill Harvester (ETL de memoria procedural)
├── scripts/
│   ├── validate_and_build.py          # Valida YAML, <=12k chars, cero Mermaid, cero términos de clientes y compila a los 3 IDEs
│   ├── harvest.py                     # Escáner incremental SHA-256 de proyectos, cursos y memorias locales
│   └── deploy-to-project.sh           # Instalador multi-IDE retrocompatible (--target, --profile, --dry-run, --clean)
├── .agents/                           # Salida compilada para Antigravity / Gemini CLI
├── .claude/                           # Salida compilada para Claude Code
├── .github/                           # Salida compilada para VS Code / GitHub Copilot
├── plans/                             # Control Room de planes, registro de tareas y base de conocimiento
├── AGENTS.md                          # Constitución raíz multi-agente
└── CLAUDE.md                          # Guía de entrada rápida para Claude Code
```

---

## 3. Flujo de Uso Rápido

### A. Validar y Compilar Activos tras Editar `core/`
```bash
python3 scripts/validate_and_build.py
```

### B. Ejecutar el Recopilador Periódico de Conocimientos (*Knowledge Harvester*)
Para escanear tus proyectos y cursos locales en busca de nuevas skills, reglas o hallazgos técnicos:
```bash
# 1. Inicializar tu configuración local de rutas (ignorado por Git)
python3 scripts/harvest.py --init-local-config

# 2. Escaneo incremental SHA-256 (genera harvester/inbox/<YYYY-MM-DD>/harvest_report.md)
python3 scripts/harvest.py

# 3. Una vez generalizados y compilados los nuevos activos en core/, marcar estado como procesado
python3 scripts/harvest.py --mark-processed
```

### C. Desplegar hacia un Proyecto Consumidor
```bash
# Previsualizar despliegue completo (Antigravity + Claude Code + VS Code)
./scripts/deploy-to-project.sh --dry-run --target all --profile data-eng-full /ruta/a/tu/proyecto

# Aplicar despliegue
./scripts/deploy-to-project.sh --target all --profile data-eng-full /ruta/a/tu/proyecto
```

---

## 4. Documentación Clave

- **Catálogo Completo de Activos (11 Agentes + 35 Skills + Reglas + MCP)**: [docs/asset-catalog.md](./docs/asset-catalog.md)
- **Playbook de Producción e Incidentes Reales (`INC-01..INC-10`)**: [core/playbooks/data-engineering-production-playbook.md](./core/playbooks/data-engineering-production-playbook.md)
- **Catálogo de Servidores MCP para Ingeniería de Datos**: [core/mcp/catalog.md](./core/mcp/catalog.md)
- **Extracción Maestra de Conocimientos (Proyectos, Cursos e Investigación Web)**: [plans/knowledge/2026-11-18-project-courses-web-knowledge-extraction.md](./plans/knowledge/2026-11-18-project-courses-web-knowledge-extraction.md)
