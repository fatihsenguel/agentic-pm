"""
The general risk answer says which risk figures it did not compute.

Intent risk_analysis with no measure plans DataAgent alone, and the answer
is the annualised volatility of each holding. The intent registry describes
the intent as VaR, volatility and drawdown, and the router sends a VaR or a
drawdown question here, so without this line "what is my VaR?" is answered
with nine volatilities and nothing saying that none of them is a VaR. The
formatter cannot read the question, so the line is on every answer from this
path: what it states is what it did not compute, not what it guesses was
asked.

The covariance block is built by `CovarianceResult.to_dict`, so the shape
the formatter reads is the producer's. The price summary carries the two
keys the price tool's summary writes and the formatter reads.
"""

from agents.nodes import _format_risk_response
from portfolio_tool.quant.covariance import CovarianceResult


NOT_COMPUTED = ("Value at risk, expected shortfall and drawdown are not "
                "computed by this system")


def _answer():
    covariance = CovarianceResult(
        success=True,
        tickers=["SPY", "TLT"],
        annualized_volatilities={"SPY": 0.1500, "TLT": 0.0955},
        num_observations=252,
    ).to_dict()
    data = {
        "success": True,
        "prices": {"period": "2025-09-03 to 2026-09-02", "num_observations": 252},
        "covariance": covariance,
    }
    return "\n".join(_format_risk_response({"DataAgent": data}))


def test_the_answer_says_it_computed_no_var_shortfall_or_drawdown():
    answer = " ".join(_answer().split())
    assert NOT_COMPUTED in answer


def test_the_per_holding_volatilities_are_still_the_answer():
    answer = _answer()
    assert "15.00%" in answer
    assert "9.55%" in answer
    assert "2025-09-03 to 2026-09-02" in answer
