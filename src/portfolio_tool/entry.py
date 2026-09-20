"""
My entry condition, read against the screen's finding on its clause
(case 4.3; decision 68; expected_values.md Part 17 I).

The third of decision 68's four inputs. The condition is mine, stated on
the watchlist entry and loaded as written; whether it is met is the
screen's to say, not this module's: a `valuation` condition names a
philosophy clause, and the condition is met exactly when the screen's
finding on that clause passes. Nothing here computes a price, a range or
a distance, so there is no second arithmetic path beside the screen's.

Three answers, and the third is the one to read carefully:

  - **met**, the screen's finding on the clause passes;
  - **not met**, the finding does not pass;
  - **not established**, `None`, the screen reported no finding on the
    clause at all. That is what a stopped screen looks like: PHI-1.2 and
    D25 say a clause is never skipped to let the rest of the screen report
    a verdict, so a screen that stopped reports a finding on nothing, and
    there is no verdict on the entry condition to read. Decision 68 words
    a stop as not established, never as a no. On Alphabet today the screen
    stops at PHI-2.1, so this is the live answer and it is not a defect
    (Part 17 I's note of 2026-09-20).

The kind's vocabulary lives here and not in the loader, the shape D42 gave
the prediction metric: the loader takes any non-empty kind and this module
stops on one it has no rule for. `valuation` is the one kind it reads. An
`event` condition stops naming itself: the condition is met when the event
happens, and nothing in this system is told that it did, so a verdict on
one would be invented. Both candidates state a valuation condition, so
nothing is wrong today and no rule is written for a case nobody asks.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from portfolio_tool.screening import PASS
from portfolio_tool.watchlist import ENTRY_KIND

__all__ = ["EntryCondition", "EntryError", "VALUATION", "KINDS", "read"]

VALUATION = "valuation"
# The kinds this module has a rule for. A kind the watchlist states and
# this tuple does not name stops, naming it.
KINDS = (VALUATION,)
CLAUSE = "clause"


class EntryError(Exception):
    """Raised when an entry condition cannot honestly be read."""


@dataclass(frozen=True)
class EntryCondition:
    """My entry condition and where it stands: the kind and the clause as
    the watchlist states them, and `met` True, False, or None when the
    screen established no verdict on the clause."""
    kind: str
    clause: str
    met: Optional[bool]


def read(stated: Mapping[str, Any], findings: Sequence[Mapping[str, Any]]) -> EntryCondition:
    """My entry condition as `stated` on the watchlist entry, read against
    the screen's `findings`, or a refusal naming why."""
    if not isinstance(stated, Mapping):
        raise EntryError(f"an entry condition is a table, not {type(stated).__name__}.")
    kind = stated.get(ENTRY_KIND)
    if kind not in KINDS:
        raise EntryError(
            f"entry condition kind {kind!r} is not one this reads; it reads "
            f"{', '.join(KINDS)}. An event condition is met when the event happens, and "
            "nothing here is told that it did, so there is no verdict to report."
        )
    clause = stated.get(CLAUSE)
    if not isinstance(clause, str) or not clause.strip():
        raise EntryError(f"a {VALUATION} entry condition names no clause; it is met when the "
                         "screen's finding on a philosophy clause passes, and without the "
                         "clause there is nothing to read.")

    # A string and a single mapping are both refused before the list is
    # read: a string is a Sequence, and iterating one gives characters,
    # none of which is a finding - so the answer would come back as "not
    # established" for an argument of the wrong type, which is a wrong
    # answer with a plausible face.
    if isinstance(findings, (str, bytes, Mapping)) or not isinstance(findings, Sequence):
        raise EntryError(f"findings is {type(findings).__name__}, not the screen's list of "
                         "findings.")
    on_clause = [f for f in findings if isinstance(f, Mapping) and f.get("clause") == clause]
    if len(on_clause) > 1:
        raise EntryError(f"the screen reports {len(on_clause)} findings on {clause}; a clause "
                         "has one verdict (D22), and two is a defect upstream.")
    # No finding on the clause: not established, never a no. A screen that
    # stopped reports a finding on no clause (PHI-1.2, D25).
    met = (on_clause[0].get("status") == PASS) if on_clause else None
    return EntryCondition(kind=kind, clause=clause, met=met)
