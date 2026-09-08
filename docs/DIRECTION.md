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
it against a policy, valuing a company, or reading a filing, the model **calls a
tool**. The tools are the deterministic pipelines this repository builds: fixed
graphs with typed inputs, traced execution, hand-computed references, and
outputs that are summaries, never raw data.

Two halves, as in the goal. The **guarantee half** — positions, allocation, P&L,
risk, compliance — is tools. The **judgement half** — equity analysis: research,
valuation, a thesis, an entry, a sized position — is the model reading and
reasoning with further tools, marked as judgement, measured by the owner's own
predictions over time. The seam between them is a gate: any answer that implies
a position passes through the compliance checker before it reaches the owner.

**Composition is dynamic; pipelines are fixed.** The model decides *whether* to
run a pipeline and in what order with other tools. It never decides *how* a
pipeline runs, and it never computes what a pipeline computes.

## The judgement half, concretely

This is what the owner does by hand today, and what the system is for:

1. **Research** a company — filings, results, news, the business.
2. **Judge it against a philosophy** — the owner's own criteria for what is
   worth owning (quality of the business, returns on capital, balance sheet,
   price against value, a margin of safety; the owner's list, not this file's).
3. **Value it** — a range, from stated assumptions, not a point.
4. **Put it on a watchlist** with a thesis, an entry condition, and a dated
   prediction: what has to be true in a year for the thesis to have been right.
5. **Follow it** — news, results, the prediction against what actually happened.
6. **When the entry condition is met, size a position** — and the size is what
   the IPS allows, not what conviction suggests.
7. **Hold and re-check** — the thesis, the prediction, the policy, over time.

Each step splits the same way the guarantee half did:

- **Deterministic, with references:** valuation arithmetic from stated inputs
  (multiples, a discounted cash flow, whatever the owner uses — each a pipeline
  with a hand-computed reference); screening a company's figures against the
  philosophy's numeric criteria, clause cited; scoring a dated prediction
  against the outcome; sizing a candidate position against the IPS.
- **Judgement, marked as judgement:** the assumptions that go into a valuation;
  reading a filing; the thesis itself; whether now is an entry. Uncertainty and
  sources are fields of the output, not tone.

The artifacts this needs, all documents or data the owner owns:

- **A philosophy document**, the IPS pattern again: numbered clauses, a derived
  config, numeric criteria checked deterministically and cited by clause,
  statements citable but not computed. The IPS says what may be *held*; the
  philosophy says what is worth *wanting*. Two documents because they change for
  different reasons.
- **A watchlist**: candidates with thesis, entry condition, and the philosophy
  check that put them there.
- **A prediction ledger**: dated, specific, falsifiable predictions attached to
  a thesis, scored when their date comes. This ledger *is* the eval set for the
  judgement half. There is no golden baseline for judgement; there is the
  record of whether the owner's — and the system's — predictions were right.
- **Research sources as tools** with the same contracts as everything else:
  filings (EDGAR is free and structured), fundamentals, news. Raw documents
  never enter a context window whole; a reading tool returns a summary with its
  source and its uncertainty.

Recommendations are in scope here, and only here: "this clears the philosophy on
clauses P-2 and P-5, fails P-7 on price, and at 6% would clear every IPS clause;
at 10% it fails IPS-4.2." A recommendation is a judgement with its reasons, its
uncertainty, and the two policy checks attached. A recommendation without the
checks is generic advice; the policies are what make it the owner's.

The judgement half is not started, on purpose. It starts when benchmark.md has a
Level 4 that defines a good answer and the prediction ledger exists to score it.

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
   around figures; it never produces one. This includes valuations and
   predictions: the model may propose an assumption, the pipeline computes what
   follows from it, and the answer says which is which. A figure that cannot be
   traced is a defect even inside an answer that reads well.
2. **Compliance is a gate, not a tool.** An answer that implies a position —
   including a research recommendation — is checked against the IPS before it
   is shown. The model cannot route around it.
3. **Hot potato.** Agents and the model see summaries; raw arrays and raw
   documents move through shared state and never into a context window.
4. **Policy lives in config.** The IPS and the philosophy are documents with
   numbered clauses and derived config files; a personal one replaces a
   synthetic one as a file, with no code change.
5. **Raise, do not repair.** A missing input, an unknown vocabulary value, an
   absent asset class, a holding of unknown type, a valuation input nobody
   stated: the pipeline stops and says why. A default is a wrong answer with a
   plausible face.
6. **References before code.** A figure the system produces has a hand-computed
   reference first; a case the system passes has a check written before the
   capability; a judgement the system makes has a prediction in the ledger
   before it counts as right.
7. **No price forecasts as numbers.** The system never emits "the stock will be
   at X". A prediction is a statement about the business or the thesis with a
   date; a valuation is a range from stated assumptions. This is the line
   between judgement and a plausible-faced guess.
8. **Scope is fixed by benchmark.md.** Security selection is out until Level 4
   defines it. Until then "should I buy X" is refused, correctly.

## Order

1. Finish the guarantee half's vocabulary: the block shapes the CLI questions
   exposed, then the router restructure (registry → extraction → derived plans
   → prompt shrink), then conversation memory as an extraction rule.
2. Make it the owner's: a transaction ledger and cost-basis method; a base
   currency and FX source (the owner's portfolio is not single-currency); a
   price source that can be defended with real money; the personal IPS, with
   the type vocabulary grown one clause at a time; a Part 8 reference for the
   real portfolio before any figure about it is trusted.
3. The philosophy document, the watchlist and the prediction ledger — the
   owner's artifacts, before any tool reads them. Level 4 in benchmark.md: the
   definition of a good research answer, scored by the ledger.
4. The judgement half's tools, one at a time, each with a reference: a
   valuation pipeline; the philosophy check; a filings reader; prediction
   scoring. A stronger model for the reading. Then the research agent.
5. The conversational layer replaces the router. The pipelines do not change.

Scope creep is the live risk at every step, not under-delivery. No deadline.

## When you are unsure

If a change makes the router smarter rather than smaller, stop and ask. If a
change puts a number in a model's hands, stop and ask. If a change would make a
tool's output depend on how it was asked rather than what was asked, stop and
ask. If a change lets the system recommend before the philosophy, the ledger and
Level 4 exist, stop and ask. Otherwise follow the handoff.

*Written 8 September 2026. Revised the same day: the judgement half specified as
the owner's workflow, with the philosophy document, the watchlist and the
prediction ledger as its artifacts.*
