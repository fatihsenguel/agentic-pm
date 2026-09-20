"""
portfolio_tool.thesis_view: the model's view of a thesis, held to
expected_values.md Part 15 G, D61.

The model is a stand-in that records what it is asked and answers with a
fixed view. The thesis, the claims and the message are the proposer's
tests', imported so that the view and the prediction are held over one
set of claims and one message: decision A of this session sends the same
string to both requests, and a test that built its own would not see them
diverge.

The rules, each a test:

  - the request is the fixed prompt, the schema and the proposer's
    message, once, and the message is `proposer.message` itself
  - the closed sets are written here as literals, and the parametrized
    tests take their cases from literals too: two wrong versions showed
    that a test reading the constant it checks follows a wrong constant
    rather than catching it
  - the prompt defines each of the three values, on the definition line
    and not the word anywhere, and says nothing about what the view is
    used for
  - the schema is one object `view` of the three fields, the values
    enumerated and nothing else allowed
  - G's rows: T-1 to T-4 accepted, T-5 to T-10 refused, each naming its
    rule
  - a thesis or a claim missing refuses before any request
  - the type guards beyond G's rows: a view that is not an object, a
    `reasons` that is a string, a field missing
  - nothing is written
"""

import pytest

from portfolio_tool import thesis_view
from portfolio_tool.reading import UNCERTAINTIES

from test_proposer import MESSAGE, READINGS, THESIS, _reading

CLAIM_IDS = ("1.1", "7.2")


class _Model:
    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error
        self.asked = []

    def view(self, prompt, schema, text):
        self.asked.append((prompt, schema, text))
        if self.error is not None:
            raise self.error
        return self.answer


def view(value="stands", reasons=("1.1",), uncertainty="stated", **extra):
    return {"thesis_view": value, "reasons": list(reasons), "uncertainty": uncertainty,
            **extra}


def _ask(model, thesis=THESIS, readings=READINGS):
    return thesis_view.ask(model, thesis, readings)


# --- the request ---------------------------------------------------------------------

def test_the_request_is_the_prompt_the_schema_and_the_message_once():
    model = _Model(view())
    _ask(model)
    assert model.asked == [(thesis_view.PROMPT, thesis_view.SCHEMA, MESSAGE)]


def test_the_message_is_the_proposers_and_is_not_rewritten():
    from portfolio_tool import proposer
    model = _Model(view())
    _ask(model)
    assert model.asked[0][2] == proposer.message(THESIS, READINGS)


def test_the_closed_sets_are_the_references():
    # Written as literals and not off the module: a test parametrized over
    # the constant it is checking follows a wrong constant instead of
    # catching it, which is what two wrong versions showed.
    assert thesis_view.VIEWS == ("stands", "strained", "no_view")
    assert thesis_view.NEEDS_REASON == ("stands", "strained")
    assert thesis_view.NO_VIEW == "no_view"
    assert thesis_view.SUPPLIED == {"thesis_view", "reasons", "uncertainty"}
    assert UNCERTAINTIES == ("stated", "inferred")


def test_the_prompt_defines_each_of_the_three_values():
    # The definition line and not the word anywhere: the reasons paragraph
    # mentions `no_view` too, so a prompt that lost the definition still
    # carried the word.
    for value in ("stands", "strained", "no_view"):
        assert f"{value}: " in thesis_view.PROMPT


def test_the_prompt_does_not_say_what_the_view_is_used_for():
    # The composition is decision 68's and the model is not told it.
    lowered = thesis_view.PROMPT.lower()
    for word in ("entry", "outcome", "buy", "gate", "policy"):
        assert word not in lowered


def test_the_schema_is_one_object_of_the_three_fields():
    assert thesis_view.SCHEMA["required"] == ["view"]
    assert thesis_view.SCHEMA["additionalProperties"] is False
    inner = thesis_view.SCHEMA["properties"]["view"]
    assert set(inner["properties"]) == thesis_view.SUPPLIED
    assert set(inner["required"]) == thesis_view.SUPPLIED
    assert inner["additionalProperties"] is False
    assert inner["properties"]["thesis_view"]["enum"] == list(thesis_view.VIEWS)
    assert inner["properties"]["uncertainty"]["enum"] == list(UNCERTAINTIES)
    assert inner["properties"]["reasons"]["items"] == {"type": "string"}


# --- the rows of section G -----------------------------------------------------------

def test_t_1_stands_on_one_reason_is_accepted():
    record = thesis_view.record(view(), CLAIM_IDS)
    assert (record.thesis_view, record.reasons, record.uncertainty) == (
        "stands", ("1.1",), "stated")


def test_t_2_strained_on_one_reason_is_accepted():
    record = thesis_view.record(view("strained", ("7.2",), "inferred"), CLAIM_IDS)
    assert (record.thesis_view, record.reasons, record.uncertainty) == (
        "strained", ("7.2",), "inferred")


def test_t_3_more_than_one_reason_is_accepted():
    record = thesis_view.record(view("strained", ("1.1", "7.2"), "inferred"), CLAIM_IDS)
    assert record.reasons == ("1.1", "7.2")


def test_t_4_no_view_needs_no_reason():
    record = thesis_view.record(view("no_view", (), "inferred"), CLAIM_IDS)
    assert (record.thesis_view, record.reasons) == ("no_view", ())


@pytest.mark.parametrize("value", ["stands", "strained"])
def test_t_5_a_view_without_a_reason_is_refused(value):
    with pytest.raises(thesis_view.ThesisViewError, match="gives no reason"):
        thesis_view.record(view(value, ()), CLAIM_IDS)


def test_t_6_a_reason_beside_no_view_is_refused():
    with pytest.raises(thesis_view.ThesisViewError, match="rests on, and this one states none"):
        thesis_view.record(view("no_view", ("1.1",)), CLAIM_IDS)


def test_t_7_a_value_outside_the_set_is_refused():
    with pytest.raises(thesis_view.ThesisViewError, match="'holds' is not one of"):
        thesis_view.record(view("holds"), CLAIM_IDS)


def test_t_8_a_reason_that_is_no_claim_is_refused():
    with pytest.raises(thesis_view.ThesisViewError, match="'1.9' is no claim"):
        thesis_view.record(view(reasons=("1.9",)), CLAIM_IDS)


def test_t_9_an_uncertainty_outside_the_two_is_refused():
    with pytest.raises(thesis_view.ThesisViewError, match="'likely' is not one of"):
        thesis_view.record(view(uncertainty="likely"), CLAIM_IDS)


def test_t_10_a_fourth_field_is_refused():
    with pytest.raises(thesis_view.ThesisViewError, match=r"\['sentence'\]"):
        thesis_view.record(view(sentence="The thesis holds."), CLAIM_IDS)


# --- the type guards, beyond G's rows ------------------------------------------------

@pytest.mark.parametrize("supplied", ["stands", ["stands"], None])
def test_a_view_that_is_not_an_object_is_refused(supplied):
    with pytest.raises(thesis_view.ThesisViewError, match="a view is an object"):
        thesis_view.record(supplied, CLAIM_IDS)


def test_reasons_as_one_string_is_refused():
    supplied = view()
    supplied["reasons"] = "1.1"
    with pytest.raises(thesis_view.ThesisViewError, match="not a list of claim ids"):
        thesis_view.record(supplied, CLAIM_IDS)


@pytest.mark.parametrize("field", ["thesis_view", "reasons", "uncertainty"])
def test_a_field_missing_is_refused(field):
    supplied = view()
    del supplied[field]
    with pytest.raises(thesis_view.ThesisViewError, match=f"states no {field}"):
        thesis_view.record(supplied, CLAIM_IDS)


# --- what is refused before the request ----------------------------------------------

@pytest.mark.parametrize("thesis", ["", "   ", None])
def test_no_thesis_refuses_before_any_request(thesis):
    model = _Model(view())
    with pytest.raises(thesis_view.ThesisViewError, match="no thesis"):
        _ask(model, thesis=thesis)
    assert model.asked == []


@pytest.mark.parametrize("readings", [(), (_reading("Item 1"),)], ids=["none", "no claims"])
def test_no_claim_refuses_before_any_request(readings):
    model = _Model(view())
    with pytest.raises(thesis_view.ThesisViewError, match="no claim"):
        _ask(model, readings=readings)
    assert model.asked == []


class _ModelRefused(Exception):
    """A stand-in for the model module's own error, which lands in its own
    commit: what is held here is that `ask` raises it as it comes and asks
    nothing a second time."""


def test_the_models_refusal_is_raised_after_one_request():
    model = _Model(error=_ModelRefused("the model stopped on 'max_tokens'"))
    with pytest.raises(_ModelRefused, match="max_tokens"):
        _ask(model)
    assert len(model.asked) == 1


def test_nothing_is_written(monkeypatch):
    import builtins
    opened = []
    real = builtins.open
    monkeypatch.setattr(builtins, "open", lambda *a, **k: opened.append(a) or real(*a, **k))
    _ask(_Model(view()))
    assert opened == []
