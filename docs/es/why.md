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
source_sha: 331a861da2e1
source_commit: 933f4e0
model: claude-opus-5
---

# Por qué

Si has puesto un modelo de lenguaje en algo que la gente usa, esta página trata de un problema que ya tienes. Puede que aún no lo hayas notado. Ese es el problema.

Los ejemplos que siguen provienen de un proyecto real y público: un pequeño programa que lee cada mañana unos cuantos boletines sobre IA y pregunta a un modelo qué artículos merecen veinte minutos del tiempo de una persona. Es casi lo más simple que puede ser una aplicación de LLM. Todo lo que aparece en esta página le ocurrió a él.

## Un prompt no es código

Cuando cambias una línea de código, la misma entrada produce la misma salida, siempre. Eso es lo que hace posibles las pruebas: escribes lo que debería salir y la máquina te dice si salió.

Un prompt no funciona así. Envía el mismo artículo al mismo modelo con el mismo prompt y una mañana lo puntúa con un 4 y la mañana siguiente con un 3. Nada cambió: ni tu código, ni el modelo, ni la entrada. El modelo es una distribución de probabilidad y tú estás muestreando de ella.

En el juez de boletines, de veintiún artículos puntuados dos veces con un prompt idéntico, uno cambió de veredicto. Eso no es un error del juez. Es lo que un juez es. Pero significa que el reflejo habitual —*ejecutarlo una vez, parece correcto, publicar*— no es una prueba. Es una sola muestra.

## El modelo cambia bajo tus pies

Aunque no toques una línea, aquello sobre lo que construiste se mueve.

Los proveedores actualizan modelos. Retiran versiones. Cambian a qué apunta un alias por defecto. Un modelo llamado `latest` en marzo no es el mismo modelo en junio, y nada en tu repositorio registra que cambió. Tu historial de commits dice «sin cambios desde la release»; tus usuarios dicen «empeoró la semana pasada»; ambos dicen la verdad.

Este es el fallo que ninguna revisión de código puede detectar, porque no hay diff. La única forma de verlo es tener algo con lo que comparar —un registro de cómo se comportó el sistema sobre un conjunto de entradas, en una fecha, con una versión— y volver a ejecutar las mismas entradas para mirar la diferencia.

## «Funciona» no es una medición

La mayoría de los equipos sí tienen un umbral en algún sitio: una puntuación por debajo de 0.7 falla, por encima pasa. Es mejor que nada, y se le escapa el fallo que más importa.

El patrón es este. Un check obtiene 0.91 el día que publicas. Tres semanas y dos ajustes de prompt después, obtiene 0.78. Sigue por encima de 0.7. Sigue en verde. Sigue pasando todas las pruebas que tienes. Y los usuarios ya han empezado a notarlo, porque una caída de trece puntos es un producto distinto para quien está al otro lado.

Un umbral detecta *por debajo de la línea*. No detecta *peor que antes*. Para eso hace falta una referencia —el estado aprobado, registrado— y una comparación contra ella en cada cambio. La referencia es la pieza que le falta a casi todos los equipos, y es la razón de que la deriva de 0.91 a 0.78 les resulte invisible hasta que un cliente la nombra.

## Quién juzga al juez

Para todo lo que no se puede comprobar por coincidencia exacta —si una respuesta es cortés, si se ajusta a la política, si resume con fidelidad— la herramienta práctica es otro modelo que actúa como juez. Funciona. También hereda todos los problemas anteriores: el juez también muestrea, y cambia de opinión.

En el proyecto de los boletines, cuando el juez pasó a muestrearse varias veces por artículo en lugar de una, el panorama se volvió más claro y más incómodo a la vez. La mayoría de los artículos se juzgaban igual todas las veces. Seis de veintiuno, no: en esos, un juez de cinco votos se dividía 3–2 en un run y 4–1 en el siguiente. Esos seis eran exactamente los artículos ante los que una persona también habría dudado. El juez no estaba roto; era honesto sobre lo que estaba en el límite.

No es solo mi experiencia: Dan Luu volvió a calificar diez veces las mismas salidas de Senior SWE-Bench y encontró que el veredicto discrepaba del resultado oficial en torno a una cuarta parte de las veces, con entradas idénticas ([ejercicio 7](https://danluu.com/exercise-7/)). Apliqué esta lectura a mis propios jueces: [Malas evaluaciones, las mías](../blog/bad-evals-my-own.md). El juez es un instrumento. Un instrumento se calibra.

De aquí se derivan dos consecuencias. Primera, no puedes saber si tu *sistema* empeoró hasta que sepas cuánto oscila tu *juez* por sí solo: el noise floor hay que medirlo antes que nada. Segunda, un caso aislado es una mala unidad para tomar una decisión. A lo largo de esos mismos runs, el agregado —en cuántos artículos coincidieron el juez y la persona— se movió en un caso de veintiuno, mientras que los casos individuales oscilaban tres votos. Los casos individuales sirven para diagnosticar. El agregado es lo que admite un umbral.

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

En el proyecto de los boletines, todo esto cuesta unos ocho céntimos por run. Cuatro experimentos sobre el prompt del juez, una calibración, y el proyecto tiene una cifra que puede enunciar —«coincide con el lector en el 62% de los artículos dudosos, de forma estable entre runs»— y un archivo que dice qué prompt la produjo.

Eso es lo que hace [digline](../index.md), y es todo lo que hace. La referencia vive en tu repositorio. Nada sale de tu máquina. `pip install digline` para probarlo; el proyecto de los boletines es [público](https://github.com/digline/brief) si prefieres ver primero algo real.

---

Si tienes treinta minutos en lugar de cinco: el [Manual](../handbook/01-what-you-are-shipping.md).

¿Te preguntas en qué se diferencia de las herramientas que ya conoces? Consulta [Cómo se compara digline](../comparison/index.md).
