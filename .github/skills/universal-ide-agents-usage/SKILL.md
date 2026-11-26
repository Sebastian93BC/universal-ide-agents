---
name: universal-ide-agents-usage
description: Cómo usar, desplegar, verificar y actualizar la capa universal-ide-agents instalada como submódulo en este proyecto. Úsala cuando el usuario pida instalar, cambiar de perfil, actualizar, verificar o quitar la capa, o cuando un despliegue falle con conflicto.
---

# Uso de la capa universal-ide-agents en este proyecto

## Cuándo activarla
- El usuario pide instalar, actualizar, desplegar o quitar la capa de agentes.
- Pide cambiar de perfil o usar varios perfiles.
- Un despliegue sale con conflicto (código 2) o con cambio en un archivo raíz (código 3).
- Pide verificar la instalación.

## Qué hay en el proyecto
- `.modules/universal-ide-agents/`: el repositorio completo, como submódulo. Es la fuente; no se edita desde aquí.
- `.agents/`, `.claude/` y `.github/`: lo que el despliegue copió según el perfil. Se regeneran en cada despliegue; los cambios manuales se pierden o generan conflicto.
- `.agents/universal-ide-agents.json`: el manifiesto. Dice qué perfil se desplegó, qué versión y qué archivos son de la capa.
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`: son del proyecto. El despliegue no los toca nunca.

## Comandos
- Previsualizar: `.modules/universal-ide-agents/scripts/deploy-to-project.sh --dry-run --profile <perfil> .`
- Desplegar: `.modules/universal-ide-agents/scripts/deploy-to-project.sh --profile <perfil> .`
- Verificar: `python3 .modules/universal-ide-agents/scripts/check.py --project .`
- Actualizar: `git submodule update --remote .modules/universal-ide-agents`, después desplegar y verificar.

Siempre ejecuta `--dry-run` antes de un despliegue que cambie de perfil, porque lo que no pertenezca al nuevo perfil se borra.

## Perfiles
- `core`, `data-eng-base` (por defecto), `data-eng-n8n`, `data-eng-dagster-duckdb`, `data-eng-lakehouse`, `data-eng-full`.
- Se combinan con comas: `--profile data-eng-n8n,data-eng-dagster-duckdb`.
- Cada perfil de herramienta extiende `data-eng-base`. La lista completa y su contenido están en `.modules/universal-ide-agents/profiles/` y en `docs/usage-guide.md` del submódulo.

## Qué no hacer
- No edites archivos dentro de `.agents/`, `.claude/` o `.github/` que vengan de la capa. Si hace falta un cambio, propónlo en el repositorio del submódulo.
- No hagas commit del submódulo ni del despliegue sin que lo pida el usuario. El despliegue no hace commits; el puntero del submódulo lo confirma el usuario.
- No uses `--force` sin preguntar: sobrescribe archivos que pueden ser del proyecto o ediciones del usuario.

## Qué hacer ante un conflicto
1. Lee el mensaje: indica el archivo y si es ajeno a la capa o editado localmente.
2. Si es ajeno, pregunta al usuario si puede renombrarlo. No lo borres por tu cuenta.
3. Si es una edición local de un archivo de la capa, pregunta si la quiere conservar. Si la conserva, deja el archivo como está y explícale que el próximo despliegue volverá a marcarlo.
4. Solo con confirmación explícita, usa `--force`.

## Verificación
Si `check.py --project` avisa de que `AGENTS.md`, `CLAUDE.md` o `GEMINI.md` cambiaron, no es un error: la plantilla los actualiza o el usuario edita su capa. No vuelvas a desplegar por ese aviso ni cambies esos archivos.
