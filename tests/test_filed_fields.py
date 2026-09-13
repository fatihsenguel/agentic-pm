"""
filed_figures.FIELDS held to expected_values.md Part 12 C.

A field of the figures block names an ordered list of us-gaap tags; the
first that yields a fact for the period wins (D30). The list is a definition,
not policy, so it lives in code, and Part 12 C states it in prose. Two
statements of one list drift unless something holds them together: this
reads Part 12 C's table out of the document and compares it with the code,
field by field, kind by kind, tag by tag, in order. Order matters: for FY2017
Apple's three revenue tags carry the same value and the order decides which
filing a row cites.

The module is imported inside a fixture so that, before it exists, this
file is a list of errors and not an interrupted suite.
"""

import re
from pathlib import Path

import pytest


REFERENCE = Path(__file__).parent / "golden" / "expected_values.md"
SECTION = "### C. The tag each field resolves from"


def _part_12_c():
    text = REFERENCE.read_text()
    start = text.index(SECTION)
    end = text.index("\n### ", start + len(SECTION))
    rows = []
    for line in text[start:end].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in ("Field", "---") or set(cells[0]) <= {"-"}:
            continue
        rows.append((cells[0], cells[1], tuple(re.findall(r"`([^`]+)`", cells[2]))))
    return rows


@pytest.fixture(scope="module")
def fields():
    from portfolio_tool.filed_figures import FIELDS
    return FIELDS


def test_the_reference_table_is_read():
    rows = _part_12_c()
    assert len(rows) == 14
    assert rows[0] == ("revenue", "duration", (
        "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "Revenues"))


def test_the_fields_are_part_12_c_in_order(fields):
    assert [f.name for f in fields] == [r[0] for r in _part_12_c()]


@pytest.mark.parametrize("name, kind, tags", _part_12_c())
def test_each_field_has_its_kind_and_its_tags_in_order(fields, name, kind, tags):
    field = next(f for f in fields if f.name == name)
    assert field.kind == kind
    assert field.tags == tags


def test_a_kind_is_duration_or_instant(fields):
    assert {f.kind for f in fields} <= {"duration", "instant"}
