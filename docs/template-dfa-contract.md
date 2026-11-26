# Contrato con `template-data-flow-automation`

Este documento dice qué da `universal-ide-agents` a los proyectos que genera la plantilla y qué espera de ella y de su CLI `dfa`. Es la parte que la plantilla puede dar por fija; lo que todavía es provisional está marcado.

## 1. Las tres capas y de quién es cada archivo

El `AGENTS.md` del proyecto tiene la capa de la plantilla y la del cliente; la plantilla ya menciona en su capa que existe esta capa genérica. **Este repositorio no escribe en `AGENTS.md`, `CLAUDE.md` ni `GEMINI.md`.** Su capa vive en archivos propios bajo `.agents/`, `.claude/` y `.github/`, que los IDE cargan solos.

| Archivo o carpeta del proyecto | Dueño |
| :--- | :--- |
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.claude/settings.json` | La plantilla (y el cliente en su sección de `AGENTS.md`). |
| Lo listado en `.agents/universal-ide-agents.json` | Este repositorio, a través del despliegue. |
| Cualquier otro archivo bajo `.agents/`, `.claude/`, `.github/` | El proyecto. El despliegue no lo toca. Si choca con uno suyo, se detiene. |

## 2. Inclusión

La URL del submódulo es HTTPS. El repositorio es público y el clon anónimo funciona (comprobado el 2026-11-25), así que no hace falta llave:

```bash
git submodule add https://github.com/Sebastian93BC/universal-ide-agents.git .modules/universal-ide-agents
```

Para actualizar: `git submodule update --remote .modules/universal-ide-agents` y volver a desplegar.

### 2.1 Quien prefiere SSH

La URL en `.gitmodules` se queda en HTTPS, para que el proyecto no dependa de la forma de autenticarse de cada máquina. Cada máquina que clone o actualice el submódulo puede pedir a git que use SSH para GitHub:

```bash
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

Esto reescribe todas las URL de GitHub por SSH en esa máquina. Si prefieres limitarlo a una organización, usa el patrón completo:

```bash
git config --global url."git@github.com:Sebastian93BC/".insteadOf "https://github.com/Sebastian93BC/"
```

### 2.2 Repositorios privados: deploy keys de solo lectura

Si el submódulo o el proyecto que lo contiene es privado, no uses la llave personal del usuario. Usa una **deploy key**, que GitHub asocia a un solo repositorio:

1. Genera una llave dedicada para ese repositorio, sin frase de paso si la va a usar un proceso automático: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_deploy_<repo> -C "deploy <repo>"`.
2. En el repositorio, **Settings → Deploy keys → Add deploy key**, pega la parte `.pub`. Deja **sin marcar** *Allow write access*: la llave solo lee.
3. Como una llave no sirve para varios repositorios, asigna un alias en `~/.ssh/config` para que git use esa llave y no la predeterminada:

```text
Host github.com-<repo>
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_deploy_<repo>
    IdentitiesOnly yes
```

4. Reescribe la URL solo para ese repositorio:

```bash
git config --global url."git@github.com-<repo>:Sebastian93BC/<repo>.git".insteadOf "https://github.com/Sebastian93BC/<repo>.git"
```

Con esto, la URL del submódulo sigue en HTTPS y git la traduce a SSH con la llave de solo lectura. Así un proceso automático nunca tiene la llave personal del usuario.

## 3. Despliegue

```bash
.modules/universal-ide-agents/scripts/deploy-to-project.sh --profile data-eng-n8n .
```

- **Perfiles.** `data-eng-base` es el núcleo, MongoDB y el modelado, sin herramienta de ETL. Cada herramienta es un perfil que lo extiende: `data-eng-n8n` y `data-eng-dagster-duckdb`. Si un proyecto tiene módulos en las dos, se combinan: `--profile data-eng-n8n,data-eng-dagster-duckdb`. Solo llega lo que piden los perfiles.
- **Qué escribe.** Solo bajo `.agents/`, `.claude/` y `.github/`: agentes, skills, reglas, el guardián `.claude/hooks/universal-ide-agents-guard.py`, los ejemplos MCP filtrados por perfil y el manifiesto. No crea `plans/` ni toca la raíz.
- **Idempotente.** Con la misma fuente y los mismos perfiles, volver a desplegar no cambia ningún byte, tampoco la fecha del manifiesto.
- **Limpieza.** Borra lo que desplegó antes y ya no toca, por ejemplo al cambiar de perfil. Conserva y avisa si alguien lo editó.
- **Conflictos.** Si un archivo destino existe y no es suyo, o lo editó alguien, no escribe nada y sale con código 2. `--force` sobrescribe.
- **Códigos de salida.** `0` bien; `1` error de uso o de perfil; `2` conflicto; `3` cambió un archivo raíz durante el despliegue, lo que no debe ocurrir nunca.
- `--dry-run` muestra el plan sin escribir.

### El manifiesto `.agents/universal-ide-agents.json`

```json
{
  "schemaVersion": "1.0.0",
  "source": "universal-ide-agents",
  "sourceUrl": "https://github.com/Sebastian93BC/universal-ide-agents",
  "version": "3.0.0",
  "profiles": ["data-eng-n8n"],
  "resolvedProfiles": ["core", "data-eng-base", "data-eng-n8n"],
  "targets": ["antigravity", "claude", "vscode"],
  "deployedAt": "2026-11-25",
  "rootFiles": {"AGENTS.md": "sha256:…", "CLAUDE.md": "sha256:…", "GEMINI.md": "sha256:…"},
  "files": {".claude/rules/three-level-limits.md": "sha256:…"}
}
```

`rootFiles` guarda la huella de los tres archivos raíz en el momento del despliegue, para que el verificador compruebe que no cambiaron. `files` es lo que es de este repositorio.

## 4. Verificación (para `dfa doctor`)

```bash
python3 .modules/universal-ide-agents/scripts/check.py --project .
```

Comprueba que el manifiesto existe y está completo, que cada archivo desplegado está y no se editó (si se editó, avisa), que `CLAUDE.md` y `GEMINI.md` son punteros de una línea, el tope de líneas de `AGENTS.md`, que cada skill tiene su `name` igual a su carpeta y que no hay copias de conflicto (`SKILL 2.md`). Sale con 1 si algo falla.

Los cambios en `AGENTS.md`, `CLAUDE.md` o `GEMINI.md` desde el último despliegue **no son un fallo**: la plantilla los actualiza con `copier update` y el cliente edita su capa. El verificador lo muestra como aviso informativo. Solo el propio despliegue debe no tocar esos archivos, y eso lo garantiza con su código de salida 3, no el verificador.

## 5. El guardián de límites

La regla `three-level-limits` tiene siete límites y cada uno se comprueba en `.claude/hooks/universal-ide-agents-guard.py`. El despliegue deja el script, pero conectarlo es cosa de `.claude/settings.json`, que es de la plantilla:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Read|Grep|Glob|Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [
          {"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/universal-ide-agents-guard.py"}
        ]
      }
    ]
  }
}
```

El guardián es una segunda capa, no una frontera: la frontera es que el agente no tenga el secreto (modelo "usar sin leer", decisión T30 de la plantilla).

## 6. Cierre de tarea: `knowledge-harvester cierre-tarea`

Al cerrar una tarea, `dfa task close` invoca al agente `knowledge-harvester` con este mensaje. Las tres rutas van siempre por argumento porque la estructura de la tarea (decisión A5) es provisional: el agente no supone ningún nombre.

```text
knowledge-harvester cierre-tarea
  --tarea <carpeta de la tarea>
  --conocimiento-tarea <archivo de conocimiento de la tarea>
  --conocimiento-proyecto <archivo de conocimiento del proyecto>
```

**Qué hace `dfa` antes:** comprueba que la tarea puede cerrarse, con sus propias reglas, y que el archivo de conocimiento de la tarea tiene contenido o dice explícitamente "nada nuevo".

**Qué hace el agente:** lee el conocimiento de la tarea y lo consolida en el del proyecto con `CREATE` / `UPDATE` / `INVALIDATE`, una idea por entrada y su origen `(origen: <tarea>, AAAA-MM-DD)`. Escribe **solo** en `--conocimiento-proyecto`, y lo crea si no existe. No hace commits ni copia secretos. El procedimiento completo está en `core/agents/core/knowledge-harvester.agent.md`, sección 1.

**Qué devuelve.** Termina siempre con este bloque, que `dfa` lee:

```text
RESULTADO: consolidado | nada-nuevo | error
CAMBIOS: <n> (CREATE <a>, UPDATE <b>, INVALIDATE <c>)
CANDIDATOS-HUB: <k>
DETALLE:
- <clase> · <CREATE|UPDATE|INVALIDATE> · <resumen de una línea>
```

**Qué hace `dfa` después:** con `RESULTADO: error` no cierra la tarea; con `consolidado` o `nada-nuevo`, deja la entrada en `plans/` y sigue. Los `CANDIDATOS-HUB` son aprendizajes genéricos que la cosecha periódica de este repositorio puede llevar a `core/`.

**Por decidir en la plantilla (paso 3, `dfa task close`):** cómo lanza `dfa` al agente en cada IDE (Claude Code o Antigravity sin interfaz) y dónde vive el archivo de conocimiento del proyecto. Este contrato fija solo el mensaje y la respuesta.

## 7. Nota de traspaso

La skill `session-handoff` deja al final de la sesión, en el archivo de estado de la tarea, dónde quedó el trabajo y qué se decidió. Para no suponer nombres, usa el archivo que designe la capa de la plantilla en `AGENTS.md`; si no hay ninguno designado, pregunta. **Pendiente en la plantilla:** escribir en su capa cuál es ese archivo (hoy sería el `plan.md` de la tarea).

## 8. Lo que la plantilla tiene que hacer

1. Incluir el submódulo por HTTPS en `.modules/universal-ide-agents` (sección 2).
2. Conectar el guardián en su `.claude/settings.json` (sección 5).
   - Si el equipo o un proceso automático clona por SSH, aplicar la sección 2.1 o 2.2 en esa máquina.
3. En `dfa task close`, invocar `knowledge-harvester cierre-tarea` con las tres rutas y leer el bloque de respuesta (sección 6).
4. En `dfa doctor`, llamar a `check.py --project` (sección 4).
5. Designar en su capa de `AGENTS.md` el archivo de estado de la tarea para la nota de traspaso (sección 7).
7. Si genera `docs/standards/mongodb-query-optimization.md`, la skill `mongodb-query-optimizer` ya le remite a ese documento (sección 0). Confirmar que el estándar y la skill no se contradicen antes de publicarlo; hoy el estándar no existe en ningún repositorio.
6. Su capa de `AGENTS.md` repite hoy los límites. Que digan lo mismo que la regla `three-level-limits`; si una cambia, cambiar la otra.
