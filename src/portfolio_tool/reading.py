"""
The reading record, pure (cases 4.3 and 4.4; DIRECTION.md invariants 1
and 3; expected_values.md Part 15, D47 and A).

A reading tool returns a summary with its source and its uncertainty as
fields, never the document. This module is the half of it that is code:
given the section's text as stored, the filing it came from, and the
claims a model supplied, it returns the record or refuses the reading.
It calls no model, fetches nothing and stores nothing; the text is an
argument and does not appear in what is returned.

What is held, by code and not by the model: the filing is a 10-K and the
section one of Item 1, Item 1A and Item 7; a reading carries between one
and twelve claims; a claim is one sentence with no digit in it, so a
figure appears only inside a quote, where it is the filing's with its
source; the quote is at most 300 characters and is a substring of the
section once runs of whitespace on both sides collapse to one space,
nothing else normalised, not case and not punctuation; the uncertainty is
`stated` or `inferred`. The record keeps the quote in that collapsed form
and numbers the claims itself, the section and the claim's place in it.

One claim that fails refuses the whole reading with a ReadingError naming
the claim and the reason. A failed claim is not dropped and the rest
kept: that is repair, and a reading that invents one quote is not read.
"""

import datetime as dt
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple

__all__ = ["Claim", "Reading", "ReadingError", "FORM", "SECTIONS", "UNCERTAINTIES",
           "QUOTE_CAP", "CLAIMS_CAP", "record"]

FORM = "10-K"
SECTIONS = ("Item 1", "Item 1A", "Item 7")
UNCERTAINTIES = ("stated", "inferred")
QUOTE_CAP = 300
CLAIMS_CAP = 12
# What a model supplies for a claim. An id, a figure or a source from the
# model is refused: the record numbers the claims and the filing is the
# caller's, read from the store.
SUPPLIED = {"claim", "quote", "uncertainty"}
_FILING = ("form", "accn", "filed", "fiscal_year", "source")
_DIGIT = re.compile(r"\d")


class ReadingError(Exception):
    """Raised when a reading cannot honestly be recorded."""


@dataclass(frozen=True)
class Claim:
    id: str
    claim: str
    quote: str
    uncertainty: str


@dataclass(frozen=True)
class Reading:
    form: str
    accn: str
    filed: dt.date
    fiscal_year: str
    source: str
    section: str
    claims: Tuple[Claim, ...]


def _collapsed(text: str) -> str:
    return " ".join(text.split())


def record(filing: Mapping[str, Any], section: str, text: str,
           supplied: Sequence[Mapping[str, Any]]) -> Reading:
    """The reading of one section as a record (D47), or a ReadingError."""
    missing = [k for k in _FILING if not filing.get(k)]
    if missing:
        raise ReadingError(f"the filing lacks {missing}; a reading names its source.")
    if filing["form"] != FORM:
        raise ReadingError(f"the filing is a {filing['form']}, not a {FORM}; no other form "
                           "is read.")
    if section not in SECTIONS:
        raise ReadingError(f"{section!r} is not a section that is read; the sections are "
                           f"{', '.join(SECTIONS)}.")
    body = _collapsed(text or "")
    if not body:
        raise ReadingError(f"{section}: the stored section is empty; nothing was read.")
    if not isinstance(supplied, (list, tuple)) or not 1 <= len(supplied) <= CLAIMS_CAP:
        count = len(supplied) if isinstance(supplied, (list, tuple)) else supplied
        raise ReadingError(f"{section}: {count!r} claims; a reading carries between 1 and "
                           f"{CLAIMS_CAP}.")

    label = section.split(" ", 1)[1]
    claims = []
    for n, entry in enumerate(supplied, start=1):
        where = f"{section}, claim {n}"
        if not isinstance(entry, Mapping):
            raise ReadingError(f"{where}: not a claim.")
        extra = sorted(set(entry) - SUPPLIED)
        if extra:
            raise ReadingError(f"{where}: supplies {extra}; a claim is {sorted(SUPPLIED)}.")
        sentence, quote = entry.get("claim"), entry.get("quote")
        if not isinstance(sentence, str) or not sentence.strip():
            raise ReadingError(f"{where}: no sentence.")
        if _DIGIT.search(sentence):
            raise ReadingError(f"{where}: a digit in the claim; a figure appears only inside "
                               "a quote, where it is the filing's.")
        if not isinstance(quote, str) or not quote.strip():
            raise ReadingError(f"{where}: no quote; a claim without its source is tone.")
        quote = _collapsed(quote)
        if len(quote) > QUOTE_CAP:
            raise ReadingError(f"{where}: a quote of {len(quote)} characters; the cap is "
                               f"{QUOTE_CAP}, and a record is not the document.")
        if quote not in body:
            raise ReadingError(f"{where}: the quote is not in the section: {quote!r}.")
        if entry.get("uncertainty") not in UNCERTAINTIES:
            raise ReadingError(f"{where}: uncertainty {entry.get('uncertainty')!r} is not one "
                               f"of {', '.join(UNCERTAINTIES)}.")
        claims.append(Claim(id=f"{label}.{n}", claim=sentence.strip(), quote=quote,
                            uncertainty=entry["uncertainty"]))
    return Reading(form=filing["form"], accn=filing["accn"], filed=filing["filed"],
                   fiscal_year=filing["fiscal_year"], source=filing["source"],
                   section=section, claims=tuple(claims))
