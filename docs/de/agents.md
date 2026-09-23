---
title: digline für Agenten
template: agents.html
seo_title: 'digline für Agenten: alles messen, nichts freigeben'
lang: de
translation_of: agents.md
description: 'Was ein Coding-Agent mit digline tun kann und was nicht: jede Messung ausführen und lesen, und keine Oberfläche erreichen, die einen run zur neuen baseline macht.'
search:
  exclude: true
source: agents.md
source_sha: 0ba003e650a9
source_commit: 1e6213e
model: claude-opus-5
---

# digline für Agenten

Ein Agent kann alles messen und nichts freigeben. Messen ist Arbeit, die sich delegieren lässt; die Freigabe dessen, was als „akzeptabel“ gilt, nicht, denn ein System, das seine eigene Referenz verschieben kann, optimiert die Referenz.

<div class="principle" markdown>

## Die Abwesenheit, nicht die Weigerung

Auf dem MCP-Server gibt es `promote` nicht: seine Tools lesen ein Ergebnis oder messen ein neues, und keines davon schreibt eine baseline. Eine Weigerung ist ein Gespräch, das ein Agent wieder aufnehmen kann – dagegen argumentieren, es erneut versuchen, sie umgehen. Eine Abwesenheit nicht. Die Begründung steht in [ADR 0011](../product/adr/0011-the-mcp-server.md).

</div>

## Die Oberflächen, die ein Agent erreicht

<div class="tiles" markdown>

<div class="tile" markdown>

### Der MCP-Server

Seine Tools lesen, was ein run aufgezeichnet hat, und messen neue runs.

**Nicht vorhanden:** `promote`.

**Details:** [digline über MCP](../product/mcp.md)

</div>

<div class="tile" markdown>

### Der Operator

Er überwacht eine Suite nach Zeitplan und öffnet ein Issue, wenn ein Ergebnis eine Entscheidung braucht. In jedem Durchlauf wird geprüft, dass `promote` weiterhin fehlschlägt.

**Nicht vorhanden:** die Behebung. Den Prompt zu korrigieren ist Sache eines Entwicklers oder eines Coding-Agents, und die Meldung ist die Übergabe.

**Details:** [die Operator-Schleife](../product/operator.md), [das Beispiel dazu](../product/examples/operator.md)

</div>

<div class="tile" markdown>

### pytest-digline und die GitHub Action

pytest-digline bringt den Vergleich in den pytest-Report; die GitHub Action kommentiert ihn am Pull Request und beendet sich mit dem Exit-Code von digline.

**Nicht vorhanden:** ein Weg zum Promoten. Kein Flag, keine Fixture und kein Marker im Plugin und kein Input in der Action macht einen run zur neuen baseline.

**Details:** [pytest-digline](../product/pytest.md), [die GitHub Action](https://github.com/digline/digline-action)

</div>

<div class="tile" markdown>

### AGENTS.md und der Skill

AGENTS.md ist die Urteilsebene, die das Werkzeug nicht abbildet: wann ein run zu wiederholen, wann zu untersuchen und wann zu empfehlen ist. Dieselben Regeln gibt es als Claude-Code-Skill, der mit dem Plugin `digline@digline` installiert wird, und ein Test schlägt fehl, wenn die Regeln auseinanderlaufen.

Das Plugin fragt dich außerdem, bevor ein Agent `promote` oder `register` ausführt. Das ist eine Voreinstellung, keine Mauer: du kannst sie abschalten, und ein Befehl, den es nicht erkennt, kommt durch. Die Mauer ist das geprüfte Diff, denn baselines und das Register werden committet.

**Nicht vorhanden:** die Freigabe. Die erste Regel, unten, überlässt sie einem Menschen.

**Details:** [`AGENTS.md`](https://github.com/digline/digline/blob/main/AGENTS.md), [`operating-digline`](https://github.com/digline/digline/tree/main/.claude/skills/operating-digline), [das Plugin](../product/mcp.md#in-claude-code-as-a-plugin)

</div>

</div>

<div class="aside" markdown>

## Beurteilen, was er getan hat, nicht was er geschrieben hat

Der getestete Agent, nicht der Agent, der digline benutzt.
{: .aside__kicker }

Der Satz eines Agenten ist nicht das, was das Geld bewegt hat. `ToolsCalled` hält fest, welche Tools aufgerufen wurden und in welcher Reihenfolge; `ToolCalledWith` hält die Argumente fest, die ein einzelner Aufruf trug. Im [Beispiel zu LangGraph](../product/examples/langgraph.md) muss ein Dispatch-Agent eine Bestellung nachsehen, bevor er sie erstattet, und genau den Betrag erstatten, den die Abfrage zurückgegeben hat – ein Agent, der die Abfrage überspringt, schreibt einen guten Satz, und keine Zusicherung über den Text kann das erkennen. Beide checks sind unter [den Zusicherungen](../product/api.md#the-assertions) aufgeführt.

</div>
