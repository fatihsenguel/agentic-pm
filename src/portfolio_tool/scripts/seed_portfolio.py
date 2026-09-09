"""
Seed a synthetic portfolio that can actually support the benchmark.

Roadmap 0.1. The existing demo data cannot: portfolio 1 has January
average_price values and sector NULL on every holding, so case 1.4 is
unanswerable against it; portfolio 2 has only two positions, both Technology.

Usage:
    python src/portfolio_tool/scripts/seed_portfolio.py            # create
    python src/portfolio_tool/scripts/seed_portfolio.py --reset    # wipe the ledger first
    python src/portfolio_tool/scripts/seed_portfolio.py --show     # print, write nothing

Writes Asset rows via SQLAlchemy directly: asset_class / sector / industry /
country / instrument_type live on Asset with no API path at all.

DESIGN NOTES — read before changing the numbers.

Synthetic, not real holdings. The repo is public, so real positions and cost
basis would be in git history permanently and in the golden set output.

Deliberately round quantities and prices. Two reasons: roadmap 0.2 requires
hand-computing allocation, P&L and volatility BEFORE the code exists, and round
numbers make that tractable in a spreadsheet; and nobody can mistake 200 shares
at exactly $200.00 for a real cost basis.

Composition is driven by what the benchmark needs, not realism:
  - 4 asset classes (Equity, Fixed Income, Commodity, Real Estate) so 1.1 has
    something to aggregate.
  - Single stocks carry sectors; broad ETFs correctly do not. A portfolio of
    only ETFs makes 1.4 unanswerable no matter how good the code is, because
    SPY / TLT / GLD / VNQ have no meaningful sector.
  - Technology holds TWO positions, so 1.4's "complete, no omissions" is a real
    test rather than a lookup that cannot fail.
  - Purchase dates spread over 18 months so 1.2's P&L varies in sign.
  - cash_balance is non-zero, which forces 0.2's open question: does cash count
    in the allocation denominator?

Cost basis totals 284,500 and cash is 15,500, so the portfolio is 300,000 flat.
Equity is 187,500 of cost basis — 65.9% excluding cash, 62.5% including it.
Those two numbers differing is the point: 0.2 has to decide which one 1.1 means.

THE LEDGER (expected_values.md Part 8 A, 9 September). Each position is
written as one buy row in `transactions`: the purchase date, the quantity,
the price, no fees, amount = quantity x price (D11, D14). Holdings derive
from those rows (D13); there is no holdings table. tests/test_ledger_seed.py
holds the ledger to Part 8 A, and Part 8 A reproduces Part 1.

A rerun without --reset would append nine more buys and double every
position silently, so the seed refuses when the portfolio already has
ledger rows. --reset clears the ledger first.
"""

import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from portfolio_tool.database_setup import (  # noqa: E402
    Asset,
    Portfolio,
    Transaction,
    get_session,
)

PORTFOLIO_NAME = "Benchmark Portfolio"
PORTFOLIO_DESCRIPTION = (
    "Synthetic portfolio for benchmark.md Levels 1-3. Round numbers on purpose; "
    "see seed_portfolio.py for why."
)
CASH_BALANCE = 15_500.00

# ticker, name, asset_class, sector, industry, country, instrument_type, qty, avg_price, purchase_date
#
# instrument_type is 'share' or 'fund' (expected_values.md Part 7): IPS-4.2
# and 4.3 count directly held shares only. It is carried data, not inferred
# from "has no sector", so a share with an unknown sector cannot turn into a
# fund silently.
POSITIONS = [
    ("SPY",  "SPDR S&P 500 ETF Trust",             "Equity",       None,          None,                   "US", "fund",  100, 500.00, "2024-01-15"),
    ("AAPL", "Apple Inc.",                          "Equity",       "Technology",  "Consumer Electronics", "US", "share", 200, 200.00, "2024-02-20"),
    ("MSFT", "Microsoft Corporation",               "Equity",       "Technology",  "Software",             "US", "share", 100, 400.00, "2024-03-18"),
    ("JNJ",  "Johnson & Johnson",                   "Equity",       "Healthcare",  "Pharmaceuticals",      "US", "share", 150, 150.00, "2024-05-06"),
    ("JPM",  "JPMorgan Chase & Co.",                "Equity",       "Financials",  "Banks",                "US", "share", 100, 200.00, "2024-07-15"),
    ("NEE",  "NextEra Energy Inc.",                 "Equity",       "Utilities",   "Electric Utilities",   "US", "share", 200,  75.00, "2024-09-09"),
    ("TLT",  "iShares 20+ Year Treasury Bond ETF",  "Fixed Income", None,          None,                   "US", "fund",  500,  90.00, "2025-01-13"),
    ("GLD",  "SPDR Gold Shares",                    "Commodity",    None,          None,                   "US", "fund",  100, 250.00, "2025-03-10"),
    ("VNQ",  "Vanguard Real Estate ETF",            "Real Estate",  None,          None,                   "US", "fund",  300,  90.00, "2025-06-02"),
]


def summarise():
    """Print what will be written, plus the figures 0.2 has to reproduce by hand."""
    by_class, by_sector, total = {}, {}, 0.0
    for _, _, acls, sector, _, _, _, qty, price, _ in POSITIONS:
        cost = qty * price
        total += cost
        by_class[acls] = by_class.get(acls, 0.0) + cost
        if sector:
            by_sector[sector] = by_sector.get(sector, 0.0) + cost

    print(f"{len(POSITIONS)} positions, {len(by_class)} asset classes, "
          f"{len(by_sector)} sectors")
    print(f"cost basis {total:,.2f}  cash {CASH_BALANCE:,.2f}  "
          f"total {total + CASH_BALANCE:,.2f}\n")

    print("BY ASSET CLASS (cost basis)")
    for name, cost in sorted(by_class.items(), key=lambda kv: -kv[1]):
        print(f"  {name:<14} {cost:>10,.2f}  {cost/total:>6.2%} ex-cash  "
              f"{cost/(total+CASH_BALANCE):>6.2%} inc-cash")

    print("\nBY SECTOR (cost basis; broad ETFs have none)")
    for name, cost in sorted(by_sector.items(), key=lambda kv: -kv[1]):
        print(f"  {name:<14} {cost:>10,.2f}")
    no_sector = total - sum(by_sector.values())
    print(f"  {'(no sector)':<14} {no_sector:>10,.2f}")

    print("\nThese are COST BASIS figures. Market-value allocation needs current")
    print("prices and will differ. 0.2 must decide which one case 1.1 means.")


def seed(reset: bool) -> int:
    session = get_session()
    try:
        portfolio = (
            session.query(Portfolio)
            .filter(Portfolio.name == PORTFOLIO_NAME)
            .one_or_none()
        )
        if portfolio is None:
            portfolio = Portfolio(
                name=PORTFOLIO_NAME,
                description=PORTFOLIO_DESCRIPTION,
                currency="USD",
                cash_balance=CASH_BALANCE,
            )
            session.add(portfolio)
            session.flush()
            print(f"created portfolio id={portfolio.id}")
        else:
            print(f"found portfolio id={portfolio.id}")
            portfolio.description = PORTFOLIO_DESCRIPTION
            portfolio.cash_balance = CASH_BALANCE

        if reset:
            deleted = (
                session.query(Transaction)
                .filter(Transaction.portfolio_id == portfolio.id)
                .delete()
            )
            print(f"  deleted {deleted} existing ledger rows")

        existing_rows = (
            session.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio.id)
            .count()
        )
        if existing_rows:
            raise RuntimeError(
                f"portfolio {portfolio.id} already has {existing_rows} ledger rows; "
                "seeding again would append nine more buys and double every "
                "position. Rerun with --reset."
            )

        for ticker, name, acls, sector, industry, country, kind, qty, price, bought in POSITIONS:
            asset = session.query(Asset).filter(Asset.ticker == ticker).one_or_none()
            if asset is None:
                asset = Asset(ticker=ticker, name=name)
                session.add(asset)
                print(f"  + asset {ticker}")
            else:
                print(f"  = asset {ticker} (updating metadata)")

            # Always (re)write metadata. Portfolio 1's holdings have sector NULL,
            # which is precisely why 1.4 cannot pass against the old demo data.
            asset.name = name
            asset.asset_class = acls
            asset.sector = sector
            asset.industry = industry
            asset.country = country
            asset.currency = "USD"
            asset.instrument_type = kind
            session.flush()

            # The position as its one ledger row (Part 8 A). `amount` is data
            # (D14); here, with one currency and no fees, it is the D11
            # arithmetic.
            purchase_date = datetime.date.fromisoformat(bought)
            session.add(Transaction(
                portfolio_id=portfolio.id,
                asset_id=asset.id,
                date=datetime.datetime.combine(purchase_date, datetime.time()),
                type="buy",
                quantity=qty,
                price_per_unit=price,
                fees=0.0,
                amount=qty * price,
            ))

            print(f"      {qty:>5g} @ {price:>8,.2f}  bought {bought}  "
                  f"{acls}/{sector or '-'}  {kind}")

        session.commit()
        print(f"\ncommitted. run the CLI with --portfolio {portfolio.id}")
        return portfolio.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Seed the benchmark portfolio")
    parser.add_argument("--reset", action="store_true",
                        help="delete this portfolio's existing ledger rows first")
    parser.add_argument("--show", action="store_true",
                        help="print the composition and exit without writing")
    args = parser.parse_args()

    summarise()
    if args.show:
        return
    print()
    seed(args.reset)


if __name__ == "__main__":
    main()
