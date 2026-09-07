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
