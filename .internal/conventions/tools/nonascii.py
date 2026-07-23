#!/usr/bin/env python3
"""List non-ASCII characters per markdown cell of ONE notebook, to guide the
unicode-cleanup agent. Flags reference-like cells (whose citation dashes/quotes
should be preserved) and whether each char sits inside a code span (left alone).

    python3 nonascii.py <notebook.ipynb>
"""

import json, re, sys, unicodedata
from collections import Counter

CODE_SPAN = re.compile(r"```.*?```|`[^`\n]*`", re.S)
REF_HINT = re.compile(r"(?mi)^#{1,4}\s*references?\b|<a id=|\[\d+\]\(#")


def main() -> None:
    nb = json.load(open(sys.argv[1]))
    any_found = False
    for i, c in enumerate(nb.get("cells", [])):
        if c.get("cell_type") != "markdown":
            continue
        text = "".join(c["source"])
        code = [(m.start(), m.end()) for m in CODE_SPAN.finditer(text)]

        def in_code(p):
            return any(a <= p < b for a, b in code)

        chars = Counter()
        in_code_chars = Counter()
        for p, ch in enumerate(text):
            if ord(ch) >= 128:
                (in_code_chars if in_code(p) else chars)[ch] += 1
        if not chars and not in_code_chars:
            continue
        any_found = True
        ref = (
            "  <-- REFERENCE-like (preserve citation dashes/quotes; consider --skip)"
            if REF_HINT.search(text)
            else ""
        )
        print(f"cell {i}{ref}")
        for ch, n in chars.most_common():
            print(f"    {ch!r:>6} U+{ord(ch):04X} x{n:<3} {unicodedata.name(ch,'?')}")
        for ch, n in in_code_chars.most_common():
            print(
                f"    {ch!r:>6} U+{ord(ch):04X} x{n:<3} {unicodedata.name(ch,'?')}  [in code — leave]"
            )
    if not any_found:
        print("(no non-ASCII in markdown cells)")


if __name__ == "__main__":
    main()
