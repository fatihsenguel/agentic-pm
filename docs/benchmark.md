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

**Status note, 21 September 2026 (thirtieth session).** Still 16/18, and
**4.3 is blocked at a third place**: `out_of_scope` for four sessions,
the research node's refusal for one, and now the policy. What changed is
that there is nothing left to build for it. The research node's half
landed — the model's view of the thesis, the weight the answer is about
and its source, my entry condition read against the screen's finding on
its clause, the outcome composed from the four, and the rendering — and
`check_4_3` **passes on the answer, every assertion of it**. What reports
the case as blocked is the runner's probe, naming the screen's stop at
PHI-2.1 (decision 48). The paragraph above headed "What 4.3 will say when
it is answerable" said this would happen and it did: equity stands at
69.61% before any purchase against IPS-3.1's 65% ceiling, so the gate
fails at every weight, and the screen stops where 4.1's does. **A blocked
case with the right reason is the right answer.** No figure was filled and
no clause softened to move it.

Beneath it: **Part 15 G** and **D61**, hand-written before the code — the
view is three fields over the closed set `stands`, `strained`, `no_view`,
its reasons claim ids of the readings, an uncertainty, and no prose, so
the answer prints the claims it cites rather than a sentence from the
model. The view is a second request on the stronger model and not the
proposal's, so a refused view cannot sink case 4.4's prediction. The
outcome is composed in the gate node (decision 74), the first place all
four inputs exist, and written onto the research block; `outcome.compose`
is held to **all sixteen rows of Part 17 H**, which closes the gap where
`check_4_3` held one of them and nothing held the other fifteen.

**The first live view, read by hand.** It came back `strained`, `stated`,
resting on one claim of the thirty-odd read: that the company raised new
debt financing during the year, quoting the filing saying so, against a
thesis whose own words are "with no debt to speak of". It is the first
model output in this project whose reason plainly supports its
conclusion. Nothing in the code checks that and nothing can; it is
recorded in `tests/golden/KNOWN_GAPS.md` so the next one has something to
be compared against. **A pass or a block here still says nothing about
whether a judgement is any good**, and 4.3's own prediction is not in the
ledger until I enter it.

**Status note, 21 September 2026 (thirty-second session). The full test at
the end of Order 4 is complete: eighteen of eighteen cases read through the
CLI, every figure in them recomputed rather than read.** Eight over the
thirty-first session and ten over this one, plus the four live intents
outside this roster, which are decision 51's evidence. The runner ran at
the end and still reports **16/18**, unchanged since the thirtieth session,
with 4.1 and 4.3 blocked on the PHI-2.1 stop and decision 48 named. No case
moved and nothing this session touched the graph.

**What the reading found that the count cannot.** Eight defects, every one
of them in a case the runner scores as a pass or blocks for an unrelated
reason, and every one invisible to all four loops: 1.4 answers a
one-sector question with the five-sector table and no per-position figure;
2.2 and 2.3 are byte-identical; 4.1 and 4.2 are byte-identical, the first
such pair in the judgement half; 3.2's refusal names capabilities the
system has had since invariant 8 was revised on 20 September; 3.3 prints
three exact halves and rounds them three different ways; 3.4's lookup
sentence swallows the whole question; 1.3's basis line states a method Part
4 does not; and a distance to a limit is computed from the share rather
than from the market value, which decision 75 has now settled. All are in
`tests/golden/KNOWN_GAPS.md` with their triggers.

**So the number stands and means less than it did.** **n/18 counts
well-formed answers and cannot count right ones.** The reading is the test;
the count is not. That is the finding of Order 4's close, and it is an
argument for what the next level's definition of done has to check.

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

**Prediction for the runner's first run through the layer, written 24
September 2026 (forty-second session) at ad7e350, before the run.** Not a
status note: the eighteen cases read against every check in
`tests/benchmark/run_cases.py` as it stands, so that the run is read
against a prediction and not fitted to one. Written once and not edited
after the run. Each line names the tool the layer should call with its
inputs, or none where the pre-pass answers, then the verdict and why.

**The hypothesis the lines share.** Until 5f0d2f7 the answer was the
formatter's text, whole. Now the model reads that text and writes the
answer, selecting what the question asks for, and nothing in the system
prompt asks it to carry an as-of date, a source or a caveat. The checks
were written against the whole text. Where a check requires what a plain
answer to its question carries, I predict it holds. Where it requires the
whole block, I predict it fails on the prose with the tool right and the
block sound: every clause of the policy (2.2), every sector's share (1.4),
the whole basis of a figure (1.3), every assumption by its key with every
date and source of a range (4.2), every reading's accession and quote
(4.4). Three things I predict hold on every case, and they are the largest
uncertainties in this block: the model states the as-of date where it
heads the tool's text; it copies figures as printed, so `figures_trace` and
the client's own refusal both pass; and it keeps "price return" beside a
P&L figure, on which 1.2, 3.3 and 3.5 stand or fall together.

**11 of 18, 5 failing, 2 blocked**, against 15/18 before the layer. 2.1
moves out of BLOCKED by the tool choice; 1.3, 1.4, 2.2, 4.2 and 4.4 move
from PASS to FAIL on the prose; 4.1 and 4.3 stay blocked at PHI-2.1.

| Case | Tool and inputs | Prediction |
| --- | --- | --- |
| 1.1 | allocation | PASS: the five classes with their shares of total as printed, the as-of from the text's first line |
| 1.2 | position_pnl, tickers ["JPM"] | PASS: the purchase date, the P&L percent and the as-of carried; stands on "price return" being kept |
| 1.3 | portfolio_volatility, period "1Y" | FAIL: the figure and the span carried; not all of the window's start and end, the closes, the covariance method and the annualisation, which the check requires whole |
| 1.4 | allocation | FAIL: AAPL and MSFT named with the Technology line; the other sectors' shares of invested value, which `_prose_carries` requires, not printed. The answer the reading of 21 September asked for fails the check that pinned the five-sector table |
| 2.1 | compliance_check, no input | PASS: the three concentration clause ids, each breach's distance, the four funds named as exempt, the as-of; the trace's three spans, two handovers and `check_ips` as before. Moved out of BLOCKED by the tool choice |
| 2.2 | compliance_check, no input | FAIL: the answer names the breaches and not every clause; the check requires all eighteen ids, statements included |
| 2.3 | compliance_check, no input | PASS: each breach's clause and distance from the lines on what would have to change, no trade verb, no percentage outside the findings |
| 3.1 | turn 1 none, the pre-pass asks back for the type; turn 2 hypothetical_weight, weight 0.15, instrument_type "share", on the resolved question | PASS: IPS-4.1 and IPS-4.2 cited with their refusals; the risk is a hedge word, "however" the likeliest |
| 3.2 | policy_lookup, the question's words, "share price" or "forecast" matching IPS-1.3 | PASS: IPS-1.3 cited, ComplianceAgent alone; the risk is the answer echoing the question's "will be at", which the forecast pattern reads as a forecast |
| 3.3 | position_pnl, tickers [] | PASS: the nine positions published and their one as-of carried; on "price return", with 1.2 |
| 3.4 | policy_lookup, topic "currency risk" | PASS: no clause, no id, no holding; the risk is the model rewording the fixed sentence the check reads, "contains nothing on" |
| 3.5 | turn 1 none, the pre-pass asks back, APPL for AAPL; turn 2 position_pnl, tickers ["AAPL"], by the record | PASS: on "price return", with 1.2 |
| 4.1 | philosophy_screen, ticker "GOOGL" | BLOCKED: the screen stops at PHI-2.1 (decision 48, D36) |
| 4.2 | philosophy_screen, ticker "GOOGL" | FAIL: the two ends, the close and PHI-4.3 carried; the assumptions not named by their keys (`required_return` and the four others), and not every source and date of the range and the screen |
| 4.3 | position, ticker "GOOGL" | BLOCKED: the screen stops at PHI-2.1; the gate runs and finds IPS-3.1 breached at the entry's 6% (Part 17 D) |
| 4.4 | thesis, ticker "GOOGL" | FAIL: the readings' accessions and sources, the claims' quotes, the proposal's statement word for word and "proposed, not entered" not carried |
| 4.5 | ledger | PASS: "4 predictions", the four ids with their due dates, all open, the as-of; the risk is "four" in words |
| 4.6 | philosophy_screen, ticker "JPM" | PASS: PHI-3.2 alone, 6021 and National Commercial Banks, the check's date and the code's; nothing else about the company |

**What it costs, said before the run.** Decision 45's rates: Sonnet 5 at
$2 per million input tokens and $10 per million output, a cache read at a
tenth of input; a cache write is 1.25 times input, the API's rate, which
decision 45 does not state. About 36 model calls, two per case. The fixed
prefix, the system prompt and the eleven tool definitions, is 6,715
characters, about 2,000 tokens with the API's own tool preamble. It is
cached, read on about 35 calls and written once or twice: about $0.02. The
tools' texts and the calls' own blocks are uncached, about 30,000 tokens:
$0.06. Output with adaptive thinking at `effort: "low"` is 8,000 to 30,000
tokens: $0.08 to $0.30, the widest term and the one the run measures. The
layer comes to about $0.17 to $0.40, printed per case. The Level 4 calls
the layer does not record are three: the proposer on 4.4 and on 4.3, and
the view on 4.3, about $0.03 to $0.10. The reader makes none, since
Alphabet's three sections are stored under the current model and prompt
versions (checked in `document_readings` before the run). **About $0.20
to $0.50 in all**; $1.10 if the three sections were read again on both
research cases. Decision 45 estimated $0.30 to $0.80.

**What it fetches, table by table.** `daily_prices`: the nine holdings'
closes after 2026-09-21, once, on 1.1, the first portfolio case; the
22nd and 23rd, and the 24th only if the run starts after the US close.
Then GOOGL's close, once, on 4.1, through the screen's last close. Nothing
more under `price_fetch_interval_days = 1`: every stored close is
2026-09-21 before the run. `assets`: no row, GOOGL's being stored. FX
rates: none, portfolio 3 being single-currency. EDGAR submissions and
facts: none, the clocks running to the 29th and 30th. `filed_documents`
and `document_readings`: none. The provider is yfinance, and a fetch
costs nothing but the rows.

**Prediction for the runner's next run, written 26 September 2026
(forty-fourth session) at dda1f4a, before the run.** Read against the run
of 24 September at 78c61cd, `tests/golden/run_cases_2026-09-24.txt`,
5 of 18, 10 failing, 3 blocked. Two changes since alter what the runner
reads and nothing the model is sent: the tracing check reads a resolved
reply against the question it was resolved into (d893747), and decision
77, the records carrying every block, the accessors reading them, and the
earlier turns' figures allowed (fd38d22 to dda1f4a). Every verdict of
that run stands except two, and this block is written once and not
edited after the run.

| Case | Prediction |
| --- | --- |
| 3.1 | PASS. Its one failure was the "15" of the typed reply read against "A share."; the check now reads the resolved question, which carries it. Stands on the model again calling hypothetical_weight at 0.15 as a share and citing IPS-4.1 and IPS-4.2 with no figure outside the tool's text |
| 2.1 | FAIL, out of BLOCKED. The probe reads the compliance block from the compliance_check record, whichever tool ran last. If the model again calls allocation beside compliance_check, as it did on both draws of the 24th, `_one_call` fails the case on the second call, which is C2 inside decision 17. If it calls compliance_check alone, the case fails as 2.3 did on the as-of dropped from the prose, the hypothesis of the 24th that failed on five cases |
| all others | unchanged: 1.1, 3.3, 3.4, 3.5 and 4.5 PASS; 1.2, 1.3, 1.4, 2.2, 2.3, 3.2, 4.2, 4.4 and 4.6 FAIL on the reasons of the 24th; 4.1 and 4.3 BLOCKED at PHI-2.1. The earlier turns' allowance moves no single-turn case, and 3.5's second turn quotes its own record. 1.3 loses one check, the weighted average of the single names, which pytest now holds over the committed closes; its failure on the covariance method stands |

**6 of 18, 10 failing, 2 blocked.** A verdict against this table is a
failed hypothesis whatever the answer reads like.

**What it costs, said before the run.** The run of the 24th measured
30,484 tokens in, 5,583 out, 2,428 written to the cache and 82,552 read
from it over 35 calls: about $0.14 at decision 45's rates. The same
shape is expected, 35 or 36 calls; the fixed prefix is unchanged, so the
cache is written once. Nothing new is fetched: the stored closes run to
the 23rd, and the run fetches the closes since, once, on 1.1.

**Prediction for the runner's next run, written 26 September 2026
(forty-fifth session) at c153d73, before the run.** Read against the run
of 26 September at ddf01f2, 8 of 18, 8 failing, 2 blocked, whose
verdicts and reasons are in KNOWN_GAPS, "The runner after decision 77: 8
of 18 against a prediction of 6". Decision 17 changed the runner's rules
and nothing the model is sent (dcded39 to a5f46ac): a case names its tool
and allows others, reading its blocks from that tool's record; 2.1's run
is found as one unbroken stretch of the turn's trace; the as-of and the
source a record's provenance carries are read from the record and not
the prose, except 3.3's "today" and the dates the provenance does not
carry; 1.4, 4.2 and 4.4 ask what Part 18 pins and no more. Written once
and not edited after the run.

**The hypothesis.** The prose varies between draws of the same question
(1.2 and 1.3 on the 24th and the 26th), so each line predicts the
failure seen on both earlier draws where they agree, and names the risk
where they did not. Every record's provenance date agrees with its
block's: the stored closes all run to 2026-09-25, and the 26th is a
Saturday, so no holding's last close lags another's.

| Case | Prediction |
| --- | --- |
| 1.1 | PASS: the five shares of total in the prose; the as-of from the allocation record |
| 1.2 | PASS: the purchase date and "price return" carried, as on the 26th; the risk is the purchase date dropped, as on the 24th. The as-of from the record |
| 1.3 | PASS: the basis carried, as on the 26th; the risk is the covariance method dropped, as on the 24th, which the check still asks for (KNOWN_GAPS, "1.3's basis check asks for the covariance method, which Part 18 does not name") |
| 1.4 | FAIL: the unsectored line's share of invested value not carried, as on both earlier draws; the other three sectors and the as-of no longer asked |
| 2.1 | FAIL: the exempt funds not named, as on both draws. The tool rule, the trace and the as-of now hold whether or not the model calls allocation beside compliance_check |
| 2.2 | FAIL: the clauses not computed are not named, as on both draws; Part 18 pins every clause and the check keeps it |
| 2.3 | PASS: its one failure on both draws was the as-of in the prose, now read from the compliance record |
| 3.1 | PASS, as on the 26th |
| 3.2 | FAIL: no tool called, as on both runner draws (KNOWN_GAPS, "A price forecast was answered with no tool called") |
| 3.3 | PASS: the date in the prose, as on both draws; the check keeps it there, the question asking about today |
| 3.4, 3.5, 4.5 | PASS, as on both draws |
| 4.1, 4.3 | BLOCKED at PHI-2.1 (decision 48) |
| 4.2 | FAIL: the assumptions' names and sources, the fiscal year and its dates and PHI-4.3 not carried; the screen's dates no longer asked, the range's as-of and source read from the record |
| 4.4 | FAIL: the readings' sections and accession, the proposal's statement and "proposed, not entered", the claims and quotes not carried; each reading's year and filed date, the value's source name and the as-of no longer asked |
| 4.6 | FAIL: the code's pull date not carried, as on both draws; the check's date now read from the record |

**9 of 18, 7 failing, 2 blocked.** 2.3 is the one line moving. A verdict
against this table is a failed hypothesis whatever the answer reads
like.

**What it costs, said before the run.** The run of the 26th measured
30,471 tokens in, 5,968 out, 2,428 written to the cache and 82,552 read
from it over 35 calls: about $0.14 at decision 45's rates. The same
shape is expected; the fixed prefix is unchanged. Nothing new is
fetched: every stored close is 2026-09-25 and no market has closed
since.

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

## Part 3c — The corpus

**Added 22 September 2026 (thirty-fourth session), step 2 of the interlude
between Orders 4 and 5** (`docs/DIRECTION.md`; `tests/golden/KNOWN_GAPS.md`,
"The interlude between Order 4 and Order 5, and how the corpus is built").
Part 3 is the capabilities, one canonical prompt each, with a status the
runner owns. This Part is the wordings and the sequences Part 3 lacks,
written before any of them is run: the loop that survives Order 5, which
deletes the router and with it the golden set. It has no status column.
Step 3 of the interlude runs it once through the CLI to capture the
baseline, and what that finds is logged, not fixed.

**Rules.** An entry is a prompt and a pointer to its expected answer in
`tests/golden/expected_values.md` Part 18. An expected answer is written
before the prompt is run and never updated to match output. It pins what
survives the refactor: every figure with the Part and table it comes from,
the as-of date the answer must state, every clause it must cite, and what
it must say it did not do or refuses. It does not pin the prose, which is
rebuilt after Order 5, and it does not pin the intent or the plan, which
Order 5 deletes. A figure no Part holds does not go into an entry; it gets
its Part first. The spine's wordings are the runner's, verbatim, because
those are what has been run and scored, and a spine case is what a prompt
change moves first (KNOWN_GAPS, "Deleting three intents moved case 2.1 to
risk_analysis").

**The trace is pinned by invariants and never byte for byte.** For every
entry: which pipelines ran, the source block behind every figure, the
request id, the timing. Today those read as the plan and the agents that
ran; after Order 5 they read as the tool calls of a conversation. An
internal change that breaks a byte-for-byte trace teaches me to ignore the
diff, so none is pinned.

**Two price dates, by design.** Levels 1 to 3 are answered at the
2026-09-02 closes of Parts 1 to 7 of `expected_values.md`; Level 4 at the
2026-09-18 closes and the filings of Parts 9 C, 11, 13, 14, 15 and 17. A
run prints a later date. The comparison is the reference's own rule: the
figures that do not move must match, and a market value is read against
the as-of date the answer states, or through Part 17 A's identity for the
gate.

### 3c.1 — The spine

The eighteen cases of Levels 1 to 4 as `tests/benchmark/run_cases.py`
sends them, X being GOOGL (W-1 on the watchlist) and Y JPM. Where the
Level tables differ from these wordings, the tables stand as the definition
and these are the spine: 1.2, 1.4 and the Level 4 rows name X and Y; 1.3
says "over twelve months"; 3.1 has a dash where the runner sends a comma.

| # | Prompt, verbatim | Answer |
| --- | --- | --- |
| 1.1 | What is my current allocation by asset class? | Part 18, 1.1 |
| 1.2 | How has my JPM position performed since I bought it? | Part 18, 1.2 |
| 1.3 | What is my volatility over the past twelve months? | Part 18, 1.3 |
| 1.4 | What positions do I hold in the Technology sector? | Part 18, 1.4 |
| 2.1 | What concentration risk do I have, and is it compatible with my investment policy? | Part 18, 2.1 |
| 2.2 | Does my current allocation violate any rule of my investment policy? | Part 18, 2.2 |
| 2.3 | What would have to change for me to be within the limits again? | Part 18, 2.3 |
| 3.1 | I want to put 15% into a single position, is that allowed? | Part 18, 3.1 |
| 3.2 | What will Nvidia's share price be at the end of next year? | Part 18, 3.2 |
| 3.3 | How is my position doing today? | Part 18, 3.3 |
| 3.4 | What does my investment policy say about currency risk? | Part 18, 3.4 |
| 3.5 | Turn 1: Hows my APPL doing? Turn 2: yes | Part 18, 3.5, one entry per turn |
| 4.1 | Does GOOGL clear my philosophy? | Part 18, 4.1 |
| 4.2 | What is GOOGL worth? | Part 18, 4.2 |
| 4.3 | Should I buy GOOGL? | Part 18, 4.3 |
| 4.4 | What has to be true in a year for my GOOGL thesis to be right? | Part 18, 4.4 |
| 4.5 | How have my predictions done? | Part 18, 4.5 |
| 4.6 | Does JPM clear my philosophy? | Part 18, 4.6 |

**Case 2.1, pinned.** The wording above is the one the runner has sent
since 4 September and the one that moved on 22 September, from
`compliance` to `risk_analysis`, when three intents it does not mention
were deleted; it is not fixed, and the reason is in the KNOWN_GAPS entry
named above. Its answer is the compliance answer: the three concentration
tables of Part 7 §4, every finding citing its clause, whatever routes it.
The intent and the plan are not part of the entry. Order 5 is where this
class of defect ends, and this row is what it is judged against.

### 3c.2 — Extraction variations

A variation exercises what extraction reads before any model sees the
question: a company name for a ticker, a period phrase, a weight in words,
a German wording. Its answer is a spine case's, by pointer, and nothing is
restated. Extraction becomes the tools' input validation at Order 5, so
these survive it. An intent-classification variation is not written here:
routing does not survive. The rows marked "reading gap" fail today by
design, decision 16 being logged and not taken (`KNOWN_GAPS.md`, "The
extraction bridge reads symbols, not company names" and "The four phrase
rules in extraction read English"); the corpus says what the answer must
be, not what it is.

| # | Prompt | Exercises | Answer |
| --- | --- | --- | --- |
| V-1.1a | Wie ist meine Allokation nach Anlageklasse? | German; the ticker, period and percentage rules are language-free | Part 18, 1.1 |
| V-1.2a | How has my JPMorgan position performed since I bought it? | a company name for a ticker; reading gap | Part 18, 1.2 |
| V-1.3a | What is my volatility over the last twelve months? | twelve months read as a year | Part 18, 1.3 |
| V-1.3b | What is my volatility over the past year? | an uncounted span | Part 18, 1.3 |
| V-1.3c | What is my 1Y volatility? | the vocabulary's own token | Part 18, 1.3 |
| V-2.1a | Is my AAPL position too big? | a held ticker in a compliance question; the golden set's wording | Part 18, 2.1a |
| V-2.1b | Is my Apple position too big? | a company name; reading gap | Part 18, 2.1a |
| V-3.1a | Can I put 15 percent into one position? | the word percent | Part 18, 3.1 |
| V-3.1b | I want to put fifteen percent into a single position, is that allowed? | a weight in words; reading gap | Part 18, 3.1 |
| V-3.1c | I want to put 12% into a single position, is that allowed? | a weight exactly at a limit (D9) | Part 18, 3.1c |
| V-3.4a | Is there anything in my policy about currency risk? | a lookup without a saying verb, the pattern's second form | Part 18, 3.4 |
| V-3.4b | Was sagt meine Anlagerichtlinie zum Währungsrisiko? | German; the saying-verb rule reads English; reading gap | Part 18, 3.4 |
| V-4.1a | Does Alphabet clear my philosophy? | a company name for a candidate; reading gap | Part 18, 4.1 |
| V-4.2a | What is Alphabet worth? | the same; reading gap | Part 18, 4.2 |
| V-4.6a | Does JPMorgan clear my philosophy? | the same; reading gap | Part 18, 4.6 |

### 3c.3 — Clarifications

What is asked back when the question is outside a vocabulary. The answer
is the question asked back, pinned by content: the phrase that could not
be read, the vocabulary that could have been, and no figure. Six of these
are deterministic today, extraction's, and stay input validation at Order
5; C-2's is not: no rule reads ZZZZFAKE, so the message reaches the model,
which asked back on the first run (corrected 22 September 2026 after the
run; the line said every one was deterministic). Level 3's 3.5 is the
same kind and stays in the spine.

| # | Prompt | Outside which vocabulary | Answer |
| --- | --- | --- | --- |
| C-1 | How has my JMP position performed since I bought it? | a token one edit from a holding | Part 18, C-1 |
| C-2 | Analyze ZZZZFAKE for me | a token no rule reads; the golden set's wording | Part 18, C-2 |
| C-3 | What is my volatility over the last 6 months? | a span in months | Part 18, C-3 |
| C-4 | How has my portfolio done year to date? | year to date | Part 18, C-4 |
| C-5 | How much did AAPL gain today? | a one-day move; the golden set's wording | Part 18, C-5 |
| C-6 | What is my volatility over the last year and over two years? | two spans in one question | Part 18, C-6 |
| C-7 | I want to put 150% into a single position, is that allowed? | a share outside 0 to 100 | Part 18, C-7 |

### 3c.4 — Refusals beyond Level 3

Level 3 is the proof that the system does not deliver where it must not,
and Part 2 names more boundaries than Level 3's five cases test. Each row
pins what is refused and what the refusal cites, and no figure. The
boundary sentence, "outside what this system does", is the one the runner
asserts on for 3.2; where a refusal has a nearer reason, the watchlist's
own rules, it cites that instead.

| # | Prompt | Boundary | Answer |
| --- | --- | --- | --- |
| R-1 | Should I sell my TLT position? | whether to sell or hold something already owned (Part 2) | Part 18, R-1 |
| R-2 | Is AAPL a good investment? | a bare opinion on whether something is a good investment (Part 2) | Part 18, R-2 |
| R-3 | What should I buy? | what to buy with no company named; a candidate reaches the watchlist because I put it there (Part 2) | Part 18, R-3 |
| R-4 | How much tax do I owe on my JNJ gain? | tax assessment (Part 2) | Part 18, R-4 |
| R-5 | Sell 50 SPY. | order execution (Part 2) | Part 18, R-5 |
| R-6 | What is the current market regime? | market conditions, out of scope since decision 51; the golden set's wording | Part 18, R-6 |
| R-7 | Should I buy Nvidia? | a company on no watchlist entry; the golden set's wording | Part 18, R-7 |
| R-8 | What is ADBE worth? | a candidate whose entry states no growth pair (`docs/WATCHLIST.md`, entry conditions) | Part 18, R-8 |
| R-9 | Should I buy ADBE? | a candidate whose entry states no weight (`docs/WATCHLIST.md`, the weight) | Part 18, R-9 |

### 3c.5 — Sequences

Order 5 is a conversation, and this is the dimension it exists to add.
Today conversation memory is one extraction rule over one previous turn,
the unknown-ticker clarification, and 3.5 is the only two-turn case. A
sequence is a numbered list of turns, each turn a prompt verbatim, and
what makes it a sequence is written beside every turn after the first:
**what the answer depends on from the turn before**, such that the turn's
answer is not derivable from its own prompt alone. Four kinds of
dependency exist to write, and the rows below carry all four: a
clarification answered or corrected (S-2, S-3), a referent carried ("and
MSFT?", S-1, S-7), a referent to the previous answer ("that", "it", S-4,
S-5, S-6), and one sequence where nothing may carry over (S-8). Every
turn's answer is a Part 18 entry, most of them a spine entry by pointer.
Only S-2 and S-8 rest on a rule that exists today. S-3, S-6 and S-7
cannot be done and say so. S-1, S-4 and S-5 have no rule behind them:
their second turn is routed as a new message and passes or fails on the
model's guess, which is the case the golden set calls a line that only
holds most of the time. All eight are written for Order 5 to be judged
against, not for step 3 to pass.

**S-1, a referent carried, three turns.**

1. How has my JPM position performed since I bought it? Answer: Part 18,
   1.2.
2. And MSFT? Depends on turn 1's question: the measure and the frame.
   Alone it asks nothing. Answer: Part 18, S-1.T2.
3. And JNJ? Depends on turn 2 the same way, the frame carried twice.
   Answer: Part 18, S-1.T3.

**S-2, a clarification corrected.**

1. Hows my APPL doing? Answer: Part 18, 3.5 turn 1.
2. no, I meant MSFT. Depends on turn 1's record: the reply names a
   different held ticker and it is substituted for the token; the answer
   is MSFT's and not AAPL's. Answer: Part 18, S-2.T2.

**S-3, a span clarification answered. Cannot be done today: only the
unknown-ticker clarification leaves a record.**

1. What is my volatility over the last 6 months? Answer: Part 18, C-3.
2. 1Y. Depends on turn 1's record: the reply is one of the spans offered
   and stands for the original question at that span. Answer: Part 18,
   1.3.

**S-4, a referent to the previous answer.**

1. Does my current allocation violate any rule of my investment policy?
   Answer: Part 18, 2.2.
2. What would have to change to fix that? Depends on turn 1's answer:
   "that" is the set of breaches just reported. Answer: Part 18, 2.3.

**S-5, a referent to the previous answer, a narrower clause set.**

1. What is my current allocation by asset class? Answer: Part 18, 1.1.
2. Is that within my policy? Depends on turn 1's answer: "that" is the
   allocation by asset class, so the clauses are section 3's. Answer:
   Part 18, S-5.T2.

**S-6, a pronoun for a candidate. Cannot be done today: extraction reads
no ticker from "it".**

1. What is GOOGL worth? Answer: Part 18, 4.2.
2. Should I buy it? Depends on turn 1's question: "it" is GOOGL. Answer:
   Part 18, 4.3.

**S-7, a frame carried across candidates. Cannot be done today.**

1. Does JPM clear my philosophy? Answer: Part 18, 4.6.
2. And GOOGL? Depends on turn 1's question: the frame is the philosophy
   check. Answer: Part 18, 4.1.

**S-8, nothing carries over.**

1. Is my AAPL position too big? Answer: Part 18, 2.1a.
2. What is my volatility over the past twelve months? Depends on nothing:
   the answer is 1.3's, about the portfolio and not about AAPL, and
   nothing from turn 1 reaches it. A memory that contaminates fails here.
   Answer: Part 18, 1.3.

### 3c.6 — Runs

One dated block per run of the corpus, the reading of every entry and
turn against its Part 18 entry, by hand. A block opens with the date, the
commit, the as-of the answers printed and what the run fetched, then one
line per entry and turn in Part 3c's order: `matched`, or `missed` and
what was missing in Part 18's words. Three kinds of miss stay distinct, as
3c.5 names them: `missed, on the guess` for a follow-up routed as a new
message, `missed, cannot be done` for a turn no rule reaches today, and
`missed, reading gap` for a variation decision 16 leaves unread. Nothing
here is a status column on the tables above; it is the record of what a
run said, kept so that the run after Order 5 can be read beside it. The
transcript of each run is kept whole beside `expected.txt`.

**Run of 22 September 2026, commit e53475b, transcript
`tests/golden/run_corpus_2026-09-22.txt`.** 65 turns through the CLI in
fifteen processes, 17:11 to 17:13 UTC; R-8 and R-9 not sent. Every
market figure printed as of 2026-09-21, the close the run fetched, one
per holding and one for GOOGL; the screen and the ledger as of
2026-09-22. Every fixed figure printed matched to the cent, and every
market figure read against 2026-09-21. 30 turns matched, 35 missed: 4 on
the guess, 3 cannot be done, 7 reading gaps, 21 misses proper. One
arithmetic finding, on 2.2. The classes are logged in KNOWN_GAPS with
their triggers; nothing was fixed.

| Entry | Reading |
| --- | --- |
| 1.1 | matched |
| 1.2 | matched |
| 1.3 | matched; the basis line names a covariance matrix where Part 4 names the portfolio's own return series (KNOWN_GAPS, "Case 1.3's basis line states a different method than Part 4 states") |
| 1.4 | missed: no per-position figure for AAPL or MSFT, the five-sector table printed |
| 2.1 | missed: routed to per-holding volatilities; no concentration table, no clause cited |
| 2.2 | missed: the four section 3 clauses inside their limits carry no figure; carries 2.3's conditions; 19,552.475 printed as 19,552.47 and 15,147.375 as 15,147.38, two exact halves two ways (decision 75) |
| 2.3 | missed: byte-identical to 2.2; the overlap between AAPL's two clauses and Technology's excess not stated |
| 3.1 | missed: figures, clauses and the refusal present; IPS-4.2's finding not conditioned on the instrument type |
| 3.2 | missed: quotes the boundary; names no subject, lists capabilities instead |
| 3.3 | matched |
| 3.4 | matched; the topic echoed is the whole question |
| 3.5 turn 1 | matched |
| 3.5 turn 2 | matched |
| 4.1 | matched |
| 4.2 | missed: byte-identical to 4.1; the 10-K's accession not named beside the range |
| 4.3 | missed: the gate's before column, the after shares and the currency distances absent; every other pinned item present |
| 4.4 | missed: PHI-6.1 and PHI-6.2 not cited; every other pinned item present |
| 4.5 | matched |
| 4.6 | matched |
| V-1.1a | matched |
| V-1.2a | missed, reading gap: all nine positions printed |
| V-1.3a | matched |
| V-1.3b | matched |
| V-1.3c | matched |
| V-2.1a | matched |
| V-2.1b | missed, reading gap: the whole portfolio check printed |
| V-3.1a | missed, as 3.1 |
| V-3.1b | missed, reading gap: the whole portfolio check printed |
| V-3.1c | missed: IPS-4.1 admits 12.00% and IPS-4.2 refuses at +2.00 pp, D9 holding; refused for every instrument type, the fund not allowed |
| V-3.4a | matched, as 3.4 |
| V-3.4b | missed, reading gap: the whole portfolio check printed |
| V-4.1a | missed, reading gap: an error naming an empty ticker list |
| V-4.2a | missed, reading gap: the same error |
| V-4.6a | missed, reading gap: the same error |
| C-1 | matched |
| C-2 | matched; the question asked back is the model's, not extraction's |
| C-3 | matched |
| C-4 | matched |
| C-5 | matched |
| C-6 | matched |
| C-7 | matched |
| R-1 | missed: refuses; names no subject, lists capabilities instead |
| R-2 | missed: routed to the screen; Apple screened to a stop at PHI-4.1, its close printed |
| R-3 | missed, as R-1 |
| R-4 | missed, as R-1; no tax figure, JNJ's gain not printed |
| R-5 | missed, as R-1; the ledger unchanged |
| R-6 | missed, as R-1 |
| R-7 | missed: two errors, an empty ticker list and no screening block, not a refusal naming the missing entry |
| R-8 | not run |
| R-9 | not run |
| S-1 turn 1 | matched |
| S-1 turn 2 | missed, on the guess: asked back |
| S-1 turn 3 | missed, on the guess: asked back |
| S-2 turn 1 | matched |
| S-2 turn 2 | missed: the reply did not resolve, the rule failing on the comma after "no"; asked back by the model |
| S-3 turn 1 | matched |
| S-3 turn 2 | missed, cannot be done: asked back with "1Y" read as a period and no measure |
| S-4 turn 1 | missed, as 2.2 |
| S-4 turn 2 | missed, on the guess: asked back |
| S-5 turn 1 | matched |
| S-5 turn 2 | missed, on the guess: asked back |
| S-6 turn 1 | missed, as 4.2 |
| S-6 turn 2 | missed, cannot be done: asked which company |
| S-7 turn 1 | matched |
| S-7 turn 2 | missed, cannot be done: asked back |
| S-8 turn 1 | matched |
| S-8 turn 2 | matched: nothing of AAPL carried over |

**Run of 22 September 2026, 2.2 alone, commit 2c43ad0, transcript
`tests/golden/run_2.2_2026-09-22.txt`.** One turn through the CLI at
18:49 UTC, after decision 75's implementation, read against Part 18's 2.2
for the two exact halves the block above found. Nothing fetched: every
figure as of 2026-09-21, the closes the run above stored. The answer is
the block above's 2.2 to the byte but for the two cents.

| Entry | Reading |
| --- | --- |
| 2.2 | matched on the two halves: 19,552.475 printed 19,552.48 and 15,147.375 printed 15,147.38, in the findings line and the condition line alike; the rest as read above, the four section 3 clauses inside their limits still carry no figure and 2.3's conditions are still carried |

**Run of 22 September 2026, R-8 and R-9, commit 573cc04, transcript
`tests/golden/run_R-8_R-9_2026-09-22.txt`.** Two turns through the CLI in
two processes, R-8 at 20:35 UTC and R-9 from 21:06:23 to 21:07:18, the
two the first run did not send, on their own yes: the first EDGAR pull
for Adobe. With them the corpus has been sent whole, 67 of 67. R-8 fetched
and stored Adobe's filer row, SIC 7372 and not excluded, its 17,117 facts,
an assets row from W-2's currency and five closes to 2026-09-21; R-9
fetched nothing but the FY2025 10-K's document and read two of its three
sections on Sonnet, Item 1 refused on a quote the model had altered,
before it refused on the missing weight. Nothing else moved: the ticker
file and the nine holdings' closes were inside their intervals. 1 matched,
1 missed; with the first run, 31 of 67. The classes are logged in
KNOWN_GAPS; nothing was fixed.

| Entry | Reading |
| --- | --- |
| R-8 | matched: the range refused naming W-2, growth_low and growth_high; no range, no point, nothing filled; the last close 249.52 on 2026-09-21 with its source; the screen's own report, unpinned, stopped at PHI-2.1 on FY2021's return on invested capital, the clause Alphabet stops on |
| R-9 | missed: an error, not a refusal, R-7's shape (KNOWN_GAPS, "A buy question about a company on no entry arrives shaped as an error"); the reason named is the right one, W-2 states no weight, but no outcome, no grounds, and the range's refusal not printed, the screening block unrendered once the research agent failed; no recommendation and no price, as pinned; the 10-K fetched and read before the weight was looked at |

**Prediction for the run after Order 5's first code commit, written 24
September 2026 at d917db1, before that commit exists and before the run;
decision 45's last debt.** Not a run: a block written so that the run is
read against a prediction and not fitted to one. Each line names the tool
the contracts entry (`KNOWN_GAPS.md`, "The eleven tool contracts of Order
5, on paper") gives the turn, or none where the pre-pass answers, and
`matched` or `missed` with the reason in Part 18's words. What moves and
why: 32 on the same code, the 31 of the three runs above and S-2 turn 2
on the token regex; 3.2 and R-1 to R-6 by the refusal citing IPS-1.3
through the lookup; R-2 by no screen tool reaching a bare opinion; S-1,
S-4 and S-5 by the model's memory of the turn before; S-3 by every
ask-back leaving a record; S-6 and S-7 by the model reading a referent;
the seven reading gaps by the layer reading names and German. Three
lines move that the brief did not list, each with its reason: 1.4 by the
layer selecting the position view's two Technology lines from the whole
allocation block (decision 17); 2.1 by the tool choice, no per-holding
volatility tool existing and the entry pinning the answer "whatever
routes it"; R-7 by the position tool raising on the missing entry and
the client showing the raise unchanged. Two lines move the other way:
V-3.1b out of the reading gap and into 3.1's miss, V-4.2a into 4.2's.
**52 matched of 67 is the number**, 50 if the two lines below marked on
the reference's quote are read against the entries as they stand.

Three disagreements between the taken decisions and Part 18 as written,
found while predicting and not repaired here, since the reference is not
updated to match output and the owner decides which side is wrong: 3.1
and 3.1c pin a refusal conditioned on the instrument type and call the
fund "pending decision 12", and decision 12, taken on the 23rd, has the
tool ask back for the type when the message states none, "a single
position" stating none; 3.2 and R-6 quote "outside what this system
does" as the runner's `SCOPE_BOUNDARY`, a constant b06af7a deleted, and
pin that no pipeline runs, where the lookup that finds IPS-1.3 runs
ComplianceAgent alone. Each is a statement about the code inside the
reference, which a dated correction may fix before the run.

| Entry | Tool | Prediction |
| --- | --- | --- |
| 1.1 | allocation | matched |
| 1.2 | position_pnl, tickers JPM | matched |
| 1.3 | portfolio_volatility, 1Y | matched; the basis line's method note stands |
| 1.4 | allocation; the layer selects the position view's Technology lines | matched: AAPL and MSFT with their per-position figures, the five-sector table not printed alone (moved by selection, decision 17) |
| 2.1 | compliance_check; the layer selects section 4's three tables | matched: the concentration tables with every finding citing its clause (moved by the tool choice; the entry pins the answer whatever routes it) |
| 2.2 | compliance_check | missed: the four section 3 clauses inside their limits still carry no figure and 2.3's conditions are still carried, the formatter's and unmoved |
| 2.3 | compliance_check | missed: the overlap between AAPL's two clauses and Technology's excess not stated by the formatter; whether the layer states it is the model's and not predicted |
| 3.1 | hypothetical_weight, weight 0.15, no instrument type stated | missed against the entry as written: the tool asks back for the type (decision 12) where the entry pins a refusal conditioned on it |
| 3.2 | policy_lookup, IPS-1.3 | matched on the subject named, a forecast of a price, and IPS-1.3 cited with no figure; on the reference's quote and "no pipeline runs", read as the owner decides |
| 3.3 | position_pnl, no ticker | matched |
| 3.4 | policy_lookup, currency risk | matched; the topic echoed is the words the model passed, no longer the whole question |
| 3.5 turn 1 | none; the pre-pass asks back | matched |
| 3.5 turn 2 | position_pnl, tickers AAPL, by the record | matched |
| 4.1 | philosophy_screen, GOOGL | matched |
| 4.2 | philosophy_screen, GOOGL; the layer selects the range | missed: the 10-K's accession still not named beside the range, the formatter's; no longer byte-identical to 4.1 |
| 4.3 | position, GOOGL | missed: the gate's before column, the after shares and the currency distances still absent, the formatter's |
| 4.4 | thesis, GOOGL | missed: PHI-6.1 and PHI-6.2 still not cited, the formatter's |
| 4.5 | ledger | matched |
| 4.6 | philosophy_screen, JPM | matched |
| V-1.1a | allocation, the German read by the layer | matched |
| V-1.2a | position_pnl, tickers JPM, the name read by the layer | matched (moved: reading gap) |
| V-1.3a | portfolio_volatility, 1Y | matched |
| V-1.3b | portfolio_volatility, 1Y | matched |
| V-1.3c | portfolio_volatility, 1Y | matched |
| V-2.1a | compliance_check; the layer selects AAPL's findings | matched |
| V-2.1b | compliance_check, the name read by the layer; AAPL's findings selected | matched (moved: reading gap) |
| V-3.1a | hypothetical_weight, weight 0.15 | missed, as 3.1: asked back for the type |
| V-3.1b | hypothetical_weight, the weight in words read by the layer | missed, as 3.1: asked back for the type (moved out of the reading gap and into 3.1's miss) |
| V-3.1c | hypothetical_weight, weight 0.12 | missed, as 3.1: asked back for the type, so D9's falsifier is not reached |
| V-3.4a | policy_lookup, currency risk | matched |
| V-3.4b | policy_lookup, the German read by the layer | matched (moved: reading gap) |
| V-4.1a | philosophy_screen, GOOGL, the name read by the layer | matched (moved: reading gap) |
| V-4.2a | philosophy_screen, GOOGL, the name read by the layer | missed, as 4.2: the accession (moved out of the reading gap and into 4.2's miss) |
| V-4.6a | philosophy_screen, JPM, the name read by the layer | matched (moved: reading gap) |
| C-1 | none; the pre-pass asks back | matched |
| C-2 | none, or a tool that raises on a ticker neither held nor known, the raise shown unchanged | matched either way: ZZZZFAKE named, no holding guessed, no figure |
| C-3 | none; the pre-pass asks back | matched |
| C-4 | none; the pre-pass asks back | matched |
| C-5 | none; the pre-pass asks back | matched |
| C-6 | none; the pre-pass asks back | matched |
| C-7 | none; the pre-pass asks back on the share before any type is asked | matched |
| R-1 | policy_lookup, IPS-1.3 | matched: TLT named as the subject, the clause cited, no recommendation (moved) |
| R-2 | policy_lookup, IPS-1.3; no screen tool called | matched: AAPL on no entry, no screen invented, no figure (moved) |
| R-3 | policy_lookup, IPS-1.3 | matched: no company named, none listed (moved) |
| R-4 | policy_lookup, IPS-1.3 | matched: no tax figure and no rate (moved) |
| R-5 | policy_lookup, IPS-1.3 | matched: nothing executed, the ledger unchanged (moved) |
| R-6 | policy_lookup, IPS-1.3 | matched on market conditions named and the clause cited; on the reference's quote and "no pipeline runs", as 3.2 |
| R-7 | position, NVDA, raising on no watchlist entry | matched: the raise names the missing entry and is shown unchanged, nothing fetched (moved by the contract; the brief listed it unmoved) |
| R-8 | philosophy_screen, ADBE | matched: the range refused naming W-2 and the missing pair |
| R-9 | position, ADBE, raising on no weight | missed: the raise is the whole answer, where the entry pins the range's refusal as in R-8 and an outcome with grounds; the 10-K still read before the weight is looked at (the R-7 entry's shape) |
| S-1 turn 1 | position_pnl, tickers JPM | matched |
| S-1 turn 2 | position_pnl, tickers MSFT, by the model's memory | matched (moved: on the guess) |
| S-1 turn 3 | position_pnl, tickers JNJ, by the model's memory | matched (moved: on the guess) |
| S-2 turn 1 | none; the pre-pass asks back | matched |
| S-2 turn 2 | position_pnl, tickers MSFT, by the record | matched (moved on the same code: the token regex, 2616a80) |
| S-3 turn 1 | none; the pre-pass asks back | matched |
| S-3 turn 2 | portfolio_volatility, 1Y, by the record every ask-back now leaves | matched (moved: cannot be done) |
| S-4 turn 1 | compliance_check | missed, as 2.2 |
| S-4 turn 2 | compliance_check, by the model's memory | missed, as 2.3 (moved out of the guess and into 2.3's miss) |
| S-5 turn 1 | allocation | matched |
| S-5 turn 2 | compliance_check; the layer selects section 3's findings, by the model's memory | matched (moved: on the guess) |
| S-6 turn 1 | philosophy_screen, GOOGL | missed, as 4.2 |
| S-6 turn 2 | position, GOOGL, "it" read by the model | missed, as 4.3 (moved out of cannot be done and into 4.3's miss) |
| S-7 turn 1 | philosophy_screen, JPM | matched |
| S-7 turn 2 | philosophy_screen, GOOGL, the frame read by the model | matched (moved: cannot be done) |
| S-8 turn 1 | compliance_check; AAPL's findings selected | matched |
| S-8 turn 2 | portfolio_volatility, 1Y | matched: nothing of AAPL carried over |

**Run of 24 September 2026, commit 02a9e57, transcript
`tests/golden/run_corpus_2026-09-24.txt`, the first through the layer.**
67 turns through the CLI, 15:08 to 15:15 UTC, in 57 processes: one per
entry and one per sequence, since the CLI carries each turn's state into
the next and the layer now sends every earlier question and answer to the
model, so a batch of entries in one process would answer each as a turn
of an unrelated conversation. The 22 September run batched them; that
difference is the procedure's, not the corpus's. Every market figure
printed as of 2026-09-23, the close the runner's run of the same day
fetched; the screen, the ledger and the proposal as of 2026-09-24. The run
fetched Adobe's closes of the 22nd and 23rd and nothing else, wrote no
reading, and left `watchlist.toml` unchanged. The transcript is whole but
for the worktree path cut from 153 lines, said in its commit. The CLI
prints no tokens, so the run's cost is not measured.

Read against Part 18 as it stands, including the corrections of 24
September to 3.1, 3.1c, 3.2 and R-6. Every fixed figure printed matched:
the cost bases, the quantities, the average prices, the purchase dates,
cash. Every market figure was read against 2026-09-23 and reconciles with
itself: the classes sum to the total, each percentage is its value over
the total, each P&L is its value less its cost. **33 of 67 matched, where
the fourth block predicted 52**: 7 of 19 in the spine, 7 of 15
variations, 7 of 7 clarifications, 6 of 9 refusals, 6 of 17 sequence
turns. Twenty-three lines the fourth block called matched missed, each a
failed hypothesis whatever the answer reads like; four it called missed
matched, 3.1 and V-3.1a to V-3.1c, by Part 18's correction of 24
September and with the behaviour it predicted. No miss is on the guess,
cannot be done or a reading gap: every name was read (V-1.2a, V-4.1a,
V-4.2a, V-4.6a, V-2.1b's "Apple" named back), the German was answered in
German, and every sequence's turn two read what it refers to.

The misses, by kind. **The as-of dropped**, the largest: 1.4, 2.1, 2.3,
4.1, V-2.1a, V-4.1a, V-4.6a, S-5 turn 2, S-7 both turns, S-8 turn 1.
**A statement Part 18 pins left out**: no look-through (1.1, S-5 turn 1),
not an average of the holdings' volatilities (1.3, V-1.3b, V-1.3c, S-3
turn 2, S-8 turn 2), PHI-6.2 (4.5). **The whole-table entries answered
with a selection**: 2.1's ok and exempt rows, 2.2's statements, 4.3's
before column. **Five failures no loop had shown**: V-1.1a's German
figures refused by the tracing check; S-4 turn 2 answered from turn 1's
figures after a policy lookup that printed none of them, and refused; 3.3 asked which
position instead of showing all nine; V-2.1b refused as an opinion where
V-2.1a, the same question with the ticker, ran the check; R-2 offered to
screen a company on no watchlist entry. Each is logged in `KNOWN_GAPS.md`
with its trigger; nothing was fixed.

| Entry | Reading | Against the fourth block |
| --- | --- | --- |
| 1.1 | missed: funds counted at fund level with no look-through, not stated | moved against |
| 1.2 | matched | as predicted |
| 1.3 | missed: the 251 returns from 252 closes, the weights' date and "not an average of the holdings' volatilities" not stated; the method is "daily returns of the invested assets" | moved against |
| 1.4 | missed: AAPL and MSFT with their values, but as shares of total and not of invested value; Technology's share of invested value, the unsectored 47% and the as-of not stated | moved against |
| 2.1 | missed: IPS-4.1, 4.2 and 4.3 cited on the breaches only; the ok rows as "everything else", the four funds not named as exempt, the no-sector line not reported, no as-of | moved against |
| 2.2 | missed: IPS-3.2 to 3.5 inside with no figure; IPS-1.1, 1.2, 2.1, 2.2, 5.1, 5.3, 6.1 and 6.2 not named as not computed; 2.3's conditions carried | as predicted, on more |
| 2.3 | missed: the overlaps not stated; no as-of | as predicted, on more |
| 3.1 | matched: asks share or fund, no clause, no figure (Part 18 as corrected) | moved the other way, the behaviour as predicted |
| 3.2 | matched: IPS-1.3 cited, the forecast named as refused, the lookup alone ran; one sentence lists what the policy answers | as predicted |
| 3.3 | missed: asked which position instead of showing all nine; no figure | moved against |
| 3.4 | matched | as predicted |
| 3.5 turn 1 | matched | as predicted |
| 3.5 turn 2 | matched | as predicted |
| 4.1 | missed: the check's as-of not stated; the range and a last close printed beside the stop, the close with no date | moved against |
| 4.2 | missed: the fiscal year's dates and the accession, W-1 as the growth pair's source, PHI-4.3 by id and the close's source not stated | as predicted, on more |
| 4.3 | missed: no before column, no after shares, IPS-3.2 to 3.5 and the statements not named, the thesis not word for word, neither W-1.1 nor W-1.2 cited | as predicted, on more |
| 4.4 | missed: the thesis not word for word, the readings' claims without their quotes and with digits in their sentences, the filed date, PHI-6.1 and PHI-6.2 not cited | as predicted, on more |
| 4.5 | missed: PHI-6.2 not cited by id | moved against |
| 4.6 | matched: "doesn't clear" worded beside the exclusion | as predicted |
| V-1.1a | missed: the answer, written in German number format, refused by the tracing check; nothing shown | moved against |
| V-1.2a | matched: the name read by the layer | as predicted |
| V-1.3a | matched; the method note of 1.3 stands | as predicted |
| V-1.3b | missed: "not an average of the holdings' volatilities" not stated | moved against |
| V-1.3c | missed: "not an average of the holdings' volatilities" not stated | moved against |
| V-2.1a | missed: no as-of, the position's value not stated | moved against |
| V-2.1b | missed: "Apple" read, the question refused as an opinion under IPS-1.3 through the lookup, no compliance check run, one offered | moved against |
| V-3.1a | matched: asks share or fund (Part 18 as corrected) | moved the other way, the behaviour as predicted |
| V-3.1b | matched: the model asks share or fund, no tool called | moved the other way, the behaviour as predicted |
| V-3.1c | matched: asks share or fund (3.1c as corrected) | moved the other way, the behaviour as predicted |
| V-3.4a | matched | as predicted |
| V-3.4b | matched: answered in German, no clause | as predicted |
| V-4.1a | missed, as 4.1: the name read, the as-of not stated | moved against |
| V-4.2a | missed, as 4.2 | as predicted |
| V-4.6a | missed: the pull date not stated | moved against |
| C-1 | matched | as predicted |
| C-2 | matched: the screen's raise names ZZZZFAKE, no holding guessed, no figure | as predicted |
| C-3 | matched | as predicted |
| C-4 | matched | as predicted |
| C-5 | matched | as predicted |
| C-6 | matched | as predicted |
| C-7 | matched | as predicted |
| R-1 | matched | as predicted |
| R-2 | missed: offers to run AAPL through the philosophy screen and names the position tool, a company on no entry | moved against |
| R-3 | matched: offers a screen if a company is named, names none | as predicted |
| R-4 | matched | as predicted |
| R-5 | matched: nothing executed, `watchlist.toml` unchanged | as predicted |
| R-6 | matched: the lookup alone ran | as predicted |
| R-7 | missed: the missing entry named and nothing fetched, but shaped as the input model's error, where Part 18 pins a refusal and not an error | moved against |
| R-8 | matched: W-2 and the missing pair named; the close printed with its date and source | as predicted |
| R-9 | missed: the raise is the whole answer, as predicted; Adobe's Item 1 read again and refused, no row | as predicted |
| S-1 turn 1 | matched | as predicted |
| S-1 turn 2 | matched | as predicted |
| S-1 turn 3 | matched | as predicted |
| S-2 turn 1 | matched | as predicted |
| S-2 turn 2 | matched | as predicted |
| S-3 turn 1 | matched | as predicted |
| S-3 turn 2 | missed, as 1.3: "not an average" not stated; resolved by the record | moved against |
| S-4 turn 1 | missed, as 2.2 | as predicted |
| S-4 turn 2 | missed: "that" read as the breaches, but answered from turn 1's figures after a policy lookup that printed none of them, and refused by the tracing check; nothing shown | as predicted, on another reason |
| S-5 turn 1 | missed, as 1.1 | moved against |
| S-5 turn 2 | missed: "that" read as section 3; IPS-3.2 to 3.5 inside with figures but not cited by clause, no limits, no as-of | moved against |
| S-6 turn 1 | missed, as 4.2 | as predicted |
| S-6 turn 2 | missed, as 4.3: "it" read as GOOGL | as predicted |
| S-7 turn 1 | missed, as V-4.6a: the pull date not stated | moved against |
| S-7 turn 2 | missed, as 4.1: the frame carried, the as-of not stated | moved against |
| S-8 turn 1 | missed, as V-2.1a: no as-of; IPS-4.3 reported as the sector's; "the larger, 6.59 pp, governs" nets the two clauses | moved against |
| S-8 turn 2 | missed, as 1.3: nothing of AAPL carried, the basis not stated | moved against |

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