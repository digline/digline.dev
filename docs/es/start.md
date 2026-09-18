---
title: Empieza aquí
template: start.html
lang: es
translation_of: start.md
description: Qué es una regresión de LLM, por qué las pruebas habituales no la detectan y qué hace digline al respecto, en lenguaje sencillo.
search:
  exclude: true
source: start.md
source_sha: f1b884ed9bca
source_commit: 200f768
model: claude-opus-5
---

# Empieza aquí

Si ya sabes qué es una regresión silenciosa, ve directamente a la [Guía](../product/guide.md). Esta página es para todos los demás.

## El problema, contado en una historia

Tengo un script pequeño que cada mañana lee unos cientos de artículos sobre IA y le pide a un modelo de lenguaje que elija los cinco que merecen la pena. Funcionaba. Hasta que un día empezó a dejar fuera los buenos.

Nada se había caído. Ninguna prueba había fallado. El código era el mismo que la semana anterior. Lo que había cambiado era el *comportamiento* del modelo —un ajuste en el prompt por aquí, una actualización del modelo por allá— y el comportamiento no es algo que compruebe una prueba unitaria. El script seguía devolviendo cinco artículos. Solo que eran los cinco equivocados.

Eso es una **regresión de LLM**: tu sistema sigue ejecutándose, sigue respondiendo, sigue pasando sus pruebas y, sin hacer ruido, es peor de lo que era.

## Por qué tus pruebas no la ven

Las pruebas habituales comparan una salida con un valor esperado. Un modelo de lenguaje no te da un valor esperado. Hazle la misma pregunta dos veces y puedes obtener dos respuestas distintas, ambas aceptables. Así que los equipos o dejan de probar el comportamiento del modelo, o escriben una prueba que pasa hoy y no te dice nada sobre mañana.

Las preguntas prácticas resultan ser estas:

- ¿Comparado con *qué*? Necesitas una referencia: el comportamiento que aceptaste la última vez.
- ¿Peor *cuánto*? Una puntuación que pasa de 0.88 a 0.86 puede ser ruido. De 0.88 a 0.73 es una regresión. Sin saber cuánto oscila el sistema por sí solo, no puedes distinguir un caso del otro.
- ¿Quién decide qué significa «correcto» y dónde queda escrita esa decisión?

## Qué hace digline

digline es un gate que pones delante de esa pregunta. Escribes una vez lo que esperas de tu sistema en forma de un conjunto de checks: deterministas (la respuesta es JSON válido, no contiene números de teléfono, menciona el nombre del cliente) y juzgados (un segundo modelo puntúa la respuesta según una rúbrica). Los ejecutas contra tu sistema. Cuando el resultado te parece bien, lo **promueves**: pasa a ser el baseline, un archivo versionado en tu repositorio junto al código.

A partir de entonces, cada run se compara con ese baseline y el informe responde a la única pregunta que importa. Este es un run en el que nada empeoró, aunque tres checks se movieron y un caso no pudo resolverse:

<!-- digline: a comparison where nothing got worse -->

y este es uno en el que seis checks sí empeoraron:

<!-- digline: a comparison where something did -->

Ambos son lo que imprimió `digline compare` en la suite de ejemplo del primer capítulo de la [Guía](../product/guide.md), capturado de la versión publicada de la que proceden estos documentos. Las cifras son las que midieron esos runs.

El baseline es un archivo en git. Tiene historial, se le puede sacar un diff y nadie más que tú lo promueve. No hay ningún panel en el que iniciar sesión ni ningún servicio que reciba tus datos: digline se ejecuta donde se ejecuta tu código.

## Treinta segundos, en imágenes

<video controls preload="none" poster="/assets/video/ep01-poster.jpg"
       width="1920" height="1080"
       style="width:100%; height:auto; aspect-ratio:16/9; background:#0f1117">
  <source src="/assets/video/ep01.mp4" type="video/mp4">
  Tu navegador no admite la etiqueta de vídeo. <a href="/assets/video/ep01.mp4">Descarga el vídeo</a>.
</video>

*Episodio 1 de una serie breve sobre regresiones de LLM. Se sirve desde este sitio: sin reproductor de terceros, sin cookies.*

## Adónde ir después

- [Por qué](../why.md): el razonamiento detrás del diseño, por si quieres discutirlo.
- [Guía](../product/guide.md): instálalo y consigue tu primer `compare` en unos minutos.
- [En qué se diferencia digline](../comparison/index.md): si ya usas una herramienta de evaluación y quieres saber en qué se diferencia.

Diez palabras que te encontrarás por el camino: **run**, **baseline**, **comparar**, **promover**, **check**, **juzgar**, **tolerancia**, **noise floor**, **regresión**, **gate**. Cada una se explica la primera vez que aparece en la Guía.
