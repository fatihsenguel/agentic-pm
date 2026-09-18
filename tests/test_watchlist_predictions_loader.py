"""
The watchlist loader's prediction rows (case 4.5, Part 14), held to their
raises the way test_watchlist_loader.py holds the candidates. The
file-to-document tests are in test_watchlist.py.

What the loader reads now: each candidate's predictions in document order,
each with its id, made_on, due, kind and statement; a figure prediction's
metric, bound, value and period; and, where the ledger carries one, the
score I wrote, its four fields. What it still leaves alone: the thesis,
the entry condition, added_on and the philosophy check, which nothing
consumes. What it refuses: a kind other than figure or event, a figure
lacking any of its four keys or an event carrying one, a bound other than
min or max, a period not FYnnnn, a value that is not a number, a score
with some of its four fields, a result other than right or wrong, a
scored_on before the due date, an id not W-n.m under W-n, an id twice, a
due date not after made_on, an empty statement, a key nothing reads. The
metric's vocabulary is the scorer's (D42): the loader takes any name and
the scorer stops on one it has no formula for.
"""

import datetime as dt

import pytest


FIGURE = '''
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

[[candidate.prediction]]
id = "W-1.1"
made_on = 2026-01-01
due = 2026-03-01
kind = "figure"
metric = "revenue"
bound = "min"
value = 400000000000
period = "FY2025"
statement = "Revenue of at least 400 billion."
'''

EVENT = '''
[[candidate.prediction]]
id = "W-1.2"
made_on = 2026-01-01
due = 2026-03-01
kind = "event"
statement = "Something about the business."
'''

SCORE = '''
outcome = "The segment note shows it."
source = "10-K, segment note"
scored_on = 2026-03-02
result = "right"
'''


@pytest.fixture
def watchlist():
    from portfolio_tool import watchlist
    return watchlist


@pytest.fixture
def load(watchlist, tmp_path):
    def _load(text):
        path = tmp_path / "watchlist.toml"
        path.write_text(text)
        return watchlist.load_watchlist(str(path))
    return _load


# --- the committed file ------------------------------------------------------

def test_the_committed_file_has_four_predictions_in_document_order(watchlist):
    wl = watchlist.load_watchlist("watchlist.toml")
    rows = watchlist.predictions(wl)
    assert [p.id for p in rows] == ["W-1.1", "W-1.2", "W-2.1", "W-2.2"]
    assert [p.candidate for p in rows] == ["W-1", "W-1", "W-2", "W-2"]
    assert all(p.score is None for p in rows), "none is scored today"
    w11, w12, w21, w22 = rows
    assert (w11.kind, w11.metric, w11.bound, w11.value, w11.period) == (
        "figure", "revenue", "min", 420000000000, "FY2026")
    assert w11.due == dt.date(2027, 3, 1) and w11.made_on == dt.date(2026, 9, 10)
    assert w12.kind == "event"
    assert (w12.metric, w12.bound, w12.value, w12.period) == (None, None, None, None)
    assert (w21.metric, w21.value, w21.due) == ("revenue", 25500000000, dt.date(2027, 2, 1))
    assert (w22.metric, w22.bound, w22.value) == ("gross_margin", "min", 0.87)
    assert list(wl.candidates["W-1"].predictions) == rows[:2]
    assert list(wl.candidates["W-2"].predictions) == rows[2:]


def test_what_the_loader_still_leaves_alone(watchlist):
    wl = watchlist.load_watchlist("watchlist.toml")
    for field in ("thesis", "entry_condition", "added_on", "philosophy_check"):
        assert not hasattr(wl.candidates["W-1"], field), field


# --- the shapes ----------------------------------------------------------------

def test_a_figure_and_an_event_load_with_their_fields(load):
    wl = load(FIGURE + EVENT)
    figure, event = wl.candidates["W-1"].predictions
    assert figure.statement == "Revenue of at least 400 billion."
    assert (figure.metric, figure.bound, figure.value, figure.period) == (
        "revenue", "min", 400000000000, "FY2025")
    assert isinstance(figure.value, int)
    assert event.kind == "event" and event.metric is None and event.score is None


def test_a_written_score_loads_with_its_four_fields(load):
    wl = load(FIGURE + EVENT + SCORE)
    event = wl.candidates["W-1"].predictions[1]
    assert event.score is not None
    assert (event.score.outcome, event.score.source, event.score.scored_on, event.score.result) == (
        "The segment note shows it.", "10-K, segment note", dt.date(2026, 3, 2), "right")


def test_a_score_on_the_due_date_loads(load):
    wl = load(FIGURE + EVENT + SCORE.replace("2026-03-02", "2026-03-01"))
    assert wl.candidates["W-1"].predictions[1].score.scored_on == dt.date(2026, 3, 1)


def test_a_candidate_without_prediction_rows_loads_with_none(load):
    """PHI-6.1's at-least-one is held on the committed file by
    test_watchlist.py; a fixture candidate without rows loads empty."""
    wl = load(FIGURE.split("[[candidate.prediction]]")[0])
    assert wl.candidates["W-1"].predictions == ()


def test_a_fractional_value_loads_as_written(load):
    wl = load(FIGURE.replace('metric = "revenue"', 'metric = "gross_margin"')
              .replace("value = 400000000000", "value = 0.59"))
    assert wl.candidates["W-1"].predictions[0].value == 0.59


# --- the refusals --------------------------------------------------------------

def _refused(load, watchlist, text, *words):
    with pytest.raises(watchlist.WatchlistError) as e:
        load(text)
    for word in words:
        assert word in str(e.value), (word, str(e.value))


def test_a_kind_outside_the_vocabulary_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE.replace('kind = "figure"', 'kind = "guess"'),
             "W-1.1", "guess", "figure", "event")


@pytest.mark.parametrize("line", ['metric = "revenue"', 'bound = "min"',
                                  "value = 400000000000", 'period = "FY2025"'])
def test_a_figure_lacking_one_of_its_four_keys_is_refused_naming_it(load, watchlist, line):
    key = line.split(" =")[0]
    _refused(load, watchlist, FIGURE.replace(line + "\n", ""), "W-1.1", key)


@pytest.mark.parametrize("line", ['metric = "revenue"', 'bound = "min"',
                                  "value = 400000000000", 'period = "FY2025"'])
def test_an_event_carrying_a_figure_key_is_refused(load, watchlist, line):
    key = line.split(" =")[0]
    _refused(load, watchlist, FIGURE + EVENT.replace(
        'kind = "event"\n', f'kind = "event"\n{line}\n'), "W-1.2", key)


def test_a_bound_outside_min_and_max_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE.replace('bound = "min"', 'bound = "over"'),
             "W-1.1", "over", "min", "max")


@pytest.mark.parametrize("period", ['"2025"', '"FY25"', '"fy2025"', "2025"])
def test_a_period_not_of_the_form_fy_year_is_refused(load, watchlist, period):
    _refused(load, watchlist, FIGURE.replace('period = "FY2025"', f"period = {period}"),
             "W-1.1", "FY")


@pytest.mark.parametrize("value", ['"400000000000"', "true", "false"])
def test_a_value_that_is_not_a_number_is_refused(load, watchlist, value):
    _refused(load, watchlist, FIGURE.replace("value = 400000000000", f"value = {value}"),
             "W-1.1", "value")


@pytest.mark.parametrize("drop", ["outcome", "source", "scored_on", "result"])
def test_a_score_with_three_of_its_four_fields_is_refused(load, watchlist, drop):
    lines = [l for l in SCORE.splitlines() if l and not l.startswith(drop)]
    _refused(load, watchlist, FIGURE + EVENT + "\n".join(lines) + "\n",
             "W-1.2", drop, "all four")


def test_a_result_outside_right_and_wrong_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE + EVENT + SCORE.replace('"right"', '"maybe"'),
             "W-1.2", "maybe", "right", "wrong")


def test_a_score_dated_before_the_due_date_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE + EVENT + SCORE.replace("2026-03-02", "2026-02-28"),
             "W-1.2", "2026-02-28", "2026-03-01")


def test_a_score_whose_date_is_not_a_date_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE + EVENT + SCORE.replace("2026-03-02", '"soon"'),
             "W-1.2", "scored_on")


def test_an_empty_outcome_or_source_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE + EVENT + SCORE.replace('"10-K, segment note"', '"  "'),
             "W-1.2", "source")


def test_an_id_under_the_wrong_candidate_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE.replace('id = "W-1.1"', 'id = "W-2.1"'),
             "W-2.1", "W-1")


def test_an_id_off_form_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE.replace('id = "W-1.1"', 'id = "W-1-1"'), "W-1-1")


def test_an_id_twice_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE + EVENT.replace('id = "W-1.2"', 'id = "W-1.1"'),
             "W-1.1", "twice")


def test_a_due_date_not_after_made_on_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE.replace("due = 2026-03-01", "due = 2026-01-01"),
             "W-1.1", "due")


def test_a_date_that_is_not_a_date_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE.replace("made_on = 2026-01-01", 'made_on = "January"'),
             "W-1.1", "made_on")


def test_an_empty_statement_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE.replace('"Revenue of at least 400 billion."', '"  "'),
             "W-1.1", "statement")


def test_a_key_nothing_reads_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE + 'note = "a remark"\n', "W-1.1", "note")


def test_a_prediction_lacking_a_header_field_is_refused(load, watchlist):
    _refused(load, watchlist, FIGURE.replace("due = 2026-03-01\n", ""), "W-1.1", "due")


def test_predictions_that_are_not_a_list_are_refused(load, watchlist):
    _refused(load, watchlist, FIGURE.replace("[[candidate.prediction]]", "[candidate.prediction]"),
             "W-1", "prediction")
