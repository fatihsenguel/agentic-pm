"""
Deterministic extraction from the user's message, before any model sees it.

docs/DIRECTION.md: extraction of tickers, weights, periods and topics before
the LLM is the router work that moves toward the tool boundary - it becomes
the tools' input validation. Every rule here is a closed vocabulary or a
fixed pattern, so the same message always extracts the same way and a test
can pin it. Where the message asks for something the vocabulary lacks, the
result is a clarification naming what the vocabulary has, never the nearest
value (KNOWN_GAPS: "last week becomes 1Y").

Pure: no LLM, no database, no config import. The caller passes the held
tickers and the period vocabulary in.

Tickers. An all-caps token that is a held ticker, or a known ETF or stock of
at least two letters from validators.py. The macro index set is left out.
Names are not mapped to symbols. An all-caps token of two to five letters
that is neither held nor known, and sits within one edit of a held ticker,
is a typo of a holding and is asked about, naming the holding: no stoplist
is needed, because ETF, IPS and VIX are not one edit from anything held.

Periods. The caller's vocabulary is year-multiples ("1Y", "2Y", ...). A span
in years that the vocabulary has is that value; twelve months is a year; any
other span - months, weeks, days, a year the vocabulary lacks, an absolute
year - is a clarification naming the spans it has. No span is None.

Percentages. A figure with a percent sign next to "vol" or "volatility" is
the volatility cap; any other single percentage is the hypothetical weight
in one position. Two of a kind, or a figure outside (0, 100], clarify.

Topics are not extracted here: the policy is matched on the user's own
words, and the router passes the message itself.
"""

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from .validators import KNOWN_ETFS, KNOWN_STOCKS


@dataclass(frozen=True)
class Extraction:
    tickers: List[str]
    period: Optional[str]
    max_volatility: Optional[float]
    hypothetical_weight: Optional[float]
    # When set, the message asked for something outside the vocabularies and
    # this is the question to ask back. The other fields carry what was
    # extracted before the question arose.
    clarification: Optional[str]


_KNOWN = {t for t in KNOWN_ETFS | KNOWN_STOCKS if len(t) >= 2}

# A whole all-caps token: letters, digits and dots, not glued to other
# alphanumerics, so "P&L" yields P and L (single letters, never tickers) and
# "ZZZZFAKE" yields nothing (no split can end at a boundary).
_TOKEN = re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9.]{0,5})(?![A-Za-z0-9])")

_NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12,
}
# A counted span: "1 year", "3y", "twelve months", "the last 6 months". The
# bare unit letter "y" is allowed only after a digit, so "any" is not "an y".
_SPAN = re.compile(
    r"\b(?:(?:the\s+)?(?:past|last|previous|next)\s+)?"
    r"(?:(\d+)\s*(y|yrs?|years?|mos?|months?|wks?|weeks?|days?)"
    r"|(a|an|one|two|three|four|five|six|seven|eight|nine|ten|twelve)"
    r"[\s-]+(years?|months?|weeks?|days?))\b",
    re.IGNORECASE,
)
# An uncounted span: "the past year" is one year; "last month", "this week"
# are spans the vocabulary lacks.
_BARE_SPAN = re.compile(
    r"\b(?:the\s+)?(past|last|previous|this)\s+(year|quarter|month|week|day)\b",
    re.IGNORECASE,
)
_SINCE_YEAR = re.compile(r"\bsince\s+(19|20)\d{2}\b", re.IGNORECASE)
_YTD = re.compile(r"\b(year\s+to\s+date|ytd)\b", re.IGNORECASE)

_PERCENT = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:%|percent\b)", re.IGNORECASE)
_VOL_WINDOW = 25  # characters either side of a percentage in which "vol" makes it a cap


def extract(message: str, held_tickers: Sequence[str], periods: Iterable[str]) -> Extraction:
    """Extract what the message states, or the question to ask back.

    Args:
        message: the user's words, unmodified
        held_tickers: the active portfolio's tickers, or empty
        periods: the period vocabulary, config.data.period_days' keys

    Returns:
        Extraction. `clarification` is set when a ticker, a span or a
        percentage is outside what the vocabularies can express; the
        first such finding wins, in that order.
    """
    held = [t.upper() for t in held_tickers]
    vocabulary = list(periods)

    tickers, ticker_question = _tickers(message, held)
    period, period_question = _period(message, vocabulary)
    max_vol, weight, percent_question = _percentages(message)

    clarification = ticker_question or period_question or percent_question
    return Extraction(
        tickers=tickers,
        period=period,
        max_volatility=max_vol,
        hypothetical_weight=weight,
        clarification=clarification,
    )


# --- tickers -----------------------------------------------------------------

def _tickers(message: str, held: List[str]):
    found: List[str] = []
    for token in _TOKEN.findall(message):
        if token in held or token in _KNOWN:
            if token not in found:
                found.append(token)
            continue
        if 2 <= len(token) <= 5 and token.isalpha():
            near = [h for h in held if _within_one_edit(token, h)]
            if near:
                return found, (
                    f"{token} is not a ticker I know. Did you mean {near[0]}, "
                    f"which you hold? Your portfolio holds {', '.join(held)}."
                )
    return found, None


def _within_one_edit(a: str, b: str) -> bool:
    """Optimal string alignment distance of at most one: a substitution, an
    insertion, a deletion, or a transposition of two adjacent letters."""
    if a == b:
        return False
    if len(a) == len(b):
        diffs = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if len(diffs) == 1:
            return True
        return (len(diffs) == 2 and diffs[1] == diffs[0] + 1
                and a[diffs[0]] == b[diffs[1]] and a[diffs[1]] == b[diffs[0]])
    if abs(len(a) - len(b)) == 1:
        longer, shorter = (a, b) if len(a) > len(b) else (b, a)
        return any(longer[:i] + longer[i + 1:] == shorter for i in range(len(longer)))
    return False


# --- periods -----------------------------------------------------------------

def _period(message: str, vocabulary: List[str]):
    years_in_vocabulary = {}
    for key in vocabulary:
        m = re.fullmatch(r"(\d+)Y", key)
        if m:
            years_in_vocabulary[int(m.group(1))] = key
    spans = ", ".join(vocabulary)

    def unsupported(phrase: str) -> str:
        return (f"I can measure over {spans}, not over '{phrase}'. "
                f"Which of those do you mean?")

    found = []  # (phrase, key or None)
    for m in _SPAN.finditer(message):
        phrase = m.group(0).strip()
        if m.group(1) is not None:
            count, unit = int(m.group(1)), m.group(2).lower()
        else:
            count, unit = _NUMBER_WORDS[m.group(3).lower()], m.group(4).lower()
        years = None
        if unit.startswith("y"):
            years = count
        elif unit.startswith("mo") and count == 12:
            years = 1
        key = years_in_vocabulary.get(years) if years is not None else None
        found.append((phrase, key))
    for m in _BARE_SPAN.finditer(message):
        qualifier, unit = m.group(1).lower(), m.group(2).lower()
        key = years_in_vocabulary.get(1) if (unit == "year" and qualifier != "this") else None
        found.append((m.group(0).strip(), key))
    for pattern in (_SINCE_YEAR, _YTD):
        for m in pattern.finditer(message):
            found.append((m.group(0).strip(), None))

    if not found:
        return None, None
    for phrase, key in found:
        if key is None:
            return None, unsupported(phrase)
    keys = {key for _, key in found}
    if len(keys) > 1:
        phrases = " and ".join(f"'{p}'" for p, _ in found)
        return None, (f"The message names two spans, {phrases}. Which one do you mean? "
                      f"I can measure over {spans}.")
    return keys.pop(), None


# --- percentages -------------------------------------------------------------

def _percentages(message: str):
    caps, weights = [], []
    for m in _PERCENT.finditer(message):
        value = float(m.group(1).replace(",", "."))
        printed = m.group(0).strip()
        if not 0 < value <= 100:
            return None, None, (f"'{printed}' is not a share of a portfolio. "
                                "A share is between 0 and 100 percent.")
        window = message[max(0, m.start() - _VOL_WINDOW): m.end() + _VOL_WINDOW].lower()
        (caps if "vol" in window else weights).append((printed, value / 100))

    def one(kind, items, what):
        if len(items) > 1:
            names = " and ".join(p for p, _ in items)
            return None, f"The message names {names}. Which {what} do you mean?"
        return (items[0][1] if items else None), None

    cap, q1 = one("cap", caps, "volatility cap")
    weight, q2 = one("weight", weights, "weight")
    return cap, weight, (q1 or q2)
