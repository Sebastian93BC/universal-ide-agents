---
name: three-level-limits
description: Límites del agente en tres niveles (siempre, preguntar primero, nunca). Una restricción y una razón por regla; cada una tiene una comprobación mecánica en el guardián de herramientas.
trigger: always_on
applyTo: "**"
---

# Límites en tres niveles

Cada regla tiene una sola restricción, su razón y cómo se comprueba. El guardián `.claude/hooks/universal-ide-agents-guard.py` (Claude Code, hook `PreToolUse`) aplica las comprobaciones; es una segunda capa, no una frontera de seguridad: la frontera es que el agente no tenga el secreto.

## Siempre

1. **Trabaja en la rama `local`.** Razón: los ambientes del cliente no son seguros para agentes; en `local` la base es dummy. Comprobación: si existe la rama `local` y la activa es otra, el guardián pide confirmación antes de editar archivos.

## Preguntar primero

2. **Pregunta antes de escribir en una base de un ambiente del cliente.** Razón: es caro de deshacer y afecta datos reales. Comprobación: el guardián pide confirmación para comandos con `--env development|quality|production` y para `mongosh`/`psql` contra un servidor que no sea `localhost`.
3. **Pregunta antes de cualquier despliegue.** Razón: cambia lo que corre en el cliente. Comprobación: el guardián pide confirmación para `dfa deploy`, `deploy_n8n`, `kubectl apply`, `helm upgrade`, `docker push` y `dg deploy`.
4. **Pregunta antes de cualquier commit o push.** Razón: los commits los decide el usuario. Comprobación: el guardián pide confirmación para `git commit` y `git push`.

## Nunca

5. **Nunca leas credenciales.** Razón: un secreto leído ya está fuera de control. Haz en su lugar: de `.env.example` lee solo los nombres. Comprobación: el guardián bloquea la lectura de `.env` y `.env.*` (salvo `.env.example`) por herramienta o por comando.
6. **Nunca imprimas un secreto.** Razón: la salida queda en el historial del IDE. Haz en su lugar: usa los comandos de `dfa`, que usan la credencial sin mostrarla. Comprobación: el guardián bloquea `printenv`, `env` sin argumentos y `echo` de variables con `KEY`, `TOKEN`, `SECRET`, `PASSWORD` o `URI` en el nombre.
7. **Nunca borres una colección o tabla existente.** Razón: no hay vuelta atrás sin respaldo. Haz en su lugar: crea una nueva y migra. Comprobación: el guardián bloquea `drop()`, `dropCollection`, `dropDatabase`, `DROP TABLE|SCHEMA|DATABASE` y `TRUNCATE`.
