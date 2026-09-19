"""
portfolio_tool.proposer: the one prediction a model proposes for a thesis,
held to expected_values.md Part 15 F, D58, and through the frame to Part
15 C.

The model is a stand-in that records what it is asked and answers with a
fixed prediction. The block is Part 14 B's and the candidate Part 15 C's
W-1, both imported from the frame's tests so that the proposer and the
frame are held over one set of figures. The readings are built here, the
two claims of section F's message.

The rules, each a test:

  - the message is section F's, character for character, and carries
    neither the candidate's name nor its id nor its predictions
  - the request is the fixed prompt, the schema and the message, once
  - the schema offers the metrics the frame writes and the bounds it
    reads, and each shape the keys the frame accepts
  - S-1 and S-2 frame to P-1 and P-4 under W-1.3
  - S-3, S-5 and S-6 are refused; S-7's refusal is raised as it comes,
    after one request
  - no thesis and no claims refuse before any request
  - nothing is written
"""

import datetime as dt

import pytest

from portfolio_tool import proposals
from portfolio_tool.reading import Claim, Reading

from test_predictions import block
from test_proposals import AS_OF, candidate

THESIS = "The business sells subscriptions customers keep renewing."
MESSAGE = """Thesis:
The business sells subscriptions customers keep renewing.

Claims:
[1.1] (stated) The business is subscription software that customers keep renewing.
Quote: "Customers renew because their work lives in the files."
[7.2] (inferred) Renewals and subscription revenue are described together.
Quote: "lives in the files. Revenue from subscriptions\""""


def _reading(section, *claims):
    return Reading(form="10-K", accn="0001652044-26-000018", filed=dt.date(2026, 2, 5),
                   fiscal_year="FY2025", source="EDGAR filing archive", section=section,
                   claims=claims)


READINGS = (
    _reading("Item 1", Claim(id="1.1", claim="The business is subscription software that "
                             "customers keep renewing.",
                             quote="Customers renew because their work lives in the files.",
                             uncertainty="stated")),
    _reading("Item 7", Claim(id="7.2", claim="Renewals and subscription revenue are "
                             "described together.",
                             quote="lives in the files. Revenue from subscriptions",
                             uncertainty="inferred")),
)


class _Model:
    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error
        self.asked = []

    def propose(self, prompt, schema, text):
        self.asked.append((prompt, schema, text))
        if self.error is not None:
            raise self.error
        return self.answer


def figure(metric="gross_margin", bound="min", reasons=("1.1",), **extra):
    return {"kind": "figure", "metric": metric, "bound": bound, "reasons": list(reasons),
            **extra}


EVENT = {"kind": "event",
         "event": "the cloud segment profitable at the operating level for the full year",
         "reasons": ["7.2"]}


@pytest.fixture
def proposer():
    from portfolio_tool import proposer
    return proposer


def _propose(proposer, model, thesis=THESIS, readings=READINGS):
    return proposer.propose(model, candidate(), thesis, readings, block(), AS_OF)


# --- the request ---------------------------------------------------------------------

def test_the_message_is_the_references(proposer):
    assert proposer.message(THESIS, READINGS) == MESSAGE


def test_the_thesis_is_sent_without_the_whitespace_at_its_ends(proposer):
    assert proposer.message(f"\n{THESIS}\n", READINGS) == MESSAGE


def test_the_message_names_no_candidate_and_no_prediction(proposer):
    text = proposer.message(THESIS, READINGS)
    cand = candidate()
    assert cand.name not in text and cand.id not in text and cand.ticker not in text
    for p in cand.predictions:
        assert p.statement not in text


def test_the_request_is_the_prompt_the_schema_and_the_message_once(proposer):
    model = _Model(figure())
    _propose(proposer, model)
    assert model.asked == [(proposer.PROMPT, proposer.SCHEMA, MESSAGE)]


def test_the_schema_offers_what_the_frame_writes(proposer):
    shapes = proposer.SCHEMA["properties"]["prediction"]["anyOf"]
    by_kind = {s["properties"]["kind"]["enum"][0]: s for s in shapes}
    assert set(by_kind) == set(proposals.KINDS) and len(shapes) == 2
    for kind, shape in by_kind.items():
        assert set(shape["properties"]) == proposals.SUPPLIED[kind]
        assert set(shape["required"]) == proposals.SUPPLIED[kind]
        assert shape["additionalProperties"] is False
    assert by_kind["figure"]["properties"]["metric"]["enum"] == ["revenue", "gross_margin"]
    assert by_kind["figure"]["properties"]["metric"]["enum"] == list(proposals.WRITTEN)
    assert by_kind["figure"]["properties"]["bound"]["enum"] == ["min", "max"]
    assert proposer.SCHEMA["required"] == ["prediction"]
    assert proposer.SCHEMA["additionalProperties"] is False


def test_the_prompt_names_the_offered_metrics(proposer):
    assert "revenue, gross_margin" in proposer.PROMPT


# --- the rows of section F -----------------------------------------------------------

def test_s_1_a_figure_frames_to_p_1(proposer):
    p = _propose(proposer, _Model(figure()))
    assert (p.id, p.kind, p.metric, p.bound, p.value, p.period) == (
        "W-1.3", "figure", "gross_margin", "min", 0.5965, "FY2026")
    assert p.statement == ("By 18 September 2027 Alphabet will have reported a gross margin "
                           "for fiscal 2026 of at least 59.65%.")
    assert p.reasons == ("1.1",) and (p.author, p.status) == ("system", "proposed")


def test_s_2_an_event_frames_to_p_4(proposer):
    p = _propose(proposer, _Model(EVENT))
    assert (p.id, p.kind, p.value) == ("W-1.3", "event", None)
    assert p.statement == ("By 18 September 2027 Alphabet's annual report for fiscal 2026 will "
                           "show the cloud segment profitable at the operating level for the "
                           "full year.")
    assert p.reasons == ("7.2",)


def test_s_3_a_metric_not_offered_is_refused(proposer):
    with pytest.raises(proposals.ProposalError, match="return_on_invested_capital.*not one "
                                                      "offered"):
        _propose(proposer, _Model(figure(metric="return_on_invested_capital")))


def test_s_5_a_value_from_the_model_is_refused(proposer):
    with pytest.raises(proposals.ProposalError, match="value"):
        _propose(proposer, _Model(figure(metric="revenue", value=420)))


def test_s_6_a_reason_that_is_no_claim_is_refused(proposer):
    with pytest.raises(proposals.ProposalError, match="1.9"):
        _propose(proposer, _Model(figure(metric="revenue", reasons=("1.9",))))


def test_s_7_the_models_refusal_is_raised_after_one_request(proposer):
    from agents.proposal_model import ProposalModelError
    model = _Model(error=ProposalModelError("the model stopped on 'max_tokens'"))
    with pytest.raises(ProposalModelError, match="max_tokens"):
        _propose(proposer, model)
    assert len(model.asked) == 1


# --- what is refused before the request ----------------------------------------------

@pytest.mark.parametrize("thesis", ["", "   ", None])
def test_no_thesis_refuses_before_any_request(proposer, thesis):
    model = _Model(figure())
    with pytest.raises(proposals.ProposalError, match="no thesis"):
        _propose(proposer, model, thesis=thesis)
    assert model.asked == []


@pytest.mark.parametrize("readings", [(), (_reading("Item 1"),)], ids=["none", "no claims"])
def test_no_claim_refuses_before_any_request(proposer, readings):
    model = _Model(figure())
    with pytest.raises(proposals.ProposalError, match="no claim"):
        _propose(proposer, model, readings=readings)
    assert model.asked == []


def test_nothing_is_written(proposer, monkeypatch):
    import builtins
    opened = []
    real = builtins.open
    monkeypatch.setattr(builtins, "open", lambda *a, **k: opened.append(a) or real(*a, **k))
    _propose(proposer, _Model(figure()))
    assert opened == []
