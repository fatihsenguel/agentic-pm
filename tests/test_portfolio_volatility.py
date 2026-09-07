"""
Portfolio volatility checked against tests/golden/expected_values.md Part 4.

10.2936% on the 252 closes committed in tests/golden/benchmark_closes.csv,
extracted from expected_values.xlsx. Do NOT update that figure to match code
output. The reference window (2025-09-03 to 2026-09-02) is unreachable from a
live run, which is why this is a fixture and not a live comparison.

Two independent routes to the same number, on purpose:

  1. numpy sample covariance of simple daily returns, built here - checks the
     formula against the reference with nothing of the system's in the path.
  2. the system's own CovarianceEstimator on the same closes - checks that the
     matrix DataAgent publishes carries the conventions the reference assumes
     (simple returns, sample covariance, x252). expected_values.md says not to
     trust the system's matrix; this is the test that earns that trust.

No database is touched.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from portfolio_tool.quant.risk_metrics import (
    portfolio_volatility,
    portfolio_volatility_by_ticker,
)


CLOSES = Path(__file__).parent / "golden" / "benchmark_closes.csv"

# expected_values.md Part 1, quantities. Weights are market value at the last
# close in the fixture (2026-09-02), cash excluded (Part 4).
QUANTITIES = {
    "SPY": 100, "AAPL": 200, "MSFT": 100, "JNJ": 150, "JPM": 100,
    "NEE": 200, "TLT": 500, "GLD": 100, "VNQ": 300,
}

EXPECTED = 0.102936  # Part 4, 10.2936%
TRADING_DAYS = 252


@pytest.fixture(scope="module")
def closes():
    df = pd.read_csv(CLOSES, index_col="date", parse_dates=True)
    assert len(df) == 252, "Part 4: 252 closes"
    assert str(df.index[0].date()) == "2025-09-03"
    assert str(df.index[-1].date()) == "2026-09-02"
    return df


@pytest.fixture(scope="module")
def weights(closes):
    last = closes.iloc[-1]
    values = {t: q * last[t] for t, q in QUANTITIES.items()}
    invested = sum(values.values())
    return {t: v / invested for t, v in values.items()}


def test_part_4_from_numpy_sample_covariance(closes, weights):
    returns = closes.pct_change().dropna()
    assert len(returns) == 251, "Part 4: 251 daily returns"
    cov = returns.cov(ddof=1) * TRADING_DAYS
    vol = portfolio_volatility_by_ticker(
        weights, {t: cov.loc[t].to_dict() for t in cov.index}
    )
    assert vol == pytest.approx(EXPECTED, abs=5e-7)


def test_part_4_from_the_system_estimator(closes, weights):
    from portfolio_tool.quant.covariance import CovarianceEstimator, CovarianceMethod

    returns = closes.pct_change().dropna()
    result = CovarianceEstimator(
        method=CovarianceMethod.SAMPLE, annualize=True, min_observations=1
    ).estimate(returns)
    assert result.success, result.error_message
    cov = result.to_dict()["covariance_matrix"]
    vol = portfolio_volatility_by_ticker(weights, cov)
    assert vol == pytest.approx(EXPECTED, abs=5e-7)


def test_part_4_is_not_the_weighted_average(closes, weights):
    """Part 4's sanity check: weighted average of single-name vols is 20.54%,
    roughly double the portfolio figure. A function returning the average
    would pass a loose test; this one refuses it."""
    returns = closes.pct_change().dropna()
    vols = returns.std(ddof=1) * np.sqrt(TRADING_DAYS)
    weighted_average = sum(weights[t] * vols[t] for t in weights)
    assert weighted_average == pytest.approx(0.205408, abs=5e-7)
    cov = returns.cov(ddof=1) * TRADING_DAYS
    vol = portfolio_volatility_by_ticker(weights, {t: cov.loc[t].to_dict() for t in cov.index})
    assert vol < weighted_average / 1.5


def test_weights_must_sum_to_one():
    cov = np.eye(2) * 0.04
    with pytest.raises(ValueError):
        portfolio_volatility(np.array([0.5, 0.4]), cov)


def test_shape_mismatch_raises():
    with pytest.raises(ValueError):
        portfolio_volatility(np.array([0.5, 0.5]), np.eye(3))


def test_missing_covariance_row_raises():
    with pytest.raises(ValueError):
        portfolio_volatility_by_ticker(
            {"A": 0.5, "B": 0.5}, {"A": {"A": 0.04, "B": 0.0}}
        )


def test_unweighted_covariance_row_raises():
    with pytest.raises(ValueError):
        portfolio_volatility_by_ticker(
            {"A": 1.0}, {"A": {"A": 0.04, "B": 0.0}, "B": {"A": 0.0, "B": 0.04}}
        )


def test_two_uncorrelated_assets():
    """Hand check: two assets at 20% vol, uncorrelated, equal weight ->
    sqrt(0.5^2 * 0.04 * 2) = 14.14%."""
    cov = np.array([[0.04, 0.0], [0.0, 0.04]])
    assert portfolio_volatility(np.array([0.5, 0.5]), cov) == pytest.approx(0.1414214, abs=1e-6)
