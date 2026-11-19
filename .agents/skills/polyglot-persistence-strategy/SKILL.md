---
name: polyglot-persistence-strategy
description: Estrategia de Persistencia Políglota para arquitecturas de datos modernas: matriz de decisión entre MongoDB (OLTP documental/operacional), PostgreSQL (catálogos ACID/relacional), DuckDB/DuckLake/Parquet (analítica columnar/Medallion) y Vector Search.
---

# Polyglot Persistence Strategy — Matriz de Motores de Datos

## Cuándo Activar esta Skill
- Al decidir en qué motor almacenar o procesar cada carga de trabajo dentro de una plataforma de datos, evitando forzar un único motor para cargas OLTP, OLAP y búsqueda vectorial.

## 1. Matriz de Asignación de Cargas de Trabajo

| Carga de Trabajo | Motor Primario Recomendado | Justificación Arquitectónica |
| :--- | :--- | :--- |
| **Ingesta Transaccional de Alta Velocidad / Perfiles Operativos / Polimorfismo JSON** | **MongoDB (Replica Set / Sharded Cluster)** | Escrituras distribuidas de baja latencia, documentos ricos sin `JOINs`, índices parciales y pre-cálculo de perfiles por clave. |
| **Catálogos de Metadatos ACID (Catálogo DuckLake, Estado Dagster/Airflow, Contabilidad Relacional Estricta)** | **PostgreSQL** | Integridad referencial declarativa, transacciones multi-tabla ligeras de metadatos y ecosistema universal de catálogos. |
| **Analítica Pesada, Ventanas Históricas Masivas, Cruces Dimensionales y Transformaciones `dbt`** | **DuckDB / DuckLake + Parquet** (o **PySpark + Delta/Iceberg** a escala `> 250 GB`) | Ejecución columnar vectorizada, compresión `ZSTD`, salto de bloques por *Zone Maps* y cero impacto sobre los motores OLTP. |
| **Streaming CDC y Desacoplamiento de Eventos entre Dominios** | **Apache Kafka + Debezium + Schema Registry** | Log inmutable particionado por PK que alimenta tanto consumidores en tiempo real como la capa Bronze del Lakehouse. |

## 2. Regla de Frontera OLTP <-> OLAP
- Ningún dashboard de BI ni reporte histórico de múltiples meses debe golpear directamente el primario de **MongoDB** o **PostgreSQL** transaccional.
- Establece siempre un puente de descarga incremental/CDC hacia **Parquet / DuckLake** o una colección reducida de resúmenes diarios.
