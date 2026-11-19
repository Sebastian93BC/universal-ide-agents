---
name: n8n-workflow-engineering
description: Ingeniería de flujos de datos en n8n bajo arquitectura Hub-and-Spoke sin estado: modularización por sub-workflows, validación estática S01-S10, separación declarativa de código (@only:dev vs @only:n8n), manejo de errores y seguridad de credenciales.
---

# n8n Stateless Hub-and-Spoke Workflow Engineering

## Cuándo Activar esta Skill
- Al diseñar, revisar o depurar flujos de automatización e integración de datos en **n8n** que interactúan con **MongoDB, PostgreSQL, APIs REST o agentes LLM/MCP**.
- Al sincronizar código JavaScript/Python compartido entre el repositorio local de desarrollo y nodos `Code` de n8n.

## 1. Arquitectura Hub-and-Spoke Sin Estado (Stateless Orchestration)

1. **Orquestador Central (`Hub`) + Sub-workflows Especializados (`Spokes`)**:
   - El flujo principal (`Hub`) solo coordina el estado de la corrida, inicializa el contexto de trazabilidad (`trace_id`, `module_name`) y llama a sub-workflows modulares mediante el nodo `Execute Workflow`.
   - Ningún sub-workflow debe asumir estado en memoria local entre ejecuciones; todo estado o checkpoint se lee y persiste en la base de datos (MongoDB / PostgreSQL).
2. **Separación Declarativa de Entorno (`@only:dev` vs `@only:n8n`)**:
   - Cuando desarrolles scripts JS reutilizables probados localmente con Node.js/Jest que luego se empaquetan en nodos `Code` de n8n, usa directivas de bloque para que el empaquetador filtre automáticamente las importaciones locales (`require('fs')`, `dotenv`) y conserve el wrapper de salida de n8n (`return items.map(...)`).

## 2. Checklist de Validación Estática de Workflows (`S01..S10`)

Antes de dar por válido un archivo `.json` de workflow n8n, verifica:
- **S01 (Cero Credenciales / URIs Hardcodeadas)**: Ningún nodo contiene tokens, contraseñas ni IPs literales en `parameters`; todo usa el almacén de credenciales de n8n o `$env.VAR`.
- **S02 (Integridad de Referencias `$node["..."]`)**: Todo nombre de nodo referenciado en expresiones `{{ $node["Nombre"].json... }}` existe exactamente con ese nombre y está aguas arriba del nodo actual.
- **S03 (Guardas ante Payloads Vacíos)**: Los nodos de consulta a BD que pueden devolver 0 documentos tienen manejo explícito (`alwaysOutputData: true` + nodo `IF` de verificación de vacío) para no abortar silenciosamente la rama de cierre de telemetría.
- **S04 (Workflow de Error Conectado)**: `settings.errorWorkflow` está configurado hacia el colector central de fallos/alertas.
- **S05 (Aritmética y Tipos BSON en Nodos MongoDB)**: Las fechas se convierten explícitamente a objetos `Date` / ISODate y los montos operan en centavos enteros.
