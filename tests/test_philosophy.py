"""
philosophy.toml held to docs/PHILOSOPHY.md.

The document is the philosophy; the TOML is derived from it. If they
disagree, the TOML is wrong. Every expected number here is copied from the
document, the way test_ips.py copies docs/IPS.md.

The loader's own raises are in test_philosophy_loader.py.
"""

import re
from pathlib import Path

import pytest

from portfolio_tool.philosophy import load_philosophy


ROOT = Path(__file__).parent.parent
DOCUMENT = ROOT / "docs" / "PHILOSOPHY.md"

# **PHI-x.y** then its paragraph, up to a blank line.
DOC_CLAUSE = re.compile(r"\*\*(PHI-\d+\.\d+)\*\*\s+(.*?)(?:\n\s*\n|\Z)", re.S)

# docs/PHILOSOPHY.md sections 2 to 4, in each metric's own unit: shares as
# fractions, a ratio as a ratio.
CHECKABLE = {
    "PHI-2.1": ("metric_band", {"metric": "return_on_invested_capital", "min": 0.12, "years": 5}),
    "PHI-2.2": ("metric_band", {"metric": "gross_margin", "min": 0.35, "years": 3}),
    "PHI-3.1": ("metric_band", {"metric": "net_debt_to_ebitda", "max": 2.0, "years": 1}),
    "PHI-4.1": ("margin_of_safety", {"discount": 0.25}),
    "PHI-4.2": ("metric_band", {"metric": "free_cash_flow_yield", "min": 0.04, "years": 1}),
}
STATEMENTS = {"PHI-1.1", "PHI-1.2", "PHI-2.3", "PHI-3.2", "PHI-4.3",
              "PHI-5.1", "PHI-5.2", "PHI-6.1", "PHI-6.2", "PHI-6.3",
              "PHI-7.1", "PHI-7.2"}


def _document_clauses():
    text = DOCUMENT.read_text(encoding="utf-8")
    return {m.group(1): " ".join(m.group(2).split()) for m in DOC_CLAUSE.finditer(text)}


@pytest.fixture(scope="module")
def philosophy():
    return load_philosophy("philosophy.toml")


def test_document_has_seventeen_clauses():
    assert len(_document_clauses()) == 17


def test_same_clause_ids_as_the_document(philosophy):
    assert list(philosophy.clauses) == list(_document_clauses())


def test_same_text_as_the_document(philosophy):
    doc = _document_clauses()
    for clause in philosophy:
        assert " ".join(clause.text.split()) == doc[clause.id], clause.id


def test_checkable_clauses_carry_the_documents_numbers(philosophy):
    assert {c.id for c in philosophy.checkable} == set(CHECKABLE)
    for clause_id, (kind, params) in CHECKABLE.items():
        clause = philosophy[clause_id]
        assert clause.type == kind, clause_id
        assert dict(clause.params) == params, clause_id


def test_statements_carry_nothing(philosophy):
    assert {c.id for c in philosophy.statements} == STATEMENTS
    for clause in philosophy.statements:
        assert dict(clause.params) == {}


def test_every_clause_carries_topics(philosophy):
    for clause in philosophy:
        assert clause.topics, clause.id


def test_topics_are_containment_not_similarity(philosophy):
    assert [c.id for c in philosophy.clauses_on("my philosophy on debt")] == ["PHI-3.1"]
    assert [c.id for c in philosophy.clauses_on("margin of safety")] == ["PHI-4.1"]
    assert philosophy.clauses_on("dividends") == []


def test_no_clause_names_a_price_target(philosophy):
    """DIRECTION.md invariant 7: a prediction is about the business, never a
    price level. The document may name a price against a valuation range and
    may not name a price a stock will reach."""
    for clause in philosophy:
        assert "price target" not in clause.text.lower(), clause.id
        assert "will be at" not in clause.text.lower(), clause.id
