# Expected values — Benchmark Portfolio (portfolio_id 3)

Roadmap 0.2. Computed **by hand, before the capabilities exist**, so that when
they do exist there is an independent reference to check them against.

Do not update these numbers to match code output. If the code disagrees, one of
the two is wrong and that has to be resolved deliberately. If a decision below
turns out to be wrong, change the decision, record why, and recompute.

- **Computed on:** ____________
- **Price source:** ____________ (Yahoo Finance web, broker, or the CLI's
  `latest_prices` — if the last, spot-check at least three tickers against an
  independent source and note it, otherwise a systematic price error would be
  inherited by both sides of the comparison)
- **Price as-of date:** ____________

---

## Part 0 — Decisions

These are the point of the exercise. Each one is a choice the code has to encode
somewhere, and it is better made here than accidentally inside an agent.

| # | Decision | Choice | Why |
|---|---|---|---|
| D1 | Allocation by market value or cost basis? | | |
| D2 | Does cash count in the allocation denominator? | | |
| D3 | Are unsectored holdings reported explicitly, or excluded from the sector denominator? | | |
| D4 | Is P&L total return or price return? | | |
| D5 | Volatility on daily or weekly returns? | | |
| D6 | Annualisation factor? | | |
| D7 | Which of the five volatility implementations is canonical? | | |

Notes to help D2 and D3: cash is 15,500.00, which is 5.17% of the 300,000
total. Unsectored cost basis is 147,000.00, which is 51.7% of the 284,500
invested — so D3 is not a rounding decision, it changes every sector percentage
by roughly a factor of two.

---

## Part 1 — Positions

Cost basis is pre-filled: it follows mechanically from the seed data and is
independently verified. Everything right of the double line is yours.

| Ticker | Asset class | Sector | Qty | Avg price | Cost basis ‖ | Current price | Market value | P&L abs | P&L % | Purchase date |
|---|---|---|---|---|---|---|---|---|---|---|
| SPY  | Equity       | —          | 100 | 500.00 | 50,000.00 ‖ | | | | | 2024-01-15 |
| AAPL | Equity       | Technology | 200 | 200.00 | 40,000.00 ‖ | | | | | 2024-02-20 |
| MSFT | Equity       | Technology | 100 | 400.00 | 40,000.00 ‖ | | | | | 2024-03-18 |
| JNJ  | Equity       | Healthcare | 150 | 150.00 | 22,500.00 ‖ | | | | | 2024-05-06 |
| JPM  | Equity       | Financials | 100 | 200.00 | 20,000.00 ‖ | | | | | 2024-07-15 |
| NEE  | Equity       | Utilities  | 200 |  75.00 | 15,000.00 ‖ | | | | | 2024-09-09 |
| TLT  | Fixed Income | —          | 500 |  90.00 | 45,000.00 ‖ | | | | | 2025-01-13 |
| GLD  | Commodity    | —          | 100 | 250.00 | 25,000.00 ‖ | | | | | 2025-03-10 |
| VNQ  | Real Estate  | —          | 300 |  90.00 | 27,000.00 ‖ | | | | | 2025-06-02 |
| **Total** | | | | | **284,500.00** ‖ | | | | | |

Cash: 15,500.00 · Total with cash: 300,000.00

Benchmark case 1.2 asks about one position and requires the purchase date to be
named. Pick one and write the full expected answer out in prose at the bottom
of this file, in the form the output contract demands.

---

## Part 2 — Allocation by asset class

Cost basis is pre-filled and verified. Market value is yours.

| Asset class | Cost basis | % of invested | % of total incl. cash | Market value | % of invested | % of total incl. cash |
|---|---|---|---|---|---|---|
| Equity       | 187,500.00 | 65.91% | 62.50% | | | |
| Fixed Income |  45,000.00 | 15.82% | 15.00% | | | |
| Real Estate  |  27,000.00 |  9.49% |  9.00% | | | |
| Commodity    |  25,000.00 |  8.79% |  8.33% | | | |
| Cash         |  15,500.00 |    n/a |  5.17% | 15,500.00 | n/a | |
| **Total**    | **284,500.00** | **100.00%** | **100.00%** | | | |

Whichever of these D1 and D2 select is the answer case 1.1 must produce.

---

## Part 3 — Allocation by sector

| Sector | Cost basis | % of sectored | % of invested | Market value | % of sectored | % of invested |
|---|---|---|---|---|---|---|
| Technology  | 80,000.00 | 58.18% | 28.12% | | | |
| Healthcare  | 22,500.00 | 16.36% |  7.91% | | | |
| Financials  | 20,000.00 | 14.55% |  7.03% | | | |
| Utilities   | 15,000.00 | 10.91% |  5.27% | | | |
| (no sector) | 147,000.00 |   n/a | 51.67% | | | |

Case 1.4 asks which positions are in a given sector and passes on completeness.
Expected answer for Technology: ____________ (name the positions, not just the
percentage — and note whether a correct answer mentions that half the portfolio
has no sector at all).

---

## Part 4 — Twelve-month portfolio volatility

**Do not average the per-ticker volatilities.** That ignores correlation and
will be wrong. And do not use the covariance matrix the system produced — if
that matrix is wrong, both sides of the comparison inherit the same error.

Easier route than the covariance quadratic form, and mathematically equivalent:
build the portfolio's own return series.

1. Pull 12 months of daily closes for the nine tickers from your price source.
2. Compute portfolio weights from market value (per D1/D2).
3. For each day, portfolio return = sum over positions of weight × that
   position's daily return. One column.
4. Take the standard deviation of that column.
5. Annualise: multiply by the square root of the D6 factor.

In a spreadsheet that is `=STDEV(range) * SQRT(252)` on one column.

- Weights used: ____________
- Trading days in the window: ____________
- Daily std dev: ____________
- **Annualised portfolio volatility: ____________**
- Sample or population std dev (`STDEV.S` or `STDEV.P`): ____________

Sanity check: it should land below the weighted average of the individual
volatilities. If it doesn't, something is wrong. Record the weighted average
here for comparison: ____________

Case 1.3 passes when the basis of calculation is traceable, so the answer has
to carry D5, D6 and the window, not just the number.

---

## Part 5 — Expected answer, written out

For the position chosen in Part 1, write the full expected response in the shape
benchmark.md Part 3b requires: the result in the units asked for, the data age
as an as-of date, the source for any policy claim, and what it did not do.

> ____________

---

## Part 6 — What these values do not cover

- **Price return only, not total return.** Dividends live in a table with no
  `portfolio_id`, so no dividend can be attributed to a portfolio. Any P&L here
  understates actual return on the dividend-paying positions.
- **Single purchase date per position.** `PortfolioHolding` carries one
  `purchase_date` and one `average_price`, which cannot represent a position
  built in tranches. Fine for this synthetic portfolio, where each position was
  a single purchase. Not fine for a real portfolio with savings plans or DRIP.
- **Single currency.** Everything here is USD. There is no FX conversion
  anywhere in the codebase, so these values say nothing about whether a
  multi-currency portfolio would compute correctly.
- **No look-through.** SPY, TLT, GLD and VNQ are treated as having no sector.
  A real sector allocation would decompose SPY into its constituents. Out of
  scope, but it means the sector figures describe the holdings, not the
  underlying economic exposure.
