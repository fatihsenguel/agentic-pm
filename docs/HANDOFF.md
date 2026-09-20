# AGENTIC_FINANCE — Session Handoff

**Session date:** 19 to 20 September 2026 (twenty-eighth session), begun 19 September at 16:25 UTC. Regenerated at its end.
**Branch:** `cap`, cut from `baseline-v1` at 3ce7dab on the owner's yes, the branch the brief named not existing. **`baseline-v1` is the trunk** and stood at 3ce7dab when the session began; `thesis` is merged into it. Each session branch is merged into the trunk with `--ff-only` when the loops are green; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count 3ce7dab..HEAD` — 7 with this file: the reference, the code, the record, benchmark.md, this file regenerated, the record again after one live request, and this file corrected for what that request changed. **Not merged and not pushed**: the owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1650 passed, 6 xfailed**, up from 1646 by 4. **Golden set: twenty lines, one run, zero diff.** **Runner 16/18, one run**: 4.1 BLOCKED at PHI-2.1 naming D36, 4.3 BLOCKED at out_of_scope, 4.4 PASS. **The CLI once**, the allocation question, which fetched nothing: the price interval had not run out, against the brief's reading of it. **Decision 70 is taken and built**: the record caps a reading's quoted text at 3,600 characters a section and no longer caps a single quote, the reference first. **Decisions 63, 64, 65, 68 and 69 are taken and nothing of them is built**; the gate's Part comes next. **All three sections are read for the first time**: Item 1A was stored by one of the two paid loops, and Item 7 was accepted on one request made after the cap changed, the 330-character sentence that had been refused twice now quoted whole. Both were read by hand. **Order 4 is not done. Left: the gate and 4.3, then the full test before anything of Order 5.**

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Sections whose claims were checked again this session and
still hold are kept word for word; the rest is rewritten. Misses of my own
this session, caught before or after landing: the brief said the price
interval had run out early on 20 September and it had not, the clock
reading 19 September at 16:25 UTC, so the CLI fetched nothing and was said
so before it ran; the brief's pending list of seventeen and CLAUDE.md's
line of seventeen with sixteen numbers disagree, and the handoff's own
quotation of that line, "16 on 18 September", was already stale; the first
run of the wrong versions printed the colour codes instead of the failing
tests' names and was rerun to name them; which of the two paid loops stored
the Item 1A reading cannot be said, since nothing records it, and the
entry says so rather than guessing; and the script that kept the Item 7
answer kept the claims and not the token counts, so that request's cost
is an estimate from an earlier measurement and not a measurement.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the bridge, the SIC code, the philosophy check node, the metric keys, the valuation range, prediction scoring, the research agent's shape, reference, checks and pure modules, the reading tool, the research agent in the graph for a thesis question, and, this session, **decision 70 and the five the gate waits on**. Left in Order 4: the gate and 4.3, then the full test. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. Level 4: 4.2, 4.4, 4.5 and 4.6 pass, 4.1 blocked by decision, 4.3 blocked on the gate that is not built (nine dated status notes under Level 4, the ninth this session's). n/18. Part 2 and the 3.2 row are untouched: their rewrite is at the commit that makes 4.3 answerable. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Eighteen cases. This session `_readings_invariants` changed with decision 70: `QUOTED_CAP` is 3,600 for a reading's quotes together and no single quote is capped. `check_4_4` passed on the live answer; its docstring and KNOWN_GAPS say what it cannot see, and a field it finds on another line is one of them. `check_4_3` and its probe hold `shared_data["gate"]` for the commit that makes 4.3 answerable; its prediction requirement is rewritten there, decision 69. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 147 lines start `**Trigger:**`, counted by `grep -c '^\*\*Trigger:\*\*'`. New this session: four entries, and dated lines on five whose triggers fired, decisions 70, 63, 64, 65, 68 and 69 written into two of them. **The next session reads "The shape of the research agent: decisions 59 to 69" first**, for the five taken this session, and "What the gate needs that the candidate's row lacks" beside it. |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, Parts 1 to 16. **Changed this session: Part 15 D47 and section A**, dated, decision 70: the cap is on a reading's quoted text, 3,600 characters a section, and a quote has no cap of its own. Never update it to match code output. |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, saved in Excel at c75b73b. Untouched this session; Parts 9 C, 11, 14, 15 and 16 have no sheet. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. Unchanged. PHI-6.1 now has a reader: every candidate's thesis is loaded and a candidate without one is refused. |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027, none scored. Unchanged; no prediction of the system's is entered. The prediction rows and, since the twenty-seventh session, the theses are read by `portfolio_tool/watchlist.py`. No score is written into it by the system, ever. |
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
and a judgement half whose tools, the philosophy check, the valuation
range, prediction scoring and, since the twenty-seventh session, the research agent for
a thesis, are in the graph with their references, and whose gate for a
position is not. The router is scaffolding until the tool layer is
complete. **No deadline. Correctness over speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** The last session's form: the
  research node reads the figures the screen stored back from the
  database and publishes none; the screening block still carries dates
  and findings only. The proposal model sees the thesis and the claims
  with their quotes, never the section's text and never the question. The
  last sessions' forms stand: a filing's document is text in
  `filed_documents` returned to no agent; what leaves the reader is the
  record, at most twelve claims a section and, since decision 70, at most
  3,600 characters of quotation in them together.
- **No number from a model.** A claim's sentence carries no digit and a
  figure appears only inside a quote held to the stored section; a
  proposed prediction's metric is one of the two the frame writes, its
  bound one of two words, and its threshold, period, dates, id and
  sentence are the pipeline's (D58). **A number written in words is not
  caught**, and the live readings of Item 1 carried "two" three times.
- **Policy lives in config, not code.** The thesis is the watchlist's,
  loaded as written; the metrics a model is offered are the frame's own
  list, `proposals.WRITTEN`, read by the schema; the sections read are
  named once, `reading.SECTIONS`.
- **Two policies, two questions; three now; and one intent with two
  questions.** A question naming one company is research; a question
  about the predictions names none and is the ledger (decision 58); a
  research question that names a thesis reads the filing after the screen
  (decision 66), `asks` set by extraction and never by the model.
- **Raise, do not repair.** The last session's form: a thesis or readings
  missing refuse before any request; a model answer that is not one
  prediction of the schema's shapes is refused; a metric not offered
  refuses; a section refused is printed as not read with its reason and
  is never retried within a run; a proposal refused is `proposal_stopped`
  beside an empty list; the screen's stop does not stop the research,
  which asks for no verdict. The last sessions' forms stand.
- **References before code.** Part 15 F before the proposer, and its
  refusals before the request dated into it before the code landed; every
  test seen failing without its module and against one wrong version per
  rule with bytecode off; every live reading and proposal read by hand
  before it is believed.
- **The score is mine, and so is a row.** The system proposes a
  prediction, prints the row and the sentence marked proposed and not
  entered, and writes neither file. WATCHLIST.md and watchlist.toml are
  written by hand.
- **A recommendation exists only with both checks attached.** The model's
  judgement is a view of the thesis from a closed set and never "buy";
  the outcome is computed in the node from the screen, my entry
  condition, the gate and that view; neither the formatter nor the model
  decides it. Not built: 4.3.
- **The count is the ledger's.** The scorer counts once; the formatter
  prints; the runner's check counts the file itself.
- **The registry is the prompt.** A sentence describing a capability that
  now exists is allowed where a rule tuned to a case is not, and it is
  still a hypothesis: prediction in the commit, two runs, stop at the
  second miss. The last session's routing sentence held on all twenty lines.
- **A value nothing consumes is not stored.** `asks` takes "thesis" only;
  "position" comes with 4.3. A proposal is not cached, being the system's
  prediction and not a record (D50, D58).

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
  This session was decisions and one change: 70 with its three rejected
  options, then 63, 64, 65, 68 and 69, each brought on its own with the
  figures that decide it and each waiting for its own word.
- **The check first, seen BLOCKED**; the Part before the code; the
  reference commit before the code commit each time, and a correction to
  the reference dated in its own commit.
- **A paid loop says first what it will fetch and store, table by
  table**, read off the store and the clock, and says after what moved.
  This session the CLI turned out to fetch nothing, its interval not run out, and was said so first.
- **A request to the outside is asked for before it is made**, one
  request or one set, and what it returns is kept whatever the code says.
- **A claim in a brief is measured before it is written down.**
- **A check is exercised against wrong versions**, one per rule, and a
  wrong version that changes nothing is a finding about the wrong version
  or about the test, not a pass.
- **The first live record is read against the document before it is
  believed**, quote by quote with the lines around it.
- **Grep the caller, not the registration.** `reader.read` has one caller,
  the research node; `proposer.propose` one, the node; `proposals.frame`
  one, the proposer; `nodes.reading_model()` and `nodes.proposal_model()`
  one each, the node; `_format_thesis_response` one, the synthesizer;
  `research_agent_node` is bound in `graph.py`.
- **CLAUDE.md is mine and untracked.** A session proposes wording; I apply it.
- No emoji in anything newly written. A count I predict is a count I add up.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect. My real portfolio's data in the repo: Order 6, last. No cached
holdings table; no fallback rate, currency or policy; no adjusted close; no
environment switch for which policy runs. **No invented figures as a runtime
source, and no price a stock will reach anywhere.** No mutation testing until
necessary. No widening of the router's schema to make it a better classifier.
No SIC code range recited from memory. No NOPAT at the company's filed tax
rate. No formatter sentence that states the system's status. No model
proposing a valuation assumption before case 4.3 defines how a proposal is
marked; no midpoint, spread or sorted range; no currency the record does not
carry. **No number, threshold or weight from a model; no second range
from a model's growth pair; no row written into the watchlist by the
system; no outcome decided by the formatter or the model; no gate that
checks the concentration clauses alone; no section truncated to fit and no
failed claim dropped to keep the rest.** **No score written into the ledger by the system; no partial credit
and no distance on a prediction; no prediction scored before its date; no
outcome filled to make one scorable; no event scored off filed facts.**
**No nearest heading, no heading matched by its title, no page furniture
removed by a rule measured on one filer, and no question in a reading's
prompt.** **No long quote cut in code to pass the cap, no third wording
after two misses, and no `asks` value nothing consumes.**

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

**1650 passed, 6 xfailed, 35 warnings, about 5 seconds.** Run at session
start (1646) and after every commit. The four are decision 70's: one test
replaced by two and four added.

**Golden set: twenty lines, one pinned failure** ("Should I rebalance my
portfolio?", errors 1). **One run this session, zero diff**, its stderr
holding only the pinned line's error. **A golden run asks for the sections
the cache lacks and proposes once**: no reading now that all three are
stored, about $0.007 on Sonnet for the proposal, recorded nowhere.

**The runner once: 16/18**, 4.4 PASS, 4.1 BLOCKED naming D36, 4.3 BLOCKED
at out_of_scope with intent `out_of_scope` and an empty plan. The runner
prints no answer, so which sections that run read cannot be read off it
(KNOWN_GAPS).

**The CLI, once.** The allocation question: priced as of 2026-09-18, total
408,447.50 USD, Equity 69.61%, the five lines summing to the total. It
fetched nothing — the holdings' stamps were 19 September 02:51 UTC and the
interval one day — and cost one Haiku call.

**Level 4: 4 of 6 cases pass (4.2, 4.4, 4.5, 4.6); 4.1 blocked by
decision; 4.3 blocked on the gate.** Read n/18 as a count of well-formed
answers and never as the system being good at research (benchmark.md),
never as the range being right, and never as a prediction having been
scored: none is due before February 2027.

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. **The trunk stood at 3ce7dab** at
session start, `thesis` merged into it. `cap` is this session's branch,
cut there on the owner's yes, since the branch the brief named did not
exist. `thesis`, `reader`, `research`, `score`, `publish`, `range`,
`keys`, `node`, `filer`, `bridge`, `consolidate`, `selection`,
`compliance` and `vocabulary` are merged and older. `wip/phase7-snapshot` holds rejected
Compliance/IPS code. `wip/rag-early` and tag `rag-early-parked` hold the
RAG code. `quant-inventory-parked` at 8d87455 holds the tree before the
seventeenth session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`2445c12e728c`**, 26 migrations, linear, all applied; no migration this
session. No reseed. **What this session wrote:**
- `daily_prices`: **7,009, unchanged**, the last close 2026-09-18. Every
  holding's last fetch is still 2026-09-19 02:51 UTC and GOOGL's 03:07;
  **the price interval ran out at those times on the 20th, so the next
  paid loop or allocation question fetches the closes**.
- `macro_data`: **209, unchanged**, as predicted: no trading day closed
  between the runs. The stamps were rewritten, last at 2026-09-20 16:29
  UTC by the golden run.
- `api_call_logs`: 2,436 to **2,439**, the macro fetch of each paid loop;
  the `api_quotas` counter for the 19th 22 to **25**.
- `document_readings`: 3 to **5 rows**. Item 1 under `1b2d86a8ba32`,
  `ba9a7051eeca` and **`a64f51fde1eb` (068134c's, the one the node
  serves)**; **Item 1A under `903e89b123b5`**, stored by one of the two
  paid loops; and **Item 7 under `54b0dba223f4`**, stored by the one
  request made after the cap changed, twelve claims and 2,554 characters
  of quotation against the cap of 3,600. Each was read by hand
  (KNOWN_GAPS). **All three sections the reader reads are now cached**,
  so a thesis answer asks the model only for its proposal.

Unchanged: `ticker_ciks` 10,422 rows as of 2026-09-16 01:33 UTC;
`filers` three rows; `filed_facts` 28,787, Apple's 15,132 and Alphabet's
13,655; `filed_fetch_metadata` two rows; `filed_documents` one row,
Alphabet's FY2025 10-K, 343,344 characters; `assets` ten rows, GOOGL the
tenth and not held and its asset class, sector and instrument type all
blank (decision 63 states them on the watchlist entry instead);
`financial_statements` 65 and `shares_history` 947, neither a source.
**The filings interval runs out on 22 and 23 September**: Apple's facts
pulled 2026-09-15 22:17 UTC, its filer row 2026-09-16 00:03, the ticker
file and JPMorgan's filer row 01:33, Alphabet's filer row and facts 01:38.

**There is no holdings table.** Portfolio 3, "Benchmark Portfolio", is the
only portfolio: nine ledger rows, cost basis 284,500 plus 15,500 cash, USD,
policy `ips.toml`. GOOGL is not held: it has an assets row and no ledger row.
Adobe has no assets row, no filers row and no facts.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py`, `test_screening.py` | the screening node, by `nodes.PHILOSOPHY_PATH` (decision 30); PHI-4.1's three parameters by `screening.range_assumptions` |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py`, `test_watchlist_loader.py`, `test_watchlist_predictions_loader.py` | the screening node, by `nodes.WATCHLIST_PATH`, the candidates and their growth pairs; the ledger node, the prediction rows; **the research node, the candidate and its thesis as written** |

### The philosophy check, as it stands

Unchanged this session. `screening_agent_node`, intent `research`, plan
`[ScreeningAgent]` alone when `asks` is unset, one ticker from
extraction; the calls in order are the ticker file, the submissions
document, the exclusion on the code, the company facts, the last close,
the range, the screen. Publishes `shared_data["screening"]` with the
block, the price and the range, each stop published beside what it stops.
On Alphabet today: the screen stops at PHI-2.1 for FY2021 (decision 48,
D36), the range publishes regardless, 129.39 to 205.62 on FY2025, the
price is the last stored close.

### The ledger, as it stands

Unchanged this session. `ledger_agent_node`, intent `ledger` (decision
58), plan `[LedgerAgent]` alone, no parameter read. Today nothing is due,
so the node fetches nothing and publishes four open records.

### The research agent, as it stands

**In the graph for a thesis question.** Intent `research` with `asks`
"thesis", set by extraction when the message names a thesis: plan
`['ScreeningAgent', 'ResearchAgent']`, the terminal table's row, the
requirement ResearchAgent needs ScreeningAgent. The node answers on the
screen's subject, CIK, as-of and source; reads Items 1, 1A and 7 through
the reader, a refusal about the filing putting every section left in
`not_read` once and a refusal about one section that section alone;
reads the figures the screen stored; asks for one proposal. Publishes
`shared_data["research"]`: asks, subject with its candidate, as-of,
thesis, the two models' ids, readings, not_read, predictions and
`proposal_stopped`. The synthesizer prints it through
`_format_thesis_response` when ResearchAgent ran.

| Piece | Where | Held by |
|---|---|---|
| The reading record | `portfolio_tool/reading.py`, `record` | `tests/test_reading.py`, to Part 15 A |
| The prediction frame; `WRITTEN`, the metrics it writes | `portfolio_tool/proposals.py`, `frame` | `tests/test_proposals.py`, to Part 15 C and D |
| A document's text; a filing's row and document; the store; the sectioner | `filing_text.py`, `providers/edgar.py`, `filings.py`, `sections.py` | their tests, to Part 16 |
| The reading model's client | `agents/reading_model.py`, `reading_model()` | `tests/test_reading_model.py`, to Part 16 D56 |
| The reader, its prompts at **068134c's wording** (quotes "at most thirty words", which the record no longer holds them to) | `portfolio_tool/reader.py` | `tests/test_reader.py`, 20, to Part 16 D56 and D57 |
| **The proposal model's client** | `agents/proposal_model.py`, `ProposalModel`, `proposal_model()` | `tests/test_proposal_model.py`, 22, to Part 15 F |
| **The proposer**: prompt, schema, message, one request, the frame | `portfolio_tool/proposer.py`, `propose`, `message`, `PROMPT`, `SCHEMA` | `tests/test_proposer.py`, 18, to Part 15 F |
| **The loader's thesis** | `portfolio_tool/watchlist.py`, `Candidate.thesis` | `tests/test_watchlist_loader.py` |
| **The node** and its seams | `agents/nodes.py`, `research_agent_node`, `reading_model()`, `proposal_model()` | `tests/test_research_node.py`, 17 |
| **The rendering** | `agents/nodes.py`, `_format_thesis_response`, `_proposed_row` | `tests/test_thesis_formatter.py`, 8, through `check_4_4` and Part 15 C's row |
| **`asks`** | `agents/extraction.py`, `schemas.ExtractedParameters.asks`, `smart_router._with_extraction` | `tests/test_extraction.py`, `tests/test_router_extraction.py` |
| **The routing** | `schemas.AGENTS`, `REQUIRES`, `TERMINAL`, the registry's research sentence; `graph.AGENT_NODES` | `tests/test_derived_plans.py`, `tests/test_smart_router.py`, the golden line |

**What the live answers show** (read by hand): Item 1's twelve claims
under `a64f51fde1eb`, five faithful, two faithful at the core, two
stretches marked `inferred`, three saying more than their quote under
`stated`; and, this session, Item 1A's twelve under `903e89b123b5`, three
faithful, six faithful at the core with a detail from the paragraph, two
saying more than their quote under `stated` and one stretch marked
`inferred` (KNOWN_GAPS); and Item 7's twelve under `54b0dba223f4`, eight
faithful, three faithful at the core and one getting the filing wrong,
calling Waymo's valuation-based charge "stock-based" as the last
session's Item 7 answer also did. The proposal is W-1.3, a gross margin for FY2026 of at least 59.65%, the
value right, resting on claims that say nothing about margins. Part 15 F9
has no code: the loader reads no `author`.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  for the router. **`ANTHROPIC_SONNET` is `claude-sonnet-5`**, used by the
  reader and the proposer, and **it refuses a temperature**; neither sends
  one. It answers with a thinking block beside the text on most requests,
  which both clients ignore. The router's stronger-model switch sends 0.0
  and would fail (KNOWN_GAPS).
- **The `anthropic` SDK is 1.2.0**: `messages.create` takes `output_config`
  for structured output, and a schema's `anyOf` of two object shapes is
  held by it (the proposer's).
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing. Four documents: company facts and submissions from
  `data.sec.gov`, the ticker file from `www.sec.gov/files/company_tickers.json`,
  a filing's primary document from the archive. Nothing was fetched from
  EDGAR this session.
- **Measured costs on `claude-sonnet-5`, $2 and $10 a million:** Item 1 about
  7,770 tokens in, $0.030; Item 1A about 24,800, $0.066; Item 7 about
  17,680, $0.051; a proposal over Item 1's claims 2,424 in and 214 out,
  $0.007. With all three sections cached, a paid loop asks for one
  proposal, about $0.007. The golden script, the runner and the CLI record
  none of their requests.
- **The price provider** is `nodes.price_provider()`; **the models** are
  `nodes.reading_model()` and `nodes.proposal_model()`, the same pattern,
  each calling its `agents` module's function; the EDGAR provider is
  `nodes.edgar_provider()`.
- **The allocation question fetches prices** when the one-day interval has
  run out: `data_agent_node` → `fetch_prices_tool` → `update_prices_for_asset`.
  The CLI is a paid loop in that case, and is said first.
- `config.toml` carries five fetch intervals. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; `config.toml` is read relative to the project
  root, so scripts run from the root.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router. A question can
  be piped in: `printf 'question\n:q\n' | python src/agents/cli.py --portfolio 3`.
- **Import order, for any commit sequence.** `filing_text.py` and
  `reading.py` import nothing of the repository's; `sections.py` imports
  `reading.SECTIONS`; `filings.py` imports `filing_text` and
  `providers.edgar.ARCHIVE_NAME`; `reader.py` imports `filings`, `reading`
  and `sections`; **`proposer.py` imports `proposals`, `reading` and
  `watchlist`**; `agents/reading_model.py` and **`agents/proposal_model.py`**
  import `agents.config` and nothing of `portfolio_tool`; `agents/nodes.py`
  imports the reader, the proposer and both models' modules inside the
  research node. The last sessions' order stands: `quant/fundamentals.py`
  imports `filed_figures.FIELDS`; `predictions.py` imports `fundamentals`
  and `watchlist`; `proposals.py` imports `predictions`.
- **Tests import from other tests.** `test_research_node.py` imports from
  `test_filed_documents.py`, `test_reader.py` and `test_screening_node.py`
  (the `provider` fixture); `test_thesis_formatter.py` its fixtures from
  `test_research_node.py`; `test_proposer.py` from `test_predictions.py`
  and `test_proposals.py`; the last sessions' imports stand.
- **Tests delete rows from the suite's copy they did not write**:
  `test_screening_node.py` Alphabet's and JPMorgan's facts, filers and the
  ticker table, `test_filed_facts_fetch.py` Apple's facts. A test reads
  only rows it wrote: `test_research_node.py` writes Alphabet's facts
  through the store and clears the stored document and readings of
  0001652044-26-000018 before and after each test.
- **The committed fixtures**: `tests/golden/edgar_document_goog_excerpt.htm`
  (Part 16 G); `tests/golden/edgar_filings_goog.csv` (Part 16 H). The
  fetched document is not committed.
- **The macro update has no interval**: any run of the macro agent, the
  golden set's first line among them, asks the price provider and upserts
  `macro_data`, adding rows when a trading day has closed since.
- **A scratch copy of the tree runs the suite against a changed file
  without touching the repository.** This session's copy was made from the
  working tree, `cp -R src tests docs alembic config.toml ips.toml
  philosophy.toml watchlist.toml pyproject.toml <copy>/`, because the
  changes under test were not yet committed; from HEAD it is
  `git archive HEAD src tests docs alembic config.toml ips.toml
  philosophy.toml watchlist.toml pyproject.toml | tar -x -C <copy>`. Copy
  `data/portfolio.db` into `<copy>/data/`, then from inside it
  `DATABASE_URL=sqlite:///<copy>/data/portfolio.db USE_MOCK_QUOTA=True PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 <repo>/.venv/bin/python -m pytest -q -p no:cacheprovider <tests>`
  after deleting its `__pycache__`. This session made no request of its
  own, so no raw answer was kept outside the store; the claims of the
  Item 1A reading the paid loops stored are in `document_readings` as the
  model supplied them (D57).
- **`nodes.utc_today()`** is the ledger node's clock; the screening node
  still reads the clock inline, and the research node reads the screen's
  as-of.
- **`tests/golden/edgar_facts_aapl.csv` has mixed line endings**, 97 of 104
  lines CRLF; it is edited on the bytes, each line keeping its own ending.
- **zsh does not split an unquoted variable into words.** Write test paths
  out. **zsh reads a bare `=word` as a command lookup**. **A `grep -c`
  that finds nothing exits 1 and stops a `&&` chain.** **`re.match`
  anchors at the start by itself.** **Python's look-behind needs a fixed
  width.** **`cat -A` is not macOS's.**
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
  fields of the figures block. `backtest/metrics.py` keeps its own copies of
  the risk metrics for the backtest intent.

---

## 4. What the twenty-eighth session did

`git log --oneline 3ce7dab..HEAD`, seven commits with this file. Six
decisions, the one change one of them asked for, and one live request
that the change made answerable. **No node, no check
and no Part of the gate**, by the brief: those come next.

**The loops, first.** `cap` cut from the trunk at 3ce7dab on the owner's
yes. pytest 1646. The CLI on the allocation question, said first to fetch
nothing since the interval had not run out, and it fetched nothing. Then,
on a yes and one after the other, the golden set once, twenty lines and
zero diff, and the runner once, 16/18 — each predicted first, table by
table, and each holding: no price row, no filing row, the macro count
still 209.

**What the paid loops left behind.** One of them was answered for Item 1A
within the old cap, and the reading is stored: the first ever accepted for
that section. It was read by hand against the stored section before
anything was decided on it, quote by quote with the paragraph around each.
Which of the two loops asked is not recorded anywhere, and the entry says
so.

**Under the yes, in order.**
- **fdea842** Part 15 D47 and section A, dated: the cap is on a reading's
  quoted text, 3,600 characters a section, not on a quote; the refusal
  names the section and the total; the total is checked after each claim's
  own rules. Decision 70, taken after its three options were brought with
  the figures.
- **7a42330** the code: `reading.record` drops the per-quote cap and adds
  the total; the runner's `_readings_invariants` does the same; one test
  replaced and five added, two touched. Each was seen failing against the
  old code, then against ten wrong versions on a scratch copy with
  bytecode off, and `test_reading.py` seen erroring without its module.
  pytest 1646 to 1650.
- **Decisions 63, 64, 65, 68 and 69**, each brought on its own with its
  options, its recommendation, its rejected alternatives and the figures
  that decide it, and each taken on its own word. §5 and KNOWN_GAPS carry
  them.
- **77d1e48** the record: three entries, four dated lines, the header.
- **1a2d2e4** benchmark.md's status note.
- **d422d7f** this file, regenerated.
- **One request for Item 7 under the new cap**, asked for and said first:
  accepted on the first draw, twelve claims, 2,554 characters of
  quotation against 3,600, the 330-character liquidity sentence that had
  been refused twice now quoted whole, stored and read by hand. Under the
  old per-quote cap the whole reading would have been refused and its
  other eleven claims lost. About $0.051 by the earlier measurement; the
  script kept the claims and not the token counts.
- **f562351** the record again: Item 7's entry, two dated lines, the
  header's counts.

**Spent on Sonnet:** about $0.12 on each of the two paid loops, the last
runs at the old cost, and about $0.051 on the Item 7 request, that one an
estimate. A run from here asks for no reading and proposes once, about
$0.007.

**Not done, on purpose.** The gate's Part, node and check and everything
of 4.3; the watchlist's new fields and their sentence, which need the
owner's word and come with the gate; Adobe's asset class, sector and
instrument type, unstated; the loader's `author` and Part 15 F9; the seven emoji headers; decisions 51, 52 and
54; the currency; the philosophy topic lookup; the CIK confirmation;
formulas for `operating_margin` and `free_cash_flow`; any change to the
reading or the proposal prompts for faithfulness.

---

## 5. Decisions taken, and decisions pending

**Taken this session**, each with the owner's yes, each brought on its own:
- **70**: the record caps a reading's quoted text at 3,600 characters a
  section and caps no single quote. Built, the reference first.
- **63**: the watchlist entry states a candidate's asset class, sector and
  instrument type; a candidate missing one is refused before the gate
  runs. **Alphabet's sector is Communication Services**, the owner's word.
- **64**: the purchase is funded by new money on top of the portfolio, the
  stated weight being the candidate's share of the grown total. IPS-5.3
  becomes a finding of its own.
- **65**: the weight is stated by the watchlist entry, which the gate
  cites as its `weight_source`. A weight in the question is its own
  decision, when a case asks.
- **68**: the outcome supports an entry only when all four permit — the
  screen clear, the gate clear, my entry condition met, the model's view
  of the thesis `stands`; otherwise it supports none and the grounds name
  each input that did not, a stop worded as not established. The model's
  view can only take away.
- **69**: 4.3 passes on a prediction **entered** in the ledger under the
  candidate, mine or the system's, cited by id; a proposal made in the
  same run is printed beside it, marked proposed and not entered.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve. **Eleven by count**: six closed, none opened.
CLAUDE.md's line reads "The list stands at 17 on 18 September" with
sixteen numbers and no longer matches on either count; it is mine to
change, to "The list stands at 11 on 20 September: 10, 12, 13, 16, 17, 22,
45, 48, 51, 52 and 54". The cap is 25.

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
    Trigger: the full test at the end of Order 4. The macro upsert, its
    call log and quota counter on every golden run are facts for it.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields: delete, its
    own sitting.
63, 64, 65, 68, 69 and 70 are closed this session; see the list above.

- **The full test at the end of Order 4** (owner's, unchanged): when Order
  4's last commit lands, the project stops for a full test across both
  halves before Order 5. Not this session: the gate and 4.3 are not built.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12. Level 4: 4.2, 4.4, 4.5 and 4.6 PASS; 4.1 BLOCKED by
decision, the runner's reason line saying why; 4.3 BLOCKED at
out_of_scope, its check written and its gate not built. 16/18. The ledger
has four open predictions and no scored one, and the first due date is 1
February 2027. n/18 is a count of well-formed answers. What the runner
cannot see: whether the range's ends are right (Part 11 C in pytest);
whether a filing's verdict is right (Part 14 C in pytest); any due
prediction until 2027; for 4.4, whether a quote supports its claim,
whether the prediction's reasons support it, and a field the answer
prints only on another line (KNOWN_GAPS). 4.4 passes on all three sections,
Items 1A and 7 having been read for the first time this session. Item 7
is the section that talks about margins, so the next proposal has claims
about margins available to cite, which the first ones did not.

---

## 7. Next steps, in order

**1. The gate and 4.3**, every decision it waited on now taken (§5). In
order: the watchlist's new fields, the sentence for `docs/WATCHLIST.md`
brought for my word first and Adobe's three values asked for, then
`watchlist.toml` and the loader; the Part that computes a candidate at a
stated weight by hand, with decision 68's truth table and decision 64's
funding; the gate node and the test that no outcome prints without its
block; `check_4_3`'s prediction requirement rewritten to decision 69;
`asks` gaining "position" with its pattern and its row; the registry's
sentences and the Siemens few-shot, a prompt hypothesis; 3.2 rewritten to
a price forecast and the out-of-scope paragraph at that commit, Part 2 of
benchmark.md in the next.

**On this portfolio the gate will fail IPS-3.1 at every weight**, equity
being 69.61% against a 65% ceiling, and IPS-5.3 with it under decision
64's funding (KNOWN_GAPS, with the figures). That is the policy answering
and not a defect; the first run should not be read as one.

**At the end of Order 4: the full test** (§5), before Order 5.

### Later, with reasons

- **The trunk.** `git switch baseline-v1 && git merge --ff-only cap`.
- **CLAUDE.md's pending line**, mine to change to eleven (§5).
- **Every paid loop still costs Sonnet**, less than before: each golden
  run, runner run and thesis question proposes once over three cached
  readings, about $0.007. A section whose stored reading stops passing the
  record is asked for again on every run (D57).
- **The next proposal can cite Item 7's claims**, which are about
  margins; the first three proposals cited claims that say nothing about
  one (KNOWN_GAPS). Whether it does is a thing to read, not to fix.
- **The next paid loop fetches the holdings' closes**: the interval ran
  out at 02:51 UTC on 20 September, GOOGL's at 03:07. The filings interval
  runs out on 22 and 23 September.
- **The first score I write**: seven tests go red by design, and the
  document test does not see a score the document lacks (KNOWN_GAPS).
- **The loader's `author`**, with my sentence in WATCHLIST.md, before the
  first system prediction is entered; Part 15 F9 comes with it.
- **1 February 2027**: W-2.1 and W-2.2 fall due.
- The proposals' reasons, the readings' faithfulness, a refusal's reason
  written for the code: each a hypothesis or a rendering change, each on
  its own trigger (KNOWN_GAPS).
- The router's stronger-model switch and `ANTHROPIC_SONNET`'s temperature,
  when the switch is turned on (KNOWN_GAPS).
- The currency on the range, the close and the reported figure, when a
  case asks (KNOWN_GAPS).
- The formatter headers carrying an emoji, seven in `nodes.py`. One commit,
  the runner run against it. `docs/workflow.md` in the console-glyph session.
- Three stale statements, mine to fix on my word: `watchlist.toml`'s
  header and `test_watchlist.py`'s docstring, "read by nothing yet"; Part
  11 D38's "D46".
- A philosophy topic lookup: a discriminator row on `research`, when a case asks.
- The node does not confirm the resolved CIK's submissions document lists
  the ticker asked (KNOWN_GAPS, the tickers entry).
- Decisions 51, 52 and 54, each its own sitting.
- The registry text naming VaR, drawdown and risk parity: a prompt change,
  prediction first, two golden runs.
- `operating_margin` and `free_cash_flow` get formulas, and
  `return_on_invested_capital` its tax rate, when a prediction names one.

---

## 8. Rules learned the hard way

**A refusal that held on every measured draw is still a draw.** Items 1A
and 7 were refused on every request the twenty-seventh session made, and
one of this session's two paid loops was answered for Item 1A under the
same prompt. Seven refusals are evidence about the odds, not a rule about
the model.

**A script that keeps the answer keeps what the answer cost.** The Item 7
request was wrapped so that the claims survived a refusal; the token
counts were not kept, so the one measurement the session could have taken
of a reading under the new cap was lost and the cost is an older
estimate.

**A brief's claim about the clock is checked against the clock.** The
brief said the price interval had run out early on 20 September; it was
19 September at 16:25 UTC, the holdings' stamps were 02:51 that morning
and the interval is one day, so the CLI fetched nothing.

**What nothing records cannot be said afterwards.** Which of the two paid
loops stored the accepted reading is unknowable: the runner prints no
answer and `document_readings` carries no time. The entry says so instead
of choosing the likelier one.

**Look at a path before writing to it.** A new test file written under a
name the suite already had replaced 20 committed tests without a word;
the suite's count was the only thing that showed it.

**A limit told to a model is not a limit.** Two wordings of the quote's
length, in characters and in words, moved nothing on the long sections:
the model quotes whole sentences, and the filer writes sentences longer
than the cap. The cap in code is the limit, and the second miss stops the
wording.

**Keep the raw answer of every paid request, whatever the code says.** A
refused reading whose answer was not kept could not be read by hand and
cost a second request.

**A check that looks for a field anywhere passes a line that lost it.**
Five wrong versions dropped a date or an accession from its own line and
passed `check_4_4` on another line's copy; the test holds each line whole.

**A pattern is tested on the word it names.** `theses?` matched "these"
and "theses" and not "thesis".

**A prediction about a table counts the calendar.** The macro count stands
still only when no trading day has closed since the last run.

**A loop the brief calls free is read off the code.** The CLI's allocation
question fetches prices once the interval has run out.

**A test over the suite's copy owns the rows it reads, and a test that
passes alone has not shown it**; **a wrong version that changes nothing is
not a pass**; **a number is measured before it is written, including the
one in the reference**; **a brief's instruction about the outside is
checked against the outside**; **a brief's claim about an interval is
checked against the clock**; **a falsifier row counts the way its section
counts**; **a quote is judged with the lines around it**; **a command
carries only what it needs**, broken again this session by `git stash
list`; **a brief's list is a claim, and a claim is measured**; **a test
over a committed file that changes by design has an expiry date**; **a
threshold compared strictly is the value its sentence says**; **a check
holds what is decided, and of what is not, the one thing no decision could
break**; **a Part covers what is built against now**; **"nothing fetched"
is read off the store, table by table**; **a promise about a tool is kept,
or the next message says it was not**; **a count in a message is
counted**; **sight a new case before writing its golden line**; **the
registry's descriptions are the prompt**; **add up the pending list**;
**the owner's documents are written on a separate word**; **the golden
loop's stderr goes to a file**; **say which loop cannot see a change**;
**a formatter states what the data says and never what the system is**;
**two paid loops on one SQLite file run one after the other**; **an
instruction with words missing is read against the record**; **grep the
writer the reader reads**; **delete the caller before the callee**; **a
wrong version checked in place can run the previous one's bytecode** —
still true, from earlier sessions.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/tmp/golden_err.txt
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 4.4

python src/agents/cli.py --portfolio 3        # :q to quit
printf 'What has to be true in a year for my GOOGL thesis to be right?\n:q\n' | python src/agents/cli.py --portfolio 3

grep -rn "SymbolName" src/ tests/ --include='*.py'
git status --short

# this session's commits: count from the branch's base, 3ce7dab.
git log --oneline 3ce7dab..HEAD
git rev-list --count 3ce7dab..HEAD

# by hand, from the project root, after a migration or a seed change:
alembic upgrade head
python src/portfolio_tool/scripts/seed_portfolio.py --reset

# what the database says it is at (expected 2445c12e728c):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# the reading tool's two tables:
sqlite3 data/portfolio.db "select accn, length(text), source from filed_documents; select accn, section, model, substr(prompt_version,1,12) from document_readings;"

# ten assets, GOOGL the tenth and not held; the filings tables:
sqlite3 data/portfolio.db "select count(*) from ticker_ciks; select cik, sic, pulled_at from filers; select cik, count(*) from filed_facts group by cik;"

# a check run against an edited, deliberately wrong module:
find src tests -name __pycache__ -type d -prune -exec rm -rf {} +
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/<file>.py

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only cap
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~5s, no model calls | Do the components still work; does every reference Part reproduce; does each node fetch in order and publish its block; does each rendering pass the runner's check; does the reader send what D56 says and the proposer what D58 says |
| CLI | ~3s and one Haiku call for most questions; **the thesis question ~45s and about $0.007 on Sonnet**; **fetches prices past their interval** | What it is actually doing: the plan, the parameters, the reasoning line, the answer text |
| Golden set | ~2 min, **about $0.007 on Sonnet per run for the thesis line** and Haiku, **writes price rows past their interval, filed rows past theirs, a reading it is answered for, and the macro rows, the call log and the quota counter on every run** | Did routing change anywhere (twenty lines, one pinned failure). Blind to parameters and answer text; stderr kept to a file |
| Benchmark runner | ~2 min, **about $0.007 on Sonnet for 4.4** and Haiku, **writes price and filed rows past their intervals, and a reading it is answered for** | How many cases pass, n/18. Blind to the four intents outside the roster, to whether a range's ends are right, to any due prediction until 2027, and, for 4.4, to a quote's support for its claim, a prediction's support in its reasons, a field printed only on another line, and which sections the run read at all |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once. **A live reading or proposal made on its own is not a loop**:
it is asked for, said first, and read by hand.
