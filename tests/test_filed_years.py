"""
filed_figures.filed_years held to expected_values.md Parts 12 and 13.

The assembler turns filed facts into the `years` half of the figures block:
which fiscal years exist, when each counts from, and each field's figure in
each year with the filing it comes from. The rules, from the reference:

  D28  A year is the end date of annual facts. Two year ends fewer than 350
       days apart raise: a change of fiscal year is not guessed at.
  D21  A filing's own year is the latest year end it carries an annual fact
       for. A year's own report is the earliest-filed 10-K or 10-K/A whose own
       year it is; the label is FY and that report's `fy`, and the year counts
       from that report's filed date. A year no filing reports as its own is
       not a year (Part 12 A, F11). Only reports filed on or before the as-of
       date count.
  D29  A figure is the latest vintage filed on or before the as-of date. Two
       different values filed on the same day raise.
  D30  The first tag in the field's list with a fact at the year end wins. A
       field no tag yields is left out of that year and listed as unresolved
       with the tags tried; nothing fills it.
  D39  The share count is a field like the others, the filer's own count at
       the year end in whole shares (Part 12 B's and Part 13 B's notes,
       decision 48 item 7). Its unit is shares, not money, and the block's
       one currency is read from the money fields alone.

The facts go through the EDGAR provider over a stand-in session, so what the
assembler sees is what the provider returns. The fixtures are samples of a
document, not whole documents: a filing is present only through the rows
cited from it, so its own year is right only where every year it reports is
cited. Apple's checks therefore read section A and the own-report rows, and
F11 reads its one filing; Alphabet's and JPMorgan's fixtures are read whole.

The module is imported inside a fixture so that, before the function exists,
this file is a list of errors and not an interrupted suite.
"""

import csv
import datetime as dt
import json
from decimal import Decimal
from pathlib import Path

import pytest


GOLDEN = Path(__file__).parent / "golden"
AS_OF = dt.date(2026, 9, 13)
APPLE, ALPHABET, JPMORGAN = 320193, 1652044, 19617
DEI_TAGS = {"EntityCommonStockSharesOutstanding"}


# --- the facts, through the provider -------------------------------------------

def _rows(name, sections=None):
    with open(GOLDEN / name, newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["end"]]
    return [r for r in rows if sections is None or r["section"] in sections]


def _document(cik, rows):
    facts, seen = {}, set()
    for row in rows:
        key = (row["tag"], row["unit"], row["start"], row["end"], row["accn"], row["val"])
        if key in seen:
            continue
        seen.add(key)
        fact = {"end": row["end"], "val": json.loads(row["val"]), "accn": row["accn"],
                "fy": int(row["fy"]) if row["fy"] else None, "fp": row["fp"] or None,
                "form": row["form"], "filed": row["filed"]}
        if row["start"]:
            fact["start"] = row["start"]
        if row["frame"]:
            fact["frame"] = row["frame"]
        taxonomy = "dei" if row["tag"] in DEI_TAGS else "us-gaap"
        units = facts.setdefault(taxonomy, {}).setdefault(row["tag"], {"units": {}})["units"]
        units.setdefault(row["unit"], []).append(fact)
    return {"cik": cik, "entityName": f"CIK {cik}", "facts": facts}


class _Response:
    def __init__(self, body):
        self.status_code = 200
        self.content = json.dumps(body).encode()

    def raise_for_status(self):
        pass


class _Session:
    def __init__(self, body):
        self.body = body

    def get(self, url, headers=None, timeout=None):
        return _Response(self.body)


def facts_for(cik, rows, monkeypatch):
    from portfolio_tool.providers.edgar import EdgarProvider
    monkeypatch.setenv("EDGAR_USER_AGENT", "benchmark-suite test@example.invalid")
    return EdgarProvider(session=_Session(_document(cik, rows))).annual_facts(cik)


def _synthetic(tag, start, end, accn, filed, value="1", fy=2025, form="10-K"):
    from portfolio_tool.provider_models import ProviderFiledFact
    return ProviderFiledFact(
        tag=tag, unit="USD", start=dt.date.fromisoformat(start) if start else None,
        end=dt.date.fromisoformat(end), value=Decimal(value), accn=accn, fy=fy, fp="FY",
        form=form, filed=dt.date.fromisoformat(filed), frame=None, source="stand-in")


@pytest.fixture(scope="module")
def filed_figures():
    from portfolio_tool import filed_figures
    assert hasattr(filed_figures, "filed_years"), "no filed_years in filed_figures"
    return filed_figures


def _own_reports(name):
    """Part 12 A and Part 13 F, as the csv's section Y rows carry them."""
    return {f"FY{r['fy']}": (dt.date.fromisoformat(r["end"]), dt.date.fromisoformat(r["filed"]))
            for r in _rows(name, {"Y"})}


def _label_by_end(name):
    return {ends: label for label, (ends, _) in _own_reports(name).items()}


# --- D21 and D28: the years -------------------------------------------------------

@pytest.mark.parametrize("name, cik, sections", [
    ("edgar_facts_aapl.csv", APPLE, {"A", "Y"}),
    ("edgar_facts_googl.csv", ALPHABET, None),
    ("edgar_facts_jpm.csv", JPMORGAN, None),
])
def test_each_year_is_dated_by_its_own_report(filed_figures, monkeypatch, name, cik, sections):
    block = filed_figures.filed_years(facts_for(cik, _rows(name, sections), monkeypatch), AS_OF)
    expected = _own_reports(name)
    assert set(block["years"]) == set(expected)
    for label, (ends, filed) in expected.items():
        assert block["years"][label]["ends"] == ends
        assert block["years"][label]["filed"] == filed


def test_f11_a_year_no_filing_reports_as_its_own_is_not_a_year(filed_figures, monkeypatch):
    accn = "0001193125-09-214859"
    rows = [r for r in _rows("edgar_facts_aapl.csv", {"F3", "F11"}) if r["accn"] == accn]
    assert len(rows) == 3
    block = filed_figures.filed_years(facts_for(APPLE, rows, monkeypatch), AS_OF)
    assert list(block["years"]) == ["FY2009"]
    assert block["years"]["FY2009"]["ends"] == dt.date(2009, 9, 26)
    assert block["years"]["FY2009"]["filed"] == dt.date(2009, 10, 27)


def test_an_amendment_does_not_redate_the_year(filed_figures):
    """Apple's FY2009 10-K (0001193125-09-214859, filed 2009-10-27) and its
    10-K/A (0001193125-10-012091, filed 2010-01-25) both carry 2009-09-26 as
    their latest year end. The committed fixture holds only the amendment's
    FY2008 row, so the pair is typed here with those accessions, dates and
    net income figures, as in the document pulled 2026-09-13."""
    facts = [
        _synthetic("NetIncomeLoss", "2008-09-28", "2009-09-26", "0001193125-10-012091",
                   "2010-01-25", value="8235000000", fy=2009, form="10-K/A"),
        _synthetic("NetIncomeLoss", "2008-09-28", "2009-09-26", "0001193125-09-214859",
                   "2009-10-27", value="5704000000", fy=2009),
    ]
    block = filed_figures.filed_years(facts, AS_OF)
    assert block["years"]["FY2009"]["filed"] == dt.date(2009, 10, 27)


def test_a_report_filed_after_the_as_of_date_is_not_yet_a_year(filed_figures, monkeypatch):
    facts = facts_for(APPLE, _rows("edgar_facts_aapl.csv", {"A", "Y"}), monkeypatch)
    block = filed_figures.filed_years(facts, dt.date(2025, 10, 30))
    assert "FY2025" not in block["years"]
    assert "FY2024" in block["years"]


def test_two_year_ends_closer_than_350_days_raise(filed_figures):
    facts = [
        _synthetic("Revenues", "2024-01-01", "2024-12-31", "A-1", "2025-02-01", fy=2024),
        _synthetic("Revenues", "2024-06-30", "2025-06-30", "A-2", "2025-08-01", fy=2025),
    ]
    with pytest.raises(filed_figures.FiledFiguresError, match="2024-12-31"):
        filed_figures.filed_years(facts, AS_OF)


def test_one_label_for_two_years_raises(filed_figures):
    facts = [
        _synthetic("Revenues", "2023-01-01", "2023-12-31", "A-1", "2024-02-01", fy=2024),
        _synthetic("Revenues", "2024-01-01", "2024-12-31", "A-2", "2025-02-01", fy=2024),
    ]
    with pytest.raises(filed_figures.FiledFiguresError, match="FY2024"):
        filed_figures.filed_years(facts, AS_OF)


# --- D29 and D30: the figures ---------------------------------------------------------

@pytest.mark.parametrize("name, cik, section, sections", [
    ("edgar_facts_aapl.csv", APPLE, "A", {"A", "Y"}),
    ("edgar_facts_googl.csv", ALPHABET, "B", None),
    ("edgar_facts_jpm.csv", JPMORGAN, "C", None),
])
def test_every_figure_is_the_reference_row(filed_figures, monkeypatch, name, cik, section, sections):
    block = filed_figures.filed_years(facts_for(cik, _rows(name, sections), monkeypatch), AS_OF)
    labels = _label_by_end(name)
    checked = 0
    for row in _rows(name, {section}):
        if not row["field"]:
            continue
        label = labels[dt.date.fromisoformat(row["end"])]
        assert block["years"][label][row["field"]] == Decimal(row["val"]), row
        source = block["provenance"][label][row["field"]]
        assert (source["tag"], source["accn"]) == (row["tag"], row["accn"]), row
        checked += 1
    assert checked == {"A": 75, "B": 67, "C": 25}[section]


ALPHABET_UNRESOLVED = (
    {(y, "depreciation_amortisation") for y in ("FY2021", "FY2022", "FY2023", "FY2024", "FY2025")}
    | {("FY2025", "marketable_securities_noncurrent"),
       ("FY2021", "long_term_debt_noncurrent"), ("FY2022", "long_term_debt_noncurrent")}
)

JPMORGAN_UNRESOLVED = {
    (y, field)
    for y in ("FY2021", "FY2022", "FY2023", "FY2024", "FY2025")
    for field in ("cost_of_revenue", "operating_income", "capex", "cash",
                  "marketable_securities_current", "marketable_securities_noncurrent",
                  "commercial_paper", "long_term_debt_current", "long_term_debt_noncurrent",
                  "shares_outstanding")
}


@pytest.mark.parametrize("name, cik, expected", [
    ("edgar_facts_googl.csv", ALPHABET, ALPHABET_UNRESOLVED),
    ("edgar_facts_jpm.csv", JPMORGAN, JPMORGAN_UNRESOLVED),
])
def test_a_field_no_tag_yields_is_named_and_not_filled(filed_figures, monkeypatch, name, cik, expected):
    block = filed_figures.filed_years(facts_for(cik, _rows(name), monkeypatch), AS_OF)
    unresolved = {(u["year"], u["field"]) for u in block["unresolved"]}
    assert unresolved == expected
    for year, field in expected:
        assert field not in block["years"][year]
    lists = {f.name: f.tags for f in filed_figures.FIELDS}
    for entry in block["unresolved"]:
        assert entry["tags"] == lists[entry["field"]], entry


def test_cost_of_revenue_resolves_from_each_filers_own_tag(filed_figures, monkeypatch):
    """D36 and Part 12 H: the field lists two tags no filer files together,
    Apple's cost of sales and Alphabet's cost of revenue; each year cites
    the filer's own, and the bank, which files neither, has both named as
    tried."""
    apple = filed_figures.filed_years(
        facts_for(APPLE, _rows("edgar_facts_aapl.csv", {"A", "Y"}), monkeypatch), AS_OF)
    alphabet = filed_figures.filed_years(
        facts_for(ALPHABET, _rows("edgar_facts_googl.csv"), monkeypatch), AS_OF)
    jpmorgan = filed_figures.filed_years(
        facts_for(JPMORGAN, _rows("edgar_facts_jpm.csv"), monkeypatch), AS_OF)
    years = ("FY2021", "FY2022", "FY2023", "FY2024", "FY2025")
    assert {apple["provenance"][y]["cost_of_revenue"]["tag"] for y in years} == {"CostOfGoodsAndServicesSold"}
    assert {alphabet["provenance"][y]["cost_of_revenue"]["tag"] for y in years} == {"CostOfRevenue"}
    assert apple["years"]["FY2025"]["cost_of_revenue"] == Decimal("220960000000")
    assert alphabet["years"]["FY2025"]["cost_of_revenue"] == Decimal("162535000000")
    tried = {u["tags"] for u in jpmorgan["unresolved"] if u["field"] == "cost_of_revenue"}
    assert tried == {("CostOfRevenue", "CostOfGoodsAndServicesSold")}
    assert all("gross_profit" not in year for block in (apple, alphabet, jpmorgan)
               for year in block["years"].values())


def test_the_share_count_is_the_filers_year_end_count(filed_figures, monkeypatch):
    """Part 12 B's and Part 13 B's notes of 2026-09-17: shares_outstanding
    resolves from CommonStockSharesOutstanding at the year end, in whole
    shares as filed. Alphabet's FY2021 is the split-adjusted count on the
    FY2022 10-K, the later vintage F9 shows, not the FY2021 report's
    662,121,000."""
    apple = filed_figures.filed_years(
        facts_for(APPLE, _rows("edgar_facts_aapl.csv", {"A", "Y"}), monkeypatch), AS_OF)
    alphabet = filed_figures.filed_years(
        facts_for(ALPHABET, _rows("edgar_facts_googl.csv"), monkeypatch), AS_OF)
    assert apple["years"]["FY2025"]["shares_outstanding"] == Decimal("14773260000")
    assert apple["years"]["FY2021"]["shares_outstanding"] == Decimal("16426786000")
    assert alphabet["years"]["FY2025"]["shares_outstanding"] == Decimal("12088000000")
    assert alphabet["years"]["FY2021"]["shares_outstanding"] == Decimal("13242000000")
    source = alphabet["provenance"]["FY2021"]["shares_outstanding"]
    assert (source["tag"], source["accn"]) == ("CommonStockSharesOutstanding", "0001652044-23-000016")
    assert all("shares_outstanding" in year for block in (apple, alphabet)
               for year in block["years"].values())


def test_a_count_in_shares_is_not_a_second_currency(filed_figures, monkeypatch):
    """The count's unit is shares. A block that carries it beside dollar
    figures has one reporting currency, USD, and does not raise as if it
    were filed in two."""
    for name, cik, sections in (("edgar_facts_aapl.csv", APPLE, {"A", "Y"}),
                                ("edgar_facts_googl.csv", ALPHABET, None)):
        block = filed_figures.filed_years(facts_for(cik, _rows(name, sections), monkeypatch), AS_OF)
        assert block["currency"] == "USD"
        assert "shares_outstanding" in block["years"]["FY2025"]


def test_the_neighbour_is_not_used(filed_figures, monkeypatch):
    """F8 and Part 13 C: Depreciation, pre-tax income and CashAndDueFromBanks
    are in the facts and belong to no field. CostOfRevenue left this set on
    2026-09-16: it is cost_of_revenue's own tag (D36)."""
    for name, cik in (("edgar_facts_googl.csv", ALPHABET), ("edgar_facts_jpm.csv", JPMORGAN)):
        block = filed_figures.filed_years(facts_for(cik, _rows(name), monkeypatch), AS_OF)
        used = {s["tag"] for year in block["provenance"].values() for s in year.values()}
        assert not used & {"Depreciation", "CashAndDueFromBanks",
                           "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"}


def test_no_figure_was_filed_after_the_as_of_date(filed_figures, monkeypatch):
    facts = facts_for(APPLE, _rows("edgar_facts_aapl.csv", {"A", "Y"}), monkeypatch)
    as_of = dt.date(2025, 10, 30)
    block = filed_figures.filed_years(facts, as_of)
    filed = [s["filed"] for year in block["provenance"].values() for s in year.values()]
    assert filed and max(filed) <= as_of


def test_two_values_filed_the_same_day_raise(filed_figures):
    facts = [
        _synthetic("Revenues", "2025-01-01", "2025-12-31", "A-1", "2026-02-01", value="100"),
        _synthetic("Revenues", "2025-01-01", "2025-12-31", "A-2", "2026-02-01", value="101"),
    ]
    with pytest.raises(filed_figures.FiledFiguresError, match="revenue"):
        filed_figures.filed_years(facts, AS_OF)


def test_the_block_names_its_currency_and_as_of(filed_figures, monkeypatch):
    facts = facts_for(APPLE, _rows("edgar_facts_aapl.csv", {"A", "Y"}), monkeypatch)
    block = filed_figures.filed_years(facts, AS_OF)
    assert block["currency"] == "USD"
    assert block["as_of"] == AS_OF


# --- the same, over what filed_facts and filers hold --------------------------------

def _filers():
    """Alphabet's and JPMorgan's rows of edgar_submissions.csv (Part 13 C)."""
    from portfolio_tool.provider_models import ProviderFiler
    with open(GOLDEN / "edgar_submissions.csv", newline="") as fh:
        rows = {int(r["cik"]): r for r in csv.DictReader(fh)}
    return {cik: ProviderFiler(cik=cik, name=rows[cik]["name"], sic=rows[cik]["sic"],
                               sic_description=rows[cik]["sic_description"])
            for cik in (ALPHABET, JPMORGAN)}


@pytest.fixture
def stored(monkeypatch):
    """Both fixtures and both filers stored through the filings fetch, in a
    session that is rolled back and cleared afterwards."""
    from portfolio_tool import filings
    from portfolio_tool.database_setup import FiledFact, FiledFetchMetadata, Filer, get_session

    stored_facts = {
        ALPHABET: facts_for(ALPHABET, _rows("edgar_facts_googl.csv"), monkeypatch),
        JPMORGAN: facts_for(JPMORGAN, _rows("edgar_facts_jpm.csv"), monkeypatch),
    }
    filers = _filers()

    class StandIn:
        name = "stand-in filings"

        def annual_facts(self, cik):
            return stored_facts[cik]

        def filer(self, cik):
            return filers[cik]

    def clear(session):
        for model in (FiledFact, FiledFetchMetadata, Filer):
            session.query(model).filter(model.cik.in_(list(stored_facts))).delete(
                synchronize_session=False)
        session.commit()

    session = get_session()
    try:
        clear(session)
        for cik in stored_facts:
            filings.update_filed_facts(session, StandIn(), cik)
            filings.update_filer(session, StandIn(), cik)
        yield session, stored_facts, filers
    finally:
        session.rollback()
        clear(session)
        session.close()


def test_the_stored_rows_give_the_same_years(filed_figures, stored):
    """Alphabet's and JPMorgan's fixtures stored through the filings fetch
    and read back: every figure survives the text column as the same Decimal,
    and one company's block holds none of the other's rows."""
    session, stored_facts, _ = stored
    for cik, facts in stored_facts.items():
        pure = filed_figures.filed_years(facts, AS_OF)
        block = filed_figures.filed_years_for(session, cik, AS_OF)
        assert {key: block[key] for key in pure} == pure


def test_the_block_carries_the_code_as_of_its_pull(filed_figures, stored):
    """D35: the SIC code as EDGAR states it, on the block, as of its pull
    date. The pull time is the filers row's, uninterpreted: which calendar
    day it names is the clock question the UTC entry keeps."""
    from portfolio_tool.database_setup import Filer
    session, _, filers = stored
    for cik, filer in filers.items():
        block = filed_figures.filed_years_for(session, cik, AS_OF)
        assert (block["sic"], block["sic_description"]) == (filer.sic, filer.sic_description)
        assert block["sic_as_of"] == session.get(Filer, cik).pulled_at
    assert filed_figures.filed_years_for(session, JPMORGAN, AS_OF)["sic"] == "6021"
    assert filed_figures.filed_years_for(session, ALPHABET, AS_OF)["sic"] == "7370"


def test_the_block_has_exactly_these_keys(filed_figures, stored):
    session, _, _ = stored
    block = filed_figures.filed_years_for(session, ALPHABET, AS_OF)
    assert set(block) == {"currency", "as_of", "years", "provenance", "unresolved",
                          "sic", "sic_description", "sic_as_of"}


def test_a_code_edgar_does_not_state_is_none_with_its_pull(filed_figures, stored):
    from portfolio_tool.database_setup import Filer
    session, _, _ = stored
    row = session.get(Filer, ALPHABET)
    row.sic, row.sic_description = None, None
    session.commit()
    block = filed_figures.filed_years_for(session, ALPHABET, AS_OF)
    assert block["sic"] is None and block["sic_description"] is None
    assert block["sic_as_of"] == row.pulled_at


def test_no_filers_row_raises(filed_figures, stored):
    """A company whose submissions document was never fetched has no code
    on the block, and none is assumed: the reader stops and names the
    fetch, rather than handing the screen a block that reads as EDGAR
    stating no code."""
    from portfolio_tool.database_setup import Filer
    session, _, _ = stored
    session.query(Filer).filter(Filer.cik == JPMORGAN).delete()
    session.commit()
    with pytest.raises(filed_figures.FiledFiguresError, match="19617"):
        filed_figures.filed_years_for(session, JPMORGAN, AS_OF)
