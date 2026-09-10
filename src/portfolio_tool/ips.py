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

The vocabulary grows one clause at a time. A rule a personal policy states
and this checker cannot check yet is written as a statement: cited by id,
listed by every full check as a statement outside the check, carrying no
number here. When it is to be checked, in this order: a hand-computed
reference for that clause on the portfolio first, then its type here with
its parameters, then the checker's arm with the test over that reference,
then the entry's type in the file flips from statement to the new type.

The loading itself - the header, the unknown-type refusal, parameters,
duplicates, path anchoring, topics - is clauses.py, shared with the
philosophy. This module states what an IPS is: the id prefix, the type
table, and the checks on limits and bands.
"""

import re
from types import MappingProxyType
from typing import Any, Mapping

from portfolio_tool.clauses import (
    STATEMENT, Clause, ClauseDocument, ClauseError, DocumentSpec, load_clauses,
    normalise_topic, resolve_path,
)

__all__ = ["IPS", "IPSError", "Clause", "CLAUSE_TYPES", "STATEMENT", "CLAUSE_ID",
           "load_ips", "normalise_topic", "resolve_ips_path"]

IPS = ClauseDocument
resolve_ips_path = resolve_path

CLAUSE_ID = re.compile(r"^IPS-\d+\.\d+$")

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

_LIMITS = ("min", "max")


class IPSError(ClauseError):
    """Raised when the policy file cannot be loaded as a valid policy."""


def _validate_params(where: str, clause_type: str, params: Mapping[str, Any]) -> None:
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


SPEC = DocumentSpec(
    noun="policy",
    id_pattern=CLAUSE_ID,
    id_form="IPS-<section>.<number>",
    types=CLAUSE_TYPES,
    validate_params=_validate_params,
    error=IPSError,
)


def load_ips(path: str) -> IPS:
    """Load and validate the ips.toml at `path`, relative to the project root
    or absolute. Raises IPSError on anything short of a policy every clause
    of which the checker can either check or cite. No default path: the
    policy is the portfolio's, and a caller that names none has forgotten
    which portfolio it is about."""
    return load_clauses(path, SPEC)
