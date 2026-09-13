"""
EDGAR company facts: the figures a company filed, as it filed them.

Reference: tests/golden/expected_values.md Parts 12 and 13, recorded from
fetched documents before this existed. What this module decides:

  D27  A duration fact is annual when `end - start` is 350 to 380 days,
       both included. `fp` is the filing's label and decides nothing. An
       instant is kept whatever its date; matching it to a fiscal year end
       is D28 and not this module's.
  D29  A figure is filed on a 10-K, 10-Q or 8-K or an amendment of one of
       them. A fact on any other form, a proxy statement above all, is not
       a vintage and is not returned.

Every vintage of a kept fact comes back. Which vintage stands (D29's
"latest"), which fiscal year an instant belongs to (D28) and which tag a
field resolves from (D30) are decided downstream, over what this returns.

Only `us-gaap` facts are returned: the block's fields are all there, and the
one `dei` figure anyone has asked about, the cover-page share count, waits
on a decision (Part 13 E7).

Not the price vendor's interface: `DataProviderInterface` has no method this
source can fill.
"""

import datetime as dt
import json
from decimal import Decimal
from typing import List, Optional

import requests

import config
from portfolio_tool.provider_models import ProviderFiledFact


COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

# D27: annual periods measured on three filers are 363 to 370 days; the
# nearest durations that are not a year are 273 and 925.
ANNUAL_DAYS = (350, 380)

# D29: the forms that file a figure.
FILING_FORMS = frozenset({"10-K", "10-K/A", "10-Q", "10-Q/A", "8-K", "8-K/A"})

TAXONOMY = "us-gaap"
TIMEOUT_SECONDS = 30


class EdgarError(Exception):
    """Raised when a company-facts document is not what was asked for."""


def _date(value: Optional[str]) -> Optional[dt.date]:
    return dt.date.fromisoformat(value) if value else None


def _is_annual_or_instant(start: Optional[dt.date], end: dt.date) -> bool:
    if start is None:
        return True
    low, high = ANNUAL_DAYS
    return low <= (end - start).days <= high


class EdgarProvider:
    """Fetches one company's facts from data.sec.gov."""

    name = "EDGAR companyfacts"

    def __init__(self, session: Optional[requests.Session] = None):
        # Read before anything else, so no request leaves without a contact.
        self.user_agent = config.edgar_user_agent()
        self.session = session if session is not None else requests.Session()

    def annual_facts(self, cik: int) -> List[ProviderFiledFact]:
        """Every us-gaap fact for `cik` that is annual or an instant and was
        filed on a form in FILING_FORMS, every vintage of each."""
        response = self.session.get(
            COMPANY_FACTS_URL.format(cik=cik),
            headers={"User-Agent": self.user_agent},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        document = json.loads(response.content, parse_float=Decimal)

        if document.get("cik") != cik:
            raise EdgarError(
                f"Asked for CIK {cik}, and the document is for CIK {document.get('cik')}."
            )

        facts = []
        for tag, entry in document["facts"].get(TAXONOMY, {}).items():
            for unit, rows in entry["units"].items():
                for row in rows:
                    if row["form"] not in FILING_FORMS:
                        continue
                    start, end = _date(row.get("start")), _date(row["end"])
                    if not _is_annual_or_instant(start, end):
                        continue
                    facts.append(ProviderFiledFact(
                        tag=tag,
                        unit=unit,
                        start=start,
                        end=end,
                        value=Decimal(row["val"]),
                        accn=row["accn"],
                        fy=row.get("fy"),
                        fp=row.get("fp"),
                        form=row["form"],
                        filed=_date(row["filed"]),
                        frame=row.get("frame"),
                        source=self.name,
                    ))
        return facts
