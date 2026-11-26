---
name: gitlab-ssh-access
description: Configurar acceso por SSH a GitLab desde macOS con una llave dedicada, su archivo de configuración y la verificación. Úsala cuando el usuario no pueda clonar, hacer push o pull por SSH, o pida crear o cambiar su llave de GitLab.
---

# Acceso SSH a GitLab

## Cuándo usarla
- `git clone`, `push` o `pull` piden contraseña o fallan con `Permission denied (publickey)`.
- El usuario quiere una llave exclusiva para GitLab, separada de otras.
- Hay varias cuentas o instancias de GitLab en la misma máquina.

Si el repositorio se clona por HTTPS, no hace falta SSH. Para submódulos públicos, HTTPS funciona sin llave.

## Regla de seguridad
Nunca imprimas la llave **privada** (`~/.ssh/id_ed25519_gitlab` sin `.pub`). Solo se muestra la pública (`.pub`) y solo cuando hay que pegarla en GitLab. Si la privada aparece en una conversación, se considera comprometida: hay que generar otra y revocar la anterior.

## Paso 1: generar una llave dedicada
```bash
ssh-keygen -t ed25519 -C "<correo de la cuenta de GitLab>" -f ~/.ssh/id_ed25519_gitlab
```
- `ed25519` es el algoritmo recomendado.
- `-f` da un nombre propio y evita sobrescribir la llave por defecto.
- La frase de paso es opcional. Si la pones, el llavero de macOS puede recordarla (paso 4).

## Paso 2: configurar el cliente SSH
Añade a `~/.ssh/config`:

```text
Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/id_ed25519_gitlab
    IdentitiesOnly yes
```

- `IdentitiesOnly yes` evita que SSH pruebe otras llaves y entre con la cuenta equivocada.
- Si la instancia es de una empresa, cambia `gitlab.com` (en las dos líneas `Host` y `HostName`) por su dominio.
- Para varias cuentas, un bloque `Host` por cuenta, cada uno con su `IdentityFile`.

## Paso 3: subir la llave pública a GitLab
```bash
pbcopy < ~/.ssh/id_ed25519_gitlab.pub
```
En GitLab: avatar, **Edit profile** (o **Preferences**), **SSH Keys**, **Add new key**, pegar y **Add key**. Pon un título que identifique el equipo.

Fuera de macOS, `pbcopy` no existe; usa `cat ~/.ssh/id_ed25519_gitlab.pub` y copia la salida.

## Paso 4: recordar la frase de paso (solo macOS)
Si pusiste frase de paso y GitLab sigue pidiendo contraseña:
```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519_gitlab
```

## Paso 5: verificar
```bash
ssh -T git@gitlab.com
```
La primera vez pregunta si confías en el servidor: responde `yes`. La respuesta correcta es un saludo de bienvenida con el usuario de la cuenta. Ese saludo no significa que el acceso al repositorio esté autorizado; para eso, prueba `git ls-remote <url>` sobre el repositorio concreto.

## Errores frecuentes
| Síntoma | Causa probable | Qué hacer |
| :--- | :--- | :--- |
| `Permission denied (publickey)` | La llave pública no está en GitLab, o se usa otra llave. | Repite el paso 3 y revisa `IdentityFile`. |
| Pide contraseña del usuario | SSH no usa la llave. | Revisa `IdentitiesOnly` y el bloque `Host`. |
| `Host key verification failed` | El servidor cambió o es la primera vez. | Si es la primera, acepta. Si no, verifica la huella con el administrador antes de seguir. |
| Funciona en un repo y no en otro | Ese repositorio usa otra URL, otra instancia o HTTPS. | Revisa `git remote -v`. |
