"""
Filed facts: the EDGAR provider's records stored under a cache rule.

The same shape as the rate fetch beside the price fetch, with one difference:
one company-facts document is the company's whole history, so the record
keeps only when a company was last fetched (filed_fetch_metadata), and that
time is also the pull date an answer states. Within
filings_fetch_interval_days the provider is not asked.

Every fact the provider returns is stored, not only the tags a field list
names: the lists are still open (expected_values.md Part 13 E), and storing
named tags alone would need a rule to fetch again past the interval whenever
a list changed.

A fact already stored under its key (D26, `(tag, start, end, accn)` per
company) is not stored again. The same key with a different value or unit
raises and nothing from that fetch is stored: one filing's figure never
changes, so a difference is a defect upstream, not a vintage. A restatement
arrives under a new accession and is a new row. A provider that fails
leaves no rows and no record, so the next call asks again.

The filer (filers): the name and the SIC code from the submissions
document, under the same interval. The document carries the current code
only, no date and no history, so the row is the document as of its pull:
a fetch past the interval rewrites the row as the document now states it
and moves `pulled_at`, whether or not the code changed. A code the document
does not state is stored empty, the fact EDGAR states; the screen stops on
it (D35). `pulled_at` is on the clock `last_fetch_time` is on, so a block
built from both records carries one clock; which clock a pull date is on
is decided where an answer first prints one (KNOWN_GAPS, the UTC entry).

The ticker file (ticker_ciks): every (ticker, CIK) pair the SEC's published
file states, under the same interval (decision 29, question 50). The file
is one document, so a fetch past the interval rewrites the whole table as
the file now states it and moves every row's date; a ticker the file
dropped leaves with it. `cik_for` resolves a ticker through that table,
fetching first when it is stale or empty, and raises on a ticker the file
does not list: never asked is not the same as EDGAR listing no filer.
`pulled_at` is on the same clock as the other two records.

A filing's document (filed_documents): the text of one accession's primary
document, stored once and under no interval, since an accession never
changes (expected_values.md Part 16). `latest_annual_report` names the
filing to read off the stored facts (D54): the latest 10-K filed by a date,
refused when a 10-K/A follows it. `stored_document` returns the stored row
without asking the provider, and otherwise asks for the accession's row in
the recent listing, holds its form and filed date to the facts', asks for
the document, extracts its text and stores it (D55, D51). Anything that
fails on the way leaves no row, so the next call asks again. The text is
read from the row by the sectioner; it is returned to no agent and
published nowhere.
"""

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from portfolio_tool import filing_text
from portfolio_tool.data_manager import load_config
from portfolio_tool.database_setup import (
    FiledDocument, FiledFact, FiledFetchMetadata, Filer, TickerCik,
)
from portfolio_tool.providers.edgar import ARCHIVE_NAME


INTERVAL_KEY = "filings_fetch_interval_days"
# D54: the form that is read, and the form that refuses when it follows.
ANNUAL_REPORT = "10-K"
AMENDMENT = "10-K/A"


class FiledFactsError(Exception):
    """Raised when stored facts and a fetch cannot both be true."""


def _interval_days() -> int:
    data_fetch = load_config().get("data_fetch", {})
    if INTERVAL_KEY not in data_fetch:
        raise FiledFactsError(
            f"config.toml [data_fetch] has no {INTERVAL_KEY}; the filings fetch "
            "interval is policy and has no default in code."
        )
    return data_fetch[INTERVAL_KEY]


Key = Tuple[str, Optional[dt.date], dt.date, str]


def update_filed_facts(session: Session, provider, cik: int) -> int:
    """Fetch `cik`'s facts unless fetched within the interval, and store the
    ones not yet stored. Returns the number of rows added."""
    interval = _interval_days()
    now = dt.datetime.utcnow()

    record = session.get(FiledFetchMetadata, cik)
    if record is not None and (now - record.last_fetch_time).days < interval:
        return 0

    facts = provider.annual_facts(cik)

    stored: Dict[Key, Tuple[str, Decimal]] = {
        (row.tag, row.start, row.end, row.accn): (row.unit, Decimal(row.value))
        for row in session.query(FiledFact).filter(FiledFact.cik == cik)
    }

    new_rows = []
    for fact in facts:
        key = (fact.tag, fact.start, fact.end, fact.accn)
        if key in stored:
            unit, value = stored[key]
            if unit != fact.unit or value != fact.value:
                raise FiledFactsError(
                    f"CIK {cik}: {fact.tag} for {fact.start or 'the instant'} to "
                    f"{fact.end} in {fact.accn} is stored as {value} {unit} and was "
                    f"returned as {fact.value} {fact.unit}. One filing's figure does "
                    "not change; nothing from this fetch is stored."
                )
            continue
        stored[key] = (fact.unit, fact.value)
        new_rows.append(FiledFact(
            cik=cik, tag=fact.tag, unit=fact.unit, start=fact.start, end=fact.end,
            value=str(fact.value), accn=fact.accn, fy=fact.fy, fp=fact.fp,
            form=fact.form, filed=fact.filed, frame=fact.frame, source=fact.source,
        ))

    if record is None:
        record = FiledFetchMetadata(cik=cik, last_fetch_time=now)
        session.add(record)
    else:
        record.last_fetch_time = now
    session.add_all(new_rows)
    session.commit()
    return len(new_rows)


def update_filer(session: Session, provider, cik: int) -> Filer:
    """Fetch `cik`'s submissions document unless fetched within the interval,
    and store the filer as it states it. Returns the stored row."""
    interval = _interval_days()
    now = dt.datetime.utcnow()

    row = session.get(Filer, cik)
    if row is not None and (now - row.pulled_at).days < interval:
        return row

    stated = provider.filer(cik)

    if row is None:
        row = Filer(cik=cik)
        session.add(row)
    row.name = stated.name
    row.sic = stated.sic
    row.sic_description = stated.sic_description
    row.pulled_at = now
    session.commit()
    return row


def update_ticker_ciks(session: Session, provider) -> int:
    """Fetch the SEC's ticker file unless fetched within the interval, and
    store it whole: every row rewritten as the file now states it, every
    date moved. Returns the number of rows the table holds after a fetch,
    0 when the table was not asked again."""
    interval = _interval_days()
    now = dt.datetime.utcnow()

    latest = session.query(func.max(TickerCik.pulled_at)).scalar()
    if latest is not None and (now - latest).days < interval:
        return 0

    stated = provider.tickers()

    session.query(TickerCik).delete()
    session.add_all(TickerCik(ticker=t.ticker, cik=t.cik, pulled_at=now) for t in stated)
    session.commit()
    return len(stated)


def cik_for(session: Session, provider, ticker: str) -> int:
    """The CIK the SEC's ticker file names for `ticker`, through the cache.
    Raises FiledFactsError on a ticker the file does not list."""
    update_ticker_ciks(session, provider)
    asked = ticker.strip().upper()
    row = session.get(TickerCik, asked)
    if row is None:
        raise FiledFactsError(
            f"{asked}: the SEC's ticker file lists no filer under this ticker, so there is "
            "no CIK to ask EDGAR about. A company is screened by the filings it made."
        )
    return row.cik


@dataclass(frozen=True)
class AnnualReport:
    """The filing a reading reads, as the stored facts name it (D54)."""
    accn: str
    form: str
    filed: dt.date


def _filings_in_facts(session: Session, cik: int, *criteria):
    return session.query(FiledFact.accn, FiledFact.form, FiledFact.filed).filter(
        FiledFact.cik == cik, *criteria).distinct().all()


def latest_annual_report(session: Session, cik: int, as_of: dt.date) -> AnnualReport:
    """`cik`'s latest 10-K filed by `as_of`, read off the stored facts (D54).
    Fetches nothing. Raises FiledFactsError when the facts name no 10-K, two
    filed on one day, or a 10-K/A filed on or after the latest one."""
    listed = _filings_in_facts(session, cik, FiledFact.filed <= as_of,
                               FiledFact.form.in_((ANNUAL_REPORT, AMENDMENT)))
    reports = [row for row in listed if row.form == ANNUAL_REPORT]
    if not reports:
        raise FiledFactsError(
            f"CIK {cik}: the stored facts name no {ANNUAL_REPORT} filed by {as_of}. A filer "
            f"with no {ANNUAL_REPORT} is not read; no other form is."
        )
    filed = max(row.filed for row in reports)
    latest = sorted(row.accn for row in reports if row.filed == filed)
    if len(latest) > 1:
        raise FiledFactsError(
            f"CIK {cik}: the stored facts name {len(latest)} {ANNUAL_REPORT} filings filed on "
            f"{filed}, {' and '.join(latest)}; which is the latest is not decided, and "
            "neither is read."
        )
    amended = sorted((row.filed, row.accn) for row in listed
                     if row.form == AMENDMENT and row.filed >= filed)
    if amended:
        when, accn = amended[-1]
        raise FiledFactsError(
            f"CIK {cik}: {AMENDMENT} {accn}, filed {when}, follows the latest "
            f"{ANNUAL_REPORT}, {latest[0]}, filed {filed}. Which text stands is not "
            "decided, and neither is read."
        )
    return AnnualReport(accn=latest[0], form=ANNUAL_REPORT, filed=filed)


def stored_document(session: Session, provider, cik: int, accn: str) -> FiledDocument:
    """The stored text of `accn`'s primary document, fetched and stored on
    the first call and never again (D55). The row's text is the sectioner's
    to read and nobody's to publish."""
    row = session.get(FiledDocument, accn)
    if row is not None:
        return row

    known = {(form, filed) for _, form, filed in
             _filings_in_facts(session, cik, FiledFact.accn == accn)}
    if not known:
        raise FiledFactsError(
            f"CIK {cik}: no stored fact carries accession {accn}. A document is fetched "
            "for a filing the facts name, and for no other."
        )
    if len(known) > 1:
        raise FiledFactsError(
            f"CIK {cik}: the stored facts give accession {accn} as {sorted(known)}; one "
            "filing has one form and one date."
        )
    form, filed = known.pop()

    listed = provider.filing(cik, accn)
    if (listed.form, listed.filed) != (form, filed):
        raise FiledFactsError(
            f"CIK {cik}: accession {accn} is a {form} filed {filed} in the stored facts and "
            f"a {listed.form} filed {listed.filed} in the submissions document. Two EDGAR "
            "documents disagree about one filing; its document is not fetched."
        )

    text = filing_text.text_of(provider.document(cik, accn, listed.primary_document))
    if not text:
        raise FiledFactsError(f"CIK {cik}: the document of accession {accn} yields no text; "
                              "nothing is stored.")

    row = FiledDocument(accn=accn, text=text, source=ARCHIVE_NAME)
    session.add(row)
    session.commit()
    return row
