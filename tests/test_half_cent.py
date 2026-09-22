"""
Decision 75, the exact half cent, held to Part 7 at its own as-of.

A distance to a limit is a currency figure, `market_value - limit * total`
against a ceiling and `limit * total - market_value` against a floor, and
the percentage points beside it are derived from that figure, so the two
numbers on one line are one quantity in two units. Where the figure is
printed it is rounded half-up on a decimal built from it. Part 7 states
five distances in currency at the 2026-09-02 closes and two of them land
on an exact half: IPS-3.1's 18,083.175 is stated 18,083.18 and IPS-4.3's
12,123.875 is stated 12,123.88. Every figure here is Part 7's, transcribed
from the document; if the checker and the Part disagree, the Part does not
move to match the code.

Two later closes add falsifiers that no reference Part carries and that
the record does. The 2026-09-18 closes of Part 17 B, where decision 75's
entry predicts what moves: 18,841.625 stays 18,841.63 and 14,492.125 moves
from 14,492.12 to 14,492.13. The 2026-09-21 closes of the corpus run,
where the transcript shows 19,552.475 printed 19,552.47 and 15,147.375
printed 15,147.38 in one answer, two halves two ways: under the decision
both round up.

The share-first path, `(pct_of_total - limit) * total`, lands on neither
side of a half by rule, only by the order of two float operations; these
tests fail on it as a whole, which is why each is one test over its
figures rather than one test per figure.
"""

from dataclasses import asdict
from decimal import Decimal

import pytest

from agents.nodes import _format_compliance_response
from portfolio_tool.compliance import BREACH, ComplianceError, check
from portfolio_tool.ips import load_ips

from test_compliance import CLASSES, INSTRUMENT_TYPES, SECTORS, TOTAL, allocation


# Part 7's eight breaches at 2026-09-02: the distance in currency as the
# reference computed it, exact, and as it prints it, to the cent.
PART_7 = [
    ("IPS-3.1", "Equity", "max", "18083.175", "18,083.18"),
    ("IPS-4.1", "SPY", "max", "27291.94", "27,291.94"),
    ("IPS-4.1", "AAPL", "max", "15767.94", "15,767.94"),
    ("IPS-4.1", "MSFT", "max", "457.94", "457.94"),
    ("IPS-4.2", "AAPL", "max", "23971.95", "23,971.95"),
    ("IPS-4.2", "MSFT", "max", "8661.95", "8,661.95"),
    ("IPS-4.2", "JNJ", "max", "261.45", "261.45"),
    ("IPS-4.3", "Technology", "max", "12123.875", "12,123.88"),
]

# Part 17 B, the 2026-09-18 closes, total 408,447.50.
CLOSES_09_18 = {
    "SPY": 76_169.00, "AAPL": 67_226.00, "MSFT": 49_378.00, "TLT": 40_625.00,
    "JNJ": 40_498.50, "GLD": 40_117.00, "JPM": 34_967.00, "VNQ": 27_873.00,
    "NEE": 16_094.00,
}
# The corpus run's 2026-09-21 closes (tests/golden/run_corpus_2026-09-22.txt,
# the 2.2 answer), quantity times the close: total 411,238.50.
CLOSES_09_21 = {
    "SPY": 77_350.00, "AAPL": 67_796.00, "MSFT": 50_161.00, "JNJ": 40_420.50,
    "JPM": 35_204.00, "NEE": 15_926.00, "TLT": 40_900.00, "GLD": 39_838.00,
    "VNQ": 28_143.00,
}
CASH = 15_500.00

# (clause, subject, the exact half, what the decision prints)
LATER_HALVES = {
    "2026-09-18": [("IPS-3.1", "Equity", "18841.625", "18,841.63"),
                   ("IPS-4.3", "Technology", "14492.125", "14,492.13")],
    "2026-09-21": [("IPS-3.1", "Equity", "19552.475", "19,552.48"),
                   ("IPS-4.3", "Technology", "15147.375", "15,147.38")],
}


def _allocation_at(market_values, cash, as_of):
    """The block PortfolioAnalysisAgent publishes, from one market value per
    holding, in the shape of test_compliance.allocation()."""
    total = sum(market_values.values()) + cash
    invested = total - cash
    by_ticker = {t: sum(market_values[x] for x in tickers)
                 for t, _, tickers in CLASSES if tickers}
    by_ticker["Cash"] = cash
    sectors = {label: sum(market_values[x] for x in tickers)
               for label, _, tickers in SECTORS}
    sectored = sum(v for label, v in sectors.items() if label != "(no sector)")

    def line(label, value, tickers, of_sectored=None, of_invested=None):
        return {"label": label, "market_value": value, "cost_basis": 0.0,
                "pct_of_sectored": of_sectored, "pct_of_invested": of_invested,
                "pct_of_total": value / total, "tickers": list(tickers)}

    return {
        "by_asset_class": {
            "lines": [line(label, by_ticker[label], tickers,
                           of_invested=(by_ticker[label] / invested if tickers else None))
                      for label, _, tickers in CLASSES],
            "invested_value": invested, "cash_balance": cash, "total_value": total,
        },
        "by_sector": {
            "lines": [line(label, sectors[label], tickers,
                           of_sectored=(sectors[label] / sectored
                                        if label != "(no sector)" else None),
                           of_invested=sectors[label] / invested)
                      for label, _, tickers in SECTORS],
            "invested_value": invested, "sectored_value": sectored, "total_value": total,
        },
        "by_position": {
            "lines": [line(t, v, [t], of_invested=v / invested)
                      for t, v in sorted(market_values.items(), key=lambda kv: -kv[1])],
            "invested_value": invested, "cash_balance": cash, "total_value": total,
        },
        "as_of": {"worst_case": as_of, "stalest": "SPY", "uniform": True},
        "base_currency": "USD",
    }


def _answer(ips, alloc, findings):
    block = {"policy": {c.id: {"type": c.type, "text": c.text} for c in ips},
             "statements": [{"clause": c.id, "text": c.text} for c in ips.statements],
             "total_value": alloc["by_asset_class"]["total_value"],
             "as_of": alloc["as_of"], "base_currency": alloc["base_currency"],
             "findings": [asdict(f) for f in findings], "no_clause": False, "topic": None}
    decision = {"parameters": {"tickers": [], "status": None}}
    return "\n".join(_format_compliance_response(
        decision, {"ComplianceAgent": {"success": True, "compliance": block}}))


@pytest.fixture(scope="module")
def ips():
    return load_ips("ips.toml")


def _by_key(findings):
    return {(f.clause, f.subject, f.bound): f for f in findings}


def test_the_distance_is_the_market_value_less_the_limits_share_of_total(ips):
    """Part 7's eight distances reproduce exactly, as decimals, from the
    market value, and the percentage points are that figure over the total.
    The share-first path misses the two halves by a few billionths of a
    cent, which is the whole defect."""
    keys = _by_key(check(ips, allocation(), INSTRUMENT_TYPES))
    for clause, subject, bound, exact, _ in PART_7:
        f = keys[(clause, subject, bound)]
        assert f.status == BREACH
        assert Decimal(repr(f.distance_value)) == Decimal(exact), (clause, subject)
        assert f.distance_pp == pytest.approx(f.distance_value / TOTAL * 100, abs=1e-9)


def test_a_line_without_a_market_value_raises(ips):
    """The distance is computed from the market value the allocation
    publishes, not divided for from the share; a line carrying none is
    refused, as one carrying no pct_of_total already is."""
    alloc = allocation()
    for line in alloc["by_asset_class"]["lines"]:
        if line["label"] == "Equity":
            del line["market_value"]
    with pytest.raises(ComplianceError, match="Equity.*market_value"):
        check(ips, alloc, INSTRUMENT_TYPES)


def test_part_7s_cents_are_printed(ips):
    """The answer at the 2026-09-02 closes prints each breach's distance as
    Part 7 states it, the two halves rounded up, in both places the
    formatter prints a distance in currency."""
    alloc = allocation()
    answer = _answer(ips, alloc, check(ips, alloc, INSTRUMENT_TYPES))
    for clause, subject, _, _, cents in PART_7:
        assert f"({cents} USD)." in answer, (clause, subject, cents)
        assert f"({cents} USD at unchanged total)." in answer, (clause, subject, cents)


@pytest.mark.parametrize("as_of, market_values", [
    ("2026-09-18", CLOSES_09_18), ("2026-09-21", CLOSES_09_21)])
def test_the_later_halves_round_up(ips, as_of, market_values):
    """Each later day carries two exact halves in one answer; under the
    decision both round up, and the cent the share-first path printed for
    one of them is gone."""
    alloc = _allocation_at(market_values, CASH, as_of)
    findings = check(ips, alloc, INSTRUMENT_TYPES)
    keys = _by_key(findings)
    answer = _answer(ips, alloc, findings)
    for clause, subject, exact, cents in LATER_HALVES[as_of]:
        assert Decimal(repr(keys[(clause, subject, "max")].distance_value)) == Decimal(exact)
        assert f"({cents} USD)." in answer, (as_of, clause, subject, cents)
        assert f"({cents} USD at unchanged total)." in answer, (as_of, clause, subject, cents)
        down = f"{Decimal(exact).quantize(Decimal('0.01')) - Decimal('0.005'):,}"
        assert f"({down} USD" not in answer, (as_of, clause, subject, down)
