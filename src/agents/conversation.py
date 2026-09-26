"""
The conversation layer's client (decision 45): one turn of the tool loop.

The model is shown the conversation's own messages, the system prompt and
the eleven tools, and chooses which to call; it never sees a plan and never
names an agent. A call's inputs are validated by the tool's input model
(agents/tool_inputs.py) and the tool is run with its plan set
(agents/tool_runner.py); the model is shown the tool's rendered text, the
figures it may quote. A raise from either ends the turn: the error is the
answer, shown unchanged, and the model is not asked again, so a re-call with
a guessed value cannot happen.

What the model narrates is held to DIRECTION.md invariant 1 before it is
shown: every number token of the answer is a token of a tool's text from
this turn, of the question, or of what the conversation's earlier turns
printed or were asked, which the caller passes as `earlier` (decision 77:
a figure that passed an earlier turn's check may be quoted in a
follow-up). An answer that carries any other is refused with the figures
named; nothing is redacted.

`usage` is recorded for every call, the four token counts the API returns,
so that what a turn costs is a measurement (decision 45). No price is
computed here.

`conversation_model()` is the function the layer asks for the model, so a
test stands one in, as `reading_model()` is for a reading. The model is the
one `ANTHROPIC_SONNET` names; it refuses a temperature, and none is sent.
The system prompt and the tool definitions are the request's fixed prefix,
cached from the second call.
"""

import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

import anthropic

from agents.config import ANTHROPIC_SONNET

from .tool_inputs import TOOLS, ToolContext, ToolInputError, tool_schema, validate_inputs
from .tool_runner import ToolRunError, run_tool

__all__ = ["ConversationError", "ConversationModel", "MAX_MODEL_CALLS", "SYSTEM_PROMPT",
           "answer", "conversation_model", "tool_definitions"]

MAX_TOKENS = 16_000

# Every call is paid for; a turn that has called the model this many times
# without finishing is stopped rather than left to run. The longest turn the
# corpus asks for calls two tools.
MAX_MODEL_CALLS = 6


class ConversationError(Exception):
    """Raised when a turn ends without an answer that may be shown. Carries
    the usage of the calls made before it, which were paid for."""

    def __init__(self, message: str, model_calls: Sequence[Dict[str, Any]] = ()):
        super().__init__(message)
        self.model_calls = list(model_calls)


SYSTEM_PROMPT = (
    "You answer questions about one investment portfolio and the companies on its owner's "
    "watchlist, using only the tools provided. Every figure you state is copied from a tool's "
    "output in this turn exactly as printed: no rounding, no arithmetic, no figure of your own. "
    "Call a tool with only what the message states; never supply an input the message leaves "
    "out. If no tool answers what was asked, say so. The policy makes no forecast of a price, a "
    "return or the market's regime, assesses no tax, places or sizes no order, gives no opinion "
    "on whether something is a good investment, and says neither what to buy with no company "
    "named nor whether to sell or hold what is owned: for such a question, call policy_lookup "
    "with the words naming what was asked, and answer by citing the clause it returns and "
    "naming what is refused, with no figure. Whether to buy one named company is answered only "
    "through the position tool. Add no recommendation, price view or judgement of your own "
    "beside any tool's output. You may select from a tool's output what the question asks "
    "for; cite clause ids exactly as printed. Write every figure with the digits, separators "
    "and decimal point exactly as the tool printed it, whatever language you answer in."
)

TOOL_DESCRIPTIONS: Dict[str, str] = {
    "allocation": (
        "The portfolio's allocation as it stands: each holding's value and share of the total "
        "by asset class, by sector and by position, with cash, as of the last stored close."),
    "position_pnl": (
        "Profit and loss of held positions since purchase: quantity, average price, cost basis, "
        "last price, market value, and the gain in money and in percent, as of the last stored "
        "close. Pass the held tickers the question names, or an empty list for every position."),
    "portfolio_volatility": (
        "The portfolio's annualised volatility from its current weights and the covariance of "
        "its holdings over a span of whole years. Pass the span the question names, written as "
        "a number of years followed by Y, or null when it names none."),
    "compliance_check": (
        "The whole portfolio checked against every numbered clause of the investment policy: "
        "each finding with its clause id, the observed figure, the limit and the distance to "
        "it, as of the last stored close."),
    "hypothetical_weight": (
        "A proposed weight in one new, unnamed position checked against the policy's "
        "concentration limits, with no portfolio figure. Pass the weight as a fraction of the "
        "whole portfolio and whether the position would be a directly held share or a fund. "
        "When the message does not say which, do not call this tool."),
    "policy_lookup": (
        "What the investment policy says on a topic: the clauses whose topics occur in the "
        "words passed, each quoted with its id, or that the policy contains nothing on it. "
        "Pass the question's own words for the topic. This is also the tool for a question "
        "the policy places outside what it answers."),
    "philosophy_screen": (
        "One company screened against the owner's investment philosophy on its filed figures: "
        "one finding per numeric clause with its distance, the valuation range from the "
        "owner's stated assumptions, and the last stored close. Pass the one ticker."),
    "thesis": (
        "For one company on the watchlist, its latest annual report read and one dated "
        "prediction proposed that tests the owner's thesis, for the owner to enter or not. "
        "Pass the ticker."),
    "position": (
        "Whether the owner's checks support taking a position in one company on the watchlist "
        "at the weight its entry states: the philosophy screen, the valuation range, the "
        "reading and the policy check at that weight. Pass the ticker only; the weight is the "
        "entry's."),
    "rebalance": (
        "The portfolio's drift against the policy's target allocation and whether it calls for "
        "rebalancing. No trade is shown."),
    "ledger": (
        "The owner's prediction ledger as of today: every prediction with its due date and "
        "status, a due one scored against what the company reported."),
}

if set(TOOL_DESCRIPTIONS) != set(TOOLS):
    raise RuntimeError(f"tool descriptions {sorted(TOOL_DESCRIPTIONS)} and tools "
                       f"{sorted(TOOLS)} disagree; a tool is described once or not at all")


def tool_definitions() -> List[Dict[str, Any]]:
    """The eleven tools as the API is sent them, strict, in TOOLS order."""
    return [{"name": tool, "description": TOOL_DESCRIPTIONS[tool],
             "input_schema": tool_schema(tool), "strict": True} for tool in TOOLS]


class ConversationModel:
    """Sends one request of the tool loop to the model."""

    def __init__(self, client, model: str):
        self.client = client
        self.id = model

    def respond(self, system: str, tools: Sequence[Mapping[str, Any]],
                messages: Sequence[Mapping[str, Any]]):
        try:
            return self.client.messages.create(
                model=self.id,
                max_tokens=MAX_TOKENS,
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                tools=list(tools),
                messages=list(messages),
                output_config={"effort": "low"},
            )
        except anthropic.APIStatusError as error:
            raise ConversationError(f"The model refused the request, {error.status_code}: "
                                    f"{error.message}") from error


def conversation_model() -> ConversationModel:
    """The model the conversation layer runs on (decision 45)."""
    return ConversationModel(anthropic.Anthropic(api_key=ANTHROPIC_SONNET.api_key),
                             ANTHROPIC_SONNET.model)


# A figure as the formatters print it: digits, thousands commas, an
# optional decimal part. A date is three of these and a clause id one.
FIGURE = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def untraced_figures(answer: str, texts: Sequence[str], question: str) -> List[str]:
    """The number tokens of the answer that are tokens of neither a tool's
    text nor the question, compared whole: 4.4 is not 4.41."""
    allowed = set(FIGURE.findall(question))
    for text in texts:
        allowed.update(FIGURE.findall(text))
    return sorted(set(FIGURE.findall(answer)) - allowed)


def _usage(response) -> Dict[str, Any]:
    usage = response.usage
    return {"model": response.model,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_creation_input_tokens": usage.cache_creation_input_tokens or 0,
            "cache_read_input_tokens": usage.cache_read_input_tokens or 0}


def _turn(text: str, records: List[Dict[str, Any]], calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"text": text, "tool_calls": records, "model_calls": calls}


async def answer(message: str, *, history: Sequence[Any], context: ToolContext,
                 portfolio_id: Optional[int], model: ConversationModel,
                 request_id: Optional[str] = None,
                 earlier: Sequence[str] = ()) -> Dict[str, Any]:
    """One turn: the answer's text, the tool-call records in call order and
    the usage of every model call. A run's final state stops at its record,
    which carries every block the run published (decision 77). `earlier`
    is the texts of the conversation's earlier turns, each question and
    each tool's text, whose figures the answer may carry beside this
    turn's own; the model is not shown them, only `history`."""
    messages: List[Any] = list(history) + [{"role": "user", "content": message}]
    tools = tool_definitions()
    records: List[Dict[str, Any]] = []
    calls: List[Dict[str, Any]] = []

    for _ in range(MAX_MODEL_CALLS):
        try:
            response = model.respond(SYSTEM_PROMPT, tools, messages)
        except ConversationError as error:
            raise ConversationError(str(error), calls) from error
        calls.append(_usage(response))

        if response.stop_reason == "end_turn":
            text = "\n".join(b.text for b in response.content if b.type == "text").strip()
            untraced = untraced_figures(text, [r["text"] for r in records] + list(earlier),
                                        message)
            if untraced:
                text = (f"The answer carried figures no tool printed this turn: "
                        f"{', '.join(untraced)}. It is not shown.")
            return _turn(text, records, calls)
        if response.stop_reason != "tool_use":
            raise ConversationError(f"The model stopped on {response.stop_reason!r} before "
                                    "finishing its answer; nothing is shown.", calls)

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                inputs = validate_inputs(block.name, block.input, context)
                record, _ = await run_tool(block.name, inputs, portfolio_id, request_id)
            except (ToolInputError, ToolRunError) as error:
                return _turn(str(error), records, calls)
            records.append(record)
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": record["text"]})
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": results})

    raise ConversationError(f"The model made {MAX_MODEL_CALLS} calls without finishing the "
                            "turn; nothing is shown.", calls)
