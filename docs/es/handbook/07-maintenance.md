---
seo_title: 'Mantenimiento: ejecutar la suite como práctica'
lang: es
translation_of: handbook/07-maintenance.md
description: Cuándo debe ejecutarse una suite de evaluación, qué debería hacerte mirar y qué hacer la mañana en que CI se pone en rojo y no cambiaste absolutamente nada.
search:
  exclude: true
source: handbook/07-maintenance.md
source_sha: 0117d185cb00
source_commit: d52f054
model: claude-opus-5
---

# 7. Mantenimiento

Una suite que se ejecuta una vez es una demo. Este capítulo trata de la parte que la convierte en una práctica: cuándo se ejecuta, qué debería hacerte mirar y qué hacer la mañana en que se pone en rojo y no cambiaste nada.

## Los cinco disparadores

Algo ocurre; la suite se ejecuta; la comparación dice si empeoró. Hay cinco «algos» distintos, y requieren respuestas distintas.

### 1. Cambiaste algo

El prompt, el modelo, la recuperación, el código alrededor de la llamada. Este es el disparador que esperas, y del que se ocupa CI: cada pull request ejecuta la suite y compara con la referencia. El rojo bloquea el merge; las líneas debajo del titular dicen qué casos se movieron y cuánto; el diff del prompt está justo al lado.

La respuesta es la de siempre: mira los casos que empeoraron, decide si el cambio vale la pena, corrige o acepta. La única regla: una comparación en rojo nunca se arregla ampliando la tolerancia ni bajando el umbral. Eso son cambios de reglas, y los cambios de reglas entran por la puerta principal (capítulo 6), no por el arreglo de una build que falla.

### 2. El proveedor cambió algo

Nada se movió en tu repositorio. Sí lo hizo el modelo detrás de la API: una actualización, una versión marcada como obsoleta, un alias que ahora apunta a otro sitio, un cambio en el comportamiento por defecto. Tu historial de commits dice «sin cambios». La comparación, si se ejecutó, dice cuatro casos peor.

*Si se ejecutó* es la clave. CI se ejecuta con los pushes, y nadie hizo push. Este disparador necesita una programación: un trabajo nocturno o semanal que ejecute la suite contra la referencia sin ningún cambio de tu parte. Un resultado en rojo con un diff limpio es la firma del proveedor: el único fallo que ninguna revisión de código, ninguna prueba de tu propio código y ningún cuidado pueden detectar, y el que la mayoría de los equipos descubre por los usuarios.

En el [proyecto de la newsletter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) esto es un workflow semanal que ejecuta el juez real y compara. Cuesta unos siete céntimos a la semana. Es el seguro más barato del repositorio.

La respuesta es distinta de la del disparador 1: tú no hiciste esto, así que no puedes deshacerlo. Opciones, en orden: fijar la versión del modelo si el proveedor lo permite y estabas usando un alias; ajustar el prompt al nuevo comportamiento y promocionar cuando hayas recuperado el nivel; o aceptar el nuevo comportamiento como referencia, deliberadamente, con la promoción como constancia de que lo viste y decidiste.

### 3. Un caso real salió mal

Un usuario lo reporta. Un log lo muestra. Alguien del equipo nota una respuesta que no debería haber ocurrido. La suite no lo detectó porque la suite no tenía esa entrada.

La respuesta es el hábito del capítulo 2, y es la frase más importante de este manual: **un fallo visto, un caso escrito, el mismo día.** Antes de tocar el prompt, guarda la entrada y la respuesta correcta como un caso. Ejecuta la suite: el caso nuevo falla, y eso es correcto; aparece como *nuevo*, sin nada con qué compararlo. Luego arregla el prompt. Luego vuelve a ejecutar: el caso nuevo pasa, y los otros veinte te dicen si el arreglo rompió algo. Luego promociona.

Sáltate el primer paso y habrás parcheado una entrada sin aprender nada. Hazlo y el fallo se convierte en protección permanente.

### 4. Las reglas se movieron

Alguien subió un umbral, apretó una tolerancia, añadió un check, quitó otro. La comparación se sigue ejecutando, y te dice que la configuración difiere de la referencia, de modo que un caso que pasó de aprobar a fallar se lee como un cambio de reglas, no como un cambio del modelo. La promoción se rechaza hasta que la referencia se restablezca bajo las nuevas reglas.

La respuesta es corta: ejecuta con las nuevas reglas, mira, promociona. El sentido del rechazo es que un cambio de reglas nunca es invisible: siempre produce una promoción que alguien puede ver en la revisión.

### 5. Un caso dejó de poder juzgarse

Un check devuelve *no se pudo juzgar*: las muestras del juez se dividieron, la salida tenía la forma equivocada, el proveedor superó el tiempo de espera. No es ni aprobado ni fallo, y bloquea la promoción.

Dos respuestas, y solo dos. Si el caso es genuinamente ambiguo —las muestras se dividieron porque una persona también se dividiría—, suspéndelo, con una razón escrita, para que siga en la suite como un hueco visible en vez de desaparecer en silencio. Si la culpa es del check —forma equivocada, prompt equivocado en el juez—, arregla el check. Lo que no debes hacer es bajar el acuerdo mínimo hasta que la división se convierta en aprobado: eso convierte *desconocido* en *correcto* sin que nadie lo haya decidido.

## Los diez minutos semanales

Los disparadores son reactivos. La práctica que mantiene honesta a una suite es un acto pequeño, aburrido y programado:

1. Abre la comparación del run programado. Esté en verde o en rojo, lee los agregados —precision, accuracy— frente a la referencia. Dos números, treinta segundos.
2. Mira la lista de casos que se movieron, aunque sea dentro de la tolerancia. Un caso que se desvía un poco cada semana te está diciendo algo antes de cruzar la línea.
3. Revisa el número de casos. Si no ha crecido desde la semana pasada, pregúntate si no salió nada mal en producción o si nadie lo anotó. Suele ser lo segundo.
4. Revisa la antigüedad de la referencia. Una referencia de hace cuatro meses sobre una funcionalidad que cambió dos veces es una referencia que nadie volvió a aprobar.
5. Si algo de los puntos 1 a 4 requiere una decisión, tómala ahora —promocionar, suspender, añadir un caso— y haz commit.

Diez minutos, una vez por semana, a cargo de quien sea responsable de la funcionalidad. Sáltatelo un mes y la suite sigue ahí; sáltatelo un trimestre y vuelve a ser una demo.

## Lo que empeora sin que te des cuenta

Tres fallos lentos que ningún disparador detecta, porque cada paso es demasiado pequeño para alarmar:

**Deriva del coste.** Cada edición del prompt añade una frase; nadie quita ninguna. El check de presupuesto se puntúa de forma gradual precisamente para que un coste *dentro* del límite siga apareciendo como un cambio frente a la referencia. Vigila el número, no solo el color.

**Casos que se pudren.** Un caso cuya respuesta esperada era correcta en marzo puede ser incorrecta en septiembre porque el producto cambió: el plazo de devolución se movió, la taxonomía ganó una categoría. Una suite con casos podridos falla por razones equivocadas y enseña a la gente a ignorar el rojo. Cuando un caso falla y la salida parece correcta, revisa el caso antes que el prompt.

**Deriva de la referencia por promoción.** Cada promoción acepta una pequeña pérdida: «un caso peor, pero el diff queda mejor». Diez promociones después, la referencia está diez pequeñas pérdidas por debajo de donde empezaste, y todas y cada una de las comparaciones estaban en verde. La defensa es el agregado en el archivo: compara la precision de este mes no con la referencia de la semana pasada, sino con la primera que aprobaste. Git la tiene.

## Hazlo hoy

1. Añade el run programado —con una vez por semana basta— con el juez real. Que sea el único trabajo que se ejecuta cuando nadie hizo push.
2. Pon la revisión de diez minutos en el calendario, a cargo de la persona responsable de la funcionalidad.
3. Escribe la regla de «un fallo, un caso» donde el equipo la vea: el README de la suite, la plantilla de pull request, el tema del canal.
4. La próxima vez que la comparación esté en rojo y no hayas cambiado nada, no toques la tolerancia. Lee el diff. Está vacío. Eso es el proveedor, y ahora ya sabes qué aspecto tiene.

El último capítulo es para los equipos que construyen funcionalidades con LLM para otros: donde la misma suite se convierte en la respuesta a una pregunta que hará el cliente, y donde parte de lo que contiene nunca debe salir de su perímetro.
