---
title: Por qué
template: why.html
seo_title: Por qué las aplicaciones de LLM necesitan un baseline
lang: es
translation_of: why.md
description: Un prompt no es código, y el modelo se mueve bajo tus pies. Por qué un umbral de aprobado/fallo no puede ver una regresión de calidad y qué mide en su lugar un baseline aprobado.
search:
  exclude: true
source: why.md
source_sha: d1952e7f33ac
source_commit: 3f60b0d
model: claude-opus-5
---

# Por qué

Si has puesto un modelo de lenguaje en algo que la gente usa, esta página trata de un problema que ya tienes. Puede que aún no lo hayas notado. Ese es el problema.

Los ejemplos que siguen provienen de un proyecto real y público: un pequeño programa que lee cada mañana unos cuantos boletines sobre IA y pregunta a un modelo qué artículos merecen veinte minutos del tiempo de una persona. Es casi lo más simple que puede ser una aplicación de LLM. Todo lo que aparece en esta página le ocurrió a él.

## Un prompt no es código

Cuando cambias una línea de código, la misma entrada produce la misma salida, siempre. Eso es lo que hace posibles las pruebas: escribes lo que debería salir y la máquina te dice si salió.

Un prompt no funciona así. Haz la misma pregunta al mismo modelo cinco veces, con el mismo prompt y el mismo artículo, y no siempre responde igual. Cada run del juez de boletines pregunta cinco veces por cada uno de los veintiún artículos. En dos a seis de ellos, según el run, las cinco respuestas no coinciden entre sí. Nada cambió entre esas cinco: ni el código, ni el modelo, ni la entrada. El modelo es una distribución de probabilidad y tú estás muestreando de ella.

Pero significa que el reflejo habitual —*ejecutarlo una vez, parece correcto, publicar*— no es una prueba. Es una sola muestra.

## El modelo cambia bajo tus pies

Aunque no toques una línea, aquello sobre lo que construiste se mueve.

Los proveedores actualizan modelos. Marcan versiones como obsoletas. Cambian a qué apunta un alias por defecto. Un modelo llamado `latest` en marzo no es el mismo modelo en junio, y nada en tu repositorio registra que cambió. Tu historial de commits dice «sin cambios desde la release»; tus usuarios dicen «empeoró la semana pasada»; ambos dicen la verdad.

Este es el fallo que ninguna revisión de código puede detectar, porque no hay diff. La única forma de verlo es tener algo con lo que comparar —un registro de cómo se comportó el sistema sobre un conjunto de entradas, en una fecha, con una versión— y volver a ejecutar las mismas entradas para mirar la diferencia.

## «Funciona» no es una medición

La mayoría de los equipos sí tienen un umbral en algún sitio: una puntuación por debajo de 0.7 falla, por encima pasa. Es mejor que nada, y se le escapa el fallo que más importa.

El patrón es este, con cifras inventadas. Un check obtiene 0.91 el día que publicas. Tres semanas y dos ajustes de prompt después, obtiene 0.78. Sigue por encima de 0.7. Sigue en verde. Sigue pasando todas las pruebas que tienes. Y los usuarios ya han empezado a notarlo, porque una caída de trece puntos es un producto distinto para quien está al otro lado.

Un umbral detecta lo que está *por debajo de la línea*. No detecta *peor que antes*. Para eso hace falta una referencia —el estado aprobado, registrado— y una comparación contra ella en cada cambio. La referencia es la pieza que le falta a casi todos los equipos, y es la razón de que la deriva de 0.91 a 0.78 les resulte invisible hasta que un cliente la nombra.

## Quién juzga al juez

Para todo lo que no se puede comprobar por coincidencia exacta —si una respuesta es cortés, si se ajusta a la política, si resume con fidelidad— la herramienta práctica es otro modelo que actúa como juez. Funciona. También hereda todos los problemas anteriores: el juez también muestrea, y cambia de opinión.

En el proyecto de los boletines, el juez vota cinco veces por artículo y decide la mayoría. Dos runs separados por quince minutos, con el mismo prompt: en uno de los veintiún artículos la mayoría se dio la vuelta, de dos votos de cinco a cinco de cinco. Y los artículos en los que el voto se divide no son los mismos en cada run: en los seis runs publicados, once de los veintiuno se dividieron al menos una vez, uno de ellos en cinco runs y cuatro de ellos solo una vez. Diez no se dividieron nunca. Esos once son los que están en el límite, y una mayoría de cinco votos es poca cosa sobre la que sostener una decisión.

No es solo mi experiencia. Dan Luu hizo calificar otras diez veces las mismas salidas de Senior SWE-Bench y el veredicto sobre el buen gusto discrepó del oficial en el 23% de los casos, con entradas idénticas ([ejercicio 7](https://danluu.com/exercise-7/)). Apliqué la misma lectura a mis propios jueces: [Malas evaluaciones, las mías](../blog/bad-evals-my-own.md). El juez es un instrumento. Un instrumento se calibra.

De aquí se derivan dos consecuencias. Primera, no puedes saber si tu *sistema* empeoró hasta que sepas cuánto oscila tu *juez* por sí solo: el noise floor hay que medirlo antes que nada. Segunda, un caso aislado es una mala unidad para tomar una decisión. A lo largo de ese par de runs, el agregado se movió en un artículo de veintiuno, mientras que el propio artículo se movió tres votos de cinco. Los casos individuales sirven para diagnosticar. El agregado es lo que admite un umbral.

## La pregunta del cliente

Si construyes funcionalidades con LLM para tu propio producto, todo lo anterior es un problema de calidad. Si las construyes para otro —un cliente, un comprador, una empresa regulada— también es un problema contractual, y la pregunta llega en una forma concreta:

*¿Qué probaste, cuándo, con qué versión y quién lo aprobó?*

Un dashboard no responde a eso. Un dashboard muestra el día de hoy. La pregunta es sobre una fecha, un commit, un artefacto que alguien pueda abrir seis meses después. La respuesta tiene que ser un archivo: esta suite, esta referencia, esta comparación, esta aprobación, en el repositorio, junto al código que describe, con el texto del prompt que lo produjo. Si vive en el servidor de un proveedor, no puedes mostrarlo tú; si vive solo en la memoria de alguien, no existe.

Para el cliente, ese mismo archivo es la prueba de que aquello que pagó sigue haciendo lo que hacía el día en que lo aceptó. Eso vale más para él que cualquier métrica.

## Qué significa «bajo control»

Junta las piezas y «bajo control» resulta ser tres cosas concretas, ninguna de ellas costosa:

**Una referencia.** Un run de tu suite que hayas mirado y aprobado —puntuaciones, texto del prompt, commit— registrado como archivo y añadido al repositorio. No el primer run en verde: la mediana de unos cuantos, porque ya sabes que el juez oscila.

**Una comparación en cada cambio.** Cambias el prompt, el modelo, la recuperación, cualquier cosa: ejecuta la suite otra vez y compárala con la referencia. No «¿está por debajo del umbral?» sino «¿es peor que antes, dónde y cuánto?», con el diff del prompt justo al lado de las puntuaciones que movió. En CI, para que ocurra te acuerdes o no; de forma programada, para que ocurra cuando el proveedor cambie algo y tú no.

**Un historial.** Cada referencia que hayas aprobado, en git, con los motivos. Cuando alguien haga la pregunta del cliente, la respuesta es un `git log`.

En el proyecto de los boletines, un run cuesta unos siete céntimos: veintiún artículos, juzgados cinco veces cada uno. El proyecto tiene una cifra que puede enunciar, con los runs que la respaldan: el juez coincide con el lector en 16 de 21 artículos en cuatro de los seis runs publicados, y en 15 y 14 en los otros dos.

Eso es lo que hace [digline](../index.md), y es todo lo que hace. La referencia vive en tu repositorio. La única llamada que sale es la que tu suite hace a tu propio modelo: digline no tiene servidor, ni cuenta, ni telemetría. `pip install digline` para probarlo; el proyecto de los boletines es [público](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) si prefieres ver primero algo real.

De dónde salen estas cifras: seis runs del juez de boletines, incluidos en el repositorio como [fixtures](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures), [con una nota sobre qué cifra viene de qué run](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/README.md), y [un script](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/recompute.py) que recalcula a partir de ellos todas las cifras de esta página.

---

Si tienes treinta minutos en lugar de cinco: el [Manual](../handbook/01-what-you-are-shipping.md).

¿Quieres saber en qué se diferencia de las herramientas que ya conoces? Consulta [En qué se diferencia digline](../comparison/index.md).
