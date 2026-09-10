"""
ips.toml held to docs/IPS.md, and the loader held to its raises.

The document is the owner's policy; the TOML is derived from it. If they
disagree, the TOML is wrong. Every expected number here is copied from the
document, the way test_allocation.py copies expected_values.md.
"""

import re
from pathlib import Path

import pytest

from portfolio_tool.ips import IPSError, load_ips


ROOT = Path(__file__).parent.parent
DOCUMENT = ROOT / "docs" / "IPS.md"

# **IPS-x.y** then its paragraph, up to a blank line.
DOC_CLAUSE = re.compile(r"\*\*(IPS-\d+\.\d+)\*\*\s+(.*?)(?:\n\s*\n|\Z)", re.S)


def _document_clauses():
    text = DOCUMENT.read_text(encoding="utf-8")
    return {m.group(1): " ".join(m.group(2).split()) for m in DOC_CLAUSE.finditer(text)}


# docs/IPS.md sections 3 and 4, as fractions.
CHECKABLE = {
    "IPS-3.1": ("asset_class_band", {"asset_class": "Equity", "min": 0.40, "max": 0.65}),
    "IPS-3.2": ("asset_class_band", {"asset_class": "Fixed Income", "min": 0.08, "max": 0.30}),
    "IPS-3.3": ("asset_class_band", {"asset_class": "Commodity", "max": 0.15}),
    "IPS-3.4": ("asset_class_band", {"asset_class": "Real Estate", "max": 0.15}),
    "IPS-3.5": ("asset_class_band", {"asset_class": "Cash", "min": 0.03}),
    "IPS-4.1": ("max_instrument_weight", {"max": 0.12}),
    "IPS-4.2": ("max_issuer_weight", {"max": 0.10}),
    "IPS-4.3": ("max_sector_weight", {"max": 0.25}),
}
STATEMENTS = {"IPS-1.1", "IPS-1.2", "IPS-2.1", "IPS-2.2",
              "IPS-5.1", "IPS-5.2", "IPS-5.3", "IPS-6.1", "IPS-6.2"}


@pytest.fixture(scope="module")
def ips():
    return load_ips()


def test_document_has_seventeen_clauses():
    assert len(_document_clauses()) == 17


def test_same_clause_ids_as_the_document(ips):
    assert list(ips.clauses) == list(_document_clauses())


def test_same_text_as_the_document(ips):
    doc = _document_clauses()
    for clause in ips:
        assert " ".join(clause.text.split()) == doc[clause.id], clause.id


def test_checkable_clauses_carry_the_documents_numbers(ips):
    assert {c.id for c in ips.checkable} == set(CHECKABLE)
    for clause_id, (kind, params) in CHECKABLE.items():
        clause = ips[clause_id]
        assert clause.type == kind, clause_id
        assert dict(clause.params) == params, clause_id


def test_statements_carry_nothing(ips):
    assert {c.id for c in ips.statements} == STATEMENTS
    for clause in ips.statements:
        assert dict(clause.params) == {}


def test_no_clause_on_currency(ips):
    assert not any("currenc" in c.text.lower() for c in ips)
    assert "currency" not in ips.topics
    assert ips.clauses_on("currency risk") == []


def test_every_clause_carries_topics(ips):
    for clause in ips:
        assert clause.topics, clause.id


def test_topics_are_containment_not_similarity(ips):
    """The owner's words inside the user's words, whole, never the reverse."""
    concentration = ["IPS-4.1", "IPS-4.2", "IPS-4.3"]
    assert [c.id for c in ips.clauses_on("concentration")] == concentration
    assert [c.id for c in ips.clauses_on("  Concentration ")] == concentration
    assert [c.id for c in ips.clauses_on("my concentration risk")] == concentration
    assert [c.id for c in ips.clauses_on("allocation")] == ["IPS-3.1", "IPS-3.2", "IPS-3.3", "IPS-3.4", "IPS-3.5"]
    assert [c.id for c in ips.clauses_on("leveraged products")] == []   # "leverage" is not a whole word of it
    assert [c.id for c in ips.clauses_on("using leverage")] == ["IPS-2.1", "IPS-2.2"]
    assert ips.clauses_on("cashflow") == []                              # whole word, not substring
    assert [c.id for c in ips.clauses_on("holding cash")] == ["IPS-3.5"]
    assert ips.clauses_on("too concentrated") == []                      # a miss, closed in ips.toml, not in code
    assert ips.clauses_on("currency risk") == []


def test_topic_vocabulary_is_the_union(ips):
    assert ips.topics == sorted({t for c in ips for t in c.topics})
    assert "concentration" in ips.topics and "cash" in ips.topics


# --- the loader's raises, over inline TOML -----------------------------------

GOOD = '''
[[clause]]
id = "IPS-4.1"
type = "max_instrument_weight"
topics = ["concentration", "instrument"]
max = 0.12
text = "No single instrument exceeds 12% of total portfolio value."
'''


def _write(tmp_path, body):
    p = tmp_path / "ips.toml"
    p.write_text(body, encoding="utf-8")
    return str(p)


def test_inline_good_loads(tmp_path):
    ips = load_ips(_write(tmp_path, GOOD))
    assert len(ips) == 1 and ips["IPS-4.1"].params["max"] == 0.12


def test_a_relative_path_is_anchored_to_the_project_root(tmp_path, monkeypatch):
    """A portfolio row names the committed policy as `ips.toml`; the loader
    finds it from any working directory, the way the database URL is
    anchored, and never relative to the shell. An absolute path is taken
    as given."""
    monkeypatch.chdir(tmp_path)
    ips = load_ips("ips.toml")
    assert ips.path == str(ROOT / "ips.toml")
    assert len(ips) == 17


def test_missing_file_is_an_error_not_an_empty_policy(tmp_path):
    with pytest.raises(IPSError, match="no default policy"):
        load_ips(str(tmp_path / "absent.toml"))


@pytest.mark.parametrize("body, message", [
    (GOOD.replace("max_instrument_weight", "max_currency_exposure"), "not one the checker knows"),
    (GOOD.replace("max = 0.12\n", ""), "needs \\['max'\\]"),
    (GOOD.replace("max_instrument_weight", "statement"), "statement carries"),
    (GOOD.replace("max = 0.12", "max = 12"), "not a fraction"),
    (GOOD.replace("max = 0.12", "max = 0.12\nmin = 0.5"), "does not take"),
    (GOOD + GOOD, "appears twice"),
    (GOOD.replace('"IPS-4.1"', '"4.1"'), "does not match"),
    (GOOD.replace('text = "No single instrument exceeds 12% of total portfolio value."', 'text = ""'),
     "lacks \\['text'\\]"),
    ('[[clause]]\nid = "IPS-3.5"\ntype = "asset_class_band"\ntopics = ["cash"]\n'
     'asset_class = "Cash"\ntext = "Cash."',
     "min, max or both"),
    ('[[clause]]\nid = "IPS-3.1"\ntype = "asset_class_band"\ntopics = ["equity"]\nasset_class = "Equity"\n'
     'min = 0.65\nmax = 0.40\ntext = "Equity."', "not below max"),
    ('[policy]\ntitle = "x"\n' + GOOD, "nothing reads"),
    ("not = [toml", "not valid TOML"),
    (GOOD.replace('topics = ["concentration", "instrument"]\n', ""), "lacks \\['topics'\\]"),
    (GOOD.replace('["concentration", "instrument"]', "[]"), "non-empty list"),
    (GOOD.replace('["concentration", "instrument"]', '["Concentration"]'), "lowercase"),
    (GOOD.replace('["concentration", "instrument"]', '["a", "a"]'), "duplicate topics"),
])
def test_loader_raises(tmp_path, body, message):
    with pytest.raises(IPSError, match=message):
        load_ips(_write(tmp_path, body))
