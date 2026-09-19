"""
A section of a filing's document, pure (expected_values.md Part 16, D52).

Text in, one section's text out. It fetches nothing and stores nothing; the
text is a filing's document as `portfolio_tool.filing_text` yields it, and
the section is returned whole, its heading line first, cut nowhere.

The rule, measured over the whole of Alphabet's FY2025 10-K and written to
refuse a document it does not fit rather than read it by guess:

  - a heading is a line that starts with `Item`, whitespace, one or two
    digits, an optional letter A to C and a period, case disregarded; the
    title after it is not read
  - the heading lines, in order, form exactly two runs, each rising in item
    order and both carrying the same items: the table of contents, then the
    body
  - a section is the lines from its heading in the body to the line before
    the body's next heading, whichever item that is

Refused, each naming what it found: a document whose headings form one run
or more than two; two runs that differ in their items; a section asked for
that the body does not carry, or carries last, with nothing to end it; a
heading with no line beneath it. There is no nearest heading, no match on a
title, and no minimum length.
"""

import re
from typing import List, Tuple

from portfolio_tool.reading import SECTIONS

__all__ = ["SectionError", "HEADING", "section"]

HEADING = re.compile(r"^item\s+(\d{1,2})([a-c]?)\.", re.IGNORECASE)
_NAME = re.compile(r"^Item (\d{1,2})([A-C]?)$")

Item = Tuple[int, str]


class SectionError(Exception):
    """Raised when a section cannot be found in a document by the rule."""


def _label(item: Item) -> str:
    return f"Item {item[0]}{item[1]}"


def _runs(lines: List[str]) -> List[List[Tuple[int, Item]]]:
    runs: List[List[Tuple[int, Item]]] = []
    for n, line in enumerate(lines):
        found = HEADING.match(line)
        if not found:
            continue
        item = (int(found.group(1)), found.group(2).upper())
        if not runs or item <= runs[-1][-1][1]:
            runs.append([])
        runs[-1].append((n, item))
    return runs


def section(text: str, name: str) -> str:
    """The section `name` of the document `text` under D52, or a
    SectionError naming what was found."""
    if name not in SECTIONS:
        raise SectionError(f"{name!r} is not a section that is read; the sections are "
                           f"{', '.join(SECTIONS)}.")
    number, letter = _NAME.match(name).groups()
    wanted = (int(number), letter)

    lines = text.split("\n")
    runs = _runs(lines)
    if len(runs) != 2:
        raise SectionError(
            f"the document's item headings form {len(runs)} run(s) in item order, not two, "
            "a table of contents and a body; no section is read."
        )
    contents, body = ([item for _, item in run] for run in runs)
    if contents != body:
        differ = sorted(set(contents) ^ set(body)) or sorted(set(contents))
        raise SectionError(
            f"the table of contents and the body carry different items, "
            f"{', '.join(_label(item) for item in differ)}; no section is read."
        )

    items = [item for _, item in runs[1]]
    if wanted not in items:
        raise SectionError(f"the document carries no heading for {name}.")
    at = items.index(wanted)
    if at + 1 == len(items):
        raise SectionError(f"{name} is the document's last item; nothing ends it, and it "
                           "is not read.")
    start, end = runs[1][at][0], runs[1][at + 1][0]
    if end - start < 2:
        raise SectionError(f"{name} has a heading and no line beneath it; nothing is read.")
    return "\n".join(lines[start:end])
