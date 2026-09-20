"""
The outcome of case 4.3, composed from decision 68's four inputs
(expected_values.md Part 17 H, its sixteen rows).

The outcome supports an entry only when all four permit: the screen with
every philosophy clause passing, the gate with every finding ok or exempt,
my entry condition met, and the model's view of the thesis `stands`.
Anything else supports no entry, and the grounds name each input that did
not permit. One row of sixteen supports an entry.

**Not established is not a yes.** An input this cannot read - a condition
whose clause the screen never reached, a view the model did not give -
does not permit. It is named in the grounds like any other, and whoever
prints the answer words it as not established rather than as a no
(decision 68), reading which it was off the block. Nothing here words
anything: it returns the verdict and the names, and the formatter says it
in English. **The model's view can only take away**: there is no value of
it that turns a no into a yes, because every input must permit.

There is no partial credit, no third value beside the boolean and no
short-circuiting: every input is judged whatever the first of them says,
so row 13's grounds name the gate as well as the screen and the answer
carries both policy checks' findings.

**The gate's verdict is read, not recomputed.** `Gate.permits` is
decision 68's rule over the gate's own findings and `gate_node` publishes
it as `permits`; this module consumes it. `tests/benchmark/run_cases.py`
derives the same thing from the findings, which makes the check an
independent cross-check of the block rather than a second implementation
inside the pipeline.

The screen has no such field: nothing publishes whether it is clear, so
it is derived here, in the one place that asks. It is derived by the rule
`check_4_3` asserts, with one difference named here: a screen with no
stop and no finding permits under the check, because `all()` over nothing
is true, and does not permit here. A screen that computed no finding
established nothing, and an input that established nothing never grants
an entry. The difference cannot make the case fail, since it can only
withhold one.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple

from portfolio_tool.entry import EntryCondition
from portfolio_tool.screening import PASS
from portfolio_tool.thesis_view import ThesisView

__all__ = ["Outcome", "GROUNDS", "STANDS", "compose"]

# The four inputs, in the order Part 17 H's columns stand and the grounds
# are listed.
SCREEN = "screen"
GATE = "gate"
ENTRY_CONDITION = "entry_condition"
THESIS_VIEW = "thesis_view"
GROUNDS = (SCREEN, GATE, ENTRY_CONDITION, THESIS_VIEW)
# The one view that permits (decision 68).
STANDS = "stands"


@dataclass(frozen=True)
class Outcome:
    """Whether the four inputs support an entry, and which of them did not
    permit. `grounds` is empty exactly when `supports_entry` is true."""
    supports_entry: bool
    grounds: Tuple[str, ...]


def _screen_permits(screen: Optional[Mapping[str, Any]]) -> bool:
    if not isinstance(screen, Mapping) or screen.get("stopped"):
        return False
    findings = screen.get("findings")
    if not isinstance(findings, Sequence) or not findings:
        return False
    return all(isinstance(f, Mapping) and f.get("status") == PASS for f in findings)


def _gate_permits(gate: Optional[Mapping[str, Any]]) -> bool:
    """The gate's own verdict, read and not recomputed. `Gate.permits` is
    decision 68's rule over the gate's findings - every finding ok or
    exempt - `gate_node` publishes it on the block, and
    `tests/test_gate.py` holds it. Deriving it again here would be a
    second implementation of one rule, and the first version of this
    module did exactly that."""
    return isinstance(gate, Mapping) and gate.get("permits") is True


def _condition_permits(condition: Optional[EntryCondition]) -> bool:
    return isinstance(condition, EntryCondition) and condition.met is True


def _view_permits(view: Optional[ThesisView]) -> bool:
    return isinstance(view, ThesisView) and view.thesis_view == STANDS


def compose(screen: Optional[Mapping[str, Any]], gate: Optional[Mapping[str, Any]],
            condition: Optional[EntryCondition], view: Optional[ThesisView]) -> Outcome:
    """The outcome decision 68 composes from the four (Part 17 H). Each
    argument may be absent, which does not permit and is named in the
    grounds; nothing here raises, because every state of the four is a row
    of the table."""
    permits = {
        SCREEN: _screen_permits(screen),
        GATE: _gate_permits(gate),
        ENTRY_CONDITION: _condition_permits(condition),
        THESIS_VIEW: _view_permits(view),
    }
    grounds = tuple(name for name in GROUNDS if not permits[name])
    return Outcome(supports_entry=not grounds, grounds=grounds)
