---
seo_title: Para equipos que construyen para otros
lang: es
translation_of: handbook/08-for-teams-building-for-others.md
description: 'Una suite de evaluación, tres partes interesadas: qué necesita cada una —el desarrollador, la consultora y el cliente— de los mismos runs, y la regla que no admite excepciones.'
search:
  exclude: true
source: handbook/08-for-teams-building-for-others.md
source_sha: 86ffefba379b
source_commit: e4039b7
model: claude-opus-5
---

# 8. Para equipos que construyen para otros

Todo lo anterior vale para cualquiera que tenga un LLM en producción. Este capítulo es para un grupo más reducido: consultoras, empresas de software, cualquiera que construya y mantenga una funcionalidad con LLM para un cliente que no desarrolla y que es dueño de los datos sobre los que esa funcionalidad se ejecuta. Si es tu caso, la misma suite cumple dos funciones más, y una de ellas tiene una regla que no admite excepciones.

## Tres personas, una suite

En un producto que construyes para ti mismo hay una sola parte interesada. Aquí hay tres, y quieren cosas distintas de los mismos números.

**El desarrollador** quiere lo que describen los siete capítulos anteriores: casos, checks, una referencia, una comparación en CI.

**La consultora** —tu empresa— mantiene esta funcionalidad para varios clientes a la vez. Necesita responder, para cada uno de ellos, *¿la release del martes pasado empeoró el asistente del cliente A?*, y necesita responderlo sin tener los datos del cliente A y sin que los números del cliente A estén nunca en el mismo sitio que los del cliente B.

**El cliente** es dueño de los datos y no lee código. Tiene dos derechos: a un veredicto comprensible sobre un sistema que no puede inspeccionar, y a que sus datos no salgan de sus instalaciones. Y tiene una pregunta, que hará tarde o temprano, en una reunión o en una auditoría:

> *¿Qué probaste, cuándo, con qué versión y quién lo aprobó?*

Un dashboard no responde eso. Un dashboard muestra el estado de hoy. La pregunta es sobre una fecha, un commit, un artefacto que alguien pueda abrir seis meses después y que no haya cambiado desde entonces. El archivo de referencia del capítulo 6 es ese artefacto, y por eso vive en el repositorio y no en el servidor de un proveedor: un archivo que puedes entregar, con un hash y una fecha, es una prueba; una pantalla alojada por otro, no.

## La regla: el payload se queda donde nació, el veredicto viaja

Piensa en un caso inventado, con números incluidos, en una herramienta de reclutamiento: entra el CV de un candidato, sale un ranking y un check con juez pregunta si ese ranking está justificado. El run contiene ahora tres tipos de cosas:

- **El veredicto**: nombre del check, pasa o falla, puntuación 0.81, umbral 0.70, tolerancia, coste. Números sobre cómo se comportó el sistema.
- **El payload**: el CV, el texto del ranking y la *razón* del juez, que cita el CV para explicar la puntuación.
- **El agregado**: precision 0.75 sobre el conjunto, 12 verdaderos positivos, 4 falsos.

La consultora necesita el primero y el tercero para hacer su trabajo. No tiene derecho al segundo, ni lo necesita. Así que la regla es mecánica: **un run que cruza la frontera entre el cliente y la consultora se depura antes** — se eliminan las razones, se eliminan los metadatos del payload, se conservan los veredictos y los números. No como una opción que alguien se acuerda de marcar al exportar, sino como una propiedad del run mismo, verificada al leer el archivo, de modo que un documento que dice estar depurado no pueda contener una razón.

De ahí se siguen tres cosas, y cada una es una decisión de diseño a la que te enfrentarás con cualquier herramienta que uses:

**El juez se ejecuta dentro del perímetro.** Su razón cita los datos. Solo puede calcularse donde los datos pueden estar. Lo que sale es la puntuación que produjo, nunca la frase.

**El identificador del caso no es payload, así que nunca debe contener payload.** Tiene que cruzar la frontera, porque es la forma en que un veredicto encuentra a su equivalente en la referencia. `order-12345-mario-rossi` como id lleva el nombre de un cliente al repositorio de la consultora. Cuando los casos se generan a partir de producción, el id también debe generarse —una fecha, un número de secuencia, un hash corto— sin ninguna forma de colar un identificador de la aplicación.

**Los prompts no son seguros de forma automática.** Un prompt es trabajo de la consultora, pero a menudo contiene las reglas de negocio del cliente, y esas son del cliente. Por defecto, mantén el prompt dentro del perímetro; deja que una suite declare, en código que pasa por revisión, que sus prompts pueden viajar.

## Qué recibe el cliente

El repositorio no. Un **informe**: un documento que se basta a sí mismo —un único archivo HTML, imprimible— que empieza por *qué se estaba probando*: el cliente, la suite, este run, la referencia con la que se compara, la versión del código y si el árbol estaba limpio. Después responde *¿empeoró?* y luego *qué checks y cuánto*. Escrito para alguien que no lee código, generado a partir de la misma comparación que vio el desarrollador, de modo que los dos nunca puedan contradecirse.

Registra *cuándo* se aprobó la referencia, no quién la aprobó. El quién está en el historial de git del commit que la añadió, y eso es lo que hay que responder cuando llega la pregunta.

El informe se genera dentro del perímetro del cliente, donde las razones están disponibles, y puede incluirlas: para el cliente, la explicación del juez sobre por qué falló un caso es la línea más útil de la página. La versión depurada del mismo informe —veredictos, sin razones— es la que conserva la consultora.

Dos hábitos que hacen que el informe valga algo:

**Una referencia por entrega.** Cuando el cliente acepta una release, esa aceptación es una promoción. El archivo de referencia registra el estado que aceptó; el siguiente informe se compara con él. «Empeoró desde que lo aceptaste» es una frase que ambas partes pueden verificar.

**El agregado en el contrato.** Con casos etiquetados, una suite tiene un número —precision 0.75, en el caso inventado de arriba— lo bastante estable como para dejarlo por escrito: *el clasificador coincide con tus revisores en al menos el 70% de los casos confirmados.* Fíjalo donde el sistema está, medido, en el momento de la aceptación, no donde a alguna de las partes le gustaría que estuviera. El umbral es el compromiso; la comparación es la forma en que ambas partes lo vigilan.

## Qué conserva la consultora

Para cada cliente, en el repositorio propio de ese cliente o en un directorio por cliente que no pueda confundirse con el de otro: la suite, las referencias, los runs depurados. Nunca un único almacén donde los veredictos del cliente A estén junto a los del cliente B, donde basta una errata para leer los de uno como los del otro. Los perímetros son directorios, y la herramienta debería negarse a comparar o promocionar entre ellos, para que el error sea imposible y no solo poco recomendable.

Entre clientes, la consultora solo ve lo que viaja: qué checks, qué puntuaciones, qué agregados, qué prompts si la suite lo permitió. Eso basta para notar que una actualización del modelo degradó a tres clientes a la vez, y no contiene nada a lo que ninguno de ellos pudiera oponerse.

## Cuando producción alimenta la suite

Los capítulos anteriores ejecutan la suite sobre casos que escribiste tú. El siguiente paso —y es un paso, no un salto— es ejecutar los mismos checks sobre las respuestas que el sistema da en producción, dentro del perímetro del cliente, y convertir un fallo allí en un caso de la suite.

Eso cierra el ciclo que el capítulo 2 pedía a mano: *un fallo visto, un caso escrito* pasa a ser automático. También pone en vigor de golpe todas las reglas de este capítulo: el veredicto viaja a la consultora, la respuesta no; el juez se ejecuta donde están los datos; el caso generado tiene un id generado y una entrada reescrita. Si estableces esas reglas ahora, sobre la suite que ejecutas a mano, la versión automática son las mismas reglas sobre otra fuente. Si te las saltas ahora, las descubrirás la primera vez que un caso generado deje el CV de un candidato en un pull request.

## Hazlo hoy

1. Decide cuál será la pregunta del cliente y anota dónde está la respuesta. Si la respuesta es «en un dashboard contratado a un proveedor», no tienes respuesta.
2. Marca cada check de tu suite: ¿su razón cita los datos? Si es así, la razón de ese check es payload y no puede salir del perímetro.
3. Revisa los ids de tus casos. Si alguno contiene un nombre, un número de pedido, un identificador real, cámbialos ahora, antes de que el archivo vaya a ninguna parte.
4. Pon la suite y las referencias de cada cliente en el lugar propio de ese cliente. Si hoy dos clientes comparten un directorio, sepáralos hoy.
5. En la próxima aceptación, promociona. Entrega el informe al cliente. Escribe el agregado en el acta de aceptación. Desde ese momento, «¿empeoró desde que lo aceptaste?» tiene una respuesta que ambas partes pueden comprobar.

---

Este es el manual. Si lo has leído de principio a fin, sabes más sobre cómo mantener bajo control una funcionalidad con LLM que la mayoría de los equipos que publican una. La herramienta construida en torno a estos capítulos es [digline](../../index.md); el proyecto del que salió la mayoría de los números es [público](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f). Ninguno de los dos hace falta para empezar; los veinte casos sí.
