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

### C. A candidate not held — Alphabet, GOOGL

Computed 2026-09-17 by hand, before any code stores a close for a company
outside portfolio 3 (decision 57; Part 11 E). Case 4.2 states the price a
range is measured against, and PHI-4.1 reads it, and every close the
system stored until now belonged to a holding. The source is the same
provider as A and B, asked for the unadjusted close as Part 9 made it
ask; the row defends that call on a ticker nothing has fetched before.

**The second source**, as above: the exchange's historical quotes for
`GOOGL` with `assetclass=stocks`, 10 to 16 September 2026, field
`Close/Last`, five rows. Fetched by me on 2026-09-17 with one command from
the shell. **The provider's figure**: the library the provider wraps,
called from the shell the way the provider calls it,
`history(start, end, auto_adjust=False)` over the same days, storing no
row and passing through no cache. Both as printed are the record.

| Date | Exchange | Provider | Difference | Verdict |
|---|---|---|---|---|
| 2026-09-17 | 347.33 | 347.33 | 0.00 | agrees |
| 2026-09-16 | 342.87 | 342.87 | 0.00 | agrees |
| 2026-09-15 | 344.98 | 344.98 | 0.00 | agrees |
| 2026-09-14 | 349.39 | 349.39 | 0.00 | agrees |
| 2026-09-11 | 338.50 | 338.50 | 0.00 | agrees |
| 2026-09-10 | 332.60 | 332.60 | 0.00 | agrees |

Five of five. The exchange prints volume to the share and the library to
the hundred (18,928,860 against 18,928,900 on the 16th); the close is the
figure a valuation reads and the only one this row checks.

*Added 2026-09-18.* The 17th's row, six of six. Asked at about 22:30 UTC
on the 17th the exchange's table stopped at the 16th; asked again at about
02:00 UTC on the 18th it carried the 17th, 347.33. The provider's figure on
this row is the close the node stored on the first live run of case 4.2,
through the price provider, not a call from the shell: the row that was
stated as the last close before the table could be asked, now checked.

**What C settles.** The first close the system stores for GOOGL, the last
close before 2026-09-17, is defended when it equals 342.87 on 2026-09-16
with its source on the row; the 17th's, 347.33, since the row above. The
ticker is the one the question names, not the CIK's other classes: GOOG's
print is a different figure and would need its own row (Part 13 E item 7,
second half).

**What C does not cover.** A refetch after Alphabet's next ex-dividend
date: B is the falsifier for that and the provider's call has not changed
since. A candidate in another currency: the watchlist's two are USD.

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

*The block's shape, 2026-09-15, decisions 46 and 47.* The table keeps its
columns and every figure below stands; two of the columns are no longer
figures of the block. **Tax rate** is not a per-year figure but the rate the
philosophy states on PHI-2.1, 0.20, one number for every year; the block
carries no `tax_rate`, and a reader's block carries `effective_tax_rate`
beside it, unread (D32, Part 12 G). **Debt** is the sum of the block's three
borrowing fields: in the synthetic block `long_term_debt_noncurrent` carries
the figure shown and `commercial_paper` and `long_term_debt_current` are 0,
filed zeros, not blanks (D33, Part 12 G); section E's at-the-limit row puts
its 120,000 in the same field. Sections C, D and E are unchanged by this
and the workbook's `Philosophy` sheet keeps its two columns, since the
arithmetic they feed is the same.

*The block's shape, 2026-09-16, decision 48 items 3 and 4.* A third column
is no longer a figure of the block. **Gross profit** is not a field: the
block carries `cost_of_revenue`, and gross margin is revenue less cost of
revenue, over revenue (section B, Part 12 H). In the synthetic block
`cost_of_revenue` is revenue less the gross profit shown, 45,000, 48,160
and 52,500 for FY2023 to FY2025, blank before, so section C's margins are
what they were: 55,000 / 100,000, 63,840 / 112,000 and 72,500 / 125,000
are the same three ratios. Section E's missing-figure row now removes
FY2024's cost of revenue and stops on the same clause naming the same
metric and year.

Shares outstanding 4,000 million. Price 171.00 as of 2026-09-10. Valuation
range 180.00 to 240.00 per share as of 2026-09-10, typed here; Part 11 will
compute one from stated assumptions.

*The block's shape, 2026-09-17, decision 48 item 7 (Part 11 D39).* The
share count is a figure of the fiscal year, not of the block:
`shares_outstanding` sits in FY2025's figures, the 4,000 million above, the
way the reader carries the filer's year-end count (Part 12 B's note), and
the yield divides the year's free cash flow by the price times the year's
own count. FY2021 to FY2024 carry no count in this synthetic block and
their yield is absent, as it already was for want of their cash flows. The
price and the range stay on the block with their as-of dates. Nothing in
sections C, D or E moves. Part 11's range is computed by hand on filed
figures and this typed range stands as the screen's input until a pipeline
publishes one.

### B. The metric formulas (D24)

- **return_on_invested_capital** = operating income x (1 - tax rate) /
  (equity + debt - cash), per fiscal year, on that year's figures.
- **gross_margin** = (revenue - cost of revenue) / revenue. Until
  2026-09-16 this line read gross profit / revenue; the measure is the same
  and the inputs moved with decision 48 (Part 12 H holds the identity on
  Apple's filed figures, five years to the dollar; Part 13 B the figures
  for a filer that presents no gross profit).
- **net_debt_to_ebitda** = (debt - cash) / (operating income + D&A).
- **free_cash_flow_yield** = (operating cash flow - capex) / (price x shares
  outstanding), the latest fiscal year's cash flows at the as-of price.
  Since 2026-09-17 the count is the year's own, a figure of the block's
  years like the cash flows (decision 48 item 7, Part 11 D39), and the
  price stays on the block with its as-of date: the same measure, the
  divisor's home moved.

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

**Statements, cited and not computed:** PHI-1.1, PHI-1.2, PHI-2.3, PHI-4.3,
PHI-5.1, PHI-5.2, PHI-6.1, PHI-6.2, PHI-6.3, PHI-7.1, PHI-7.2. A full check
lists them, so the philosophy is visibly all of it. PHI-3.2 was a statement
when this section was computed; from 2026-09-14 it is `excluded_industry`
(section F), the five findings above are unchanged, and a block carrying a
SIC code adds a sixth.

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
cost of revenue absent (gross profit, until 2026-09-16; decision 48). The
check stops on PHI-2.2 naming `gross_margin` for `FY2024` and reports no
finding on any clause. Not a pass on PHI-2.1, not a
verdict on the company, not a finding on PHI-2.2 over the two years it has.

**A year not yet reported is not a year (D21).** The same block asked for
as of 2025-06-30, before FY2025 was filed: PHI-2.1 reads FY2020 to FY2024
and the block has no FY2020, so the check stops naming
`return_on_invested_capital` for `FY2020`. It does not read FY2021 to
FY2025 and it does not read four years.

### F. PHI-3.2, the industry exclusion

Added 2026-09-14, before the clause type or its screen exists. PHI-3.2
becomes `excluded_industry`: a company whose SIC code is one of the clause's
codes is not screened by the philosophy. Nothing here is arithmetic, so the
workbook's `Philosophy` sheet does not change.

| # | Decision | Choice |
|---|---|---|
| D34 | When is an industry exclusion decided? | **Before any figure is read.** D25 stops the whole check at the first missing figure, and a bank's filed figures lack most of what the other clauses read (Part 13 C), so a check that reads figures first refuses a bank under PHI-1.2: a true refusal citing the wrong clause. |
| D35 | What decides it, and what does the check report? | **The SIC code as EDGAR states it**, on the block, as of its pull date: EDGAR carries the current code only (Part 13 C). A listed code gives one finding, status **excluded**, carrying the code, and the check reports nothing else about the company. An unlisted code gives one finding, status **pass**, carrying the code, in philosophy order, and the check goes on. A block with no code stops the check naming PHI-3.2: a company is never assumed not to be a bank. |

**The codes**, each with the filers it was measured on in Part 13 C, decided
2026-09-14:

| SIC | Kind | Measured on | Listed |
|---|---|---|---|
| 6021 | national commercial banks | JPMorgan, Zions | yes |
| 6022 | state commercial banks | Fifth Third, M&T | yes |
| 6035 | savings institutions, federally chartered | Capitol Federal, TFS | yes |
| 6036 | savings institutions, not federally chartered | Flagstar | yes |
| 6211 | security brokers and dealers | Goldman Sachs | yes |
| 6311 | life insurers | MetLife, Prudential | yes |
| 6331 | fire, marine and casualty insurers | Travelers | yes |
| 6411 | insurance agents and brokers | Marsh & McLennan, Gallagher | **no** |

Broker-dealers count: their balance sheet is their business the way a
bank's is. Insurance brokers do not: they sell insurance and do not carry
it, so the clause's reason does not reach them. A bank or an insurer filing
under a code this list does not carry is screened as if it were neither;
that is the list's known limit, closed one measured code at a time, never by
a code range recited from memory.

**Rows**, as of 2026-09-10 like the rest of this Part:

**A bank is excluded before its figures are read (D34).** JPMorgan, SIC
6021, with a block carrying only the five fields Part 13 C resolves for it:
one finding, PHI-3.2 **excluded**, code 6021. No finding on any other clause,
and no stop, although gross profit, operating income, cash and debt are not
in its figures. A check that reads figures first fails this row by stopping
on PHI-2.1.

**A broker-dealer is excluded.** Goldman Sachs, SIC 6211, the same way: one
finding, PHI-3.2 **excluded**, code 6211.

**An insurance broker is not.** Section A's block with SIC 6411: section D's
five findings, and PHI-3.2 **pass** carrying 6411 between PHI-3.1 and
PHI-4.1.

**Alphabet passes and the rest stands.** Section A's block with SIC 7370,
Alphabet's code in Part 13 C: six findings in philosophy order, PHI-2.1,
PHI-2.2 and PHI-3.1 as in section D, PHI-3.2 **pass** carrying 7370, then
PHI-4.1 and PHI-4.2 as in section D; eleven statements.

**No code, no check.** Section A's block with no SIC code: the check stops
naming PHI-3.2 and reports no finding.

### Expected answers, in the Part 3b shape

- **4.1 (does X clear my philosophy)** - the five findings above with their
  deciding years and distances, and section F's PHI-3.2 finding with the
  company's SIC code, each citing its clause; the eleven statements named as
  not computed; every figure with its fiscal year and its source; no
  recommendation.
- **4.6 (a missing figure)** - "the check stopped: FY2024 gross margin is
  not in the figures", no finding on any clause, nothing invented.
- **4.6 (a bank)** - "JPMorgan is excluded under PHI-3.2: SIC 6021, National
  Commercial Banks, as EDGAR stated it on 2026-09-13"; no other finding, no
  figure read, no verdict on the company.

*Note, 2026-09-16, decision 29.* The first live answer, through the node on
JPM: "JPM is excluded under PHI-3.2: SIC 6021, National Commercial Banks,
as EDGAR stated it on 2026-09-16 UTC", the clause text, "no figure was read
and no other clause was checked". The runner's 4.6 passes on it. The date
is the pull day, UTC, as decided with the node; the row above cites the
pull day of Part 13 C's own fetch.

---

## Part 11 — The valuation range

Computed 2026-09-17 by hand, before any pipeline exists (DIRECTION.md Order
4, invariant 6; PHI-4.1 and PHI-4.3; benchmark case 4.2), so the pipeline
has something independent to be wrong against. Decisions D37 to D40. Plain
decimal arithmetic at 28 significant digits, none of the repository's code.
The filed inputs are read from the stored facts of the pulls of 2026-09-15
(Apple) and 2026-09-16 (Alphabet) at the latest vintage (D29); every figure
below is the same on every vintage that carries it. USD millions except the
share count, in millions of shares, and the value per share, in dollars to
the cent from the unrounded quotient. Part 12 was written before this Part
because the reader comes before the valuation it feeds.

**The assumptions are synthetic**, stand-ins in the synthetic philosophy
and watchlist the way PHI-2.1's 20% is, so that the arithmetic has a
reference before my own numbers exist. A range is computed for two filers,
Alphabet, W-1 on the watchlist with a December year end, and Apple, held in
portfolio 3 with a September year end, both because their blocks carry
every input in the latest year. The Apple range is a witness for the
arithmetic on a second year end and says nothing about the holding; nothing
in the philosophy reads it.

### Decisions

| # | Decision | Choice |
|---|---|---|
| D37 | What is the range? | **A discounted cash flow over the latest fiscal year's free cash flow, run twice, once at each of two stated growth rates; the low end is the low rate and the high end the high rate.** Free cash flow FCF0 is operating cash flow less capex of the year. For t = 1 to N, FCF_t = FCF0 x (1 + g)^t, discounted at (1 + r)^t and summed; the terminal value at year N is FCF_N x (1 + gT) / (r - gT), discounted at (1 + r)^N; enterprise value is the sum; equity is enterprise value less net debt; the value per share is equity over the share count. There is no midpoint and no spread: the two ends are two runs of one formula on two stated assumptions, which is what PHI-4.3's "a range from stated assumptions" means here. Rejected: a multiple of free cash flow, since a multiple is what the market pays and stating one is a price forecast under an assumption's name; a one-stage perpetuity, in which one difference, r less g, sets the whole value and a decade's growth cannot be stated apart from forever's; a pair of discount rates beside the pair of growth rates, four ends for a two-ended range; a point with a spread, which is the shape PHI-4.3 refuses. |
| D38 | Whose assumptions, and where do they live? | **Five, all mine, each stated in a document and carried to the record with the id of the clause or entry that states it.** The investor's three on PHI-4.1 in `philosophy.toml`, the clause that reads the range, the way D46 put `tax_rate` on PHI-2.1, the clause that names the metric: `required_return` r, `terminal_growth` gT, `horizon_years` N, all three stated or none. *Corrected 2026-09-17, the day this Part was written: the shape said PHI-4.3, and the loader refuses a parameter on a statement because a number on a statement is a limit nobody checks; PHI-4.3 stays a statement.* The business's two on the watchlist entry in `watchlist.toml`: `growth_low` and `growth_high`. An assumption reaches the range record as its name, its value and its source id, and that citation is what case 4.2 means by an assumption marked as mine; a proposal by a model (case 4.3) would carry a different source, and no vocabulary for it is added before the case asks. A clause or entry that states none of them, or a growth pair without both ends, does not load. Rejected: `config.toml`, whose values are the same for anyone and would keep a personal philosophy from carrying its own rate; a constant in the module; the model proposing a rate, a number in a model's hands. |
| D39 | Which year, which figures? | **The latest fiscal year filed by the as-of date (D21), the year PHI-4.2 reads, for every filed input at once.** FCF0 is that year's `operating_cash_flow` less `capex`; net debt is `quant/fundamentals.net_debt` on that year, borrowings less cash under Part 12 F's definition A (D33), so the range and PHI-3.1 share one arithmetic path and marketable securities net against nothing; the share count is that year's, `shares_outstanding` at the year end as Part 13 E item 7's first half shapes it, pending decision 48. Rejected: free cash flow computed on the way into the block, D33's refused shape; an average of several years' cash flow, a figure nobody filed; the latest quarterly count against a fiscal year's cash flow, two dates in one ratio. |
| D40 | What does the record carry, and what raises? | **Low, high, as-of, the year read with its end and filed dates, the source, the five assumptions with their sources, and no filed figure**, the rule the screening block already keeps: the year, its filed date and the source trace the inputs, and the figures stay in the database. The pipeline raises, naming which, when `growth_low` is not below `growth_high` (equal ends are a point, PHI-4.3), when r is not above gT (the terminal value is undefined or negative), when FCF0 is not positive (this method values a business that generates cash and does not say what one that burns it is worth), when equity at the low end is not positive (a value PHI-4.1's division cannot read), when the share count is missing for the year, or when an assumption is not stated. Nothing is sorted, clamped, defaulted or filled. Rejected: carrying FCF0 and net debt on the record for traceability, a filed figure in shared_data; sorting two ends that came out reversed, which hides that the stated assumptions contradict each other. |

### A. The stated assumptions

| Name | Symbol | Value | Stated on |
|---|---|---|---|
| required_return | r | 0.09 | PHI-4.1 (corrected 2026-09-17 from PHI-4.3, D38) |
| terminal_growth | gT | 0.03 | PHI-4.1 |
| horizon_years | N | 10 | PHI-4.1 |
| growth_low | g_low | 0.06 | W-1 (and, for the witness, the same pair on Apple) |
| growth_high | g_high | 0.12 | W-1 |

The powers the tables below use, exact: (1.06)^10 = 1.79084769654285362176,
(1.12)^10 = 3.10584820834420916224, (1.09)^10 = 2.36736367459211723401.

### B. The filed inputs

Alphabet FY2025 ends 2025-12-31, own report 0001652044-26-000018 filed
2026-02-05. Apple FY2025 ends 2025-09-27, own report 0000320193-25-000079
filed 2025-10-31. The duration figures are on each year's own report; the
instants recur on the following 10-Qs at the same value, and the latest
vintage is that 10-Q (Alphabet 0001652044-26-000071, filed 2026-07-23;
Apple 0000320193-26-000020, filed 2026-07-31). The share count is
`CommonStockSharesOutstanding`, whole shares as filed, 12,088,000,000 and
14,773,260,000, shown in millions.

| Input | Field or formula | Alphabet FY2025 | Apple FY2025 |
|---|---|---|---|
| operating cash flow | `operating_cash_flow` | 164,713 | 111,482 |
| capex | `capex` | 91,447 | 12,715 |
| **FCF0** | operating cash flow - capex | **73,266** | **98,767** |
| commercial paper | `commercial_paper` | 0 | 7,979 |
| long-term debt, current | `long_term_debt_current` | 1,996 | 12,350 |
| long-term debt, non-current | `long_term_debt_noncurrent` | 46,547 | 78,328 |
| borrowings | the three added (D33) | 48,543 | 98,657 |
| cash | `cash` | 30,708 | 35,934 |
| **net debt** | borrowings - cash | **17,835** | **62,723** |
| shares (millions) | `shares_outstanding` | 12,088 | 14,773.26 |

Apple's net debt reproduces Part 12 G's FY2025 row, 62,723, from the same
figures.

### C. The range, step by step

Each table is one run of D37's formula. FCF_t and PV_t to a tenth of a
million; (1 + r)^t exact.

**Alphabet, low end, g = 0.06**

| t | FCF_t | (1.09)^t | PV_t |
|---|---|---|---|
| 1 | 77,662.0 | 1.09 | 71,249.5 |
| 2 | 82,321.7 | 1.1881 | 69,288.5 |
| 3 | 87,261.0 | 1.295029 | 67,381.5 |
| 4 | 92,496.6 | 1.41158161 | 65,526.9 |
| 5 | 98,046.4 | 1.5386239549 | 63,723.5 |
| 6 | 103,929.2 | 1.677100110841 | 61,969.6 |
| 7 | 110,165.0 | 1.82803912081669 | 60,264.0 |
| 8 | 116,774.9 | 1.9925626416901921 | 58,605.4 |
| 9 | 123,781.4 | 2.171893279442309389 | 56,992.4 |
| 10 | 131,208.2 | 2.36736367459211723401 | 55,423.8 |

Sum of PV_t 630,425.0. Terminal value 131,208.2 x 1.03 / 0.06 =
2,252,408.2, discounted 951,441.6. Enterprise value 1,581,866.6; equity
1,581,866.6 - 17,835 = 1,564,031.6; per share 1,564,031.6 / 12,088 =
**129.39** (129.3871305225...).

**Alphabet, high end, g = 0.12**

| t | FCF_t | (1.09)^t | PV_t |
|---|---|---|---|
| 1 | 82,057.9 | 1.09 | 75,282.5 |
| 2 | 91,904.9 | 1.1881 | 77,354.5 |
| 3 | 102,933.5 | 1.295029 | 79,483.5 |
| 4 | 115,285.5 | 1.41158161 | 81,671.1 |
| 5 | 129,119.7 | 1.5386239549 | 83,919.0 |
| 6 | 144,614.1 | 1.677100110841 | 86,228.7 |
| 7 | 161,967.8 | 1.82803912081669 | 88,601.9 |
| 8 | 181,403.9 | 1.9925626416901921 | 91,040.5 |
| 9 | 203,172.4 | 2.171893279442309389 | 93,546.2 |
| 10 | 227,553.1 | 2.36736367459211723401 | 96,120.9 |

Sum of PV_t 853,248.8. Terminal value 227,553.1 x 1.03 / 0.06 =
3,906,327.8, discounted 1,650,075.1. Enterprise value 2,503,323.8; equity
2,485,488.8; per share **205.62** (205.6162184284...).

**Apple, low end, g = 0.06**

| t | FCF_t | (1.09)^t | PV_t |
|---|---|---|---|
| 1 | 104,693.0 | 1.09 | 96,048.6 |
| 2 | 110,974.6 | 1.1881 | 93,405.1 |
| 3 | 117,633.1 | 1.295029 | 90,834.3 |
| 4 | 124,691.1 | 1.41158161 | 88,334.3 |
| 5 | 132,172.5 | 1.5386239549 | 85,903.1 |
| 6 | 140,102.9 | 1.677100110841 | 83,538.8 |
| 7 | 148,509.0 | 1.82803912081669 | 81,239.5 |
| 8 | 157,419.6 | 1.9925626416901921 | 79,003.6 |
| 9 | 166,864.8 | 2.171893279442309389 | 76,829.2 |
| 10 | 176,876.7 | 2.36736367459211723401 | 74,714.6 |

Sum of PV_t 849,851.1. Terminal value 176,876.7 x 1.03 / 0.06 =
3,036,382.6, discounted 1,282,600.8. Enterprise value 2,132,451.9; equity
2,132,451.9 - 62,723 = 2,069,728.9; per share 2,069,728.9 / 14,773.26 =
**140.10** (140.0996741701...).

**Apple, high end, g = 0.12**

| t | FCF_t | (1.09)^t | PV_t |
|---|---|---|---|
| 1 | 110,619.0 | 1.09 | 101,485.4 |
| 2 | 123,893.3 | 1.1881 | 104,278.5 |
| 3 | 138,760.5 | 1.295029 | 107,148.6 |
| 4 | 155,411.8 | 1.41158161 | 110,097.6 |
| 5 | 174,061.2 | 1.5386239549 | 113,127.8 |
| 6 | 194,948.5 | 1.677100110841 | 116,241.4 |
| 7 | 218,342.4 | 1.82803912081669 | 119,440.8 |
| 8 | 244,543.5 | 1.9925626416901921 | 122,728.1 |
| 9 | 273,888.7 | 2.171893279442309389 | 126,106.0 |
| 10 | 306,755.3 | 2.36736367459211723401 | 129,576.8 |

Sum of PV_t 1,150,231.0. Terminal value 306,755.3 x 1.03 / 0.06 =
5,265,966.2, discounted 2,224,401.0. Enterprise value 3,374,632.0; equity
3,311,909.0; per share **224.18** (224.1826772441...).

**The ranges.** Alphabet FY2025: **129.39 to 205.62** per share. Apple
FY2025: **140.10 to 224.18** per share. Each is two runs of one formula on
the stand-in assumptions and says nothing about either company; the
terminal value is three fifths of enterprise value at the low ends and two
thirds at the high ends, which is what a ten-year horizon at these rates
gives and is not a finding.

### D. Falsifier rows

**A one-year horizon with no terminal growth collapses to one line (D37).**
With N = 1 and gT = 0 the formula is FCF0 x (1 + g) / (1 + r) + FCF0 x
(1 + g) / r / (1 + r), which is FCF0 x (1 + g) / r exactly. Enterprise
value: Alphabet 862,910.67 at g = 0.06 and 911,754.67 at g = 0.12; Apple
1,163,255.78 and 1,229,100.44. A pipeline that discounts the terminal value
one year too many or too few, or grows FCF_N once more before the terminal
step, fails all four: by a factor of 1.09 for the discounting, of 1.06 or
1.12 for the growth.

**Swapped rates raise (D40).** `growth_low` 0.12 and `growth_high` 0.06
raises naming both; a pipeline that sorts the ends prints 129.39 to 205.62
and hides that the stated assumptions contradict each other. Equal rates,
0.06 and 0.06, raise too: two ends that are one number are a point.

**A required return at or below the terminal growth raises (D40).** r =
0.03 with gT = 0.03 divides by zero in the terminal value; r = 0.02 makes
it negative. Both raise naming r and gT; neither prints a value.

**A non-positive free cash flow raises (D40).** The same Alphabet year with
capex 164,713 has FCF0 0 and raises naming FCF0 and the year; capex
170,000 gives -5,287 and raises the same way. Nothing is discounted from a
negative base.

**A non-positive low end raises (D40).** The same Alphabet year with net
debt of 1,581,866.6 or more has equity at the low end of 0 or less and
raises; the high end, 2,503,323.8 less the same net debt, is positive and
is not printed alone.

**A missing count raises (D40, D39).** The Alphabet year without
`shares_outstanding` raises naming the field and FY2025; nothing divides by
a count from another date.

**The as-of date moves the year (D39, D21).** As of 2026-01-31 Alphabet's
latest filed year is FY2024, and the range is FY2024's inputs, 125,299 -
52,535 = 72,764 of free cash flow, its own net debt and its own count, not
FY2025's. No row is computed here for it; the rule is D21's and the
metrics already keep it.

### E. What Part 11 does not cover

- **The price and PHI-4.1's discount.** The range needs no price; the
  margin of safety and case 4.2's "price and its as-of date stated" do,
  and a price source for a candidate not held in portfolio 3 is undecided
  and unnumbered. Part 10 D's synthetic row stands for the discount's
  arithmetic until a stored close for a candidate has its own Part 9 row.
- **A second method.** One formula; a different formula is a different
  range and gets its own decision and its own rows.
- **A model's proposal.** Every assumption here is mine by document. What
  a proposed assumption is, how it is marked and how it reaches the record
  is case 4.3's.
- **More than one share class.** One count against one value, the known
  limit Part 13 B records; Alphabet's count is the filer's own and covers
  every class.
- **The workbook.** No sheet, like Part 12 G and H.

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
carries until a December year end and a bank are added. Part 13 adds both,
Alphabet and JPMorgan, and holds each of D26 to D33 against them; the
decisions revised on what they showed say so in their rows.

**The facts cited here are committed** as `tests/golden/edgar_facts_aapl.csv`,
93 rows, extracted from that artifact: the 70 of section B and the 16 falsifier
rows of section D, each with its `accn`, `fy`, `fp`, `form`, `filed` and
`frame` as fetched, and the five of section A's own annual reports and Part
13's two F11 rows, from the second pull. Section B's rows carry `A` in the
csv's `section` column, a mislabel from when the file was written. The 3.79 MB
document is not committed. A reference that needs a re-fetch to verify is not
pinned.

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
| D26 | What identifies a fact? | **`(tag, start, end, accn)`, with `start` empty for an instant.** Taken as `(tag, end, accn)` on 2026-09-11; `start` added 2026-09-13 on Part 13's F6, because a 10-Q carries a quarter and a year to date under one tag, end and accession, and over every duration fact `(tag, end, accn)` collides on 2,048 keys on Alphabet and 6,098 on JPMorgan, with `start` on none. The measurements below were taken on annual facts, where the difference cannot show. `fy` is the fiscal year of the *filing that reported the fact*, not of the fact, so the same figure recurs under several `fy` values as a comparative and `fy` is provenance, never a key. Measured on this artifact: annual `NetIncomeLoss` keyed on `fy` gives 18 keys of which 18 collide, worst 6; on `end` alone, 18 of 19 collide, because a restatement shares its period; on `(end, accn)`, 60 keys and none collide. Section D, F1 and F3; Part 13, F6. |
| D27 | Does `fp == "FY"` mean annual? | **No. The period decides, never the label.** A fact is annual when `end - start` is a year; `fp` is inherited from the parent filing, so a 10-K's quarterly comparatives carry `fp: FY`. On this artifact 567 of 6,062 `fp: FY` facts are quarter-length and 523 of those arrive on 10-Ks. A reader that trusts `fp` mixes quarters into an annual series silently. Section D, F2. **A year is 350 to 380 days, `end` minus `start`, both bounds included**, added 2026-09-13. Measured that way, Apple's annual periods are 363 and 370 days (Part 12 A counts both ends, 364 and 371), Alphabet's and JPMorgan's 364 and 365; on the last two the nearest durations that are not a year are 273 days, nine months, and on Alphabet 925, a figure over several years. Any bound inside that gap keeps the same facts, so the window is stated here and not configured. |
| D28 | How is a balance-sheet figure matched to a fiscal year? | **An instant fact is matched by the fiscal year's end date, and those end dates are derived from the annual duration facts, never assumed.** Instants exist at every quarter end: `StockholdersEquity` carries 2024-03-30, 2024-06-29, 2024-09-28 and 2024-12-28. Matching by calendar year returns a quarter. Apple's year ends, derived: 2021-09-25, 2022-09-24, 2023-09-30, 2024-09-28, 2025-09-27. Section D, F5. |
| D29 | Which vintage of a restated figure? | **The latest filed, and the reference is pinned to a pull date.** D24's "adjusted by nobody" says the system computes no adjustments; it does not say which vintage, and that is underspecified rather than wrong, so this is its companion and D24 is not rewritten. Latest, because a five-year series built from originals mixes pre- and post-restatement figures and stops being a comparison. The cost is that a reference goes stale when a restatement lands — the same problem as prices moving, and the same fix: the pull date above, `filed` and `accn` on every row, and the answer states its as-of. **The periodic form is not a filter.** A restated figure arrives on whatever the filer used: FY2008's amendment is a 10-K/A (0001193125-10-012091, `d10ka.htm`, "Amendment No. 1 to Form 10-K"), and section D's F2 row reaches EDGAR on an **8-K** (0001193125-13-170623, items 8.01 and 9.01). A reader that selects on `form == "10-K"` to find annual figures silently drops both, and the second is not an edge case - it is in the committed fixture. **Which filings carry a figure**, added 2026-09-13 on Part 13's F10: a 10-K, 10-Q or 8-K, or an amendment of one of them (10-K/A, 10-Q/A, 8-K/A). A fact on any other form is not a vintage of the figure and is ignored, because a proxy statement quotes the statements rather than filing them: JPMorgan's 2026 proxy repeats five years of net income rounded to the hundred million and is the latest filing of every one of them. Latest filed means latest filed among those forms. Rejected: excluding the proxy by name, which admits the next unlisted form unseen; taking the later filing only where it differs, which Alphabet's proxy, equal to the dollar, and JPMorgan's, rounded, answer differently; 10-K only, which drops F3's amendment and F2's 8-K. |
| D30 | One metric, one tag? | **No. A field names an ordered list of tags, and a year that resolves from none of them has no figure for that field, named as such.** A tag change truncates history: Apple's annual revenue is `SalesRevenueNet` for FY2007 to FY2017, `Revenues` for FY2016 to FY2018 and `RevenueFromContractWithCustomerExcludingAssessedTax` for FY2017 to FY2025. A reader anchored on `Revenues` alone returns three fiscal years, and PHI-2.1 asks for five. Falling back silently to a shorter series is the repair shape; the raise names the field and the year. Section D, F4. **Where the raise happens**, revised 2026-09-13: not in the reader. The figures block leaves the field out of that year and lists it as unresolved, with the tags tried, and the check stops where a clause needs it (D25, PHI-1.2), naming the field, the year and the tags. A raise in the reader leaves no block at all for a filer missing a field no failing clause reads: Alphabet files no gross profit (Part 13 B), and every other figure PHI-2.1 needs would never reach the screen. Nothing is filled either way; the cells Part 13 B and C mark **raises** are these. |
| D31 | What is `frame` for? | **A cross-check, never a key.** It is calendar-aligned and exists only when the window lines up: 9,716 of 25,046 facts on this artifact, 38.8%. Where it exists it disagrees with the filer's own labels by design — one fact for 2013-09-29 to 2013-12-28 carries `fy: 2015`, `fp: Q1` and `frame: CY2013Q4`, three labels for one period. |
| D32 | Is a tax rate a figure or an assumption? | **Both, and they are different things in different places.** The block carries `EffectiveIncomeTaxRateContinuingOperations` because it is a filed fact and the block reports what the document says. The tax rate that goes into NOPAT is a **stated assumption in config**, not the block's. The evidence for keeping them apart is in Apple's own series: 0.133, 0.162, 0.147, **0.241**, 0.156. FY2024 is a discrete item, not a change in how Apple earns money; fed into NOPAT it swings PHI-2.1's five-year ROIC series for a reason that is not the business, on the metric written to measure the business. Recorded here so it is not re-litigated. D24 stands: the block's figures are as filed. **Decided 2026-09-15 (decision 46):** the stated rate is a parameter of the clause that names the metric, `tax_rate` on PHI-2.1 in `philosophy.toml`, with the sentence that states it in `docs/PHILOSOPHY.md`, mine to write; the metrics take the stated assumptions as an input beside the block, and a clause naming `return_on_invested_capital` without a rate does not load. The synthetic philosophy states 0.20, the rate Part 10 was computed at, so no Part 10 figure moves. Rejected: `config.toml`, which holds values the same for anyone and would keep a personal philosophy from carrying its own rate; a document-level table outside every clause and outside PHI-7.1; a constant in the metrics module. Section G carries the row. |
| D33 | How does debt reach the block? | **Every borrowing tag as filed, separately; the sum is a metric.** No arithmetic on the way into the block. `net_debt` therefore lives in `quant/fundamentals.py` with its own reference row, and **what nets against debt is policy and belongs in `docs/PHILOSOPHY.md`** — open, section F. Apple's borrowings are `CommercialPaper`, `LongTermDebtCurrent` and `LongTermDebtNoncurrent`. Not `LongTermDebt`, which is a different measure: it agrees with the sum of the two carrying tags in FY2022, FY2023 and FY2024 and disagrees by 19 and 22 million in FY2021 and FY2025. A borrowing tag the block does not name is a raise, not an omission. **Decided 2026-09-15 (decision 47):** `net_debt` is a named function in `quant/fundamentals.py` with its own reference row, section G, and not a key a clause may name; a borrowing is one of the three named fields and a finance lease is not one (Part 13 E5); the last sentence is a known limit, not a rule the code can keep: nothing raises on a tag it does not know, and the list grows one measured tag at a time, the way PHI-3.2's codes do. The revisit trigger for leases is the first candidate whose PHI-3.1 verdict moves when finance leases are counted. |
| D36 | When does a tag belong in a field's list? | **On a witness, and one witnessed tag at a time.** Decided 2026-09-16 (decision 48, item 3). A tag joins a field's list when a filer files it and a tag already in the list for the same period on the same filing at the same value: Apple's three revenue tags for FY2017 (F4), Alphabet's two for FY2021, FY2023 and FY2024 (Part 13 B). A filer that files both at different values has shown two measures, and the tag stays out even where it is the only tag some filer uses; that year raises: `LongTermDebtAndCapitalLeaseObligations` against `LongTermDebtNoncurrent`, 13,253 against 11,870 at 2023-12-31 on one filing (F7), and `Depreciation` against `DepreciationDepletionAndAmortization`, 9,500 against 11,284 for Apple's FY2021 and apart in every year (F8). A tag no filer has filed beside a listed one has no witness and stays out. One exception, recorded as one: `cost_of_revenue` lists `CostOfRevenue` and `CostOfGoodsAndServicesSold`, which no filer here files together; the field is witnessed by an identity over fields on the block, revenue less Apple's cost of sales equal to Apple's filed gross profit in five years (section H), and Alphabet's tag joins as the taxonomy's element for the same line with no witness of its own. The rule has no automated check; `tests/test_filed_fields.py` holds the list to section C and review holds section C to this row. What it decides for Alphabet: FY2021 and FY2022 have no non-current debt and PHI-2.1 stops at FY2021 until the FY2027 report is filed and the five-year window is FY2023 to FY2027, every year under the narrow tag. Rejected: the wider debt tag in the list, which errs in the safe direction and joins two measures in one series with no raise; splitting it by `FinanceLeaseLiability` less its current part, arithmetic on the way in for two years only. |

### A. The fiscal years

As of the pull date, the five most recent fiscal years Apple has filed are
**FY2021 to FY2025** (D21 counts a year by its filed date). FY2026 ends in
September 2026 and is not filed, so it is not a year — exactly the case Part
10 E's third falsifier states in the synthetic.

| Fiscal year | Ends | Days | Own annual report | Filed | Notes |
|---|---|---|---|---|---|
| FY2021 | 2021-09-25 | 364 | 0000320193-21-000105 | 2021-10-29 | |
| FY2022 | 2022-09-24 | 364 | 0000320193-22-000108 | 2022-10-28 | |
| FY2023 | 2023-09-30 | 371 | 0000320193-23-000106 | 2023-11-03 | a 53-week year |
| FY2024 | 2024-09-28 | 364 | 0000320193-24-000123 | 2024-11-01 | |
| FY2025 | 2025-09-27 | 364 | 0000320193-25-000079 | 2025-10-31 | |

The 53-week year is why D27's duration test is a range and not an equality.

**Each year's own annual report**, added 2026-09-13 for D21. A year counts from
the day its own report was filed, not from the `filed` date on the vintage
section B cites: FY2021's revenue row cites the FY2023 10-K, filed 2023-11-03,
and a year dated by that would not have been a year until two years after it
was reported. A filing's own year is the latest year end it carries an annual
figure for; a year's own report is the earliest-filed 10-K or 10-K/A whose own
year it is; the label is `FY` and that report's `fy`, and every one of the five
matches the year it reports. A year no filing reports as its own is left out,
not dated from a later report: the first rule written here, the earliest-filed
10-K carrying the year at all, was corrected the same day, because it dates
Apple's FY2007 and FY2008 from the FY2009 10-K and labels both FY2009. Over the
whole document the corrected rule leaves out exactly those two, whose own
reports predate the structured data, and keeps 17 years with no label twice.
Part 13, F11. All five are 10-Ks, and no filing of another form carried an
annual figure for any of the five years before them. Read from a second pull of
the same document on 2026-09-13, HTTP 200, 3.79 MB, 503 `us-gaap` tags and
25,135 facts, 89 more than on 2026-09-11; every one of section B's 70 rows is
still the latest vintage in it. One row per year, the revenue figure as that
report filed it, is in the committed csv with section `Y`.

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

*The block's shape, 2026-09-16, decision 48 items 3 and 4.* Every figure
above stands and one row is no longer a field of the block: `gross_profit`
is the witness for the formula and is not carried, since no formula reads
it. The block carries `cost_of_revenue` instead, `CostOfGoodsAndServicesSold`
for Apple, read from the stored facts of the pull of 2026-09-15 at the
same vintages as the gross profit row: FY2021 212,981 (0000320193-23-000106),
FY2022 223,546 (0000320193-24-000123), FY2023 214,137, FY2024 210,352 and
FY2025 220,960 (0000320193-25-000079). Section H holds the identity between
the two rows; the csv carries the five rows with their provenance.

*The block's shape, 2026-09-17, decision 48 item 7, first half (Part 11
D39).* A fifteenth field joins the table: `shares_outstanding`, the filer's
own count at the fiscal year end from `CommonStockSharesOutstanding`, in
whole shares as filed and never in millions. Read from the stored facts of
the pull of 2026-09-15 at the latest vintage: FY2021 **16,426,786,000**,
FY2022 **15,943,425,000**, FY2023 **15,550,061,000**, FY2024
**15,116,786,000**, each on the following year's 10-K (0000320193-22-000108,
-23-000106, -24-000123, -25-000079), and FY2025 **14,773,260,000** on the
10-Q filed 2026-07-31 (0000320193-26-000020); every count is the same on
every vintage that carries it, the year's own 10-K included. The unit is
`shares`, not money: the block's one-currency rule reads money units only,
so a count beside dollar figures is not a second currency. The second half
of item 7, the price and a filer with more than one class, stays open.

### C. The tag each field resolves from

In order; the first that yields a fact for the period wins, and none yielding
a fact leaves the field out of that year, listed as unresolved with the field,
the year and the tags, for the check to stop on (D30).

| Field | Kind | Tags, in order |
|---|---|---|
| revenue | duration | `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet`, `Revenues` |
| cost_of_revenue | duration | `CostOfRevenue`, `CostOfGoodsAndServicesSold` |
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
| shares_outstanding | instant | `CommonStockSharesOutstanding` |

The revenue ordering is newest-tag-first on purpose: for FY2017, all three
tags carry the same value and the order decides which `accn` the row cites,
never which number it reports.

*Row changed 2026-09-16, decision 48 (D36, section H).* `cost_of_revenue`
stands where `gross_profit` stood. No filer here files both of its tags, so
the order decides nothing; the taxonomy's total is first.

*Row added 2026-09-17, decision 48 item 7, first half (section B's note,
Part 13 B's note, Part 11 D39).* `shares_outstanding` is the fifteenth
field. A new field's first tag has no listed tag to be witnessed against
(D36); it is the taxonomy's element for the line, as `CostOfRevenue` was
admitted, and its falsifier is F9, the split reaching FY2021's count through
a later vintage. Its unit is `shares`: the one-currency rule reads the units
of money fields only, so the count is not a second currency.

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

*Note, 2026-09-16, decision 41.* PHI-3.1's text now says so (f3b0deb):
borrowings less cash and cash equivalents, and nothing else, with the
presentation-choice reason below as the clause's own. The same sentence is
the clause's `text` in `philosophy.toml`; no parameter was added, since the
definition is carried by the key `net_debt_to_ebitda` (decision 47). The
figures in this section stand as computed.

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
definition living in the key's name rather than in a parameter. Decided
2026-09-15 with decision 47: the key stays `net_debt_to_ebitda`, its formula
is Part 10 B's, and a formula that netted securities would be a new key.

### G. The bridge's rows: net debt and NOPAT on the filed figures

Computed 2026-09-15 by hand, decisions 46 and 47, before the bridge between
the reader's block and the metrics exists (Order 4, step 1). Part 10 holds
the metrics to synthetic figures with one `debt` and one `tax_rate` per year;
the block the reader returns carries three borrowing fields and an
`effective_tax_rate` the metrics may not use (D32, D33). These rows are the
same arithmetic on Apple's filed figures from section B, in the shape the
block carries, so the bridge has something independent to be wrong against
that Part 10 cannot see. Plain decimal arithmetic, none of the repository's
code. USD millions, as section B; the block holds the figures in whole
dollars as filed (`edgar_facts_aapl.csv`), so every sum and difference here
is exact and a reader that rounds on the way in fails these rows.

**Net debt (D33, definition A of section F).** Borrowings are the three
named fields added; net debt is borrowings less cash. A year in which any
of the three does not resolve has no net debt, and the check stops there
when a clause needs it (D25, D30): a missing borrowing field is never read
as 0.

| FY | commercial_paper | long_term_debt_current | long_term_debt_noncurrent | Borrowings | cash | net_debt |
|---|---|---|---|---|---|---|
| FY2021 | 6,000 | 9,613 | 109,106 | 124,719 | 34,940 | **89,779** |
| FY2022 | 9,982 | 11,128 | 98,959 | 120,069 | 23,646 | **96,423** |
| FY2023 | 5,985 | 9,822 | 95,281 | 111,088 | 29,965 | **81,123** |
| FY2024 | 9,967 | 10,912 | 85,750 | 106,629 | 29,943 | **76,686** |
| FY2025 | 7,979 | 12,350 | 78,328 | 98,657 | 35,934 | **62,723** |

Cross-check against section F, computed three days earlier from the same
figures: net debt over EBITDA (operating income + D&A) is 89,779 / 120,233
= 0.7467, 96,423 / 130,541 = 0.7386, 81,123 / 125,820 = 0.6448, 76,686 /
134,661 = 0.5695 and 62,723 / 144,748 = 0.4333, which round to section F's
definition A row, 0.75, 0.74, 0.64, 0.57 and 0.43. A `net_debt_to_ebitda`
that reads the three fields reproduces both.

**NOPAT at the stated rate (D32).** Operating income times one less the
rate the philosophy states, 0.20 for the synthetic philosophy; the block's
`effective_tax_rate` is beside it and is not read. The two columns are the
row's point: a NOPAT computed at the filed rate is a different figure in
every year, and in FY2024 by 5,052 million.

| FY | operating_income | Stated rate | NOPAT at the stated rate | effective_tax_rate, filed | NOPAT at the filed rate, not the figure |
|---|---|---|---|---|---|
| FY2021 | 108,949 | 0.20 | **87,159.2** | 0.133 | 94,458.8 |
| FY2022 | 119,437 | 0.20 | **95,549.6** | 0.162 | 100,088.2 |
| FY2023 | 114,301 | 0.20 | **91,440.8** | 0.147 | 97,498.8 |
| FY2024 | 123,216 | 0.20 | **98,572.8** | 0.241 | 93,520.9 |
| FY2025 | 133,050 | 0.20 | **106,440.0** | 0.156 | 112,294.2 |

The stated-rate column is exact: a rate stated to n decimal places times
a whole-dollar figure has at most n decimal places, so at 0.20 the product
ends at a tenth of a dollar at worst, which is why the block's Decimals
survive to here. The filed-rate column is rounded
to a tenth and is in this table only so that a bridge reading the wrong
field is caught by every row, not by FY2024 alone.

### H. Gross margin on the filed figures

Computed 2026-09-16 by hand, decision 48 items 3 and 4, before the key's
formula changed. Part 10 B now reads gross margin as revenue less cost of
revenue, over revenue, so that a filer presenting no gross profit can be
screened on PHI-2.2 from the two lines it does file (Part 13 B). This
section shows, on Apple, that the formula measures what the old one
measured: revenue less the cost of sales Apple files equals the gross
profit Apple files, to the dollar, in every year, so no margin moves for a
filer that presents both. Plain decimal arithmetic, none of the
repository's code. USD millions; the identity was checked on the whole
dollars the block holds and is exact. No workbook sheet: as with section
G, nothing here has a second source by hand.

| FY | revenue | cost_of_revenue | revenue less cost | gross_profit as filed | Equal | gross_margin |
|---|---|---|---|---|---|---|
| FY2021 | 365,817 | 212,981 | 152,836 | 152,836 | yes | **0.4178** |
| FY2022 | 394,328 | 223,546 | 170,782 | 170,782 | yes | **0.4331** |
| FY2023 | 383,285 | 214,137 | 169,148 | 169,148 | yes | **0.4413** |
| FY2024 | 391,035 | 210,352 | 180,683 | 180,683 | yes | **0.4621** |
| FY2025 | 416,161 | 220,960 | 195,201 | 195,201 | yes | **0.4691** |

The margin is the ratio rounded to four places; the code's float is
compared at that precision and not closer. The same statements witness
the cost line's place: revenue less cost of sales less `OperatingExpenses`
equals `OperatingIncomeLoss` in all five years (43,887, 51,345, 54,847,
57,467 and 62,151 of operating expenses), so the cost of sales is the line
between revenue and operating income and nothing else is in it.

**Why the cost line and not the subtotal.** A gross profit is a subtotal
some filers present and some do not; a cost of revenue is a line every
income statement has. Under Part 12 F's principle a cost line can only be
as wide as or wider than the line behind a presented gross profit, so the
margin computed from it is never the flattering one. Rejected: keeping
`gross_profit` on the block beside `cost_of_revenue` with no formula
reading it, which D32 did for the tax rate and which the rule that a value
nothing consumes is not stored refuses here; two formulas under one key,
the subtotal where filed and the difference where not, the repair shape;
a second key, which PHI-2.2 would have to name for a filer-dependent
reason.

**What is not decided here.** A filer that presents gross profit and files
no cost-of-revenue tag would stop on PHI-2.2 under this formula; none of
the three filers is one, and the trigger is the first candidate that is.

---

## Part 13 — Two more filers: a December year end and a bank

Recorded 2026-09-13 from four fetched documents, before any provider method
exists. Part 12 took D26 to D33 on one filer and said so. This Part holds each
of them against two more: which a second and third witness confirm, which they
cannot exercise, and which they contradict, with the rows that show it. It is
not a second figures table for the reader to reproduce; Part 12 B stays that.

**Sources**, all from `data.sec.gov`, pulled 2026-09-13, each HTTP 200. Fact
counts are across every namespace in the document.

| Filer | CIK | Document | Size | Content |
|---|---|---|---|---|
| Alphabet Inc. | 1652044 | `api/xbrl/companyfacts/CIK0001652044.json` | 3.16 MB | 543 `us-gaap` tags, 20,907 facts |
| Alphabet Inc. | 1652044 | `submissions/CIK0001652044.json` | 0.15 MB | the filer's record |
| JPMorgan Chase & Co. | 19617 | `api/xbrl/companyfacts/CIK0000019617.json` | 7.94 MB | 918 `us-gaap` tags, 53,666 facts |
| JPMorgan Chase & Co. | 19617 | `submissions/CIK0000019617.json` | 4.61 MB | the filer's record |

**These two on purpose.** Alphabet is W-1 on the watchlist and closes its year
on 31 December, so a calendar label happens to be right on every row: the
opposite of Apple. JPMorgan is held in portfolio 3, it is the bank
`excluded_industry` needs for its reference row, and its `assets` row carries
an industry label that can be set beside what EDGAR states.

**The facts cited here are committed** as `tests/golden/edgar_facts_googl.csv`
(82 rows), `tests/golden/edgar_facts_jpm.csv` (53 rows) and
`tests/golden/edgar_submissions.csv` (14 rows), the first two in Part 12's
columns, with `section` naming this Part's section or falsifier row set, or
`Y` for section F's rows. A row
whose note begins `absent` records a tag with no fact anywhere in its artifact.
A stand-in built from the fixture lacks that tag either way, so the row records
the claim and does not check it; the check is the neighbour rows, tags that are
in the artifact and that a reader might reach for when a field's own tags yield
nothing. The documents are not committed.

**No workbook sheet.** Every row here is transcribed from one artifact and
nothing has a second source by hand, so there is nothing for a sheet to
compare. Part 12 gained its sheet when section E gave it a second column; this
Part gets one on the same terms.

### A. D26 to D33 against two more witnesses

USD millions.

| # | Alphabet | JPMorgan | Verdict |
|---|---|---|---|
| D26 | Annual `NetIncomeLoss` keyed on `fy`: 12 keys, all 12 collide, worst 6. On `(end, accn)`: 41 keys, none collide. | 18 keys, all collide, worst 6. On `(end, accn)`: 59 keys, none. | **Confirms** over annual durations and instants. **Contradicts as worded** over all durations: F6. |
| D27 | 14 of 3,897 `fp: FY` duration facts are shorter than 120 days, 11 of them on 10-Ks. None is on a tag in Part 12 C. | 12 of 8,739, 9 on 10-Ks. None on a tag in Part 12 C. | **Confirms.** Cannot exercise on the block's tags. The 53-week range cannot be exercised: every annual period is 364 or 365 days. |
| D28 | Instants at every quarter end: `StockholdersEquity` 362,916 at 2025-06-30, 415,265 at 2025-12-31. Year ends derived from the annual facts: 31 December, FY2020 to FY2025. | The same shape; year ends 31 December. | **Confirms** that instants are quarterly. **Cannot exercise** "derived, never assumed": a reader that assumes 31 December returns the same dates on both. Apple remains the only witness for that half. |
| D29 | Latest filed cites a 10-Q (filed 2026-07-23) for FY2024 equity and for every FY2025 balance-sheet field. A split reaches FY2021's share count through a 10-Q: F9. | FY2025 equity cites a 10-Q (filed 2026-08-06). | **Confirms** that the form is not a filter among periodic reports. **Contradicts twice**: a proxy statement is the latest filing, F10; and latest filed does not keep a series comparable, F7. |
| D30 | Revenue resolves from the first tag for FY2021 to FY2024 and the third for FY2025. `gross_profit` and `depreciation_amortisation` raise in every year, `long_term_debt_noncurrent` in FY2021 and FY2022, `marketable_securities_noncurrent` in FY2025. | Nine of fourteen fields raise in every year: section C. | **Confirms the rule**: every raise is true. **Contradicts its premise**, that the tags in one list measure one thing: F7, F8. |
| D31 | `frame` on 9,205 of 20,907 facts, 44.0%. | 20,402 of 53,666, 38.0%. | **Confirms**, with one more reason: in F10 the frame sits on the proxy copy, the latest, as it sits on the latest copy in Part 12's F1 to F3, so a reader keyed on `frame` returns the proxy's figure. |
| D32 | `EffectiveIncomeTaxRateContinuingOperations` in all five years, 0.139 to 0.168. | All five, 0.184 to 0.221. | **Confirms** the tag is filed. **Cannot exercise** the reason for keeping NOPAT's rate out of the block: neither series has a year like Apple's FY2024. |
| D33 | `LongTermDebt` 49,085 at FY2025 against 1,996 + 46,547 = 48,543 from the carrying tags, commercial paper 0. | `CommercialPaper` last filed for 2017-09-30; `LongTermDebtCurrent` and `LongTermDebtNoncurrent` never. | **Confirms** that `LongTermDebt` is a different measure. **Cannot be implemented as written**: "a borrowing tag the block does not name is a raise" needs a stated list of what a borrowing tag is, and Alphabet's `FinanceLeaseLiability`, 2,500 at FY2025, is a case where the answer moves the figure. Cannot be exercised on the bank, and should not be. |

### B. Alphabet, FY2021 to FY2025, read with Part 12 C's tags as written

USD millions except the tax rate. Latest filed per D29. A cell reading
**raises** is a year that no tag in the field's list yields. Each row's tag,
`accn` and `filed` are in the committed csv.

| Field | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|
| revenue | 257,637 | 282,836 | 307,394 | 350,018 | 402,836 |
| gross_profit | **raises** | **raises** | **raises** | **raises** | **raises** |
| operating_income | 78,714 | 74,842 | 84,293 | 112,390 | 129,039 |
| effective_tax_rate | 0.162 | 0.159 | 0.139 | 0.164 | 0.168 |
| depreciation_amortisation | **raises** | **raises** | **raises** | **raises** | **raises** |
| operating_cash_flow | 91,652 | 91,495 | 101,746 | 125,299 | 164,713 |
| capex | 24,640 | 31,485 | 32,251 | 52,535 | 91,447 |
| equity | 251,635 | 256,144 | 283,379 | 325,084 | 415,265 |
| cash | 20,945 | 21,879 | 24,048 | 23,466 | 30,708 |
| marketable_securities_current | 118,704 | 91,883 | 86,868 | 72,191 | 96,135 |
| marketable_securities_noncurrent | 1,400 | 803 | 1,400 | 266 | **raises** |
| commercial_paper | 0 | 0 | 0 | 2,300 | 0 |
| long_term_debt_current | 0 | 0 | 1,000 | 999 | 1,996 |
| long_term_debt_noncurrent | **raises** | **raises** | 11,870 | 10,883 | 46,547 |

**Revenue changes tag in the other direction.** Alphabet tags
`RevenueFromContractWithCustomerExcludingAssessedTax` through FY2024 and
`Revenues` on the FY2025 10-K; where both exist, in FY2021, FY2023 and FY2024,
they agree to the dollar. Part 12 C calls its order newest-tag-first. For
Alphabet the newest tag is last in the list. No value moves; the sentence
describes Apple's history, not a property of the order.

**What the raises are.** Three kinds, which D30 treats alike:

- **A subtotal the filer does not present.** No `GrossProfit` fact exists in
  the artifact in any year; `CostOfRevenue` does, 162,535 at FY2025. A gross
  profit for Alphabet is revenue less cost of revenue: arithmetic on the way
  into the block, the shape D33 refuses for debt, or a different formula for
  `gross_margin`, which D24 says is a different metric key. The only
  depreciation or amortisation expense tag with annual facts in FY2021 to
  FY2025 is `Depreciation`, 21,136 at FY2025, which names no amortisation;
  putting it in the list would change what EBITDA means for this filer alone.
  F8.
- **A wider measure under an older tag.** `long_term_debt_noncurrent` for
  FY2021 and FY2022. F7.
- **A field nothing reads.** Alphabet filed no `MarketableSecuritiesNoncurrent`
  at 2025-12-31. Under Part 12 F's decision A no metric nets securities, so
  this raise stops a check over a field no formula uses.

So on the watchlist's own first candidate a reader built to Part 12 stops the
philosophy check at PHI-1.2, and any one of three clauses would stop it: return
on invested capital needs FY2021's debt, gross margin needs gross profit, net
debt to EBITDA needs D&A. That is D25 working, and it is not the answer case
4.1 is written for.

*Decided 2026-09-16, decision 48 items 3 and 4 (D36, Part 12 H).* The
table above is the read of 2026-09-13 with Part 12 C's tags as written
then and stands as read. Since then: `gross_profit` is not a field, so its
five raises are gone; `cost_of_revenue` is, resolving from `CostOfRevenue`
in every year, read from the stored facts of the pull of 2026-09-16 at the
latest vintage, and gross margin is computed from it. Plain decimal
arithmetic, USD millions, the ratio to four places:

| FY | revenue | cost_of_revenue | Vintage | gross_margin |
|---|---|---|---|---|
| FY2021 | 257,637 | 110,939 | 0001652044-24-000022, filed 2024-01-31 | 0.5694 |
| FY2022 | 282,836 | 126,203 | 0001652044-25-000014, filed 2025-02-05 | 0.5538 |
| FY2023 | 307,394 | 133,332 | 0001652044-26-000018, filed 2026-02-05 | **0.5663** |
| FY2024 | 350,018 | 146,306 | 0001652044-26-000018, filed 2026-02-05 | **0.5820** |
| FY2025 | 402,836 | 162,535 | 0001652044-26-000018, filed 2026-02-05 | **0.5965** |

PHI-2.2 reads the last three, every one above 0.35; the deciding year
would be FY2023 at 21.63 points of headroom. No gross profit witnesses the
identity for this filer; what the artifact shows is revenue less
`CostsAndExpenses` equal to `OperatingIncomeLoss` in all five years
(178,923, 207,994, 223,101, 237,628 and 273,797), and `CostOfRevenue` is
one component of that total. That it is the cost of revenue line is the
taxonomy's definition and a reading of the filing, and D36 records the
admission as the one without a witness.

The other two raises stand, decided. `depreciation_amortisation`: Alphabet
files no D&A figure under any us-gaap tag; `Depreciation` is a different
measure by F8's witness on Apple, no amortisation expense tag exists in
the artifact in any year, and the FY2021 report tagged its depreciation
outside us-gaap, so the stored FY2021 figure, 10,273, is a comparative
from the FY2023 report. PHI-3.1 stops naming the field for as long as
Alphabet files this way; `Depreciation` in the list, two fields with the
sum in the metric, and a key over operating income plus depreciation alone
were rejected, the last as a change to what PHI-3.1 measures for every
filer. `long_term_debt_noncurrent` for FY2021 and FY2022: D36 keeps the
wider tag out, PHI-2.1 stops at FY2021, and the stop expires with the
FY2027 report. So the check on this candidate stops at PHI-2.1 until
early 2028 and at PHI-3.1 after; the runner's 4.1 says the first, and
whether Alphabet stays case 4.1's X is a decision surfaced, not taken.

**Shares outstanding, and whether it is a sum.** Not in this artifact, and the
arithmetic the question points at moves rather than disappears.

- **No per-class share count is in the artifact.** The cover-page count,
  `dei:EntityCommonStockSharesOutstanding`, has no fact at all for Alphabet;
  JPMorgan's artifact, one class, carries it (2,697,032,375 at 2026-01-31).
  Every instant in Alphabet's artifact is unique on `(tag, end, accn)`, so no
  class-level values sit under one key waiting to be added.
- **The one count present is the filer's own.** `CommonStockSharesOutstanding`,
  one value per period and accession: 12,088,000,000 at 2025-12-31. Reading it
  is not arithmetic. Whether it equals the classes added up cannot be checked
  from this artifact; that is a reading of the filing, which is on
  `www.sec.gov`, the host that refuses a generic User-Agent.
- **The arithmetic reappears in the metric.** `free_cash_flow_yield` divides by
  price times shares outstanding, one price against one count. The submissions
  document lists four tickers under Alphabet's one CIK, and neither document
  says which ticker is which class or how many shares each has. Part 10 B's
  formula assumes one class. That is D24's question about the metric key, not
  the reader's.
- **The count moves with a split**, F9. Latest filed returns the split-adjusted
  count, the convention D19 fixed for closes.
- **Also not decided**: the year-end count or the cover-page count, each
  against a price of a later date. Part 12 carries no shares field.

*Decided 2026-09-17, decision 48 item 7, first half (Part 11 D39).* The
count is a field, `shares_outstanding`, the filer's own count at the year
end from `CommonStockSharesOutstanding`, whole shares, one per year, the
range and the yield reading the latest year's. From the stored facts of the
pull of 2026-09-16 at the latest vintage: FY2021 **13,242,000,000** on the
FY2022 10-K (0001652044-23-000016, filed 2023-02-03), the split-adjusted
count F9 shows reaching back, and not the FY2021 report's 662,121,000;
FY2022 **12,849,000,000**, FY2023 **12,460,000,000** and FY2024
**12,211,000,000**, each on the following year's 10-K (0001652044-24-000022,
-25-000014, -26-000018); FY2025 **12,088,000,000** on the 10-Q filed
2026-07-23 (0001652044-26-000071). The filer's own count covers every class
and is read, not summed. Rejected, from the shape the handoff carried: the
cover-page count, which Alphabet does not file; the weighted average, a
different measure; summing the classes, which the artifact cannot do;
refusing a CIK with several tickers, which refuses every preferred series.
The second half, the price and the classes, is open.

### C. JPMorgan: the SIC code, the label, and a block that mostly raises

**What EDGAR states.** In the submissions document: `sic` "6021",
`sicDescription` "National Commercial Banks", `ownerOrg` "02 Finance",
`entityType` "operating", `fiscalYearEnd` "1231". Alphabet's, for contrast:
"7370", "Services-Computer Programming, Data Processing, Etc.", "06
Technology". The SIC code is in the submissions document and not in
companyfacts, so it is a second fetch. The document carries the current code
only, with no date and no history, where it does carry a dated history of the
filer's names, four entries since 1994. A SIC code is therefore as of the pull
date, and a reference row that cites one cites the pull date.

**Twelve more financial filers, for `excluded_industry`'s code list.** Pulled
from `data.sec.gov` on 2026-09-14, each HTTP 200, and committed as rows of
`tests/golden/edgar_submissions.csv`. Chosen to be one or two of each kind
of company PHI-3.2 is about, so that each code the clause lists has a filer
behind it rather than a code remembered:

| Filer | CIK | SIC | `sicDescription` |
|---|---|---|---|
| Goldman Sachs Group Inc. | 886982 | 6211 | Security Brokers, Dealers & Flotation Companies |
| Travelers Companies, Inc. | 86312 | 6331 | Fire, Marine & Casualty Insurance |
| Fifth Third Bancorp | 35527 | 6022 | State Commercial Banks |
| M&T Bank Corp | 36270 | 6022 | State Commercial Banks |
| Zions Bancorporation, N.A. | 109380 | 6021 | National Commercial Banks |
| Capitol Federal Financial, Inc. | 1490906 | 6035 | Savings Institution, Federally Chartered |
| TFS Financial Corp | 1381668 | 6035 | Savings Institution, Federally Chartered |
| Flagstar Bank, N.A. | 910073 | 6036 | Savings Institutions, Not Federally Chartered |
| MetLife Inc. | 1099219 | 6311 | Life Insurance |
| Prudential Financial Inc. | 1137774 | 6311 | Life Insurance |
| Marsh & McLennan Companies, Inc. | 62709 | 6411 | Insurance Agents, Brokers & Service |
| Arthur J. Gallagher & Co. | 354190 | 6411 | Insurance Agents, Brokers & Service |

Every one of the thirteen financial filers here, JPMorgan included, carries
`ownerOrg` "02 Finance", and Alphabet "06 Technology"; nothing in either
document says what the field classifies, so it is recorded and not used.
Goldman Sachs is not a bank by its code: it is a broker-dealer. Flagstar's
name says national association and its code says a savings institution not
federally chartered, which is what a code with no date looks like when the
company it describes has changed. Eight codes over thirteen filers, and no
code for any kind this Part did not fetch.

**Where the label in the database comes from.** `assets` row 12 reads sector
"Financials", industry "Banks". It was written by
`src/portfolio_tool/scripts/seed_portfolio.py`, line 90, typed by hand with the
rest of the synthetic seed. `DataManager.force_update_asset_info` overwrites it
with the price provider's label, reached from `scripts/update_all_assets.py`
and from `tools/data_tools.py`, which nothing in the agent package imports;
`DataManager._get_or_create_asset` writes the provider's label when a row is
first created, including from `data_agent.py`. `assets` has no source column,
so a row cannot say which writer last set it, and only a held or queried
company has a row. Read from the code, not run.

*Note, 2026-09-15, decision 55.* `scripts/update_all_assets.py` and
`tools/data_tools.py` were deleted on 2026-09-15 (4911f5e and 0707ac6), so
`force_update_asset_info` has no caller and the provider's label reaches an
existing row through nothing. `_get_or_create_asset` still writes it when a
row is first created, and the seed still writes row 12 by hand. The paragraph
above describes the code as read on 2026-09-13 and stands as read.

So the label has no filed source and no date, and its vocabulary is a price
vendor's or the seed's. The SIC code has a filed source and a pull date, and
exists for every filer, held or not. Decision 28 put the SIC code on the block;
this is the measurement under it.

**The block.** Part 12 C's tags against JPMorgan. USD millions except the tax
rate.

| Field | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 | Resolved from |
|---|---|---|---|---|---|---|
| revenue | 121,649 | 128,695 | 158,104 | 177,556 | 182,447 | `Revenues`, the third tag; equal in every year to `RevenuesNetOfInterestExpense` |
| effective_tax_rate | 0.189 | 0.184 | 0.196 | 0.221 | 0.214 | `EffectiveIncomeTaxRateContinuingOperations` |
| depreciation_amortisation | 7,932 | 7,051 | 7,512 | 7,938 | 8,821 | `DepreciationAmortizationAndAccretionNet`, the second tag |
| operating_cash_flow | 78,084 | 107,119 | 12,974 | -42,012 | -147,782 | `NetCashProvidedByUsedInOperatingActivities` |
| equity | 294,127 | 292,332 | 327,878 | 344,758 | 362,438 | `StockholdersEquity` |

**Raises in every year**, no fact of the tag anywhere in the artifact:
`gross_profit`, `operating_income`, `capex`, `marketable_securities_current`,
`marketable_securities_noncurrent`, `long_term_debt_current`,
`long_term_debt_noncurrent`. **Raises in every year**, the tag last used long
before the window: `cash` (`CashAndCashEquivalentsAtCarryingValue`, last at
2018-12-31) and `commercial_paper` (last at 2017-09-30).

*Note, 2026-09-17, decision 48 item 7.* `shares_outstanding` is not in this
fixture. The artifact was read on 2026-09-13 for the fields of that day and
is not stored, since the exclusion decides before the facts are fetched,
and it was not read again for this field. In the fixture the field is
unresolved in every year by construction, which says nothing about what
JPMorgan files under the tag.

**Whether that is D30 working, or D30 needing a bank rule: working.** Every
raise is true: JPMorgan files no gross profit, no operating income and no
capital expenditure under those tags, and has not used the cash or commercial
paper tags since 2018 and 2017. A bank rule inside D30 would have to put
something in those cells, pre-tax income (72,595 at FY2025) for operating
income or `CashAndDueFromBanks` (21,742) for cash, which is a figure nobody
filed under that name and the reader answering PHI-3.2's question by itself.
The five fields that do resolve are the warning: revenue net of interest
expense, a tax rate, D&A with accretion, an operating cash flow of minus
147,782 and equity all reach the block with nothing wrong in their provenance,
and none means for a bank what the metrics assume.

**What it shows instead is an order.** D25 stops the whole check at the first
missing figure and names it. A bank read figures-first reaches the answer as
PHI-1.2, gross margin not in the figures: a true refusal citing the wrong
clause, where case 4.6 asks for PHI-3.2. The exclusion is decidable from the
submissions document before any year is read, and nothing in D26 to D33 says
which comes first.

### D. Falsifier rows

Numbered on from Part 12's. Each is in the committed csv with its full
provenance.

**F6 — two facts under one `(tag, end, accn)` (D26).** `OperatingIncomeLoss` on
Alphabet's 10-Q 0001652044-25-000062, both ending 2025-06-30: 61,877 million
from 2025-01-01 and 31,271 million from 2025-04-01. A 10-Q carries the quarter
and the year to date. Over every duration fact, `(tag, end, accn)` collides on
2,048 keys on Alphabet and 6,098 on JPMorgan; with `start` added, on none. Over
annual durations and instants it collides on neither, with or without the unit.
So D26 holds for the rows the reader keeps, and only because D27's period test
runs first; as the identity of a fact it needs `start`. Part 12 measured D26 on
annual `NetIncomeLoss`, where the difference cannot show.

**F7 — a re-presentation that reaches back one year (D29, D30).** Alphabet's
non-current debt at 2023-12-31 is **13,253 million** under
`LongTermDebtAndCapitalLeaseObligations` on the FY2023 10-K, and **11,870** on
the FY2024 10-K under that tag and under `LongTermDebtNoncurrent`. The
difference, 1,383, is `FinanceLeaseLiabilityNoncurrent` at the same date on the
same filing. FY2021 (14,817) and FY2022 (14,701) exist only under the older tag
and were never re-presented, because a balance sheet carries one comparative
year. For D30: the older tag is not the newer one renamed but a wider measure,
so listing it under `long_term_debt_noncurrent` would join lease-inclusive and
lease-exclusive years into one series without a raise. A list is safe only for
tags that measure the same thing, which Part 12 did not need to say because
Apple's revenue tags do. For D29: "a five-year series built from originals
mixes pre- and post-restatement figures" is true and not sufficient; a series
built from latest filed mixes them too, as far back as no comparative column
reached.

**F8 — the neighbour of a field the filer does not present (D30).** Alphabet at
FY2025: `CostOfRevenue` 162,535 and `Depreciation` 21,136 are in the artifact;
`GrossProfit`, `DepreciationDepletionAndAmortization` and
`DepreciationAmortizationAndAccretionNet` are not, in any year. A reader that
falls back to the neighbour returns a gross profit nobody filed or an EBITDA
with no amortisation in it, and passes a test that only asks for a number.
*Note, 2026-09-16, decision 48.* `CostOfRevenue` is now a field's own tag
(D36, section B's note) and no longer a neighbour; `Depreciation` still is,
and the test that no neighbour is used keeps it.

**F9 — a split reaching back through a 10-Q (D29).** Alphabet's
`CommonStockSharesOutstanding` at 2021-12-31: **662,121,000** on the FY2021
10-K, filed 2022-02-02, and **13,242,000,000** on the 10-Q filed 2022-07-27,
after the split `StockholdersEquityNoteStockSplitConversionRatio1` records as
20 at 2022-07-15. A reader that keeps the original, or selects on 10-K, returns
a count twenty times too small against any price quoted after the split.

**F10 — a proxy statement is the latest filing (D29, D31).** JPMorgan's
`NetIncomeLoss` for each of FY2021 to FY2025 is on its 2026 proxy statement
(DEF 14A, 0000019617-26-000096, filed 2026-04-06), rounded to the hundred
million: **48,300** against the 10-K's 48,334; 37,700 against 37,676; 49,600
against 49,552; 58,500 against 58,471; **57,000** against 57,048. The proxy
rows carry no `fy` and no `fp`, and they carry the `frame` the 10-K copies do
not. Latest filed, whatever form carried it, returns the proxy's figure for all
five years; a reader keyed on `frame` does the same; a check that reads a
changed figure as a restatement, PHI-5.2's shape, finds five. Alphabet's proxy
carries the same tag for the same years equal to the dollar, so "take the later
filing only where it differs" passes Alphabet and fails JPMorgan. Net income is
not a field in Part 12 B, so no figure there moves; what F10 contradicts is
D29's rule.

**F11 — a year no filing reports as its own (D21).** Apple's first filing in
the structured data is the FY2009 10-K (0001193125-09-214859, filed
2009-10-27), and it carries `NetIncomeLoss` for three fiscal years: 3,496
million for the year ending 2007-09-29, 4,834 for 2008-09-27 (section D's F3
row) and 5,704 for 2009-09-26. The earliest 10-K carrying 2008-09-27 is that
filing, so a reader that takes it as FY2008's own report dates FY2008 from
October 2009 and labels it FY2009, beside the real FY2009. Its own year is
2009-09-26, the latest end it carries; FY2007 and FY2008 have no own report and
are not years. The committed csv carries the 2007 and 2009 rows with section
`F11`; F3 already carries 2008.

### E. What this Part leaves open

Questions the rows above raise and D26 to D33 do not answer. None is decided
here.

1. D26's wording, which F6 shows needs `start`, or says which rows it keys.
   Decided 2026-09-13: `start` is in the key (D26).
2. Which forms count as filing a figure, since D29 excludes none and F10 shows
   one that has to be. Decided 2026-09-13: 10-K, 10-Q, 8-K and their
   amendments (D29).
3. When a tag belongs in a field's list (F7, F8). Decided 2026-09-16
   (decision 48, D36): on a witness, one tag at a time; F7's and F8's tags
   stay out.
4. `gross_margin` and `net_debt_to_ebitda` for a filer that presents no gross
   profit and no combined D&A: D24's question about the metric keys. Until it
   is answered W-1 cannot be screened on PHI-2.2 or PHI-3.1. Decided
   2026-09-16 (decision 48): `gross_margin` is revenue less cost of revenue
   over revenue, the block carrying `cost_of_revenue` and not `gross_profit`
   (Part 10 B, Part 12 H, section B's note); `net_debt_to_ebitda` keeps its
   formula and the refusal stays, W-1 stopping on PHI-3.1 as it files today.
5. What a borrowing tag is for D33's raise, and whether a finance lease is one.
   Decided 2026-09-15 (decision 47, D33): a borrowing is one of the three
   named fields, a finance lease is not one, and the raise is a known limit,
   not a rule the code can keep (Part 12 G).
6. The two `marketable_securities` fields in Part 12 B, which no metric reads
   under Part 12 F's decision A.
7. `shares_outstanding`: which count, and `free_cash_flow_yield` for a filer
   with more than one class. First half decided 2026-09-17 (decision 48,
   Part 11 D39): the filer's own year-end count, `CommonStockSharesOutstanding`,
   a field of the block per year, the range and the yield reading the latest
   year's (Part 12 B's and section B's notes). The second half, the price
   and a filer with more than one class, is open.
8. Whether an industry exclusion is decided before the years are read.
   Decided 2026-09-14 (D34, Part 10 F): before. *Note, 2026-09-16, decision
   29.* Built as `screening.exclude`, which the node runs on the filers row
   before the company facts are fetched, so an excluded company's figures
   are never asked for; JPMorgan's first live check read no fact.

### F. Each fiscal year's own annual report

Added 2026-09-13 for D21, from the same two documents, the rule stated in
Part 12 A: a filing's own year is the latest year end it carries an annual
figure for, a year's own report is the earliest-filed 10-K or 10-K/A whose own
year it is, its label is `FY` and that report's `fy`, and the year counts from
that report's filed date. Over the whole documents the rule leaves out
Alphabet's 2013 and 2014 year ends, first carried by its FY2015 10-K, and
JPMorgan's 2007 and 2008, first carried by its FY2009 10-K, and keeps 11 and
17 years with no label twice.

| Fiscal year | Alphabet: own report | Filed | JPMorgan: own report | Filed |
|---|---|---|---|---|
| FY2021 | 0001652044-22-000019 | 2022-02-02 | 0000019617-22-000272 | 2022-02-22 |
| FY2022 | 0001652044-23-000016 | 2023-02-03 | 0000019617-23-000231 | 2023-02-21 |
| FY2023 | 0001652044-24-000022 | 2024-01-31 | 0000019617-24-000225 | 2024-02-16 |
| FY2024 | 0001652044-25-000014 | 2025-02-05 | 0000019617-25-000270 | 2025-02-14 |
| FY2025 | 0001652044-26-000018 | 2026-02-05 | 0001628280-26-008131 | 2026-02-13 |

Every own report is a 10-K, every `fy` matches the year it reports, and no
filing of another form carried an annual figure for any of the ten years
before it. Every annual figure in either document ends on 31 December, and no
two year ends are fewer than 350 days apart, so neither filer exercises a
change of fiscal year. One row per year, the revenue figure as the own report
filed it, is in each committed csv with section `Y`. JPMorgan's FY2025 report
is filed under an accession whose prefix is not JPMorgan's CIK: the prefix
names whoever submitted the filing, and it is not a way to find the filer's
own reports.

---

## Part 14 — Prediction scoring

Computed 2026-09-18 by hand, before any code (DIRECTION.md, step 5 of the
judgement half, invariant 6; PHI-6.2; benchmark case 4.5), so the scorer
has something independent to be wrong against. Decisions D41 to D45.
Plain decimal arithmetic, none of the repository's code. The ledger is the
four predictions in `docs/WATCHLIST.md`; all four are due in 2027 and none
can be scored today, so the rows below are **synthetic predictions, stated
here and nowhere else, over real filed figures**: Alphabet's FY2025 lines
from Part 13 B, read from the stored facts of the pull of 2026-09-16 at
the latest vintage (D29), the year's own annual report Part 13 F's,
`0001652044-26-000018` filed 2026-02-05. USD millions. Nothing in this
Part is written into `docs/WATCHLIST.md` or `watchlist.toml`, and nothing
in the code writes a score into either: the score in the ledger is mine.

### Decisions

| # | Decision | Choice |
|---|---|---|
| D41 | What is a score? | **Right or wrong, one comparison, strict and unrounded, no partial credit and no distance.** A `min` prediction is right when the reported figure is at or above the stated value and a `max` one when it is at or below it: "at least" and "at most" admit equality, the mirror of D9 and D23. Rejected: a distance beside the result, which is what a screen reports and a ledger does not ("No partial credit"); rounding either side before comparing, which F7 catches. |
| D42 | Which figure is the reported one? | **The period's own annual report, through the reader the screen uses (Part 12, D21 and D29), the field or metric the prediction names.** `revenue` is a field of the block, read as filed; `gross_margin`, `return_on_invested_capital` and `net_debt_to_ebitda` are Part 10 B's metric keys, by their one formula each. `operating_margin` and `free_cash_flow` are in the ledger's vocabulary (`tests/test_watchlist.py`) and no formula in the repository computes them: a prediction naming either stops naming the metric, and the formula is added with its row here when a prediction asks. A period the filer has not filed by the as-of date is not a figure: the prediction is due and unscored with that reason, never wrong (the document: "never scored right because nothing was reported", and never wrong for the same reason). A period filed but the field missing stops naming the figure, PHI-1.2's shape (D25). Rejected: the latest year in place of the stated period; a quarterly figure; a figure from anywhere but the reader. |
| D43 | When is a prediction due? | **On and after its due date, by the UTC date of the run**, the clock the screening node keeps (decision 29). Open before it, whatever has been filed. Rejected: due only after the date has passed, which leaves a prediction "by 1 March" open on 1 March; a default as-of. |
| D44 | Who writes the score, and what does the pipeline compute? | **I write the score into the ledger, with the outcome, its source, the date and the result** (`docs/WATCHLIST.md`; PHI-6.2). The pipeline writes nowhere. For a due figure prediction it computes the filing's verdict under D41 and D42 and reports it as the filing's, marked not yet recorded until the ledger carries the score; where the ledger carries one, both are reported and the answer says whether they agree, and a disagreement changes nothing, since a prediction is never edited. For an event prediction the pipeline has no outcome and reports the prediction as due and awaiting mine, listed, never skipped. Rejected: the system writing into either document; reading an event's outcome off filed facts, which is a reading and not a figure; a due event counted as scored. |
| D45 | What does the record carry? | **Per prediction: id, candidate, kind, statement, made_on, due, status (open, due, scored), and for a figure prediction its metric, bound, value and period; for a ledger-scored one the four written fields; for a due figure one the reported figure, the result, the form, the filed date and the source name; for a due one that could not be scored, the reason.** One reported figure per due prediction reaches the record, the way a finding carries `observed`: the outcome is the point of the answer. No array, no document, no figure for an open prediction. The summary beside the records: the counts of predictions, scored, due and open, computed once in the scorer and printed by the formatter. Rejected: dates only, which leaves the answer unable to state the outcome case 4.5 asks for; every year's figures; the counts in the formatter. |

### A. The ledger as of three dates

The four predictions as `watchlist.toml` carries them, none scored.

| id | kind | period | due | 2026-09-18 | 2027-02-01 | 2027-03-01 |
|---|---|---|---|---|---|---|
| W-1.1 | figure, revenue, min 420,000 | FY2026 | 2027-03-01 | open | open | due |
| W-1.2 | event | | 2027-03-01 | open | open | due |
| W-2.1 | figure, revenue, min 25,500 | FY2026 | 2027-02-01 | open | due | due |
| W-2.2 | figure, gross_margin, min 0.87 | FY2026 | 2027-02-01 | open | due | due |

| as of | predictions | scored | due | open |
|---|---|---|---|---|
| 2026-09-18 | 4 | 0 | 0 | 4 |
| 2027-02-01 | 4 | 0 | 2 | 2 |
| 2027-03-01 | 4 | 0 | 4 | 0 |

W-2.1 and W-2.2 are due on 2027-02-01 (D43); whether Adobe's FY2026 report
is filed by then is what decides scored against due-and-unscored, and
nothing here assumes it. W-1.2 on 2027-03-01 is section D's E-2 shape.

### B. The filed inputs

Alphabet, FY2025, the year's own 10-K, both lines on one filing.

| Field | Tag | Value | Form, accession, filed |
|---|---|---|---|
| revenue | `Revenues` | 402,836 | 10-K, 0001652044-26-000018, 2026-02-05 |
| cost_of_revenue | `CostOfRevenue` | 162,535 | 10-K, 0001652044-26-000018, 2026-02-05 |

gross profit = 402,836 - 162,535 = 240,301
gross_margin = 240,301 / 402,836 = 0.5965231508603997656614602468 (Part
10 B's formula; the Decimal quotient at 28 digits, 0.596523 at six).

### C. Figure predictions against the filed figure

Synthetic, made 2026-01-01, due 2026-03-01, period FY2025, read as of
2026-09-18: every row is due (D43) and FY2025 is filed, so every row is
scored. The reported figure and its source are section B's.

| id | metric | bound | value | reported | comparison | result |
|---|---|---|---|---|---|---|
| S-1 | revenue | min | 400,000 | 402,836 | 402,836 >= 400,000 | right |
| S-2 | revenue | min | 410,000 | 402,836 | 402,836 < 410,000 | wrong |
| S-3 | revenue | min | 402,836 | 402,836 | equal, at the bound | right |
| S-4 | revenue | max | 400,000 | 402,836 | 402,836 > 400,000 | wrong |
| S-5 | revenue | max | 402,836 | 402,836 | equal, at the bound | right |
| S-6 | gross_margin | min | 0.59 | 0.596523... | 0.596523 >= 0.59 | right |
| S-7 | gross_margin | min | 0.60 | 0.596523... | 0.596523 < 0.60 | wrong |

The record for S-1 (D45): status scored by the filing, not recorded;
reported 402,836,000,000 as filed, in the block's currency USD; result
right; form 10-K, filed 2026-02-05, source EDGAR. S-6's reported figure is
the ratio, 0.5965231508603997 as a float, as a finding carries a metric.

### D. Event predictions

| id | shape | as of | status | what is reported |
|---|---|---|---|---|
| E-1 | event, due 2026-03-01, the four score fields written: outcome "the FY2025 annual report's segment note shows the cloud segment with positive operating income for the full year", source "10-K 0001652044-26-000018 filed 2026-02-05, segment note", scored_on 2026-02-06, result right | 2026-09-18 | scored | the four fields as written; nothing computed, nothing checked against a figure |
| E-2 | event, due 2026-03-01, no score written | 2026-09-18 | due | due since 2026-03-01, awaiting the outcome, which is mine to write; listed, never skipped, never right |
| E-3 | event, due 2027-03-01, no score written (W-1.2's shape) | 2026-09-18 | open | open, due 2027-03-01 |

E-1's outcome text is a stand-in for the shape and not a claim about
Alphabet's segment note; a real written score carries what I read, and no
figure is invented here for one. The scorer copies the fields and computes
nothing.

### E. Falsifier rows

- **F1: before the due date, nothing is scored (D43).** S-1 read as of
  2026-02-28: open, no figure read, no result, though FY2025 was filed on
  2026-02-05. A scorer that scores a filed period ahead of the date fails.
- **F2: on the due date it is due (D43).** S-1 as of 2026-03-01: due and
  scored. A scorer reading "passed" as strictly after fails here.
- **F3: an unfiled period is never wrong (D42).** A revenue prediction,
  min 400,000, period FY2026, due 2026-03-01, as of 2026-09-18: due,
  unscored, reason "FY2026 is not filed by 2026-09-18", no result. A scorer
  that returns wrong, or that reads FY2025 in place of FY2026, fails.
- **F4: a metric with no formula stops (D42).** The same prediction with
  metric `operating_margin`: a stop naming the metric. No result.
- **F5: a filed period missing the field stops (D42, D25).** S-6 over a
  block whose FY2025 carries revenue and no cost_of_revenue: a stop naming
  `cost_of_revenue` for FY2025. No result, not wrong.
- **F6: a written score that disagrees is reported, not repaired (D44).**
  S-2 with a written score, result right, outcome "revenue 410,200", source
  "press release": the record carries the written four fields and the
  filing's verdict, wrong, with its source; the answer says the two differ.
  Nothing is changed and nothing is raised.
- **F7: strict and unrounded (D41).** Revenue min 402,835.999: right.
  Revenue min 402,836.001: wrong. A scorer rounding to the million calls
  both right.
- **F8: the count is the file's (case 4.5).** A ledger of four with one
  record missing from the block is a defect the runner names; the summary's
  four counts sum to the number of predictions on every date in section A.

### F. What Part 14 does not cover

- A prediction on `return_on_invested_capital` or `net_debt_to_ebitda`:
  allowed by D42, no row, since no prediction states one and Alphabet's
  block stops on both (Part 13 B). The row comes with the first prediction.
- A real due prediction: February and March 2027, on Adobe's and
  Alphabet's FY2026 reports, neither filed. Adobe has no facts stored
  (KNOWN_GAPS, "What W-2 needs before it has a range").
- A figure restated between the period's own report and a later filing:
  D29 reads the latest vintage, and no row here has two vintages.
- The score I write into the ledger: its shape is `tests/test_watchlist.py`'s
  and the loader's; nothing here scores my scoring.
