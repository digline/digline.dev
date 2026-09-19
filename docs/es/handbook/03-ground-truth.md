---
seo_title: Verdad de referencia cuando nadie te la da
lang: es
translation_of: handbook/03-ground-truth.md
description: 'De dónde sale la respuesta esperada cuando no hay datos etiquetados: congela la entrada, cubre formas, captura el desacuerdo y diseña la funcionalidad para que un juicio tenga a qué agarrarse.'
search:
  exclude: true
source: handbook/03-ground-truth.md
source_sha: 74e7f304be5e
source_commit: d778c40
model: claude-opus-5
---

# 3. Verdad de referencia: cuando nadie te la da

El capítulo 2 decía que había que encontrar el punto donde una persona corrige al modelo. Este capítulo trata del caso en que ese punto no existe — o existe y registra algo distinto de lo que crees. Está escrito a partir de tres sistemas: el [juez de la newsletter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f), cuyo código y casos son públicos pero cuyo registro de cada elemento que juzgó no lo es — las cifras de abajo se leen de ese registro, tal como lo muestra [Bad evals, my own](../../blog/bad-evals-my-own.md); un segundo juez del mismo autor que elige hilos de Reddit que vale la pena responder (privado, descrito en la misma entrada); y una funcionalidad de producto descrita solo en su forma. Cada uno falló al producir verdad de referencia de una manera distinta.

## Congela la entrada, no el mundo

Un caso es una fotografía de una situación. Que los datos de mañana sean distintos es irrelevante: estás probando qué hace el sistema ante esa situación, no los datos.

Por eso la entrada va entera dentro del caso, tal como la vio el modelo ese día. Volver a descargar un artículo hoy pondría una entrada distinta bajo una etiqueta antigua. El proyecto de la newsletter guarda el resumen que juzgó — pero solo para los elementos que mostró a su lector, así que 144 elementos que juzgó y nunca mostró tienen puntuación y no tienen entrada. Aun estando etiquetados, no se podrían reproducir.

## Cubre formas, no muestrees

La manera obvia de obtener casos es exportar todos los registros etiquetados. El juez de Reddit lo hizo el 2026-09-11 y obtuvo 144 casos. 109 de ellos eran hilos que el lector ignoró y el juez descartó: la misma mañana corriente, una y otra vez. Accuracy sobre ese conjunto fue 0.85. Precision sobre el único veredicto que importaba fue 0.52. El volumen favorecía a los días fáciles y no decía nada de los difíciles.

Elige los casos por su forma: la entrada saturada, la vacía, el elemento urgente sepultado bajo el ruido, el campo que falta, dos prioridades que chocan. Esa lista no es un resultado. El día corriente es una de las formas, y el capítulo 2 tiene razón en que debe estar — como forma, no como el sedimento de todas las mañanas.

## Una etiqueta no es un juicio

El juez de Reddit preguntaba a su lector, cada mañana, qué había hecho con cada hilo: comentar, votar a favor o ignorar. `ignored` se convirtió en `skip` en la suite. Luego el lector miró nueve hilos que había ignorado y que el juez había marcado como `comment`, y descubrió que en al menos cinco el juez tenía razón según sus propias reglas. Los había ignorado porque era el cuarto hilo de esa mañana, o porque ya había comentado dos veces en ese foro ese día.

Así que `ignored` significaba *el juez se equivocó* y *no había tiempo*, y cada caso construido sobre esa etiqueta era una lectura de una respuesta que nunca decía cuál de las dos. **No la reinterpretes después** — por fecha, por la confianza del juez, por lo que seguramente quisiste decir. Eso es inventarse un valor esperado en nombre propio. Los registros antiguos siguen siendo ambiguos, y de ellos no se acuña ningún caso nuevo.

La corrección está en el teclado. La tecla que vacía la lista de la mañana, sea cual sea, tiene que escribir *deferred*, el valor que no afirma nada, no *declined*. Si no, la etiqueta ambigua vuelve con otro nombre en una sola mañana. Los negativos escritos antes de la corrección no se pueden recuperar.

Esa división no elimina la ambigüedad, porque `declined` sigue preguntando qué *hiciste*. Un hilo que se dejó pasar porque el lector ya había comentado dos veces en ese foro sigue siendo un `declined`, sigue siendo un negativo. Eliminarlo exige una pregunta sobre la regla — no *¿comentaste?* sino *¿esto debería haber sido un comentario?* — y ninguno de los dos jueces la hace.

## El desacuerdo es el acontecimiento

Releer salidas buenas no te enseña nada y te convence de mucho. El único momento que vale la pena capturar es aquel en que una persona habría respondido de otra forma que el modelo. Ninguno de los dos jueces hace eso todavía: ambos exportan todas las etiquetas explícitas, acuerdos incluidos.

**El proyecto de la newsletter es el contraejemplo**, y resulta más útil que un éxito. A su lector se le muestran los elementos que el juez puntuó con 4 o 5, rellenados hasta cinco, y se le pregunta *¿cuáles te interesan? (enter = ninguno)*. La única respuesta explícita es *sí*, y solo se puede dar a elementos que el juez ya eligió. Los elementos no mostrados no tienen etiqueta; 265 de 446 ni siquiera se puntuaron. Enter es ambiguo. La única vía hacia un desacuerdo — marcar un elemento de relleno con puntuación baja — había estado abierta dieciséis veces a fecha de 6 de septiembre, y se tomó cero veces. El método no produce **ningún desacuerdo capturable**, no porque el lector nunca discrepara, sino porque nunca preguntó allí donde podía hacerlo.

La verdad de referencia tiene que ser un subproducto del trabajo que la persona ya hace. Los dos jueces preguntan al final de una mañana que el lector iba a tener de todas formas; una pregunta que es un comando aparte para ejecutar más tarde es una tarea pesada. En un producto la persona no eres tú, que es el caso difícil, y aquí eso no se ha resuelto.

## Cuando la selección nunca fue un dato

El tercer sistema tiene la forma más común de funcionalidad con LLM en producción, y lo que sigue se leyó de su código, no se obtuvo ejecutándolo. Un producto escribe a cada usuario un resumen matutino. El código arma un contexto y lo pasa a una sola llamada al modelo. El modelo decide qué elementos mencionar, en qué orden, con qué razonamiento, y si decir algo siquiera.

La respuesta es prosa con enlaces dentro. Nada la analiza ni la valida. Un elemento solo es identificable si el modelo lo envolvió en un enlace con un id, y nada comprueba que ese id exista en la entrada.

En los dos jueces las etiquetas eran ambiguas. Aquí **la selección solo existe dentro de la prosa**. No hay nada sobre lo que afirmar, ni nada a lo que pudiera agarrarse el juicio de un usuario: un botón de valoración no tendría ningún objeto al que apuntar. Dos cosas corrientes lo empeoran. Una llamada al modelo fallida y un auténtico «nada que reportar» guardan la misma fila — una ausencia disfrazada de respuesta. Y algunas de las consultas que construyen el contexto toman N filas sin ordenarlas, así que qué elementos llegan al modelo depende de la base de datos: un run y otro sobre los mismos datos pueden diferir sin que el modelo cambie de opinión, y no hay ninguna entrada que congelar.

La funcionalidad funciona, y nada de esto se ve en la revisión de código. Simplemente no se puede evaluar. **Que tu verdad de referencia se pueda recoger o no se decide cuando escribes la funcionalidad**, no después. Un sistema que emite su decisión como una estructura — los elementos elegidos, en orden, con sus ids — se puede comprobar de forma determinista y puede llevar el juicio de una persona. Uno que solo emite prosa no puede, le añadas lo que le añadas después.

La corrección es una forma: emite primero la selección; valida sus ids contra la entrada; guarda un fallo como un fallo; deja que la prosa sea una representación de la selección.

## Lo que puedes afirmar entonces

Con la selección como dato, la mayor parte de lo que importa es estable en cualquier día posible y no necesita modelo: todos los ids están en la entrada, así que nada se inventa y nada procede de los datos de otro usuario; el elemento que debe aparecer aparece; una entrada vacía da una selección vacía. Solo el orden — ¿está lo urgente primero? — necesita un juez. Ningún check de los anteriores se ha ejecutado todavía sobre ese sistema; son lo que la estructura hace posible.

## Crecimiento, y el límite honesto

Empieza con unas pocas formas elegidas. Deja que cada fallo en producción se convierta en un caso, y no borres ninguno: un caso que encontró un defecto es un muro que sostiene, y quitarlo es la única manera de averiguar qué sostenía. El exportador del proyecto de la newsletter hace lo contrario: regenera su archivo entero.

Veinte casos no te dicen que el sistema sea correcto. Te dicen que no ha empeorado en veinte situaciones que alguien juzgó representativas. Un gate de regresión, no una demostración.

## Hazlo hoy

1. Averigua dónde vive la decisión de tu funcionalidad. Si solo está en la prosa, cambia la salida antes de escribir un solo caso. Si todavía no puedes cambiarla, no puedes evaluar la funcionalidad. Eso ya es un hallazgo en sí mismo, y lo que hay que hacer hoy es registrar el contexto armado y la respuesta, porque mañana ya no estarán.
2. Comprueba que tus entradas sean deterministas. Una consulta que trunca sin ordenar es el primer error.
3. Fíjate en la respuesta que dan tus usuarios al no hacer nada. Asegúrate de que no afirme nada.
4. Pregunta por la regla, no por el comportamiento, y solo allí donde la persona habría respondido de otra forma.
5. Elige cinco formas. Escribe un caso para cada una.

El siguiente capítulo trata de qué comprobar en esos casos — y de por qué los checks que no necesitan ningún modelo van primero.
