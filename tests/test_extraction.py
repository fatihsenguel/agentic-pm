"""
Deterministic extraction of tickers, periods and percentages from the
message, before any model sees it (docs/DIRECTION.md: extraction becomes the
tools' input validation).

The table carries every golden query, every benchmark prompt and the CLI
prompts KNOWN_GAPS records, each with the extraction it must produce, so a
rule change that moves any of them fails here before it costs a run. The
period vocabulary is passed in from config's keys, never restated.

No LLM, no database. Held tickers are portfolio 3's nine for the pid-3
prompts, portfolio 1's three and portfolio 2's two for the others, as the
golden set runs them.
"""

import pytest

from agents.extraction import extract


PERIODS = ("1Y", "2Y", "3Y", "5Y", "10Y")
P1 = ("SPY", "TLT", "GLD")
P2 = ("AAPL", "MSFT")
P3 = ("SPY", "AAPL", "MSFT", "JNJ", "JPM", "NEE", "TLT", "GLD", "VNQ")
NONE = ()

# message, held, tickers, period, max_volatility, hypothetical_weight
CLEAN = [
    # golden set
    ("What is the current market regime?", NONE, [], None, None, None),
    ("Get me the last 1 year of prices for SPY and TLT", NONE, ["SPY", "TLT"], "1Y", None, None),
    ("Optimize a portfolio of SPY, TLT and GLD for maximum Sharpe ratio", NONE, ["SPY", "TLT", "GLD"], None, None, None),
    ("What is my current allocation by asset class?", P1, [], None, None, None),
    ("What is my volatility over the past twelve months?", P1, [], "1Y", None, None),
    ("Should I rebalance my portfolio?", P1, [], None, None, None),
    ("What is the risk of my portfolio?", P1, [], None, None, None),
    ("What positions do I hold in the Technology sector?", P2, [], None, None, None),
    ("Analyze ZZZZFAKE for me", NONE, [], None, None, None),
    ("help", NONE, [], None, None, None),
    ("Should I buy Nvidia?", P1, [], None, None, None),
    ("How much did AAPL gain today?", P3, ["AAPL"], None, None, None),
    ("Is my AAPL position too big?", P3, ["AAPL"], None, None, None),
    ("Is my AAPL position within my policy's limits?", P3, ["AAPL"], None, None, None),
    ("Is AAPL too concentrated?", P3, ["AAPL"], None, None, None),
    # benchmark cases
    ("How has my JPM position performed since I bought it?", P3, ["JPM"], None, None, None),
    ("What concentration risk do I have, and is it compatible with my investment policy?", P3, [], None, None, None),
    ("Does my current allocation violate any rule of my investment policy?", P3, [], None, None, None),
    ("What would have to change for me to be within the limits again?", P3, [], None, None, None),
    ("I want to put 15% into a single position, is that allowed?", P3, [], None, None, 0.15),
    ("How is my position doing today?", P3, [], None, None, None),
    ("What does my investment policy say about currency risk?", P3, [], None, None, None),
    # CLI prompts from KNOWN_GAPS
    ("Is my JNJ position over any limit?", P3, ["JNJ"], None, None, None),
    ("What's my biggest position?", P3, [], None, None, None),
    ("What share of my portfolio is technology?", P3, [], None, None, None),
    ("Could I put 11% into a new stock?", P3, [], None, None, 0.11),
    ("Could I put 11% into a new ETF?", P3, [], None, None, 0.11),
    # prompt few-shots and vocabulary edges
    ("Erstelle ein risiko-optimiertes Portfolio mit SPY, TLT, GLD, VWO", NONE, ["SPY", "TLT", "GLD", "VWO"], None, None, None),
    ("Optimize SPY and TLT with max 12% volatility", NONE, ["SPY", "TLT"], None, 0.12, None),
    ("Keep vol under 15 % over 2 years", P1, [], "2Y", 0.15, None),
    ("What is the VIX doing?", NONE, [], None, None, None),
    ("Backtest over the past 10 years", P1, [], "10Y", None, None),
    ("three years of prices for GLD", NONE, ["GLD"], "3Y", None, None),
    ("my returns over the last year", P3, [], "1Y", None, None),
    ("Compare SPY with SPY", NONE, ["SPY"], None, None, None),
]


@pytest.mark.parametrize("message, held, tickers, period, vol, weight", CLEAN,
                         ids=[row[0][:40] for row in CLEAN])
def test_extraction_table(message, held, tickers, period, vol, weight):
    x = extract(message, held, PERIODS)
    assert x.clarification is None, x.clarification
    assert x.tickers == tickers
    assert x.period == period
    assert x.max_volatility == vol
    assert x.hypothetical_weight == weight


# message, held, words the clarification must name
CLARIFY = [
    ("Hows my APPL doing?", P3, ["APPL", "AAPL"]),                 # benchmark 3.5
    ("Is MSTF too big?", P3, ["MSTF", "MSFT"]),                     # a transposition
    ("How has my portfolio done over the last month?", P3, ["last month", "1Y", "10Y"]),
    ("Show me 6 months of prices for SPY", NONE, ["6 months", "1Y"]),
    ("How have I done since 2021?", P3, ["since 2021", "1Y"]),
    ("Volatility over 4 years", P1, ["4 years", "5Y"]),
    ("Prices for the last week", P1, ["last week"]),
    ("Put 15% into AAPL and 20% into MSFT", P3, ["15%", "20%"]),
    ("Put 150% into one stock", P3, ["150%"]),
    ("Over 1 year and 3 years", P1, ["1 year", "3 years"]),
]


@pytest.mark.parametrize("message, held, names", CLARIFY, ids=[row[0][:40] for row in CLARIFY])
def test_extraction_clarifies_instead_of_repairing(message, held, names):
    x = extract(message, held, PERIODS)
    assert x.clarification is not None
    for name in names:
        assert name in x.clarification, (name, x.clarification)


def test_single_letters_and_abbreviations_are_not_tickers():
    x = extract("I want a P&L for my ETF and my IPS", P3, PERIODS)
    assert x.tickers == [] and x.clarification is None


def test_unknown_ticker_needs_a_holding_within_one_edit():
    """No stoplist: an all-caps word that is not one edit from a holding is
    not a ticker candidate and reaches the model as it does today."""
    assert extract("Analyze ZZZZ for me", P3, PERIODS).clarification is None
    assert extract("Hows my APPL doing?", NONE, PERIODS).clarification is None


def test_period_vocabulary_is_the_callers():
    """Years the caller's vocabulary lacks clarify; nothing here knows the list."""
    x = extract("over 2 years", P1, ("1Y", "3Y"))
    assert x.period is None and "2 years" in x.clarification and "3Y" in x.clarification
    assert extract("over 2 years", P1, ("1Y", "2Y")).period == "2Y"


def test_message_and_held_are_untouched():
    held = ["AAPL"]
    extract("Is my AAPL position too big?", held, PERIODS)
    assert held == ["AAPL"]


# --- the compliance mode: does the message ask what the policy itself says? ---

LOOKUP = [
    "What does my investment policy say about currency risk?",        # benchmark 3.4
    "What does my policy say about borrowing against the account?",   # the prompt's example
    "Does my IPS cover margin loans?",
    "Is there anything in my policy about cash?",
    "What does the Investment Policy Statement require on rebalancing?",
    "Does my policy prohibit options?",
]

CHECK = [
    "What concentration risk do I have, and is it compatible with my investment policy?",  # 2.1
    "Does my current allocation violate any rule of my investment policy?",                  # 2.2
    "What would have to change for me to be within the limits again?",                       # 2.3
    "I want to put 15% into a single position, is that allowed?",                             # 3.1
    "Is my AAPL position too big?",
    "Is my AAPL position within my policy's limits?",
    "Is AAPL too concentrated?",
    "Is my JNJ position over any limit?",
    "What are my policy's rules on cash?",   # a lookup without a saying verb: the check, the honest miss
]


@pytest.mark.parametrize("message", LOOKUP, ids=[m[:40] for m in LOOKUP])
def test_a_question_about_what_the_policy_says_is_a_lookup(message):
    assert extract(message, P3, PERIODS).policy_lookup is True


@pytest.mark.parametrize("message", CHECK, ids=[m[:40] for m in CHECK])
def test_a_question_about_the_portfolio_is_not_a_lookup(message):
    """Naming the policy is not asking what it says. The pattern's miss is
    a lookup phrased without a saying verb, which runs the fuller check;
    the model's flag missed the other way, into "the policy contains
    nothing on this" (the shrink's golden diff, 8 September)."""
    assert extract(message, P3, PERIODS).policy_lookup is False

