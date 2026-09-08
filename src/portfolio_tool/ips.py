"""
The Investment Policy Statement, loaded from ips.toml.

Policy lives in config, not code: the numbers are typed once in ips.toml,
derived from docs/IPS.md, and cited from each clause's `text`. This module
only loads and validates. It computes nothing; the checker does that, over
the allocation block PortfolioAnalysisAgent publishes.

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
from typing import Any, Dict, Mapping, Optional

import tomli


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The committed policy, anchored to the repository like the database URL is:
# never the shell's current directory.
DEFAULT_IPS_PATH = os.path.join(_PROJECT_ROOT, "ips.toml")

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

_HEADER = ("id", "type", "text")
_LIMITS = ("min", "max")


class IPSError(Exception):
    """Raised when the policy file cannot be loaded as a valid policy."""


@dataclass(frozen=True)
class Clause:
    id: str
    type: str
    text: str
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


def load_ips(path: Optional[str] = None) -> IPS:
    """Load and validate ips.toml. Raises IPSError on anything short of a
    policy every clause of which the checker can either check or cite."""
    path = path or DEFAULT_IPS_PATH
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
    missing = [k for k in _HEADER if not isinstance(entry.get(k), str) or not entry[k].strip()]
    if missing:
        raise IPSError(f"{where} lacks {missing}; every clause has an id, a type and its text.")

    clause_id, clause_type, text = entry["id"], entry["type"], entry["text"].strip()
    where = clause_id
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

    return Clause(id=clause_id, type=clause_type, text=text, params=MappingProxyType(params))
