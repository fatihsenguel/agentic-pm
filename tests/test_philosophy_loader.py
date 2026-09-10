"""
The philosophy loader held to its raises, the way test_ips.py holds the IPS
loader. The file-to-document tests are in test_philosophy.py.

Every metric key names a formula in quant/fundamentals.py; a key nothing
computes fails to load, so a philosophy that loads is one every numeric
clause of which can be screened.
"""

from pathlib import Path

import pytest


ROOT = Path(__file__).parent.parent

GOOD = '''
[[clause]]
id = "PHI-2.1"
type = "metric_band"
topics = ["quality", "return on capital"]
metric = "return_on_invested_capital"
min = 0.12
years = 5
text = "Return on invested capital of at least 12% in each of the last five fiscal years."
'''

SAFETY = '''
[[clause]]
id = "PHI-4.1"
type = "margin_of_safety"
topics = ["price", "margin of safety"]
discount = 0.25
text = "I pay at most the low end of my valuation range less a 25% discount."
'''


@pytest.fixture(scope="module")
def philosophy():
    from portfolio_tool import philosophy
    return philosophy


def _write(tmp_path, body):
    p = tmp_path / "philosophy.toml"
    p.write_text(body, encoding="utf-8")
    return str(p)


def test_inline_good_loads(philosophy, tmp_path):
    doc = philosophy.load_philosophy(_write(tmp_path, GOOD))
    clause = doc["PHI-2.1"]
    assert dict(clause.params) == {"metric": "return_on_invested_capital", "min": 0.12, "years": 5}


def test_margin_of_safety_loads(philosophy, tmp_path):
    doc = philosophy.load_philosophy(_write(tmp_path, SAFETY))
    assert dict(doc["PHI-4.1"].params) == {"discount": 0.25}


def test_a_relative_path_is_anchored_to_the_project_root(philosophy, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    doc = philosophy.load_philosophy("philosophy.toml")
    assert doc.path == str(ROOT / "philosophy.toml")
    assert len(doc) == 17


def test_the_loader_takes_no_default(philosophy):
    with pytest.raises(TypeError):
        philosophy.load_philosophy()


def test_missing_file_is_an_error_not_an_empty_philosophy(philosophy, tmp_path):
    with pytest.raises(philosophy.PhilosophyError, match="no default philosophy"):
        philosophy.load_philosophy(str(tmp_path / "absent.toml"))


def test_the_error_is_a_clause_error(philosophy):
    from portfolio_tool.clauses import ClauseError
    assert issubclass(philosophy.PhilosophyError, ClauseError)


def test_the_type_vocabulary(philosophy):
    assert set(philosophy.CLAUSE_TYPES) == {"statement", "metric_band", "margin_of_safety"}


@pytest.mark.parametrize("body, message", [
    (GOOD.replace("metric_band", "quality_score"), "not one the checker knows"),
    (GOOD.replace("metric_band", "quality_score"), "as a statement until"),
    # the metric vocabulary is quant/fundamentals.METRICS, and nothing else
    (GOOD.replace("return_on_invested_capital", "return_on_equity"), "no formula computes"),
    (GOOD.replace("return_on_invested_capital", "return_on_equity"), "return_on_invested_capital"),
    (GOOD.replace('metric = "return_on_invested_capital"\n', ""), "needs \\['metric'"),
    (GOOD.replace("years = 5\n", ""), "needs \\['years'\\]"),
    (GOOD.replace("years = 5", "years = 0"), "positive whole number"),
    (GOOD.replace("years = 5", "years = 2.5"), "positive whole number"),
    (GOOD.replace("years = 5", "years = true"), "positive whole number"),
    (GOOD.replace("min = 0.12\n", ""), "min, max or both"),
    (GOOD.replace("min = 0.12", "min = 0.20\nmax = 0.10"), "not below max"),
    (GOOD.replace("min = 0.12", 'min = "12%"'), "not a number"),
    (GOOD.replace("min = 0.12", "min = 0.12\ndiscount = 0.2"), "does not take"),
    (GOOD.replace("metric_band", "statement"), "statement carries"),
    (SAFETY.replace("discount = 0.25", "discount = 25"), "fraction in \\(0, 1\\)"),
    (SAFETY.replace("discount = 0.25", "discount = 0"), "fraction in \\(0, 1\\)"),
    (SAFETY.replace("discount = 0.25\n", ""), "needs \\['discount'\\]"),
    (SAFETY.replace("discount = 0.25", "discount = 0.25\nyears = 1"), "does not take"),
    (GOOD + GOOD, "appears twice"),
    (GOOD.replace('"PHI-2.1"', '"P-2.1"'), "does not match PHI-<section>"),
    (GOOD.replace('"PHI-2.1"', '"IPS-2.1"'), "does not match PHI-<section>"),
    ('[philosophy]\ntitle = "x"\n' + GOOD, "nothing reads"),
    ("not = [toml", "not valid TOML"),
])
def test_loader_raises(philosophy, tmp_path, body, message):
    with pytest.raises(philosophy.PhilosophyError, match=message):
        philosophy.load_philosophy(_write(tmp_path, body))
