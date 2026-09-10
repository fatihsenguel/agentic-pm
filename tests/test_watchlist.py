"""
watchlist.toml held to docs/WATCHLIST.md: the watchlist and the prediction
ledger on it.

The document is the theses and the predictions in my words; the TOML is
derived from it. If they disagree, the TOML is wrong.

No loader reads the TOML yet (DIRECTION.md Order 3: shapes and references
before any tool reads them), so this test reads the file itself and carries
the shape the loader and the scorer will own in Order 4: a prediction is
dated, specific, falsifiable, attached to a thesis, and never a price.
"""

import datetime as dt
import re
from pathlib import Path

import pytest
import tomli


ROOT = Path(__file__).parent.parent
DOCUMENT = ROOT / "docs" / "WATCHLIST.md"
CONFIG = ROOT / "watchlist.toml"

CANDIDATE_ID = re.compile(r"^W-\d+$")
PREDICTION_ID = re.compile(r"^(W-\d+)\.\d+$")
DOC_SECTION = re.compile(r"^## (W-\d+) ", re.M)
DOC_THESIS = re.compile(r"\*\*Thesis\.\*\*\s+(.*?)(?:\n\s*\n|\Z)", re.S)
DOC_PREDICTION = re.compile(r"\*\*(W-\d+\.\d+)\*\*\s+(.*?)(?:\n\s*\n|\Z)", re.S)

CANDIDATE_KEYS = {"id", "ticker", "name", "currency", "added_on", "thesis",
                  "entry_condition", "status", "prediction"}
CANDIDATE_OPTIONAL = {"philosophy_check", "closed_on", "closed_reason"}
ENTRY_KINDS = {"valuation", "event"}
STATUSES = {"active", "closed"}

PREDICTION_KEYS = {"id", "made_on", "due", "statement", "kind"}
FIGURE_KEYS = {"metric", "bound", "value", "period"}
SCORE_KEYS = {"outcome", "source", "scored_on", "result"}
KINDS = {"figure", "event"}
RESULTS = {"right", "wrong"}
# Reported figures a prediction may be about. Nothing that depends on the
# price (DIRECTION.md invariant 7): free_cash_flow_yield is a philosophy
# metric and not a prediction metric.
PREDICTION_METRICS = {"revenue", "gross_margin", "operating_margin",
                      "return_on_invested_capital", "net_debt_to_ebitda",
                      "free_cash_flow"}
PERIOD = re.compile(r"^FY\d{4}$")


def _squash(text):
    return " ".join(text.split())


def _document():
    text = DOCUMENT.read_text(encoding="utf-8")
    starts = list(DOC_SECTION.finditer(text))
    sections = {}
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        body = text[m.start():end]
        thesis = DOC_THESIS.search(body)
        sections[m.group(1)] = {
            "thesis": _squash(thesis.group(1)) if thesis else None,
            "predictions": {p.group(1): _squash(p.group(2)) for p in DOC_PREDICTION.finditer(body)},
            "unchecked": "not yet checked" in body.lower(),
        }
    return sections


@pytest.fixture(scope="module")
def candidates():
    with open(CONFIG, "rb") as f:
        raw = tomli.load(f)
    assert set(raw) == {"candidate"}, "top-level keys nothing reads"
    ids = [c["id"] for c in raw["candidate"]]
    assert len(ids) == len(set(ids)), "a candidate appears twice"
    return {c["id"]: c for c in raw["candidate"]}


def _predictions(candidates):
    return {p["id"]: (cid, p) for cid, c in candidates.items() for p in c["prediction"]}


def test_document_has_two_candidates_and_four_predictions():
    doc = _document()
    assert len(doc) == 2
    assert sum(len(s["predictions"]) for s in doc.values()) == 4


def test_same_candidates_as_the_document(candidates):
    doc = _document()
    assert list(candidates) == list(doc)
    for cid, entry in candidates.items():
        assert _squash(entry["thesis"]) == doc[cid]["thesis"], cid


def test_same_predictions_as_the_document(candidates):
    doc = _document()
    for cid, entry in candidates.items():
        ids = [p["id"] for p in entry["prediction"]]
        assert ids == list(doc[cid]["predictions"]), cid
        for p in entry["prediction"]:
            assert _squash(p["statement"]) == doc[cid]["predictions"][p["id"]], p["id"]


def test_candidate_shape(candidates):
    doc = _document()
    for cid, entry in candidates.items():
        assert CANDIDATE_ID.match(cid), cid
        keys = set(entry)
        assert CANDIDATE_KEYS <= keys, (cid, CANDIDATE_KEYS - keys)
        assert keys <= CANDIDATE_KEYS | CANDIDATE_OPTIONAL, (cid, keys - CANDIDATE_KEYS - CANDIDATE_OPTIONAL)
        assert isinstance(entry["added_on"], dt.date), cid
        assert entry["thesis"].strip(), cid
        assert entry["currency"], cid
        assert entry["status"] in STATUSES, cid
        condition = entry["entry_condition"]
        assert condition["kind"] in ENTRY_KINDS, cid
        if condition["kind"] == "valuation":
            assert set(condition) == {"kind", "clause"} and condition["clause"] == "PHI-4.1", cid
        else:
            assert set(condition) == {"kind", "event"} and condition["event"].strip(), cid
        if "philosophy_check" in entry:
            check = entry["philosophy_check"]
            assert set(check) == {"checked_on", "fails"}, cid
            assert isinstance(check["checked_on"], dt.date), cid
            assert all(re.match(r"^PHI-\d+\.\d+$", f) for f in check["fails"]), cid
        else:
            assert doc[cid]["unchecked"], f"{cid}: no check record and the document does not say so"
        if entry["status"] == "closed":
            assert isinstance(entry.get("closed_on"), dt.date) and entry.get("closed_reason"), cid
        else:
            assert "closed_on" not in entry and "closed_reason" not in entry, cid
        assert entry["prediction"], f"{cid}: a thesis carries at least one prediction (PHI-6.1)"


def test_prediction_shape(candidates):
    seen = set()
    for pid, (cid, p) in _predictions(candidates).items():
        m = PREDICTION_ID.match(pid)
        assert m and m.group(1) == cid, f"{pid} is not attached to {cid} by its id"
        assert pid not in seen, pid
        seen.add(pid)
        keys = set(p)
        assert PREDICTION_KEYS <= keys, (pid, PREDICTION_KEYS - keys)
        assert isinstance(p["made_on"], dt.date) and isinstance(p["due"], dt.date), pid
        assert p["due"] > p["made_on"], f"{pid}: due is not after made_on"
        assert p["statement"].strip(), pid
        assert p["kind"] in KINDS, pid
        extra = keys - PREDICTION_KEYS
        if p["kind"] == "figure":
            assert FIGURE_KEYS <= extra, (pid, FIGURE_KEYS - extra)
            assert p["metric"] in PREDICTION_METRICS, (pid, p["metric"])
            assert p["bound"] in ("min", "max"), pid
            assert isinstance(p["value"], (int, float)) and not isinstance(p["value"], bool), pid
            assert PERIOD.match(p["period"]), pid
            extra -= FIGURE_KEYS
        assert extra <= SCORE_KEYS, (pid, extra - SCORE_KEYS)
        if extra:
            assert extra == SCORE_KEYS, f"{pid}: a score carries all four fields or none"
            assert isinstance(p["scored_on"], dt.date) and p["scored_on"] >= p["due"], pid
            assert p["result"] in RESULTS, pid
            assert p["source"].strip(), pid


def test_no_prediction_names_a_price(candidates):
    for pid, (_, p) in _predictions(candidates).items():
        text = p["statement"].lower()
        for phrase in ("share price", "stock price", "price target", "will be at", "will trade"):
            assert phrase not in text, (pid, phrase)
