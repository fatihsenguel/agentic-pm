"""
The exploratory CLI's console after a turn (decision 77): one line per
record the turn logged, with the tool, its inputs and its provenance, and
each of the tool's fixed caveats under it, in place of the dump of the
last run's `shared_data` and the block of its agents, both of which a
finished turn now leaves empty. The client proper comes after Order 5;
this is the least the console must show for a corpus run to be read.

`show` is called as the CLI calls it after a turn, over a state built by
hand, and its output captured. Nothing is paid for.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents import cli  # noqa: E402


def _record(tool, inputs, text, as_of=None, source=None, caveats=(), agents=None):
    return {"tool": tool, "inputs": inputs, "key": tool, "block": {}, "text": text,
            "blocks": {}, "agents": agents or {},
            "provenance": {"as_of": as_of, "source": source, "caveats": tuple(caveats)}}


def _state(answer, *records):
    return {"tool_calls": list(records), "final_response": answer, "errors": [],
            "warnings": [], "shared_data": {}, "sub_results": {}, "execution_step": 0,
            "request_id": "r1"}


def _shown(state, question="q", verbose=False, capsys=None):
    cli.show(state, 0.1, verbose, question, {})
    return capsys.readouterr().out


COMPLIANCE = _record("compliance_check", {}, "IPS-4.2: AAPL 4.41 pp over, as of 2026-09-23",
                     as_of="2026-09-23",
                     caveats=("Not done: no recommendation, no target weight, no instrument "
                              "to trade.",),
                     agents={"DataAgent": True, "PortfolioAnalysisAgent": True,
                             "ComplianceAgent": True})
SCREEN = _record("philosophy_screen", {"ticker": "GOOGL"}, "PHI-2.1 fails; source EDGAR",
                 as_of="2026-09-24", source="EDGAR")


def test_one_line_per_record_with_the_tool_its_inputs_and_its_provenance(capsys):
    out = _shown(_state("AAPL is 4.41 pp over IPS-4.2 as of 2026-09-23.", COMPLIANCE, SCREEN),
                 capsys=capsys)
    assert "TOOLS CALLED" in out
    lines = [line for line in out.splitlines() if line.startswith("  ")]
    compliance = next(line for line in lines if "compliance_check" in line)
    assert "{}" in compliance and "2026-09-23" in compliance and "not recorded" in compliance
    screen = next(line for line in lines if "philosophy_screen" in line)
    assert "GOOGL" in screen and "2026-09-24" in screen and "EDGAR" in screen
    assert out.index("compliance_check") < out.index("philosophy_screen")


def test_each_caveat_is_printed_under_its_record(capsys):
    out = _shown(_state("AAPL is 4.41 pp over.", COMPLIANCE, SCREEN), capsys=capsys)
    assert "Not done: no recommendation, no target weight, no instrument to trade." in out
    assert out.index("compliance_check") < out.index("Not done:") < out.index("philosophy_screen")


def test_a_missing_as_of_and_source_print_as_not_recorded_and_never_a_default(capsys):
    out = _shown(_state("IPS-1.3 forbids it.",
                        _record("policy_lookup", {"topic": "share price"}, "IPS-1.3")),
                 capsys=capsys)
    line = next(l for l in out.splitlines() if "policy_lookup" in l)
    assert line.count("not recorded") == 2
    assert "None" not in line


def test_the_dumps_of_the_last_runs_state_are_gone(capsys):
    out = _shown(_state("Nothing.", COMPLIANCE), capsys=capsys)
    assert "SHARED_DATA" not in out and "AGENTS RUN" not in out


def test_a_turn_that_called_no_tool_says_so(capsys):
    out = _shown(_state("Which position do you mean?"), capsys=capsys)
    assert "TOOLS CALLED" in out and "(none)" in out


def test_the_no_numbers_warning_reads_the_records_texts(capsys):
    """A tool printed figures and none reached the answer: the warning
    fires on the records' texts, and reads nothing from `shared_data`."""
    fired = _shown(_state("The check ran.", COMPLIANCE), capsys=capsys)
    assert "NO NUMBERS IN ANSWER" in fired
    quiet = _shown({**_state("The check ran."), "shared_data": {"allocation": {"x": 1}}},
                   capsys=capsys)
    assert "NO NUMBERS IN ANSWER" not in quiet


def test_verbose_prints_each_records_agents(capsys):
    out = _shown(_state("AAPL is 4.41 pp over.", COMPLIANCE), verbose=True, capsys=capsys)
    assert "ComplianceAgent" in out and "DataAgent" in out
    quiet = _shown(_state("AAPL is 4.41 pp over.", COMPLIANCE), capsys=capsys)
    assert "ComplianceAgent" not in quiet
