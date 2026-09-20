"""
The gate: the IPS applied to a candidate at a stated weight, before the
answer that implies the position is shown (DIRECTION.md invariant 2).

Pure functions over dicts and a Candidate. No database, no LLM, no state.

**This is not a second checker.** It builds the allocation the portfolio
would have after the purchase and hands it to `compliance.check`, so Part 7
and Part 17 of `tests/golden/expected_values.md` are reproduced by one
piece of clause arithmetic. The only thing computed here that the checker
does not compute is IPS-5.3's finding, which the checker cannot produce
because IPS-5.3 is a statement clause (Part 17 D59, D60).

Reference: Part 17, computed by hand before this existed, and its
decisions, with the session decisions it rests on:

  64  The purchase is funded by **new money on top of the portfolio**, so
      the stated weight is the candidate's share of the grown total:
      M = w x T / (1 - w) and T' = T / (1 - w). Nothing is sold, no
      existing market value changes, and every existing share becomes its
      old share times (1 - w). The candidate's share is w exactly, which
      is why its line carries `weight` rather than a division.
  65  The weight is the watchlist entry's, and `weight_source` is that
      entry's id. This module takes both as given; reading them is
      `watchlist.position_weight`'s.
  68  The gate permits only when every finding is ok or exempt. It checks
      the whole portfolio as it would be and not the candidate's rows
      alone: on this portfolio a purchase can clear one clause by dilution
      while deepening another, and a gate that saw only the candidate
      would report the first and miss the second (Part 17 E).
  D59 IPS-5.3 is a finding of pass or fail with its grounds and no
      distance: it is a rule about where money goes, not a limit on a
      figure, so no amount returns anything to a limit.
  D60 The four typed clause kinds over the portfolio as it would be, plus
      IPS-5.3. Statement clauses produce no finding and are named as not
      computed by whoever prints this.

**IPS-5.3's second limb is not computed.** The clause reads "New money is
allocated first to whatever restores a breached limit, then to whichever
asset class is furthest below the middle of its band." The first limb is
computed here and is a guardrail: a purchase that leaves a breached limit
breached fails it. The second limb is an allocation preference, and
enforcing it would block a purchase for being a worse use of the next
dollar rather than for breaking a limit - a recommendation with the force
of a refusal. So `first_limb_binds` says whether the first limb decided
the finding, and when it did not the clause is half-applied and whoever
prints it says so. Decided 2026-09-20; the entry in KNOWN_GAPS carries the
trigger, the first portfolio state with no limit breached.

Raise, do not repair. A candidate already held, an asset class no band
clause names, a share whose sector is the unsectored label, a weight
outside (0, 1): each would otherwise become a plausible verdict.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from portfolio_tool.compliance import (
    BREACH, EXEMPT, FUND, OK, Finding, check,
)
from portfolio_tool.ips import IPS
from portfolio_tool.quant.allocation import UNSECTORED_LABEL
from portfolio_tool.watchlist import Candidate

__all__ = ["Gate", "GateError", "gate", "NEW_MONEY_CLAUSE", "FUNDING"]

# The clause decision 64 makes directly applicable to the purchase.
NEW_MONEY_CLAUSE = "IPS-5.3"
STATEMENT = "statement"
# How the purchase is paid for, carried into the block so that the answer
# states it: every figure below depends on it.
FUNDING = "new money on top of the portfolio"


class GateError(Exception):
    """Raised when the policy cannot be applied honestly to the purchase."""


@dataclass(frozen=True)
class Gate:
    """One candidate checked at one weight.

    `findings` is the portfolio as it would be; `findings_before` is the
    same clauses over the portfolio as it stands, so that a reader can see
    whether the purchase moved a clause and in which direction (Part 17 A).
    Both are in the compliance finding's shape.

    `unrestored` names the (clause, subject) pairs that were breached
    before and are breached still - IPS-5.3's grounds as data, worded by
    whoever prints it. `first_limb_binds` is False when nothing was
    breached before, and then the clause is half-applied.
    """

    ticker: str
    weight: float
    weight_source: str
    funding: str
    asset_class: str
    sector: str
    instrument_type: str
    new_money: float
    total_before: float
    total_after: float
    findings: Tuple[Finding, ...]
    findings_before: Tuple[Finding, ...]
    first_limb_binds: bool
    unrestored: Tuple[Tuple[str, str], ...]

    @property
    def permits(self) -> bool:
        """Decision 68: every finding ok or exempt, or the gate does not
        permit. The outcome is composed elsewhere; this says only what the
        gate itself found."""
        return all(f.status in (OK, EXEMPT) for f in self.findings)


def gate(
    ips: IPS,
    allocation: Mapping,
    instrument_types: Mapping[str, Optional[str]],
    candidate: Candidate,
    weight: float,
    weight_source: str,
) -> Gate:
    """The IPS over the portfolio as it would be with `candidate` bought at
    `weight`, funded by new money on top (decision 64).

    Args:
        ips: the loaded policy
        allocation: `shared_data["allocation"]` as PortfolioAnalysisAgent
            publishes it, the same block `compliance.check` reads
        instrument_types: ticker -> 'share' | 'fund', one per held position
        candidate: the watchlist entry, for its ticker and its three
            classification words (decision 63)
        weight: the candidate's share of the grown total
        weight_source: the id of the entry that states the weight (65)
    """
    if not isinstance(weight, float) or not 0 < weight < 1:
        raise GateError(
            f"Weight {weight!r} is not a fraction above 0 and below 1. A purchase of "
            "nothing is not a position, and at a weight of 1 the funding asks for an "
            "infinite amount of new money."
        )

    total_before = (allocation.get("by_asset_class") or {}).get("total_value")
    if total_before is None or total_before <= 0:
        raise GateError(
            f"Total portfolio value is {total_before!r}; the weight is a share of the "
            "total after the purchase and there is nothing to take a share of."
        )

    held = {line["label"] for line in (allocation.get("by_position") or {}).get("lines") or []}
    if candidate.ticker in held:
        raise GateError(
            f"{candidate.ticker} is already a position in this portfolio. The gate checks a "
            "new position at a stated weight; adding to one already held is a different "
            "question and no case asks it."
        )

    bands = {c.params["asset_class"] for c in ips.checkable if c.type == "asset_class_band"}
    if candidate.asset_class not in bands:
        raise GateError(
            f"{candidate.id} ({candidate.ticker}) states asset class {candidate.asset_class!r}; "
            f"the policy has a band for {sorted(bands)}. A class the policy states no band for "
            "cannot be checked against section 3, and a position in it is not reported as clear."
        )

    if candidate.instrument_type != FUND and candidate.sector == UNSECTORED_LABEL:
        raise GateError(
            f"{candidate.id} ({candidate.ticker}) is a {candidate.instrument_type} whose sector "
            f"is {UNSECTORED_LABEL!r}, the label IPS-4.3 leaves out of its count. A directly "
            "held share is counted in a sector or the clause is not applied to it."
        )

    new_money = weight * total_before / (1 - weight)
    total_after = total_before + new_money

    after = _with_candidate(allocation, candidate, weight, new_money, total_after)
    types_after = dict(instrument_types)
    types_after[candidate.ticker] = candidate.instrument_type

    findings = tuple(check(ips, after, types_after))
    findings_before = tuple(check(ips, allocation, instrument_types))

    breached_before = {(f.clause, f.subject) for f in findings_before if f.status == BREACH}
    breached_after = {(f.clause, f.subject) for f in findings if f.status == BREACH}
    unrestored = tuple(sorted(breached_before & breached_after))

    return Gate(
        ticker=candidate.ticker,
        weight=weight,
        weight_source=weight_source,
        funding=FUNDING,
        asset_class=candidate.asset_class,
        sector=candidate.sector,
        instrument_type=candidate.instrument_type,
        new_money=new_money,
        total_before=total_before,
        total_after=total_after,
        findings=findings + (_new_money_finding(candidate, bool(breached_before), unrestored),),
        findings_before=findings_before,
        first_limb_binds=bool(breached_before),
        unrestored=unrestored,
    )


def _new_money_finding(
    candidate: Candidate, first_limb_binds: bool, unrestored: Sequence[Tuple[str, str]]
) -> Finding:
    """IPS-5.3 over the purchase (D59). The subject is the asset class the
    money went to, since that is what the clause is about. No arithmetic:
    a rule about where money goes has no distance.

    First limb: a limit is breached and the money must restore it. It fails
    when any limit breached before the purchase is breached after it - the
    money went somewhere that left it standing. Second limb: not computed
    (see the module's docstring), so with nothing breached before, the
    finding is ok and half the clause is unapplied.
    """
    status = BREACH if (first_limb_binds and unrestored) else OK
    return Finding(
        clause=NEW_MONEY_CLAUSE,
        type=STATEMENT,
        subject=candidate.asset_class,
        observed=None,
        limit=None,
        bound=None,
        status=status,
        distance_pp=None,
        distance_value=None,
    )


def _with_candidate(
    allocation: Mapping,
    candidate: Candidate,
    weight: float,
    new_money: float,
    total_after: float,
) -> Dict[str, Dict[str, Any]]:
    """The allocation the portfolio would have. Every existing line keeps
    its market value and takes a smaller share of the larger total; the
    candidate gets a line in each of the three views, at `weight` exactly
    rather than at a division, since decision 64 defines the weight as that
    share.

    `pct_of_invested` and `pct_of_sectored` are carried as None. Nothing
    checked here reads them, and a stale figure that looks computed is
    worse than an absent one.
    """
    by_class = _view(allocation, "by_asset_class", total_after)
    by_sector = _view(allocation, "by_sector", total_after)
    by_position = _view(allocation, "by_position", total_after)

    _add(by_class, candidate.asset_class, candidate.ticker, new_money, total_after)
    sector_label = (UNSECTORED_LABEL if candidate.instrument_type == FUND
                    else candidate.sector)
    _add(by_sector, sector_label, candidate.ticker, new_money, total_after)
    _add(by_position, candidate.ticker, candidate.ticker, new_money, total_after)

    # The candidate's own share is the weight, by decision 64's definition,
    # rather than a division that would land a hair off it. Only the
    # position line is the candidate alone; its class and sector lines hold
    # whatever else sits in that bucket and keep their divisions.
    for line in by_position["lines"]:
        if line["label"] == candidate.ticker:
            line["pct_of_total"] = weight

    return {"by_asset_class": by_class, "by_sector": by_sector, "by_position": by_position}


def _view(allocation: Mapping, name: str, total_after: float) -> Dict[str, Any]:
    block = allocation.get(name) or {}
    lines = block.get("lines")
    if not lines:
        raise GateError(
            f"The allocation has no {name} lines. The gate checks the portfolio as it "
            "would be against every clause, and a view it cannot build is a clause it "
            "cannot apply."
        )
    return {
        "lines": [
            {
                "label": line["label"],
                "market_value": line["market_value"],
                "cost_basis": line.get("cost_basis"),
                "tickers": list(line.get("tickers") or []),
                "pct_of_sectored": None,
                "pct_of_invested": None,
                "pct_of_total": line["market_value"] / total_after,
            }
            for line in lines
        ],
        "total_value": total_after,
    }


def _add(
    view: Dict[str, Any], label: str, ticker: str, new_money: float, total_after: float
) -> None:
    """The purchase into one view: an existing bucket grows, an absent one
    is opened. A new bucket is the normal case for a sector the portfolio
    does not hold and for a ticker it does not own."""
    for line in view["lines"]:
        if line["label"] == label:
            line["market_value"] += new_money
            line["cost_basis"] = (line["cost_basis"] or 0.0) + new_money
            if ticker not in line["tickers"]:
                line["tickers"].append(ticker)
            line["pct_of_total"] = line["market_value"] / total_after
            return
    view["lines"].append({
        "label": label,
        "market_value": new_money,
        "cost_basis": new_money,
        "tickers": [ticker],
        "pct_of_sectored": None,
        "pct_of_invested": None,
        "pct_of_total": new_money / total_after,
    })
