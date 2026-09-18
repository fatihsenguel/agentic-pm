"""
A filing's primary document as text, pure (expected_values.md Part 16,
D51).

Bytes in, text out: the lines of the document joined by one newline. It
fetches nothing and stores nothing, and imports nothing of the
repository's. The rule is measured on one document, Alphabet's FY2025
10-K, and is written to refuse what it has not seen rather than read it
by guess:

  - the document declares its encoding as ASCII and every byte is; any
    other declaration, no declaration, or a byte that is not ASCII is
    refused naming it
  - an element outside the ones that document carries, and outside a
    namespace prefix, is refused naming the element
  - text under `head`, `script` and `ix:header` is left out: the last is
    the inline XBRL header, contexts and units and no word of the filing.
    Every other namespaced element is transparent, so a figure tagged
    `ix:nonFraction` is the filing's figure in the filing's line
  - a line ends where a `div` or a `tr` starts or ends, and at a `br`; a
    `td` separates by a space; character references are resolved
  - runs of whitespace inside a line, a no-break space among them, collapse
    to one space, and an empty line is dropped

Page furniture stays (D53), tables survive as lines of cells, and emphasis
and images are lost (Part 16 E). Nothing is cut.
"""

import re
from html.parser import HTMLParser

__all__ = ["FilingTextError", "ENCODING", "ELEMENTS", "LEFT_OUT", "LINE", "text_of"]

ENCODING = "ascii"
# The elements the measured document carries outside a namespace prefix.
ELEMENTS = frozenset({"html", "head", "meta", "title", "body", "script", "div", "span",
                      "table", "tr", "td", "a", "br", "hr", "img"})
LEFT_OUT = frozenset({"head", "script", "ix:header"})
LINE = frozenset({"div", "tr", "br"})
CELL = "td"

_DECLARATION = re.compile(rb"^\s*<\?xml[^>]*?encoding=['\"]([^'\"]+)['\"][^>]*\?>")


class FilingTextError(Exception):
    """Raised when a document is not one this module has a rule for."""


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pieces = []
        self.left_out = 0

    def _known(self, tag):
        if tag not in ELEMENTS and ":" not in tag:
            raise FilingTextError(
                f"the document carries a <{tag}> element, which no document looked at so "
                "far does; what it does to a line is not decided, and nothing is read."
            )

    def handle_starttag(self, tag, attrs):
        self._known(tag)
        if tag in LEFT_OUT:
            self.left_out += 1
        if tag in LINE:
            self.pieces.append("\n")
        elif tag == CELL:
            self.pieces.append(" ")

    def handle_startendtag(self, tag, attrs):
        self._known(tag)
        if tag in LINE:
            self.pieces.append("\n")
        elif tag == CELL:
            self.pieces.append(" ")

    def handle_endtag(self, tag):
        if tag in LEFT_OUT and self.left_out:
            self.left_out -= 1
        if tag in LINE:
            self.pieces.append("\n")

    def handle_data(self, data):
        if not self.left_out:
            self.pieces.append(data)


def text_of(document: bytes) -> str:
    """The document's text under D51, or a FilingTextError."""
    declared = _DECLARATION.match(document)
    if declared is None:
        raise FilingTextError("the document declares no encoding; the one looked at "
                              "declares ASCII, and no other is read.")
    encoding = declared.group(1).decode("ascii", "replace")
    if encoding.lower() != ENCODING:
        raise FilingTextError(f"the document declares its encoding as {encoding}; the one "
                              "looked at declares ASCII, and no other is read.")
    try:
        markup = document.decode(ENCODING)
    except UnicodeDecodeError as error:
        raise FilingTextError(f"the document declares ASCII and byte {error.start} is "
                              "not; nothing is read.") from error

    parser = _Text()
    parser.feed(markup)
    parser.close()
    lines = (" ".join(line.split()) for line in "".join(parser.pieces).split("\n"))
    return "\n".join(line for line in lines if line)
