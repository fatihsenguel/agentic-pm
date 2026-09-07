# Investment Policy Statement — Benchmark Portfolio

**Status.** Synthetic. Written for the benchmark portfolio (portfolio 3) so that
the compliance layer can be built and tested against it. It is the policy the
committed benchmark checks are computed against, the same way portfolio 3 is
the portfolio they are computed against. A personal IPS replaces it later, as
a local file, without changing the code.

**How to read it.** Every clause has an identifier. A compliance check cites
the identifier, not a paraphrase. Percentages are of total portfolio value
including cash, at market value (`expected_values.md` D1 and D2). Where a
clause states a number, it is a rule: a breach is reported as a breach with
the distance to the limit, and is not weighed, softened or explained away.
Where a clause states no number, it is a statement of policy that can be
cited but not computed.

---

## 1. Purpose and horizon

**IPS-1.1** The portfolio is a single long-term investment account with a
horizon of ten years or more. Its purpose is capital growth with a level of
risk the owner can hold through a drawdown without selling.

**IPS-1.2** The portfolio is judged against this document, not against a
market index. Underperforming an index while inside every limit is not a
policy failure. Being outside a limit while outperforming is.

## 2. Permitted instruments

**IPS-2.1** The portfolio holds only exchange-listed equities and
exchange-traded funds, plus cash. Individual bonds, options, futures, leveraged
or inverse products, private investments and digital assets are not held.

**IPS-2.2** No position is held on margin. No borrowing against the portfolio.

## 3. Strategic allocation

Limits are on the share of total portfolio value. A breach of either bound is
a breach.

**IPS-3.1** Equity, including equity index funds: no less than 40% and no more
than 65%.

**IPS-3.2** Fixed income: no less than 8% and no more than 30%.

**IPS-3.3** Commodities: no more than 15%.

**IPS-3.4** Real estate: no more than 15%.

**IPS-3.5** Cash: no less than 3%.

## 4. Concentration

**IPS-4.1** No single instrument exceeds 12% of total portfolio value. This
applies to every holding, funds included: a fund is one instrument regardless
of what it holds.

**IPS-4.2** No single issuer exceeds 10% of total portfolio value. Exposure to
an issuer is counted through directly held shares only; a diversified index
fund is not attributed to its constituents.

**IPS-4.3** No single sector, counted over directly held shares, exceeds 25%
of total portfolio value. Holdings without a sector — index funds, bond funds,
commodity and real-estate funds — are outside this count and are reported as
unsectored.

## 5. Rebalancing

**IPS-5.1** The portfolio is checked against sections 3 and 4 at least
quarterly and after any purchase or sale.

**IPS-5.2** When a limit is breached, the required change is the amount that
returns the figure to the limit — not to the midpoint of a band and not to a
target the policy does not state. What must change is stated as a condition
on the portfolio; which instruments to trade to meet it is not decided by this
document.

**IPS-5.3** New money is allocated first to whatever restores a breached
limit, then to whichever asset class is furthest below the middle of its band.

## 6. Review

**IPS-6.1** This document is reviewed once a year and after any change in the
owner's circumstances. A change to a number in sections 3 or 4 is a policy
change and is dated.

**IPS-6.2** A position that has drifted outside a limit through market
movement alone is not a policy failure; leaving it there past the next
quarterly check is.
