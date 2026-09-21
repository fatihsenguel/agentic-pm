# AGENTIC_FINANCE — Session Handoff

**Session date:** begun 20 September 2026 at 15:56 UTC (thirtieth session), ended on the 21st. Regenerated at its end.
**Branch:** `judgement`, cut from `baseline-v1` at **1f75b72** on the owner's word, the branch not existing before. **`baseline-v1` is the trunk** and stood at 1f75b72 at session start, level with `origin/baseline-v1` — the brief warned the tracking ref might read 641b492 after a push by URL and it did not. The previous session's branch `gate` is merged and its commits are on the trunk; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count 1f75b72..HEAD` — **13**, this file making 14. The owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1943 passed, 6 xfailed**, up from 1761 by 182. **Golden set: twenty lines, two runs, zero diff both times**, the second after everything had landed. **Runner 16/18, twice** — at session start 4.3 blocked at the research node's refusal, at session end **blocked at the policy**, the same count and a different reason. **The CLI twice**: the allocation question, which fetched nothing, and **"Should I buy GOOGL?", the first live position answer**. **Case 4.3's half is built end to end**: Part 15 G and D61, the view and its own request, the loader's entry condition, `entry.py`, `outcome.py` over all sixteen rows of Part 17 H, the research node's position branch, the gate node composing the outcome, and the rendering with `check_4_3` run over it. **`check_4_3` passes on the live answer, every assertion of it; the probe blocks the case on the screen's stop.** **Decision 74 taken** with a word. **Order 4's work is done. What is left is the full test across both halves, which is its own session, before anything of Order 5.**

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Sections whose claims were checked again this session and
still hold are kept word for word; the rest is rewritten.

**Misses of my own this session, caught before landing.** **I wrote
decision 68's gate rule twice**: `outcome.py` derived "every finding ok or
exempt" from the block's findings when `Gate.permits` already computes it,
publishes it and is held by `test_gate.py` — `gate.py`'s own docstring
says "the outcome is composed elsewhere", which was telling me to read it.
**The outcome never reached the formatter**: I read the research block from
`sub_results`, the node's own return, while the gate writes
`shared_data["research"]`, so the grounds printed empty whatever the gate
found. **IPS-5.3 printed as a finding and as not computed in one answer**,
it being a statement clause that D59 gives a finding. **`compose` took two
published blocks and two dataclasses**, a shape no caller has. **A
`findings` type guard let a string through** — a string is a `Sequence`, so
iterating one gave characters, matched no finding, and returned `met =
None`, "not established", for an argument of the wrong type. **My
wrong-version driver corrupted a patch** and printed "1 error" where every
other line printed "N failed". **Five wrong versions changed nothing and
were rewritten rather than counted**: a prompt check that passed on a word
it found elsewhere; a test parametrized over the constant it was checking,
where narrowing the constant deleted the case instead of failing it; a
whitespace mutation the message builder strips; an unreachable comment; and
the driver bug. **And my cost prediction for two paid loops was half
right**, because I carried a figure measured over one section into a run
over three.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4's work is built**: the bridge, the SIC code, the philosophy check node, the metric keys, the valuation range, prediction scoring, the research agent, the reading tool, the gate, and, this session, **case 4.3's half — the view, the entry condition, the outcome and the rendering**. What is left of Order 4 is the full test. Invariant 8 was revised at 5b4be76, dated 20 September: security selection is in scope through Level 4's checks and through nothing else. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. Level 4: 4.2, 4.4, 4.5 and 4.6 pass; 4.1 and 4.3 blocked. 16/18. **Eleven dated status notes under Level 4, the eleventh this session's**: 4.3 blocked at a third place, with nothing left to build for it and `check_4_3` passing on the answer. |
| `tests/golden/expected_values.md` | Hand-computed reference, Parts 1 to 17. **New this session: Part 15 G**, the model's view of a thesis, with D61 and ten accept/refuse rows, written before the code; and **a dated note on Part 17 I** saying the entry condition reads *not established* while the screen stops. Never update it to match code output. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Eighteen cases, unchanged this session — nothing in it was edited, and that is the point: `check_4_3` was written before the capability and the capability was built to it. **It discards every answer** through `contextlib.redirect_stdout` (lines 2501 and 2515), so a live model output cannot be read from a runner run (KNOWN_GAPS). |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 159 lines start `**Trigger:**`, counted by `grep -c '^\*\*Trigger:\*\*'`. New this session: six entries and one addendum. **The next session reads "Case 4.3 answers: D61, the view's own request, and what the first live run showed" first.** |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, **not opened this session**. Saved in Excel at b07bc33 by the owner at the end of the twenty-ninth session, checked then through openpyxl with zero cell differences. Parts 9 C, 11, 14, 15, 16 and 17 have no sheet. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. Unchanged. |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027, none scored. **Unchanged this session**, and read further than before: the entry condition it has always stated is now loaded and checked. No score is written into it by the system, ever. |
| `docs/PM-Assistant — Roadmap.md` | Stale; DIRECTION.md's Order supersedes it. |
| `docs/workflow.md` | Stale, and a pasted conversational reply with emoji in its headers (KNOWN_GAPS). |

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`.
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half that is tools and done,
and a judgement half whose tools — the philosophy check, the valuation
range, prediction scoring, the reading tool, the research agent, the gate
and, since this session, **the model's view of a thesis and the outcome it
feeds** — are in the graph with their references. The router is
scaffolding until the tool layer is complete.
**No deadline. Correctness over speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** A filing's document is text
  in `filed_documents` returned to no agent; what leaves the reader is the
  record, at most twelve claims a section and at most 3,600 characters of
  quotation in them together. The gate reads the allocation block as
  published and the candidate's entry, and publishes findings and figures,
  never a holdings table. **The view's form:** it is sent the thesis and
  the claims and nothing else, and it returns three fields.
- **No number from a model.** A claim's sentence carries no digit and a
  figure appears only inside a quote held to the stored section; a
  proposed prediction's metric is one of the two the frame writes. The
  gate's numbers are one multiplication from the allocation. **The view
  carries no number and no prose at all**: the value, the claim ids and
  the uncertainty are the whole record, so the answer prints the claims it
  cites rather than a sentence from the model. **A number written in words
  is not caught.**
- **Policy lives in config, not code.** The thesis, the growth pair, the
  classification, the weight and **the entry condition** are the
  watchlist's, loaded as written; the IPS's words are the IPS's. **The
  loader checks presence and shape; the check that reads a word is where
  that word's vocabulary lives** — the loader takes any non-empty entry
  condition kind and `entry.py` stops on one it has no rule for, the shape
  D42 gave the prediction metric and decision 63 the classification.
- **One arithmetic path.** The gate is not a second checker: it builds the
  allocation the portfolio would have and hands it to `compliance.check`.
  **And the outcome reads the gate's own verdict rather than re-deriving
  it**: `Gate.permits` is decision 68's rule over the gate's findings, and
  `outcome.py` consumed a copy of it until it was caught.
- **Raise, do not repair.** The gate raises on a candidate already held,
  an asset class no band names, a weight outside (0, 1) and a view it
  cannot build. **A position question about a candidate stating no weight
  raises**, the size being the owner's to decide. **A view or an entry
  condition that cannot be read is recorded and not raised**, so the rest
  of the answer stands and the outcome reads that input as not permitting.
- **Compliance is a gate, not a tool.** `gate_node` is in neither
  `schemas.AGENTS` nor `graph.AGENT_NODES`: the router cannot plan it,
  cannot be asked for it and cannot route around it. It sits on the edge
  into the synthesizer, and `require_gate` refuses to print anything that
  implies a position without its block **for the same ticker and the same
  weight**.
- **The outcome is nobody's judgement.** `outcome.compose` takes the four
  inputs as published blocks and returns a boolean and the names of the
  inputs that did not permit; it words nothing. The gate node calls it,
  the formatter words it, and neither decides it. **Not established is not
  a yes**: an input that could not be read never grants an entry, and is
  named as not established rather than as a no.
- **References before code.** Part 15 G before `thesis_view.py`, the Part
  17 I note before `entry.py`, the sixteen rows of Part 17 H as a harness
  the same day the composition landed; every test seen failing without its
  module and against one wrong version per rule with bytecode off; **a
  wrong version that changes nothing is a finding, and five of them were.**
- **The score is mine, and so is a row.** The system proposes a
  prediction, prints it marked proposed and not entered, and writes
  neither file. Case 4.3 passes on a prediction **entered** in the ledger
  (decision 69), and the answer cites W-1.1 and W-1.2 by id.
- **A recommendation exists only with both checks attached.** Built: the
  answer carries the philosophy screen clause by clause and the IPS over
  the portfolio as it would be, each with its statements named as not
  computed.
- **The registry is the prompt.** No prompt change this session, so no
  hypothesis and no golden line moved.
- **A value nothing consumes is not stored.** The entry condition entered
  the schema the commit its loader read it; `entered` entered the block
  the commit the answer cited it.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
- **The reference before the code**, each time, in its own commit.
- **A paid loop says first what it will fetch and store, table by table**,
  read off the store and the clock, and says after what moved. Five paid
  loops this session, **every table prediction exact, to the new quota
  row's count**, and **the cost prediction wrong by half**, which is its
  own KNOWN_GAPS entry.
- **A check is exercised against wrong versions**, one per rule, and one
  that changes nothing is rewritten, not counted.
- **Say which loop can see a change.** Most of this session was pytest
  alone; two commits reached the graph and one changed the answer's text.
- **Grep the caller, not the registration**, and **grep the writer the
  reader reads** — the formatter read `sub_results` while the gate wrote
  `shared_data`, and nothing but a test caught it.
- **Read a live model output by hand.** The runner discards it, so that
  costs a CLI run of its own (KNOWN_GAPS).
- **CLAUDE.md is mine and untracked.** A session proposes wording; I apply it.
- No emoji in anything newly written. A count I predict is a count I add up.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect. My real portfolio's data in the repo: Order 6, last. No cached
holdings table; no fallback rate, currency or policy; no adjusted close; no
environment switch for which policy runs. **No invented figures as a runtime
source, and no price a stock will reach anywhere.** No widening of the
router's schema to make it a better classifier. No NOPAT at the company's
filed tax rate. No formatter sentence that states the system's status.
**No number, threshold or weight from a model; no row written into the
watchlist by the system; no outcome decided by the formatter or the model;
no gate that checks the concentration clauses alone; no second arithmetic
path beside the allocation the analysis agent publishes; no verdict on a
clause nobody has decided how to check.** **No score written into the
ledger by the system; no partial credit; no prediction scored before its
date.** **No nearest heading, no page furniture removed by a rule measured
on one filer, and no question in a reading's prompt.** **No long quote cut
in code to pass the cap, no third wording after two misses, and no `asks`
value nothing consumes.** **No prose from a model in an answer that
nothing holds; no third value beside the outcome's boolean; and no check
rewritten to fit the code it was written before.**

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q

python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/tmp/golden_err.txt
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py

python src/agents/cli.py --portfolio 3
```

**1943 passed, 6 xfailed, 35 warnings, about 6 seconds.** Run at session
start (1761) and after every commit. The 182 are `thesis_view` (31),
`view_model` (24), `entry` (22), `outcome` (46), the loader's entry
condition (16), the research node's position branch (16), the gate node's
composition (6) and the position rendering (21).

**Golden set: twenty lines, one pinned failure** ("Should I rebalance my
portfolio?", errors 1). **Two runs, both zero diff**: one at session start
and one at the end, on the owner's word, after everything had landed. No
prompt changed this session, so no line was expected to move and none did.
**Line 11, "Should I buy Nvidia?", is sighted on the final code**: it
exercises the refusal branch and its error count is unchanged at 2, now
for a different reason on the second error — the screen refuses a company
on no entry (decision 73) and the research node then finds no screening
block, where before this session the node refused the question itself.
The second run wrote exactly what was predicted: `api_call_logs` 2,461 to
**2,464**, a new `api_quotas` row for the 21st with a count of 3, and no
price row, no macro row, no reading and no EDGAR fetch.

**The runner twice: 16/18 both times, the same eighteen questions, and
4.3 blocked at two different places.** At session start it stopped at the
research node's refusal. At session end it routes, screens Alphabet, reads
three cached sections, proposes a prediction, gives a view, gates the
position at 6%, composes the outcome and renders the answer — and
`check_4_3` **passes on all of it**. The probe reports the block:
`the philosophy check stopped on PHI-2.1 … (decision 48)`.

**The CLI twice.** The allocation question: priced as of 2026-09-18, total
408,447.50 USD, Equity 69.61%, and it fetched nothing, the interval having
almost a day to run. Then **"Should I buy GOOGL?", the first live position
answer**, read by hand: the view came back `strained`, `stated`, on claim
7.12, that the company raised new debt financing in the year, against a
thesis whose own words are "with no debt to speak of". It wrote nothing to
any table.

**Level 4: 4 of 6 cases pass (4.2, 4.4, 4.5, 4.6); 4.1 and 4.3 blocked by
decision.** Read n/18 as a count of well-formed answers and never as the
system being good at research.

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. **The trunk stood at 1f75b72** at
session start and is level with `origin/baseline-v1`. `judgement` is this
session's branch, cut there on the owner's word. `gate`, the previous
session's, is merged and its commits are on the trunk. `thesis`, `reader`,
`research`, `score`, `publish`, `range`, `keys`, `node`, `filer`,
`bridge`, `consolidate`, `selection`, `compliance` and `vocabulary` are
merged and older. `wip/phase7-snapshot` holds rejected Compliance/IPS
code. `wip/rag-early` and tag `rag-early-parked` hold the RAG code.
`quant-inventory-parked` at 8d87455 holds the tree before the seventeenth
session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`2445c12e728c`**, 26 migrations, linear, all applied; no migration this
session. No reseed. **What this session wrote:**
- `daily_prices`: **7,009, unchanged**, the last close 2026-09-18. No loop
  fetched a price: the holdings' stamps are 2026-09-20 12:53 UTC and
  GOOGL's 12:56, so **the price interval runs out on 21 September at 12:53
  and 12:56** — a few hours after this session ended.
- `macro_data`: **209, unchanged**. The regime line asked for three
  indicators on each golden run and no trading day had closed either time
  — Friday the 18th was already stored and Monday's close was still hours
  away; the runner asks for none.
- `api_call_logs`: 2,458 to **2,464**. Three macro indicators on each of
  the two golden runs, and nothing else: no provider call in either runner
  run or either CLI run. `api_quotas`: the 20th **22**, the 21st **3**.
  **No Anthropic call is logged here at all** (KNOWN_GAPS).
- `document_readings`: **5 rows, unchanged.** Item 1 under `1b2d86a8ba32`,
  `ba9a7051eeca` and `a64f51fde1eb` (the one the node serves); Item 1A
  under `903e89b123b5`; Item 7 under `54b0dba223f4`. All three sections
  the reader reads are cached, so a run asks the model only for its
  proposal and, for a position question, its view.
- **No EDGAR fetch at all.** `filers` three rows, `filed_facts` 28,787,
  `ticker_ciks` 10,422, `filed_documents` one row, `filed_fetch_metadata`
  two. **The filings intervals run out on 22 September at 22:17 (Apple's
  document) and 23 September at 01:33 to 01:38 (Alphabet's document, and
  the three filers and the ticker file).**

Unchanged: `assets` ten rows, GOOGL the tenth and not held, its asset
class, sector and instrument type still blank — the watchlist entry states
them (decision 63); `financial_statements` 65 and `shares_history` 947,
neither a source.

**There is no holdings table.** Portfolio 3, "Benchmark Portfolio", is the
only portfolio: nine ledger rows, cost basis 284,500 plus 15,500 cash, USD,
policy `ips.toml`. GOOGL is not held. Adobe has no assets row and no facts.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row; the gate, over the portfolio as it would be |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py`, `test_screening.py` | the screening node, by `nodes.PHILOSOPHY_PATH` (decision 30) |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py`, `test_watchlist_loader.py`, `test_watchlist_predictions_loader.py` | the screening node, the candidates and their growth pairs; the ledger node, the prediction rows; the research node, the candidate, its thesis, **its entry condition and its entered predictions**; the gate node, the classification and the weight |

### Case 4.3, as it stands

**Built this session, and answered end to end.**

| Piece | Where | Held by |
|---|---|---|
| The reference | `expected_values.md` Part 15 G, D61; Part 17 I's note | themselves, hand-written before the code |
| The view | `portfolio_tool/thesis_view.py` | `tests/test_thesis_view.py`, 31, to Part 15 G's ten rows |
| Its request | `agents/view_model.py`, `nodes.view_model` | `tests/test_view_model.py`, 24 |
| The entry condition | `portfolio_tool/entry.py` | `tests/test_entry.py`, 22 |
| Its config | `watchlist.Candidate.entry_condition` | `tests/test_watchlist_loader.py` |
| The outcome | `portfolio_tool/outcome.py` | `tests/test_outcome.py`, 46, **all sixteen rows of Part 17 H** |
| The node's half | `agents/nodes.py`, `_position` | `tests/test_research_node.py` |
| The composition | `agents/nodes.py`, `gate_node` | `tests/test_gate_node.py` |
| The rendering | `agents/nodes.py`, `_format_position_response`, `_position_grounds`, `_not_computed`, `_readings_and_proposals` | `tests/test_position_formatter.py`, 21, with `check_4_3` over it |

**What it says on this portfolio.** Equity is 69.61% against IPS-3.1's 65%
before any purchase, so the gate fails at every weight and IPS-5.3 with
it; the screen stops at PHI-2.1 on Alphabet's FY2021 (decision 48); and
the entry condition is therefore **not established**, the screen having
reported a finding on no clause. The outcome supports no entry and names
those three, plus the view when it does not stand. `check_4_3` passes;
the probe blocks. **That is Part 17 I's row 15 arriving at the runner, and
it is the right answer.**

### The research agent, the screen and the ledger, as they stand

`screening_agent_node`, intent `research`, plan `[ScreeningAgent]` alone
when `asks` is unset; it refuses a ticker on no watchlist entry when
`asks` is "position", before its first EDGAR call (decision 73). On
Alphabet the screen stops at PHI-2.1 for FY2021 (decision 48, D36); the
range publishes regardless, 129.39 to 205.62 on FY2025.
**`research_agent_node` answers `asks` "thesis" and "position"** and
refuses anything else. `ledger_agent_node`, intent `ledger`, unchanged.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  for the router. **`ANTHROPIC_SONNET` is `claude-sonnet-5`**, used by the
  reader, the proposer and **the view**, and **it refuses a temperature**;
  none of the three sends one. The router's stronger-model switch sends 0.0
  and would fail (KNOWN_GAPS).
- **The `anthropic` SDK is 1.2.0**: `messages.create` takes `output_config`
  for structured output, and a schema's `anyOf` of two object shapes is
  held by it.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing. **Nothing was fetched from EDGAR this session.**
- **What a model call costs, and why every figure here is an estimate.**
  `claude-sonnet-5` is $2 and $10 a million. The only recorded measurement
  is 19 September's: 2,424 tokens in, 214 out, $0.0070, over **Item 1's
  claims alone**. With all three sections cached the user message is
  13,945 characters against 4,779, so **a proposal is nearer $0.0136 and a
  view nearer $0.0116**, scaled at 2.79 characters a token from that one
  measurement. **Nothing records a model call's tokens** — `api_call_logs`
  is provider calls only and `observability/token_counter.py` counts words
  times 1.3 for `smart_router.py` alone (KNOWN_GAPS). **Spent this
  session: about $0.10** — two golden runs, two runner runs and one CLI
  position answer, five paid loops — plus Haiku router calls. Treat it as
  an estimate.
- **The price provider** is `nodes.price_provider()`; **the models** are
  `nodes.reading_model()`, `nodes.proposal_model()` and
  `nodes.view_model()`; the EDGAR provider is `nodes.edgar_provider()`.
- **The allocation question fetches prices** when the one-day interval has
  run out. The CLI is a paid loop in that case, and is said first.
- `config.toml` carries five fetch intervals. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; `config.toml` is read relative to the project
  root, so scripts run from the root.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router.
- **Import order, for any commit sequence.** The last sessions' order
  stands. **New: `portfolio_tool/thesis_view.py` imports `proposer` and
  `reading` and nothing of `agents`; `portfolio_tool/entry.py` imports
  `screening` and `watchlist`; `portfolio_tool/outcome.py` imports
  `screening` alone, taking its four inputs as published blocks;
  `agents/view_model.py` imports `anthropic` and `agents.config`;
  `agents/nodes.py` imports `entry`, `thesis_view` and `view_model` inside
  `_position` and `outcome.compose` inside the gate node.**
- **Tests import from other tests.** The last sessions' imports stand.
  **New: `test_thesis_view.py` imports `MESSAGE`, `READINGS`, `THESIS` and
  `_reading` from `test_proposer.py`; `test_view_model.py` imports
  `_Client` and `_response` from `test_proposal_model.py`;
  `test_position_formatter.py` imports the fixtures from
  `test_research_node.py`, `state_with` from `test_screening_node.py`, the
  allocation from `test_gate.py`, and `run_cases` off `tests/benchmark`.**
- **Tests delete rows from the suite's copy they did not write**:
  `test_screening_node.py` Alphabet's and JPMorgan's facts, filers and the
  ticker table, `test_filed_facts_fetch.py` Apple's facts. `test_gate.py`,
  `test_gate_node.py`, `test_outcome.py`, `test_entry.py` and
  `test_thesis_view.py` touch no table.
- **A scratch copy of the tree runs the suite against a changed file
  without touching the repository.** From the working tree,
  `cp -R src tests docs alembic config.toml ips.toml philosophy.toml
  watchlist.toml pyproject.toml <copy>/`; copy `data/portfolio.db` into
  `<copy>/data/`, then from inside it
  `DATABASE_URL=sqlite:///<copy>/data/portfolio.db USE_MOCK_QUOTA=True PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 <repo>/.venv/bin/python -m pytest -q -p no:cacheprovider --color=no <tests>`
  after deleting its `__pycache__`. **Pass `--color=no`** or the failing
  tests' names come back as colour codes. **Seventy-eight wrong versions
  ran this way this session — 20, 11, 6, 9, 13, 11 and 8 over the seven
  modules — driven by a script that asserts each anchor appears exactly
  once**, because one that did not apply printed a green run that meant
  nothing.
- **`nodes.utc_today()`** is the ledger node's clock; the screening node
  reads the clock inline, so **a research answer's as-of is the day of the
  run**, and the research node reads the screen's as-of.
- **zsh does not split an unquoted variable into words**, and **has no
  `tac`**. **A `grep -c` that finds nothing exits 1 and stops a `&&`
  chain.** **BSD `sed`'s `0,/re/` first-occurrence form is a GNU extension
  and silently matches nothing on macOS.** **A backslash inside an
  f-string expression is a syntax error in 3.10.**
- **What is no longer in the tree** (do not look for it): `portfolio_tool/rag/`,
  `tools/data_tools.py`, `tools/macro_tools.py`, `tools/analytics_tools.py`,
  `portfolio_tool/analytics/`, `scripts/run_metrics_update.py`,
  `scripts/update_all_assets.py`, `agents/risk_manager_agent.py`,
  `optimization/risk_parity.py`, `tests/test_design_violations.py`,
  `tests/violation_detector.py`; and inside surviving files, VaR, CVaR,
  drawdown, Sharpe, Sortino, Calmar and `RiskMetricsCalculator` from
  `quant/risk_metrics.py`, shrinkage and exponential covariance, the frontier,
  min-vol, target-return and target-volatility optimisers,
  `DataAgent.get_risk_metrics_tool`, and the two `marketable_securities`
  fields of the figures block.

---

## 4. What the thirtieth session did

`git log --oneline 1f75b72..HEAD`, 13 commits and 14 with this file. **Case
4.3's half, end to end**, in the order the brief set: the reference before
the code each time, and each commit on its own word.

**The loops, first.** `judgement` cut from the trunk at 1f75b72. pytest
1761. The CLI on the allocation question, said first to fetch nothing, its
interval having almost a day to run — and it fetched nothing. Then, on a
word and one after the other, the golden set once (twenty lines, zero
diff) and the runner once (16/18), each predicted table by table and each
holding. **And at the end, on the owner's word, the golden set a second
time over the final code**: twenty lines, zero diff again, and line 11
sighted at errors 2.

**Under the word, in order.**
- **51cf7ce** **Part 15 G**, the model's view of a thesis, by hand before
  the code: D61, three fields and no prose, the three values and what each
  means, which of them needs a reason, ten accept/refuse rows, and the map
  onto Part 17 H's two columns. The call left open, as D49 left the
  proposer's until D58.
- **2078e22** `portfolio_tool/thesis_view.py` and its 31 tests. Two wrong
  versions changed nothing and taught the file something: a prompt check
  that passed on a word found elsewhere, and a test parametrized over the
  constant it was checking.
- **de8b9a3** `agents/view_model.py` and its 24 tests: a second request on
  the stronger model, not the proposal's.
- **e200df4** Part 17 I's dated note: the entry condition reads *not
  established* while the screen stops.
- **64fb2a7** the loader reads `[candidate.entry_condition]`; four TOML
  fixtures and one `Candidate` fixture gain it, and two tests that said it
  was read by nothing say where it is held now.
- **44ff12e** `portfolio_tool/entry.py` and its 22 tests. A guard of mine
  let a string through, since a string is a `Sequence`.
- **0e27798** `portfolio_tool/outcome.py` and its 45 tests, **all sixteen
  rows of Part 17 H**, closing the gap where `check_4_3` held one.
- **55e940b** the correction: read the gate's verdict, do not recompute it.
- **ab07f68** the research node answers a position question.
- **2e17d94** the gate node composes the outcome onto the research block
  (decision 74), and `compose` takes the four as published blocks.
- **0d99229** the rendering, with `check_4_3` run over it; three defects
  it caught are in §8.
- **01d3572** the record: six entries, one addendum, decision 74.
- **799e352** benchmark.md's status note.
- **this file**, regenerated.

**The runner, against the answer-text commit**, and the CLI on "Should I
buy GOOGL?" after it, both said first, both fetching nothing, together
about $0.064. The runner printed 16/18 with 4.3 blocked at the probe. The
CLI printed the answer, which is where the live view was read: **the
runner discards every answer, so reading one costs a run of its own**
(KNOWN_GAPS).

**Not done, on purpose.** The full test, which is its own session; a
golden line for a buy question about a company that *is* a candidate,
which wants sighting first; the loader's `author` and Part 15 F9; the
seven emoji headers; decisions 51, 52 and 54; the currency; the philosophy
topic lookup; the CIK confirmation; formulas for `operating_margin` and
`free_cash_flow`; any change to the reading, proposal or view prompts for
faithfulness.

---

## 5. Decisions taken, and decisions pending

**Taken this session**, with the owner's word, **numbered here and his to
renumber**:
- **74**: the **gate node** composes decision 68's outcome and writes it
  onto the research block. The outcome must sit on the research block,
  where `check_4_3` reads it and where the answer about the position is,
  and it needs the gate, which runs after the research agent on the edge
  into the synthesizer (decision 62) — so something after the gate writes
  into another node's block either way and the only choice is which node.
  Rejected: a third node between the gate and the synthesizer, one job
  each but a second node on an edge decision 62 calls one, and writing the
  research block all the same; changing `check_4_3` to read the outcome
  off the gate block, which moves a check written before the capability to
  fit the code.

**Pending — decide before writing code. Eleven by count, unchanged: none
closed, none opened.** CLAUDE.md's line reads "The list stands at 11 on
20 September: 10, 12, 13, 16, 17, 22, 45, 48, 51, 52 and 54" and matched on
both the count and the members at session start. The cap is 25.

10. A window return as a measure with a reference.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding. Absorbs 35.
22. Volatility over as-traded closes or a total-return series.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, 11 and 36.
48. Part 13 E's item 7, second half only: the price and a filer with more
    than one class. Items 3, 4, 6 and 7's first half decided.
51. The four live intents outside the benchmark roster: delete or keep.
    Trigger: the full test at the end of Order 4.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields: delete, its
    own sitting.

- **The full test at the end of Order 4** (owner's): **its trigger has
  fired.** Order 4's work is built and the project stops for a full test
  across both halves before anything of Order 5. That is the next session
  and is not this one. Decision 51's trigger fires with it.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12. Level 4: 4.2, 4.4, 4.5 and 4.6 PASS; 4.1 BLOCKED by
decision, the runner's reason naming D36; **4.3 BLOCKED at the policy**,
with nothing left to build for it. 16/18.

**`check_4_3` passes on 4.3's live answer, every assertion of it.** The
case is reported blocked by the probe, `blocked_on_recommendation`, which
names the screen's stop at PHI-2.1. On this portfolio equity is 69.61%
before any purchase against a 65% ceiling, so the gate fails at every
weight; the screen stops as 4.1's does; and the entry condition is not
established because a stopped screen reports a finding on no clause. **A
blocked case with the right reason is the right answer**, and Part 17 I
computed this row before any of it was built.

What the runner cannot see: **whether the view is a defensible read of the
claims it cites**, which only a hand reading finds and which the runner
discards; whether the gate's arithmetic is right, which is pytest's
against Part 17; whether the range's ends are right; any due prediction
until 2027; whether a quote supports its claim; and whether a proposal's
reasons bear on the metric it names — they are about margins now and
about operating margin rather than gross (KNOWN_GAPS).

---

## 7. Next steps, in order

**1. The full test across both halves** (§5, the owner's), before anything
of Order 5. Its trigger has fired: Order 4's work is built. Decision 51's
trigger — the four live intents outside the benchmark roster — fires with
it.

**Before it, one thing this session did not sight.** **No golden line
covers a buy question about a company that is a candidate** (KNOWN_GAPS) —
the runner's 4.3 covers it and the golden set does not, so a routing
change that broke only the candidate path would show up in one loop of
four. A line for it wants sighting first, and there is now something to
sight: the answer exists and the CLI prints it. Line 11's own error count
was the other unsighted prediction and is sighted: the golden set ran a
second time at session end and it held at 2.

### Later, with reasons

- **The trunk.** `git switch baseline-v1 && git merge --ff-only judgement`.
- **Decision 74's number** is mine to propose and the owner's to set; it
  appears in one KNOWN_GAPS entry and in §5 here.
- **A live model output can only be read through the CLI**, the runner
  discarding every answer (KNOWN_GAPS). Whether the runner should keep
  them is a decision about what a run leaves behind.
- **Nothing records a model call's tokens**, so every cost figure here is
  arithmetic on one measurement over one section (KNOWN_GAPS).
- **`check_4_3`'s weight_source assertion cannot fail** while the
  candidate's id is printed (KNOWN_GAPS).
- **`outcome.compose` is stricter than `check_4_3`** on a screen with no
  finding, named in both (KNOWN_GAPS).
- **An event entry condition stops** and no candidate states one
  (KNOWN_GAPS).
- **A buy question about a company on no entry reads as an error**, not as
  a refusal, and two agents compute a portfolio for it first (KNOWN_GAPS).
- **IPS-2.1 would pass an instrument the policy forbids**, being a
  statement clause (Part 17 G, KNOWN_GAPS).
- **IPS-5.3's second limb** is not computed; its trigger is the first
  portfolio state with no limit breached (decision 71).
- **Every paid loop still costs Sonnet**: a golden run proposes once, a
  runner run proposes twice and views once, a CLI position answer proposes
  and views once.
- **The next paid loop fetches the holdings' closes**: the stamps stand at
  2026-09-20 12:53 UTC and GOOGL's at 12:56, so the interval runs out on
  21 September at those times — the last golden run, at 08:53, was still
  four hours inside it. **The filings intervals run out on 22 September at
  22:17 and 23 September at 01:33 to 01:38.**
- **The loader's `author`**, with my sentence in WATCHLIST.md, before the
  first system prediction is entered; Part 15 F9 comes with it.
- **1 February 2027**: W-2.1 and W-2.2 fall due.
- The proposals' reasons and the readings' faithfulness: each a hypothesis,
  each on its own trigger (KNOWN_GAPS).
- The router's stronger-model switch and `ANTHROPIC_SONNET`'s temperature.
- The currency on the range, the close and the reported figure.
- The formatter headers carrying an emoji, seven in `nodes.py`. One commit,
  the runner run against it. `docs/workflow.md` in the console-glyph session.
- Three stale statements, mine to fix on my word: `watchlist.toml`'s
  header and `test_watchlist.py`'s docstring, "read by nothing yet"; Part
  11 D38's "D46".
- A philosophy topic lookup; the CIK confirmation; decisions 51, 52 and 54.
- `operating_margin` and `free_cash_flow` get formulas, and
  `return_on_invested_capital` its tax rate, when a prediction names one.

---

## 8. Rules learned the hard way

**Grep the writer the reader reads, and then read what the reader reads.**
The position formatter took the research block from `sub_results`, the
node's own return, while the gate node writes the outcome onto
`shared_data["research"]`. The answer printed its grounds list empty and
would have done so whatever the gate found. Nothing but a test over the
rendered answer caught it.

**A test parametrized over the constant it is checking cannot catch a
wrong constant.** `T-5` took its cases from `thesis_view.NEEDS_REASON`, so
a wrong version narrowing that tuple **deleted the case** and the suite
went from 29 tests to 28, green. Parametrize over literals and pin the
constant in one test of its own.

**A check that looks for a word anywhere passes a line that lost it** —
again, in a prompt this time. Removing `no_view`'s definition from the
view's prompt left the word in the reasons paragraph, so the test passed
on an incidental mention. Assert the definition line.

**A wrong version that changes nothing is a finding about something, and
not always about the test.** Five this session: two about tests, one about
a mutation the code strips (a whitespace change cannot reach a message
whose builder calls `strip()`), one an unreachable comment, and one a bug
in my own driver. **A driver that patches by string replacement asserts
each anchor appears exactly once**, or a green run means nothing.

**A statement clause can carry a finding.** IPS-5.3 states no number, so
the loader reads it as a statement, and decision 64's funding makes D59
give it a finding — so an answer that lists "the statements" as not
computed printed IPS-5.3 twice, once with its finding and once as
uncomputed. The not-computed list is the statements that carry no finding.

**A rule already implemented is not implemented again.** `Gate.permits` is
decision 68's rule over the gate's findings, published on the block and
held by `test_gate.py`; `outcome.py` derived it a second time until the
block was read properly. The runner deriving the same thing from outside
the pipeline is a cross-check; a second derivation inside it is a copy.

**A type guard written against `Sequence` lets a string through**, and a
string iterates into characters. `entry.read(condition, "PHI-4.1")`
matched no finding and returned "not established" — a wrong answer with a
plausible face, in the module whose whole point is that the phrase means
something.

**A figure measured before a prompt changed is not a figure about the call
being made.** "$0.007 a proposal" was measured over one section; three are
cached now and the message is 2.9 times longer. I carried it into a
prediction anyway and was wrong by half.

**A cost you cannot measure is a cost you will misstate.** Nothing in this
project records a model call's tokens.

**A scoreboard that discards its answers cannot be read.** The runner
produced the first live view and showed nobody a word of it.

**Take the shapes a caller actually has.** `compose` took two published
blocks and two dataclasses; the only caller holds four blocks.

Still true, from earlier sessions: **hand arithmetic is checked, and the
check is part of the work**; **a statement about the code goes stale four
commits after it was true**; **an import-time check cannot be shown
working on the table it guards**; **a guard that cannot fire is not a
guard**; **a tool's first-occurrence flag may not be the tool's**; **pass
`--color=no` to a captured pytest run**; **a routing test that sets the
wrong key passes for the wrong reason**; **look at a path before writing
to it**, and **load a config file after editing it**; **a refusal that is
right can still be shaped wrong**; **a check that looks for a field
anywhere passes a line that lost it**; **a test over the suite's copy owns
the rows it reads**; **a number is measured before it is written**; **a
brief's claim about an interval is checked against the clock**; **a quote
is judged with the lines around it**; **a count in a message is counted**;
**sight a new case before writing its golden line**; **the registry's
descriptions are the prompt**; **add up the pending list**; **the owner's
documents are written on a separate word**; **the golden loop's stderr
goes to a file**; **say which loop cannot see a change**; **a formatter
states what the data says and never what the system is**; **two paid loops
on one SQLite file run one after the other**; **an instruction with words
missing is read against the record**; **a wrong version checked in place
can run the previous one's bytecode**.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/tmp/golden_err.txt
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 4.3

python src/agents/cli.py --portfolio 3        # :q to quit
printf 'Should I buy GOOGL?\n:q\n' | python src/agents/cli.py --portfolio 3

git status --short
git log --oneline 1f75b72..HEAD
git rev-list --count 1f75b72..HEAD

# by hand, from the project root, after a migration or a seed change:
alembic upgrade head
python src/portfolio_tool/scripts/seed_portfolio.py --reset

# what the database says it is at (expected 2445c12e728c):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# the reading tool's two tables:
sqlite3 data/portfolio.db "select accn, length(text), source from filed_documents; select accn, section, model, substr(prompt_version,1,12) from document_readings;"

# the price and filings clocks, which decide what a paid loop fetches:
sqlite3 data/portfolio.db "select a.ticker, m.last_price_fetch_time from asset_fetch_metadata m join assets a on a.id=m.asset_id order by a.ticker;"
sqlite3 data/portfolio.db "select cik, pulled_at from filers; select * from filed_fetch_metadata;"

# a check run against an edited, deliberately wrong module:
find src tests -name __pycache__ -type d -prune -exec rm -rf {} +
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider --color=no tests/<file>.py

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only judgement
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~6s, no model calls | Do the components still work; does every reference Part reproduce, **Parts 15 G and 17 H among them**; does each node fetch in order and publish its block; does the gate refuse what it must; **does the outcome compose every row of the truth table, and does the rendering satisfy `check_4_3`** |
| CLI | ~3s and one Haiku call for most questions; **a thesis question about $0.014 and a position question about $0.025 on Sonnet**; **fetches prices past their interval** | What it is actually doing: the plan, the parameters, the reasoning line, the answer text. **The only loop that shows a live reading, proposal or view** |
| Golden set | ~2 min, **about $0.014 on Sonnet per run** and Haiku, **writes price rows past their interval, the macro rows, the call log and the quota counter on every run** | Did routing change anywhere (twenty lines, one pinned failure). Blind to parameters and answer text; stderr kept to a file |
| Benchmark runner | ~2 min, **about $0.039 on Sonnet** and Haiku | How many cases pass, n/18. Blind to whether a view or a proposal is any good, to whether a range's ends are right, to any due prediction until 2027, and **to every answer it renders, which it discards** |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once. **A live reading, proposal or view made on its own is not a
loop**: it is asked for, said first, and read by hand.
