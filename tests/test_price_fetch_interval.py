"""
price_fetch_interval_days is policy and lives in config.toml, not in code.

The price cache skips the provider when it has asked this far back before
and checked within the interval; the rate fetch runs under the same rule.
The interval is a number somebody could set differently, so it belongs in
config.toml beside the earnings, profile and shares intervals, and nowhere
else: not as a code default the reader falls back to when the key is
missing, and not in a hardcoded table used when the file itself is
missing. A missing key raises; a missing file raises.
"""

import datetime
import pathlib

import pytest
import tomli

from portfolio_tool.data_manager import DataManager, load_config


CONFIG = pathlib.Path(__file__).parent.parent / "config.toml"


def test_config_toml_carries_the_price_fetch_interval():
    data_fetch = tomli.load(CONFIG.open("rb"))["data_fetch"]
    assert "price_fetch_interval_days" in data_fetch
    assert isinstance(data_fetch["price_fetch_interval_days"], int)


class _NeverCalled:
    name = "never"

    def get_daily_prices(self, ticker, start, end):
        raise AssertionError("the provider must not be reached")


class _Asset:
    id = -1
    ticker = "ZZINTERVAL"


def test_a_config_without_the_key_raises_rather_than_fetching_daily(monkeypatch):
    import portfolio_tool.data_manager as module
    monkeypatch.setattr(module, "CONFIG", {"data_fetch": {"earnings_fetch_interval_days": 7}})
    dm = DataManager(session=_FakeSession(), provider=_NeverCalled())
    result = dm.update_prices_for_asset(_Asset(), start_date=datetime.date(2026, 9, 1))
    assert result.success is False
    assert "price_fetch_interval_days" in (result.error_message or "")


def test_a_missing_config_file_raises(monkeypatch):
    monkeypatch.setattr("portfolio_tool.data_manager.CONFIG_PATH", "/nonexistent/config.toml")
    with pytest.raises(FileNotFoundError):
        load_config()


class _Query:
    """Enough of a session for update_prices_for_asset to reach the
    interval: no stored rows, and a fresh metadata record."""

    def __init__(self, session):
        self.session = session

    def get(self, key):
        return None

    def filter(self, *args):
        return self

    def one(self):
        return (None, None)


class _FakeSession:
    def query(self, *args):
        return _Query(self)

    def add(self, obj):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass
