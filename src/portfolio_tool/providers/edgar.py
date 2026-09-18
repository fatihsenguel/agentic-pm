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

`filer` fetches the submissions document, which carries what company facts
do not: the filer's name and its SIC code as EDGAR states it, current only,
with no date and no history (Part 13 C). It returns those and nothing else
in the document; `entityType`, `ownerOrg` and `fiscalYearEnd` have no
consumer. A code that is missing or not four digits comes back as None, the
form the screen stops on (D35), rather than guessed at.

`tickers` fetches the SEC's published ticker file, every listed filer's
tickers against its CIK, and returns one record per pair: the forward map a
ticker needs to become a CIK before either document above can be asked for
(decision 29, question 50). The submissions document's own `tickers` list
maps the other way and verifies a CIK; it cannot resolve one. A ticker
naming two CIKs, or an entry without a ticker or a readable CIK, raises:
a map with a hole in it is not the map. The file's company title has no
consumer and is not returned.

`filing` reads the same submissions document for one accession's row in
`filings.recent`, and `document` fetches that filing's primary document from
the archive on www.sec.gov, as bytes (Part 16 H, D55). An accession that
`recent` does not hold is refused stating what the listing holds; the older
files it names are not asked for. What the bytes say is
`portfolio_tool.filing_text`'s to decide, not this module's.

Not the price vendor's interface: `DataProviderInterface` has no method this
source can fill.
"""

import datetime as dt
import json
import re
from decimal import Decimal
from typing import List, Optional

import requests

import config
from portfolio_tool.provider_models import (
    ProviderFiledFact, ProviderFiler, ProviderFiling, ProviderTicker,
)


COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
# The ticker file is served from www.sec.gov, not data.sec.gov, with the same
# contact. URL and shape from memory until the first live fetch records them.
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
# D55: the CIK without padding, the accession without hyphens, the file's name.
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{folder}/{name}"
# The source a stored document states; `name` above is the facts'.
ARCHIVE_NAME = "EDGAR filing archive"

ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")
# D55: a primary document's name as `recent` writes them, a directory allowed.
DOCUMENT_NAME = re.compile(r"^[A-Za-z0-9._/-]+$")
# The columns of `filings.recent` that `filing` reads.
LISTING_COLUMNS = ("accessionNumber", "form", "filingDate", "primaryDocument")

# D27: annual periods measured on three filers are 363 to 370 days; the
# nearest durations that are not a year are 273 and 925.
ANNUAL_DAYS = (350, 380)

# D29: the forms that file a figure.
FILING_FORMS = frozenset({"10-K", "10-K/A", "10-Q", "10-Q/A", "8-K", "8-K/A"})

TAXONOMY = "us-gaap"

# A SIC code is four digits; the screen reads no other form (D35).
SIC_CODE = re.compile(r"^\d{4}$")
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

    def _get(self, url: str) -> bytes:
        response = self.session.get(
            url, headers={"User-Agent": self.user_agent}, timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.content

    def annual_facts(self, cik: int) -> List[ProviderFiledFact]:
        """Every us-gaap fact for `cik` that is annual or an instant and was
        filed on a form in FILING_FORMS, every vintage of each."""
        document = json.loads(self._get(COMPANY_FACTS_URL.format(cik=cik)), parse_float=Decimal)

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

    def _submissions(self, cik: int) -> dict:
        """The submissions document for `cik`, refused when it is another
        company's."""
        document = json.loads(self._get(SUBMISSIONS_URL.format(cik=cik)))

        # The document's `cik` is compared as a number. The company-facts
        # document carries an integer; what form this document carries, and
        # whether it is zero-padded, is EDGAR's to say and the first live
        # fetch's to record, not this module's to assume.
        stated = document.get("cik")
        try:
            stated_cik = int(str(stated))
        except (TypeError, ValueError):
            raise EdgarError(f"Asked for CIK {cik}, and the document states {stated!r} as its CIK.")
        if stated_cik != cik:
            raise EdgarError(f"Asked for CIK {cik}, and the document is for CIK {stated_cik}.")
        return document

    def filer(self, cik: int) -> ProviderFiler:
        """The filer's number, name, SIC code and its description from the
        submissions document, as EDGAR states them today."""
        document = self._submissions(cik)

        name = document.get("name")
        if not isinstance(name, str) or not name:
            raise EdgarError(f"The submissions document for CIK {cik} states no name.")

        sic = document.get("sic")
        if not isinstance(sic, str) or not SIC_CODE.match(sic):
            sic = None
        description = document.get("sicDescription")
        if not isinstance(description, str) or not description:
            description = None

        return ProviderFiler(cik=cik, name=name, sic=sic, sic_description=description)

    def filing(self, cik: int, accn: str) -> ProviderFiling:
        """One accession's row in the submissions document's
        `filings.recent` (D55): its form, its filed date and the name of its
        primary document."""
        if not ACCESSION.match(accn):
            raise EdgarError(f"{accn!r} is not an accession number.")
        document = self._submissions(cik)

        recent = (document.get("filings") or {}).get("recent")
        if not isinstance(recent, dict):
            raise EdgarError(f"The submissions document for CIK {cik} lists no recent filings.")
        columns = {name: recent.get(name) for name in LISTING_COLUMNS}
        unreadable = sorted(name for name, column in columns.items()
                            if not isinstance(column, list))
        if unreadable:
            raise EdgarError(f"The recent filings of CIK {cik} lack {unreadable}.")
        lengths = {len(column) for column in columns.values()}
        if len(lengths) != 1:
            raise EdgarError(f"The recent filings of CIK {cik} are columns of different "
                             f"lengths, {sorted(lengths)}; a row cannot be read across them.")

        rows = [i for i, listed in enumerate(columns["accessionNumber"]) if listed == accn]
        if not rows:
            count = lengths.pop()
            dates = sorted(d for d in columns["filingDate"] if d)
            span = f", filed {dates[0]} to {dates[-1]}" if dates else ""
            raise EdgarError(
                f"Accession {accn} is not among the {count} recent filings the submissions "
                f"document lists for CIK {cik}{span}. The older files it names are not "
                "asked for."
            )
        if len(rows) > 1:
            raise EdgarError(f"The recent filings of CIK {cik} list accession {accn} "
                             f"{len(rows)} times; one accession is one filing.")

        row = rows[0]
        name = columns["primaryDocument"][row]
        if not isinstance(name, str) or not DOCUMENT_NAME.match(name) or ".." in name:
            raise EdgarError(f"Accession {accn} names {name!r} as its primary document, "
                             "which is not a file's name.")
        form = columns["form"][row]
        if not isinstance(form, str) or not form:
            raise EdgarError(f"Accession {accn} is listed without a form.")
        stated = columns["filingDate"][row]
        try:
            filed = dt.date.fromisoformat(stated)
        except (TypeError, ValueError):
            raise EdgarError(f"Accession {accn} is listed as filed on {stated!r}, which is "
                             "not a date.")
        return ProviderFiling(accn=accn, form=form, filed=filed, primary_document=name)

    def document(self, cik: int, accn: str, name: str) -> bytes:
        """A filing's primary document from the archive, as bytes (D55)."""
        if not ACCESSION.match(accn):
            raise EdgarError(f"{accn!r} is not an accession number.")
        if not DOCUMENT_NAME.match(name) or ".." in name:
            raise EdgarError(f"{name!r} is not a file's name.")
        return self._get(ARCHIVE_URL.format(cik=cik, folder=accn.replace("-", ""), name=name))

    def tickers(self) -> List[ProviderTicker]:
        """Every (ticker, CIK) pair the SEC's ticker file states today, one
        record per pair, in file order, each pair once."""
        document = json.loads(self._get(TICKERS_URL))

        # The file is an object keyed by position; the same entries as a
        # list are read too, and the first live fetch records which is sent.
        if isinstance(document, dict):
            entries = list(document.values())
        elif isinstance(document, list):
            entries = document
        else:
            raise EdgarError(f"The ticker file is a {type(document).__name__}, not a "
                             "collection of entries.")
        if not entries:
            raise EdgarError("The ticker file has no entries; an empty map is not the map.")

        records: List[ProviderTicker] = []
        cik_by_ticker = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise EdgarError(f"A ticker file entry is {entry!r}, not an object.")
            ticker = entry.get("ticker")
            if not isinstance(ticker, str) or not ticker:
                raise EdgarError(f"A ticker file entry states no ticker: {entry!r}.")
            try:
                cik = int(str(entry.get("cik_str")))
            except (TypeError, ValueError):
                raise EdgarError(f"The ticker file entry for {ticker} states "
                                 f"{entry.get('cik_str')!r} as its CIK.")
            if ticker in cik_by_ticker:
                if cik_by_ticker[ticker] != cik:
                    raise EdgarError(f"The ticker file names {ticker} for CIK "
                                     f"{cik_by_ticker[ticker]} and for CIK {cik}; one ticker "
                                     "names one filer.")
                continue
            cik_by_ticker[ticker] = cik
            records.append(ProviderTicker(ticker=ticker, cik=cik))
        return records
