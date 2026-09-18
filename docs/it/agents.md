---
title: digline per gli agenti
template: agents.html
seo_title: 'digline per gli agenti: misurare tutto, approvare nulla'
lang: it
translation_of: agents.md
description: 'Cosa può fare un agente di programmazione con digline e cosa non può: eseguire e leggere ogni misurazione, senza raggiungere alcuna superficie che promuova un baseline.'
search:
  exclude: true
source: agents.md
source_sha: 2837b5253048
source_commit: 503ec3b
model: claude-opus-5
---

# digline per gli agenti

Un agente può misurare tutto e non approvare nulla. La misurazione è un lavoro che si può delegare; approvare ciò che conta come «accettabile» no, perché un sistema che può spostare il proprio riferimento ottimizza il riferimento.

<div class="principle" markdown>

## L'assenza, non il rifiuto

Sul server MCP `promote` non esiste: i suoi strumenti leggono un risultato o ne misurano uno nuovo, e nessuno di essi scrive un baseline. Un rifiuto è una conversazione che un agente può riaprire: contestare, ritentare, aggirare. Un'assenza no. Il ragionamento è nell'[ADR 0011](../product/adr/0011-the-mcp-server.md).

</div>

## Le superfici che un agente raggiunge

<div class="tiles" markdown>

<div class="tile" markdown>

### Il server MCP

I suoi strumenti leggono ciò che un run ha registrato e misurano nuovi run.

**Assente:** `promote`.

**Dettagli:** [digline via MCP](../product/mcp.md)

</div>

<div class="tile" markdown>

### L'operatore

Osserva una suite a intervalli programmati e apre una issue quando un risultato richiede una decisione. Ogni ciclo verifica che `promote` continui a fallire.

**Assente:** il rimedio. Correggere il prompt spetta a un ingegnere o a un agente di programmazione, e l'avviso è il passaggio di consegne.

**Dettagli:** [il ciclo dell'operatore](../product/operator.md), [il suo esempio](../product/examples/operator.md)

</div>

<div class="tile" markdown>

### pytest-digline e la GitHub Action

pytest-digline inserisce il confronto in un report di pytest; la GitHub Action lo pubblica come commento sulla pull request ed esce con il codice di digline.

**Assente:** un modo per promuovere. Nessun flag, fixture o marker nel plugin e nessun input nella Action rende un run il nuovo baseline.

**Dettagli:** [pytest-digline](../product/pytest.md), [la GitHub Action](https://github.com/digline/digline-action)

</div>

<div class="tile" markdown>

### AGENTS.md e la skill

AGENTS.md è lo strato di giudizio che lo strumento non codifica: quando rieseguire, quando indagare, quando formulare una raccomandazione. Le stesse regole sono distribuite come skill di Claude Code, e un test fallisce se le rispettive regole divergono.

**Assente:** l'approvazione. La prima regola, qui sotto, la lascia a una persona.

**Dettagli:** [`AGENTS.md`](https://github.com/digline/digline/blob/main/AGENTS.md), [`operating-digline`](https://github.com/digline/digline/tree/main/.claude/skills/operating-digline)

</div>

</div>

<div class="aside" markdown>

## Giudicare ciò che ha fatto, non ciò che ha scritto

L'agente sotto test, non l'agente che usa digline.
{: .aside__kicker }

La frase di un agente non è ciò che ha spostato il denaro. `ToolsCalled` contiene quali strumenti sono stati chiamati e in che ordine; `ToolCalledWith` contiene gli argomenti passati in una chiamata. Nell'[esempio LangGraph](../product/examples/langgraph.md) un agente di smistamento deve cercare un ordine prima di rimborsarlo e rimborsare l'importo restituito dalla ricerca: un agente che salta la ricerca scrive una buona frase, e nessuna asserzione sul testo può accorgersene. Entrambi i check sono elencati in [le asserzioni](../product/api.md#the-assertions).

</div>
