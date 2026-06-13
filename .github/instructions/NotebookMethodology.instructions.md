---
applyTo: "**/*.ipynb"
description: Rules for Jupyter Notebook development, code extraction, and Git versioning.
---

# Notebook Development & Git Versioning Rules

Whenever you work with Jupyter Notebooks (`.ipynb`) or code folders inside exploration/notebooks, you must enforce the following methodology:

## 1. Directory Structure
Every experimental module must follow this structure:
```text
nombre_modulo/
├── versiones/                          # Clean python snapshots (.py)
│   ├── modulo_v1.py
│   └── ...
├── soporte/                            # Auxiliary parameter calibration or debug scripts
│   ├── calibrate_params.py
│   └── debug_visual/                   # Visual output dumps (images, logs)
├── diagnostico_vX.py                   # CLI script to evaluate version performance in batch
├── nombre_modulo.ipynb                 # Interactive orchestration notebook
├── notes.md                            # Development log / Design discussions
└── informe_nombre_modulo.md            # Technical report and version comparison tables
```

## 2. Code Extraction Rule
- **Extraction**: Do not accumulate complex, business-critical logic in notebook cells. Once logic is functional, immediately extract it to `versiones/modulo_vX.py` as structured, modular functions.
- **Config**: Group hyperparameters inside a configuration class or dataclass to support easy parameter sweeps or calibrators.

## 3. Batch Diagnosis
- Every algorithm version must be validated against a representative local validation dataset (found in `data/` or a local sample folder) using a `diagnostico_vX.py` script.
- The diagnosis script must output quantitative performance metrics (accuracy, error rate, execution times) and generate visual side-by-side grids comparing input, processing steps, and outputs to spot anomalies quickly.

## 4. Git Hygiene
- **Never commit large binaries inside notebooks**. Before committing, you must strip all cell outputs from the `.ipynb` file.
- Use `scripts/clean-notebook-outputs.py` or `nbstripout` to ensure only code cells are committed, ensuring readable Git diffs.
