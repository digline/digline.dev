---
seo_title: Lo que realmente estás entregando
lang: es
translation_of: handbook/01-what-you-are-shipping.md
description: 'Una llamada a un modelo parece una función y no lo es: el mismo prompt, muestreado dos veces, da dos respuestas. Lo que eso te cuesta y por qué las pruebas corrientes no pueden verlo.'
search:
  exclude: true
source: handbook/01-what-you-are-shipping.md
source_sha: 29449261b5b7
source_commit: 356a3c8
model: claude-opus-5
---

# 1. Lo que realmente estás entregando

Si vienes del software corriente, lo primero que hay que desaprender es qué es una función.

## Una función, y aquello que se le parece

Durante treinta años esto ha sido cierto: dada la misma entrada, el mismo código produce la misma salida. Todo en la ingeniería de software se apoya en ello: las pruebas, la depuración, la revisión de código, el «en mi máquina funciona». Puedes razonar sobre una función porque es una correspondencia fija entre entradas y salidas.

Una llamada a un modelo de lenguaje parece una función. Tiene una entrada (el prompt) y una salida (la respuesta). Está en tu código entre dos funciones corrientes. No lo es.

Un modelo de lenguaje produce una *distribución de probabilidad* sobre los posibles tokens siguientes y luego extrae muestras de ella. El muestreo es justamente la clave: es lo que permite que el mismo modelo escriba un poema y una consulta SQL. También significa que el mismo prompt, enviado dos veces, puede devolver dos respuestas distintas, y ambas son «correctas» en el único sentido que el modelo conoce: que ambas eran probables.

Puedes poner la temperatura a cero y reducir la variación. No puedes eliminarla y, para la mayoría de las tareas útiles, tampoco te conviene: un modelo a temperatura cero es peor precisamente en aquello para lo que lo compraste.

## Qué le hace esto a tus intuiciones

**«Lo probé y funciona».** Lo ejecutaste una vez. Extrajiste una muestra de la distribución. La siguiente muestra puede ser distinta. En el [juez de newsletter](https://github.com/digline/brief/tree/9507bb06f7dd90a4b6a624dbe77725e50819a02f) que este manual usa como ejemplo recurrente, los mismos veintiún artículos puntuados dos veces con un prompt idéntico produjeron veinte veredictos idénticos y uno distinto. Uno de cada veintiuno no es un error. Es la forma que tiene esto.

**«Arreglé el prompt».** Cambiaste la distribución. Ahora produce la respuesta que querías para la entrada que probaste. También produce respuestas ligeramente distintas para todas las demás entradas, y esas no las has mirado. Los cambios en el prompt son globales; tu atención era local.

**«No cambió nada, así que sigue funcionando».** Tu código no cambió. El modelo detrás de la API sí: los proveedores actualizan, reentrenan, marcan versiones como obsoletas y reapuntan alias sin un changelog que vayas a leer. Tu historial de git dice que el sistema no ha cambiado. Tus usuarios dicen que ha empeorado. Ambos tienen razón.

**«Está por encima del umbral».** Un umbral detecta lo que queda *por debajo del umbral*. No detecta lo que está *peor que el mes pasado*. Pon números inventados: una puntuación que se desplaza de 0.91 a 0.78 sigue estando por encima de 0.7, sigue en verde y es trece puntos peor para la persona que recibe la respuesta.

## Lo que realmente estás entregando, entonces

No una función. Un sistema cuyo comportamiento es una distribución, que se desplaza por su cuenta, que cambia globalmente cuando lo editas localmente y del que nadie en tu equipo ha visto más que un puñado de muestras.

Suena alarmante. Es manejable, pero solo con herramientas adecuadas a lo que es, y las del software corriente no lo son. `assert output == expected` no significa nada frente a una distribución. La revisión de código no puede ver un cambio que ocurrió del lado del proveedor. Una demo demuestra una muestra.

Lo que sí encaja es lo que harías con cualquier otra medición que tenga ruido: tomar varias muestras, compararlas con una referencia registrada y considerar real un cambio solo cuando es mayor que el ruido. No es una idea nueva. Así funciona un laboratorio. Simplemente no es como se ha enseñado a trabajar a los equipos de software, porque hasta hace poco nada en el stack se comportaba así.

## Las cuatro cosas que necesitas

Todo lo que queda de este manual se reduce a cuatro cosas, y el orden importa:

1. **Casos**: un conjunto de entradas que te importan, con lo que sabes sobre las respuestas correctas. Mantenidas fuera del prompt. Que crece con el tiempo. Este es el activo, y de él trata el [capítulo 2](../../handbook/02-cases.md); el [capítulo 3](../../handbook/03-ground-truth.md) trata de dónde salen las respuestas cuando nadie te da ninguna.
2. **Checks**: lo que verificas en cada salida. Primero los que no necesitan modelo; al final los que necesitan un juez, porque un juez es otra distribución. [Capítulo 4](../../handbook/04-checks.md), [capítulo 5](../../handbook/05-the-judge.md).
3. **Una referencia**: un run que has mirado y aprobado, registrado junto con el prompt y el commit que lo produjeron, para que cada run futuro tenga con qué compararse. [Capítulo 6](../../handbook/06-the-reference.md).
4. **Una rutina**: cuándo ejecutar, qué dispara una revisión, qué hacer cuando la comparación se pone en rojo. [Capítulo 7](../../handbook/07-maintenance.md).

Si desarrollas software para otros, hay una quinta cosa —qué puedes mostrarle al cliente y qué nunca debe salir de su perímetro— en el [capítulo 8](../../handbook/08-for-teams-building-for-others.md).

## Un hábito antes de seguir leyendo

Abre el proyecto donde tienes una llamada a un LLM. Busca la entrada con la que lo probaste cuando lo construiste. Envíala otra vez, ahora, cinco veces.

Si las cinco respuestas son iguales, bien: tienes una tarea con poco ruido y el resto de este manual te resultará fácil. Si difieren, acabas de ver en tu propio sistema, en un minuto, aquello de lo que trata este capítulo. En cualquier caso, ahora sabes algo que no sabías antes de ejecutarlo, que es de lo que se trata.
