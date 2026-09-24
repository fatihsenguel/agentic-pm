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

One exception, named in `REPLY_TO_ASK_BACK`: the runner's 3.1 sends a
second turn, the instrument type the first turn asks back for (decision
12), which the corpus does not send. For it the table's prompt is the
runner's first turn, and the second turn is the runner's alone.

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

# The runner's second turn for a case whose first turn asks back, the
# corpus sending the first turn only.
REPLY_TO_ASK_BACK = {"3.1": "A share."}


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
    """The runner's prompts as the corpus sends them: a case in
    `REPLY_TO_ASK_BACK` must be exactly its first turn and that reply, and
    is compared on its first turn."""
    cases = {}
    for case_id, prompt, *_ in run_cases.CASES:
        reply = REPLY_TO_ASK_BACK.get(case_id)
        if reply is not None:
            assert isinstance(prompt, tuple) and len(prompt) == 2 and prompt[1] == reply, (
                f"{case_id}: CASES {prompt!r} is not a first turn and the reply {reply!r}")
            prompt = prompt[0]
        cases[case_id] = prompt
    return cases


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
