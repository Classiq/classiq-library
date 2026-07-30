#!/usr/bin/env python3
"""Convert markdown headings in a Jupyter notebook to title case.

Usage:
    python3 title_case.py <notebook.ipynb>              # dry-run: show changes
    python3 title_case.py <notebook.ipynb> --apply      # apply changes in-place
    python3 title_case.py <notebook.ipynb> --outline     # just list headings

Title case rules (Chicago Manual of Style, adapted):
  - Capitalize the first and last *textual* word (numbers don't count).
  - Capitalize all major words (nouns, verbs, adjectives, adverbs, pronouns).
  - Do NOT capitalize minor words (articles, short prepositions, conjunctions)
    unless they are the first or last word, or follow a colon/dash.
  - Preserve ALL-CAPS words (acronyms like QAOA, VQE, HHL).
  - Preserve mixed-case words (MaxCut, PyTorch, NumPy, PennyLane).
  - Preserve content inside $...$ / $$...$$ (LaTeX), `...` (code spans),
    and <...> (HTML tags, including anchors and attributes).
  - Preserve exercise sub-labels (5a, 10b), dimension notation (4x4),
    and parenthesized roman numerals ((i), (ii), (iii)).
  - Capitalize each part of hyphenated words (Block-Encoding, Non-Unitary).
  - After a colon or standalone dash, capitalize the next word (subtitle rule).

Writes JSON with indent=1, ensure_ascii=False so the diff stays minimal.
"""

import json
import re
import sys
from pathlib import Path

MINOR_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "but",
        "by",
        "for",
        "from",
        "in",
        "into",
        "nor",
        "of",
        "on",
        "or",
        "per",
        "so",
        "the",
        "to",
        "vs",
        "via",
        "with",
        "yet",
    }
)


def _is_allcaps(word: str) -> bool:
    letters = re.sub(r"[^A-Za-z]", "", word)
    return len(letters) >= 2 and letters == letters.upper()


def _is_mixed_case(word: str) -> bool:
    letters = re.sub(r"[^A-Za-z]", "", word)
    if len(letters) < 2:
        return False
    has_upper = any(c.isupper() for c in letters)
    has_lower = any(c.islower() for c in letters)
    if not (has_upper and has_lower):
        return False
    return bool(re.search(r"[a-z][A-Z]|[A-Z][a-z].*[A-Z]", letters))


def _capitalize_word(word: str) -> str:
    if not word:
        return word
    for i, c in enumerate(word):
        if c.isalpha():
            return word[:i] + c.upper() + word[i + 1 :]
    return word


def _has_alpha(token: str) -> bool:
    return bool(re.search(r"[A-Za-z]", token))


def _case_one_part(
    part: str, *, is_first: bool, is_last: bool, after_colon: bool
) -> str:
    leading = trailing = ""
    core = part
    lm = re.match(r"^([^A-Za-z0-9]*)", part)
    if lm and lm.group(1):
        leading = lm.group(1)
        core = part[len(leading) :]
    tm = re.search(r"([^A-Za-z0-9]+)$", core)
    if tm:
        trailing = tm.group(1)
        core = core[: -len(trailing)]

    if not core:
        return part

    if _is_allcaps(core) or (
        core.endswith("s") and len(core) > 2 and _is_allcaps(core[:-1])
    ):
        return part

    if _is_mixed_case(core):
        return part

    if re.fullmatch(r"[\d.]+", core):
        return part

    # Ordinal numbers: 1st, 2nd, 3rd, 4th, 21st, etc.
    if re.fullmatch(r"\d+(st|nd|rd|th)", core, re.IGNORECASE):
        return part

    # Exercise sub-labels: 5a, 10b, etc.
    if re.fullmatch(r"\d+[a-z]", core):
        return part

    # Dimension notation: 4x4, 2x2, etc.
    if re.fullmatch(r"\d+x\d+", core, re.IGNORECASE):
        return part

    # Roman numeral markers in parentheses: (i), (ii), (iii), (iv), etc.
    if leading.endswith("(") and re.fullmatch(r"[ivxlcdm]+", core, re.IGNORECASE):
        return part

    if "_" in core:
        return part

    # Single uppercase letter = mathematical variable (A, B, N, ...), preserve
    if len(core) == 1 and core.isupper():
        return part

    core_lower = core.lower()

    if is_first or is_last or after_colon:
        return leading + _capitalize_word(core) + trailing

    if core_lower in MINOR_WORDS:
        return leading + core_lower + trailing

    return leading + _capitalize_word(core) + trailing


def _title_case_token(
    token: str, *, is_first: bool, is_last: bool, after_colon: bool
) -> str:
    if "-" not in token:
        return _case_one_part(
            token, is_first=is_first, is_last=is_last, after_colon=after_colon
        )

    parts = token.split("-")
    new_parts = []
    for j, part in enumerate(parts):
        new_parts.append(
            _case_one_part(
                part,
                is_first=is_first and j == 0,
                is_last=is_last and j == len(parts) - 1,
                after_colon=after_colon if j == 0 else True,
            )
        )
    return "-".join(new_parts)


def title_case_heading(text: str) -> str:
    protected: dict[str, str] = {}

    def _protect(m: re.Match) -> str:
        key = f"\x00{len(protected)}\x00"
        protected[key] = m.group(0)
        return key

    work = re.sub(
        r"\$\$.*?\$\$|\$[^$\n]+?\$|`[^`\n]+?`|\\\(.*?\\\)|<[^>]+>",
        _protect,
        text,
        flags=re.DOTALL,
    )

    pairs = re.findall(r"(\S+)(\s*)", work)
    if not pairs:
        return text

    tokens = [p[0] for p in pairs]
    spaces = [p[1] for p in pairs]

    # Find first/last content index (alpha words OR placeholders count as content)
    first_real = last_real = None
    for i, tok in enumerate(tokens):
        if not (_has_alpha(tok) or "\x00" in tok):
            continue
        if first_real is None:
            first_real = i
        last_real = i

    after_colon = False
    new_tokens: list[str] = []
    for i, tok in enumerate(tokens):
        if "\x00" in tok:
            restored = tok
            for key, original in protected.items():
                restored = restored.replace(key, original)
            new_tokens.append(restored)
            after_colon = False
            continue

        # Standalone dash or em/en dash → treat as subtitle separator
        if tok in ("-", "—", "–"):
            new_tokens.append(tok)
            after_colon = True
            continue

        if not _has_alpha(tok):
            new_tokens.append(tok)
            after_colon = tok.endswith(":")
            continue

        new_tok = _title_case_token(
            tok,
            is_first=(i == first_real),
            is_last=(i == last_real),
            after_colon=after_colon,
        )
        new_tokens.append(new_tok)
        after_colon = tok.endswith(":")

    return "".join(t + s for t, s in zip(new_tokens, spaces))


def process_notebook(path: Path, *, apply: bool = False) -> list[tuple[str, str]]:
    nb = json.loads(path.read_text())
    changes: list[tuple[str, str]] = []
    modified = False

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue

        source = cell.get("source", [])
        in_fence = False
        new_source: list[str] = []

        for line in source:
            stripped = line.rstrip("\n")
            if re.match(r"^\s*```", stripped):
                in_fence = not in_fence
                new_source.append(line)
                continue

            if in_fence:
                new_source.append(line)
                continue

            m = re.match(r"^(#{1,6}\s+)(.*)", line)
            if m:
                prefix = m.group(1)
                heading_text = m.group(2)

                # (.*) doesn't capture \n — preserve it from the original line
                trailing_nl = "\n" if line.endswith("\n") else ""

                new_heading = title_case_heading(heading_text)

                if new_heading != heading_text:
                    changes.append((prefix + heading_text, prefix + new_heading))
                    new_source.append(prefix + new_heading + trailing_nl)
                    modified = True
                else:
                    new_source.append(line)
            else:
                new_source.append(line)

        cell["source"] = new_source

    if apply and modified:
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")

    return changes


def outline(path: Path) -> None:
    nb = json.loads(path.read_text())
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        in_fence = False
        for line in cell.get("source", []):
            stripped = line.rstrip("\n")
            if re.match(r"^\s*```", stripped):
                in_fence = not in_fence
                continue
            if not in_fence:
                m = re.match(r"^(#{1,6})\s+(.*\S)", stripped)
                if m:
                    level = len(m.group(1))
                    print(f"  H{level} {'  ' * (level - 1)}{m.group(2)}")


def main() -> None:
    if len(sys.argv) < 2:
        print(
            f"Usage: {sys.argv[0]} <notebook.ipynb> [--apply|--outline]",
            file=sys.stderr,
        )
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)

    if "--outline" in sys.argv:
        outline(path)
        return

    apply = "--apply" in sys.argv
    changes = process_notebook(path, apply=apply)

    if not changes:
        print(f"OK — no title case changes needed: {path}")
        return

    mode = "APPLIED" if apply else "DRY-RUN"
    print(f"{mode}: {len(changes)} heading(s) to fix in {path}")
    for old, new in changes:
        print(f"  - {old}")
        print(f"  + {new}")


if __name__ == "__main__":
    main()
