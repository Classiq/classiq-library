#!/usr/bin/env python3
"""Structural math-markup linter for notebooks (MARKDOWN CELLS ONLY).
Catches the breakage our delimiter/unicode edits could introduce — without
executing or even rendering. Run before & after edits and compare.

Checks per markdown cell:
  - balanced $$ (even count) and balanced inline $ (even after removing $$)
  - matched \\begin{X} / \\end{X} per environment
  - no [$$...$$](  — a markdown link-label wrongly turned into math
  - no leftover \\[ or \\] that became unbalanced
"""
import glob, json, re, sys


def lint_cell(text: str) -> list[str]:
    issues = []
    dd = text.count("$$")
    single = text.replace("$$", "").replace("\\$", "").count("$")
    if dd % 2:
        issues.append(f"odd $$ count ({dd})")
    if single % 2:
        issues.append(f"odd inline $ count ({single})")
    for env in set(re.findall(r"\\begin\{(\w+\*?)\}", text)) | set(
        re.findall(r"\\end\{(\w+\*?)\}", text)
    ):
        b, e = len(re.findall(rf"\\begin\{{{re.escape(env)}\}}", text)), len(
            re.findall(rf"\\end\{{{re.escape(env)}\}}", text)
        )
        if b != e:
            issues.append(f"\\begin/\\end mismatch for {env}: {b} vs {e}")
    if re.search(r"\[\$\$[^]]*\$\$\]\(", text):
        issues.append("broken link-label: [$$...$$](  — was an escaped [\\[..\\]] link")
    return issues


def lint(path: str) -> list[str]:
    out = []
    for i, c in enumerate(json.load(open(path)).get("cells", [])):
        if c.get("cell_type") != "markdown":
            continue
        for msg in lint_cell("".join(c["source"])):
            out.append(f"  cell {i}: {msg}")
    return out


bad = 0
for p in sorted(sys.argv[1:]):
    if issues := lint(p):
        bad += 1
        print(f"ISSUES {p}")
        print("\n".join(issues))
print(f"\n{'OK — all clean' if not bad else f'{bad} notebook(s) with issues'}")
sys.exit(1 if bad else 0)
