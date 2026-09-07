> **Stale in places, committed 4 September 2026 to stop it being lost again.**
> Recovered from outside the repo; `HANDOFF.md` had listed it as required
> reading while it was untracked. Superseded points, do not follow them:
> Phase 1 item 1 (base-agent deduplication is no longer first — see HANDOFF
> §6); Phase 2 "Wire RiskManagerAgent" (it is a supervisor, not a risk agent —
> see KNOWN_GAPS); Phase 4 (the case runner arrives with the synthesizer, not
> last). Phase 0.1–0.3 are done. **Phase 1 items 2–5 are done as of
> 7 September; all four Level 1 cases pass on the runner.** Item 4's text
> below says the calculation does not exist; it does now, in
> `quant/risk_metrics.py`. Regenerate rather than patch further.

# PM-Assistant — Roadmap

**Written:** 2 September 2026
**Read alongside:** `docs/HANDOFF.md` (state of the code), `docs/benchmark.md` (definition of done), `tests/golden/KNOWN_GAPS.md` (open decisions and why obvious fixes are wrong).

**Ordering principle.** Nothing in this list is ordered by effort. It is ordered by what other things depend on it. The target architecture (Supervisor, Compliance, Risk, Quant, Data, later an Equity Analyst) is closer than it looks — the supervisor and data layers work, Quant is two agents that need merging, Risk exists but is unwired, and Compliance is sitting on `wip/phase7-snapshot`. What is missing is not agents. It is the capabilities underneath them.

---

## Phase 0 — Make it usable and measurable (today)

The system has never actually been used. Every interaction so far has been a one-off `python -c` command. That is a poor way to find behavioural problems, and behavioural problems are what Phase 1 is about to create.

Nothing here changes agent behaviour. It builds the ground truth and the tooling that Phase 1 will be judged against.

### 0.1 — Build a real portfolio

The current demo data cannot support the benchmark:

- Portfolio 1 (SPY/TLT/GLD) has January `average_price` values (SPY at 450), so any P&L figure is meaningless, and `sector` is `None` on every holding — benchmark case 1.4 cannot pass against it.
- Portfolio 2 (AAPL/MSFT) has sector data but only two positions, both Technology.

Build one portfolio with **6–10 positions spanning at least three asset classes and three sectors**, with real purchase dates and purchase prices.

Own holdings or realistic synthetic ones both work. Own data makes errors easier to spot because the numbers mean something; synthetic data avoids putting real positions in a public repo and in the golden set. Rounded, realistic proportions are indistinguishable to the code.

**Note:** `PortfolioManager.update_holding` accepts only `quantity` and `average_price`. There is no API path to set `asset_class` or `sector` — those live on `Asset`, reachable only via SQLAlchemy directly. Write a seed script rather than editing rows ad hoc, and treat closing that API gap as Phase 1 work.

### 0.2 — Hand-compute the expected answers

**Before** building any Level 1 capability, compute by hand (spreadsheet is fine):

- Allocation by asset class — both by market value and by cost basis
- Allocation by sector
- Per-position P&L since purchase, absolute and percentage
- Twelve-month portfolio volatility

This is not busywork. Two reasons:

**Anchoring.** If the tool is built first and checked afterwards, its output becomes the reference and the check degenerates into looking for reasons the number is plausible. An independently computed answer removes that.

**It is specification work in disguise.** Deciding by hand forces decisions the code must encode anyway: is allocation by market value or cost basis, does cash count as a position, is P&L total return or price return, is volatility computed on daily or weekly returns and annualised how. These are better decided in a spreadsheet than accidentally inside an agent.

Benchmark Level 1 says "passes when: correct sums." Until this exists, that criterion has nothing to compare against.

Commit the expected values as `tests/golden/expected_values.md`.

### 0.3 — Build a CLI

Roughly 50 lines against `run_agent_graph_sync`. Requirements:

- Holds a `portfolio_id` across queries so it need not be retyped
- Prints the trace (`observability/tracer.py` already produces it)
- Prints the routing decision and which agents ran, not just the final text
- Reads a query, prints, loops

This is the fast exploratory loop. The golden set answers "did anything change"; the CLI answers "what is it actually doing." Both are needed and neither substitutes for the other.

Do **not** rebuild the deleted `multi_agent_cli.py` — it instantiated agents directly via `create_*_agent` factories, bypassing the graph. Write it against the graph.

### 0.4 — Rewrite the README

The current one is a January artifact and is wrong in ways that predate the redesign: it describes RiskManagerAgent as an active supervisor (it is not wired at all), references `demos/` scripts that no longer exist, specifies `gpt-4-turbo`, and links `docs/ARCHITECTURE.md` and `docs/ROADMAP_PHASE_6.md`, both deleted.

Describe the intended architecture and state honestly what works today. The "Design Principles" section is worth keeping almost verbatim — the Hot Potato description in it is the clearest statement of that principle anywhere in the project, and better than the one currently in the handoff.

---

## Phase 1 — Level 1 capabilities

The four benchmark Level 1 queries currently route correctly to DataAgent, which fetches prices and stops. Nothing aggregates, compares against `average_price`, surfaces volatility, or reads holdings as positions rather than as a ticker list.

Everything above this depends on it. Benchmark Level 2 asks about concentration risk, which is allocation. Level 3's data-freshness case needs an output contract, which does not exist until something produces a real answer.

**Order within the phase:**

1. **Base-agent deduplication first.** `agent_name=self.name` appears in five agent files, each builds `PortfolioResult` by hand, `smart_router` constructs its own LLM instead of using the factory. Bug 3 from the recovery session was caused directly by this. Scope it to what the benchmark needs — two new agents (Risk, Compliance), not four — so this is a small change, not a rewrite.
2. **Allocation by asset class and sector** (benchmark 1.1, 1.4). Requires an agent that reads holdings as positions. Also close the `update_holding` gap from 0.1.
3. **Position P&L since purchase** (benchmark 1.2). Current price against `average_price`. Decide total vs price return, per 0.2.
4. **Portfolio volatility** (benchmark 1.3). **The calculation does not exist.** An earlier version of this line said it did and that only reporting was missing; `grep -rn "def portfolio_volatility" src/` returns nothing. What `src/portfolio_tool/quant/risk_metrics.py` holds is return-series volatility per ticker, which is a different quantity — `shared_data["volatilities"]` carries those floats. Per D7, `portfolio_volatility(weights, cov_matrix)` has to be written. Its check is a pytest fixture over the 252 closes committed from `expected_values.xlsx`, asserting 10.2936%, not a live comparison — the reference window is unreachable from a live run.
5. **Data-age reporting** (benchmark 3.3). Cross-cutting. Build it into the output contract here rather than retrofitting — `DailyPrice` rows carry dates, so the information exists and is simply never surfaced. This is the single most transferable point for the interview.

Each capability: golden set → build → golden set → decide whether the diff is an improvement → update `expected.txt` deliberately → commit.

---

## Phase 2 — Consolidate the agent roster

Mechanical once Phase 1 has established the patterns.

- **Wire RiskManagerAgent.** The file exists and imports; it has no node in `graph.py`, no routing-map entry, and no mention in `router_prompts.py`. The router already classifies `intent: risk_analysis` correctly and then has nowhere to send it.
- **Merge `optimization_agent` and `rebalance_agent` into a Quant agent.** `rebalance_tools.py` is pure deterministic math with a thin wrapper — the cleanest module in the project and a good template.
- **Decide the supervisor's shape.** The target architecture names a Supervisor. What exists is a router that plans upfront and a graph that executes the plan. That is more deterministic than a step-by-step supervisor and suits the stated principles better. Decide deliberately rather than drifting into one or the other.

---

## Phase 3 — Compliance and the IPS

Pull `ips_manager.py`, `esg_screener.py`, `compliance_agent.py` forward from `wip/phase7-snapshot`, one file at a time. Expect the same rot found during recovery: stale imports and renamed config fields.

Unlocks benchmark Level 2 in full, plus cases 3.1 (refusal with clause citation) and 3.4 (clause does not exist). Also resolves where rebalancing targets come from — see `KNOWN_GAPS.md`; do **not** solve it by inserting the optimizer into the rebalance chain.

**Note the architecture decision recorded in `benchmark.md` Part 1:** a self-authored IPS is structured data, and deterministic clause citation is a stronger claim than retrieval. Case 3.4 is trivially correct with structured rules and genuinely hard with RAG, which returns a nearest neighbour precisely when the right answer is "nothing."

---

## Phase 4 — Evaluation set

20–30 questions with expected answer and expected source per question. Produces the figure quoted in the CV.

Last not because it matters least, but because it is the only item that cannot be built before the things it measures. Phase 0.2's hand-computed values are the seed for it.

---

## Later — explicitly not now

- **Conversation memory.** Needed for exactly one benchmark case (3.5, clarification loop). The plumbing exists — `AgentState.messages` and `build_router_prompt(conversation_history=...)` are simply never populated. Small when it comes.
- **Equity Analyst agent.** The right long-term target and the wrong next step: it needs the data layer, the IPS, and retrieval over filings, all downstream of Phases 1–3.
- **RAG over filings and transcripts.** This is where retrieval genuinely belongs — external, unstructured documents. Separate from the IPS question. The `rag/` decision from the recovery session (Fed minutes) is a smaller, separate question; run the scraper once to see whether it still works before deciding anything.
- **Frontend, multi-user, order execution.** Out of scope per `benchmark.md` Part 2, and deliberately so.

---

## Working rhythm

Four loops, different speeds, run as separate commands and never chained with `&&`. Each has a blind spot and they do not overlap.

| Loop | Cost | Answers |
| --- | --- | --- |
| `pytest` | seconds | Do the components still work |
| CLI | seconds | What is it actually doing |
| Golden set | ~40s, a few cents | Did routing behaviour change anywhere |
| `python tests/benchmark/run_cases.py` | ~1min, cents | What actually works against benchmark.md |

The runner was built after this table was first written and is the authoritative one: **run it before believing anything about what works.** The golden set prints five routing fields and no answer content, so it is blind to every figure; `pytest` collects nothing that exercises the synthesizer. On 7 September the golden set caught a cache-key regression `pytest` passed straight through, and a separate change passed three of the four loops while being arithmetically inert.

`golden set -> change -> golden set -> decide whether the diff is an improvement -> then update expected.txt`.

**Rules carried over from the recovery session:**

1. `grep -rn "Name" src/ tests/` before deleting any symbol or module — including lazy imports inside function bodies.
2. Never infer a module's dependencies or purpose from its name.
3. One change per commit.
4. Watch VS Code's unresolved-import warnings after deletions. Pylance caught what both the test suite and the golden set missed.