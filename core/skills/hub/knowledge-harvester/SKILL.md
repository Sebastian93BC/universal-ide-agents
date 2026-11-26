---
name: knowledge-harvester
description: Procedimiento operativo del motor periódico Knowledge & Skill Harvester: ejecución de scripts/harvest.py, análisis de deltas SHA-256, algoritmo de consolidación de memoria procedural (CREATE/UPDATE/INVALIDATE), sanitización anti-cliente y compilación multi-IDE con validate_and_build.py.
---

# Knowledge & Skill Harvester — Guía Operativa de Recopilación Periódica

## Cuándo Activar esta Skill
- Cada vez que el usuario pida **"escanear los proyectos en busca de nuevos conocimientos, skills o agentes"**, ejecutar una cosecha periódica (*harvest*) o promover un aprendizaje de un proyecto/curso hacia `universal-ide-agents`.

## 1. Flujo de Trabajo Paso a Paso

### Paso 1: Ejecutar el Escáner Incremental (`scripts/harvest.py`)
```bash
python3 scripts/harvest.py
```
- El script lee `harvester/sources.local.json` (o `harvester/sources.example.json` si no existe el local), calcula hashes SHA-256 de todos los activos de agentes, skills, reglas, memorias (`~/.claude/projects/*/memory/`, `~/.gemini/antigravity-ide/knowledge/`), post-mortems (`fallos/`) y notas de cursos.
- Compara contra `harvester/state.local.json` y genera un reporte incremental en `harvester/inbox/<YYYY-MM-DD>/harvest_report.md` listando archivos **`NEW`** y **`MODIFIED`**, junto con alertas de términos sensibles detectados.

### Paso 2: Aplicar el Algoritmo ETL de Consolidación de Memoria Procedural
Para cada archivo nuevo o modificado del reporte:
1. **Filtrado de Significancia**:
   - ¿Es un patrón técnico extrapolable a otros proyectos (invariante de motor de datos, patrón de modelado, guardrail de pipeline, configuración MCP, flujo de revisión)? Si es lógica comercial exclusiva de un cliente, descártalo.
2. **Sanitización Obligatoria (Regla Cero Fugas)**:
   - Elimina todo rastro de nombres de clientes definidos en `harvester/schema/sanitization_rules.json`, rutas absolutas de usuario, credenciales e IPs.
3. **Decisión de Consolidación (`CREATE` / `UPDATE` / `INVALIDATE`)**:
   - **`UPDATE`**: Si ya existe una skill del tema en `core/skills/`, integra el nuevo hallazgo o caso de borde dentro de esa skill cuidando que `SKILL.md` no supere `12,000` caracteres (extrae anexos largos a `references/`).
   - **`CREATE`**: Si es un dominio nuevo, crea `core/skills/<categoria>/<nombre-kebab>/SKILL.md` y agrégala al perfil correspondiente en `profiles/`.
   - **`INVALIDATE`**: Si el hallazgo corrige una suposición previa errónea, actualiza la regla anterior explicando el nuevo invariante verificado.

### Paso 3: Validar, Compilar y Actualizar el Estado
```bash
python3 scripts/validate_and_build.py
python3 scripts/harvest.py --mark-processed
```
- `validate_and_build.py` verifica que no exista ningún término prohibido de cliente, valida el YAML frontmatter, comprueba el límite de `12,000` caracteres y sincroniza automáticamente `.agents/`, `.claude/` y `.github/`.
- `--mark-processed` actualiza `harvester/state.local.json` para que la próxima corrida periódica solo reporte deltas futuros.
