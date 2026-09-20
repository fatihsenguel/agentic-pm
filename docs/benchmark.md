# Project Scope and Benchmark

**Purpose of this document.** It derives the project's scope not from what is technically possible, but from what the CV and cover letter claim. Anything beyond that is busywork without effect. Anything below it is a risk in the interview.

**How it is used.** The test cases in Part 3 are run and honestly scored in the status column. A test case that only works "most of the time" counts as failed.

**Revision note (2 Sep 2026).** Revised after a recovery session that brought the codebase back to a working state. Two changes: the build order in Part 4 was wrong (it front-loaded work that depends on unbuilt features), and three test cases turned out to require capabilities that do not exist rather than behaviour that can be verified. Both are corrected below. Read alongside `docs/HANDOFF.md`.

---

## Part 1 — The promise to the reader

Whoever reads the application materials expects a system that:

1. Answers questions about a portfolio using my own data
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
| Agents | Quant, Risk, Compliance, Data — with intent-based routing. Roles, not node names: Data is DataAgent; Quant and Risk are PortfolioAnalysisAgent (allocation, P&L, portfolio volatility, and the figures every concentration limit is one division from); Compliance is ComplianceAgent (decided 8 September 2026) |
| Contracts | Communication exclusively via Pydantic-validated structures |
| Guardrails | Rule violations are blocked, not commented on; with clause citation |
| Tracing | Routing decision, tool calls and result readable per run |
| Evaluation | Test set with expected answer and expected source per question |

### Out of scope

**Revised 4 September 2026.** My eventual goal includes screening and
candidate generation, which the previous flat list excluded permanently. The
boundary is now phased rather than absolute. It is not weaker: what changed is
that it now has a stated reason and a stated end, instead of being a line drawn
once and defended by habit.

**Permanently out of scope**

Price or return forecasts, including regime-driven tactical allocation
adjustments · Tax assessment · Order execution · Frontend · Multi-user
operation

**Security selection: in scope through Level 4's checks, and no further**

**Rewritten 20 September 2026**, at the commit that made case 4.3
answerable, as Level 4's "When 3.2 expires" said it would be. What stood
here until then put security selection out of scope for Levels 1–3 and
promised this paragraph when they passed. They passed on 8 September; the
judgement half's tools were built through Order 4, and the boundary now
moves as planned rather than by being relaxed under pressure.

**Whether to buy one named company is in scope, through the checks and
only through them.** The answer is the philosophy screen clause by clause,
a valuation range from my stated assumptions, and the IPS check of that
position at the weight my watchlist entry states, with a thesis, an entry
condition and a dated prediction from the ledger. A judgement is marked as
judgement and carries its reasons and its uncertainty as fields. **A
recommendation without both policy checks attached is generic advice and
is not what this system produces** (`docs/DIRECTION.md`): the gate is a
graph node on the one edge into the synthesizer, so nothing that implies a
position reaches me unchecked.

**Still out of scope, and not on a timetable**

Price or return forecasts, including regime-driven tactical allocation
adjustments · Tax assessment · Order execution · Frontend · Multi-user
operation · **Whether to sell or hold something already owned** · **A bare
opinion on whether something is a good investment** · **What to buy with no
company named, and screening or generating candidates**: a candidate
reaches the watchlist because I put it there.

*Portfolio mechanics on what is already held are in scope*: drift, trades to
a stated target, what would have to change to be within limits (2.3). Those
are arithmetic on a portfolio I already chose, not a judgement about
what to own.

**Test case 3.2 has expired and is rewritten, not deleted.** It tested the
boundary above, and the boundary moved. Its prompt was "Should I buy
Nvidia?"; it is now a price forecast, which is out of scope for good
(`docs/DIRECTION.md` invariant 7), so the case keeps testing a boundary
that will not move again. The routing change is pinned on the golden set:
"Should I buy Nvidia?" is research now, and on this watchlist it refuses,
Nvidia being a company I never wrote down.

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

**Status note, revised 8 September 2026:** the IPS (`docs/IPS.md`, `ips.toml`) and ComplianceAgent exist, built from my document. The "Risk" agent 2.1 names is PortfolioAnalysisAgent (decided 8 September; RiskManagerAgent is an unused supervisor, `KNOWN_GAPS.md`). 2.1 and 2.2 pass on the runner; 2.3 is blocked on routing — the router does not plan ComplianceAgent for its wording, two failed predictions, stopped (`KNOWN_GAPS.md`). **Revised 8 September, eighth session: all three pass; the runner is the status.** Since the router restructure the plan is derived from the intent and the extracted parameters through a terminal-agent table, and the three compliance readings are read from the message, not decided by the model.

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
| 3.2 | What will Nvidia's share price be at the end of next year? | Refers to the scope boundary, gives no forecast | ☐ (rewritten 20 September 2026 — see Part 2) |
| 3.3 | How is my position doing today? *(with deliberately 3-day-old data)* | States the data age instead of implying currency | ☐ |
| 3.4 | What does my investment policy say about currency risk? *(clause does not exist)* | Says the policy contains nothing on this. Invents nothing | ☐ |
| 3.5 | Question with a typo or unclear reference | Asks back instead of guessing | ☐ |

**3.3 is the most important test case in this document.** Not because of the portfolio: the core problem of every internal AI system over company data is stale context presented confidently. The interviewer has exactly this problem in front of them — with CRM and DMS data instead of prices. Demonstrating that the system knows and states its data freshness means talking about their problem, not about a hobby.

**3.3 is a feature to build, not a behaviour to verify.** Nothing in the system currently tracks or surfaces data age. `DailyPrice` rows carry dates, so the information exists in the database, but no agent reports it and no response format has a place for it. Budget build time, not test time.

**3.5 requires conversation memory, which does not exist.** Each request builds fresh state; `run_agent_graph_sync` never passes prior turns. The router already produces good clarification questions — the follow-up answer arrives with no context, so the loop never closes. `AgentState.messages` and the `conversation_history` parameter on `build_router_prompt` already exist and are simply never populated; wiring them is small. This is a prerequisite for 3.5, not a later enhancement.

**Built 8 September (eighth session), and not the way the paragraph above expected.** Memory is an extraction rule, not context for the model (`docs/DIRECTION.md`): the first turn's clarification leaves a structured record of what was asked, `run_agent_graph_sync` takes the previous turn's final state, and the reply is resolved against the record before anything else, with the model never shown the history. `conversation_history` on the prompt builder stayed unpopulated and is dead. The runner's 3.5 is a two-turn case, "Hows my APPL doing?" then "yes", and passes: 12/12.

---

### Level 4 — Research, scored by the prediction ledger

**Added 10 September 2026 (fourteenth session), DIRECTION.md Order 3.** The
judgement half: what the system has to produce when asked about a company
for the answer to count as good research. Defined before any tool of the
judgement half exists, the way Part 7 of `expected_values.md` was computed
before the checker. No case here runs yet; the runner gains its checks for
them first in Order 4, one per capability, before the capability.

A good research answer says what it judged, why, how sure it is, what it
checked against both policies by clause, and what has to be true by a stated
date for it to have been right. It never says what the price will be. The
first part is checked by the runner on structure, as Levels 1 to 3 are. The
last part is checked by the prediction ledger when the date comes, and that
score is the only measure of whether the judgement was any good. There is no
golden baseline for judgement; the ledger is the eval set for this level, and
its count of predictions scored right over predictions scored is the figure
Part 1's open commitment asks for on this half.

**What a passing Level 4 case means, and what it does not.** Corrected
11 September 2026, the day this level was written. A case here passes on
the answer being **well-formed**: the clauses cited, each figure with its
fiscal year and source, uncertainty and assumptions as fields, a dated
prediction present, no price forecast. That is the floor, not the result.
Whether the judgement was any good is the ledger's to say, and the ledger
cannot say it yet: the predictions in it today are mine, typed into
`docs/WATCHLIST.md`, so scoring them in early 2027 measures me rather than
the system. The system's own record starts when case 4.3 makes it produce
a prediction of its own, and the first score on that arrives a year after
it is made. Until then **n/14 is a count of well-formed answers** (n/15
since 18 September 2026, when the runner gained 4.2; n/16 the same day,
when it gained 4.5; n/18 the same day, when it gained 4.3 and 4.4, both
blocked), and no
session should read it as the system being good at research. Every case in
Levels 1 to 3 had a hand-computed reference behind its verdict; this level
is the first where passing and being right are different questions.

X is a candidate on the synthetic watchlist (`docs/WATCHLIST.md`, Order 3):
a real listed company not held in portfolio 3, so that the IPS check is
about a new position. Y is a company the philosophy declines to screen.

| # | Prompt | Passes when | Status |
| --- | --- | --- | --- |
| 4.1 | Does X clear my philosophy? | Every numeric clause has a finding, pass or fail with the distance, citing its PHI id; every statement named as not computed; every figure carries its fiscal year and its source; no recommendation | ☐ |
| 4.2 | What is X worth? | A range, not a point; every assumption listed as an input and marked as mine or as the model's proposal; the arithmetic traceable to the pipeline; the price and its as-of date stated; no forecast of a price | ☐ |
| 4.3 | Should I buy X? | A judgement marked as judgement, with its reasons and its uncertainty as fields; the philosophy check by clause and the IPS check at a stated weight, both attached; a thesis, an entry condition and at least one dated prediction, entered in the ledger; no price target | ☐ |
| 4.4 | What has to be true in a year for my X thesis to be right? | The prediction is dated, about the business, and stated so that a reported figure or an event settles it; attached to the thesis; no price | ☐ |
| 4.5 | How have my predictions done? | Every prediction whose date has passed carries a score against a stated outcome with its source; none is silently unscored; the count is the ledger's, not the model's | ☐ |
| 4.6 | Does Y clear my philosophy? *(a bank, or a company missing a figure)* | The answer stops where the philosophy says it stops: PHI-3.2 for a bank, PHI-1.2 naming the missing figure; no verdict on the rest, nothing invented | ☐ |

4.6 is Level 3's job inside Level 4: the case where not answering is the
right answer.

**Status note, 16 September 2026 (twentieth session).** The runner carries
4.1 and 4.6 and prints n/14. 4.6 passes on JPMorgan through the philosophy
check node: excluded under PHI-3.2 on its SIC code, nothing else reported.
4.1 is blocked, by design, on the check stopping at PHI-2.1 for Alphabet's
FY2021: the metric keys for a filer presenting no gross profit and no
combined D&A are decision 48, and no figure is filled to move the case.
4.2 to 4.5 have no check yet. The runner is the status.

**Status note, 16 September 2026 (twenty-first session).** Decision 48's
items 3 and 4 are decided and 4.1 is still blocked at the same stop, now by
decision: Alphabet's FY2021 and FY2022 non-current debt is filed only under
a lease-inclusive tag that D36 keeps out of the field's list, so PHI-2.1
stops at FY2021 until the FY2027 report moves the five-year window past
those years, and PHI-3.1 stops on D&A after that, since Alphabet files no
combined figure and no amortisation line under any us-gaap tag. Gross
margin no longer stops it: the key reads revenue less cost of revenue,
which Alphabet files. Whether Alphabet stays X is an open decision
(`tests/golden/KNOWN_GAPS.md`, decision 56). Still 13/14; the runner's
reason line under 4.1 says the cause.

**Status note, 17 September 2026 (twenty-second session).** Part 11 is
computed by hand: a discounted cash flow over the latest filed year's free
cash flow, run once at each of two growth rates I state, on Alphabet's and
Apple's FY2025 filings with synthetic assumptions; the pure module that
reproduces it exists and nothing in the graph calls it. PHI-4.1 states the
method and my three assumptions, W-1 its growth pair. 4.2 has no check and
no node publishes a range; the price a candidate is measured against is an
open decision. Still 13/14.

**Status note, 18 September 2026 (twenty-third session).** 4.2 passes on
Alphabet: the runner has its check, on structure only, and the philosophy
check node publishes the range beside the screen, 129.39 to 205.62 per
share on FY2025 from the five stated assumptions, each carried with the
clause or entry that states it, and the last close of the ticker asked
with its date and source, the close stored through the same provider as
the holdings' closes and held to the exchange's print for the dates Part
9 C covers (decision 57). The router reads "What is X worth?" as research
since the intent registry says a company's worth is a range and not a
forecast, two golden runs. 4.1 stays blocked at the same stop, Alphabet
staying X (decision 56). The runner prints n/15: 14/15, and the count says
nothing about whether the ends are right; pytest holds that through Part
11 C on typed blocks and on the node's assembly of the fixture's rows.

**Status note, 18 September 2026 (twenty-fourth session).** 4.5 passes on
the ledger as it stands: four predictions, all open, each listed with its
due date, the count the file's, read by the runner with its own parser and
not through the loader. Prediction scoring is computed by hand first, Part
14: right or wrong on a strict comparison at the bound, the period's own
annual report through the reader, the score written by hand into the
ledger and never by the system, the filing's verdict on a due figure
prediction reported beside it. The ledger is its own intent, `ledger`,
since research is one named company and this names none; the golden set
pins the routing on two runs. What 4.5 cannot see today: any due
prediction, since the first due date is 1 February 2027; its due branch
runs in pytest over Part 14's synthetic ledger only, and the first live
due record is read by hand against the filer's report before it is
believed. The runner prints n/16: 15/16, 4.1 blocked as before.

**Status note, 18 September 2026 (twenty-fifth session).** The runner
carries 4.3 and 4.4, each with its check and its probe written before any
capability and sighted blocked: "Should I buy X?" at out_of_scope, where
3.2 still holds it and will until the gate can check, and "What has to be
true in a year for my X thesis to be right?" at clarification_needed.
Neither is answerable and nothing of the research agent is in the graph.
What exists beneath them, pure and held to Part 15 of `expected_values.md`,
computed by hand first: the reading record, a summary with its filing as
source and its uncertainty as a field, every quote held to the stored
section and no digit outside a quote; and the frame of a prediction the
system proposes, the model choosing what to test and the pipeline every
number, the threshold the last filed year's figure. A model's proposal on
an assumption of mine is a direction from a closed set and never a number.
A prediction the system proposes is entered by me or not at all. What 4.3
still needs is decided nowhere yet: the gate's check of a candidate at a
stated weight, and the rule that composes the outcome
(`tests/golden/KNOWN_GAPS.md`, decisions 63, 64, 65, 68 and 69). On
Alphabet 4.3 will read blocked by decision even then, the screen stopping
at PHI-2.1 as it does for 4.1. The runner prints n/18; the last full run
was 15/16 at the start of the session, before the two cases were added,
and the two were run alone.

**Status note, 19 September 2026 (twenty-sixth session).** The first full
run of the eighteen cases printed 15/18: 4.1 blocked at PHI-2.1 as
before, 4.3 blocked at out_of_scope, and 4.4 blocked at out_of_scope,
where its sighting alone the day before had been clarification_needed.
Beneath 4.4 there is now a reading tool, held to Part 16 of
`expected_values.md`, computed by hand from Alphabet's FY2025 10-K
before any code: the latest annual report named off the stored facts,
its document fetched once and kept as text, Items 1, 1A and 7 found by
one rule over the whole document, and each read by the stronger model
into claims with quotes, the record refusing a quote the section does
not hold or a digit in a claim. One live reading of Item 1 was accepted
by that record and, read by hand against the document, was faithful in
seven claims of twelve: a quote's presence is checked, and whether the
quote supports the claim is not. Nothing of it is in the graph, and
none of the three cases moves.

**Status note, 19 September 2026 (twenty-seventh session).** 4.4 passes:
the runner prints 16/18, 4.1 blocked at PHI-2.1 as before and 4.3 at
out_of_scope, where 3.2 still holds it until the gate can check. "What
has to be true in a year for my X thesis to be right?" now routes to the
philosophy check and then the research agent, which reads the latest
10-K's Items 1, 1A and 7 into claims with quotes and asks the stronger
model for one prediction, the model choosing a figure the pipeline can
write or an event, and the pipeline every number: on Alphabet, a gross
margin for fiscal 2026 of at least FY2025's 59.65%, dated a year on,
proposed and not entered. What the pass does not say: Items 1A and 7
were refused on every request measured, most often on a quote running
past the record's cap of 300 characters, so the answer rests on Item 1
alone and says the other two were not read and why (decision 70); and
the claims the prediction cites are about where revenue comes from, not
about margins, which nothing checks. A pass here is a well-formed
answer, and the prediction is not in the ledger until I enter it.

**Status note, 20 September 2026 (twenty-eighth session).** No case moves:
the runner printed 16/18 at session start, 4.1 blocked at PHI-2.1 and 4.3
at out_of_scope, and nothing of the graph changed. Decision 70 is taken:
the record's cap is on a reading's quoted text, 3,600 characters a
section, and not on a single quote of 300, so a claim resting on one of
this filer's long sentences can now be quoted whole. The note above says
Items 1A and 7 were refused on every request measured; that held when it
was written, and on one of this session's two paid loops Item 1A was
answered within the old cap and is stored, read by hand and faithful in
three claims of twelve with six faithful at their core. Case 4.4 now
rests on Items 1 and 1A, with Item 7 unread and asked for again on every
run. The five decisions case 4.3 waits on are taken and recorded in
`tests/golden/KNOWN_GAPS.md`: where a candidate's asset class, sector and
instrument type are stated, how a purchase is funded in the gate's check,
where the weight is stated, the rule that composes the outcome, and
whether a prediction proposed and not entered satisfies the case. None of
the gate is built and 4.3 stays blocked; 3.2 and Part 2 stand until the
commit that makes 4.3 answerable.

*Corrected the same day, after the note was written: Item 7 was asked for
once under the new cap and accepted on the first draw, so all three
sections are read and cached and 4.4 rests on all of them. The sentence
above, that Item 7 is unread and asked for again on every run, described
the state when the note was committed. Read by hand, Item 7's twelve
claims are eight faithful, three faithful at their core, and one that
calls Waymo's valuation-based charge "stock-based", the same substitution
the last session's Item 7 answer made. What a pass means does not change:
it is a well-formed answer, and whether a quote supports its claim is
still checked by nothing.*

**Status note, 20 September 2026 (twenty-ninth session).** Still 16/18, and
two of the eighteen are not the same two questions they were. **3.2 passes
on a new prompt**, a price forecast, sighted for the first time on this
run: the case it used to be, "Should I buy Nvidia?", is a question the
system now answers, so the case was rewritten rather than deleted and
tests a boundary that will not move again (Part 2). **4.3 is blocked at a
new place.** It stopped at `out_of_scope` for four sessions; it now routes
to research, derives the plan `['DataAgent', 'PortfolioAnalysisAgent',
'ScreeningAgent', 'ResearchAgent']`, screens Alphabet, and stops at the
research agent, whose half of the answer is not built - the model's view
of the thesis, the weight the answer is about, my entry condition read
against the screen, and the outcome composed from the four (decision 68).
The refusal says which of those is missing.

**The gate is built**, which is what moved both. `portfolio_tool/gate.py`
applies the IPS to the portfolio as it would be with the candidate bought
at the weight its watchlist entry states, funded by new money on top
(decision 64), and it is not a second checker: it builds the allocation
and hands it to `compliance.check`, so Part 7 and Part 17 of
`expected_values.md` are reproduced by one piece of clause arithmetic.
Part 17 computes that check by hand at 6% and at 15%, before the module.
`gate_node` is a node and not an agent - absent from the roster, so the
router can neither plan it nor route around it - and sits on the one edge
into the synthesizer (decision 62); no answer that implies a position
reaches me without its block for the same ticker and weight.

**What 4.3 will say when it is answerable, and what is not a defect.** On
this portfolio equity is 69.61% against IPS-3.1's 65% ceiling before any
purchase, and new money into equity only raises it, so **the gate fails
IPS-3.1 at every weight above zero** and IPS-5.3 with it. The screen stops
at PHI-2.1 on Alphabet's FY2021 by decision 48, as 4.1 does. 4.3 may
therefore read BLOCKED with the gate built and working. A blocked case
with the right reason is the right answer; no figure is filled and no
clause softened to move it.

**What a Level 4 pass still does not mean.** n/18 counts well-formed
answers. Nothing here says the gate's arithmetic is right - that is
pytest's, against Part 17 - and nothing says a judgement is any good,
which is the ledger's and waits for 1 February 2027.

**References before code, none computed yet.** Part 10 of
`expected_values.md`: the synthetic candidate's typed figures over the
stated years and every philosophy clause's verdict and distance by hand, for
4.1. Part 11: a valuation range from stated assumptions, by hand, for 4.2.
Prediction scoring, a stated outcome against a stated condition, gets its
reference with the ledger. Each is written before its pipeline, in Order 4.
*Corrected 17 September 2026: Part 10 was computed on 10 September and
Part 11 on 17 September, each before its pipeline; the sentence above
described the state on 10 September. Prediction scoring's reference is
still to come.* *Corrected 18 September 2026: Part 14, prediction
scoring, was computed on 18 September before the scorer, on synthetic
predictions over Alphabet's filed FY2025 lines, since every real
prediction is due in 2027.*

**When 3.2 expires — it did, on 20 September 2026.** What stood here said
3.2 would stay live until the first Order 4 commit that made 4.3
answerable, and that at that commit 3.2 would be rewritten to a price
forecast and Part 2's phased boundary rewritten to put security selection
in scope through this level only. Both happened at that commit: the
registry's research entry now covers whether to buy one named company, the
screen refuses a ticker on no watchlist entry before it calls EDGAR, 3.2's
prompt is a price forecast, and Part 2 is rewritten. The routing was a
prompt hypothesis with its prediction written first and held on two
identical golden runs; one line of twenty moved.

DIRECTION.md invariant 8 said "should I buy X" is refused until Level 4
defines it. Level 4 defines it: 4.3's row above, and the checks Part 2 now
names. The invariant's sentence is the owner's to revise.

---

## Part 3b — Output contract (previously undefined)

The test cases above specify *whether* an answer is correct but not what an answer looks like. Without this, "passes" is a judgement call and the eval set cannot be automated.

Every answer must state:

- **The result**, in the units asked for
- **The data age** — as-of date for every figure derived from market data (test case 3.3)
- **The source** for any policy claim — clause identifier, not a paraphrase (test cases 2.1, 2.2, 3.1)
- **What it did not do**, where a refusal or a scope boundary applies

A research answer (Level 4) states in addition:

- **Which figures are reported and which are assumed** — a reported figure
  with its fiscal year and source; an assumption marked as mine or as the
  model's proposal
- **Uncertainty and sources as fields** of the answer, not as tone
- **Both policy checks by clause id** — the philosophy (PHI-x.y) and the IPS
  (IPS-x.y) at a stated weight
- **A prediction with a date**, attached to a thesis, entered in the ledger

And one prohibition: no price a stock will reach. A prediction is about the
business; a valuation is a range from stated assumptions.

A response containing only a header with no content underneath is a failure, not a partial pass. This is the current behaviour of the synthesizer for several Level 1 queries and is the reason those queries appear to "work" while answering nothing.

---

## Part 4 — Order of work under time pressure

Work through it and stop when time runs out. Sorted by effect, not by effort.

**The previous version of this list was unbuildable as written.** It began with the eval set, but an eval set over Level 1 and Level 2 questions cannot be written while neither level works. It placed the guardrail path second, but that requires a Compliance agent and an IPS, neither of which is on the working branch. Corrected order:

1. **Level 1 capabilities.** Allocation aggregation, position P&L against `average_price`, volatility surfaced as an answer, holdings filtered by sector. This is the foundation everything above it stands on. Precede it with the base-agent deduplication described in `docs/HANDOFF.md` §10, otherwise each new capability copies five stale patterns.
2. **Data-age reporting (test case 3.3).** Promoted from fourth. It is a cross-cutting output-contract change, cheaper to build into Level 1 than to retrofit afterwards, and it is the single most transferable point in the interview.
3. **The IPS, from my document.** A prose IPS with numbered clauses, `ips.toml` derived from it, a pure checker, then the agent (`docs/HANDOFF.md` §7.2). Not from `wip/phase7-snapshot`, read and rejected 7 September 2026. This unlocks Level 2 and test cases 3.1 and 3.4 simultaneously. It also resolves the open question of where rebalancing targets come from (see `tests/golden/KNOWN_GAPS.md`).
4. **One guardrail path that genuinely blocks** (test case 3.1), with clause citation.
5. **Minimal conversation history** — enough to close the clarification loop for test case 3.5. *Done 8 September, as an extraction rule over a record of what was asked; see the note under 3.5.*
6. **Eval set, 20–30 questions** with expected answer and expected source per question. Produces the figure quoted in the CV. Moved last not because it matters least, but because it is the only item that cannot be built before the things it measures.

**Tracing (previously point 3) is done, and the sentence that stood here was wrong.** Until 8 September 2026 the router node opened the request span and closed it in its own `finally`, so a live trace showed the routing decision and nothing after it — no agent spans, no tool calls, no handovers (`KNOWN_GAPS.md`). `run_agent_graph` now owns the span; agents trace their spans, ComplianceAgent traces its checker call, and `mark_agent_complete` records a handover to the next agent in the plan. Case 2.1 asserts all three on the stored trace.

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