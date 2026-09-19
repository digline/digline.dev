---
seo_title: 'Checks: primero los deterministas, el juez al final'
lang: es
translation_of: handbook/04-checks.md
description: 'Cómo convertir la salida de un LLM en un veredicto y la regla que más tiempo ahorra en evaluación: usa un modelo para juzgar solo lo que nada más puede juzgar.'
search:
  exclude: true
source: handbook/04-checks.md
source_sha: bf59e8257331
source_commit: d778c40
model: claude-opus-5
---

# 4. Checks: primero los deterministas, el juez al final

Un caso dice qué entra y qué sabes de la respuesta correcta. Un check es la forma de convertir una salida en un veredicto. Este capítulo trata de cómo elegir checks — y de una regla que suena demasiado simple para importar y ahorra más tiempo que cualquier otra cosa aquí: **usa un modelo para juzgar solo lo que nada más puede juzgar.**

## Dos tipos de check

**Los checks deterministas** no necesitan ningún modelo. Miran la salida y responden una pregunta de forma mecánica: ¿contiene esta frase?, ¿es JSON válido?, ¿cumple este esquema?, ¿tiene menos de 200 palabras?, ¿cuesta menos de un céntimo?, ¿contiene un código fiscal? La misma salida, el mismo veredicto, siempre, al instante y gratis.

**Los checks con juez** piden a un modelo que evalúe la salida: ¿es educada esta respuesta?, ¿responde a la pregunta?, ¿está respaldada por los documentos recuperados?, ¿es mejor que la versión anterior? Pueden expresar cosas que ninguna expresión regular puede. También son una segunda distribución sobre la primera — el juez también extrae muestras — y cada check con juez hereda el ruido, el coste y la latencia de una llamada a un modelo.

La mayoría de los equipos recurre primero al juez, porque es la parte interesante. Este capítulo defiende el orden contrario.

## Por qué primero los deterministas

Piensa en el [juez de la newsletter](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/suite.py). Su salida es un objeto JSON pequeño: una puntuación del 1 al 5 y una razón de una frase. Antes de preguntar a ningún modelo si la puntuación es *buena*, se pueden comprobar tres cosas sin modelo alguno:

- ¿Es la salida JSON válido con exactamente esos dos campos? (`JsonSchema`)
- ¿Es la puntuación un entero entre 1 y 5? (el mismo esquema)
- ¿Costó la llamada menos que el presupuesto? (`CostBudget`)

Esos tres detectan los fallos que de verdad ocurren en producción: que el modelo envuelva el JSON en prosa, que el modelo se invente una puntuación de 0, que el prompt crezca hasta que cada llamada cueste el triple que antes. Los detectan gratis, de forma determinista, en cada run. Y cuando uno falla, el error no es ambiguo: nadie discute un «no es JSON válido».

Solo después viene la pregunta que necesita un juez —«¿coincide esta puntuación con lo que quería el lector?»— y en el proyecto de la newsletter hasta esa resultó responderse sin modelo, porque están registradas las propias marcas del lector. El check son catorce líneas de Python: *¿dijo el juez ≥4 exactamente cuando el lector lo marcó?* Sin un segundo modelo, sin ruido procedente del propio check.

La forma general: **cada check que puedas hacer determinista es una fuente de ruido menos entre tú y la respuesta.** Una suite con cinco checks deterministas y un juez tiene una señal ruidosa que calibrar. Una suite con seis jueces tiene seis.

## Qué detectan los deterministas

Un catálogo breve, según el fallo para el que existe cada uno:

| Fallo que has visto | Check |
|---|---|
| La respuesta olvidó la línea obligatoria (un aviso legal, una firma, una frase jurídica) | `Contains` |
| La respuesta mencionó algo que nunca debe mencionar (un competidor, un nombre interno, «como modelo de IA») | `NotContains` |
| La salida debía ser estructurada y volvió en prosa | `IsJson`, `JsonSchema` |
| Las respuestas se alargan cada semana, o tienen que caber en un canal | `Length` |
| La respuesta debe *parecerse* a una conocida, no ser idéntica | `Levenshtein`, gradual |
| La salida llegó a una persona y contenía un IBAN, un código fiscal, un correo electrónico | `PiiAbsent` |
| Un cambio en el prompt duplicó los tokens y nadie se dio cuenta hasta la factura | `CostBudget` |
| La funcionalidad está bien pero los usuarios esperan cuatro segundos | `LatencyBudget` |

Dos de ellos merecen un comentario. `PiiAbsent` es el que la gente se salta y luego lamenta: un LLM que tiene datos de clientes en su contexto, tarde o temprano, repetirá alguno en una salida donde no corresponde, y ningún juez detecta un IBAN válido con la fiabilidad de una suma de verificación. Y los presupuestos son graduales, no de aprobado/suspenso: un coste que sube poco a poco *dentro* del límite sigue apareciendo como un cambio respecto a la referencia, y así te das cuenta de que el prompt crece antes de que cruce el límite.

## Cuándo el juez es la herramienta adecuada

Hay preguntas que nada mecánico puede responder:

- *¿Es educada esta respuesta?* — no hay expresión regular para el tono.
- *¿Responde a la pregunta que se hizo?* — exige entender ambas.
- *¿Está toda afirmación de este resumen respaldada por la fuente?* — la pregunta central de cualquier sistema de recuperación.
- *¿Es esta reescritura mejor que el original?* — una preferencia, no una regla.

Para esas, un check con juez es la única opción, y tiene dos formas. Una **rúbrica**: describes el criterio en una frase y el juez devuelve una puntuación en [0, 1] y una razón. Y la **fidelidad**: el juez cuenta las afirmaciones de la salida y cuántas respalda el contexto proporcionado; el check divide. La segunda es la indicada para cualquier cosa que recupere documentos, y es más útil que una rúbrica porque produce un recuento con el que se puede discutir, no una impresión.

Uses la que uses, tres reglas, todas derivadas del mismo hecho: el juez es una distribución:

1. **El umbral y la tolerancia son obligatorios**, no valores por defecto. Un check con juez con un implícito «pasa cualquier cosa por encima de 0» está siempre en verde y no te dice nada. Fija el umbral donde está el sistema de forma medible; fija la tolerancia a partir del ruido medido (el capítulo 5 explica cómo).
2. **Extrae muestras.** Un juicio por caso es una sola muestra. Pregunta tres o cinco veces y combina los resultados, o te pasarás el mes siguiente persiguiendo regresiones que solo son el juez cambiando de opinión.
3. **Mantén el prompt del juez tan fijo como el de tu sistema.** Es un prompt. Deriva por las mismas razones. Debe vivir en un archivo, estar versionado y quedar registrado en cada run, igual que el prompt que se está probando.

## El juez es tuyo

Vale la pena decir una cosa con claridad, porque las herramientas difieren en esto: el juez es una función que tú proporcionas. Llama al modelo que elijas, de la forma que elijas, y la herramienta de evaluación solo compone la pregunta y lee la puntuación. Dos consecuencias. En las pruebas, inyectas un juez falso y todo check con juez se vuelve determinista. Y el razonamiento del juez, que cita la salida que juzgó, se escribe en el run, junto a la salida. La única llamada en la que interviene es la del propio juez, al modelo que elegiste; la herramienta no tiene un servidor propio al que enviarla. El capítulo 8 trata de cuándo ni siquiera ese run puede viajar.

## Cómo armar una suite

Para una primera suite, el patrón que ha resistido:

- **Un check estructural** sobre la forma de la salida. Detecta los fallos vergonzosos y no cuesta nada.
- **Uno o dos checks de contenido**: un `Contains` para la frase obligatoria, un `NotContains` para la prohibida, `PiiAbsent` si la salida llega a una persona.
- **Los presupuestos**, siempre, graduales.
- **Como mucho un check con juez**, con varias muestras, para lo que realmente necesita un juicio. Si te descubres queriendo tres, pregúntate si dos de ellos no podrían ser casos con respuesta conocida.

Cinco o seis checks sobre veinte casos. Se ejecuta en unos minutos, cuesta céntimos y ya es más de lo que tiene la inmensa mayoría de las funcionalidades con LLM en producción.

## Hazlo hoy

1. Enumera los últimos cinco fallos que produjo tu funcionalidad. Para cada uno, pregúntate: *¿habría podido detectarlo una expresión regular, un esquema o un contador?* La mayoría de las veces la respuesta es sí.
2. Escríbelos primero como checks deterministas. Ejecútalos sobre tus veinte casos. Algunos fallarán hoy mismo: de eso se trata.
3. Solo entonces escribe el único check con juez para la pregunta que de verdad necesita un modelo. Dale un umbral y una tolerancia. Extrae varias muestras.
4. Si un check con juez falla en un caso, mira la razón antes de mirar el prompt. A menudo el que está mal es el caso, no el sistema.

El capítulo siguiente trata de ese único check con juez: cuánto oscila, cómo medir la oscilación y cómo evitar que convierta cada martes en una falsa alarma.
