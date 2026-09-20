"""
The reading record held to expected_values.md Part 15 A (D47): the rules
that hold a model's claims to the stored section, each row of the table on
the Part's stand-in section, the caps, and the refusal of a whole reading
on one failed claim.

The section is the Part's, line breaks included. It is no filer's words.
No model is called anywhere here: the claims are typed in, as the Part's
rows are.

The module is imported inside a fixture so that, before it exists, this
file is a list of errors and not an interrupted suite.
"""

import datetime as dt

import pytest

SECTION = ("The company sells subscriptions to software it has already written.\n"
           "Customers renew because their work lives in the files.\n"
           "Revenue from subscriptions was 1,234 million in the year, and the\n"
           "company expects competition from new tools to increase.")

FILING = {"form": "10-K", "accn": "0001652044-26-000018", "filed": dt.date(2026, 2, 5),
          "fiscal_year": "FY2025", "source": "EDGAR"}

R1 = {"claim": "The business is subscription software that customers keep renewing.",
      "quote": "Customers renew because their work lives in the files.", "uncertainty": "stated"}
R2 = {"claim": "Renewals and subscription revenue are described together.",
      "quote": "lives in the files. Revenue from subscriptions", "uncertainty": "inferred"}
R3 = {"claim": "The filing states the year's subscription revenue.",
      "quote": "Revenue from subscriptions was 1,234 million in the year", "uncertainty": "stated"}
R4 = {"claim": "Subscription revenue was 1,234 million.",
      "quote": "Revenue from subscriptions was 1,234 million in the year", "uncertainty": "stated"}
R5 = {"claim": "Customers renew because of their files.",
      "quote": "Customers renew because their work is in the files.", "uncertainty": "stated"}
R6 = {"claim": "The business is subscription software.",
      "quote": "the company sells subscriptions", "uncertainty": "stated"}
R7 = {"claim": "Competition is expected to increase.",
      "quote": "the company expects competition from new tools to increase",
      "uncertainty": "likely"}


@pytest.fixture
def reading():
    from portfolio_tool import reading
    return reading


@pytest.fixture
def record(reading):
    def _record(claims, section="Item 7", text=SECTION, filing=None):
        return reading.record(FILING if filing is None else filing, section, text, claims)
    return _record


# --- A. the rows ------------------------------------------------------------------------

def test_r_1_to_r_3_are_accepted_and_the_record_is_the_filings(record):
    out = record([R1, R2, R3])
    assert (out.form, out.accn, out.filed, out.fiscal_year, out.source, out.section) == (
        "10-K", "0001652044-26-000018", dt.date(2026, 2, 5), "FY2025", "EDGAR", "Item 7")
    assert [c.id for c in out.claims] == ["7.1", "7.2", "7.3"]
    assert [c.uncertainty for c in out.claims] == ["stated", "inferred", "stated"]
    assert out.claims[0].claim == R1["claim"] and out.claims[0].quote == R1["quote"]


def test_r_2_a_line_break_and_a_space_are_both_whitespace(record):
    (claim,) = record([R2]).claims
    assert claim.quote == "lives in the files. Revenue from subscriptions"
    spread = {**R2, "quote": "lives in the   files.\n\tRevenue from subscriptions"}
    assert record([spread]).claims[0].quote == claim.quote


def test_r_3_a_figure_inside_the_quote_is_the_filings(record):
    (claim,) = record([R3]).claims
    assert "1,234" in claim.quote and not any(ch.isdigit() for ch in claim.claim)


def test_r_4_a_digit_in_the_claim_refuses(reading, record):
    with pytest.raises(reading.ReadingError, match="claim 1: a digit in the claim"):
        record([R4])


def test_r_5_a_quote_one_word_off_refuses(reading, record):
    with pytest.raises(reading.ReadingError, match="the quote is not in the section"):
        record([R5])


def test_r_6_case_is_not_normalised(reading, record):
    with pytest.raises(reading.ReadingError, match="the quote is not in the section"):
        record([R6])


def test_r_7_an_uncertainty_outside_the_set_refuses(reading, record):
    with pytest.raises(reading.ReadingError, match="uncertainty 'likely'"):
        record([R7])


# --- the caps and the whole reading -------------------------------------------------------

def test_a_quote_has_no_cap_of_its_own(record):
    """Decision 70: a quote of 301 characters is accepted, and so is one
    of 3,600 alone."""
    text = "x" * 4000
    assert len(record([{**R1, "quote": "x" * 301}], text=text).claims[0].quote) == 301
    assert len(record([{**R1, "quote": "x" * 3600}], text=text).claims[0].quote) == 3600


def test_quotes_of_3600_together_are_accepted_and_3601_refused(reading, record):
    """The cap is on the reading's quoted text, and the refusal names the
    section and the total, since no one claim is at fault."""
    text = "x" * 4000
    twelve = [{**R1, "quote": "x" * 300}] * 12
    assert sum(len(c.quote) for c in record(twelve, text=text).claims) == 3600
    over = twelve[:11] + [{**R1, "quote": "x" * 301}]
    with pytest.raises(reading.ReadingError,
                       match="^Item 7: the quotes hold 3,601 characters together"):
        record(over, text=text)
    with pytest.raises(reading.ReadingError, match="3,601 characters"):
        record([{**R1, "quote": "x" * 1800}, {**R1, "quote": "x" * 1801}], text=text)


def test_the_total_counts_a_quote_once_its_whitespace_collapses(reading, record):
    """A quote with a line break and a run of spaces in it counts the one
    space: 3,603 characters as supplied, 3,600 collapsed, accepted."""
    text = "x" * 2000 + " " + "y" * 2000
    quote = "x" * 1800 + "\n   " + "y" * 1799
    assert len(quote) == 3603
    assert len(record([{**R1, "quote": quote}], text=text).claims[0].quote) == 3600
    with pytest.raises(reading.ReadingError, match="3,601 characters"):
        record([{**R1, "quote": quote + "y"}], text=text)


def test_a_claim_s_own_fault_is_named_before_the_total(reading, record):
    """The total is checked once every claim has passed its own rules: a
    reading over the cap that also holds R-4 is refused naming R-4."""
    text = SECTION + "\n" + "x" * 4000
    with pytest.raises(reading.ReadingError, match="claim 2: a digit"):
        record([{**R1, "quote": "x" * 3601}, R4], text=text)


def test_no_claims_and_thirteen_are_refused_and_twelve_is_not(reading, record):
    with pytest.raises(reading.ReadingError, match="0 claims"):
        record([])
    with pytest.raises(reading.ReadingError, match="13 claims"):
        record([R1] * 13)
    assert len(record([R1] * 12).claims) == 12


def test_one_failed_claim_refuses_the_whole_reading(reading, record):
    with pytest.raises(reading.ReadingError, match="claim 2: a digit"):
        record([R1, R4])


# --- the filing, the section and what a model may supply ------------------------------------

def test_a_form_other_than_the_annual_report_is_refused_naming_it(reading, record):
    with pytest.raises(reading.ReadingError, match="20-F"):
        record([R1], filing={**FILING, "form": "20-F"})


def test_a_filing_without_its_source_is_refused(reading, record):
    with pytest.raises(reading.ReadingError, match="accn"):
        record([R1], filing={k: v for k, v in FILING.items() if k != "accn"})


def test_a_section_outside_the_three_is_refused(reading, record):
    with pytest.raises(reading.ReadingError, match="Item 8"):
        record([R1], section="Item 8")
    assert record([R1], section="Item 1A").claims[0].id == "1A.1"


def test_an_empty_section_is_refused(reading, record):
    with pytest.raises(reading.ReadingError, match="empty"):
        record([R1], text=" \n ")


@pytest.mark.parametrize("extra", [{"id": "7.9"}, {"value": 1234}, {"source": "a press release"}])
def test_a_key_the_model_may_not_supply_is_refused(reading, record, extra):
    with pytest.raises(reading.ReadingError, match=list(extra)[0]):
        record([{**R1, **extra}])


def test_the_section_text_is_not_in_the_record(record):
    out = record([R1, R2, R3])
    quoted = sum(len(c.quote) for c in out.claims)
    assert quoted <= 3600
    assert all(len(c.quote) < len(SECTION) for c in out.claims)
    assert not hasattr(out, "text")


def test_the_vocabularies_are_the_runners(reading):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / "benchmark"))
    import run_cases
    assert set(reading.SECTIONS) == run_cases.READING_SECTIONS
    assert set(reading.UNCERTAINTIES) == run_cases.UNCERTAINTIES
    assert (reading.FORM, reading.QUOTED_CAP, reading.CLAIMS_CAP) == (
        run_cases.READING_FORM, run_cases.QUOTED_CAP, run_cases.CLAIMS_CAP)
