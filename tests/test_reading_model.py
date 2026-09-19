"""
agents.reading_model: the request a reading makes and the answers it
refuses, held to expected_values.md Part 16 J, D56.

No network. The stand-in client records the request and answers with a
fixed response shaped like the SDK's; the SDK's own error class stands for
the API's refusal of a request.

The rules, each a test:

  - the request names the model `ANTHROPIC_SONNET` names, carries no
    temperature and no other sampling setting, sends the prompt as the
    system prompt and the section's text as the one user message, and asks
    for the schema passed through structured output
  - the claims come back as the model wrote them, unchecked
  - a stop other than `end_turn`, no text or two texts, text that is not
    JSON, and an object that is not `claims` and a list are each refused
  - the API's refusal of a request is refused naming the section
"""

import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from agents.config import ANTHROPIC_SONNET
from agents.reading_model import MAX_TOKENS, ReadingModel, ReadingModelError, reading_model


SECTION = "Item 1A"
PROMPT = "a fixed prompt"
SCHEMA = {"type": "object", "properties": {"claims": {"type": "array"}},
          "required": ["claims"], "additionalProperties": False}
TEXT = "ITEM 1A.RISK FACTORS\nOur operations are subject to risks."
CLAIMS = [{"claim": "The company names its risks.", "quote": "Our operations are subject",
           "uncertainty": "stated"}]


def _response(text=None, stop="end_turn", blocks=None):
    if blocks is None:
        blocks = [SimpleNamespace(type="text", text=json.dumps({"claims": CLAIMS})
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


def _read(client, model=ANTHROPIC_SONNET.model):
    return ReadingModel(client, model).read(SECTION, PROMPT, SCHEMA, TEXT)


# --- the request -------------------------------------------------------------

def test_the_request_is_the_references():
    client = _Client()
    _read(client)
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
    _read(client)
    assert key not in client.requests[0]


def test_the_model_is_the_stronger_one_and_not_the_routers(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a stand-in key")
    model = reading_model()
    assert model.id == ANTHROPIC_SONNET.model == "claude-sonnet-5"
    from agents.config import ACTIVE_LLM_CONFIG
    assert model.id != ACTIVE_LLM_CONFIG.model
    assert MAX_TOKENS == 16_000


# --- the answer --------------------------------------------------------------

def test_the_claims_come_back_as_written():
    assert _read(_Client()) == CLAIMS


def test_claims_are_not_checked_here():
    unchecked = [{"claim": "Revenue was 402,836 million.", "quote": "not in the text",
                  "uncertainty": "likely", "id": "x"}]
    client = _Client(_response(json.dumps({"claims": unchecked})))
    assert _read(client) == unchecked


@pytest.mark.parametrize("stop", ["max_tokens", "refusal", "tool_use", "pause_turn", None])
def test_a_stop_other_than_the_end_of_the_answer_is_refused(stop):
    with pytest.raises(ReadingModelError, match=f"{SECTION}: the model stopped"):
        _read(_Client(_response(stop=stop)))


@pytest.mark.parametrize("blocks", [[], [SimpleNamespace(type="text", text="{}"),
                                         SimpleNamespace(type="text", text="{}")]],
                         ids=["none", "two"])
def test_not_exactly_one_text_is_refused(blocks):
    with pytest.raises(ReadingModelError, match="text blocks"):
        _read(_Client(_response(blocks=blocks)))


def test_a_thinking_block_beside_the_text_is_not_a_text():
    blocks = [SimpleNamespace(type="thinking", thinking=""),
              SimpleNamespace(type="text", text=json.dumps({"claims": CLAIMS}))]
    assert _read(_Client(_response(blocks=blocks))) == CLAIMS


def test_text_that_is_not_json_is_refused():
    with pytest.raises(ReadingModelError, match="not JSON"):
        _read(_Client(_response("The company names its risks.")))


@pytest.mark.parametrize("answer", [[], {"claims": {}}, {"claims": CLAIMS, "summary": "x"},
                                    {"items": CLAIMS}, "claims"],
                         ids=["a list", "claims not a list", "another key", "another name",
                              "a string"])
def test_an_answer_that_is_not_a_list_of_claims_is_refused(answer):
    with pytest.raises(ReadingModelError, match="not one object holding a list"):
        _read(_Client(_response(json.dumps(answer))))


def test_the_apis_refusal_is_refused_naming_the_section():
    response = httpx2.Response(400, request=httpx2.Request("POST", "https://api.invalid/v1"))
    error = anthropic.BadRequestError("prompt is too long", response=response, body=None)
    with pytest.raises(ReadingModelError, match=f"{SECTION}: the model refused the request, 400"):
        _read(_Client(error=error))
