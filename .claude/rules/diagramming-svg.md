---
name: diagramming-svg
description: Prohibición estricta de diagramas Mermaid en toda documentación y artefactos; uso obligatorio de SVG independientes o tablas Markdown.
trigger: always_on
applyTo: "**/*.md"
---

# Regla Global de Diagramación: Prohibición Estricta de Mermaid

- **PROHIBIDO generar bloques de código con lenguaje `mermaid`** bajo cualquier circunstancia en documentación técnica, archivos Markdown o artefactos.
- El visor integrado de Markdown en Antigravity IDE bloquea la ejecución de scripts para Mermaid, mostrando bloques de código crudo en lugar de gráficos.
- **Estándar Obligatorio para Diagramas**:
  1. Generar archivos **SVG autónomos** (`.svg`) en `docs/img/` o `assets/`.
  2. Incrustar el SVG en Markdown con sintaxis estándar de imagen: `![Descripción del Diagrama](./ruta/al/diagrama.svg)`.
  3. Para relaciones textuales o matrices de decisión, usar **tablas nativas de GitHub Flavored Markdown** o jerarquías estructuradas de viñetas.
