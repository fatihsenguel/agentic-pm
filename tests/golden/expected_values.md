# Expected values — Benchmark Portfolio (portfolio_id 3)

Roadmap 0.2. Computed **by hand, before the capabilities exist**, so that when
they do exist there is an independent reference to check them against.

Do not update these numbers to match code output. If the code disagrees, one of
the two is wrong and that has to be resolved deliberately. If a decision below
turns out to be wrong, change the decision, record why, and recompute.

The working artefact is `expected_values.xlsx` in this directory — it holds the
formulas and the 252 daily closes. This file is the readable, diffable record,
because git cannot show a meaningful diff on a binary workbook. **Both must be
updated together.**

- **Computed on:** 2026-09-03
- **Price source:** Yahoo Finance via yfinance
- **Price as-of:** 2026-09-02 settled close

Pinned to settled closes on purpose. An intraday quote cannot be reproduced,
which would make this useless as a fixed reference.

**The pin has since diverged from live output, and that is the pin working.**
On 2026-09-04 the system reported prices as of **2026-09-03** and Equity at
**69.53%** against Part 2's 69.41%. Nothing here is wrong and nothing here gets
updated. Market values move with prices; this document is fixed at the 09-02
closes precisely so that a moving figure has something still to be compared
against. Expect the gap to widen.

If you are comparing a run against Part 2 and the percentages differ, check the
as-of date the answer states before looking for a defect. The figures that do
**not** move — cost bases, the ticker set, labels, percentages summing to 1.0 —
are the ones a run must still reproduce exactly, and they are what
`tests/benchmark/run_cases.py` asserts.

---

## Part 0 — Decisions

| # | Decision | Choice |
|---|---|---|
| D1 | Allocation by market value or cost basis? | **Market value.** Allocation means current exposure; cost basis tells you what you paid, which is irrelevant to risk. IPS limits are written against market value. |
| D2 | Does cash count in the allocation denominator? | **Include cash.** Holding cash is a positioning decision. Benchmark 2.1 checks concentration against the IPS, and IPS limits are expressed against total portfolio value. |
| D3 | Unsectored holdings reported explicitly, or excluded from the denominator? | **Report explicitly**, denominator = total invested. With 47% unsectored, dropping it silently inflates every sector figure roughly twofold. |
| D4 | P&L total return or price return? | **Price return.** Forced by the data model, not chosen: `Dividend` has no `portfolio_id`, so no dividend is attributable to a portfolio. Total return is not computable today. |
| D5 | Volatility on daily or weekly returns? | **Daily.** ~250 observations against ~52 weekly; weekly cuts microstructure noise but 52 points is a thin estimate. |
| D6 | Annualisation factor? | **252.** Must match D5. |
| D7 | Which volatility implementation is canonical? | **`quant/risk_metrics.py`** for return-series volatility, plus a new `portfolio_volatility(weights, cov_matrix)` there — none of the five existing implementations computes portfolio-level vol. `analytics_tools.py` and `optimization/base.py` delegate to it; `backtest/metrics.py` and the inline `engine.py:523` are scoped backtest-internal. |
| D8 | Volatility window? | **The 252 most recent daily closes, ending at the last settled close** — 252 because that is D6's annualisation factor and D5's observation count, so the window and the annualisation cannot drift apart. Instantiated 2025-09-03 to 2026-09-02 when this was computed; the dates move with the last close, the count does not. Stated as "one calendar year" in an earlier draft, which is the same thing only on average and is what the code was implementing when it came up a trading day short. The code implements this window since 7 September (`_evaluation_window`, `data_agent.py`); whether it reproduces Part 4 is shown by the fixture over the committed closes, not asserted here. |
| D9 | Is a figure exactly at an IPS limit a breach? | **No.** "No more than 12%" admits 12.00%; "no less than 3%" admits 3.00%. A breach is strictly over a max or strictly under a min, on the unrounded share. Rounding before comparing is a checker bug, and MSFT (12.11% against 12%) and JNJ (10.06% against 10%) are the rows that catch it on this portfolio. Made on the `Compliance` sheet 8 September; recorded here so both carry it. |
| D10 | Cost-basis method for a position built in tranches? | **Average cost.** The only method that yields one average price per position, which is what a holding row and every P&L figure here use. FIFO and LIFO differ from it only in realized gains, which matter for tax, permanently out of scope (benchmark.md Part 2). Decided 9 September for Part 8, before the ledger exists. |
| D11 | Are fees part of cost basis? | **Yes.** Cost basis is what was paid: quantity x price plus fees on a buy. Proceeds are quantity x price minus fees on a sale. A basis without fees understates cost and overstates every P&L. |
| D12 | What does a sale do under average cost? | Quantity falls by the quantity sold; the average price is unchanged; cost basis falls by quantity sold x average. The realized gain is proceeds minus the basis released. It is stated in Part 8 because D10 to D12 define it, and consumed by nothing: no case asks for realized gains. |
| D13 | Holdings derive from the ledger, not the other way round. | quantity = buys minus sells; cost basis per D11 and D12; average price = cost basis / quantity; `purchase_date` = the first buy, reported, never used in arithmetic. A holding row is a view of its ledger rows. Portfolio 3's nine rows are its ledger with one buy each, so Part 1 must reproduce from them to the cent - the invariant Part 8 pins. |
| D14 | A ledger row belongs to a portfolio. | The `transactions` table in the models has an asset and no portfolio, the shape that makes `Dividend` unattributable (Part 6). A row without a portfolio cannot be summed into one; the ledger carries `portfolio_id`, and the dividend fix follows the same rule when total return is built. The row's `amount` is the settled figure in the portfolio's currency, taken from the statement for a real portfolio and equal to the D11 arithmetic for a synthetic one; historical FX is data, never computed. |
| D15 | Base currency? | **The portfolio's own currency** (`Portfolio.currency`, which exists). Every figure the system reports for a portfolio is in it: total, allocation, P&L, compliance distances. One portfolio, one currency. Decided 10 September for Part 8 C, before any FX code exists. |
| D16 | Instrument currency, and a foreign holding's value? | **`Asset.currency`**, filled by the price source; a price is in it. A holding's value in the base currency is quantity x price x the spot rate on the price's as-of date, and the answer states both dates. |
| D17 | Where does a spot rate come from? | **A price source, like closes.** Stored per day with an as-of date, fetched from the same provider. A missing rate raises; nothing falls back to yesterday's rate or to 1. When the two currencies are the same there is no lookup. |
| D18 | Which currency are cost basis, average price and realized gain in? | **The base currency**, since they come from `amount` (D14). The average price of a foreign holding is therefore not comparable to its quoted price, and a formatter names the currency of every figure it prints. |
| D19 | What is a close? | **The instrument's official closing price on that date, in the instrument's currency, as traded**: adjusted for splits, so that the quantity held today times the close is the position's value on every date, and for nothing else. It is the figure a broker statement values the position at. A dividend adjustment is a return method, not a price, and does not belong in the column the valuation reads. Decided 10 September for Part 9, before any code. |
| D20 | Two sources give two closes for one instrument and one date. Which wins? | **The listing exchange's print.** A stored close that differs from it by a cent or more is a defect in the provider, fixed at the provider, never by editing the reference and never by averaging. Should a second live source ever exist, the system reports both figures, both sources and the date, and picks neither. |
| D21 | "Each of the last n fiscal years" means which years? | **The n most recent fiscal years whose reports were filed on or before the as-of date.** A year not yet reported does not count as a year; the check does not wait for it and does not fill it. Decided 10 September for Part 10, before any checker. |
| D22 | A clause over n years: one finding or n? | **One finding, decided by the worst year against the bound**: the lowest year for a floor, the highest for a ceiling. The distance is from that year, and every year is listed so the reader sees which one decided it. Rejected: the average (hides the bad year the screen exists to find), n findings (a clause has one verdict). |
| D23 | Is a figure exactly at a philosophy limit a failure? | **No.** The mirror of D9: strict, unrounded comparison, at the limit passes. Part 10 carries a row at exactly 2.0 times EBITDA to catch a checker that rounds or uses the wrong inequality. |
| D24 | What is a figure? | **The company's reported figure in its reporting currency, as filed**, adjusted by nobody. A metric that is a ratio of reported figures is computed by one stated formula, written out in Part 10, and that formula is the pipeline's definition of the metric key: return on invested capital, gross margin, net debt to EBITDA, free cash flow yield. A different formula is a different metric key. |
| D25 | A figure the company did not report, or a fiscal year missing from the block? | **The whole check stops and names the figure.** No verdict on that clause, no verdict on the others, no verdict on the company: PHI-1.2 says a clause is never skipped to let the rest of the screen report. The same shape as the compliance checker raising on a holding with no instrument type. |

Note the tension between D2 and Part 4: the volatility weights exclude cash
while D2 includes it. Resolved by disclosure — see Part 4.

---

## Part 1 — Positions

| Ticker | Asset class | Sector | Qty | Avg price | Cost basis | Price 09-02 | Market value | P&L abs | P&L % | Purchased |
|---|---|---|---|---|---|---|---|---|---|---|
| SPY  | Equity       | —          | 100 | 500.00 |  50,000.00 | 765.16 |  76,516.00 | +26,516.00 | +53.03% | 2024-01-15 |
| AAPL | Equity       | Technology | 200 | 200.00 |  40,000.00 | 324.96 |  64,992.00 | +24,992.00 | +62.48% | 2024-02-20 |
| MSFT | Equity       | Technology | 100 | 400.00 |  40,000.00 | 496.82 |  49,682.00 |  +9,682.00 | +24.21% | 2024-03-18 |
| JNJ  | Equity       | Healthcare | 150 | 150.00 |  22,500.00 | 275.21 |  41,281.50 | +18,781.50 | +83.47% | 2024-05-06 |
| JPM  | Equity       | Financials | 100 | 200.00 |  20,000.00 | 356.22 |  35,622.00 | +15,622.00 | +78.11% | 2024-07-15 |
| NEE  | Equity       | Utilities  | 200 |  75.00 |  15,000.00 |  83.10 |  16,620.00 |  +1,620.00 | +10.80% | 2024-09-09 |
| TLT  | Fixed Income | —          | 500 |  90.00 |  45,000.00 |  81.95 |  40,975.00 |  −4,025.00 |  −8.94% | 2025-01-13 |
| GLD  | Commodity    | —          | 100 | 250.00 |  25,000.00 | 402.78 |  40,278.00 | +15,278.00 | +61.11% | 2025-03-10 |
| VNQ  | Real Estate  | —          | 300 |  90.00 |  27,000.00 |  95.78 |  28,734.00 |  +1,734.00 |  +6.42% | 2025-06-02 |
| **Total invested** | | | | | **284,500.00** | | **394,700.50** | **+110,200.50** | **+38.73%** | |

Cash 15,500.00 · **Total portfolio 410,200.50**

---

## Part 2 — Allocation by asset class

| Asset class | Cost basis | % invested | % of total | Market value | % invested | % of total |
|---|---|---|---|---|---|---|
| Equity       | 187,500.00 | 65.91% | 62.50% | 284,713.50 | 72.13% | 69.41% |
| Fixed Income |  45,000.00 | 15.82% | 15.00% |  40,975.00 | 10.38% |  9.99% |
| Commodity    |  25,000.00 |  8.79% |  8.33% |  40,278.00 | 10.20% |  9.82% |
| Real Estate  |  27,000.00 |  9.49% |  9.00% |  28,734.00 |  7.28% |  7.00% |
| Cash         |  15,500.00 |    n/a |  5.17% |  15,500.00 |    n/a |  3.78% |
| **Total**    | **300,000.00** | | **100%** | **410,200.50** | | **100%** |

Per D1 and D2, the answer to case 1.1 is the **market value / % of total**
column: Equity 69.41%, Fixed Income 9.99%, Commodity 9.82%, Real Estate 7.00%,
Cash 3.78%.

---

## Part 3 — Allocation by sector

| Sector | Cost basis | % sectored | % invested | Market value | % sectored | % invested |
|---|---|---|---|---|---|---|
| Technology  |  80,000.00 | 58.18% | 28.12% | 114,674.00 | 55.08% | 29.05% |
| Healthcare  |  22,500.00 | 16.36% |  7.91% |  41,281.50 | 19.83% | 10.46% |
| Financials  |  20,000.00 | 14.55% |  7.03% |  35,622.00 | 17.11% |  9.03% |
| Utilities   |  15,000.00 | 10.91% |  5.27% |  16,620.00 |  7.98% |  4.21% |
| (no sector) | 147,000.00 |    n/a | 51.67% | 186,503.00 |    n/a | 47.25% |
| Sectored    | 137,500.00 |  100%  |        | 208,197.50 |  100%  |        |
| Invested    | 284,500.00 |        |  100%  | 394,700.50 |        |  100%  |

---

## Part 4 — Twelve-month portfolio volatility

**10.2936%**

| | |
|---|---|
| Method | Standard deviation of the portfolio's own daily return series |
| Weights | Market value of invested assets at 2026-09-02, cash excluded |
| Window | 2025-09-03 → 2026-09-02 (D8) |
| Observations | 251 daily returns from 252 closes |
| Daily std dev | 0.00648436 (sample) |
| Annualisation | × √252 (D6) |

Sanity check passes: the weighted average of the single-name volatilities is
**20.5408%**, roughly double the portfolio figure. That gap is diversification —
TLT at 9.55% and GLD at 29.21% move largely independently of the equity block.

**Cash caveat.** The weights exclude cash, which sits awkwardly against D2.
Including cash, which has no volatility, gives **9.90%** against total portfolio
value. Reported as 10.29% on invested assets with the basis stated, since case
1.3 passes on traceability rather than on a particular denominator.

Computed twice independently — spreadsheet formulas and a separate Python
recomputation from the same closes — agreeing to 4.9e-16.

---

## Part 5 — Expected answers

Written out in the shape benchmark.md Part 3b requires: the result in the units
asked for, the data age as an as-of date, the source for any policy claim, and
what it did not do. Full text lives on the `Answers` sheet of the workbook.
Headline figures:

- **1.1** — Total 410,200.50 as of 2026-09-02. Equity 69.41%, Fixed Income
  9.99%, Commodity 9.82%, Real Estate 7.00%, Cash 3.78%. Must state that
  percentages include cash, and that fund holdings are counted at fund level.
- **1.2 (JPM)** — Up 15,622.00, +78.11%, since 2024-07-15. 100 shares, cost
  20,000.00 at 200.00 average, now 35,622.00 at 356.22. Must name the purchase
  date and state that this is price return only.
- **1.3** — 10.29% annualised. Must carry the method, window, weights basis and
  annualisation factor, and must not be an average of the per-holding vols.
- **1.4 (Technology)** — 2 positions, 114,674.00, 29.05% of invested. AAPL
  64,992.00 (16.47%), MSFT 49,682.00 (12.59%). Must state that 47.25% of
  invested value carries no sector at all, and that there is no look-through.

---

## Part 6 — What these values do not cover

- **Price return only.** Dividends live in a table with no `portfolio_id`, so
  none can be attributed to a portfolio. P&L here understates actual return on
  JNJ, JPM, NEE, VNQ and TLT.
- **One purchase date per position.** `PortfolioHolding` carries a single
  `purchase_date` and `average_price`, which cannot represent a position built
  in tranches. Fine here — every position is a single purchase. Not fine for a
  real portfolio with savings plans or DRIP.
- **Single currency.** Everything is USD. There is no FX conversion anywhere in
  the codebase, so these values say nothing about whether a multi-currency
  portfolio computes correctly.
- **No look-through.** SPY, TLT, GLD and VNQ are treated as sectorless. A real
  sector allocation would decompose SPY into constituents. Out of scope, but it
  means the sector figures describe holdings, not economic exposure — true
  technology exposure is materially above 29.05%.
- **One window, one regime.** Twelve months of daily data is a single estimate
  and says nothing about volatility under different conditions.

---

## Part 7 — Compliance against `docs/IPS.md`

Computed 2026-09-07 from Part 1's 09-02 market values, before the checker
exists, so the checker has something independent to be wrong against. Every
figure here is one division of a Part 1 number by the Part 1 total; the
`Compliance` sheet of the workbook is to carry the same formulas.

**Denominator.** Total portfolio value including cash, **410,200.50**, for
every clause - the IPS says so in its preamble and in §3 and §4. Note this is
*not* Part 3's sector denominator: Part 3 reports sectors as a share of
invested value (D3), the IPS limits sectors as a share of total. Both are
right; they answer different questions. 1.4 keeps D3, IPS-4.3 uses total.

**Which holdings are "directly held shares".** IPS-4.2 and 4.3 count only
directly held shares; IPS-4.3 defines the excluded set as holdings without a
sector. On this portfolio that is SPY, TLT, GLD and VNQ (funds); AAPL, MSFT,
JNJ, JPM and NEE are shares. How the code knows is an open decision in
KNOWN_GAPS, not a fact this reference decides.

**Distances.** IPS-5.2: the required change is the amount that returns the
figure to the limit. Given in percentage points of total, and in currency
*at unchanged total* - which is the case when the excess is sold to cash.
Any other trade moves the denominator and the currency figure with it; the
percentage-point figure is the reference, the currency figure is a
convenience under that stated assumption. The `Compliance` sheet carries the
distance on every row, signed: positive is a breach, negative is headroom;
the tables below print it for breaches and describe headroom in words.

**Statuses.** A finding is `ok`, `breach` or `exempt`. Exempt is for a
holding the clause does not apply to - the funds under IPS-4.2 - and is not
`ok`: an exempt row carries no arithmetic and is reported as exempt, so the
policy is visibly applied to every holding rather than silently to some.
Comparison is strict and unrounded (D9).

### §3 — Strategic allocation

| Clause | Class | Market value | % of total | Limit | Status | Distance |
|---|---|---|---|---|---|---|
| IPS-3.1 | Equity | 284,713.50 | 69.41% | 40% – 65% | **breach, above max** | 4.41 pp = 18,083.18 |
| IPS-3.2 | Fixed Income | 40,975.00 | 9.99% | 8% – 30% | ok | 1.99 pp above min |
| IPS-3.3 | Commodity | 40,278.00 | 9.82% | ≤ 15% | ok | 5.18 pp below max |
| IPS-3.4 | Real Estate | 28,734.00 | 7.00% | ≤ 15% | ok | 8.00 pp below max |
| IPS-3.5 | Cash | 15,500.00 | 3.78% | ≥ 3% | ok | 0.78 pp above min |

### §4 — Concentration

**IPS-4.1, every holding, limit 12% of total**

| Ticker | Market value | % of total | Status | Distance |
|---|---|---|---|---|
| SPY | 76,516.00 | 18.65% | **breach** | 6.65 pp = 27,291.94 |
| AAPL | 64,992.00 | 15.84% | **breach** | 3.84 pp = 15,767.94 |
| MSFT | 49,682.00 | 12.11% | **breach** | 0.11 pp = 457.94 |
| JNJ | 41,281.50 | 10.06% | ok | |
| TLT | 40,975.00 | 9.99% | ok | |
| GLD | 40,278.00 | 9.82% | ok | |
| JPM | 35,622.00 | 8.68% | ok | |
| VNQ | 28,734.00 | 7.00% | ok | |
| NEE | 16,620.00 | 4.05% | ok | |

**IPS-4.2, directly held shares, limit 10% of total**

| Ticker | Market value | % of total | Status | Distance |
|---|---|---|---|---|
| AAPL | 64,992.00 | 15.84% | **breach** | 5.84 pp = 23,971.95 |
| MSFT | 49,682.00 | 12.11% | **breach** | 2.11 pp = 8,661.95 |
| JNJ | 41,281.50 | 10.06% | **breach** | 0.06 pp = 261.45 |
| JPM | 35,622.00 | 8.68% | ok | |
| NEE | 16,620.00 | 4.05% | ok | |

| SPY, TLT, GLD, VNQ | | | exempt | not attributed to an issuer (IPS-4.2) |

Which holdings are funds is data the code has to carry, not infer:
`Asset.instrument_type`, `share` or `fund`, set by the seed, and the checker
raises on a holding where it is missing (decision recorded in KNOWN_GAPS).

**IPS-4.3, sectors over directly held shares, limit 25% of total**

| Sector | Market value | % of total | Status | Distance |
|---|---|---|---|---|
| Technology | 114,674.00 | 27.96% | **breach** | 2.96 pp = 12,123.88 |
| Healthcare | 41,281.50 | 10.06% | ok | |
| Financials | 35,622.00 | 8.68% | ok | |
| Utilities | 16,620.00 | 4.05% | ok | |
| (no sector) | 186,503.00 | 45.47% | reported, not counted | |

### Two figures decided by cents

MSFT is 0.11 pp over IPS-4.1 and JNJ 0.06 pp over IPS-4.2 at these closes.
A live run will put either on the other side of its limit within days. Pinned
here as computed; the checker's unit test runs over the committed closes and
is stable, the runner asserts on the structure of a finding and not on which
clauses breach, and no document should say "MSFT breaches 4.1" as if it were
a standing fact. Cash is 0.78 pp above IPS-3.5 and can cross the same way.

### Expected answers, in the Part 3b shape

- **2.1 (concentration)** - the IPS-4.1 table (three breaches), the IPS-4.2
  table (three breaches, four exempt), the IPS-4.3 table (one breach), each
  figure as of 2026-09-02, each verdict citing its clause id. Must state
  that funds are counted at fund level and not attributed to issuers or
  sectors. Gives no recommendation.
- **2.2 (any rule violated)** - every checkable clause with its status, one
  finding per subject: eight breaches (IPS-3.1; 4.1 on SPY, AAPL, MSFT; 4.2
  on AAPL, MSFT, JNJ; 4.3 on Technology) and, at clause level, four clauses
  fully inside their limits (3.2 to 3.5). Must also name the clauses it
  did not compute (IPS-1.x, 2.x, 5.x, 6.x) as policy statements outside the
  check, so "all rules" is visibly all of them. Gives no recommendation.
- **2.3 (what would have to change)** - for each breach, the condition in
  the Distance column: Equity down 4.41 pp of total; SPY down 6.65 pp, AAPL
  3.84 pp, MSFT 0.11 pp under IPS-4.1; AAPL 5.84 pp, MSFT 2.11 pp, JNJ
  0.06 pp under IPS-4.2; Technology 2.96 pp under IPS-4.3. Overlaps are
  stated, not netted: reducing AAPL by 5.84 pp satisfies both of its
  clauses and most of the Technology excess, and that is for the reader to
  see. Names no instrument to trade and no target (IPS-5.2).
- **3.1 (15% in a single position)** - refused, citing IPS-4.1 (limit 12%,
  3.00 pp over) and, if the position would be a directly held share,
  IPS-4.2 (limit 10%, 5.00 pp over). No weighing, no "depends".
- **3.4 (currency risk)** - the policy contains no clause on currency risk.
  Names nothing that is not in `docs/IPS.md`. The nearest clause by topic
  is none; IPS-2.1 lists instrument types and is not about currency.

---

## Part 8 — The transaction ledger

Computed 2026-09-09 by hand, before the ledger exists (DIRECTION.md Order 2,
item 1), so the code has something independent to be wrong against.
Decisions D10 to D14. Plain decimal arithmetic, none of the repository's code.

**A ledger row.** `portfolio`, `date`, `type` (buy or sell), `ticker`,
`quantity`, `price` per unit in the instrument's currency, `fees`, `amount`:
the settled figure in the portfolio's currency, quantity x price + fees on a
buy, quantity x price - fees on a sale (D11, D14).

### A. Portfolio 3 as a ledger — the invariant

One buy per position, no fees, the dates and prices of Part 1. The holdings
derived from these rows (D13) must equal Part 1's quantity, average price,
cost basis and purchase date to the cent, and the total 284,500.00.

| Date | Type | Ticker | Qty | Price | Fees | Amount |
|---|---|---|---|---|---|---|
| 2024-01-15 | buy | SPY  | 100 | 500.00 | 0.00 |  50,000.00 |
| 2024-02-20 | buy | AAPL | 200 | 200.00 | 0.00 |  40,000.00 |
| 2024-03-18 | buy | MSFT | 100 | 400.00 | 0.00 |  40,000.00 |
| 2024-05-06 | buy | JNJ  | 150 | 150.00 | 0.00 |  22,500.00 |
| 2024-07-15 | buy | JPM  | 100 | 200.00 | 0.00 |  20,000.00 |
| 2024-09-09 | buy | NEE  | 200 |  75.00 | 0.00 |  15,000.00 |
| 2025-01-13 | buy | TLT  | 500 |  90.00 | 0.00 |  45,000.00 |
| 2025-03-10 | buy | GLD  | 100 | 250.00 | 0.00 |  25,000.00 |
| 2025-06-02 | buy | VNQ  | 300 |  90.00 | 0.00 |  27,000.00 |
| | | **Total** | | | | **284,500.00** |

### B. One position built in tranches and partly sold

A synthetic position in KO, not part of portfolio 3: a fixture for the
ledger arithmetic alone. Fees chosen so that every figure is exact to the
cent, so a rounding step anywhere shows.

| Date | Type | Qty | Price | Fees | Amount | Qty after | Cost basis after | Average after |
|---|---|---|---|---|---|---|---|---|
| 2024-09-09 | buy  | 200 | 75.00 | 0.00 | 15,000.00 | 200 | 15,000.00 | 75.00 |
| 2025-02-03 | buy  | 100 | 90.00 | 3.00 |  9,003.00 | 300 | 24,003.00 | 80.01 |
| 2025-11-17 | sell |  50 | 85.00 | 2.00 |  4,248.00 | 250 | 20,002.50 | 80.01 |

The sale releases 50 x 80.01 = 4,000.50 of basis against proceeds of
4,248.00: a realized gain of **247.50** (D12), stated and consumed by nothing.
The position after: **250 @ 80.01, cost basis 20,002.50, purchase date
2024-09-09** (D13, the first buy).

At a price of 88.00: market value 22,000.00, P&L **+1,997.50, +9.99%**
(1,997.50 / 20,002.50 = 0.099863), price return per D4.

### C. One foreign-currency position in a euro portfolio

Computed 2026-09-10 by hand, before any FX code exists (DIRECTION.md Order 2,
item 2). Decisions D15 to D18. A synthetic position, not part of portfolio 3:
a fixture for the currency arithmetic alone. Every rate is stated and
synthetic; nothing here is a market rate. Figures chosen so that every step
is exact to the cent.

**The portfolio's base currency is EUR (D15). The instrument is AAPL, quoted
in USD (D16).** Rates are euros per dollar.

| Date | Type | Qty | Price (USD) | Rate EUR/USD | Fees (EUR) | Amount (EUR) |
|---|---|---|---|---|---|---|
| 2024-02-20 | buy | 100 | 200.00 | 0.9200 | 5.00 | 18,405.00 |

Amount = 100 x 200.00 x 0.9200 + 5.00 = 18,400.00 + 5.00 = **18,405.00 EUR**,
the settled figure in the portfolio's currency (D14). The rate on the row is
data from the statement, shown here so the arithmetic can be checked; the
ledger stores the amount, not the rate.

The position after: **100 @ 184.05 EUR, cost basis 18,405.00 EUR, purchase
date 2024-02-20** (D13, D18). The average price is in euros and is not the
200.00 dollars paid per share.

**Valuation** at the 2026-09-02 close of 324.96 USD (Part 1) and a stated spot
rate of **0.8500 EUR/USD** on the same date (D17):

| | |
|---|---|
| Market value | 100 x 324.96 x 0.8500 = **27,621.60 EUR** |
| P&L abs | 27,621.60 - 18,405.00 = **+9,216.60 EUR** |
| P&L % | 9,216.60 / 18,405.00 = 0.500766 = **+50.08%** |
| Price as-of | 2026-09-02 |
| Rate as-of | 2026-09-02 |

For contrast, the same shares in dollars went from 20,000.00 to 32,496.00,
+62.48% (Part 1's AAPL row). The euro gain is smaller because the dollar fell
from 0.9200 to 0.8500 euros over the holding period. That split, into a price
part and a currency part, is **not** computed here: it is a measure with its
own reference, when a case asks.

**Under D17, the same position with no rate for 2026-09-02 has no market
value.** The answer is a refusal naming the missing rate and date, not a value
at yesterday's rate and not a value at 1.0000.

### What Part 8 does not cover

- **The currency split of a gain.** Stated once under C; not a measure.
- **Dividends and corporate actions.** Not ledger rows here; a split or a
  dividend reinvested is a buy-shaped row when total return is built. A
  dividend in a foreign currency follows D14: the settled amount is data.
- **Realized gains as a figure the system reports.** Stated once under B;
  no case asks.

---

## Part 9 — The price source

Computed 2026-09-10 by hand, before any code (DIRECTION.md Order 2, item
3), so the provider has something independent to be wrong against.
Decisions D19 and D20. No arithmetic beyond a subtraction per row.

**What is being checked.** A close the system stores is defended when a
source that is not the provider prints the same figure for the same
instrument and date, to the cent. Two dates are needed. The valuation date,
2026-09-02, is Part 1's pin: the nine closes every figure in Parts 1 to 3
and 7 stands on. And dates *before a dividend*, because the provider's
default returns closes scaled by every later dividend, so a check on the
most recent date alone passes whether or not the stored history is the
print. Rows B below are those dates, chosen where the database and the
committed series disagree most.

**The second source.** The listing exchange's own historical quotes,
`api.nasdaq.com/api/quote/<TICKER>/historical` with `assetclass=stocks`
for the shares and `assetclass=etf` for the funds, 20 August to 3 September
2026, field `Close/Last`. Fetched by me on 2026-09-10 with one command from
the shell; the output as printed is the record, 99 rows over the nine
holdings. Not Yahoo, and the exchange's print by definition.

**Tolerance: to the cent.** Two figures agree when they are equal after
rounding to two decimals. An official close is one print to the cent, so
two as-traded sources agree exactly; the float32 artefacts in the database
(324.959991 for 324.96) vanish on rounding. A cent or more is a different
figure, named here and decided by D20, never averaged.

### A. The valuation date — Part 1's nine closes

| Ticker | Exchange 2026-09-02 | Part 1 | Difference | Verdict |
|---|---|---|---|---|
| SPY  | 765.16 | 765.16 | 0.00 | agrees |
| AAPL | 324.96 | 324.96 | 0.00 | agrees |
| MSFT | 496.82 | 496.82 | 0.00 | agrees |
| JNJ  | 275.21 | 275.21 | 0.00 | agrees |
| JPM  | 356.22 | 356.22 | 0.00 | agrees |
| NEE  |  83.10 |  83.10 | 0.00 | agrees |
| TLT  |  81.95 |  81.95 | 0.00 | agrees |
| GLD  | 402.78 | 402.78 | 0.00 | agrees |
| VNQ  |  95.78 |  95.78 | 0.00 | agrees |

Nine of nine. Part 1's closes are the exchange's prints, and so is every
figure derived from them. They agree because 2026-09-02 lies after each
holding's latest ex-dividend date at the time the closes were fetched; the
same fetch repeated after the next one would not reproduce them, which is
what B shows on the dates where it has already happened.

### B. Dates before a dividend — the falsifier

The committed series `benchmark_closes.csv` (Part 4's 252 closes) against
the exchange, and the database as it stood on 2026-09-10 after the
provider had refetched:

| Ticker | Date | Exchange | Committed series | Database 2026-09-10 | Database minus exchange | Verdict |
|---|---|---|---|---|---|---|
| JNJ | 2026-08-21 | 270.24 | 270.24 | 268.91 | -1.33 | **database wrong** |
| TLT | 2026-08-28 |  82.88 |  82.88 |  82.56 | -0.32 | **database wrong** |

Over the whole fetch: 90 of the 99 exchange rows fall inside the committed
series and all 90 agree with it to the cent; the database agrees with the
exchange on 82 and disagrees on 17, every one of them a JNJ, NEE or TLT
row dated before that holding's latest ex-dividend date, and every one of
them lower than the print by that dividend's factor. Across Part 4's full
window the database disagrees with the committed series on 1,629 of 2,268
cells, every holding except GLD, which pays no dividend, by up to 4.4% on
TLT.

**The cause is the provider's call, not the vendor.** The price method
calls the library's history function with its default, and that default
replaces the close with the dividend-adjusted close. The library's own
adjustment divides the print by the product of every later dividend
factor, which is why a stored figure for a past date changes each time a
new ex-dividend date passes and the row is fetched again. The exchange
rate method is unaffected: a rate has no dividend.

**What Part 9 settles.** The committed series is the print (D19), so Part
4's 10.2936% was computed on as-traded closes and needs no recomputation.
The database is not the print on any date before a holding's latest
ex-dividend date, and the fix is at the provider: ask for the unadjusted
close, then refetch the stored history once so that the table holds one
convention. Under D20 the reference does not move.

### What Part 9 does not cover

- **Splits.** None of the nine holdings split inside Part 4's window, so
  there is no row that checks the split half of D19. The first held
  instrument that splits gets its row here before the code is trusted on
  it.
- **A total-return series.** Volatility over as-traded closes sees an
  ex-dividend drop as a negative return; D5 to D8 are silent on it and
  Part 4 is computed on the print. Whether the covariance should run on a
  series adjusted from the dividends table is a Part 4 decision with its
  own reference, not this one.
- **Where the source is named.** A close stored with its source on the row
  is the trace; whether the answer text names it is a rendering decision.

---

## Part 10 — The philosophy check

Computed 2026-09-10 by hand, before any checker exists (DIRECTION.md Order
4, first tool), so the checker has something independent to be wrong
against. Decisions D21 to D25. Plain decimal arithmetic, none of the
repository's code. Policy: `docs/PHILOSOPHY.md`, `philosophy.toml`.

**The candidate and its figures are synthetic.** W-1 on the synthetic
watchlist is Alphabet, and the figures below are stand-ins typed for this
reference, not the company's filings. This Part is a reference for the
checker's arithmetic, not for the company. Real reported figures arrive
with the filings reader, which defends them the way Part 9 defended the
closes.

**As-of date:** 2026-09-10. Fiscal years reported by then: FY2021 to
FY2025 (D21). FY2026 is not a year. Reporting currency USD; money in
millions except the price and the valuation range, per share.

**The figures block, the checker's input.** Per company, per metric, per
fiscal year: the value, the fiscal year's end date, the date its report was
filed (D21 counts a year by this date; the dates here are synthetic, about
five weeks after each year end), the source. Here the
source of every row is `expected_values.md Part 10`. For PHI-4.1 also a
valuation range and a price, each with its as-of date.

### A. Reported figures (USD millions)

| FY | Ends | Filed | Revenue | Gross profit | Operating income | Tax rate | D&A | Operating cash flow | Capex | Equity | Debt | Cash |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FY2021 | 2021-12-31 | 2022-02-04 | | | 20,000 | 0.20 | | | | 120,000 | 20,000 | 40,000 |
| FY2022 | 2022-12-31 | 2023-02-03 | | | 13,500 | 0.20 | | | | 128,000 | 22,000 | 42,000 |
| FY2023 | 2023-12-31 | 2024-02-02 | 100,000 | 55,000 | 24,000 | 0.20 | | | | 140,000 | 20,000 | 40,000 |
| FY2024 | 2024-12-31 | 2025-02-05 | 112,000 | 63,840 | 30,000 | 0.20 | | | | 150,000 | 18,000 | 43,000 |
| FY2025 | 2025-12-31 | 2026-02-04 | 125,000 | 72,500 | 36,000 | 0.20 | 16,000 | 52,780 | 22,000 | 170,000 | 16,000 | 42,000 |

A blank cell is a figure the reference does not need, not a figure the
company did not report; section E is the missing-figure case.

Shares outstanding 4,000 million. Price 171.00 as of 2026-09-10. Valuation
range 180.00 to 240.00 per share as of 2026-09-10, typed here; Part 11 will
compute one from stated assumptions.

### B. The metric formulas (D24)

- **return_on_invested_capital** = operating income x (1 - tax rate) /
  (equity + debt - cash), per fiscal year, on that year's figures.
- **gross_margin** = gross profit / revenue.
- **net_debt_to_ebitda** = (debt - cash) / (operating income + D&A).
- **free_cash_flow_yield** = (operating cash flow - capex) / (price x shares
  outstanding), the latest fiscal year's cash flows at the as-of price.

### C. The metrics by year

| FY | Invested capital | NOPAT | ROIC | Gross margin |
|---|---|---|---|---|
| FY2021 | 100,000 | 16,000 | 0.1600 | |
| FY2022 | 108,000 | 10,800 | **0.1000** | |
| FY2023 | 120,000 | 19,200 | 0.1600 | 0.5500 |
| FY2024 | 125,000 | 24,000 | 0.1920 | 0.5700 |
| FY2025 | 144,000 | 28,800 | 0.2000 | 0.5800 |

FY2025: net debt = 16,000 - 42,000 = -26,000; EBITDA = 36,000 + 16,000 =
52,000; net_debt_to_ebitda = -0.5000. Free cash flow = 52,780 - 22,000 =
30,780; market value = 171.00 x 4,000 = 684,000; free_cash_flow_yield =
0.0450. Discount to the low end of the range = 1 - 171.00 / 180.00 = 0.0500.

### D. The findings

One finding per numeric clause (D22). Distance in the metric's own unit,
signed so that positive is a failure: `limit - observed` against a floor,
`observed - limit` against a ceiling. Percentage points where the metric is
a share.

| Clause | Type | Metric | Years read | Deciding year | Observed | Limit | Bound | Status | Distance |
|---|---|---|---|---|---|---|---|---|---|
| PHI-2.1 | metric_band | return_on_invested_capital | FY2021 to FY2025 | FY2022 | 0.1000 | 0.12 | min | **fail** | +2.00 pp |
| PHI-2.2 | metric_band | gross_margin | FY2023 to FY2025 | FY2023 | 0.5500 | 0.35 | min | pass | -20.00 pp |
| PHI-3.1 | metric_band | net_debt_to_ebitda | FY2025 | FY2025 | -0.5000 | 2.0 | max | pass | -2.50 x |
| PHI-4.1 | margin_of_safety | discount to the low end of the range | as of 2026-09-10 | | 0.0500 | 0.25 | min | **fail** | +20.00 pp |
| PHI-4.2 | metric_band | free_cash_flow_yield | FY2025 | FY2025 | 0.0450 | 0.04 | min | pass | -0.50 pp |

PHI-4.1 read another way: the most I would pay is 180.00 x (1 - 0.25) =
135.00, and the price is 171.00, 36.00 over. The finding carries the
discount, a fraction like every other observed value; the price form is the
formatter's to print from the same figures.

**Statements, cited and not computed:** PHI-1.1, PHI-1.2, PHI-2.3, PHI-3.2,
PHI-4.3, PHI-5.1, PHI-5.2, PHI-6.1, PHI-6.2, PHI-6.3, PHI-7.1, PHI-7.2. A
full check lists them, so the philosophy is visibly all of it.

**The candidate does not clear the philosophy** on these figures: two of
five numeric clauses fail. That is a fact about the synthetic figures, chosen
so that both directions of a finding and the range-based clause's failing
side are in the reference; it says nothing about the company.

### E. Falsifier rows

**At the limit passes (D23).** The same FY2025 with debt 120,000 and cash
16,000: net debt 104,000, EBITDA 52,000, net_debt_to_ebitda = 2.0000
exactly against a ceiling of 2.0. Status **pass**, distance 0.00. A checker
that rounds before comparing, or compares with the wrong inequality, fails
this row.

**A missing figure stops the check (D25).** The same block with FY2024's
gross profit absent. The check stops on PHI-2.2 naming `gross_margin` for
`FY2024` and reports no finding on any clause. Not a pass on PHI-2.1, not a
verdict on the company, not a finding on PHI-2.2 over the two years it has.

**A year not yet reported is not a year (D21).** The same block asked for
as of 2025-06-30, before FY2025 was filed: PHI-2.1 reads FY2020 to FY2024
and the block has no FY2020, so the check stops naming
`return_on_invested_capital` for `FY2020`. It does not read FY2021 to
FY2025 and it does not read four years.

### Expected answers, in the Part 3b shape

- **4.1 (does X clear my philosophy)** - the five findings above with their
  deciding years and distances, each citing its clause; the twelve
  statements named as not computed; every figure with its fiscal year and
  its source; no recommendation.
- **4.6 (a missing figure)** - "the check stopped: FY2024 gross margin is
  not in the figures", no finding on any clause, nothing invented.

---

## Part 11 — The valuation range

Not computed. Reserved for the valuation pipeline (DIRECTION.md Order 4, case
4.2): a range from stated assumptions, by hand, before the pipeline exists.
Part 12 was written first because the reader comes before the valuation it
would value.

---

## Part 12 — The filings reader

Recorded 2026-09-11 by hand from one fetched artifact, before any provider
method exists, so the reader has something independent to be wrong against.
This is the Part 9 pattern applied to filed figures instead of closes: Part 9
asked whether a stored close is the exchange's print; this asks whether a
stored figure is what the filer filed.

**What this Part is not.** It is not a reference for the metrics — Part 10 is
that, on synthetic figures, and it stays. This Part is a reference for the
fetch: the tags, the periods, the vintages, and the keys. A row here is right
when the reader returns exactly it.

**Source:** EDGAR company facts,
`https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json`, Apple Inc.,
CIK 320193. **Pulled 2026-09-11**, HTTP 200, 3.79 MB, 503 `us-gaap` tags and
25,046 facts.

**Apple on purpose.** A fiscal year ending in September, so a label taken from
the calendar is wrong on every row; an ASC 606 revenue retagging inside the
window a five-year screen needs; and a balance sheet whose securities dwarf its
cash, which is what makes PHI-3.1's definition a policy question rather than an
arithmetic one. One filer is one witness, and that is the caveat this Part
carries until a December year end and a bank are added.

**The facts cited here are committed** as `tests/golden/edgar_facts_aapl.csv`,
86 rows, extracted from that artifact: the 70 of section B and the 16
falsifier rows of section D, each with its `accn`, `fy`, `fp`, `form`, `filed`
and `frame` as fetched. The 3.79 MB document is not committed. A reference
that needs a re-fetch to verify is not pinned.

**The workbook's `Filings` sheet** carries the comparison: section E's eight
FY2025 figures with the owner's reading of the 10-K beside EDGAR's and a
verdict per row, the FY2008 pair with both accessions and forms, and the MD&A
cross-check as a formula. It is the shape the `Prices` sheet has for Part 9,
and it was built when section E was filled rather than when this Part was
written, because a sheet with one empty column compares nothing. Sections A to
D transcribe and their artefact is the committed csv; the sheet holds only
what has two sides to compare.

### Decisions

| # | Decision | Choice |
|---|---|---|
| D26 | What identifies a fact? | **`(tag, end, accn)`.** `fy` is the fiscal year of the *filing that reported the fact*, not of the fact, so the same figure recurs under several `fy` values as a comparative and `fy` is provenance, never a key. Measured on this artifact: annual `NetIncomeLoss` keyed on `fy` gives 18 keys of which 18 collide, worst 6; on `end` alone, 18 of 19 collide, because a restatement shares its period; on `(end, accn)`, 60 keys and none collide. Section D, F1 and F3. |
| D27 | Does `fp == "FY"` mean annual? | **No. The period decides, never the label.** A fact is annual when `end - start` is a year; `fp` is inherited from the parent filing, so a 10-K's quarterly comparatives carry `fp: FY`. On this artifact 567 of 6,062 `fp: FY` facts are quarter-length and 523 of those arrive on 10-Ks. A reader that trusts `fp` mixes quarters into an annual series silently. Section D, F2. |
| D28 | How is a balance-sheet figure matched to a fiscal year? | **An instant fact is matched by the fiscal year's end date, and those end dates are derived from the annual duration facts, never assumed.** Instants exist at every quarter end: `StockholdersEquity` carries 2024-03-30, 2024-06-29, 2024-09-28 and 2024-12-28. Matching by calendar year returns a quarter. Apple's year ends, derived: 2021-09-25, 2022-09-24, 2023-09-30, 2024-09-28, 2025-09-27. Section D, F5. |
| D29 | Which vintage of a restated figure? | **The latest filed, and the reference is pinned to a pull date.** D24's "adjusted by nobody" says the system computes no adjustments; it does not say which vintage, and that is underspecified rather than wrong, so this is its companion and D24 is not rewritten. Latest, because a five-year series built from originals mixes pre- and post-restatement figures and stops being a comparison. The cost is that a reference goes stale when a restatement lands — the same problem as prices moving, and the same fix: the pull date above, `filed` and `accn` on every row, and the answer states its as-of. **The form is not a filter.** A restated figure arrives on whatever the filer used: FY2008's amendment is a 10-K/A (0001193125-10-012091, `d10ka.htm`, "Amendment No. 1 to Form 10-K"), and section D's F2 row reaches EDGAR on an **8-K** (0001193125-13-170623, items 8.01 and 9.01). A reader that selects on `form == "10-K"` to find annual figures silently drops both, and the second is not an edge case - it is in the committed fixture. Latest filed means latest filed, whatever carried it. |
| D30 | One metric, one tag? | **No. A field names an ordered list of tags, and a year that resolves from none of them raises.** A tag change truncates history: Apple's annual revenue is `SalesRevenueNet` for FY2007 to FY2017, `Revenues` for FY2016 to FY2018 and `RevenueFromContractWithCustomerExcludingAssessedTax` for FY2017 to FY2025. A reader anchored on `Revenues` alone returns three fiscal years, and PHI-2.1 asks for five. Falling back silently to a shorter series is the repair shape; the raise names the field and the year. Section D, F4. |
| D31 | What is `frame` for? | **A cross-check, never a key.** It is calendar-aligned and exists only when the window lines up: 9,716 of 25,046 facts on this artifact, 38.8%. Where it exists it disagrees with the filer's own labels by design — one fact for 2013-09-29 to 2013-12-28 carries `fy: 2015`, `fp: Q1` and `frame: CY2013Q4`, three labels for one period. |
| D32 | Is a tax rate a figure or an assumption? | **Both, and they are different things in different places.** The block carries `EffectiveIncomeTaxRateContinuingOperations` because it is a filed fact and the block reports what the document says. The tax rate that goes into NOPAT is a **stated assumption in config**, not the block's. The evidence for keeping them apart is in Apple's own series: 0.133, 0.162, 0.147, **0.241**, 0.156. FY2024 is a discrete item, not a change in how Apple earns money; fed into NOPAT it swings PHI-2.1's five-year ROIC series for a reason that is not the business, on the metric written to measure the business. Recorded here so it is not re-litigated. D24 stands: the block's figures are as filed. |
| D33 | How does debt reach the block? | **Every borrowing tag as filed, separately; the sum is a metric.** No arithmetic on the way into the block. `net_debt` therefore lives in `quant/fundamentals.py` with its own reference row, and **what nets against debt is policy and belongs in `docs/PHILOSOPHY.md`** — open, section F. Apple's borrowings are `CommercialPaper`, `LongTermDebtCurrent` and `LongTermDebtNoncurrent`. Not `LongTermDebt`, which is a different measure: it agrees with the sum of the two carrying tags in FY2022, FY2023 and FY2024 and disagrees by 19 and 22 million in FY2021 and FY2025. A borrowing tag the block does not name is a raise, not an omission. |

### A. The fiscal years

As of the pull date, the five most recent fiscal years Apple has filed are
**FY2021 to FY2025** (D21 counts a year by its filed date). FY2026 ends in
September 2026 and is not filed, so it is not a year — exactly the case Part
10 E's third falsifier states in the synthetic.

| Fiscal year | Ends | Days | Notes |
|---|---|---|---|
| FY2021 | 2021-09-25 | 364 | |
| FY2022 | 2022-09-24 | 364 | |
| FY2023 | 2023-09-30 | 371 | a 53-week year |
| FY2024 | 2024-09-28 | 364 | |
| FY2025 | 2025-09-27 | 364 | |

The 53-week year is why D27's duration test is a range and not an equality.

### B. The figures block the reader must return

USD millions except the tax rate, which is a fraction, and every figure taken
at the latest filed vintage per D29. Each row's `tag`, `accn` and `filed` are
in the committed csv; they are not repeated here.

| Field | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|
| revenue | 365,817 | 394,328 | 383,285 | 391,035 | 416,161 |
| gross_profit | 152,836 | 170,782 | 169,148 | 180,683 | 195,201 |
| operating_income | 108,949 | 119,437 | 114,301 | 123,216 | 133,050 |
| effective_tax_rate | 0.133 | 0.162 | 0.147 | 0.241 | 0.156 |
| depreciation_amortisation | 11,284 | 11,104 | 11,519 | 11,445 | 11,698 |
| operating_cash_flow | 104,038 | 122,151 | 110,543 | 118,254 | 111,482 |
| capex | 11,085 | 10,708 | 10,959 | 9,447 | 12,715 |
| equity | 63,090 | 50,672 | 62,146 | 56,950 | 73,733 |
| cash | 34,940 | 23,646 | 29,965 | 29,943 | 35,934 |
| marketable_securities_current | 27,699 | 24,658 | 31,590 | 35,228 | 18,763 |
| marketable_securities_noncurrent | 127,877 | 120,805 | 100,544 | 91,479 | 77,723 |
| commercial_paper | 6,000 | 9,982 | 5,985 | 9,967 | 7,979 |
| long_term_debt_current | 9,613 | 11,128 | 9,822 | 10,912 | 12,350 |
| long_term_debt_noncurrent | 109,106 | 98,959 | 95,281 | 85,750 | 78,328 |

### C. The tag each field resolves from

In order; the first that yields a fact for the period wins, and none yielding
a fact is a raise naming the field and the year (D30).

| Field | Kind | Tags, in order |
|---|---|---|
| revenue | duration | `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet`, `Revenues` |
| gross_profit | duration | `GrossProfit` |
| operating_income | duration | `OperatingIncomeLoss` |
| effective_tax_rate | duration | `EffectiveIncomeTaxRateContinuingOperations` |
| depreciation_amortisation | duration | `DepreciationDepletionAndAmortization`, `DepreciationAmortizationAndAccretionNet` |
| operating_cash_flow | duration | `NetCashProvidedByUsedInOperatingActivities` |
| capex | duration | `PaymentsToAcquirePropertyPlantAndEquipment` |
| equity | instant | `StockholdersEquity` |
| cash | instant | `CashAndCashEquivalentsAtCarryingValue` |
| marketable_securities_current | instant | `MarketableSecuritiesCurrent` |
| marketable_securities_noncurrent | instant | `MarketableSecuritiesNoncurrent` |
| commercial_paper | instant | `CommercialPaper` |
| long_term_debt_current | instant | `LongTermDebtCurrent` |
| long_term_debt_noncurrent | instant | `LongTermDebtNoncurrent` |

The revenue ordering is newest-tag-first on purpose: for FY2017, all three
tags carry the same value and the order decides which `accn` the row cites,
never which number it reports.

### D. Falsifier rows

Each of these fails a reader that takes the obvious shortcut. All sixteen are
in the committed csv with their full provenance.

**F1 — one fact, three `fy` values (D26).** `NetIncomeLoss`, period
2014-09-28 to 2015-09-26, value 53,394 million, in three 10-Ks: `fy` 2015
filed 2015-10-28, `fy` 2016 filed 2016-10-26, `fy` 2017 filed 2017-11-03. A
reader keyed on `fy` stores this fiscal-2015 figure as three different years.

**F2 — a 91-day period carrying `fp: FY` (D27).** `NetIncomeLoss`, period
2010-09-26 to 2010-12-25, value 6,004 million, five times: `fp: Q1` on two
10-Qs, **`fp: FY` on two 10-Ks**, and once on an 8-K carrying
`frame: CY2010Q4`. A reader that selects annual facts by `fp == "FY"` puts a
quarter into the annual series.

**F3 — a restatement (D29).** `NetIncomeLoss` for FY2008, period 2007-09-30
to 2008-09-27: **4,834 million** filed 2009-10-27 on a 10-K, and **6,119
million** filed 2010-01-25 on a 10-K/A and again on the FY2010 10-K. Two
numbers, one fiscal year, both "as filed". Latest filed is 6,119.

**F4 — the same value under three tag names (D30).** FY2017 revenue, period
2016-09-25 to 2017-09-30, **229,234 million** under `SalesRevenueNet` (filed
2017), `Revenues` (filed 2018) and
`RevenueFromContractWithCustomerExcludingAssessedTax` (filed 2019). The value
is stable; the tag is not. A reader anchored on one tag loses the years the
others hold.

**F5 — an instant at the wrong date (D28).** `StockholdersEquity` at
2024-06-29 is **66,708 million**; at 2024-09-28, the FY2024 year end, it is
**56,950 million**. Seventeen percent apart, and both are "2024". A reader
matching by calendar year returns whichever it meets first.

### E. The second source

**Filled 2026-09-12 by the owner, against Apple's FY2025 10-K** (accession
0000320193-25-000079, filed 2025-10-31) and, for the FY2008 row, the original
10-K and its amendment. The figures in section B are EDGAR's rendering of what
Apple filed; a row is trusted when the filer's own document says the same thing
to the dollar.

**The rule, corrected as this section was filled.** A difference on the income
statement is an error. A difference on the balance sheet is a **restatement**
and is recorded rather than reconciled away, because section B takes the latest
filed vintage (D29) and five of the nine rows below reach EDGAR through a later
filing's comparative column rather than through the FY2025 10-K itself. The
original wording of this section said "from Apple's own 10-K" without that
distinction and would have turned a restatement into a failure.

| Field | Fiscal year | Part 12 B | 10-K, by hand | Agrees |
|---|---|---|---|---|
| revenue | FY2025 | 416,161 | 416,161 | yes |
| gross_profit | FY2025 | 195,201 | 195,201 | yes |
| operating_income | FY2025 | 133,050 | 133,050 | yes |
| equity | FY2025 | 73,733 | 73,733 | yes |
| cash | FY2025 | 35,934 | 35,934 | yes |
| long_term_debt_current | FY2025 | 12,350 | 12,350 | yes |
| long_term_debt_noncurrent | FY2025 | 78,328 | 78,328 | yes |
| commercial_paper | FY2025 | 7,979 | 7,979 | yes |
| net income (F3) | FY2008 | 6,119 | 6,119 as amended, 4,834 as reported | yes |

**Eight of eight to the dollar, and the FY2008 pair confirmed both ways.** The
cause of the FY2008 restatement is the retrospective adoption of the amended
revenue-recognition standards for iPhone and Apple TV, announced 2010-01-25.

**Two label mismatches, recorded and not reconciled.** The us-gaap tag names
are not the document's words: the 10-K says **"Gross margin"** where the tag is
`GrossProfit`, and **"Term debt"** where the tags are `LongTermDebtCurrent` and
`LongTermDebtNoncurrent`. The figures agree; the vocabulary does not. This
matters for an answer that quotes a field name back to a reader, and it is the
reason section C exists: the tag is the key, the label is not.

**Three cross-checks that came free**, each an independent way for a wrong
extraction to have failed:

- the FY2024 comparatives on the same balance sheet - 56,950 equity, 29,943
  cash, 10,912 and 85,750 term debt, 9,967 commercial paper - match section B's
  FY2024 column, so the five-year table is not just internally consistent;
- the MD&A states cash plus marketable securities totalled 132.4 billion, and
  35,934 + 18,763 + 77,723 = 132,420, which ties the two securities lines the
  balance sheet reports separately;
- section F's three ratios reproduce from that balance sheet against an implied
  EBITDA near 146,000, so the arithmetic holds without section B.

**What this check is, and is not.** It is a second automated extraction, not a
human reading the filing. It catches a wrong tag, a wrong vintage, a wrong
period and a unit error - the four ways the reader can be wrong that Part 12
was written to catch. It is **not** the independent check Part 9 got, where the
owner fetched rows from the listing exchange by hand. Recorded as such, by the
owner, at the time of filling. The provider method may be written against this;
a figure that reaches an answer about a real holding wants the stronger check
first.

### F. What nets against debt, and why it is A

**What nets against debt is policy** and belongs in `docs/PHILOSOPHY.md` under
PHI-3.1, not in a metrics module. It is settled below; the clause text in
PHILOSOPHY.md still has to say so, which is the owner's to write. Three
readings, all defensible, computed on
Apple from section B (debt = commercial paper plus both long-term debt lines;
EBITDA = operating income + D&A).

A word on what "by hand" means in this Part, since it differs from Part 10's.
Sections A to E are **transcribed**, not computed: the figures are EDGAR's and
the work was reading them out of one artifact correctly, which is why every
cell of section B was checked back against the committed csv. The only
arithmetic in this Part is the table below, and it was done outside the
repository's code and is reproducible from section B with a calculator.

| Definition | What nets | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|---|
| A | cash only | 0.75 | 0.74 | 0.64 | 0.57 | **0.43** |
| B | cash and current marketable securities | 0.52 | 0.55 | 0.39 | 0.31 | **0.30** |
| C | cash and all marketable securities | -0.55 | -0.38 | -0.41 | -0.37 | **-0.23** |

**A correction to the premise this was raised on: for Apple the definition
does not decide PHI-3.1's verdict.** The clause is a ceiling of 2.0x on the
latest fiscal year, and all three readings clear it comfortably. What the
definition changes is the reported distance — 1.57x of headroom under A
against 2.23x under C — and the sign, which is the difference between saying a
company carries net debt and saying it holds net cash. It decides a verdict
only for a company near the limit, which Apple is not.

**Decided 2026-09-12: A, cash only.** I recommended B on convention and the
owner chose A on the clause, which is the better argument and is recorded as
the reason rather than the outcome.

- **A**, taken. The current and non-current split on marketable securities is
  an accounting presentation, not a liquidity fact: Apple's non-current
  holdings are largely liquid paper, and where a filer draws that line moves
  for reasons unrelated to the business. A draws a line that means something.
  It is also conservative in the direction a safety screen should be
  conservative in - it can only reject more candidates, never fewer - and it
  is what Part 10 B already computes, so nothing is recomputed.
- **B**, rejected. It is the conventional reading, which is what I argued
  from, and convention is not a reason when the line it draws is a
  presentation choice. Had it been taken it would have cost a field on the
  block and a recompute of Part 10 D's PHI-3.1 row, Part 10 E's at-the-limit
  falsifier and the workbook's `Philosophy` sheet.
- **C**, rejected. It treats a long-dated securities portfolio as a current
  asset, flatters every cash-rich technology company, and a philosophy clause
  should not lean that way by default.

**The revisit trigger, recorded so this is not reopened on a hypothetical:**
the first candidate that **fails PHI-3.1 on A and would pass on B**. That is a
real case with a real company in it, and it is the only evidence that would
show A drawing the line in the wrong place. Until then A stands.

**What this changes: nothing in the code or the references.** Part 10 B's
`net_debt_to_ebitda = (debt - cash) / (operating income + D&A)` is definition
A already, Part 10 D's PHI-3.1 row and Part 10 E's falsifier stand as
computed, and the workbook's `Philosophy` sheet is untouched. What D33 adds is
that the block carries every borrowing tag separately and the subtraction is
the metric's, so `net_debt` is a function in `quant/fundamentals.py` with its
own reference row rather than arithmetic on the way into the block.

**Also open, and smaller:** whether `net_debt` is one metric key or whether
PHI-3.1's key becomes `net_debt_to_ebitda_excluding_securities` and the like.
D24 says a different formula is a different metric key, which argues for the
definition living in the key's name rather than in a parameter.
