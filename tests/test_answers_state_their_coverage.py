"""
An answer states what it covers, and names what extraction read and it did not use.

Two rules, both from data, neither from the question.

The line they replace claimed the opposite. `_format_allocation_response`
printed "The question named no breakdown, so all three are shown" whenever
`group_by` was null, and `group_by` is the model's: null carries no evidence
about what was asked, so the sentence was a guess about the question stated as
a fact, and it was false for every question that named a breakdown the model
failed to set. Recorded under Hygiene, "Four wrong-faced answers behind 11/12"
- where it still reads "both are shown", written before the position view
existed. No test anywhere asserted that sentence, which is why it stood.

What a formatter may state is what it did: which views it rendered and how
many lines each carries. The counts here are read from the block, and the
falsifier plants a block with one position fewer so that a coverage line
carrying a hardcoded nine fails.

`tickers` is different in kind and that is the point of the second rule.
Extraction reads it from the message deterministically, so a filled list is
evidence that the message named a position - the one thing in the decision
that is. Neither the allocation views nor the portfolio volatility has a
selection by position, so a filled list there is something read and dropped,
and the answer says so instead of printing every holding under a question
about one.

Naming the drop is not honouring it. A selection axis for these views is
`filter`, not built (KNOWN_GAPS, the group_by/filter entry), and the rank
selection that "my two biggest holdings" needs is decision 35. Until a
narrowing is a field, no answer can say what the question asked and it
widened; it can only say what it covered and what it did not use.
"""

from agents.nodes import _format_allocation_response, _format_portfolio_volatility_response

from test_compliance import allocation


VOLATILITY = {
    "PortfolioAnalysisAgent": {
        "success": True,
        "portfolio_volatility": {
            "annualised": 0.102936,
            "covariance_method": "sample",
            "weights_basis": "market value of the invested assets, cash excluded",
            "weights_as_of": "2026-09-02",
            "annualisation": 252,
            "window": {"start": "2025-09-03", "end": "2026-09-02", "closes": 252},
        },
    }
}


def _alloc(group_by=None, tickers=None, alloc=None):
    """`tickers` is passed only when the case is about it, so that the
    coverage cases fail on the sentence rather than on the signature."""
    result = {"success": True, "allocation": alloc or allocation(), "base_currency": "USD"}
    args = ({"PortfolioAnalysisAgent": result}, group_by)
    if tickers is not None:
        args += (tickers,)
    return "\n".join(_format_allocation_response(*args))


def _vol(tickers=None):
    args = (VOLATILITY,) if tickers is None else (VOLATILITY, tickers)
    return "\n".join(_format_portfolio_volatility_response(*args))


# --- what it covers ----------------------------------------------------------

def test_the_allocation_answer_claims_nothing_about_the_question():
    """The sentence this file exists to delete. `group_by` null is the model
    not setting a field, not the question naming no breakdown."""
    text = _alloc()
    assert "The question named no breakdown" not in text
    assert "question named" not in text


def test_the_allocation_answer_states_the_views_it_rendered():
    text = _alloc()
    assert "**Covered:** 5 asset classes, 5 sector lines, 9 positions." in text


def test_coverage_names_only_the_view_that_was_rendered():
    assert "**Covered:** 5 sector lines." in _alloc(group_by="sector")
    assert "**Covered:** 9 positions." in _alloc(group_by="position")
    assert "**Covered:** 5 asset classes." in _alloc(group_by="asset_class")


def test_the_counts_are_read_from_the_block_not_the_portfolio():
    """The falsifier. A block with one position fewer must say eight; a
    coverage line carrying the portfolio's nine passes the test above and
    fails here."""
    thinner = allocation()
    thinner["by_position"]["lines"] = thinner["by_position"]["lines"][:-1]
    assert "**Covered:** 5 asset classes, 5 sector lines, 8 positions." in _alloc(alloc=thinner)


# --- what it read and did not use --------------------------------------------

def test_the_allocation_answer_names_a_ticker_it_did_not_select_by():
    text = _alloc(tickers=["JNJ"])
    assert "**Read and not used:** JNJ." in text
    assert "no selection by position" in text


def test_two_tickers_read_and_not_used_are_both_named():
    assert "**Read and not used:** JNJ and AAPL." in _alloc(tickers=["JNJ", "AAPL"])


def test_no_such_line_when_extraction_read_no_ticker():
    assert "Read and not used" not in _alloc()


def test_the_volatility_answer_names_a_ticker_it_did_not_select_by():
    """The same drop, one figure over. The portfolio's volatility has no
    per-position form here, so a named ticker is read and dropped exactly as
    it is in the allocation views."""
    text = _vol(tickers=["JNJ"])
    assert "**Read and not used:** JNJ." in text
    assert "10.29%" in text


def test_the_volatility_answer_says_nothing_when_no_ticker_was_read():
    assert "Read and not used" not in _vol()
