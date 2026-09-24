"""
The eleven tools' input models (KNOWN_GAPS, "The eleven tool contracts of
Order 5, on paper"): each validates what the model passes a tool, raises on
what it cannot answer, repairs nothing, and carries no default for anything
the user must state (DIRECTION.md invariant 5). A raise ends the turn and is
shown unchanged, so the model cannot re-call with a guessed value.

Pure: the held tickers, the period vocabulary and the watchlist's tickers
are passed in, as extraction takes them, and nothing here reads a file or
the database. Each model is also the tool's strict JSON schema: every
property required, none beyond them.
"""

import importlib

import pytest


@pytest.fixture
def ti():
    return importlib.import_module("agents.tool_inputs")


@pytest.fixture
def context(ti):
    return ti.ToolContext(
        held=("SPY", "AAPL", "MSFT", "JNJ", "JPM", "NEE", "TLT", "GLD", "VNQ"),
        periods=("1Y", "2Y", "3Y", "5Y", "10Y"),
        watchlist=("GOOGL", "ADBE"),
    )


ELEVEN = {"allocation", "position_pnl", "portfolio_volatility", "compliance_check",
          "hypothetical_weight", "policy_lookup", "philosophy_screen", "thesis", "position",
          "rebalance", "ledger"}


def test_the_eleven_tools_and_no_other(ti, context):
    assert set(ti.TOOLS) == ELEVEN


@pytest.mark.parametrize("tool", sorted(ELEVEN))
def test_every_schema_is_strict(tool, ti, context):
    schema = ti.tool_schema(tool)
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema.get("required", [])) == set(schema.get("properties", {}))


@pytest.mark.parametrize("tool", ["allocation", "compliance_check", "rebalance", "ledger"])
def test_a_tool_that_takes_nothing_takes_nothing(tool, ti, context):
    assert ti.validate_inputs(tool, {}, context) == {}
    with pytest.raises(ti.ToolInputError, match="tickers"):
        ti.validate_inputs(tool, {"tickers": ["AAPL"]}, context)


def test_an_unknown_tool_is_refused(ti, context):
    with pytest.raises(ti.ToolInputError, match="no tool"):
        ti.validate_inputs("risk_analysis", {}, context)


# --- position_pnl ------------------------------------------------------------

def test_pnl_takes_held_tickers_or_none(ti, context):
    assert ti.validate_inputs("position_pnl", {"tickers": ["JPM"]}, context) == {"tickers": ["JPM"]}
    assert ti.validate_inputs("position_pnl", {"tickers": []}, context) == {"tickers": []}


@pytest.mark.parametrize("tickers", [["NVDA"], ["jpm"], ["JMP"], ["JPM", "JPM"]])
def test_pnl_refuses_a_ticker_it_would_have_to_repair(tickers, ti, context):
    """Not held, lower case, a typo, a repeat: each is refused naming what
    was passed, never corrected to the nearest holding."""
    with pytest.raises(ti.ToolInputError) as raised:
        ti.validate_inputs("position_pnl", {"tickers": tickers}, context)
    assert tickers[0] in str(raised.value)


# --- portfolio_volatility ----------------------------------------------------

def test_volatility_takes_a_span_of_the_vocabulary_or_none(ti, context):
    assert ti.validate_inputs("portfolio_volatility", {"period": "1Y"}, context) == {"period": "1Y"}
    assert ti.validate_inputs("portfolio_volatility", {"period": None}, context) == {"period": None}


@pytest.mark.parametrize("period", ["6M", "1y", "4Y", "last year"])
def test_volatility_refuses_a_span_the_vocabulary_lacks_naming_the_spans(period, ti, context):
    with pytest.raises(ti.ToolInputError) as raised:
        ti.validate_inputs("portfolio_volatility", {"period": period}, context)
    assert period in str(raised.value) and "10Y" in str(raised.value)


def test_volatility_must_be_told_the_span_or_told_none(ti, context):
    with pytest.raises(ti.ToolInputError, match="period"):
        ti.validate_inputs("portfolio_volatility", {}, context)


# --- hypothetical_weight (decision 12) ---------------------------------------

@pytest.mark.parametrize("kind", ["share", "fund"])
def test_a_weight_and_its_type(kind, ti, context):
    assert ti.validate_inputs("hypothetical_weight", {"weight": 0.15, "instrument_type": kind},
                              context) == {"weight": 0.15, "instrument_type": kind}


@pytest.mark.parametrize("inputs, named", [
    ({"weight": 0.15}, "instrument_type"),
    ({"weight": 0.15, "instrument_type": "etf"}, "etf"),
    ({"weight": 0.15, "instrument_type": None}, "instrument_type"),
    ({"weight": 0, "instrument_type": "share"}, "weight"),
    ({"weight": 15, "instrument_type": "share"}, "weight"),
    ({"weight": 1.5, "instrument_type": "share"}, "weight"),
    ({"instrument_type": "share"}, "weight"),
])
def test_a_weight_is_refused_without_its_type_or_outside_a_share_of_the_portfolio(
        inputs, named, ti, context):
    with pytest.raises(ti.ToolInputError, match=named):
        ti.validate_inputs("hypothetical_weight", inputs, context)


def test_a_whole_portfolio_is_a_weight(ti, context):
    assert ti.validate_inputs("hypothetical_weight", {"weight": 1.0, "instrument_type": "fund"},
                              context)["weight"] == 1.0


# --- policy_lookup -----------------------------------------------------------

def test_a_lookup_takes_the_words_it_was_given(ti, context):
    assert ti.validate_inputs("policy_lookup", {"topic": "currency risk"}, context) == \
        {"topic": "currency risk"}


@pytest.mark.parametrize("topic", ["", "   ", None])
def test_a_lookup_with_no_words_is_refused(topic, ti, context):
    with pytest.raises(ti.ToolInputError, match="topic"):
        ti.validate_inputs("policy_lookup", {"topic": topic}, context)


# --- the three research tools ------------------------------------------------

def test_a_screen_takes_one_ticker(ti, context):
    assert ti.validate_inputs("philosophy_screen", {"ticker": "JPM"}, context) == {"ticker": "JPM"}


@pytest.mark.parametrize("inputs", [{"ticker": ["JPM", "GOOGL"]}, {"ticker": ""}, {"ticker": "jpm"}, {}])
def test_a_screen_refuses_anything_but_one_ticker(inputs, ti, context):
    with pytest.raises(ti.ToolInputError, match="ticker"):
        ti.validate_inputs("philosophy_screen", inputs, context)


@pytest.mark.parametrize("tool", ["thesis", "position"])
def test_a_thesis_or_a_position_takes_a_watchlist_ticker(tool, ti, context):
    assert ti.validate_inputs(tool, {"ticker": "GOOGL"}, context) == {"ticker": "GOOGL"}


@pytest.mark.parametrize("tool", ["thesis", "position"])
def test_a_company_on_no_entry_is_refused_naming_the_watchlist(tool, ti, context):
    """R-7: a candidate reaches the watchlist because I put it there."""
    with pytest.raises(ti.ToolInputError) as raised:
        ti.validate_inputs(tool, {"ticker": "NVDA"}, context)
    assert "NVDA" in str(raised.value) and "watchlist" in str(raised.value)


def test_a_position_takes_no_weight_from_the_model(ti, context):
    """Decision 65: the weight is the entry's, never the message's."""
    with pytest.raises(ti.ToolInputError, match="weight"):
        ti.validate_inputs("position", {"ticker": "GOOGL", "weight": 0.06}, context)
