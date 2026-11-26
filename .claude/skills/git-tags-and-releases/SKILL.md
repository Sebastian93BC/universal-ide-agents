---
name: git-tags-and-releases
description: Cómo marcar versiones con tags de git, publicarlas en el remoto, borrarlas y usar el versionado semántico. Úsala cuando el usuario pida crear una release, etiquetar una versión, enviar o borrar un tag, o elegir un número de versión.
---

# Tags de git y releases

## Qué es un tag
Un tag es una etiqueta que apunta a un commit concreto. A diferencia de una rama, no avanza: siempre señala el mismo commit. Por eso sirve para marcar releases.

```
Rama:  A → B → C → D → E   (avanza con cada commit)
Tag:   A → B → C           (fijo en C)
```

## Crear
- Tag anotado, el recomendado para releases (guarda autor, fecha y mensaje):
  `git tag -a v1.2.0 -m "Versión 1.2.0"`
- Tag ligero, solo una referencia: `git tag v1.2.0`

Crea el tag sobre el commit que corresponde. Si no pasas commit, es el `HEAD` actual.

## Ver
- `git tag` lista los locales.
- `git show v1.2.0` muestra el tag y el commit al que apunta.
- `git ls-remote --tags origin` lista los del remoto.

## Enviar al remoto
- `git push origin v1.2.0` envía un tag concreto.
- `git push origin --tags` envía todos los locales.
- **`git push` no envía tags por defecto.** Si no los envías, el remoto no los tiene.

## Borrar
- Local: `git tag -d v1.2.0`
- Remoto: `git push origin --delete v1.2.0`

Borrar un tag ya publicado puede romper a quien dependa de él. Confirma con el usuario antes de hacerlo en el remoto.

## Flujo de una release
1. Estar en la rama de integración y al día: `git pull`.
2. Crear el tag anotado sobre ese commit.
3. Enviar la rama con sus commits pendientes: `git push origin <rama>`.
4. Enviar el tag: `git push origin v1.2.0`.
5. Comprobar que llegó: `git ls-remote --tags origin | grep v1.2.0`.

Haz el push de la rama antes que el del tag, para que el tag no apunte a un commit que el remoto no tiene.

## Versionado semántico
Formato `MAJOR.MINOR.PATCH`:
- **MAJOR**: cambios incompatibles para quien usa el proyecto.
- **MINOR**: funciones nuevas compatibles con las anteriores.
- **PATCH**: correcciones sin cambios de interfaz.

Ejemplos: `1.4.2` a `1.4.3` es una corrección; `1.4.3` a `1.5.0` añade algo sin romper nada; `1.5.0` a `2.0.0` rompe compatibilidad.

## CI con tags (GitLab)
Si el proyecto usa GitLab CI, es habitual que la construcción de la imagen o el paquete solo corra con tag:

```yaml
build:
  rules:
    - if: $CI_COMMIT_TAG
```

Así un push normal ejecuta solo lint y pruebas, y un tag además construye. Dentro del script, `$CI_COMMIT_TAG` tiene el nombre del tag. Comprueba la regla en el `.gitlab-ci.yml` del proyecto antes de asumirla.

## Qué no hacer
- No muevas un tag ya publicado para "corregirlo". Crea una versión nueva.
- No pongas en el mensaje del tag datos del cliente o credenciales.
