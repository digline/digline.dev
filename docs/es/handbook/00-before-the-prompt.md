---
seo_title: 'Antes del prompt: construir una funcionalidad que se pueda medir'
lang: es
translation_of: handbook/00-before-the-prompt.md
description: 'Cuatro decisiones vienen antes del prompt y deciden si una funcionalidad con LLM se puede evaluar siquiera: emitir la decisión como estructura, hacer determinista la entrada, registrar cada llamada y almacenar un fallo como fallo.'
search:
  exclude: true
source: handbook/00-before-the-prompt.md
source_sha: a25e3595ba15
source_commit: 49fbb1a
model: claude-opus-5
---

# 0. Antes del prompt

El prompt es el medio del trabajo, no su principio. Cuatro decisiones lo preceden, cada una barata la tarde en que la tomas y casi irreversible una vez que la funcionalidad está en producción; juntas deciden si lo demás de este manual se puede hacer siquiera.

## Por qué el orden sale mal

El orden habitual es escribir el prompt, publicar y ocuparse del resto cuando alguien se queje. Parece empezar por lo difícil. Es empezar por lo único blando: el prompt sigue siendo barato de cambiar, y todo lo que lo rodea fragua. La forma de la respuesta se convierte en el contrato al que se ajustan el renderizador, el cliente y las filas almacenadas, y las filas ya escritas son las que tienes. Así que la atención va a la parte que seguirá siendo barata dentro de un año, y se salta las cuatro que no lo serán.

Lo que sigue es la forma habitual de una funcionalidad con LLM en producción, leída del código de un sistema y no contrastada con él: el código arma un contexto, una llamada al modelo decide qué decir, vuelve prosa. El [capítulo 3](../../handbook/03-ground-truth.md) desarma ese sistema desde el otro extremo y pregunta de dónde podría salir su verdad de referencia. Esta es la lista de decisiones que se la habrían dado. Aquí no hay ningún número: no se ha ejecutado nada.

Esa lectura fue una lectura, y no hay ningún artefacto detrás: ninguna nota fechada, ningún repositorio capturado, nada que citar. La forma descrita arriba es lo que se entendió al mirar un sistema, anotado después de memoria, y quien busque el documento del que proviene no lo encontrará. Se ofrece como una forma que se repite, no como evidencia: cada afirmación de este capítulo depende de si la reconoces en tu propio sistema, porque no hay nada más que la sostenga.

## 1. Emite la decisión, no solo la prosa

Si la funcionalidad elige —qué elementos mencionar, cuáles omitir, en qué orden—, esa elección es el comportamiento que vas a querer medir, y la prosa es su representación. Un sistema que devuelve los ids que eligió, en orden, junto a la frase que escribió permite hacer aserciones mecánicas y le da al juicio de una persona algo a lo que apuntar. Uno que solo devuelve la frase no lo permite, por mucho que le añadas después: cada check que escribas lee prosa, y también lo hace cualquier discusión sobre si la elección fue correcta.

Hoy es un campo en la respuesta y un parseo. Más adelante es el contrato entre el modelo y todo lo que viene después, y un contrato es de los cambios caros.

**Dónde no encaja:** no todas las funcionalidades eligen. Si lo que vendes es la prosa misma —una reescritura, una traducción, una respuesta en una conversación—, no hay selección que emitir y solo cargas con las decisiones 3 y 4. La mayoría de las funcionalidades no son así: seleccionan, ordenan, enrutan o extraen, y al resultado lo llaman resumen.

## 2. Haz que la entrada sea determinista

Los mismos datos almacenados a la entrada, el mismo contexto armado a la salida. Una consulta que toma las primeras N filas sin ordenar le cede esa elección a la base de datos, y dos runs sobre datos que no han cambiado pueden diferir sin que el modelo haya cambiado de opinión.

El coste obvio es que no hay nada que congelar, así que no hay caso. El que duele más tiempo es la atribución: cada diferencia entre dos runs tiene dos autores posibles y ninguna forma de distinguirlos, y un run en rojo que nadie puede atribuir es la manera en que un equipo aprende a dejar de mirar el rojo.

Hoy es un criterio de ordenación en una consulta. Más adelante es eso, más cada run registrado antes del arreglo, hecho sobre una entrada que nadie puede reproducir.

## 3. Registra la llamada desde el primer día

La entrada armada tal como la recibió el modelo, la respuesta tal como llegó, qué modelo respondió y cuándo. Cuatro campos.

Es el único punto que no sirve de nada el día en que lo escribes: ninguna funcionalidad lo lee, ninguna pantalla lo muestra, y es lo primero que se cuestiona en una revisión. También es el único que no se puede añadir después a ningún precio. Los demás son caros de incorporar a posteriori; este no se puede incorporar, porque lo que habría contenido ya no existe.

**Dónde no encaja:** no es gratis, y un capítulo que dijera lo contrario se equivocaría. La entrada armada son los datos que entraron, así que el registro los hereda, y hereda también las reglas sobre dónde puede residir ([capítulo 8](../../handbook/08-for-teams-building-for-others.md)): mismo perímetro, misma retención. Y toma *qué modelo respondió* de la respuesta, no de lo que pediste: el día en que un proveedor reapunta un alias, esos son dos hechos distintos.

## 4. Haz que un fallo se distinga de una respuesta vacía

Una llamada que falló y una llamada que de verdad no tenía nada que decir son dos hechos. Almacenados como la misma fila se convierten en uno solo, y el que resulta es el silencioso: una caída del servicio se lee como una mañana tranquila.

Esta es la decisión que pudre el registro que acabas de construir: todo recuento hecho sobre esas filas interpreta el silencio como conformidad, y sigue equivocado mientras se conserven las filas. Tampoco se pueden separar después, ni por fecha ni por inferencia, por la razón que da el capítulo 3 sobre reinterpretar una etiqueta ambigua. Siguen siendo ambiguas.

Hoy es un estado más. Más adelante es un estado más, y nada del historial.

## Y entonces el prompt

Ahora escríbelo, y fíjate en lo que han hecho las cuatro decisiones: el prompt es la parte más barata de cambiar de la funcionalidad, que es donde debería haber estado desde el principio. La estructura es el contrato, el prompt es cómo se rellena, y un prompt mejor es un diff en un solo archivo del que nada aguas abajo tiene que enterarse.

## Los invariantes vienen antes que los casos

Un invariante es algo que se cumple en una salida correcta cualquier día, sean cuales sean los datos. El capítulo 3 enumera los que le tocan a esta forma de funcionalidad: todo id elegido estaba en la entrada, el elemento obligatorio aparece, una entrada vacía produce una selección vacía.

Lo que vale la pena añadir es *cuándo* puedes escribirlos. Un invariante no necesita verdad de referencia, ni etiqueta, ni caso, ni juez: es una afirmación sobre el sistema, no sobre una respuesta. Es el único check que puede existir al día siguiente del prompt, antes de que haya empezado el trabajo del [capítulo 2](../../handbook/02-cases.md), y lo más barato de este manual. Casi nadie los escribe.

## El gesto, donde la persona ya está

Después, un gesto, en el camino que la persona ya recorre, con el que pueda discrepar. El capítulo 3 trata de qué preguntar, de por qué la pregunta obvia registra dos cosas a la vez, y de lo lejos que eso queda de estar resuelto para una persona que no eres tú.

Lo que viene antes es más pequeño: el gesto necesita un objeto. Sin la decisión 1 no hay a qué engancharlo, y un pulgar hacia abajo cae sobre un párrafo: registra que una mañana fue mala, lo cual no es un hecho sobre ninguna decisión que tomara el sistema. Con la estructura, el mismo clic cae sobre un elemento, en una posición, con un id. Construye las dos cosas en la misma semana, o el gesto recogerá lo que no es durante un año.

Solo entonces, la suite.

## En una página

```text
What has to be true before the prompt is worth writing?
├── the decision comes back as data ..... the ids it chose, in order, beside the prose
├── the input cannot move on its own .... same data in, same assembled context out
├── every call is written down .......... the input · the reply · which model · when
└── a failure is not an empty answer .... two outcomes, two rows, never one

                                     ── the prompt ──
                   the only part of this you can still change tomorrow

And then, in this order, what those four have made possible:
├── invariants .......................... true on every possible day, no model needed
├── one judgement gesture ............... where the person already is, attached to the ids
└── a suite ............................. cases, checks, a reference → chapters 1 to 8
```

## Hacerlo hoy

Siete preguntas, una por paso. Respóndelas en una pizarra antes de escribir una línea de la funcionalidad; la columna de la derecha es aquello entre lo que estás eligiendo.

| La pregunta | Lo que cuesta responderla tarde |
|---|---|
| 1. ¿Dice la funcionalidad *qué* cosas eligió, como datos, y no solo en prosa? | No se puede hacer ninguna aserción, y ningún gesto puede apuntar a una elección. |
| 2. Con los mismos datos almacenados, ¿llega el mismo contexto al modelo? | No hay entrada que congelar, así que no hay caso; y no hay run en rojo que se pueda atribuir. |
| 3. ¿Se registran en cada llamada la entrada armada, la respuesta, el modelo que respondió y la hora? | El único que no se puede añadir después a ningún precio. |
| 4. ¿Puedes distinguir una llamada fallida de un genuino «nada que informar»? | Una caída del servicio se almacena como una mañana tranquila, y todo recuento sobre esas filas interpreta el silencio como conformidad. |
| 5. ¿Es el prompt lo único que tiene que cambiar cuando quieres una respuesta distinta? | El prompt deja de ser barato: cambiarlo se convierte en un cambio de todo lo que viene después. |
| 6. ¿Qué se cumple en una salida correcta cualquier día, y se puede comprobar sin modelo? | Empiezas por el extremo más caro, un juez, sobre un sistema del que nadie ha demostrado que sea consistente. |
| 7. ¿En qué punto de lo que una persona ya hace podría decir que esto estuvo mal, y a qué está enganchado ese gesto? | La discrepancia nunca llega, o llega como una etiqueta que significa dos cosas. |

El siguiente capítulo trata de lo que tienes una vez que todo esto está en su sitio, y de por qué lo que está en el centro parece una función y no lo es.
