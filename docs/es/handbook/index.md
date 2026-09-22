---
title: Manual
seo_title: 'Manual: mantener bajo control una funcionalidad con LLM'
lang: es
translation_of: handbook/index.md
description: 'Nueve capítulos sobre la evaluación de aplicaciones LLM en la práctica: qué construir primero, casos, verdad de referencia, checks, el juez, la referencia, mantenimiento. Sobre el problema, no sobre la herramienta.'
search:
  exclude: true
source: handbook/index.md
source_sha: 102161a61926
source_commit: c51c251
model: claude-opus-5
---

# Manual

Nueve capítulos sobre cómo mantener bajo control una funcionalidad con LLM, para
quienes ya tienen una en producción y todavía no han pasado la mala semana.
Tratan del problema, no de la herramienta: nada de lo que hay aquí requiere
tener digline instalado, y la mayoría de los números salen de un pequeño
proyecto público que puedes consultar por tu cuenta. Empieza por el primer capítulo y léelos
en orden: cada uno se apoya en el anterior.

- **[0. Antes del prompt](../../handbook/00-before-the-prompt.md)** — las cuatro
  decisiones que vienen antes del prompt y deciden si la funcionalidad se puede
  medir siquiera. El único capítulo que te pide cambiar lo que estás
  construyendo en vez de medirlo.
- **[1. Lo que realmente estás entregando](../../handbook/01-what-you-are-shipping.md)** — por
  qué una llamada a un modelo parece una función y no lo es, y qué te cuesta eso.
- **[2. Casos: el activo que nadie construye](../../handbook/02-cases.md)** — todo equipo tiene
  un prompt, casi ninguno tiene casos. Qué es un caso y cómo tener veinte esta
  misma tarde.
- **[3. Verdad de referencia: cuando nadie te la da](../../handbook/03-ground-truth.md)** — de
  dónde salen las respuestas correctas cuando no hay datos etiquetados, y por qué
  eso se decide cuando escribes la funcionalidad.
- **[4. Checks: primero los deterministas, el juez al final](../../handbook/04-checks.md)** —
  cómo convertir una salida en un veredicto, y la regla que más tiempo ahorra:
  usar un modelo para juzgar solo aquello que no puede juzgar ninguna otra cosa.
- **[5. El juez](../../handbook/05-the-judge.md)** — los dos ruidos, por qué tienes que medir el
  del juez antes de poder leer el de tu sistema, y el procedimiento que sustituye
  las conjeturas por un número.
- **[6. La referencia](../../handbook/06-the-reference.md)** — un umbral no es una referencia.
  El único número que anotas y con el que aceptas que te midan.
- **[7. Mantenimiento](../../handbook/07-maintenance.md)** — cuándo se ejecuta la suite, qué
  debería hacerte mirar y qué hacer la mañana en que se pone en rojo y tú no has
  cambiado nada.
- **[8. Para equipos que construyen para otros](../../handbook/08-for-teams-building-for-others.md)** —
  la misma suite haciendo dos tareas más cuando la funcionalidad con LLM es de un
  cliente, y la única regla que no admite excepciones.
