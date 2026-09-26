"""
The conversation layer's client (decision 45): one turn of the tool loop
on a stand-in model, so that nothing here is paid for.

What a turn is held to. The model chooses tools from the eleven and is
shown each tool's rendered text; a tool's input model that raises, or a
run that raises, ends the turn with the error shown unchanged and the model
not asked again; an answer carrying a figure no tool printed that turn and
the question did not carry is refused with the figure named, not redacted
(DIRECTION.md invariant 1); `usage` is recorded for every call from the
first. The request is the one decision 45 chose: the conversation model,
the system prompt and the eleven strict tool definitions cached as a
prefix, no temperature. Neither the system prompt nor a tool description
quotes a benchmark or corpus prompt.
"""

import importlib
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents.tool_inputs import TOOLS, ToolContext

ROOT = Path(__file__).parent.parent

CONTEXT = ToolContext(held=("JPM", "AAPL"), periods=("1Y", "3Y"), watchlist=("GOOGL",))


@pytest.fixture
def conversation():
    return importlib.import_module("agents.conversation")


def _usage(i=100, o=20, created=0, read=0):
    return SimpleNamespace(input_tokens=i, output_tokens=o,
                           cache_creation_input_tokens=created, cache_read_input_tokens=read)


def _tool_use(name, inputs, id_="tu_1"):
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=inputs)


def _text(text):
    return SimpleNamespace(type="text", text=text)


def _response(stop, *content, usage=None):
    return SimpleNamespace(stop_reason=stop, content=list(content), model="claude-sonnet-5",
                           usage=usage or _usage())


class StandIn:
    """Answers each request with the next scripted response and keeps what
    it was sent."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def respond(self, system, tools, messages):
        self.requests.append({"system": system, "tools": tools, "messages": list(messages)})
        return self.responses.pop(0)


JPM_TEXT = "JPM: 100 shares, P&L +15,622.00 (+78.11%) as of 2026-09-02."
JPM_RECORD = {"tool": "position_pnl", "inputs": {"tickers": ["JPM"]}, "key": "position_pnl",
              "block": {"JPM": {}}, "text": JPM_TEXT, "as_of": "2026-09-02"}


@pytest.fixture
def tools_run(conversation, monkeypatch):
    runs = []

    async def run_tool(tool, inputs, portfolio_id, request_id=None):
        runs.append((tool, inputs, portfolio_id))
        return JPM_RECORD, {"shared_data": {"position_pnl": {"JPM": {}}}, "sub_results": {}}

    monkeypatch.setattr(conversation, "run_tool", run_tool)
    return runs


async def _turn(conversation, model, message="How has my JPM position performed?", **kwargs):
    return await conversation.answer(message, history=[], context=CONTEXT, portfolio_id=3,
                                     model=model, **kwargs)


async def test_a_tool_is_called_its_text_shown_and_the_answer_narrated(conversation, tools_run):
    model = StandIn(
        _response("tool_use", _tool_use("position_pnl", {"tickers": ["JPM"]})),
        _response("end_turn", _text("JPM is up +15,622.00, +78.11%, as of 2026-09-02.")),
    )
    turn = await _turn(conversation, model)
    assert tools_run == [("position_pnl", {"tickers": ["JPM"]}, 3)]
    assert turn["tool_calls"] == [JPM_RECORD]
    assert turn["text"] == "JPM is up +15,622.00, +78.11%, as of 2026-09-02."
    assert set(turn) == {"text", "tool_calls", "model_calls"}, \
        "the run's state stops at the record, and the messages nothing read are gone (decision 77)"
    [result] = model.requests[1]["messages"][-1]["content"]
    assert (result["type"], result["tool_use_id"], result["content"]) == \
        ("tool_result", "tu_1", JPM_TEXT)


async def test_a_figure_an_earlier_turn_printed_or_asked_is_allowed(conversation, tools_run):
    """S-4's follow-up (decision 77): the earlier turns' tool texts and
    questions are given to the layer as `earlier`, and a figure from them
    is allowed as this turn's own are. Without them the same answer is
    refused by name."""
    answer = "Last turn Equity was 69.41% of the total, and you asked about 15%."
    earlier = ["Can I put 15% into one position?", "Equity: 69.41% of total"]
    turn = await _turn(conversation, StandIn(_response("end_turn", _text(answer))),
                       "What did we say?", earlier=earlier)
    assert turn["text"] == answer
    refused = await _turn(conversation, StandIn(_response("end_turn", _text(answer))),
                          "What did we say?")
    assert "not shown" in refused["text"] and "69.41" in refused["text"] and "15" in refused["text"]


async def test_every_call_records_its_usage(conversation, tools_run):
    model = StandIn(
        _response("tool_use", _tool_use("position_pnl", {"tickers": ["JPM"]}),
                  usage=_usage(4200, 60, created=4000)),
        _response("end_turn", _text("As of 2026-09-02."), usage=_usage(300, 40, read=4000)),
    )
    turn = await _turn(conversation, model)
    assert turn["model_calls"] == [
        {"model": "claude-sonnet-5", "input_tokens": 4200, "output_tokens": 60,
         "cache_creation_input_tokens": 4000, "cache_read_input_tokens": 0},
        {"model": "claude-sonnet-5", "input_tokens": 300, "output_tokens": 40,
         "cache_creation_input_tokens": 0, "cache_read_input_tokens": 4000},
    ]


async def test_an_input_the_tool_refuses_ends_the_turn_unchanged(conversation, tools_run):
    model = StandIn(_response("tool_use", _tool_use("position_pnl", {"tickers": ["JMP"]})))
    turn = await _turn(conversation, model)
    assert tools_run == [] and len(model.requests) == 1
    assert turn["tool_calls"] == []
    assert turn["text"].startswith("position_pnl cannot answer on these inputs") and "JMP" in turn["text"]


async def test_a_run_that_raises_ends_the_turn_unchanged(conversation, monkeypatch):
    async def failing(tool, inputs, portfolio_id, request_id=None):
        raise conversation.ToolRunError("rebalance: no target allocation is stated")

    monkeypatch.setattr(conversation, "run_tool", failing)
    model = StandIn(_response("tool_use", _tool_use("rebalance", {})))
    turn = await _turn(conversation, model, "Should I rebalance?")
    assert turn["text"] == "rebalance: no target allocation is stated"
    assert len(model.requests) == 1


async def test_a_figure_no_tool_printed_is_refused_by_name(conversation, tools_run):
    model = StandIn(
        _response("tool_use", _tool_use("position_pnl", {"tickers": ["JPM"]})),
        _response("end_turn", _text("JPM is up about 78.1%, as of 2026-09-02.")),
    )
    turn = await _turn(conversation, model)
    assert "78.1" in turn["text"] and "not shown" in turn["text"]
    assert "JPM is up about" not in turn["text"]


async def test_the_question_s_own_figures_are_allowed(conversation, tools_run):
    model = StandIn(_response("end_turn", _text("A weight of 15% is not one I can check here.")))
    turn = await _turn(conversation, model, "Can I put 15% into one position?")
    assert turn["text"] == "A weight of 15% is not one I can check here."


@pytest.mark.parametrize("stop", ["max_tokens", "refusal"])
async def test_a_turn_the_model_did_not_finish_raises(conversation, tools_run, stop):
    model = StandIn(_response(stop, _text("JPM is")))
    with pytest.raises(conversation.ConversationError, match=stop):
        await _turn(conversation, model)


async def test_a_turn_that_keeps_calling_tools_is_stopped(conversation, tools_run):
    model = StandIn(*[_response("tool_use", _tool_use("position_pnl", {"tickers": ["JPM"]}, f"tu_{i}"))
                      for i in range(conversation.MAX_MODEL_CALLS + 1)])
    with pytest.raises(conversation.ConversationError, match="calls"):
        await _turn(conversation, model)
    assert len(model.requests) == conversation.MAX_MODEL_CALLS


# --- the request ---------------------------------------------------------------

def test_the_eleven_tools_are_offered_strict(conversation):
    definitions = conversation.tool_definitions()
    assert [d["name"] for d in definitions] == list(TOOLS)
    for d in definitions:
        assert d["strict"] is True and d["input_schema"]["additionalProperties"] is False
        assert d["description"].strip()


def test_the_request_is_the_conversation_model_with_the_prefix_cached(conversation):
    sent = {}

    class Client:
        class messages:
            @staticmethod
            def create(**kwargs):
                sent.update(kwargs)
                return _response("end_turn", _text("ok"))

    model = conversation.ConversationModel(Client(), "claude-sonnet-5")
    model.respond(conversation.SYSTEM_PROMPT, conversation.tool_definitions(),
                  [{"role": "user", "content": "q"}])
    assert sent["model"] == "claude-sonnet-5"
    assert "temperature" not in sent
    [system] = sent["system"]
    assert system["text"] == conversation.SYSTEM_PROMPT
    assert system["cache_control"] == {"type": "ephemeral"}
    assert [t["name"] for t in sent["tools"]] == list(TOOLS)


def test_the_model_is_the_one_decision_45_chose(conversation):
    from agents.config import ANTHROPIC_SONNET
    assert conversation.conversation_model().id == ANTHROPIC_SONNET.model == "claude-sonnet-5"


def _corpus_prompts():
    """Every prompt in benchmark.md Part 3c's tables and sequences."""
    text = (ROOT / "docs" / "benchmark.md").read_text(encoding="utf-8")
    part = text[text.index("### 3c.1"):text.index("### 3c.6")]
    prompts = set()
    for line in part.splitlines():
        row = re.match(r"^\| ([A-Z0-9][\w.-]*) \| (.+?) \|", line)
        if row and not row.group(2).startswith(("Prompt", "---")):
            prompts.update(p.strip() for p in re.split(r"Turn \d: ", row.group(2)) if p.strip())
        turn = re.match(r"^\d\. (.+?\?|.+?\.) ", line + " ")
        if turn:
            prompts.add(turn.group(1).strip())
    return {p for p in prompts if len(p) > 12}


def test_no_prompt_quotes_a_benchmark_or_corpus_prompt(conversation):
    prompts = _corpus_prompts()
    assert len(prompts) > 40
    words = conversation.SYSTEM_PROMPT + " ".join(
        d["description"] for d in conversation.tool_definitions())
    quoted = sorted(p for p in prompts if p.lower() in words.lower())
    assert quoted == []


NOTATION = ("Write every figure with the digits, separators and decimal point exactly as "
            "the tool printed it, whatever language you answer in.")


def test_the_prompt_keeps_the_tools_notation_in_any_language(conversation):
    """A German answer wrote 406,229.50 as 406.229,50 and the client
    refused it whole (KNOWN_GAPS, "The tracing check refuses an answer
    written in German number format"). The notation of a figure is the
    tool's, whatever the language of the prose; the check does not move."""
    assert conversation.SYSTEM_PROMPT.endswith(NOTATION)
