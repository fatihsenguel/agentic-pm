"""
portfolio_tool.entry: my entry condition read against the screen's finding
on its clause, held to expected_values.md Part 17 I and its note of
2026-09-20, and to `check_4_3`'s rule.

The findings are built here as the node publishes them, plain mappings
with a clause and a status, because that is what the block carries; the
screen's own dataclass is held by its own tests. `PASS`, `FAIL` and
`EXCLUDED` are imported from the screen so the status words live once.

The rules, each a test:

  - a finding that passes makes the condition met; one that fails makes it
    not met
  - **no finding on the clause makes it None, not established**, which is
    what a stopped screen looks like and is the live answer on Alphabet
  - the kind's vocabulary is here: `valuation` is read and an event
    condition stops naming itself
  - a valuation condition that names no clause stops, the loader having
    taken the table as stated
  - two findings on one clause stop: a clause has one verdict (D22)
  - the type guards: a condition that is not a table, findings that are
    not a list
  - nothing is computed from a price or a range, so no arithmetic beside
    the screen's
"""

import pytest

from portfolio_tool import entry
from portfolio_tool.screening import EXCLUDED, FAIL, PASS

VALUATION = {"kind": "valuation", "clause": "PHI-4.1"}


def finding(clause="PHI-4.1", status=PASS):
    return {"clause": clause, "type": "margin_of_safety", "subject": "GOOGL",
            "status": status, "distance": 0.1}


# --- the three answers ---------------------------------------------------------

def test_a_finding_that_passes_makes_the_condition_met():
    read = entry.read(VALUATION, [finding()])
    assert (read.kind, read.clause, read.met) == ("valuation", "PHI-4.1", True)


def test_a_finding_that_fails_makes_the_condition_not_met():
    assert entry.read(VALUATION, [finding(status=FAIL)]).met is False


def test_no_finding_on_the_clause_is_not_established_and_not_a_no():
    """Part 17 I's note: a screen that stopped reports a finding on no
    clause (PHI-1.2, D25), so there is no verdict on PHI-4.1 to read.
    None and not False - decision 68 words a stop as not established."""
    assert entry.read(VALUATION, []).met is None


def test_a_screen_that_stopped_elsewhere_is_still_not_established():
    """The live shape on Alphabet: the screen stops at PHI-2.1 and the
    node publishes findings empty. A finding on some other clause is the
    same case as none, since the clause read is PHI-4.1."""
    assert entry.read(VALUATION, [finding(clause="PHI-2.2")]).met is None


def test_an_excluded_finding_on_the_clause_is_not_met():
    """`check_4_3` reads met as the finding's status being exactly `pass`,
    so anything else is not met. Held here so the two agree by rule and
    not by luck; no philosophy clause but PHI-3.2 is ever excluded, so
    this is the guard and not a live case."""
    assert entry.read(VALUATION, [finding(status=EXCLUDED)]).met is False


# --- the kind's vocabulary -----------------------------------------------------

def test_valuation_is_the_kind_this_reads():
    assert entry.KINDS == ("valuation",)
    assert entry.VALUATION == "valuation"


def test_an_event_condition_stops_naming_itself():
    with pytest.raises(entry.EntryError, match="'event' is not one this reads"):
        entry.read({"kind": "event", "event": "the cloud segment turns a full-year profit"},
                   [finding()])


def test_a_kind_the_watchlist_states_and_this_does_not_read_stops():
    """The loader takes any non-empty kind (D42's shape); the stop is
    here, where the word is read."""
    with pytest.raises(entry.EntryError, match="'phase of the moon' is not one this reads"):
        entry.read({"kind": "phase of the moon", "omen": "a waxing crescent"}, [finding()])


@pytest.mark.parametrize("clause", [None, "", "   ", 3], ids=["absent", "empty",
                                                              "whitespace", "a number"])
def test_a_valuation_condition_naming_no_clause_stops(clause):
    stated = {"kind": "valuation"} if clause is None else {"kind": "valuation",
                                                           "clause": clause}
    with pytest.raises(entry.EntryError, match="names no clause"):
        entry.read(stated, [finding()])


# --- one verdict a clause -------------------------------------------------------

def test_two_findings_on_one_clause_stop():
    with pytest.raises(entry.EntryError, match="2 findings on PHI-4.1"):
        entry.read(VALUATION, [finding(), finding(status=FAIL)])


# --- the type guards ------------------------------------------------------------

@pytest.mark.parametrize("stated", ["valuation", ["valuation"], None])
def test_a_condition_that_is_not_a_table_stops(stated):
    with pytest.raises(entry.EntryError, match="is a table, not"):
        entry.read(stated, [finding()])


@pytest.mark.parametrize("findings", ["PHI-4.1", {"clause": "PHI-4.1"}, None],
                         ids=["a string", "one mapping", "none"])
def test_findings_that_are_not_a_list_stop(findings):
    with pytest.raises(entry.EntryError, match="not the screen's list of findings"):
        entry.read(VALUATION, findings)


def test_a_finding_that_is_not_a_mapping_is_not_a_finding_on_the_clause():
    """A list with rubbish in it reads as no finding on the clause rather
    than raising on the rubbish: the screen's own tests hold the shape of
    what it publishes, and this module's answer is about the clause."""
    assert entry.read(VALUATION, ["PHI-4.1", None]).met is None


# --- no arithmetic --------------------------------------------------------------

def test_the_record_carries_no_figure():
    read = entry.read(VALUATION, [finding()])
    assert [f for f in vars(read)] == ["kind", "clause", "met"]


def test_a_price_and_a_range_on_the_finding_are_not_read():
    """The condition is the screen's verdict, not this module's
    arithmetic: the same finding with a price and a range attached gives
    the same answer, and nothing here divides one by the other."""
    bare = entry.read(VALUATION, [finding()])
    rich = entry.read(VALUATION, [{**finding(), "observed": 0.72, "limit": 0.25,
                                   "price_as_of": "2026-09-18",
                                   "range_as_of": "2026-09-18"}])
    assert bare == rich
