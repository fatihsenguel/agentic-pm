"""
portfolio_tool.outcome: decision 68's composition, held to all sixteen
rows of expected_values.md Part 17 H.

`check_4_3` holds one of those rows - the one no rule may break, that an
entry is not supported unless all four permit - and until this file
nothing held the other fifteen: a run that named the wrong grounds, or
none, would have passed the runner (KNOWN_GAPS). The table below is
transcribed from the Part, row for row, with the grounds written out as
the Part lists them, so that the harness is the reference and not the
code's own output.

Beyond the table: an input that is absent does not permit and is named,
which is the not-established case and is the live one on Alphabet; the
statuses the screen and the gate are judged by are the words their own
modules define; `exempt` is clear and `breach` is not; the view can only
take away; and `grounds` is empty exactly when an entry is supported.
"""

import pytest

from portfolio_tool import outcome
from portfolio_tool.compliance import BREACH, EXEMPT, OK, REFUSED
from portfolio_tool.entry import EntryCondition
from portfolio_tool.screening import EXCLUDED, FAIL, PASS
from portfolio_tool.thesis_view import ThesisView


def screen(clear=True):
    """A screening block that permits, or one that stopped the way
    Alphabet's does."""
    if clear:
        return {"findings": [{"clause": "PHI-2.1", "status": PASS},
                             {"clause": "PHI-4.1", "status": PASS}], "stopped": None}
    return {"findings": [], "stopped": {"clause": "PHI-2.1", "reason": "a figure is missing"}}


def gate(clear=True):
    """A gate block that permits, or one that fails IPS-3.1 the way this
    portfolio's does at every weight."""
    statuses = [OK, EXEMPT] if clear else [OK, BREACH]
    return {"ticker": "GOOGL", "weight": 0.06,
            "findings": [{"clause": f"IPS-3.{n}", "status": s}
                         for n, s in enumerate(statuses, start=1)]}


def condition(met=True):
    return EntryCondition(kind="valuation", clause="PHI-4.1", met=met)


def view(stands=True):
    return ThesisView(thesis_view="stands" if stands else "strained",
                      reasons=("1.1",), uncertainty="stated")


# Part 17 H, transcribed: the four inputs and the grounds the Part lists.
# `True` is the permitting state of each column.
ROWS = [
    (1,  True,  True,  True,  True,  True,  ()),
    (2,  True,  True,  True,  False, False, ("thesis_view",)),
    (3,  True,  True,  False, True,  False, ("entry_condition",)),
    (4,  True,  True,  False, False, False, ("entry_condition", "thesis_view")),
    (5,  True,  False, True,  True,  False, ("gate",)),
    (6,  True,  False, True,  False, False, ("gate", "thesis_view")),
    (7,  True,  False, False, True,  False, ("gate", "entry_condition")),
    (8,  True,  False, False, False, False, ("gate", "entry_condition", "thesis_view")),
    (9,  False, True,  True,  True,  False, ("screen",)),
    (10, False, True,  True,  False, False, ("screen", "thesis_view")),
    (11, False, True,  False, True,  False, ("screen", "entry_condition")),
    (12, False, True,  False, False, False, ("screen", "entry_condition", "thesis_view")),
    (13, False, False, True,  True,  False, ("screen", "gate")),
    (14, False, False, True,  False, False, ("screen", "gate", "thesis_view")),
    (15, False, False, False, True,  False, ("screen", "gate", "entry_condition")),
    (16, False, False, False, False, False, ("screen", "gate", "entry_condition",
                                             "thesis_view")),
]


# --- all sixteen rows ----------------------------------------------------------

@pytest.mark.parametrize("n, s, g, c, v, supports, grounds", ROWS,
                         ids=[f"row {r[0]}" for r in ROWS])
def test_part_17_h_row(n, s, g, c, v, supports, grounds):
    result = outcome.compose(screen(s), gate(g), condition(c), view(v))
    assert result.supports_entry is supports
    assert result.grounds == grounds


def test_the_table_is_the_parts_sixteen_rows_and_one_supports_an_entry():
    """The harness is complete on its own terms: sixteen rows, every
    combination of the four once, and exactly one supporting an entry."""
    assert len(ROWS) == 16
    assert len({r[1:5] for r in ROWS}) == 16
    assert [r[0] for r in ROWS] == list(range(1, 17))
    assert sum(1 for r in ROWS if r[5]) == 1


def test_the_grounds_are_listed_in_the_parts_column_order():
    assert outcome.GROUNDS == ("screen", "gate", "entry_condition", "thesis_view")
    for row in ROWS:
        assert list(row[6]) == [g for g in outcome.GROUNDS if g in row[6]]


def test_grounds_are_empty_exactly_when_an_entry_is_supported():
    for row in ROWS:
        result = outcome.compose(screen(row[1]), gate(row[2]), condition(row[3]),
                                 view(row[4]))
        assert result.supports_entry is (result.grounds == ())


# --- an input that is absent: not established, and never a yes -----------------

@pytest.mark.parametrize("missing", ["screen", "gate", "condition", "view"])
def test_an_absent_input_does_not_permit_and_is_named(missing):
    """Part 17 I: the model's view was not established and the outcome is
    row 15 with it named. Absence is not a state of its own here - it does
    not permit, like any other non-permitting state."""
    parts = {"screen": screen(), "gate": gate(), "condition": condition(), "view": view()}
    parts[missing] = None
    result = outcome.compose(parts["screen"], parts["gate"], parts["condition"],
                             parts["view"])
    named = {"screen": "screen", "gate": "gate", "condition": "entry_condition",
             "view": "thesis_view"}[missing]
    assert result.supports_entry is False
    assert result.grounds == (named,)


def test_the_live_shape_on_alphabet_is_row_15():
    """The screen stops at PHI-2.1, the gate fails IPS-3.1 at every
    weight, the entry condition is not established because the screen
    reported no finding on PHI-4.1, and no view was given."""
    result = outcome.compose(screen(clear=False), gate(clear=False),
                             EntryCondition(kind="valuation", clause="PHI-4.1", met=None),
                             None)
    assert result.supports_entry is False
    assert result.grounds == ("screen", "gate", "entry_condition", "thesis_view")


def test_a_condition_not_established_does_not_permit():
    result = outcome.compose(screen(), gate(),
                             EntryCondition(kind="valuation", clause="PHI-4.1", met=None),
                             view())
    assert (result.supports_entry, result.grounds) == (False, ("entry_condition",))


@pytest.mark.parametrize("value", ["strained", "no_view"])
def test_no_view_but_stands_takes_away(value):
    """The model's view can only take away: no value of it turns a no into
    a yes, and only `stands` leaves the other three deciding."""
    result = outcome.compose(screen(), gate(),
                             condition(),
                             ThesisView(thesis_view=value, reasons=(), uncertainty="inferred"))
    assert (result.supports_entry, result.grounds) == (False, ("thesis_view",))


def test_stands_is_the_one_view_that_permits():
    assert outcome.STANDS == "stands"


# --- the statuses each policy check is judged by -------------------------------

@pytest.mark.parametrize("status, clear", [(OK, True), (EXEMPT, True), (BREACH, False),
                                           (REFUSED, False)])
def test_a_gate_finding_is_clear_on_ok_and_exempt_and_on_nothing_else(status, clear):
    """`exempt` is clear and is not `ok`: IPS-4.2 was applied to a fund and
    does not attribute it to an issuer (Part 17 E)."""
    block = {"findings": [{"clause": "IPS-4.1", "status": status}]}
    result = outcome.compose(screen(), block, condition(), view())
    assert result.supports_entry is clear
    assert outcome.GATE_CLEAR == (OK, EXEMPT)


@pytest.mark.parametrize("status, clear", [(PASS, True), (FAIL, False), (EXCLUDED, False)])
def test_a_screen_finding_permits_on_pass_and_on_nothing_else(status, clear):
    block = {"findings": [{"clause": "PHI-2.2", "status": status}], "stopped": None}
    result = outcome.compose(block, gate(), condition(), view())
    assert result.supports_entry is clear


def test_one_failed_finding_among_many_stops_the_check():
    block = {"findings": [{"clause": "PHI-2.1", "status": PASS},
                          {"clause": "PHI-2.2", "status": FAIL},
                          {"clause": "PHI-4.1", "status": PASS}], "stopped": None}
    assert outcome.compose(block, gate(), condition(), view()).grounds == ("screen",)


def test_a_stop_beside_passing_findings_still_does_not_permit():
    """A screen that stopped reports no finding, but a block carrying both
    is not read as clear: the stop is what decides."""
    block = {"findings": [{"clause": "PHI-2.1", "status": PASS}],
             "stopped": {"clause": "PHI-3.1", "reason": "a figure is missing"}}
    assert outcome.compose(block, gate(), condition(), view()).grounds == ("screen",)


@pytest.mark.parametrize("block", [{"findings": [], "stopped": None},
                                   {"findings": None, "stopped": None},
                                   {"stopped": None}],
                         ids=["empty", "none", "absent"])
def test_a_screen_with_no_finding_does_not_permit(block):
    """Stricter than `check_4_3`, on purpose and named in the module: the
    check's `all()` over nothing is true, so a screen with no stop and no
    finding would permit there. A screen that computed no finding
    established nothing. The difference can only withhold an entry, never
    grant one, so it cannot make the case fail."""
    assert outcome.compose(block, gate(), condition(), view()).grounds == ("screen",)


@pytest.mark.parametrize("block", [{"findings": []}, {"findings": None}, {}],
                         ids=["empty", "none", "absent"])
def test_a_gate_with_no_finding_does_not_permit(block):
    """The gate's own rule, and `check_4_3`'s: a gate that ran and found
    nothing is no policy any clause allows (Part 17 D60). A gate that
    could not run publishes no block at all and the guard stops the answer
    before this is reached."""
    assert outcome.compose(screen(), block, condition(), view()).grounds == ("gate",)


# --- no short-circuiting -------------------------------------------------------

def test_every_input_is_judged_whatever_the_first_says():
    """Row 13: the screen stopped and the gate's findings are still
    judged, so the answer carries both policy checks (Part 17 H)."""
    result = outcome.compose(screen(clear=False), gate(clear=False), condition(), view())
    assert result.grounds == ("screen", "gate")


def test_the_record_carries_the_verdict_and_the_names_and_no_prose():
    result = outcome.compose(screen(), gate(), condition(), view())
    assert [f for f in vars(result)] == ["supports_entry", "grounds"]
    assert result.supports_entry is True and result.grounds == ()
