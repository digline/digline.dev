---
title: digline para agentes
template: agents.html
seo_title: 'digline para agentes: medirlo todo, no aprobar nada'
lang: es
translation_of: agents.md
description: 'Lo que un agente de programación puede hacer con digline y lo que no: ejecutar y leer cualquier medición, sin llegar a ninguna superficie que promueva un baseline.'
search:
  exclude: true
source: agents.md
source_sha: 2837b5253048
source_commit: 503ec3b
model: claude-opus-5
---

# digline para agentes

Un agente puede medirlo todo y no aprobar nada. Medir es un trabajo que se puede delegar; aprobar qué cuenta como «aceptable» no lo es, porque un sistema que puede mover su propia referencia optimiza la referencia.

<div class="principle" markdown>

## La ausencia, no la negativa

En el servidor MCP `promote` no existe: sus herramientas leen un resultado o miden uno nuevo, y ninguna escribe un baseline. Una negativa es una conversación que un agente puede reabrir: discutirla, reintentarla, esquivarla. Una ausencia no. El razonamiento está en el [ADR 0011](../product/adr/0011-the-mcp-server.md).

</div>

## Las superficies a las que llega un agente

<div class="tiles" markdown>

<div class="tile" markdown>

### El servidor MCP

Sus herramientas leen lo que registró un run y miden runs nuevos.

**No está:** `promote`.

**Detalles:** [digline sobre MCP](../product/mcp.md)

</div>

<div class="tile" markdown>

### El operador

Vigila una suite de forma programada y abre una incidencia cuando un resultado requiere una decisión. En cada ciclo comprueba que `promote` sigue fallando.

**No está:** la solución. Arreglar el prompt le corresponde a una persona de ingeniería o a un agente de programación, y la alerta es el traspaso.

**Detalles:** [el bucle del operador](../product/operator.md), [su ejemplo](../product/examples/operator.md)

</div>

<div class="tile" markdown>

### pytest-digline y la GitHub Action

pytest-digline incluye la comparación en un informe de pytest; la GitHub Action la publica como comentario en la pull request y termina con el código de salida de digline.

**No está:** una forma de promover. Ningún flag, fixture ni marcador del plugin, ni ninguna entrada de la Action, convierte un run en el nuevo baseline.

**Detalles:** [pytest-digline](../product/pytest.md), [la GitHub Action](https://github.com/digline/digline-action)

</div>

<div class="tile" markdown>

### AGENTS.md y la skill

AGENTS.md es la capa de criterio que la herramienta no codifica: cuándo repetir una ejecución, investigar o recomendar. Las mismas reglas se distribuyen como skill de Claude Code, y un test falla si unas y otras dejan de coincidir.

**No está:** la aprobación. La primera regla, más abajo, la deja en manos de una persona.

**Detalles:** [`AGENTS.md`](https://github.com/digline/digline/blob/main/AGENTS.md), [`operating-digline`](https://github.com/digline/digline/tree/main/.claude/skills/operating-digline)

</div>

</div>

<div class="aside" markdown>

## Juzgar lo que hizo, no lo que escribió

El agente que se está probando, no el agente que usa digline.
{: .aside__kicker }

La frase de un agente no es lo que movió el dinero. `ToolsCalled` registra qué herramientas se llamaron y en qué orden; `ToolCalledWith` registra los argumentos que llevaba una llamada. En el [ejemplo de LangGraph](../product/examples/langgraph.md), un agente de despacho debe consultar un pedido antes de reembolsarlo y reembolsar la cifra que devolvió la consulta: un agente que se salta la consulta escribe una frase correcta, y ninguna aserción sobre el texto puede verlo. Los dos checks aparecen en [las aserciones](../product/api.md#the-assertions).

</div>
