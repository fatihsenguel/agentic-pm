"""
The spine's wordings live in two places, and this holds that they agree.

benchmark.md Part 3c.1 restates the eighteen benchmark prompts verbatim as
tests/benchmark/run_cases.py sends them, because the runner's wording is
the one that has been run and scored. A copy can drift from its source and
nothing else reads both: the runner never opens benchmark.md, and the
corpus is run through the CLI, not the runner. Written before the corpus
was first run (the interlude between Orders 4 and 5, step 3).

What this holds: the set of ids is the same eighteen in both, and every
prompt is character for character the runner's, 3.5's two turns included.
The table writes a two-turn case as "Turn 1: ... Turn 2: ..." on one line;
the runner holds it as a tuple.

What this does not hold: anything about the other four kinds of corpus
entry, whose wordings have no second copy, and nothing about the answers.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tests" / "benchmark"))

import run_cases  # noqa: E402

BENCHMARK = ROOT / "docs" / "benchmark.md"

ROW = re.compile(r"^\| (\d\.\d) \| (.+?) \| Part 18, ")
TURNS = re.compile(r"^Turn 1: (.+?) Turn 2: (.+)$")


def _spine_table():
    """The 3c.1 table's rows as {id: prompt}, a two-turn row as a tuple."""
    text = BENCHMARK.read_text(encoding="utf-8")
    start = text.index("### 3c.1")
    end = text.index("### 3c.2", start)
    rows = {}
    for line in text[start:end].splitlines():
        match = ROW.match(line)
        if match is None:
            continue
        case_id, prompt = match.group(1), match.group(2)
        turns = TURNS.match(prompt)
        rows[case_id] = turns.groups() if turns else prompt
    return rows


def _runner_cases():
    return {case_id: prompt for case_id, prompt, *_ in run_cases.CASES}


def test_the_spine_has_the_runner_s_eighteen_ids():
    table = _spine_table()
    runner = _runner_cases()
    assert len(runner) == 18
    assert set(table) == set(runner), (
        f"only in Part 3c.1: {sorted(set(table) - set(runner))}; "
        f"only in CASES: {sorted(set(runner) - set(table))}"
    )


def test_every_spine_wording_is_the_runner_s():
    table = _spine_table()
    runner = _runner_cases()
    drifted = {
        case_id: (table.get(case_id), runner[case_id])
        for case_id in runner
        if table.get(case_id) != runner[case_id]
    }
    assert not drifted, "\n".join(
        f"{case_id}: Part 3c.1 {table!r} / CASES {sent!r}"
        for case_id, (table, sent) in sorted(drifted.items())
    )


def test_a_two_turn_row_is_read_as_two_turns():
    assert _spine_table()["3.5"] == ("Hows my APPL doing?", "yes")
