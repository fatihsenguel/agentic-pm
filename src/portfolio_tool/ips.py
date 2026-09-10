"""
The Investment Policy Statement, loaded from the ips.toml a portfolio names.

Policy lives in config, not code: the numbers are typed once in an
ips.toml derived from a prose document with numbered clauses (docs/IPS.md
for the committed, synthetic one), and cited from each clause's `text`.
Which file is the portfolio's to say (`portfolios.ips_path`, DIRECTION.md
Order 2, item 4): the benchmark portfolio names the committed file, a
personal portfolio names one outside the repository, and this module takes
the path it is given and has no default. It only loads and validates. It
computes nothing; the checker does that, over the allocation block
PortfolioAnalysisAgent publishes.

The type vocabulary is closed. A clause with a type the checker cannot check
fails to load, as does a checkable clause missing its parameters and a
statement carrying any. A policy that loads is therefore a policy every
clause of which is either computed or visibly not computed - which is what
lets "the policy contains nothing on this" be an honest answer.

No defaults. A missing file is an error, not an empty policy; a compliance
verdict against a policy nobody wrote is the shape wip/phase7-snapshot was
rejected for (tests/golden/KNOWN_GAPS.md).
"""

import os
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Mapping

import tomli


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resolve_ips_path(path: str) -> str:
    """Anchor a relative policy path to the project root; pass an absolute
    one through. A portfolio row names the committed policy as `ips.toml`
    and a personal one by an absolute path outside the repository; neither
    is ever read relative to the shell's current directory, the way
    config.resolve_database_url treats the database."""
    if os.path.isabs(path):
        return path
    return os.path.join(_PROJECT_ROOT, os.path.normpath(path))

CLAUSE_ID = re.compile(r"^IPS-\d+\.\d+$")

STATEMENT = "statement"

# type -> (required parameters, optional parameters). A statement takes none.
# `asset_class_band` needs at least one bound, checked below, because the
# document writes cash as a floor with no ceiling.
CLAUSE_TYPES: Mapping[str, tuple] = MappingProxyType({
    STATEMENT: ((), ()),
    "asset_class_band": (("asset_class",), ("min", "max")),
    "max_instrument_weight": (("max",), ()),
    "max_issuer_weight": (("max",), ()),
    "max_sector_weight": (("max",), ()),
})

_HEADER = ("id", "type", "text", "topics")
_LIMITS = ("min", "max")


class IPSError(Exception):
    """Raised when the policy file cannot be loaded as a valid policy."""


@dataclass(frozen=True)
class Clause:
    id: str
    type: str
    text: str
    topics: tuple = ()
    params: Mapping[str, Any] = field(default_factory=dict)

    @property
    def is_statement(self) -> bool:
        return self.type == STATEMENT


@dataclass(frozen=True)
class IPS:
    """Clauses keyed by id, in document order."""

    clauses: Mapping[str, Clause]
    path: str

    def __getitem__(self, clause_id: str) -> Clause:
        return self.clauses[clause_id]

    def __iter__(self):
        return iter(self.clauses.values())

    def __len__(self) -> int:
        return len(self.clauses)

    @property
    def statements(self):
        return [c for c in self if c.is_statement]

    @property
    def checkable(self):
        return [c for c in self if not c.is_statement]

    @property
    def topics(self):
        """The closed topic vocabulary: every topic any clause carries."""
        return sorted({t for c in self for t in c.topics})

    def clauses_on(self, asked: str):
        """Clauses whose topics occur, as whole words or phrases, inside the
        user's own words for what they asked about. Containment of the
        owner's vocabulary in the question, never the reverse and never
        similarity: "concentration risk" carries "concentration", "currency
        risk" carries nothing, and the answer to the second is that the
        policy contains nothing on it. The error this can make is a miss
        ("too concentrated" does not carry "concentration") - a config gap
        closed by adding the word to the clause in ips.toml, never a clause
        cited for a topic it is not about."""
        words = normalise_topic(asked)
        return [c for c in self if any(_contains_phrase(words, t) for t in c.topics)]


def _contains_phrase(text: str, phrase: str) -> bool:
    """Whole-word containment of a normalised phrase in a normalised text."""
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


def normalise_topic(topic: str) -> str:
    """One normalisation for topics wherever they are compared: the file is
    held to this form by the loader, the router's word is brought to it."""
    return " ".join(str(topic).lower().split())


def load_ips(path: str) -> IPS:
    """Load and validate the ips.toml at `path`, relative to the project root
    or absolute. Raises IPSError on anything short of a policy every clause
    of which the checker can either check or cite. No default path: the
    policy is the portfolio's, and a caller that names none has forgotten
    which portfolio it is about."""
    path = resolve_ips_path(path)
    try:
        with open(path, "rb") as f:
            raw = tomli.load(f)
    except FileNotFoundError:
        raise IPSError(f"No policy file at {path}. There is no default policy.")
    except tomli.TOMLDecodeError as e:
        raise IPSError(f"{path} is not valid TOML: {e}")

    entries = raw.get("clause")
    if not isinstance(entries, list) or not entries:
        raise IPSError(f"{path} has no [[clause]] entries.")
    unexpected = sorted(set(raw) - {"clause"})
    if unexpected:
        raise IPSError(f"{path} has top-level keys nothing reads: {unexpected}")

    clauses: Dict[str, Clause] = {}
    for n, entry in enumerate(entries, start=1):
        clause = _parse_clause(entry, n)
        if clause.id in clauses:
            raise IPSError(f"Clause {clause.id} appears twice.")
        clauses[clause.id] = clause

    return IPS(clauses=MappingProxyType(clauses), path=path)


def _parse_clause(entry: Dict[str, Any], n: int) -> Clause:
    where = f"[[clause]] #{n}"
    missing = [k for k in ("id", "type", "text")
               if not isinstance(entry.get(k), str) or not entry[k].strip()]
    if "topics" not in entry:
        missing.append("topics")
    if missing:
        raise IPSError(f"{where} lacks {missing}; every clause has an id, a type, its "
                       "text and its topics.")

    clause_id, clause_type, text = entry["id"], entry["type"], entry["text"].strip()
    where = clause_id
    topics = entry["topics"]
    if (not isinstance(topics, list) or not topics
            or any(not isinstance(t, str) or not t.strip() for t in topics)):
        raise IPSError(f"{where}: topics must be a non-empty list of words; a clause "
                       "nobody can ask about is not citable.")
    off_form = [t for t in topics if t != normalise_topic(t)]
    if off_form:
        raise IPSError(f"{where}: topics are lowercase, single-spaced, stripped: {off_form}")
    if len(set(topics)) != len(topics):
        raise IPSError(f"{where}: duplicate topics {topics}")
    if not CLAUSE_ID.match(clause_id):
        raise IPSError(f"{where}: id does not match IPS-<section>.<number>.")
    if clause_type not in CLAUSE_TYPES:
        raise IPSError(
            f"{where}: type {clause_type!r} is not one the checker knows "
            f"({', '.join(CLAUSE_TYPES)}). A clause with no type is not a clause; "
            "a topic with no clause is one the policy contains nothing on."
        )

    required, optional = CLAUSE_TYPES[clause_type]
    params = {k: v for k, v in entry.items() if k not in _HEADER}
    allowed = set(required) | set(optional)

    absent = [k for k in required if k not in params]
    if absent:
        raise IPSError(f"{where}: {clause_type} needs {absent}.")
    extra = sorted(set(params) - allowed)
    if extra:
        if clause_type == STATEMENT:
            raise IPSError(f"{where}: a statement carries {extra}; a number on a "
                           "statement is a limit nobody checks.")
        raise IPSError(f"{where}: {clause_type} does not take {extra}.")
    if clause_type == "asset_class_band" and not any(k in params for k in _LIMITS):
        raise IPSError(f"{where}: an asset_class_band needs min, max or both.")

    for k in _LIMITS:
        if k in params:
            v = params[k]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 < v <= 1:
                raise IPSError(f"{where}: {k} = {v!r} is not a fraction in (0, 1]; "
                               "limits are shares of total value, 65% is 0.65.")
    if "min" in params and "max" in params and params["min"] >= params["max"]:
        raise IPSError(f"{where}: min {params['min']} is not below max {params['max']}.")
    if "asset_class" in params and (
        not isinstance(params["asset_class"], str) or not params["asset_class"].strip()
    ):
        raise IPSError(f"{where}: asset_class must name an allocation label.")

    return Clause(id=clause_id, type=clause_type, text=text, topics=tuple(topics),
                  params=MappingProxyType(params))
