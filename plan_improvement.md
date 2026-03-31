Estoy analizando como podemos desplegar la funcinalidad que estamos desarrollando en este repo en otros proyectos

tengo lo siguiente, evalúa exahustivamente, propon cambios si es necesario

Perfecto. Lo que necesitas es un **sistema de empaquetado y despliegue** desde `universal-ide-agents` hacia otros proyectos, con estas reglas:

## Reglas funcionales

1. **`universal-ide-agents` es el repositorio fuente único**
   - Ahí se desarrolla todo.
   - No se desarrolla directamente en los proyectos consumidores.

2. **Lo que se distribuye a otros proyectos es el contenido de `.github/`**
   - `agents/`
   - `hooks/`
   - `instructions/`
   - `prompts/`
   - `sessions/`
   - `skills/`
   - `copilot-instructions.md`

3. **`docs/` no debe desplegarse como `docs/`**
   - Debe ir a `.github/docs/` en el proyecto consumidor.

4. **`scripts/` no debe desplegarse como `scripts/`**
   - Debe ir a `.github/scripts/` en el proyecto consumidor.
   - Así no colisiona con scripts propios del proyecto.

5. **Si el proyecto consumidor ya tiene `.github/`, se debe actualizar**
   - No duplicar.
   - Hacer overwrite/merge controlado.
   - Idealmente: reemplazar solo lo que pertenece a la funcionalidad de agentes.

---

## Recomendación de diseño

La mejor solución es crear en `universal-ide-agents` un **comando de despliegue** que haga una de estas dos cosas:

### Opción recomendada
**Sincronización por copia desde el repo fuente hacia un repo destino**, con reglas de mapeo:

```text
universal-ide-agents/.github           -> consumer/.github
universal-ide-agents/docs              -> consumer/.github/docs
universal-ide-agents/scripts           -> consumer/.github/scripts
```

y con comportamiento de **update**:
- si existe `.github/`, se actualiza
- si no existe, se crea
- si hay archivos existentes del sistema de agentes, se sobreescriben
- si hay archivos del proyecto consumidor fuera de esa superficie, no se tocan

---

## Estructura de despliegue propuesta

### En `universal-ide-agents`
Agregar algo como:

```text
scripts/
├── inject-context.sh
├── install-vscode-assets.sh
└── deploy-to-project.sh
```

### Función de `deploy-to-project.sh`
- recibe la ruta del proyecto destino o su repo
- copia:
  - `.github/*` -> `.github/*`
  - `docs/*` -> `.github/docs/*`
  - `scripts/*` -> `.github/scripts/*`
- reemplaza lo que corresponda
- preserva el resto del proyecto

---

## Comportamiento de actualización de `.github`

Si el proyecto destino ya tiene `.github/`, el despliegue debe funcionar como:

- **crear** los directorios faltantes
- **actualizar** archivos existentes del agente
- **eliminar** en destino archivos que ya no existan en fuente, solo dentro del área gestionada por agentes
- no tocar otros archivos de `.github/` si no pertenecen a esta funcionalidad

Eso te da una instalación “idempotente”.

---

## Propuesta concreta de mapeo

### Fuente
```text
.github/
docs/
scripts/
```

### Destino en proyectos consumidores
```text
.github/
.github/docs/
.github/scripts/
```

---

## Cómo encaja con tu proyecto de ciencia de datos

En un proyecto como:

```text
your-project/
├── README.md
├── src/
├── notebooks/
├── scripts/
├── tests/
├── config/
└── .github/
```

el despliegue dejaría algo así:

```text
your-project/
├── .github/
│   ├── agents/
│   ├── hooks/
│   ├── instructions/
│   ├── prompts/
│   ├── sessions/
│   ├── skills/
│   ├── copilot-instructions.md
│   ├── docs/
│   │   ├── asset-catalog.md
│   │   ├── roadmap.md
│   │   └── vscode-consumption.md
│   └── scripts/
│       ├── inject-context.sh
│       └── install-vscode-assets.sh
```

---

## Importante: los nombres “sin `_shared`”
Correcto: **no hace falta `_shared`** si lo que quieres es un despliegue final limpio dentro del proyecto consumidor.

En ese caso:
- `_shared` puede existir solo internamente en algún flujo temporal
- pero **no debe formar parte del resultado final**
- el destino final debe ser exactamente `.github/...`

---

## Recomendación para implementar

Yo lo haría así:

### En `universal-ide-agents`
1. Crear un script de despliegue.
2. Definir una convención de paths.
3. Permitir que el script haga update sobre un repositorio clonado localmente.

### En el proyecto consumidor
1. Tener el repo clonado.
2. Ejecutar el despliegue.
3. Commit de los cambios generados.

---

## Si quieres, el siguiente paso correcto es este
Puedo prepararte **el diseño exacto del script `deploy-to-project.sh`** para `universal-ide-agents`, con estas capacidades:

- despliegue a un repo destino local
- mapeo de:
  - `.github -> .github`
  - `docs -> .github/docs`
  - `scripts -> .github/scripts`
- actualización si `.github` ya existe
- modo `--dry-run`
- modo `--clean`
- detección de conflictos



Modo de despliegue en otros proyectos, propuesto

Desde un proyecto consumidor, lo ideal es **sincronizar** desde `universal-ide-agents` mediante un script de actualización, no editar nada a mano.

## Flujo recomendado

1. El proyecto consumidor tiene `universal-ide-agents` agregado como **submodule** o como repositorio auxiliar.
2. Ejecutas un comando de sync que:
   - trae el último `main` del repo fuente
   - copia `.github/` al proyecto
   - copia `docs/` a `.github/docs/`
   - copia `scripts/` a `.github/scripts/`
   - sobrescribe lo que corresponda dentro del área gestionada por agentes

---

## Caso práctico con submodule

### 1) Tener el submodule en el proyecto
Por ejemplo en `.agents-src`:

```bash
git submodule add -b main https://github.com/Sebastian93BC/universal-ide-agents .agents-src
git commit -m "Add universal-ide-agents submodule"
```

### 2) Actualizar el submodule al último `main`
Cuando quieras traer cambios:

```bash
git submodule update --remote --merge
```

o si quieres hacerlo explícitamente:

```bash
cd .agents-src
git checkout main
git pull origin main
cd ..
```

### 3) Desplegar al `.github/` del proyecto
Luego ejecutas el script de despliegue:

```bash
./.agents-src/scripts/deploy-to-project.sh .
```

Eso hace que el contenido actualizado de `universal-ide-agents` se copie al proyecto actual.

---

## Si quieres una sola orden
Puedes encapsular todo en un script del proyecto consumidor, por ejemplo:

```bash
./scripts/update-agents.sh
```

y que internamente haga:

```bash
git -C .agents-src pull origin main
bash .agents-src/scripts/deploy-to-project.sh .
```

---

## Qué se actualiza exactamente
Con ese flujo, se actualiza:

- `.github/agents/`
- `.github/hooks/`
- `.github/instructions/`
- `.github/prompts/`
- `.github/sessions/`
- `.github/skills/`
- `.github/copilot-instructions.md`
- `.github/docs/`
- `.github/scripts/`

---

## Qué no se toca
No se deberían tocar:
- `src/`
- `notebooks/`
- `data/`
- `config/`
- `README.md`
- `pyproject.toml`
- otros scripts propios del proyecto, salvo que tú lo decidas

---

## Mi recomendación exacta
Para tu caso:

- **submodule** para mantener independencia del repo fuente
- **script de despliegue** para publicar actualizaciones al proyecto consumidor
- **un script wrapper** en el proyecto consumidor para simplificar el update

### Ejemplo de actualización
```bash
git submodule update --remote --merge
./.agents-src/scripts/deploy-to-project.sh .
git add .github .gitmodules .agents-src
git commit -m "Sync agents updates"
```

