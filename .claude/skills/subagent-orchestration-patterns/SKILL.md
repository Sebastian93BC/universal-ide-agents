---
name: subagent-orchestration-patterns
description: Los 5 patrones de orquestación de subagentes para IDEs con IA (Antigravity, Claude Code, VS Code Copilot): Investigación previa read-only, Análisis paralelo ortogonal, Exploración competitiva, Revisión PR multi-perspectiva y Coordinador-Trabajador con aislamiento de contexto.
---

# Subagent Orchestration & Context Engineering Patterns

## Cuándo Activar esta Skill
- Cuando una tarea compleja de ingeniería de datos o refactorización amenaza con saturar la ventana de contexto (*context rot*).
- Al coordinar múltiples subagentes especializados (`planner`, `data-engineer`, `data-modeling-architect`, `data-security-auditor`, `pipeline-reviewer`, `implementer`).

## 1. Los 5 Patrones de Orquestación Multi-Agente

| Patrón | Cuándo Usarlo | Configuración de Herramientas y Contexto |
| :--- | :--- | :--- |
| **1. Investigación Previa a la Implementación (*Research Before Implementation*)** | Antes de editar un módulo desconocido o auditar un esquema grande. | Lanza un subagente con acceso **exclusivo de lectura (`read`, `search`)**. El subagente explora docenas de archivos y devuelve únicamente un resumen ejecutivo estructurado al agente principal, manteniendo limpia la sesión de trabajo. |
| **2. Análisis Paralelo Ortogonal (*Parallel Code Analysis*)** | Al auditar un pipeline completo antes de pase a producción. | Lanza en paralelo: (a) `data-engineer` (concurrencia/particionado/I/O), (b) `data-security-auditor` (PII/CSFLE/secretos), y (c) `pipeline-reviewer` (contratos/índices/defectos). Consolida los 3 reportes en una matriz priorizada. |
| **3. Exploración Competitiva de Soluciones (*Explore Multiple Solutions*)** | Cuando existen 2 arquitecturas viables (ej. pre-cálculo en MongoDB vs offload a DuckDB/Parquet). | Pide propuestas independientes con estimación de I/O, memoria y complejidad operativa antes de elegir el diseño ganador. |
| **4. Revisión Multi-Perspectiva de PR / Diff** | Antes de fusionar a `quality` o `production`. | Un agente revisa regresión lógica y contratos de datos (`DEFECTO`/`CONDICIONAL`), mientras otro verifica seguridad, observabilidad OTel y documentación (`docs-steward`). |
| **5. Coordinador-Trabajador (*Coordinator-Worker*)** | Para ejecutar planes multi-fase de principio a fin. | El Coordinador descompone el plan, delega un paso atómico por turno al `implementer` (con contrato claro de entrada/salida) y verifica con `validate_and_build.py` / `pytest` antes de avanzar al siguiente paso. |

## 2. Regla de Responsabilidad Única por Agente
- Nunca mezcles en un mismo prompt de subagente la tarea de **búsqueda abierta/exploración** con la tarea de **escritura/mutación masiva**. Limita el número de iteraciones de búsqueda y exige una salida estructurada.
