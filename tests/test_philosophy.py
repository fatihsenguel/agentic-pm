"""
philosophy.toml held to docs/PHILOSOPHY.md.

The document is the philosophy; the TOML is derived from it. If they
disagree, the TOML is wrong. Every expected number here is copied from the
document, the way test_ips.py copies docs/IPS.md.

No loader reads the TOML yet (DIRECTION.md Order 3: shapes and references
before any tool reads them), so this test reads the file itself and carries
the closed type vocabulary the loader will own in Order 4. When the loader
exists, the fixture below goes through it and the vocabulary moves out of
this file, the way test_ips.py goes through load_ips.
"""

import re
from pathlib import Path

import pytest
import tomli


ROOT = Path(__file__).parent.parent
DOCUMENT = ROOT / "docs" / "PHILOSOPHY.md"
CONFIG = ROOT / "philosophy.toml"

# **PHI-x.y** then its paragraph, up to a blank line.
DOC_CLAUSE = re.compile(r"\*\*(PHI-\d+\.\d+)\*\*\s+(.*?)(?:\n\s*\n|\Z)", re.S)
CLAUSE_ID = re.compile(r"^PHI-\d+\.\d+$")

STATEMENT = "statement"
# type -> (required parameters, optional parameters). The three types the
# first decision of Order 3 fixed; a metric_band needs min, max or both.
CLAUSE_TYPES = {
    STATEMENT: ((), ()),
    "metric_band": (("metric", "years"), ("min", "max")),
    "margin_of_safety": (("discount",), ()),
}
HEADER = ("id", "type", "text", "topics")

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
def clauses():
    with open(CONFIG, "rb") as f:
        raw = tomli.load(f)
    assert set(raw) == {"clause"}, "top-level keys nothing reads"
    entries = raw["clause"]
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)), "a clause appears twice"
    return {e["id"]: e for e in entries}


def _params(entry):
    return {k: v for k, v in entry.items() if k not in HEADER}


def test_document_has_seventeen_clauses():
    assert len(_document_clauses()) == 17


def test_same_clause_ids_as_the_document(clauses):
    assert list(clauses) == list(_document_clauses())


def test_same_text_as_the_document(clauses):
    doc = _document_clauses()
    for clause_id, entry in clauses.items():
        assert " ".join(entry["text"].split()) == doc[clause_id], clause_id


def test_every_clause_has_the_header_and_a_known_type(clauses):
    for clause_id, entry in clauses.items():
        assert CLAUSE_ID.match(clause_id), clause_id
        for key in HEADER:
            assert key in entry, (clause_id, key)
        assert entry["type"] in CLAUSE_TYPES, clause_id
        assert entry["topics"], clause_id
        assert all(t == " ".join(t.lower().split()) for t in entry["topics"]), clause_id


def test_checkable_clauses_carry_the_documents_numbers(clauses):
    checkable = {c for c, e in clauses.items() if e["type"] != STATEMENT}
    assert checkable == set(CHECKABLE)
    for clause_id, (kind, params) in CHECKABLE.items():
        entry = clauses[clause_id]
        assert entry["type"] == kind, clause_id
        assert _params(entry) == params, clause_id
        required, optional = CLAUSE_TYPES[kind]
        assert set(required) <= set(params), clause_id
        assert set(params) <= set(required) | set(optional), clause_id
        if kind == "metric_band":
            assert "min" in params or "max" in params, clause_id


def test_statements_carry_nothing(clauses):
    assert {c for c, e in clauses.items() if e["type"] == STATEMENT} == STATEMENTS
    for clause_id in STATEMENTS:
        assert _params(clauses[clause_id]) == {}, clause_id


def test_no_clause_names_a_price_target(clauses):
    """DIRECTION.md invariant 7: a prediction is about the business, never a
    price level. The document may name a price against a valuation range and
    may not name a price a stock will reach."""
    for clause_id, entry in clauses.items():
        assert "price target" not in entry["text"].lower(), clause_id
        assert "will be at" not in entry["text"].lower(), clause_id
