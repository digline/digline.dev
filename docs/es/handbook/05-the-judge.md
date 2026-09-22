---
seo_title: El juez, y cómo medir su ruido
lang: es
translation_of: handbook/05-the-judge.md
description: Un juez LLM también extrae muestras. Por qué debes medir el ruido del juez antes de poder leer el de tu sistema, y el procedimiento que sustituye la conjetura por un número.
search:
  exclude: true
source: handbook/05-the-judge.md
source_sha: ba60264b1a69
source_commit: 340f1dd
model: claude-opus-5
---

# 5. El juez

El capítulo 4 terminaba con una regla: como máximo un check juzgado, muestreado, con una tolerancia medida. Este capítulo trata sobre la palabra *medida*: qué pasa cuando te la saltas, y el procedimiento que sustituye la conjetura por un número. Las medidas provienen de los seis runs que publica el [juez de la newsletter](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/fixtures/README.md), y puedes recalcularlas.

## Dos ruidos, no uno

Hay dos lugares en los que un modelo puede cambiar de opinión, y cada uno requiere un remedio distinto.

**El sistema bajo prueba** es un modelo. Pregúntale lo mismo dos veces y puede responder de forma distinta. En el proyecto de la newsletter el juez *es* el sistema: puntúa artículos. Ejecuta la suite dos veces, con quince minutos de diferencia y sin cambiar nada, y un artículo de cada veintiuno cambia de veredicto.

**El juez** —el modelo que usas dentro de un check para evaluar una salida— también es un modelo, y también cambia. Si tu rúbrica pregunta «¿es educada esta respuesta?», el juez puede decir 0.8 hoy y 0.7 mañana sobre la misma respuesta.

El remedio para el primero es preguntar al *sistema* varias veces por caso y combinar. El remedio para el segundo es preguntar al *juez* varias veces por salida y combinar. Se parecen y no son lo mismo: el primero mide cuán estable es tu producto; el segundo, cuán estable es tu regla de medir. Confundirlos significa arreglar la regla cuando lo que oscila es el producto, o al revés. Decide cuál de los dos estás mirando antes de tocar nada.

## Lo que te cuesta una sola muestra

Un veredicto a partir de una sola muestra es una sola tirada. En un caso que al juez le resulta fácil, la tirada casi siempre cae del mismo lado; en uno límite es cara o cruz, y cualquier conjunto real de casos tiene unos cuantos casos límite. Con un check binario y sin tolerancia, cada tirada que cae del otro lado es una regresión: la comparación se pone en rojo, la CI falla, alguien investiga y no había nada mal.

Bastan unas pocas de esas para que un equipo deje de leer las alarmas. Ese es el coste real de una sola muestra: no el número equivocado, sino el momento en que el rojo deja de significar algo.

## Muestreo

La solución es preguntar más de una vez y combinar. La suite de la newsletter pregunta cinco veces por caso, lo que convierte el veredicto binario en una fracción —0, 0.2, 0.4, 0.6, 0.8 o 1— y el check en «el juez coincide con el lector en al menos tres votos de cinco».

El muestreo trae tres preguntas, y las respuestas importan más que el número cinco:

**¿Combinar cómo?** La puntuación es la media de las muestras. Pero la cantidad interesante es el *acuerdo*: cuántas muestras comparten el veredicto mayoritario. Toma unas puntuaciones inventadas: tres muestras de 0.80, 0.85 y 0.99 difieren muchísimo y coinciden por completo en el veredicto; tres de 0.69, 0.71 y 0.70 están a menos de dos puntos unas de otras y se reparten dos a uno con un umbral de 0.70. El acuerdo ve el segundo caso; la media no.

**¿Y si no logran ponerse de acuerdo?** Entonces el juicio no era posible, y la respuesta honesta es *no se pudo juzgar*: un tercer estado, ni aprobado ni fallido. Un caso cuyas muestras se reparten tres a dos no es una regresión ni un éxito; es un caso que el juez no puede decidir, y una referencia construida sobre él sería una referencia a una moneda al aire. Fija un acuerdo mínimo por debajo del cual el veredicto es un error, y niégate a promover un run que contenga alguno, pero sitúalo donde pueda dispararse. Con cinco muestras la mayoría es siempre de al menos tres, así que `"3/5"` nunca rechaza una votación en la que se juzgaron todas las muestras; el mínimo que detecta un reparto de tres a dos es `"4/5"`.

**Escribe las fracciones como fracciones.** «Dos de tres» escrito como `0.67` es una trampa: ⅔ es 0.666…, que está *por debajo* de 0.67, y todo caso con un voto discrepante de tres se convierte en un error. `"2/3"` dice lo que quieres decir y no puede desviarse por un redondeo; la suite de la newsletter escribe `"3/5"`.

## Medir la tolerancia

La tolerancia es el tamaño de cambio que aceptas ignorar como ruido. Todo el mundo la elige a ojo; casi todo el mundo la elige mal, porque el ruido de un juez no se puede adivinar desde fuera. Sí se puede medir, en tres runs:

1. Congela todo: prompt, modelo, casos.
2. Ejecuta la suite tres veces.
3. Para cada caso, mira la mayor diferencia entre dos runs cualesquiera.
4. La tolerancia es esa diferencia mayor, más un pequeño margen.
5. Si ese número es tan grande como las diferencias que quieres *detectar*, para: el check es demasiado ruidoso para servir de gate. Muestrea más, o cambia el check; no amplíes la tolerancia hasta que se lo trague todo.

Esto es lo que se ve al aplicarlo al juez de la newsletter: seis runs, cinco muestras por caso, con los mismos prompts, los mismos casos y la misma configuración. Cada celda indica cuántas de las cinco muestras coincidieron con el lector; las horas están en UTC.

| caso | 1 sep 12:29 | 1 sep 12:44 | 3 sep 06:14 | 3 sep 06:18 | 3 sep 06:24 | 3 sep 06:30 |
|---|---|---|---|---|---|---|
| evals-skills-for-coding-agents | 2 | 5 | 5 | 2 | 5 | 5 |
| more-than-just-code-review | 4 | 5 | 5 | 2 | 5 | 5 |
| controlling-reasoning-effort-in-llms | 5 | 4 | 3 | 5 | 5 | 4 |
| recent-developments-in-llm-architectures | 5 | 4 | 5 | 3 | 5 | 4 |
| los otros diecisiete | con una diferencia máxima de dos votos, y la mayoría nunca cambia | | | | | |

Dos casos oscilaron tres votos de cinco sobre un sistema que no había cambiado, y en cualquier run dado entre dos y seis de los veintiún casos quedaron divididos. En un caso aislado, entonces, se aplica el paso 5: una tolerancia que absorbiera tres votos sería tan amplia como cualquier cambio que valga la pena detectar en ese caso. La suite declara dos votos por caso y deja que una oscilación de tres votos se vea. La tabla por caso sigue valiendo la pena: te dice exactamente en qué casos el juez no está seguro.

## El agregado es más tranquilo que los casos

Los mismos runs mostraron algo que cambia sobre qué conviene poner un umbral. Mientras que casos aislados saltaban tres votos de cinco, el número de artículos en los que juez y lector coincidieron fue 15, 16, 16, 14, 16 y 16 de 21 a lo largo de los seis runs: nunca con más de dos de diferencia.

Ese es el patrón general, y es la razón por la que una suite con casos etiquetados debería aplicar el gate sobre un agregado —precision, accuracy, recall— y usar los veredictos por caso para el diagnóstico. Un umbral del 60% de acuerdo no se habría disparado en ninguno de los seis. Frente a la referencia que guarda el proyecto, el check por caso, con sus dos votos de tolerancia, se puso en rojo en dos de los otros cinco.

## El prompt del juez es un prompt

Se desvía por las mismas razones que el tuyo y merece el mismo trato: un archivo, versionado, registrado con cada run. Cuando un check juzgado empieza a fallar, la primera pregunta no es «¿empeoró el sistema?» sino «¿cambió la regla de medir?», y si el prompt del juez es una cadena dentro de alguna función, no puedes responderla.

Dos hábitos menores. Primero, en el prompt del juez pon la instrucción antes de la salida, y etiqueta la salida con claridad; un juez que lee una instrucción después del texto que se le pidió juzgar a veces juzgará la instrucción. Segundo, cuando pruebes tu suite con un juez falso —y deberías hacerlo—, construye el falso a partir de una respuesta *real*, no a partir de lo que crees que parece la respuesta. Un falso escrito a partir del código confirma el código; en el proyecto de la newsletter [se encontró un coste contabilizado 384× por debajo](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/README.md#the-fake-judge-and-ci) con todas las pruebas en verde, porque el falso y el código compartían la misma suposición equivocada sobre la forma de la API.

## Hazlo hoy

1. Decide qué ruido estás mirando: el del sistema o el del juez.
2. Muestréalo —la suite de la newsletter pregunta cinco veces— y fija un acuerdo mínimo por debajo del cual el veredicto sea *no se pudo juzgar*.
3. Congela todo y ejecuta tres veces. Lee la mayor diferencia por caso. Esa es tu tolerancia, o tu señal para muestrear más.
4. Si tienes etiquetas, pon el gate sobre el agregado.
5. Mueve el prompt del juez a un archivo junto al del sistema, y registra ambos con cada run.

El próximo capítulo trata de qué hacer cuando los números se estabilizan: el run que apruebas, y por qué debería ser la mediana de varios y no el primero que salga en verde.
