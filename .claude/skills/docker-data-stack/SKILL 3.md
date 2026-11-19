---
name: docker-data-stack
description: Diseño, endurecimiento y diagnóstico de contenedores Docker y Docker Compose para plataformas de datos (Dagster, DuckDB/DuckLake, MongoDB, PostgreSQL, Kafka, n8n): límites de memoria, diagnóstico OOM (exit 137), healthchecks reales y volúmenes persistentes.
---

# Docker & Containerized Data Stack Engineering

## Cuándo Activar esta Skill
- Al crear o auditar archivos `Dockerfile` y `docker-compose.yml` para servicios de datos (**Dagster, dbt, DuckDB, PostgreSQL, MongoDB, Kafka, n8n**).
- Al diagnosticar contenedores que se reinician solos, fallos `exit code 137` (OOM Killed) o problemas de permisos en volúmenes montados.

## 1. Cinco Reglas de Producción para `docker-compose.yml` de Datos

1. **Alineación entre el Límite del Contenedor y el Límite del Motor (`OOM Prevention`)**:
   - Si un contenedor tiene `mem_limit: 8g` y DuckDB o la JVM intenta usar el 100% de la RAM del host, el kernel Linux matará el contenedor con **`exit code 137` (SIGKILL / OOMKilled)**.
   - **Regla del 75%**: Fija siempre el límite interno del motor al `75–80%` del límite del contenedor:
     - DuckDB: `SET memory_limit = '6GB'` para un contenedor de `8g`.
     - MongoDB WiredTiger: `--wiredTigerCacheSizeGB 4` para un contenedor de `8g`.
     - Spark / Kafka JVM: `-Xmx6g` para un contenedor de `8g`.
2. **`depends_on` con `condition: service_healthy` (Nunca solo `service_started`)**:
   - Que el contenedor de PostgreSQL o MongoDB haya arrancado (`service_started`) no significa que acepte conexiones. Define siempre un `healthcheck` real (`pg_isready` o `mongosh --eval "db.adminCommand('ping')"`) antes de levantar Dagster o n8n.
3. **Separación de Código y Datos Persistentes**:
   - Monta los datos del Lakehouse (`./data/lakehouse:/app/data/lakehouse`) y volúmenes de bases de datos en volúmenes nombrados o bind mounts dedicados, nunca dentro de la capa efímera del contenedor.
4. **Cero Secretos en `docker-compose.yml` o `Dockerfile`**:
   - Prohibido usar `ENV PASSWORD=...` en un `Dockerfile` (queda grabado en el historial de capas de la imagen). Inyecta secretos en tiempo de ejecución vía `env_file: .env` (ignorado en Git) y provee un `.env.example`.
5. **Diagnóstico Rápido de Fallos de Contenedor**:
   - Verificar si fue OOMKilled: `docker inspect <container> --format '{{.State.OOMKilled}} {{.State.ExitCode}}'`.
