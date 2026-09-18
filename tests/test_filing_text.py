"""
portfolio_tool.filing_text: a filing's primary document as text, held to
expected_values.md Part 16, D51 and section G.

The fixture is tests/golden/edgar_document_goog_excerpt.htm, an excerpt of
Alphabet's FY2025 10-K cut at element boundaries, every byte the
document's. The line numbers and counts below are section G's. What the
fixture cannot show, the whole document's 2,745 lines, was held once by
hand on the fetched document and is not a test.

The rules, each a test:

  - the text is 228 lines and 17,764 characters, no line empty, no run of
    whitespace, no character reference and no no-break space left in it
  - the XBRL header and the script yield nothing
  - a figure inside an inline XBRL element is in its line, and cells are a
    space apart
  - a line ends at a div, a tr and a br, and at no span
  - page furniture stays where the document has it (D53)
  - an element no document looked at carries is refused naming it, and a
    namespaced one is not
  - an encoding other than ASCII, no declaration, and a byte that is not
    ASCII are each refused
"""

from pathlib import Path

import pytest

from portfolio_tool import filing_text
from portfolio_tool.filing_text import FilingTextError, text_of


FIXTURE = Path(__file__).parent / "golden" / "edgar_document_goog_excerpt.htm"


@pytest.fixture(scope="module")
def document():
    return FIXTURE.read_bytes()


@pytest.fixture(scope="module")
def lines(document):
    return text_of(document).split("\n")


# --- the text as a whole ---------------------------------------------------

def test_the_fixture_is_the_one_section_g_describes(document):
    assert len(document) == 134_155


def test_lines_and_characters(lines):
    assert len(lines) == 228
    assert len("\n".join(lines)) == 17_764


def test_no_line_is_empty_and_whitespace_is_collapsed(lines):
    assert all(lines)
    assert all(line == " ".join(line.split()) for line in lines)


def test_character_references_are_resolved(lines):
    text = "\n".join(lines)
    assert "&#" not in text and "&amp;" not in text
    assert "\xa0" not in text
    assert lines[124].startswith("ITEM 5.MARKET FOR REGISTRANT’S COMMON EQUITY")


# --- what is left out ------------------------------------------------------

def test_the_xbrl_header_yields_nothing(document, lines):
    assert b"<ix:hidden>" in document and b">0001652044<" in document
    assert "FALSE" not in lines
    assert "0001652044" not in "\n".join(lines)


def test_the_head_yields_nothing(document, lines):
    assert b"<title>goog-20251231</title>" in document
    assert "goog-20251231" not in lines


def test_the_script_yields_nothing(document, lines):
    assert document.rstrip().endswith(b"</script></body></html>")
    assert lines[-1] == "98."


def test_a_script_that_carries_text_yields_nothing(document):
    # The document's one script is empty, so this is the document with one change.
    changed = document.replace(b"></script>", b">var words = 1;</script>", 1)
    assert changed != document
    assert text_of(changed) == text_of(document)


# --- lines and cells -------------------------------------------------------

def test_a_tagged_figure_is_in_its_row_and_cells_are_a_space_apart(lines):
    assert lines[150] == "Consolidated revenues $ 350,018 $ 402,836 $ 52,818 15 %"


def test_a_row_is_a_line(lines):
    assert lines[151] == "Cost of revenues $ 146,306 $ 162,535 $ 16,229 11 %"


def test_a_br_ends_a_line(lines):
    assert lines[135] == ("Approximate Dollar Value of Shares that May Yet Be Purchased "
                          "Under the Program")
    assert lines[136] == "(in millions)"


def test_a_span_ends_no_line(lines):
    assert lines[91] == "ITEM 1.BUSINESS"


def test_the_contents_page_writes_an_item_alone_on_its_line(lines):
    assert lines[15:18] == ["Item 1A.", "Risk Factors", "9"]


# --- the page furniture stays (D53) ----------------------------------------

def test_a_page_break_inside_a_sentence_keeps_its_three_lines(lines):
    assert lines[99].endswith("other companies may develop")
    assert lines[100:103] == ["10.", "Table of Contents", "Alphabet Inc."]
    assert lines[103].startswith("AI products and technologies")


# --- what is refused -------------------------------------------------------

def test_an_element_not_looked_at_is_refused_naming_it(document):
    changed = document.replace(b"<div", b"<p", 1)
    assert changed != document
    with pytest.raises(FilingTextError, match=r"<p> element"):
        text_of(changed)


@pytest.mark.parametrize("tag", ["style", "li", "b", "font", "sup"])
def test_common_elements_the_document_lacks_are_refused_too(document, tag):
    changed = document.replace(b"</body>", f"<{tag}>x</{tag}></body>".encode("ascii"))
    with pytest.raises(FilingTextError, match=rf"<{tag}> element"):
        text_of(changed)


def test_a_namespaced_element_is_not_refused_and_its_text_stays(document):
    changed = document.replace(b"</body>", b"<us-gaap:SomeAxis>kept</us-gaap:SomeAxis></body>")
    assert text_of(changed).split("\n")[-2:] == ["98.", "kept"]


def test_the_known_elements_are_the_documents(document):
    assert filing_text.ELEMENTS == {"html", "head", "meta", "title", "body", "script", "div",
                                    "span", "table", "tr", "td", "a", "br", "hr", "img"}
    assert filing_text.LEFT_OUT == {"head", "script", "ix:header"}
    assert filing_text.LINE == {"div", "tr", "br"}


def test_another_encoding_is_refused_naming_it(document):
    changed = document.replace(b"encoding='ASCII'", b"encoding='UTF-8'", 1)
    assert changed != document
    with pytest.raises(FilingTextError, match="UTF-8"):
        text_of(changed)


def test_no_declaration_is_refused(document):
    start = document.index(b"?>") + 2
    with pytest.raises(FilingTextError, match="declares no encoding"):
        text_of(document[start:])


def test_a_byte_that_is_not_ascii_is_refused(document):
    changed = document.replace(b"</body>", "é</body>".encode("utf-8"))
    with pytest.raises(FilingTextError, match="not"):
        text_of(changed)
