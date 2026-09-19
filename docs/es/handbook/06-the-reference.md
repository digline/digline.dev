---
seo_title: 'La referencia: un umbral no es un punto de comparación'
lang: es
translation_of: handbook/06-the-reference.md
description: Una puntuación puede caer mucho y aun así pasar su umbral los dos días. Lo que lo detecta es el único número que anotas y frente al cual aceptas ser medido.
search:
  exclude: true
source: handbook/06-the-reference.md
source_sha: c46f6b87214f
source_commit: 356a3c8
model: claude-opus-5
---

# 6. La referencia

Todo lo anterior produce números. Este capítulo trata del número que importa más que los demás: el que anotas y frente al cual aceptas ser medido.

## Un umbral no es una referencia

La mayoría de los equipos que siquiera prueban una función con LLM tiene un umbral: la puntuación debe superar 0.7. Responde a una pregunta — *¿es aceptable?* — y es ciego a la otra — *¿es lo que era?*

Aquí está con números inventados. Una función que obtuvo 0.91 en el lanzamiento y 0.78 hoy pasa el umbral los dos días. Nada se pone en rojo. Y sin embargo algo cambió en trece puntos, y quien la usa notó el cambio antes que cualquier prueba. Para verlo tienes que haber anotado el 0.91. Eso es la referencia: un run de tu suite que miraste, diste por bueno y registraste — las puntuaciones, el prompt que las produjo, el commit, la fecha — para que cada run posterior pueda compararse con él en lugar de con una línea.

El umbral dice dónde está el suelo. La referencia dice dónde estabas parado. Necesitas los dos, y el segundo es el que casi nadie guarda.

## Qué contiene una referencia

Un archivo, en el repositorio, junto al código. En el [proyecto de la newsletter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) es [`.digline/alessandro/baselines/brief-judge.json`](https://github.com/digline/brief/blob/9507bb06f7dd90a4b6a624dbe77725e50819a02f/.digline/alessandro/baselines/brief-judge.json), incluido en un commit como cualquier otro archivo. Dentro:

- **Los veredictos** — cada check en cada caso, con su puntuación, umbral y tolerancia. No un resumen: la tabla completa, para que una comparación posterior pueda decir *qué* caso se movió.
- **Los agregados**, si los casos están etiquetados — precision 0.667 y accuracy 0.762, diez de quince y dieciséis de veintiuno — con los recuentos que los produjeron.
- **El texto del prompt** que produjo el run, literal, con su hash. No una referencia a un archivo que puede haber cambiado desde entonces; el texto mismo, congelado.
- **El commit** en el que estaba el código, y si el árbol de trabajo estaba limpio.
- **La configuración** de la suite — qué checks, qué umbrales — como un hash, para que una comparación contra una suite con reglas distintas se rechace en vez de carecer de sentido en silencio.

Del hecho de que el prompt esté *dentro* del archivo se siguen dos cosas. Primero, la referencia es reproducible aunque nunca hayas hecho commit del prompt por separado — una situación común durante un día de experimentos. Segundo, cuando un run posterior difiere, la comparación puede mostrar el diff del prompt justo al lado del diff de las puntuaciones: *cambiaste estas tres líneas; estos dos casos se movieron.* Ese emparejamiento es lo más útil que puede mostrar una comparación, y solo existe si el prompt viaja con el run.

## Promover: un acto deliberado

Un run no se convierte en la referencia por ser el último ni por estar en verde. Alguien lo promueve. Eso es una decisión — *esto es lo que considero un buen resultado, acepto que me midan con ello* — y debería sentirse como tal. En el proyecto de la newsletter es un comando, `digline promote`, y el resultado es un commit con un archivo dentro que un revisor puede leer.

Tres cosas que una promoción debería rechazar, porque cada una convertiría la referencia en una mentira:

- Un run producido con una **configuración distinta** de la de la suite actual: sus números se midieron con otras reglas.
- Un run con **algún check en error** — un *no se pudo juzgar* — porque una referencia es un estado aprobado y un error no es un estado.
- Un run de un **tenant distinto** de aquel para el que estás promoviendo, si tu suite tiene perímetros (capítulo 8).

Si tu herramienta no las rechaza, recházalas tú. Una referencia en la que no puedes confiar es peor que ninguna, porque convierte cada comparación posterior en una discusión.

## No el primer run en verde

El primer run que pasa es el más tentador de promover y el equivocado. Acabas de leer el capítulo 5: el juez oscila, y un único run es una sola muestra. Promuévelo y la referencia registra la muestra afortunada; cada run posterior se compara con la afortunada y parece peor de lo que es.

Una sola muestra puede caer de cualquier lado. Tres runs de la suite de la newsletter el 3 de septiembre, con once minutos de diferencia y sin cambiar nada, coincidieron con el lector en 16, 14 y 16 artículos de 21. Una referencia tomada del segundo de los tres presentaría los otros dos como dos artículos mejores — una *mejora* que nadie hizo.

El procedimiento que lo sustituye cuesta tres runs:

1. Ejecuta tres veces sobre el sistema congelado.
2. Mira los casos que difieren entre runs. Para cada uno, anota qué run contiene el valor intermedio.
3. Promueve el run que queda en medio con más frecuencia. Deshaz los empates por coste.

Ese run es la referencia. Registra el comportamiento típico, no el mejor ni el peor, y una comparación posterior contra él significa lo que dice.

## Qué cambia la referencia y qué no

**Un prompt mejor.** Lo cambiaste, la comparación muestra dos casos que mejoraron y ninguno que empeoró, el diff te gusta. Promueve. La referencia antigua queda en el historial de git; la nueva lleva el nuevo texto del prompt.

**Un umbral más alto.** Decidiste que el suelo debía ser 0.70, no 0.60. Eso es un cambio de configuración: la comparación sigue funcionando — y te dice que el umbral se movió, de modo que el vuelco se lee como un cambio de regla y no como un cambio de modelo — pero la promoción se rechaza hasta que la configuración coincida. Cambia la regla, ejecuta, promueve: tres pasos, todos visibles en un pull request.

**Un caso nuevo.** Añadir un caso no invalida la referencia: aparece como *nuevo* en la siguiente comparación, sin contraparte con la que compararse. Una vez que lo has mirado, promueve y pasa a formar parte del registro.

**Un cambio de modelo.** El proveedor actualizó el modelo, nada cambió en tu código, la comparación muestra cuatro casos peores. Este es exactamente el caso para el que existe la referencia. No promuevas el run peor. Investiga, ajusta el prompt si hace falta y promueve cuando hayas vuelto — o aceptas el nuevo comportamiento de forma deliberada, y la promoción es el registro de que lo hiciste.

**La referencia no cambia porque haya pasado el tiempo.** Una referencia de marzo es válida en septiembre si no se promovió nada en medio. Su antigüedad es información, no un defecto: dice que nadie ha aprobado nada desde marzo, lo cual o está bien o es un hallazgo.

## Dónde vive la referencia

En el repositorio, con commit, revisada. No en un servidor, no en un dashboard, no en la memoria de quien la ejecutó. Tres razones que no son cuestión de preferencia:

Se le puede hacer **diff**. Dos referencias, dos archivos, `git diff`. Cada número que se movió, cada línea de prompt que cambió, en una sola vista.

Se puede **revisar**. Una promoción es un pull request. Alguien distinto del autor ve los números y el prompt antes de que se conviertan en el estándar.

Se puede **mostrar**. Cuando un cliente — o un auditor, o tu propio equipo dentro de seis meses — pregunta qué se probó y se aprobó y cuándo, la respuesta es un archivo con un hash de commit y una fecha, no una captura de pantalla.

## Hazlo hoy

1. Congela tu prompt y tus casos. Ejecuta la suite tres veces.
2. Elige el run mediano con el procedimiento de arriba. Promuévelo. Haz commit del archivo.
3. Abre el archivo. Confirma que el texto del prompt está dentro, literal. Si tu herramienta no lo pone ahí, ponlo tú — una copia del prompt junto a la referencia, en el mismo commit.
4. Haz un cambio pequeño en el prompt. Ejecuta. Compara. Lee el diff del prompt al lado del diff de las puntuaciones. Esa vista es la razón de todo lo que hay en este capítulo.

El siguiente capítulo trata de mantener esto vivo: cuándo ejecutar, qué debería hacerte mirar y qué hacer la mañana en que la comparación está en rojo y tú no cambiaste nada.
