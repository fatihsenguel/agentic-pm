"""
The watchlist as config: docs/WATCHLIST.md and watchlist.toml, the
candidates I want to own and, for each, the growth I assume for its
valuation range (Part 11 D38).

What this reads: each candidate's id, ticker, name, currency and status,
its valuation table, `growth_low` and `growth_high`, both or neither, and
its prediction rows (case 4.5, Part 14): id, made_on, due, kind and
statement; a figure prediction's metric, bound, value and period; and the
score I wrote, all four fields or none. What it leaves alone: the thesis,
the entry condition, added_on and the philosophy check, read by nothing.
The metric's vocabulary is the scorer's (D42): any name loads here and the
scorer stops on one it has no formula for.

Policy lives in config, not code. This module loads and validates; it
computes nothing and defaults nothing: a missing file is an error, a
candidate that states no pair has no range until it does, and a ticker
that is not on the list is not a candidate. The order of the two ends is
not checked here: quant/valuation.py raises on a reversed or equal pair,
so that rule lives in one place.
"""

import datetime as dt
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Tuple

import tomli

from portfolio_tool.clauses import resolve_path

__all__ = ["Candidate", "Prediction", "Score", "Watchlist", "WatchlistError",
           "load_watchlist", "growth_pair", "predictions",
           "CANDIDATE_ID", "PREDICTION_ID", "STATUSES", "KINDS", "BOUNDS", "RESULTS"]

CANDIDATE_ID = re.compile(r"^W-\d+$")
PREDICTION_ID = re.compile(r"^(W-\d+)\.\d+$")
STATUSES = ("active", "closed")
_HEADER = ("id", "ticker", "name", "currency", "status")
# A prediction row (docs/WATCHLIST.md; Part 14 D45): the five every row
# carries, the four a figure carries, the four a written score carries.
_PREDICTION = ("id", "made_on", "due", "kind", "statement")
FIGURE = ("metric", "bound", "value", "period")
SCORE = ("outcome", "source", "scored_on", "result")
KINDS = ("figure", "event")
BOUNDS = ("min", "max")
RESULTS = ("right", "wrong")
_PERIOD = re.compile(r"^FY\d{4}$")
# The two ends the range reads from the entry (Part 11 D38); a table
# stating anything else is stating something the range does not read.
GROWTH = ("growth_low", "growth_high")


class WatchlistError(Exception):
    """Raised when the watchlist cannot be loaded as a valid one, or when a
    candidate asked for is not on it or states no growth pair."""


@dataclass(frozen=True)
class Score:
    """The score I wrote next to a prediction: the outcome, its source,
    the date and right or wrong. Never computed here or anywhere."""
    outcome: str
    source: str
    scored_on: dt.date
    result: str


@dataclass(frozen=True)
class Prediction:
    id: str
    candidate: str
    made_on: dt.date
    due: dt.date
    kind: str
    statement: str
    metric: Optional[str] = None
    bound: Optional[str] = None
    value: Optional[float] = None
    period: Optional[str] = None
    score: Optional[Score] = None


@dataclass(frozen=True)
class Candidate:
    id: str
    ticker: str
    name: str
    currency: str
    status: str
    growth: Optional[Mapping[str, float]] = None
    predictions: Tuple[Prediction, ...] = ()


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
    seen: Dict[str, str] = {}
    for n, entry in enumerate(entries, start=1):
        candidate = _parse_candidate(entry, n)
        if candidate.id in candidates:
            raise WatchlistError(f"Candidate {candidate.id} appears twice.")
        if candidate.ticker in tickers:
            raise WatchlistError(f"{candidate.ticker} is listed twice, on {tickers[candidate.ticker]} "
                                 f"and {candidate.id}; one company is one candidate.")
        for p in candidate.predictions:
            if p.id in seen:
                raise WatchlistError(f"Prediction {p.id} appears twice; a prediction is "
                                     "never edited, and a changed view is a new one.")
            seen[p.id] = candidate.id
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

    rows = entry.get("prediction", [])
    if not isinstance(rows, list):
        raise WatchlistError(f"{where}: prediction is not a list of [[candidate.prediction]] rows.")
    predictions = tuple(_parse_prediction(row, cid, n) for n, row in enumerate(rows, start=1))

    return Candidate(id=cid, ticker=entry["ticker"], name=entry["name"],
                     currency=entry["currency"], status=entry["status"], growth=growth,
                     predictions=predictions)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _date(where: str, row: Mapping[str, Any], key: str) -> dt.date:
    value = row.get(key)
    if not isinstance(value, dt.date) or isinstance(value, dt.datetime):
        raise WatchlistError(f"{where}: {key} = {value!r} is not a date; written 2027-03-01.")
    return value


def _text(where: str, row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise WatchlistError(f"{where}: {key} is missing or empty.")
    return value


def _parse_prediction(row: Mapping[str, Any], cid: str, n: int) -> Prediction:
    where = f"{cid} prediction #{n}"
    if not isinstance(row, Mapping):
        raise WatchlistError(f"{where} is not a table.")
    missing = [k for k in _PREDICTION if k not in row]
    if missing:
        pid = row.get("id") if isinstance(row.get("id"), str) else where
        raise WatchlistError(f"{pid} lacks {missing}; every prediction has an id, made_on, "
                             "due, kind and statement.")
    pid = _text(where, row, "id")
    where = pid
    match = PREDICTION_ID.match(pid)
    if not match:
        raise WatchlistError(f"{where}: id does not match W-<n>.<m>.")
    if match.group(1) != cid:
        raise WatchlistError(f"{where} is written under {cid}; a prediction's id names the "
                             "candidate it belongs to.")
    made_on, due = _date(where, row, "made_on"), _date(where, row, "due")
    if not due > made_on:
        raise WatchlistError(f"{where}: due {due} is not after made_on {made_on}.")
    kind = row["kind"]
    if kind not in KINDS:
        raise WatchlistError(f"{where}: kind {kind!r} is not figure or event.")
    statement = _text(where, row, "statement")

    keys = set(row) - set(_PREDICTION)
    figure = {k: row[k] for k in FIGURE if k in row}
    if kind == "figure":
        lacking = [k for k in FIGURE if k not in figure]
        if lacking:
            raise WatchlistError(f"{where}: a figure prediction lacks {lacking}; it states "
                                 f"{list(FIGURE)}.")
        if figure["bound"] not in BOUNDS:
            raise WatchlistError(f"{where}: bound {figure['bound']!r} is not min or max.")
        if not _is_number(figure["value"]):
            raise WatchlistError(f"{where}: value = {figure['value']!r} is not a number.")
        if not isinstance(figure["period"], str) or not _PERIOD.match(figure["period"]):
            raise WatchlistError(f"{where}: period {figure['period']!r} is not of the form "
                                 "FY<year>.")
        _text(where, row, "metric")
    elif figure:
        raise WatchlistError(f"{where}: an event prediction carries {sorted(figure)}; a "
                             "figure's fields are a figure prediction's.")
    keys -= set(FIGURE)

    score = None
    stated = [k for k in SCORE if k in row]
    if stated:
        if len(stated) != len(SCORE):
            raise WatchlistError(f"{where}: a score states {stated}; a score carries all four "
                                 f"of {list(SCORE)} or none.")
        scored_on = _date(where, row, "scored_on")
        if scored_on < due:
            raise WatchlistError(f"{where}: scored_on {scored_on} is before due {due}; a "
                                 "prediction is scored when its date comes.")
        if row["result"] not in RESULTS:
            raise WatchlistError(f"{where}: result {row['result']!r} is not right or wrong.")
        score = Score(outcome=_text(where, row, "outcome"), source=_text(where, row, "source"),
                      scored_on=scored_on, result=row["result"])
    keys -= set(SCORE)
    if keys:
        raise WatchlistError(f"{where} has keys nothing reads: {sorted(keys)}.")

    return Prediction(id=pid, candidate=cid, made_on=made_on, due=due, kind=kind,
                      statement=statement, metric=figure.get("metric"), bound=figure.get("bound"),
                      value=figure.get("value"), period=figure.get("period"), score=score)


def predictions(watchlist: Watchlist) -> List[Prediction]:
    """The ledger: every candidate's predictions in document order."""
    return [p for c in watchlist.candidates.values() for p in c.predictions]


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
