#!/usr/bin/env sh
# scaffold-experimental-module.sh — Scaffold a new experimental module following the notebook methodology.

set -eu

if [ "$#" -lt 1 ]; then
  printf 'Usage: %s <module_name> [parent_directory]\n' "$0" >&2
  exit 1
fi

module_name="$1"
parent_dir="${2:-.}"

module_path="$parent_dir/$module_name"

if [ -d "$module_path" ]; then
  printf 'Error: directory already exists at: %s\n' "$module_path" >&2
  exit 1
fi

printf 'Scaffolding experimental module "%s" at: %s\n' "$module_name" "$module_path"

mkdir -p "$module_path/versiones"
mkdir -p "$module_path/soporte/debug_visual"

# Create notes.md template
cat > "$module_path/notes.md" <<EOF
# Bitácora de Desarrollo — $module_name

## Decisiones de Diseño e Ideas
- *Anota aquí los debates de arquitectura y parámetros evaluados.*

## Versiones y Descarte
- **v1**: Enfoque inicial.
- **v2**: ...

## Siguientes Pasos
- [ ] Implementar extracción de lógica a versiones/
- [ ] Diseñar script de diagnóstico en lote
EOF

# Create informe_*.md template
cat > "$module_path/informe_$module_name.md" <<EOF
# Informe Técnico — $module_name

## 1. Objetivo del Módulo
*Explicación clara de lo que resuelve este pipeline.*

## 2. Arquitectura del Pipeline Actual
*Esquema o flujo de procesamiento de la última versión estable.*

## 3. Matriz de Evaluación Comparativa

| Versión | Tasa de Éxito | Tiempo Promedio | Notas de Rendimiento |
| :--- | :--- | :--- | :--- |
| **v1** | 0.0% | - | Línea base |

## 4. API Pública
\`\`\`python
# Interfaz expuesta del módulo estable
def process_data(data, config=None):
    pass
\`\`\`

## 5. Limitaciones Conocidas y Casos Extremos
- *Lista de errores conocidos y casos donde el algoritmo falla.*
EOF

# Create a skeleton for diagnostico_v1.py
cat > "$module_path/diagnostico_v1.py" <<EOF
#!/usr/bin/env python3
"""
diagnostico_v1.py — Script de evaluación en lote para el módulo $module_name.
"""

import sys
import os

def run_diagnostics():
    print("Iniciando evaluación en lote para: $module_name")
    # 1. Leer dataset de validación local
    # 2. Ejecutar lógica de versiones/
    # 3. Calcular métricas cuantitativas
    # 4. Exportar reportes y cuadrícula visual
    print("Diagnóstico completado exitosamente.")

if __name__ == "__main__":
    run_diagnostics()
EOF

chmod +x "$module_path/diagnostico_v1.py"

# Create a simple .ipynb template
cat > "$module_path/$module_name.ipynb" <<EOF
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Notebook de Exploración — $module_name\\n",
    "\\n",
    "Utiliza este notebook para explorar de forma interactiva e inspeccionar resultados visuales. La lógica madura debe extraerse al directorio \`versiones/\`."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Carga de librerías y configuración\\n",
    "print(\"Exploración interactiva activa\")"
   ]
  }
 ],
 "metadata": {
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
EOF

printf 'Scaffolding completed successfully!\n'
printf 'Folders created:\n'
printf '  - %s/versiones/\n' "$module_path"
printf '  - %s/soporte/debug_visual/\n' "$module_path"
printf 'Files initialized:\n'
printf '  - %s/notes.md\n' "$module_path"
printf '  - %s/informe_%s.md\n' "$module_path" "$module_name"
printf '  - %s/diagnostico_v1.py\n' "$module_path"
printf '  - %s/%s.ipynb\n' "$module_path" "$module_name"
