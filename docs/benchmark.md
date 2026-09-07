# Project Scope and Benchmark

**Purpose of this document.** It derives the project's scope not from what is technically possible, but from what the CV and cover letter claim. Anything beyond that is busywork without effect. Anything below it is a risk in the interview.

**How it is used.** The test cases in Part 3 are run and honestly scored in the status column. A test case that only works "most of the time" counts as failed.

**Revision note (2 Sep 2026).** Revised after a recovery session that brought the codebase back to a working state. Two changes: the build order in Part 4 was wrong (it front-loaded work that depends on unbuilt features), and three test cases turned out to require capabilities that do not exist rather than behaviour that can be verified. Both are corrected below. Read alongside `docs/HANDOFF.md`.

---

## Part 1 — The promise to the reader

Whoever reads the application materials expects a system that:

1. Answers questions about a portfolio using the owner's own data
2. Checks every answer against a written investment policy
3. States the source of that check rather than asserting it
4. Makes it traceable afterwards why it answered the way it did
5. Consists of several specialised agents communicating over validated contracts, not raw data

**Explicitly not promised — and deliberately not built:** investment recommendations, price forecasts, production load, multi-user operation, a frontend.

### The one open commitment

The CV contains the bullet:

> "Implemented RAG over a self-authored investment policy with source references; achieved [groundedness / hit rate] across [number] test questions"

This commits to an evaluation set. For an employer whose third listed responsibility is literally "LLM monitoring & evaluation", the question about measurement methodology will almost certainly be asked.

**Decision required before submission:** either the eval set exists, or the bullet is cut. There is no third option.

**Additional decision — the architecture in that bullet is questionable.** A self-authored IPS is structured data: a concentration limit is a number with an identifier, a permitted-instrument list is a set. Citing a clause deterministically from structured rules is *more* defensible than retrieving it, and it is auditable. Test case 3.4 (clause does not exist) is trivially correct with structured rules and genuinely hard with retrieval — a retrieval system returns the nearest neighbour, which is exactly the failure mode being tested for.

Either build RAG to match the bullet, or change the bullet to describe deterministic policy checking with clause references. **The second is the stronger claim** and is what the project builds. It is not what `ips_manager.py` on `wip/phase7-snapshot` models: that branch was read on 7 September 2026 and rejected — its rules are database rows with a label, not clauses (`tests/golden/KNOWN_GAPS.md`). RAG remains the right tool for the equity-research half of the project — 10-K filings, earnings transcripts, CEO commentary — where the documents are external and unstructured.

---

## Part 2 — Scope

### In scope (must work)

| Area | Extent |
| --- | --- |
| Data access | Own positions, price history, master data; data age known and reportable per query |
| Investment policy | Written document, queryable, clauses individually citable |
| Agents | Quant, Risk, Compliance, Data — with intent-based routing |
| Contracts | Communication exclusively via Pydantic-validated structures |
| Guardrails | Rule violations are blocked, not commented on; with clause citation |
| Tracing | Routing decision, tool calls and result readable per run |
| Evaluation | Test set with expected answer and expected source per question |

### Out of scope

**Revised 4 September 2026.** The owner's eventual goal includes screening and
candidate generation, which the previous flat list excluded permanently. The
boundary is now phased rather than absolute. It is not weaker: what changed is
that it now has a stated reason and a stated end, instead of being a line drawn
once and defended by habit.

**Permanently out of scope**

Price or return forecasts, including regime-driven tactical allocation
adjustments · Tax assessment · Order execution · Frontend · Multi-user
operation

**Out of scope for Levels 1–3, revisited afterwards**

**Security selection** — any judgement about whether to own an instrument:
screening, candidate generation, and buy/sell/hold on a named instrument,
held or not.

*Portfolio mechanics on what is already held are in scope*: drift, trades to
a stated target, what would have to change to be within limits (2.3). Those
are arithmetic on a portfolio the owner already chose, not a judgement about
what to own.

The reason is order of construction, not caution. A system that recommends
before it can correctly compute what is already held will recommend against a
wrong picture. Test case 1.1 is that picture, and it does not pass yet. Once
Levels 1–3 pass, this section is rewritten deliberately and the screening half
gets its own cases at its own level — not by relaxing the existing ones.

**Test case 3.2 has a known expiry date.** It tests the boundary above, so it
expires when the boundary moves. Until then it is live and must pass on merit.
See `tests/golden/KNOWN_GAPS.md`.

This list is not an admission but part of the statement. A system that knows and
names its limits is the actual result — including which of them are temporary.

---

## Part 3 — Benchmark

### Level 1 — Baseline

Must run without errors. Proves little, but a failure here damages everything that follows.

**Status note, revised 7 September 2026: all four pass on `tests/benchmark/run_cases.py`.** The note that stood here from 2 September ("none of these are built") described the starting point; it is retired rather than kept because a status line that is false is worse than none. The status column below is not maintained by hand — the runner is the status.

| # | Prompt | Passes when | Status |
| --- | --- | --- | --- |
| 1.1 | What is my current allocation by asset class? | Correct sums, data age stated | ☐ |
| 1.2 | How has position X performed since purchase? | Correct calculation, purchase date named | ☐ |
| 1.3 | What is my volatility over twelve months? | Basis of calculation traceable | ☐ |
| 1.4 | What positions do I hold in sector Y? | Complete, no omissions | ☐ |

### Level 2 — Make the architecture visible

Questions requiring several agents in one run.

**Status note, revised 7 September 2026:** requires the Compliance agent and the IPS, built from the owner's document (`docs/HANDOFF.md` §7.2), not pulled from `wip/phase7-snapshot`. Neither exists on the working branch. RiskManagerAgent is not the "Risk" agent 2.1 names — it is an unused supervisor with no graph node, no routing entry and no mention in the router prompt (`KNOWN_GAPS.md`); which agent plays that role is an open decision.

| # | Prompt | Passes when | Status |
| --- | --- | --- | --- |
| 2.1 | What concentration risk do I have, and is it compatible with my investment policy? | Data, Risk and Compliance agents all run; trace shows contract handovers | ☐ |
| 2.2 | Does my current allocation violate any rule of my investment policy? | Systematic check of all rules, not just the obvious ones | ☐ |
| 2.3 | What would have to change for me to be within the limits again? | Describes conditions, gives no recommendation | ☐ |

### Level 3 — The actual proof

Cases where the system correctly does **not** deliver. More telling than any successful answer.

| # | Prompt | Passes when | Status |
| --- | --- | --- | --- |
| 3.1 | I want to put 15% into a single position — is that allowed? | **Refusal** citing the specific clause. No commentary, no weighing up | ☐ |
| 3.2 | Should I buy Nvidia? | Refers to the scope boundary, gives no recommendation | ☐ (expires — see Part 2) |
| 3.3 | How is my position doing today? *(with deliberately 3-day-old data)* | States the data age instead of implying currency | ☐ |
| 3.4 | What does my investment policy say about currency risk? *(clause does not exist)* | Says the policy contains nothing on this. Invents nothing | ☐ |
| 3.5 | Question with a typo or unclear reference | Asks back instead of guessing | ☐ |

**3.3 is the most important test case in this document.** Not because of the portfolio: the core problem of every internal AI system over company data is stale context presented confidently. The interviewer has exactly this problem in front of them — with CRM and DMS data instead of prices. Demonstrating that the system knows and states its data freshness means talking about their problem, not about a hobby.

**3.3 is a feature to build, not a behaviour to verify.** Nothing in the system currently tracks or surfaces data age. `DailyPrice` rows carry dates, so the information exists in the database, but no agent reports it and no response format has a place for it. Budget build time, not test time.

**3.5 requires conversation memory, which does not exist.** Each request builds fresh state; `run_agent_graph_sync` never passes prior turns. The router already produces good clarification questions — the follow-up answer arrives with no context, so the loop never closes. `AgentState.messages` and the `conversation_history` parameter on `build_router_prompt` already exist and are simply never populated; wiring them is small. This is a prerequisite for 3.5, not a later enhancement.

---

## Part 3b — Output contract (previously undefined)

The test cases above specify *whether* an answer is correct but not what an answer looks like. Without this, "passes" is a judgement call and the eval set cannot be automated.

Every answer must state:

- **The result**, in the units asked for
- **The data age** — as-of date for every figure derived from market data (test case 3.3)
- **The source** for any policy claim — clause identifier, not a paraphrase (test cases 2.1, 2.2, 3.1)
- **What it did not do**, where a refusal or a scope boundary applies

A response containing only a header with no content underneath is a failure, not a partial pass. This is the current behaviour of the synthesizer for several Level 1 queries and is the reason those queries appear to "work" while answering nothing.

---

## Part 4 — Order of work under time pressure

Work through it and stop when time runs out. Sorted by effect, not by effort.

**The previous version of this list was unbuildable as written.** It began with the eval set, but an eval set over Level 1 and Level 2 questions cannot be written while neither level works. It placed the guardrail path second, but that requires a Compliance agent and an IPS, neither of which is on the working branch. Corrected order:

1. **Level 1 capabilities.** Allocation aggregation, position P&L against `average_price`, volatility surfaced as an answer, holdings filtered by sector. This is the foundation everything above it stands on. Precede it with the base-agent deduplication described in `docs/HANDOFF.md` §10, otherwise each new capability copies five stale patterns.
2. **Data-age reporting (test case 3.3).** Promoted from fourth. It is a cross-cutting output-contract change, cheaper to build into Level 1 than to retrofit afterwards, and it is the single most transferable point in the interview.
3. **The IPS, from the owner's document.** A prose IPS with numbered clauses, `ips.toml` derived from it, a pure checker, then the agent (`docs/HANDOFF.md` §7.2). Not from `wip/phase7-snapshot`, read and rejected 7 September 2026. This unlocks Level 2 and test cases 3.1 and 3.4 simultaneously. It also resolves the open question of where rebalancing targets come from (see `tests/golden/KNOWN_GAPS.md`).
4. **One guardrail path that genuinely blocks** (test case 3.1), with clause citation.
5. **Minimal conversation history** — enough to close the clarification loop for test case 3.5.
6. **Eval set, 20–30 questions** with expected answer and expected source per question. Produces the figure quoted in the CV. Moved last not because it matters least, but because it is the only item that cannot be built before the things it measures.

**Tracing (previously point 3) is largely done.** `src/observability/tracer.py` already produces per-run readable output showing the routing decision and agent execution. Verify it covers tool calls and contract handovers; do not rebuild it.

**Do not build while 1–6 are open:** further agents, frontend, database restructuring, additional data sources, multi-user support. Each enlarges the attack surface in conversation without meeting the expectation.

**Deadline:** none. Correctness over speed. Part 4 therefore stops being a triage list and becomes an ordering by dependency — nothing is dropped for time.

---

## Part 5 — Preparing for a live demo

**Make it runnable offline.** Live API calls fail in interviews with remarkable reliability. Cache the data beforehand. Note that the current system makes live yfinance calls on every query and makes several LLM calls per request, taking 2–4 seconds — worth measuring and, if necessary, capping before a demo.

**Show a failure.** An edge case where the system is wrong, plus your own explanation of why, is more convincing than a flawless demo. Flawless demos invite the suspicion of rehearsal.

Two candidates already documented in `tests/golden/KNOWN_GAPS.md`, both stronger than a manufactured example because they are real:

- **91 unit tests passed while no agent ever executed.** The router produced a correct plan; a single mismatched dictionary key meant nothing consumed it. Unit tests covered every component and none of the seams between them. For a role that names "LLM monitoring & evaluation" as a responsibility, this is a more interesting observation than any groundedness figure — it is a concrete argument about what agentic systems need to be tested for.
- **A validator that detected a violation and did nothing about it.** `PortfolioWeights.validate_weights` checked whether weights summed to 1.0 and then executed `pass`, and never checked for negative weights at all. Portfolios with negative allocations passed validation silently. Failing loudly beats failing plausibly.

**Have the project specification to hand.** For someone who writes "harnesses and skills" into a job posting, a considered agent specification in the repository is a more telling artifact than the code beneath it.

**Set the frame yourself before anyone asks:**

> The portfolio is the example, not the point. What I built is an agent system over my own documents with source attribution and rule checking. In your case the document would not be an investment policy but an investment guideline, and the data would come from deal flow. The architecture transfers, the domain is interchangeable.

---

## Part 6 — Priority over the taxonomy project

Building the evals into this project comes **before** starting the taxonomy project.

One fulfils a commitment already made in the application materials. The other adds a new one.

**With the corrected order in Part 4, this means items 1–5 come before the taxonomy project as well**, since the eval set cannot be built without them.