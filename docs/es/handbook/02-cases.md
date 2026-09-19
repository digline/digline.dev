---
seo_title: 'Casos: el activo que nadie construye'
lang: es
translation_of: handbook/02-cases.md
description: Todo equipo que publica una función con LLM tiene un prompt y casi ninguno tiene casos. Qué es un caso y cómo tener veinte esta misma tarde.
search:
  exclude: true
source: handbook/02-cases.md
source_sha: 67838bc398da
source_commit: 48129ea
model: claude-opus-5
---

# 2. Casos: el activo que nadie construye

Todo equipo que publica una función con LLM tiene un prompt. Casi ninguno tiene casos. Este capítulo trata de por qué eso está al revés y qué hacer al respecto, en concreto, a partir de esta tarde.

## Qué es un caso

Un caso es una entrada que te importa, junto con lo que sabes sobre la respuesta correcta.

Eso es todo. Para un bot de soporte: una pregunta que un cliente hizo de verdad, y si la respuesta debería haber mencionado la política de devoluciones. Para un clasificador: una descripción de puesto, y la familia a la que un reclutador confirmó que pertenece. Para el [juez de la newsletter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) que se usa a lo largo de este manual: el título y el resumen de un artículo, y si el lector lo marcó como algo que vale la pena leer.

```json
{
  "id": "2026-08-24-controlling-reasoning-effort-in-llms",
  "vars": {
    "source": "Ahead of AI (Raschka)",
    "title": "Controlling Reasoning Effort in LLMs",
    "summary": "How LLMs Learn Low-, Medium-, and High-Effort Reasoning Modes"
  },
  "expected": {
    "marked": true
  },
  "metadata": {
    "link": "https://magazine.sebastianraschka.com/p/controlling-reasoning-effort-in-llms",
    "original_score": 4
  }
}
```

Tres campos hacen el trabajo. El `id` lo nombra. Las `vars` son lo que recibe el sistema. El `expected` es lo que sabes. Los `metadata` son para quien lea el caso más adelante —de dónde salió el artículo y la puntuación que le dio el juez esa mañana— y ningún check los lee. No siempre sabes cuál es la salida correcta exacta —para un resumen o una respuesta de texto libre, nadie lo sabe—, pero siempre sabes *algo*: debería mencionar X, no debería pasar de N palabras, una persona en la que confías la consideró aceptable. Todo lo que sepas va en `expected`. Lo que no sepas lo dejas fuera y lo compruebas con algo más débil.

## Por qué el prompt se lleva toda la atención y los casos ninguna

Escribir un prompt da la sensación de estar construyendo algo. Escribes, el modelo responde, ajustas, responde mejor. Cada iteración es una pequeña recompensa. Escribir casos parece papeleo: copiar una entrada, decidir cuál es la respuesta correcta, guardarla, repetir. Sin recompensa, sin progreso visible, y la función ya funciona: la viste funcionar, tú mismo escribiste la entrada.

Así que el prompt recibe cuarenta iteraciones y los casos cero, y el equipo publica con un prompt ajustado con lo que el autor escribiera esa tarde. Tres meses después un usuario informa de algo raro. Nadie puede decir si es nuevo, porque no hay nada con qué comparar. El autor prueba la entrada, se ve bien, o no: una sola muestra en cualquiera de los dos casos. El prompt recibe una cuadragésima primera iteración, que arregla esta entrada y rompe en silencio otras dos que nadie escribió.

Ese bucle es lo que pasa por defecto. No es una falta de disciplina; es lo que ocurre cuando la única retroalimentación es la siguiente respuesta del modelo.

Los casos cambian el bucle. Con veinte casos, la cuadragésima primera iteración es un número: *diecinueve de veinte antes, diecisiete después*. El arreglo que rompió dos cosas se ve en el mismo minuto en que se hizo.

## De dónde salen los casos

No de tu imaginación. Los casos que inventas en tu escritorio prueban las entradas en las que ya pensaste, que son exactamente las entradas que el prompt ya maneja. Los casos útiles vienen de cuatro sitios, y ninguno requiere creatividad:

**Correcciones.** Cada vez que una persona corrige al modelo —un reclutador cambia la familia del puesto, un editor reescribe el resumen, el lector marca un artículo al que el juez dio poca puntuación—, esa corrección es un caso etiquetado, gratis, y más valioso que cualquier cosa que pudieras escribir. En el proyecto de la newsletter, cada mañana el lector dice qué artículos valieron la pena de verdad; esa respuesta es el `expected` de los casos del día. El programa lo registra como efecto secundario del uso normal. Busca ese efecto secundario en tu propio producto: casi siempre está ahí, sin registrar.

**Quejas.** Un usuario dice «esto lo hizo mal». Antes de tocar el prompt, guarda la entrada y la respuesta correcta como caso. Luego arregla el prompt. Luego ejecuta los casos. La queja se convierte en protección permanente en vez de un parche puntual, y si el arreglo rompe otra cosa, te enteras ahora.

**Fallos en producción.** Cualquier salida que fuera malformada, vacía, contraria a las políticas o vergonzosa. Ya las tienes en los logs; son los casos que menos te gustaría volver a ver.

**Casos límite que notaste.** La entrada vacía. La entrada en el idioma equivocado. La entrada de 4000 palabras. La entrada que menciona a tu competidor. Has visto al modelo manejar estas entradas de forma rara al menos una vez; anótalas mientras las recuerdas.

El hábito que importa más que cualquier herramienta: **un fallo visto, un caso escrito, el mismo día.** No «habría que añadir pruebas para esto más adelante». Más adelante nunca llega; el fallo sí.

## Cuántos, y cuáles

Veinte bastan para empezar. No doscientos: nunca escribirás doscientos, y veinte ya convierten una suposición en un número. En el proyecto de la newsletter, veintiún casos bastaron para medir el ruido del juez a lo largo de seis runs, y para mostrar que reducir cuánto lee el juez de cada artículo, de 1500 caracteres a 400, [no empeoró nada](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/README.md#reporthtml).

Lo que necesitan esos veinte:

**Las dos respuestas.** Si todos los casos esperan un «sí», un modelo que siempre dice que sí obtiene una puntuación perfecta. La suite de la newsletter tiene diez artículos que el lector quería y once que no. Sin esos once, la mayor debilidad del juez —promover cosas que solo suenan relevantes— sería invisible.

**El aburrido caso intermedio, no solo los extremos.** Una suite de veinte entradas patológicas te dice cómo falla el sistema bajo presión y nada sobre cómo se comporta un martes cualquiera. Incluye entradas corrientes, con entidad propia, no como la mayor parte del conjunto.

**Entradas estables.** Un caso que descarga los datos de hoy es un caso distinto mañana. Congela la entrada en el archivo. El proyecto de la newsletter guarda el resumen del artículo en el caso, no una URL que haya que volver a descargar: las mismas veintiuna entradas, en cada run, desde agosto.

**Una etiqueta, si puedes.** Para cualquier cosa que clasifique —positivo/negativo, aprobar/rechazar, relevante/no relevante—, añade la etiqueta. Con etiquetas, tu suite obtiene un agregado: *precision entre 0.60 y 0.67 en seis runs de la suite de la newsletter*, un número lo bastante estable como para ponerle un umbral, mientras que los casos sueltos se movían por tres votos de cinco. Sin etiquetas tienes veinte veredictos y ningún resumen.

## Lo que los casos no son

**No son los ejemplos del prompt.** Los ejemplos few-shot dentro de tu prompt son ruedas de apoyo para el modelo. Los casos se reservan aparte; el modelo nunca los ve como ejemplos. Si reutilizas las mismas entradas para ambas cosas, estás probando la capacidad del modelo de copiar, no de generalizar.

**No son un entregable único.** Un archivo de casos que estaba completo el día del lanzamiento queda desfasado con la segunda queja. El conjunto crece al ritmo de producción; por eso «un fallo, un caso» es una regla y no un proyecto.

**No son datos sensibles, si el archivo va a salir a alguna parte.** Un caso construido a partir de una conversación real con un cliente lleva consigo a ese cliente. Mantén esos casos dentro del perímetro del que salieron, o reescribe la entrada con la misma forma y datos distintos. En el proyecto de la newsletter las entradas son artículos públicos, así que el archivo también es público; en una herramienta de selección de personal, las descripciones de puesto están bien y los CV no.

## La parte que se acumula

Todo lo demás en un proyecto con LLM pierde valor. El prompt que ajustaste contra un modelo es peor en el siguiente. El umbral que elegiste se desvía. El juez cambia de opinión. Los casos no pierden valor: una respuesta correcta a una entrada real sigue siendo correcta cuando cambia el modelo, cuando cambia el prompt, cuando cambias de proveedor. Veinte casos en marzo son veinte casos en septiembre, más lo que septiembre haya añadido.

Por eso el trabajo aburrido es el único que vale la pena hacer primero. Seis meses después, el equipo con el mejor prompt tiene un prompt. El equipo con doscientos casos reales tiene la capacidad de cambiar cualquier cosa —modelo, prompt, proveedor— y saber en menos de una hora si ha empeorado. El prompt es una opinión; los casos son la memoria.

## Hazlo hoy

1. Busca la corrección en tu producto: el punto donde una persona corrige al modelo. Si existe, empieza a registrarla. Si no existe, eso es lo primero que hay que construir, antes que cualquier suite.
2. Abre tus logs. Toma las últimas diez entradas que produjeron una queja o una salida rara. Escribe la respuesta correcta de cada una. Ya son diez casos.
3. Toma diez entradas corrientes de esos mismos logs, de las que nadie se quejó. Confirma que la salida estaba bien. Ya son veinte.
4. Ponlas en un archivo, en el repositorio, junto al código. Congela las entradas. Añade etiquetas donde correspondan.
5. A partir de ahora: un fallo visto, un caso escrito, el mismo día.

El siguiente capítulo trata de dónde salen las respuestas correctas cuando nadie te da ninguna, y por qué eso se decide cuando escribes la función, no después.
