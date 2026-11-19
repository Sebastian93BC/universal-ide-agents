---
name: skill-creator
description: Estándar de diseño y creación de nuevas skills modulares (SKILL.md + references/ + scripts/) compatibles simultáneamente con Antigravity (.agents/skills/), Claude Code (.claude/skills/) y VS Code GitHub Copilot (.github/skills/).
---

# Multi-IDE Skill Creator Standard

## Cuándo Activar esta Skill
- Al crear una nueva skill desde cero o convertir un prompt/documento plano en una skill modular dentro de `core/skills/<categoria>/<skill-name>/SKILL.md`.

## 1. Requisitos de Compatibilidad Multi-IDE (`Antigravity + Claude Code + VS Code`)

1. **Estructura de Directorio**:
   ```text
   core/skills/<categoria>/<skill-name>/
   ├── SKILL.md           # Instrucciones principales (<= 12,000 caracteres)
   ├── references/        # Documentación extendida o ejemplos largos (opcional)
   └── scripts/           # Scripts utilitarios deterministas en Python/Bash/JS (opcional)
   ```
2. **YAML Frontmatter Obligatorio**:
   ```yaml
   ---
   name: <skill-name-en-kebab-case>
   description: <Descripción rica en palabras clave de activación (120 a 300 caracteres) que indique QUÉ hace y CUÁNDO activarla.>
   ---
   ```
   - `name` debe coincidir exactamente con el nombre de la carpeta contenedora.
   - `description` es el único campo que los 3 IDEs cargan inicialmente en el prompt de descubrimiento (*Progressive Disclosure*). Incluye siempre los nombres de las tecnologías y los síntomas/tareas que disparan la skill.
3. **Presupuesto de Contexto (`<= 12,000` caracteres)**:
   - Antigravity impone un límite estricto de `12,000` caracteres por archivo de instrucción/skill. Mantén `SKILL.md` directo, accionable y centrado en tablas de decisión, invariantes y bloques de código canónicos.
4. **Higiene y Diagramación**:
   - Cero nombres de clientes reales, cero rutas locales de usuario y cero bloques de diagrama `mermaid` (usa SVG o tablas Markdown).
