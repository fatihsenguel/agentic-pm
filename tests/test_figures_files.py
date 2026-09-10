"""
figures/<TICKER>.toml held to Part 10 A and to the block's shape.

A figures file is the synthetic stand-in for what the filings reader will
one day publish: one company's reported figures per fiscal year with their
end and filed dates, the shares, the price and the valuation range with
their as-of dates, and a source line saying where every figure came from.
Synthetic, the way the philosophy and the watchlist are, and replaced by the
reader's output with no change to the screen or the node.

figures/GOOGL.toml IS Part 10 A, so that case 4.1 reproduces Part 10 D end
to end; test_screening.py's fixture types the same block by hand, and this
test holds the file to it. Every candidate on the watchlist has a file.
"""

import datetime as dt
from pathlib import Path

import pytest
import tomli

from test_fundamentals import figures as reference_block


ROOT = Path(__file__).parent.parent
FIGURES = ROOT / "figures"
BLOCK_KEYS = {"ticker", "currency", "source", "shares_outstanding", "price", "valuation_range", "years"}
DATED = {"price": {"value", "as_of"}, "valuation_range": {"low", "high", "as_of"}}


@pytest.fixture(scope="module")
def loader():
    from portfolio_tool import figures
    return figures


def _watchlist_tickers():
    with open(ROOT / "watchlist.toml", "rb") as f:
        return [c["ticker"] for c in tomli.load(f)["candidate"]]


def test_every_watchlist_candidate_has_a_figures_file():
    for ticker in _watchlist_tickers():
        assert (FIGURES / f"{ticker}.toml").exists(), ticker


@pytest.mark.parametrize("ticker", ["GOOGL", "ADBE"])
def test_the_block_shape(loader, ticker):
    block = loader.load_figures(ticker)
    assert set(block) == BLOCK_KEYS
    assert block["ticker"] == ticker
    for key, fields in DATED.items():
        assert set(block[key]) == fields, key
        dt.date.fromisoformat(block[key]["as_of"])
    for label, year in block["years"].items():
        assert label.startswith("FY"), label
        dt.date.fromisoformat(year["ends"])
        dt.date.fromisoformat(year["filed"])
        for k, v in year.items():
            if k not in ("ends", "filed"):
                assert isinstance(v, (int, float)) and not isinstance(v, bool), (label, k)


def test_googl_is_part_10_a(loader):
    """The file and test_fundamentals.py's typed block are two statements of
    Part 10 A; they must agree cell for cell."""
    file, typed = loader.load_figures("GOOGL"), reference_block()
    assert "Part 10" in file["source"] and "Part 10" in typed["source"]
    del file["source"], typed["source"]   # each names its own provenance
    assert file == typed


def test_the_source_says_synthetic(loader):
    for ticker in ("GOOGL", "ADBE"):
        assert "synthetic" in loader.load_figures(ticker)["source"].lower(), ticker


def test_unknown_ticker_raises(loader):
    with pytest.raises(loader.FiguresError, match="no figures file"):
        loader.load_figures("ZZZZFAKE")


def test_a_relative_directory_is_anchored_to_the_project_root(loader, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert loader.load_figures("GOOGL")["ticker"] == "GOOGL"


def test_a_ticker_that_is_not_a_symbol_raises(loader):
    with pytest.raises(loader.FiguresError, match="not a ticker"):
        loader.load_figures("../philosophy")


def test_dates_come_back_as_strings_not_toml_dates(loader):
    """The block is a summary that crosses shared_data as JSON; a date is a
    string in it, the way as_of is everywhere else."""
    block = loader.load_figures("GOOGL")
    assert isinstance(block["price"]["as_of"], str)
    assert all(isinstance(y["filed"], str) for y in block["years"].values())
