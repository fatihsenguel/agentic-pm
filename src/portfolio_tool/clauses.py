"""
A clause document: a prose document with numbered clauses and a TOML derived
from it, loaded and validated once for every policy of that shape.

The IPS (docs/IPS.md, ips.toml) and the philosophy (docs/PHILOSOPHY.md,
philosophy.toml) are the same pattern: every clause has an id, a type, its
text verbatim and its topics; a clause with a number is checked by a checker
that knows its type, a clause without one is a statement, citable and never
computed. What differs between the two documents is the id prefix, the type
vocabulary and the checks on each type's parameters, and that is all a
DocumentSpec states. Everything else - the header, the refusal of an unknown
type with the growth rule, required and optional parameters, a statement
carrying nothing, duplicate ids, stray top-level keys, path anchoring, the
topic rules - is here, once.

Policy lives in config, not code. This module loads and validates; it
computes nothing. No defaults: a missing file is an error, not an empty
document, and a call that names no path has forgotten which portfolio it is
about.
"""

import os
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Dict, Mapping, Optional, Type

import tomli


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STATEMENT = "statement"
_HEADER = ("id", "type", "text", "topics")


def resolve_path(path: str) -> str:
    """Anchor a relative document path to the project root; pass an absolute
    one through. A portfolio row names the committed policy as `ips.toml`
    and a personal one by an absolute path outside the repository; neither
    is ever read relative to the shell's current directory, the way
    config.resolve_database_url treats the database."""
    if os.path.isabs(path):
        return path
    return os.path.join(_PROJECT_ROOT, os.path.normpath(path))


class ClauseError(Exception):
    """Raised when a clause document cannot be loaded as a valid one. Each
    document's spec names its own subclass, so a caller catches the error
    of the document it asked for."""


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
class ClauseDocument:
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
        closed by adding the word to the clause in the TOML, never a clause
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


@dataclass(frozen=True)
class DocumentSpec:
    """What one kind of clause document is.

    noun: what to call it in messages ("policy", "philosophy").
    id_pattern: the id regex; id_form: how to describe it in a message.
    types: type -> (required parameters, optional parameters). The
        statement type takes none and is added here if the spec omits it.
    validate_params: the checks on one clause's parameters that depend on
        the type vocabulary - a limit being a fraction, a band having a
        bound - called with (clause_id, clause_type, params) and raising
        the spec's error on a failure.
    error: the exception class to raise, a subclass of ClauseError.
    """

    noun: str
    id_pattern: "re.Pattern"
    id_form: str
    types: Mapping[str, tuple]
    validate_params: Callable[[str, str, Mapping[str, Any]], None]
    error: Type[ClauseError] = ClauseError

    def __post_init__(self):
        if STATEMENT not in self.types:
            object.__setattr__(self, "types",
                               MappingProxyType({STATEMENT: ((), ()), **dict(self.types)}))


def load_clauses(path: str, spec: DocumentSpec) -> ClauseDocument:
    """Load and validate the TOML at `path`, relative to the project root or
    absolute, as a document of the kind `spec` describes. Raises the spec's
    error on anything short of a document every clause of which the
    checker can either check or cite."""
    err = spec.error
    path = resolve_path(path)
    try:
        with open(path, "rb") as f:
            raw = tomli.load(f)
    except FileNotFoundError:
        raise err(f"No {spec.noun} file at {path}. There is no default {spec.noun}.")
    except tomli.TOMLDecodeError as e:
        raise err(f"{path} is not valid TOML: {e}")

    entries = raw.get("clause")
    if not isinstance(entries, list) or not entries:
        raise err(f"{path} has no [[clause]] entries.")
    unexpected = sorted(set(raw) - {"clause"})
    if unexpected:
        raise err(f"{path} has top-level keys nothing reads: {unexpected}")

    clauses: Dict[str, Clause] = {}
    for n, entry in enumerate(entries, start=1):
        clause = _parse_clause(entry, n, spec)
        if clause.id in clauses:
            raise err(f"Clause {clause.id} appears twice.")
        clauses[clause.id] = clause

    return ClauseDocument(clauses=MappingProxyType(clauses), path=path)


def _parse_clause(entry: Dict[str, Any], n: int, spec: DocumentSpec) -> Clause:
    err = spec.error
    where = f"[[clause]] #{n}"
    missing = [k for k in ("id", "type", "text")
               if not isinstance(entry.get(k), str) or not entry[k].strip()]
    if "topics" not in entry:
        missing.append("topics")
    if missing:
        raise err(f"{where} lacks {missing}; every clause has an id, a type, its "
                  "text and its topics.")

    clause_id, clause_type, text = entry["id"], entry["type"], entry["text"].strip()
    where = clause_id
    topics = entry["topics"]
    if (not isinstance(topics, list) or not topics
            or any(not isinstance(t, str) or not t.strip() for t in topics)):
        raise err(f"{where}: topics must be a non-empty list of words; a clause "
                  "nobody can ask about is not citable.")
    off_form = [t for t in topics if t != normalise_topic(t)]
    if off_form:
        raise err(f"{where}: topics are lowercase, single-spaced, stripped: {off_form}")
    if len(set(topics)) != len(topics):
        raise err(f"{where}: duplicate topics {topics}")
    if not spec.id_pattern.match(clause_id):
        raise err(f"{where}: id does not match {spec.id_form}.")
    if clause_type not in spec.types:
        raise err(
            f"{where}: type {clause_type!r} is not one the checker knows "
            f"({', '.join(spec.types)}). A clause with no type is not a clause; "
            f"a topic with no clause is one the {spec.noun} contains nothing on. A rule "
            "the checker cannot check yet is written as a statement until its "
            "checker and its reference exist: cited, and visibly not computed."
        )

    required, optional = spec.types[clause_type]
    params = {k: v for k, v in entry.items() if k not in _HEADER}
    allowed = set(required) | set(optional)

    absent = [k for k in required if k not in params]
    if absent:
        raise err(f"{where}: {clause_type} needs {absent}.")
    extra = sorted(set(params) - allowed)
    if extra:
        if clause_type == STATEMENT:
            raise err(f"{where}: a statement carries {extra}; a number on a "
                      "statement is a limit nobody checks.")
        raise err(f"{where}: {clause_type} does not take {extra}.")

    spec.validate_params(clause_id, clause_type, params)

    return Clause(id=clause_id, type=clause_type, text=text, topics=tuple(topics),
                  params=MappingProxyType(params))
