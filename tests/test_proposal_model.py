"""
agents.proposal_model: the request a proposal makes and the answers it
refuses, held to expected_values.md Part 15 F, D58.

No network. The stand-in client records the request and answers with a
fixed response shaped like the SDK's; the SDK's own error class stands for
the API's refusal of a request.

The rules, each a test:

  - the request names the model `ANTHROPIC_SONNET` names, carries no
    temperature and no other sampling setting, sends the prompt as the
    system prompt and the message as the one user message, and asks for the
    schema passed through structured output
  - the prediction comes back as the model wrote it, unchecked
  - a stop other than `end_turn` (S-7), no text or two texts, text that is
    not JSON, and an object that is not `prediction` holding one object
    (S-4) are each refused, after one request
  - the API's refusal of a request is refused
"""

import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from agents.config import ANTHROPIC_SONNET
from agents.proposal_model import (MAX_TOKENS, ProposalModel, ProposalModelError,
                                   proposal_model)


PROMPT = "a fixed prompt"
SCHEMA = {"type": "object", "properties": {"prediction": {"type": "object"}},
          "required": ["prediction"], "additionalProperties": False}
TEXT = "Thesis:\nThe business sells subscriptions customers keep renewing."
PREDICTION = {"kind": "figure", "metric": "gross_margin", "bound": "min", "reasons": ["1.1"]}


def _response(text=None, stop="end_turn", blocks=None):
    if blocks is None:
        blocks = [SimpleNamespace(type="text", text=json.dumps({"prediction": PREDICTION})
                                  if text is None else text)]
    return SimpleNamespace(stop_reason=stop, content=blocks)


class _Client:
    def __init__(self, response=None, error=None):
        self.response = response if response is not None else _response()
        self.error = error
        self.requests = []
        self.messages = self

    def create(self, **request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.response


def _propose(client, model=ANTHROPIC_SONNET.model):
    return ProposalModel(client, model).propose(PROMPT, SCHEMA, TEXT)


# --- the request -------------------------------------------------------------

def test_the_request_is_the_references():
    client = _Client()
    _propose(client)
    assert client.requests == [{
        "model": "claude-sonnet-5",
        "max_tokens": 16_000,
        "system": PROMPT,
        "messages": [{"role": "user", "content": TEXT}],
        "output_config": {"format": {"type": "json_schema", "schema": SCHEMA}},
    }]


@pytest.mark.parametrize("key", ["temperature", "top_p", "top_k"])
def test_no_sampling_setting_is_sent(key):
    client = _Client()
    _propose(client)
    assert key not in client.requests[0]


def test_the_model_is_the_stronger_one_and_not_the_routers(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a stand-in key")
    model = proposal_model()
    assert model.id == ANTHROPIC_SONNET.model == "claude-sonnet-5"
    from agents.config import ACTIVE_LLM_CONFIG
    assert model.id != ACTIVE_LLM_CONFIG.model
    assert MAX_TOKENS == 16_000


# --- the answer --------------------------------------------------------------

def test_the_prediction_comes_back_as_written():
    assert _propose(_Client()) == PREDICTION


def test_the_prediction_is_not_checked_here():
    unchecked = {"kind": "figure", "metric": "return_on_invested_capital", "value": 420}
    client = _Client(_response(json.dumps({"prediction": unchecked})))
    assert _propose(client) == unchecked


@pytest.mark.parametrize("stop", ["max_tokens", "refusal", "tool_use", "pause_turn", None])
def test_s_7_a_stop_other_than_the_end_of_the_answer_is_refused_after_one_request(stop):
    client = _Client(_response(stop=stop))
    with pytest.raises(ProposalModelError, match="the model stopped"):
        _propose(client)
    assert len(client.requests) == 1


@pytest.mark.parametrize("blocks", [[], [SimpleNamespace(type="text", text="{}"),
                                         SimpleNamespace(type="text", text="{}")]],
                         ids=["none", "two"])
def test_not_exactly_one_text_is_refused(blocks):
    with pytest.raises(ProposalModelError, match="text blocks"):
        _propose(_Client(_response(blocks=blocks)))


def test_a_thinking_block_beside_the_text_is_not_a_text():
    blocks = [SimpleNamespace(type="thinking", thinking=""),
              SimpleNamespace(type="text", text=json.dumps({"prediction": PREDICTION}))]
    assert _propose(_Client(_response(blocks=blocks))) == PREDICTION


def test_text_that_is_not_json_is_refused():
    with pytest.raises(ProposalModelError, match="not JSON"):
        _propose(_Client(_response("Gross margin holds.")))


@pytest.mark.parametrize("answer", [{"prediction": [PREDICTION, PREDICTION]},
                                    {"prediction": "gross_margin"},
                                    {"prediction": PREDICTION, "note": "x"},
                                    {"predictions": [PREDICTION]}, [PREDICTION]],
                         ids=["s-4 two objects", "a string", "another key", "another name",
                              "a list"])
def test_s_4_an_answer_that_is_not_one_prediction_is_refused(answer):
    with pytest.raises(ProposalModelError, match="not one object holding one prediction"):
        _propose(_Client(_response(json.dumps(answer))))


def test_the_apis_refusal_is_refused():
    response = httpx2.Response(400, request=httpx2.Request("POST", "https://api.invalid/v1"))
    error = anthropic.BadRequestError("prompt is too long", response=response, body=None)
    client = _Client(error=error)
    with pytest.raises(ProposalModelError, match="the model refused the request, 400"):
        _propose(client)
    assert len(client.requests) == 1
