# Direction — where this is going, and what must survive getting there

This document describes the end state and the rules that hold on the way to it.
It is not a status document and is not regenerated per session; it changes only
when the direction changes, and a change to it is dated. Where it conflicts with
the handoff or the roadmap, this document wins on *direction* and the handoff
wins on *state*.

## The end state

A conversation. The owner talks to a strong model the way they would talk to any
assistant; the model remembers the conversation, works out what is wanted, and
does it. When doing it means computing something about the portfolio, checking
it against the owner's Investment Policy Statement, or reading a filing, the
model **calls a tool**. The tools are the deterministic pipelines this repository
builds: fixed graphs with typed inputs, traced execution, hand-computed
references, and outputs that are summaries, never raw data.

Two halves, as in the goal. The **guarantee half** — positions, allocation, P&L,
risk, compliance — is tools. The **judgement half** — screening, filings, a
thesis on a company — is the model reading and reasoning with further tools
(filings, fundamentals), marked as judgement, measured by an eval set. The seam
between them is a gate: any answer that implies a position passes through the
compliance checker before it reaches the owner. That is the synergy in the goal
made structural.

**Composition is dynamic; pipelines are fixed.** The model decides *whether* to
run a pipeline and in what order with other tools. It never decides *how* a
pipeline runs, and it never computes what a pipeline computes.

## What the current router is

Today one LLM call classifies intent, constructs a plan and extracts parameters
from a prose prompt of rules and few-shots. In the end state that call does not
exist: the model chooses tools by function calling, the tools validate their own
inputs, and each tool's internal graph is derived from a dependency table.

So the router is **scaffolding**. It stands in for the conversational layer until
the tool layer underneath it is complete. Work on it is worth doing only when it
moves toward the tool boundary:

- deterministic extraction of tickers, weights, periods and topics *before* any
  LLM sees the question — this becomes the tools' input validation;
- plans derived from intent through a dependency table — this becomes each
  tool's internal graph;
- intent classification reduced to the one decision an LLM should make.

Work that makes the router a *better classifier* — more intents, more prose
rules, tuned few-shots, a bigger model — is debt. Three prompt sentences and a
few-shot in one sitting moved no golden line the way they were predicted to; the
record is in KNOWN_GAPS. **Do not add prompt rules to fix a routing defect. Move
the defect into extraction or derivation, or log it.**

## Invariants — these survive every refactor

1. **Every number in an answer traces to a tool output.** The model narrates
   around figures; it never produces one. A figure that cannot be traced is a
   defect even inside an answer that reads well. The runner's "unexplained
   percentage" assertion is the first form of this rule; the end state applies
   it to every answer as a gate.
2. **Compliance is a gate, not a tool.** An answer that implies a position —
   including a thesis on a company the owner holds — is checked before it is
   shown. The model cannot route around it.
3. **Hot potato.** Agents and the model see summaries; raw arrays move through
   shared state and never into a context window.
4. **Policy lives in config.** The IPS is a document with numbered clauses and a
   derived config file; a personal IPS replaces the synthetic one as a file,
   with no code change.
5. **Raise, do not repair.** A missing input, an unknown vocabulary value, an
   absent asset class, a holding of unknown type: the pipeline stops and says
   why. A default is a wrong answer with a plausible face.
6. **References before code.** A figure the system produces has a hand-computed
   reference first (expected_values.md); a case the system passes has a check
   written before the capability. This does not relax for the judgement half:
   it gets an eval set defined in benchmark.md before a research agent exists.
7. **Scope is fixed by benchmark.md.** Security selection is out until a
   Level 4 defines what a good answer to "should I own X" is and how it is
   scored. Until then "should I buy X" is refused, correctly.

## Order

1. Finish the guarantee half's vocabulary: the block shapes the CLI questions
   exposed, then the router restructure (registry → extraction → derived plans
   → prompt shrink), then conversation memory as an extraction rule.
2. Make it the owner's: a transaction ledger and cost-basis method; a base
   currency and FX source (the owner's portfolio is not single-currency); a
   price source that can be defended with real money; the personal IPS, with
   the type vocabulary grown one clause at a time; a Part 8 reference for the
   real portfolio before any figure about it is trusted.
3. Level 4 in benchmark.md: the definition of a good research answer and its
   eval set. Nothing in the judgement half is built before this exists.
4. The judgement half: filings and fundamentals as tools with the same
   contracts; a stronger model for reading; uncertainty and sources as fields
   of the output, not tone.
5. The conversational layer replaces the router. The pipelines do not change.

Scope creep is the live risk at every step, not under-delivery. No deadline.

## When you are unsure

If a change makes the router smarter rather than smaller, stop and ask. If a
change puts a number in a model's hands, stop and ask. If a change would make a
tool's output depend on how it was asked rather than what was asked, stop and
ask. Otherwise follow the handoff.

*Written 8 September 2026.*
