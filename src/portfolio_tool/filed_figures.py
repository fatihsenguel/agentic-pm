"""
The fields of the figures block's `years`, and the tags each is filed under.

Reference: tests/golden/expected_values.md Part 12, with Part 13's two more
filers. The field list is D30: each field of the block names an ordered list
of us-gaap tags, and the first that yields a fact for the period wins. It is
a definition, not policy, so it is code and not config; the test
tests/test_filed_fields.py holds it to Part 12 C's table.

A `duration` field is read from an annual fact ending on the fiscal year's
end date, an `instant` field from a fact at that date (D27, D28).
"""

from dataclasses import dataclass
from typing import Tuple


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
