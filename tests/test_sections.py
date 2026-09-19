"""
portfolio_tool.sections: a section of a filing's document, held to
expected_values.md Part 16, D52, and section I's rows on the fixture.

The text is tests/golden/edgar_document_goog_excerpt.htm through
portfolio_tool.filing_text, so the line numbers are section G's. The whole
document's counts, section B's, were checked once by hand and are not a
test: the document is not committed.

The rules, each a test:

  - a section is its heading in the body to the line before the body's next
    heading, whichever item that is, returned whole with its heading line
  - the table of contents is not the body (F1), a cross-reference is not a
    heading (F3), and neither is a heading's shape inside a line or `Item`
    at the start without the period, each held on the fixture with one line
    added since neither occurs in it; the title may be fused to the period
    (F4), and case is not the rule (F5)
  - page furniture inside a section stays in it (D53)
  - one run, three runs, runs that differ, an item absent, an item last
    and a heading with nothing beneath it are each refused naming what was
    found (F6); only the three sections read are asked for
"""

import re
from pathlib import Path

import pytest

from portfolio_tool.filing_text import text_of
from portfolio_tool.sections import SectionError, section


FIXTURE = Path(__file__).parent / "golden" / "edgar_document_goog_excerpt.htm"


@pytest.fixture(scope="module")
def text():
    return text_of(FIXTURE.read_bytes())


@pytest.fixture(scope="module")
def lines(text):
    return text.split("\n")


# --- the three sections --------------------------------------------------

@pytest.mark.parametrize("name, first, last, size", [
    ("Item 1", 91, 96, 1_485),
    ("Item 1A", 97, 104, 1_745),
    ("Item 7", 146, 160, 1_601),
])
def test_each_section_is_its_lines_whole(text, lines, name, first, last, size):
    found = section(text, name)
    assert found == "\n".join(lines[first:last + 1])
    assert len(found) == size


def test_a_section_starts_at_its_heading_in_the_body(text):
    assert section(text, "Item 1A").split("\n")[0] == "ITEM 1A.RISK FACTORS"


def test_page_furniture_inside_a_section_stays(text):
    found = section(text, "Item 1A").split("\n")
    assert found[3:6] == ["10.", "Table of Contents", "Alphabet Inc."]
    assert section(text, "Item 1").split("\n")[-1] == "Alphabet Inc."


# --- F1 to F5 --------------------------------------------------------------

def test_the_table_of_contents_is_not_the_body(text, lines):
    assert lines[15:18] == ["Item 1A.", "Risk Factors", "9"]
    assert not section(text, "Item 1A").startswith("Item 1A.\nRisk Factors")


def test_a_section_ends_at_the_next_heading_whichever_it_is(text, lines):
    assert lines[161].startswith("ITEM 7A.")
    assert len(section(text, "Item 7")) == 1_601
    assert len("\n".join(lines[146:167])) == 2_029


def test_a_cross_reference_is_not_a_heading(text, lines):
    written = [n for n, line in enumerate(lines) if re.search(r"\bItem\s+1A\b", line, re.I)]
    assert written == [15, 97, 113, 147]
    assert section(text, "Item 1A").split("\n")[0] == lines[97]


@pytest.mark.parametrize("added, size", [
    ("Our results are discussed in Item 7. Management's Discussion and Analysis.", 1_820),
    ("Item 7 describes these results.", 1_777),
], ids=["inside a line", "no period"])
def test_a_line_that_is_not_a_heading_stays_in_its_section(text, lines, added, size):
    changed = "\n".join(lines[:101] + [added] + lines[101:])
    found = section(changed, "Item 1A").split("\n")
    assert added in found and len(found) == 9
    assert len("\n".join(found)) == size
    assert section(changed, "Item 7") == section(text, "Item 7")


def test_a_title_fused_to_the_period_is_a_heading(text, lines):
    assert lines[91] == "ITEM 1.BUSINESS"
    assert section(text, "Item 1").startswith("ITEM 1.BUSINESS\n")


def test_case_is_not_the_rule(text, lines):
    rewritten = "\n".join(re.sub(r"^ITEM ", "Item ", line) for line in lines)
    before, after = section(text, "Item 1A").split("\n"), section(rewritten, "Item 1A").split("\n")
    assert after[0] == "Item 1A.RISK FACTORS"
    assert after[1:] == before[1:]
    assert len("\n".join(after)) == 1_745


# --- F6: what is refused ----------------------------------------------------

def _without(lines, drop):
    return "\n".join(line for n, line in enumerate(lines) if n not in drop)


def test_one_run_is_refused(lines):
    with pytest.raises(SectionError, match=r"1 run\(s\)"):
        section(_without(lines, set(range(12, 84))), "Item 7")


def test_three_runs_are_refused(lines):
    changed = lines[:150] + ["Item 1A. Risk Factors above describes these."] + lines[150:]
    with pytest.raises(SectionError, match=r"3 run\(s\)"):
        section("\n".join(changed), "Item 7")


def test_runs_that_differ_are_refused_naming_the_item(lines):
    with pytest.raises(SectionError, match="different items, Item 7;"):
        section(_without(lines, {146}), "Item 7")


def test_an_item_absent_from_both_runs_is_refused_naming_it(lines):
    drop = {n for n, line in enumerate(lines) if line.lower().startswith("item 7.")}
    assert drop == {40, 146}
    with pytest.raises(SectionError, match="no heading for Item 7"):
        section(_without(lines, drop), "Item 7")


def test_an_item_last_in_its_run_is_refused(lines):
    heading = re.compile(r"^item\s+(\d{1,2})([a-c]?)\.", re.I)

    def after_seven(line):
        found = heading.match(line)
        return bool(found) and (int(found.group(1)), found.group(2).upper()) > (7, "")
    drop = {n for n, line in enumerate(lines) if after_seven(line)}
    with pytest.raises(SectionError, match="Item 7 is the document's last item"):
        section(_without(lines, drop), "Item 7")


def test_a_heading_with_nothing_beneath_it_is_refused(lines):
    with pytest.raises(SectionError, match="no line beneath it"):
        section(_without(lines, set(range(147, 161))), "Item 7")


@pytest.mark.parametrize("name", ["Item 7A", "Item 8", "item 7", "Item 1.", "Risk Factors"])
def test_only_the_sections_read_are_asked_for(text, name):
    with pytest.raises(SectionError, match="not a section that is read"):
        section(text, name)


def test_a_document_with_no_headings_is_refused(lines):
    with pytest.raises(SectionError, match=r"0 run\(s\)"):
        section("\n".join(lines[88:91]), "Item 1")
