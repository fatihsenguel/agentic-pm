"""
agents.view_model: the request the view of a thesis makes and the answers
it refuses, held to expected_values.md Part 15 G, D61.

No network. The stand-in client records the request and answers with a
fixed response shaped like the SDK's; the SDK's own error class stands for
the API's refusal of a request. The shape is `test_proposal_model.py`'s,
the request being the same one with a different system prompt and a
different outer key, and the response builder and the client are imported
from it so that a change to the SDK's shape is read in one place.

The rules, each a test:

  - the request names the model `ANTHROPIC_SONNET` names, carries no
    temperature and no other sampling setting, sends the prompt as the
    system prompt and the message as the one user message, and asks for
    the schema passed through structured output
  - the view comes back as the model wrote it, unchecked
  - a stop other than `end_turn`, no text or two texts, text that is not
    JSON, and an object that is not `view` holding one object are each
    refused, after one request
  - the API's refusal of a request is refused
  - the request is the proposal's in every part but the system prompt and
    the schema: the two go to one model and one place decides which
"""

import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from agents.config import ANTHROPIC_SONNET
from agents.view_model import MAX_TOKENS, ViewModel, ViewModelError, view_model

from test_proposal_model import _Client, _response

PROMPT = "a fixed prompt"
SCHEMA = {"type": "object", "properties": {"view": {"type": "object"}},
          "required": ["view"], "additionalProperties": False}
TEXT = "Thesis:\nThe business sells subscriptions customers keep renewing."
VIEW = {"thesis_view": "stands", "reasons": ["1.1"], "uncertainty": "stated"}


def _answered(answer, stop="end_turn", blocks=None):
    """A response carrying `answer` as its one text, or `blocks` as given.
    `_response` from the proposal model's tests defaults its text to a
    prediction, so a view's answer is always passed in."""
    if blocks is not None:
        return _response(stop=stop, blocks=blocks)
    return _response(text=json.dumps(answer), stop=stop)


def _view(client, model=ANTHROPIC_SONNET.model):
    return ViewModel(client, model).view(PROMPT, SCHEMA, TEXT)


# --- the request -------------------------------------------------------------

def test_the_request_is_the_references():
    client = _Client(_answered({"view": VIEW}))
    _view(client)
    assert client.requests == [{
        "model": "claude-sonnet-5",
        "max_tokens": 16_000,
        "system": PROMPT,
        "messages": [{"role": "user", "content": TEXT}],
        "output_config": {"format": {"type": "json_schema", "schema": SCHEMA}},
    }]


@pytest.mark.parametrize("key", ["temperature", "top_p", "top_k"])
def test_no_sampling_setting_is_sent(key):
    client = _Client(_answered({"view": VIEW}))
    _view(client)
    assert key not in client.requests[0]


def test_the_model_is_the_stronger_one_and_not_the_routers(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a stand-in key")
    model = view_model()
    assert model.id == ANTHROPIC_SONNET.model == "claude-sonnet-5"
    from agents.config import ACTIVE_LLM_CONFIG
    assert model.id != ACTIVE_LLM_CONFIG.model
    assert MAX_TOKENS == 16_000


def test_the_request_is_the_proposals_but_for_the_prompt_and_the_schema():
    from agents.proposal_model import ProposalModel
    mine = _Client(_answered({"view": VIEW}))
    theirs = _Client()
    _view(mine)
    ProposalModel(theirs, ANTHROPIC_SONNET.model).propose(PROMPT, SCHEMA, TEXT)
    assert mine.requests == theirs.requests


# --- the answer --------------------------------------------------------------

def test_the_view_comes_back_as_written():
    assert _view(_Client(_answered({"view": VIEW}))) == VIEW


def test_the_view_is_not_checked_here():
    unchecked = {"thesis_view": "holds", "reasons": ["1.9"], "sentence": "It is fine."}
    assert _view(_Client(_answered({"view": unchecked}))) == unchecked


@pytest.mark.parametrize("stop", ["max_tokens", "refusal", "tool_use", "pause_turn", None])
def test_a_stop_other_than_the_end_of_the_answer_is_refused_after_one_request(stop):
    client = _Client(_answered({"view": VIEW}, stop=stop))
    with pytest.raises(ViewModelError, match="the model stopped"):
        _view(client)
    assert len(client.requests) == 1


@pytest.mark.parametrize("blocks", [[], [SimpleNamespace(type="text", text="{}"),
                                         SimpleNamespace(type="text", text="{}")]],
                         ids=["none", "two"])
def test_not_exactly_one_text_is_refused(blocks):
    with pytest.raises(ViewModelError, match="text blocks"):
        _view(_Client(_answered(None, blocks=blocks)))


def test_a_thinking_block_beside_the_text_is_not_a_text():
    blocks = [SimpleNamespace(type="thinking", thinking=""),
              SimpleNamespace(type="text", text=json.dumps({"view": VIEW}))]
    assert _view(_Client(_answered(None, blocks=blocks))) == VIEW


def test_text_that_is_not_json_is_refused():
    with pytest.raises(ViewModelError, match="not JSON"):
        _view(_Client(_response(text="The thesis stands.")))


@pytest.mark.parametrize("answer", [{"view": [VIEW, VIEW]},
                                    {"view": "stands"},
                                    {"view": VIEW, "note": "x"},
                                    {"views": [VIEW]},
                                    {"prediction": VIEW},
                                    [VIEW]],
                         ids=["two objects", "a string", "another key", "another name",
                              "the proposal's key", "a list"])
def test_an_answer_that_is_not_one_view_is_refused(answer):
    with pytest.raises(ViewModelError, match="not one object holding one view"):
        _view(_Client(_answered(answer)))


def test_the_apis_refusal_is_refused():
    response = httpx2.Response(400, request=httpx2.Request("POST", "https://api.invalid/v1"))
    error = anthropic.BadRequestError("prompt is too long", response=response, body=None)
    client = _Client(error=error)
    with pytest.raises(ViewModelError, match="the model refused the request, 400"):
        _view(client)
    assert len(client.requests) == 1
