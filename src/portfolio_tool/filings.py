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
"""

import datetime as dt
from decimal import Decimal
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from portfolio_tool.data_manager import load_config
from portfolio_tool.database_setup import FiledFact, FiledFetchMetadata, Filer


INTERVAL_KEY = "filings_fetch_interval_days"


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
