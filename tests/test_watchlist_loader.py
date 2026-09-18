"""
The watchlist loader held to its raises, the way test_philosophy_loader.py
holds the philosophy loader. The file-to-document tests are in
test_watchlist.py.

What the loader reads (Part 11 D38): each candidate's id, ticker, name,
currency and status, and its valuation table, the growth I assume for it
as a low and a high; since case 4.5 the prediction rows too, held in
test_watchlist_predictions_loader.py. What it leaves alone: the thesis,
the entry condition and added_on, read by nothing. What it refuses: a
missing file with no default, a top-level key nothing reads, a candidate
lacking a field, two candidates with one id or one ticker, a valuation
table that is not exactly the two ends as fractions. The order of the two
ends is the range's rule, not the loader's: quant/valuation.py raises on
a reversed or equal pair, one place for that rule.

`growth_pair` is what the node asks for: the two assumptions as the range
reads them, each with the entry's id as its source. A candidate that
states none stops with both names named, never a default, and a ticker
not on the list is not a candidate.

The module is imported inside a fixture so that, before it exists, this
file is a list of errors and not an interrupted suite.
"""

from pathlib import Path

import pytest


ROOT = Path(__file__).parent.parent

W1 = '''
[[candidate]]
id = "W-1"
ticker = "GOOGL"
name = "Alphabet"
currency = "USD"
added_on = 2026-09-10
status = "active"
thesis = "A thesis."

[candidate.entry_condition]
kind = "valuation"
clause = "PHI-4.1"

[candidate.valuation]
growth_low = 0.06
growth_high = 0.12

[[candidate.prediction]]
id = "W-1.1"
made_on = 2026-09-10
due = 2027-03-01
kind = "event"
statement = "Something about the business."
'''

W2 = '''
[[candidate]]
id = "W-2"
ticker = "ADBE"
name = "Adobe"
currency = "USD"
added_on = 2026-09-10
status = "active"
thesis = "Another thesis."

[candidate.entry_condition]
kind = "valuation"
clause = "PHI-4.1"
'''


@pytest.fixture
def watchlist():
    from portfolio_tool import watchlist
    return watchlist


@pytest.fixture
def load(watchlist, tmp_path):
    def _load(text, name="watchlist.toml"):
        path = tmp_path / name
        path.write_text(text)
        return watchlist.load_watchlist(str(path))
    return _load


# --- the committed file ------------------------------------------------------

def test_the_committed_file_loads_with_its_two_candidates(watchlist):
    wl = watchlist.load_watchlist("watchlist.toml")
    assert list(wl.candidates) == ["W-1", "W-2"]
    assert wl.path == str(ROOT / "watchlist.toml")
    w1, w2 = wl.candidates["W-1"], wl.candidates["W-2"]
    assert (w1.ticker, w1.name, w1.currency, w1.status) == ("GOOGL", "Alphabet", "USD", "active")
    assert w1.growth == {"growth_low": 0.06, "growth_high": 0.12}
    assert w2.ticker == "ADBE"
    assert w2.growth is None


def test_by_ticker_finds_a_candidate_and_refuses_a_stranger(watchlist):
    wl = watchlist.load_watchlist("watchlist.toml")
    assert wl.by_ticker("GOOGL").id == "W-1"
    with pytest.raises(watchlist.WatchlistError, match="AAPL is not on the watchlist"):
        wl.by_ticker("AAPL")


# --- growth_pair --------------------------------------------------------------

def test_growth_pair_carries_both_ends_with_the_entry_as_source(watchlist):
    wl = watchlist.load_watchlist("watchlist.toml")
    assert watchlist.growth_pair(wl, "GOOGL") == {
        "growth_low": {"value": 0.06, "source": "W-1"},
        "growth_high": {"value": 0.12, "source": "W-1"},
    }


def test_a_candidate_stating_no_pair_stops_naming_both_ends(watchlist):
    wl = watchlist.load_watchlist("watchlist.toml")
    with pytest.raises(watchlist.WatchlistError,
                       match=r"W-2 \(ADBE\) states no growth_low and growth_high"):
        watchlist.growth_pair(wl, "ADBE")


def test_a_ticker_not_on_the_list_has_no_pair(watchlist):
    wl = watchlist.load_watchlist("watchlist.toml")
    with pytest.raises(watchlist.WatchlistError, match="JPM is not on the watchlist"):
        watchlist.growth_pair(wl, "JPM")


# --- what the loader refuses --------------------------------------------------

def test_no_file_no_default(watchlist):
    with pytest.raises(watchlist.WatchlistError, match="no default watchlist"):
        watchlist.load_watchlist("no/such/watchlist.toml")


def test_a_relative_path_is_anchored_to_the_project_root(watchlist, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert watchlist.load_watchlist("watchlist.toml").path == str(ROOT / "watchlist.toml")


def test_a_top_level_key_nothing_reads_is_refused(load, watchlist):
    with pytest.raises(watchlist.WatchlistError, match=r"top-level keys nothing reads: \['notes'\]"):
        load(W1 + '\n[notes]\nx = 1\n')


def test_no_candidates_is_refused(load, watchlist):
    with pytest.raises(watchlist.WatchlistError, match=r"no \[\[candidate\]\] entries"):
        load('# empty\n')


@pytest.mark.parametrize("field", ["id", "ticker", "name", "currency", "status"])
def test_a_candidate_lacking_a_field_is_refused_naming_it(load, watchlist, field):
    text = "\n".join(line for line in W1.splitlines() if not line.startswith(f"{field} = "))
    with pytest.raises(watchlist.WatchlistError, match=rf"lacks \['{field}'\]"):
        load(text)


def test_an_id_off_form_is_refused(load, watchlist):
    with pytest.raises(watchlist.WatchlistError, match="W-<number>"):
        load(W1.replace('id = "W-1"', 'id = "C-1"'))


def test_a_status_outside_the_vocabulary_is_refused(load, watchlist):
    with pytest.raises(watchlist.WatchlistError, match="status 'watching' is not active or closed"):
        load(W1.replace('status = "active"', 'status = "watching"'))


def test_two_candidates_with_one_id_are_refused(load, watchlist):
    with pytest.raises(watchlist.WatchlistError, match="W-1 appears twice"):
        load(W1 + W2.replace('id = "W-2"', 'id = "W-1"'))


def test_two_candidates_with_one_ticker_are_refused(load, watchlist):
    with pytest.raises(watchlist.WatchlistError, match="GOOGL is listed twice"):
        load(W1 + W2.replace('ticker = "ADBE"', 'ticker = "GOOGL"'))


def test_one_end_alone_is_refused(load, watchlist):
    with pytest.raises(watchlist.WatchlistError,
                       match=r"W-1: valuation states \['growth_low'\]; a growth pair is "
                             r"growth_low and growth_high, both or neither"):
        load(W1.replace("growth_high = 0.12\n", ""))


def test_a_key_the_range_does_not_read_is_refused(load, watchlist):
    with pytest.raises(watchlist.WatchlistError, match=r"valuation does not take \['method'\]"):
        load(W1.replace("growth_high = 0.12\n", 'growth_high = 0.12\nmethod = "dcf"\n'))


@pytest.mark.parametrize("value", ['"0.12"', "true", "12", "-1.5"])
def test_an_end_that_is_not_a_fraction_is_refused(load, watchlist, value):
    with pytest.raises(watchlist.WatchlistError,
                       match=r"growth_high = .* is not a fraction; 12% is written 0.12"):
        load(W1.replace("growth_high = 0.12", f"growth_high = {value}"))


def test_the_order_of_the_ends_is_the_ranges_rule_not_the_loaders(load):
    """A reversed pair loads; quant/valuation.py raises on it, naming both,
    so that the rule lives once (Part 11 D40)."""
    wl = load(W1.replace("growth_low = 0.06", "growth_low = 0.20"))
    assert wl.candidates["W-1"].growth == {"growth_low": 0.20, "growth_high": 0.12}


def test_the_prediction_rows_are_read_and_the_rest_left_alone(load):
    """The scorer's rows (case 4.5, Part 14) are read since the twenty-fourth
    session, held in test_watchlist_predictions_loader.py; the thesis, the
    entry condition and added_on are still read by nothing."""
    wl = load(W1)
    assert [p.id for p in wl.candidates["W-1"].predictions] == ["W-1.1"]
    for field in ("thesis", "entry_condition", "added_on"):
        assert not hasattr(wl.candidates["W-1"], field), field
