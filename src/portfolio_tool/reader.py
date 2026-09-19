"""
A reading of one section of a filer's latest annual report
(expected_values.md Part 15 D47; Part 16 D54 to D57).

The path, in order: the filing off the stored facts (D54) and its fiscal
year, the facts' one `fy` under that accession; the document's text,
fetched and stored once (D55, D51); the section (D52); the reading cached
under the accession, the section, the model's id and the prompt's version
(D57), or else one request to the model (D56); and what the model supplied
through `reading.record` against the section's text (D47). A reading is
stored only after the record accepts it, and a stored one is held to the
record again each time it is read.

The model is passed in, so this module calls none itself and a test stands
one in; it asks the model only `read(section, prompt, schema, text)` and its
`id`. The prompt is fixed per section and never carries the question asked;
the request carries nothing but the prompt and the section. What comes back
is the record, never the document: the section's text is an argument to
`reading.record` and is not in what it returns.
"""

import datetime as dt
import hashlib
import json

from sqlalchemy.orm import Session

from portfolio_tool import filings, reading, sections
from portfolio_tool.database_setup import DocumentReading, FiledFact

__all__ = ["COMMON", "PROMPTS", "SCHEMA", "prompt_version", "read"]

# What every section's prompt says, before what is particular to the section.
COMMON = """You are reading one section of a company's annual report on Form 10-K, \
filed with the U.S. Securities and Exchange Commission. The section is the \
whole of the user's message; nothing else about the company, and nothing about \
why the section is being read, is given.

Return between one and twelve claims about what the section says. Each claim \
has three parts.

claim: one sentence in your own words. It contains no digits and no number \
written in words: no amount, percentage, year, date or count. Where a figure \
matters, it belongs in the quote.

quote: a passage copied from the section exactly, character for character, \
that supports the claim, at most 250 characters long; where the passage that \
supports it is longer, quote the one sentence that says it. Take it from within \
one paragraph. Do not join text from two paragraphs, do not shorten it with an \
ellipsis, and do not change case, spelling or punctuation. A page number, the \
words "Table of Contents" and the company's name standing alone on their own \
lines mark a page break: never quote across one.

uncertainty: "stated" when the quoted passage says the claim in so many words; \
"inferred" when the claim is your reading of what the section implies or of \
more than one passage.

Say only what the section says. Add nothing from outside it, do not judge \
whether the company is a good investment, and do not say what its share price \
will do."""

PROMPTS = {
    "Item 1": COMMON + """

This section is Item 1, Business. Say what the company sells and to whom, how \
it earns its revenue, why its customers keep buying, and what the section says \
could make them stop.""",
    "Item 1A": COMMON + """

This section is Item 1A, Risk Factors. Say which risks the section describes \
as most able to harm the business or its results, and through what mechanism, \
as the section puts it.""",
    "Item 7": COMMON + """

This section is Item 7, Management's Discussion and Analysis. Say what \
management states drove the year's results; which way revenue, costs, margins \
and capital spending moved, and why; and what it says about its segments and \
its liquidity. A direction and its cause belong in the claim; the figure stays \
in the quote.""",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "quote": {"type": "string"},
                    "uncertainty": {"type": "string", "enum": list(reading.UNCERTAINTIES)},
                },
                "required": ["claim", "quote", "uncertainty"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["claims"],
    "additionalProperties": False,
}


def prompt_version(section: str) -> str:
    """The SHA-256, in hex, of the section's prompt followed by the schema
    as JSON with its keys sorted (D57)."""
    signed = PROMPTS[section] + json.dumps(SCHEMA, sort_keys=True)
    return hashlib.sha256(signed.encode("utf-8")).hexdigest()


def _fiscal_year(session: Session, cik: int, accn: str) -> str:
    years = sorted({fy for (fy,) in session.query(FiledFact.fy).filter(
        FiledFact.cik == cik, FiledFact.accn == accn).distinct()})
    if len(years) != 1 or years[0] is None:
        raise filings.FiledFactsError(
            f"CIK {cik}: the stored facts under accession {accn} carry the fiscal years "
            f"{years}, not one; the reading names none, and nothing is fetched."
        )
    return f"FY{years[0]}"


def read(session: Session, provider, model, cik: int, as_of: dt.date,
         section: str) -> reading.Reading:
    """The reading of `section` of `cik`'s latest annual report filed by
    `as_of`, as a record (D47), or a refusal naming why."""
    if section not in PROMPTS:
        raise reading.ReadingError(f"{section!r} is not a section that is read; the sections "
                                   f"are {', '.join(reading.SECTIONS)}.")
    report = filings.latest_annual_report(session, cik, as_of)
    fiscal_year = _fiscal_year(session, cik, report.accn)
    document = filings.stored_document(session, provider, cik, report.accn)
    text = sections.section(document.text, section)

    key = (report.accn, section, model.id, prompt_version(section))
    stored = session.get(DocumentReading, key)
    if stored is not None:
        supplied = json.loads(stored.claims)
    else:
        supplied = model.read(section, PROMPTS[section], SCHEMA, text)

    filing = {"form": report.form, "accn": report.accn, "filed": report.filed,
              "fiscal_year": fiscal_year, "source": document.source}
    record = reading.record(filing, section, text, supplied)

    if stored is None:
        session.add(DocumentReading(accn=key[0], section=key[1], model=key[2],
                                    prompt_version=key[3],
                                    claims=json.dumps(supplied, ensure_ascii=False)))
        session.commit()
    return record
