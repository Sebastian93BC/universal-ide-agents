## Plan: Agent Layer Evolution (v0.2.0 batch)

Hay siete frentes en el backlog. Los agrupo en fases por dependencia real. La recomendación general es **el camino más simple en cada decisión bifurcada**: una sola mejora por archivo, sin crear capas extra donde no hay beneficio demostrable.

---

### Decisión previa — Feature Builder / Planner / Implementer

Tu intuición es parcialmente correcta. El `Implementer` actual tiene sólo cuatro líneas de reglas genéricas ("editar poco, respetar convenciones"). Eso sí se puede colapsar. El `Planner`, en cambio, tiene valor diferenciado: bloquea ediciones, fuerza aprobación explícita y puede persistir el plan. **La recomendación es mantener `Planner`, eliminar `Implementer` y mover sus reglas mínimas a `Feature Builder` directamente.** No se reemplaza nada por los modos nativos de VS Code, porque esos modos son del usuario, no son subagentes invocables programáticamente desde un orquestador.

---

### FASE 1 — Simplificación + Planner hardening *(unidad de trabajo mínima, sin dependencias externas)*

1. **Eliminar Implementer.agent.md**
   - Mover sus reglas a un bloque "Implementation rules" dentro de `Feature Builder.agent.md`
   - Actualizar la lista `agents` de `Feature Builder` quitando `Implementer`

2. **Endurecer Planner.agent.md** con cuatro reglas nuevas en el cuerpo:
   - Siempre mostrar el plan completo al usuario antes de guardarlo
   - Siempre guardar el plan como archivo Markdown — ruta estándar: `.github/plans/YYYY-MM-DD-<slug>.md`
   - La decisión de ejecutar es explícita: require respuesta `yes/no` antes de continuar
   - Las preguntas de aclaración son obligatorias cuando haya ambigüedad — nunca asumir

3. **Crear `.github/plans/`** como estructura de persistencia de planes
   - Directorio versionado, visible al equipo, alineado con el patrón .github
   - Añadir entrada en el catálogo de assets y en .gitignore solo si se quieren excluir borradores (recomendación: no excluir, son parte del historial)

4. **Actualizar `Feature Builder.agent.md`** para reflejar que la fase de implementación ahora tiene restricciones propias y no delega a un subagente separado

---

Bien vamos a centrarnos en una fase a la vez, para la fase 1
Consideraciones:
La opción que sí recomiendo es un modelo híbrido: mantener Planner.agent.md y Implementer.agent.md como contratos estables del repositorio, pero acercarlos semánticamente a Plan y Agent. En la práctica significa que Planner siga siendo el wrapper explícito del modo plan y Implementer el wrapper explícito del modo ejecución, mientras Feature Builder.agent.md continúa orquestando ambos. Así evitas duplicidad conceptual sin perder control del workflow compartido.


Evalua si combiene eliminar el implemmeter pasando su lógica a Feature Builder
Acerca tanto implementer como planner a los agentes de visual code
Analicemos los modelos predefinidos para cada agente, ¿cómo el usario puede definirlos en ejecución?

