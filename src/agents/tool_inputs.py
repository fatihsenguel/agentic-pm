"""
The eleven tools' input models (KNOWN_GAPS, "The eleven tool contracts of
Order 5, on paper").

A tool validates what the model passes it, against the same vocabularies
extraction reads the message with, and raises on anything it would have to
repair: a ticker neither held nor on the watchlist, a span outside the
vocabulary, a weight outside (0, 1], an instrument type outside share and
fund, an input the tool does not take, an input it needs and was not given.
No model carries a default for anything the user must state
(docs/DIRECTION.md invariant 5). A raise ends the turn and the error is
shown unchanged, so a re-call with a guessed value cannot happen.

The model is not shown the vocabularies, and nothing here reads them: the
caller passes the held tickers, the period vocabulary and the watchlist's
tickers in a ToolContext, as extraction takes its vocabularies.

Each model is also the tool's JSON schema, strict: every property required,
none beyond them. `period` is required and may be null, which is the model
saying that the message named no span; the vocabulary's default then applies
in the data agent, as policy in config and not a repair here. Bounds the API
does not accept in a strict schema are left out of what it is sent and are
enforced here.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, ValidationError, ValidationInfo, field_validator

__all__ = ["TOOLS", "ToolContext", "ToolInputError", "tool_schema", "validate_inputs"]


class ToolInputError(Exception):
    """Raised when a tool is called with inputs it cannot answer on."""


@dataclass(frozen=True)
class ToolContext:
    held: Tuple[str, ...]
    periods: Tuple[str, ...]
    watchlist: Tuple[str, ...]


class _Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


def _context(info: ValidationInfo) -> ToolContext:
    return info.context["tool_context"]


class _NoInputs(_Inputs):
    pass


class Allocation(_NoInputs):
    """Every view of the allocation: by asset class, by sector, by position."""


class ComplianceCheck(_NoInputs):
    """The portfolio against every clause of the policy."""


class Rebalance(_NoInputs):
    """The drift against the target allocation."""


class Ledger(_NoInputs):
    """The prediction ledger as of today."""


class PositionPnl(_Inputs):
    tickers: List[str] = Field(description="Held tickers to show, or empty for every position.")

    @field_validator("tickers")
    @classmethod
    def _held(cls, tickers: List[str], info: ValidationInfo) -> List[str]:
        held = _context(info).held
        for i, ticker in enumerate(tickers):
            if ticker not in held:
                raise ValueError(f"{ticker!r} is not a ticker the portfolio holds; it holds "
                                 f"{', '.join(held)}.")
            if ticker in tickers[:i]:
                raise ValueError(f"{ticker!r} is named twice.")
        return tickers


class PortfolioVolatility(_Inputs):
    period: Optional[str] = Field(description="A span from the vocabulary, or null when the "
                                              "message names none.")

    @field_validator("period")
    @classmethod
    def _in_vocabulary(cls, period: Optional[str], info: ValidationInfo) -> Optional[str]:
        periods = _context(info).periods
        if period is not None and period not in periods:
            raise ValueError(f"{period!r} is not a span measured over; the spans are "
                             f"{', '.join(periods)}.")
        return period


class HypotheticalWeight(_Inputs):
    weight: float = Field(gt=0, le=1, description="The proposed share of the whole portfolio, "
                                                  "as a fraction.")
    instrument_type: Literal["share", "fund"] = Field(
        description="Whether the position would be a directly held share or a fund.")


class PolicyLookup(_Inputs):
    topic: str = Field(description="The words the question uses for what it asks the policy "
                                   "about.")

    @field_validator("topic")
    @classmethod
    def _words(cls, topic: str) -> str:
        if not topic.strip():
            raise ValueError("the topic is empty; a lookup needs the words the question used.")
        return topic


def _one_ticker(ticker: str) -> str:
    if not ticker or ticker != ticker.upper() or not ticker.replace(".", "").isalnum():
        raise ValueError(f"{ticker!r} is not one ticker as the exchange writes it.")
    return ticker


# A company the owner has written down: one held, which PHI-7.2 rechecks,
# or one on a watchlist entry. Any other is refused here, before the screen
# calls EDGAR (Part 18, R-2). A comment and not a docstring: a model's
# docstring enters its JSON schema, which the conversation model is shown.
class PhilosophyScreen(_Inputs):
    ticker: str = Field(description="The one company's ticker.")

    @field_validator("ticker")
    @classmethod
    def _written_down(cls, ticker: str, info: ValidationInfo) -> str:
        context = _context(info)
        if _one_ticker(ticker) not in context.held + context.watchlist:
            raise ValueError(f"{ticker} is neither held nor on a watchlist entry; the portfolio "
                             f"holds {', '.join(context.held)} and the watchlist lists "
                             f"{', '.join(context.watchlist)}. The philosophy is checked on a "
                             "company the owner has written down.")
        return ticker


class _Candidate(_Inputs):
    ticker: str = Field(description="The ticker of one company on the watchlist.")

    @field_validator("ticker")
    @classmethod
    def _listed(cls, ticker: str, info: ValidationInfo) -> str:
        watchlist = _context(info).watchlist
        if _one_ticker(ticker) not in watchlist:
            raise ValueError(f"{ticker} is on no watchlist entry; the watchlist holds "
                             f"{', '.join(watchlist)}. A candidate reaches the watchlist "
                             "because the owner puts it there.")
        return ticker


class Thesis(_Candidate):
    """What has to be true for the thesis on a watchlist company to be right."""


class Position(_Candidate):
    """Whether to take a position in a watchlist company, at the weight its
    entry states and never one passed here (decision 65)."""


TOOLS: Dict[str, type] = {
    "allocation": Allocation,
    "position_pnl": PositionPnl,
    "portfolio_volatility": PortfolioVolatility,
    "compliance_check": ComplianceCheck,
    "hypothetical_weight": HypotheticalWeight,
    "policy_lookup": PolicyLookup,
    "philosophy_screen": PhilosophyScreen,
    "thesis": Thesis,
    "position": Position,
    "rebalance": Rebalance,
    "ledger": Ledger,
}


def validate_inputs(tool: str, raw: Mapping[str, Any], context: ToolContext) -> Dict[str, Any]:
    """The inputs as the tool's model validates them, or ToolInputError
    naming each input refused and what was passed."""
    model = TOOLS.get(tool)
    if model is None:
        raise ToolInputError(f"There is no tool {tool!r}; the tools are {', '.join(TOOLS)}.")
    try:
        return model.model_validate(dict(raw), context={"tool_context": context}).model_dump()
    except ValidationError as error:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in e['loc']) or 'inputs'}: "
            f"{e['msg'].removeprefix('Value error, ')} (given {e.get('input')!r})"
            for e in error.errors())
        raise ToolInputError(f"{tool} cannot answer on these inputs: {problems}") from None


# Keywords a strict tool schema does not accept; the bound is enforced by the
# model above instead.
_UNSENT = {"title", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
           "multipleOf", "minLength", "maxLength", "default"}


def _strip(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _strip(v) for k, v in node.items() if k not in _UNSENT}
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def tool_schema(tool: str) -> Dict[str, Any]:
    """The tool's input schema as the API is sent it: every property
    required, no property beyond them."""
    schema = _strip(TOOLS[tool].model_json_schema())
    schema["additionalProperties"] = False
    schema["required"] = list(schema.get("properties", {}))
    schema.setdefault("properties", {})
    return schema
