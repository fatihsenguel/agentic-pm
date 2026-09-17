"""
The watchlist as config: docs/WATCHLIST.md and watchlist.toml, the
candidates I want to own and, for each, the growth I assume for its
valuation range (Part 11 D38).

What this reads: each candidate's id, ticker, name, currency and status,
and its valuation table, `growth_low` and `growth_high`, both or neither.
What it leaves alone: the prediction rows, which are the scorer's (case
4.5) and are read by nothing yet; a loader that carried them now would be
carrying what nothing consumes.

Policy lives in config, not code. This module loads and validates; it
computes nothing and defaults nothing: a missing file is an error, a
candidate that states no pair has no range until it does, and a ticker
that is not on the list is not a candidate. The order of the two ends is
not checked here: quant/valuation.py raises on a reversed or equal pair,
so that rule lives in one place.
"""

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional

import tomli

from portfolio_tool.clauses import resolve_path

__all__ = ["Candidate", "Watchlist", "WatchlistError", "load_watchlist", "growth_pair",
           "CANDIDATE_ID", "STATUSES"]

CANDIDATE_ID = re.compile(r"^W-\d+$")
STATUSES = ("active", "closed")
_HEADER = ("id", "ticker", "name", "currency", "status")
# The two ends the range reads from the entry (Part 11 D38); a table
# stating anything else is stating something the range does not read.
GROWTH = ("growth_low", "growth_high")


class WatchlistError(Exception):
    """Raised when the watchlist cannot be loaded as a valid one, or when a
    candidate asked for is not on it or states no growth pair."""


@dataclass(frozen=True)
class Candidate:
    id: str
    ticker: str
    name: str
    currency: str
    status: str
    growth: Optional[Mapping[str, float]] = None


@dataclass(frozen=True)
class Watchlist:
    candidates: Mapping[str, Candidate]
    path: str

    def by_ticker(self, ticker: str) -> Candidate:
        for candidate in self.candidates.values():
            if candidate.ticker == ticker:
                return candidate
        raise WatchlistError(f"{ticker} is not on the watchlist ({self.path}); a range is "
                             "for a candidate, and no growth is stated for anyone else.")


def _is_fraction(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and -1 < value < 1


def load_watchlist(path: str) -> Watchlist:
    """Load and validate the watchlist.toml at `path`, relative to the
    project root or absolute. Raises WatchlistError on anything short of a
    list every candidate of which names itself and, where it states a
    pair, states both ends as fractions. No default path."""
    path = resolve_path(path)
    try:
        with open(path, "rb") as f:
            raw = tomli.load(f)
    except FileNotFoundError:
        raise WatchlistError(f"No watchlist file at {path}. There is no default watchlist.")
    except tomli.TOMLDecodeError as e:
        raise WatchlistError(f"{path} is not valid TOML: {e}")

    entries = raw.get("candidate")
    if not isinstance(entries, list) or not entries:
        raise WatchlistError(f"{path} has no [[candidate]] entries.")
    unexpected = sorted(set(raw) - {"candidate"})
    if unexpected:
        raise WatchlistError(f"{path} has top-level keys nothing reads: {unexpected}")

    candidates: Dict[str, Candidate] = {}
    tickers: Dict[str, str] = {}
    for n, entry in enumerate(entries, start=1):
        candidate = _parse_candidate(entry, n)
        if candidate.id in candidates:
            raise WatchlistError(f"Candidate {candidate.id} appears twice.")
        if candidate.ticker in tickers:
            raise WatchlistError(f"{candidate.ticker} is listed twice, on {tickers[candidate.ticker]} "
                                 f"and {candidate.id}; one company is one candidate.")
        candidates[candidate.id] = candidate
        tickers[candidate.ticker] = candidate.id
    return Watchlist(candidates=MappingProxyType(candidates), path=path)


def _parse_candidate(entry: Mapping[str, Any], n: int) -> Candidate:
    where = f"[[candidate]] #{n}"
    missing = [k for k in _HEADER
               if not isinstance(entry.get(k), str) or not entry[k].strip()]
    if missing:
        raise WatchlistError(f"{where} lacks {missing}; every candidate has an id, a ticker, "
                             "a name, a currency and a status.")
    cid = entry["id"]
    where = cid
    if not CANDIDATE_ID.match(cid):
        raise WatchlistError(f"{where}: id does not match W-<number>.")
    if entry["status"] not in STATUSES:
        raise WatchlistError(f"{where}: status {entry['status']!r} is not active or closed.")

    growth = None
    if "valuation" in entry:
        table = entry["valuation"]
        if not isinstance(table, Mapping):
            raise WatchlistError(f"{where}: valuation is not a table.")
        extra = sorted(set(table) - set(GROWTH))
        if extra:
            raise WatchlistError(f"{where}: valuation does not take {extra}; the range reads "
                                 f"{list(GROWTH)}.")
        stated = [k for k in GROWTH if k in table]
        if len(stated) != len(GROWTH):
            raise WatchlistError(f"{where}: valuation states {stated}; a growth pair is "
                                 "growth_low and growth_high, both or neither.")
        for key in GROWTH:
            if not _is_fraction(table[key]):
                raise WatchlistError(f"{where}: {key} = {table[key]!r} is not a fraction; "
                                     "12% is written 0.12.")
        growth = MappingProxyType({key: table[key] for key in GROWTH})

    return Candidate(id=cid, ticker=entry["ticker"], name=entry["name"],
                     currency=entry["currency"], status=entry["status"], growth=growth)


def growth_pair(watchlist: Watchlist, ticker: str) -> Dict[str, Dict[str, object]]:
    """The two growth assumptions for the candidate with `ticker`, each as
    its value and the entry's id as its source, the shape
    quant/valuation.valuation_range reads. A candidate that states none
    raises naming both ends: a range follows from stated assumptions and
    nothing is assumed for a candidate that states none."""
    candidate = watchlist.by_ticker(ticker)
    if candidate.growth is None:
        raise WatchlistError(f"{candidate.id} ({ticker}) states no growth_low and growth_high; "
                             "a candidate under a valuation condition states the growth I "
                             "assume for it, and until it does it has no range.")
    return {key: {"value": candidate.growth[key], "source": candidate.id} for key in GROWTH}
