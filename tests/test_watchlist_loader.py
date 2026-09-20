"""
The watchlist loader held to its raises, the way test_philosophy_loader.py
holds the philosophy loader. The file-to-document tests are in
test_watchlist.py.

What the loader reads (Part 11 D38): each candidate's id, ticker, name,
currency and status, and its valuation table, the growth I assume for it
as a low and a high; since case 4.5 the prediction rows too, held in
test_watchlist_predictions_loader.py; since case 4.4 the thesis, as
written, for the research agent; and, for the gate, its asset class,
sector and instrument type (decision 63). What it leaves alone: the entry
condition and added_on, read by nothing. What it refuses: a
missing file with no default, a top-level key nothing reads, a candidate
lacking a field, two candidates with one id or one ticker, a valuation
table that is not exactly the two ends as fractions. The order of the two
ends is the range's rule, not the loader's: quant/valuation.py raises on
a reversed or equal pair, one place for that rule. The classification's
words are the IPS check's rule in the same way: any non-empty string
loads, and the check that sizes a position stops on a word it has no band
for, so that vocabulary lives where it is read and not twice.

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
asset_class = "Equity"
sector = "Communication Services"
instrument_type = "share"
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
asset_class = "Equity"
sector = "Technology"
instrument_type = "share"
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


@pytest.mark.parametrize("field", ["id", "ticker", "name", "currency", "asset_class",
                                   "sector", "instrument_type", "status", "thesis"])
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
    session, held in test_watchlist_predictions_loader.py; the entry
    condition and added_on are still read by nothing."""
    wl = load(W1)
    assert [p.id for p in wl.candidates["W-1"].predictions] == ["W-1.1"]
    for field in ("entry_condition", "added_on"):
        assert not hasattr(wl.candidates["W-1"], field), field


# --- the classification ----------------------------------------------------------

def test_the_committed_candidates_state_their_classification(watchlist):
    """Decision 63: the three the IPS check reads about the instrument
    itself, as docs/WATCHLIST.md states them and test_watchlist.py holds
    them. Alphabet's sector is Communication Services and not Technology,
    where the portfolio already sits above IPS-4.3."""
    wl = watchlist.load_watchlist("watchlist.toml")
    w1, w2 = wl.candidates["W-1"], wl.candidates["W-2"]
    assert (w1.asset_class, w1.sector, w1.instrument_type) == (
        "Equity", "Communication Services", "share")
    assert (w2.asset_class, w2.sector, w2.instrument_type) == (
        "Equity", "Technology", "share")


@pytest.mark.parametrize("field", ["asset_class", "sector", "instrument_type"])
@pytest.mark.parametrize("value", ['""', '"   "', "12"], ids=["empty", "whitespace", "a number"])
def test_a_classification_that_is_no_word_is_refused(load, watchlist, field, value):
    """A blank is not a statement. Nothing fills one with a default: the
    candidate is refused here, before the gate is asked to size it."""
    text = "\n".join(f"{field} = {value}" if line.startswith(f"{field} = ") else line
                     for line in W1.splitlines())
    with pytest.raises(watchlist.WatchlistError, match=rf"lacks \['{field}'\]"):
        load(text)


def test_a_word_the_ips_has_no_band_for_loads_here(load):
    """The vocabulary is the check's, not the loader's (D42's shape for the
    metric): a sector or an asset class the IPS does not recognise loads,
    and the check that reads it stops on it, naming it. A validation here
    would put the IPS's words in two files."""
    wl = load(W1.replace('asset_class = "Equity"', 'asset_class = "Crypto"')
                .replace('sector = "Communication Services"', 'sector = "Widgets"'))
    candidate = wl.candidates["W-1"]
    assert (candidate.asset_class, candidate.sector) == ("Crypto", "Widgets")


# --- the thesis ----------------------------------------------------------------

def test_the_committed_theses_are_the_files_word_for_word(watchlist):
    """The research agent attaches a prediction to the thesis as I wrote
    it, and case 4.4's check compares the two word for word (PHI-6.1)."""
    import tomli
    with open(ROOT / "watchlist.toml", "rb") as f:
        raw = {c["id"]: c["thesis"] for c in tomli.load(f)["candidate"]}
    wl = watchlist.load_watchlist("watchlist.toml")
    assert {cid: c.thesis for cid, c in wl.candidates.items()} == raw


def test_a_thesis_is_kept_as_written(load):
    wl = load(W1.replace('thesis = "A thesis."', 'thesis = """\n  A thesis.  \n"""'))
    assert wl.candidates["W-1"].thesis == "  A thesis.  \n"


@pytest.mark.parametrize("value", ['""', '"   "', "12"], ids=["empty", "whitespace", "a number"])
def test_a_thesis_that_is_no_sentence_is_refused(load, watchlist, value):
    with pytest.raises(watchlist.WatchlistError, match=r"lacks \['thesis'\].*a thesis \(PHI-6.1\)"):
        load(W1.replace('thesis = "A thesis."', f"thesis = {value}"))
