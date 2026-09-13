"""
The figures block's `years`, from filed facts.

Reference: tests/golden/expected_values.md Part 12, with Part 13's two more
filers. The field list is D30: each field of the block names an ordered list
of us-gaap tags, and the first that yields a fact for the period wins. It is
a definition, not policy, so it is code and not config; the test
tests/test_filed_fields.py holds it to Part 12 C's table.

`filed_years` reads the EDGAR provider's records into fiscal years (D21,
D28), each field's latest vintage as of a date (D29), and the fields no tag
yields, named and not filled (D30). A `duration` field is read from an annual
fact ending on the year's end date, an `instant` field from a fact at that
date. It builds the `years` half only: the price, the shares and the
valuation range are not filed facts. Its output is not yet the screen's
input: quant/fundamentals.py reads one `tax_rate` and one `debt`, which D32
and D33 keep out of the block.
"""

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class Field:
    name: str
    kind: str
    tags: Tuple[str, ...]


# Part 12 C, in its order. The revenue list is newest tag first for Apple;
# for FY2017 all three carry the same value and the order decides which
# filing the row cites, never which number it reports.
FIELDS: Tuple[Field, ...] = (
    Field("revenue", "duration", (
        "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "Revenues")),
    Field("gross_profit", "duration", ("GrossProfit",)),
    Field("operating_income", "duration", ("OperatingIncomeLoss",)),
    Field("effective_tax_rate", "duration", ("EffectiveIncomeTaxRateContinuingOperations",)),
    Field("depreciation_amortisation", "duration", (
        "DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet")),
    Field("operating_cash_flow", "duration", ("NetCashProvidedByUsedInOperatingActivities",)),
    Field("capex", "duration", ("PaymentsToAcquirePropertyPlantAndEquipment",)),
    Field("equity", "instant", ("StockholdersEquity",)),
    Field("cash", "instant", ("CashAndCashEquivalentsAtCarryingValue",)),
    Field("marketable_securities_current", "instant", ("MarketableSecuritiesCurrent",)),
    Field("marketable_securities_noncurrent", "instant", ("MarketableSecuritiesNoncurrent",)),
    Field("commercial_paper", "instant", ("CommercialPaper",)),
    Field("long_term_debt_current", "instant", ("LongTermDebtCurrent",)),
    Field("long_term_debt_noncurrent", "instant", ("LongTermDebtNoncurrent",)),
)


# --- the years -----------------------------------------------------------------

ANNUAL_REPORT_FORMS = frozenset({"10-K", "10-K/A"})

# D28: a year end closer than this to the previous one is a change of fiscal
# year, and the assembler does not guess which year is which.
MIN_DAYS_BETWEEN_YEAR_ENDS = 350


class FiledFiguresError(Exception):
    """Raised when filed facts cannot honestly be read as fiscal years."""


def _own_reports(facts, as_of):
    """Each fiscal year's own annual report, by year end (D21, Part 12 A).

    A filing's own year is the latest year end it carries an annual fact for;
    a year's own report is the earliest-filed 10-K or 10-K/A whose own year it
    is. A year no filing reports as its own is not a year (F11)."""
    own_year, first_fact = {}, {}
    for fact in facts:
        if fact.start is None or fact.form not in ANNUAL_REPORT_FORMS or fact.filed > as_of:
            continue
        if fact.accn not in own_year or fact.end > own_year[fact.accn]:
            own_year[fact.accn] = fact.end
        first_fact.setdefault(fact.accn, fact)

    reports = {}
    for accn, end in own_year.items():
        fact = first_fact[accn]
        current = reports.get(end)
        if current is None or (fact.filed, accn) < (current.filed, current.accn):
            reports[end] = fact
    return reports


def filed_years(facts: Iterable, as_of: dt.date) -> Dict[str, object]:
    """The `years` half of the figures block from filed facts, as of `as_of`.

    `facts` are the EDGAR provider's records (D27 and D29's forms already
    applied), every vintage. Returns the currency, the as-of date, the years
    by label with their end and filed dates and figures, each figure's
    provenance, and the fields no tag yielded (D30), each with the tags tried.
    Figures are Decimals, as filed.
    """
    facts = list(facts)
    reports = _own_reports(facts, as_of)

    ends = sorted(reports)
    for earlier, later in zip(ends, ends[1:]):
        if (later - earlier).days < MIN_DAYS_BETWEEN_YEAR_ENDS:
            raise FiledFiguresError(
                f"Year ends {earlier} and {later} are {(later - earlier).days} days apart; "
                "a change of fiscal year is not read as two years."
            )

    labels = {}
    for end in ends:
        report = reports[end]
        if report.fy is None:
            raise FiledFiguresError(f"The annual report {report.accn} for {end} carries no fy.")
        label = f"FY{report.fy}"
        if label in labels.values():
            raise FiledFiguresError(f"{label} is the label of two year ends; the filer's years "
                                    "cannot be told apart.")
        labels[end] = label

    by_tag: Dict[str, list] = {}
    for fact in facts:
        if fact.filed <= as_of:
            by_tag.setdefault(fact.tag, []).append(fact)

    years: Dict[str, Dict[str, object]] = {}
    provenance: Dict[str, Dict[str, Dict[str, object]]] = {}
    unresolved: List[Dict[str, object]] = []
    currencies = set()

    for end in ends:
        label = labels[end]
        year = {"ends": end, "filed": reports[end].filed}
        sources = {}
        for field in FIELDS:
            chosen = None
            for tag in field.tags:
                candidates = [f for f in by_tag.get(tag, ())
                              if f.end == end and (f.start is None) == (field.kind == "instant")]
                if candidates:
                    chosen = _latest(candidates, field.name, label)
                    break
            if chosen is None:
                unresolved.append({"year": label, "field": field.name, "tags": field.tags})
                continue
            year[field.name] = chosen.value
            sources[field.name] = {"tag": chosen.tag, "accn": chosen.accn,
                                   "form": chosen.form, "filed": chosen.filed}
            if chosen.unit != "pure":
                currencies.add(chosen.unit)
        years[label] = year
        provenance[label] = sources

    if len(currencies) > 1:
        raise FiledFiguresError(
            f"Figures are filed in {len(currencies)} currency units ({sorted(currencies)}); "
            "a block has one reporting currency."
        )

    return {
        # None only when no field resolved in a currency at all, which leaves
        # nothing for a currency to describe; never a guessed one.
        "currency": next(iter(currencies)) if currencies else None,
        "as_of": as_of,
        "years": years,
        "provenance": provenance,
        "unresolved": unresolved,
    }


def _latest(candidates, field: str, label: str):
    """D29: the latest vintage; two different values filed the same day raise."""
    newest = max(f.filed for f in candidates)
    same_day = [f for f in candidates if f.filed == newest]
    if len({(f.value, f.unit) for f in same_day}) > 1:
        raise FiledFiguresError(
            f"{label} {field}: {len(same_day)} different figures were filed on {newest} "
            f"({', '.join(sorted(f.accn for f in same_day))}); neither is taken."
        )
    return max(same_day, key=lambda f: f.accn)


def filed_years_for(session, cik: int, as_of: dt.date) -> Dict[str, object]:
    """`filed_years` over the rows filed_facts holds for `cik`, each value read
    back from its text as a Decimal."""
    from portfolio_tool.database_setup import FiledFact
    from portfolio_tool.provider_models import ProviderFiledFact

    rows = session.query(FiledFact).filter(FiledFact.cik == cik).all()
    return filed_years(
        (ProviderFiledFact(tag=r.tag, unit=r.unit, start=r.start, end=r.end,
                           value=Decimal(r.value), accn=r.accn, fy=r.fy, fp=r.fp,
                           form=r.form, filed=r.filed, frame=r.frame, source=r.source)
         for r in rows),
        as_of,
    )
