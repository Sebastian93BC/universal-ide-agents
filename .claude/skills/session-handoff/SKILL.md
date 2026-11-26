---
name: session-handoff
description: Nota de traspaso al cerrar una sesión de trabajo. Úsala antes de terminar una sesión con trabajo a medias, antes de compactar el contexto, al cambiar de IDE (Claude Code, Antigravity, Copilot) o cuando el usuario diga que lo deja por hoy. Deja en la tarea un párrafo de dónde quedó el trabajo y qué se decidió, para la siguiente sesión o el otro IDE.
---

# Nota de traspaso entre sesiones e IDE

La memoria de un IDE no la ve el otro, y la compactación del contexto pierde decisiones. Por eso el estado de una tarea se escribe **en la tarea**, no en la memoria del agente. Ya pasó una vez: un IDE reintrodujo decisiones rechazadas que solo estaban en la memoria del otro.

## Cuándo

- Antes de terminar una sesión en la que la tarea no quedó cerrada.
- Antes de compactar el contexto o cuando la conversación ya es larga.
- Antes de pasar la tarea a otro IDE o a otra persona.

Si la tarea se cerró en esta sesión, no hace falta nota: el cierre ya deja el registro.

## Dónde

En el archivo de estado de la tarea activa: el que designe la capa de la plantilla o del proyecto en `AGENTS.md` (en los proyectos de `template-data-flow-automation`, el plan de la tarea). Si `AGENTS.md` no designa ninguno, pregunta una vez dónde va y usa esa respuesta. No crees archivos nuevos para la nota ni la dejes en la memoria del IDE.

## Formato

Una sección al final del archivo, la más reciente arriba dentro de ella:

```markdown
## Traspaso

### AAAA-MM-DD · <IDE>
Dónde quedó: <qué está hecho y verificado, qué está a medias y en qué archivo>.
Decidido: <decisiones tomadas en la sesión, con quién y por qué; incluye lo rechazado>.
Siguiente paso: <la próxima acción concreta y cómo se comprueba>.
Abierto: <preguntas sin responder, o "nada">.
```

## Reglas

1. **Un párrafo por campo, sin relleno.** Lo que no cambió no se repite.
2. **Lo rechazado también se escribe.** Es lo que el otro IDE no puede adivinar.
3. **Solo hechos comprobados.** Lo que no verificaste se marca como `[INFERIDO]`.
4. **Sin secretos.** Ni valores de `.env`, ni tokens, ni cadenas de conexión.
5. **Al empezar una sesión**, lee la última nota de traspaso de la tarea antes de proponer nada.
