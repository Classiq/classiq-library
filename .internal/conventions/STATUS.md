# Convention points — status & how to resume

Most points below were done for the **`main` folders only** (`algorithms/`,
`applications/`, `tutorials/` ≈ 160 notebooks); `community/`, `functions/`,
`benchmarking/` can be reached by re-running the same agent on them. The
variable-name points **2 and 2b were applied to all 216 notebooks** (main +
community + other), since the renames are mechanical and low-risk.

To see current coverage of any point at any time:
`python3 .internal/notebook_uniformity_report.py` (run from the repo root).

| Pt   | Convention                                            | Status (main)                                                                               | Resume / extend with                                                                      |
| ---- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| A    | `show(qprog)` not `qprog.show()`                      | ✅ done + **enforced**                                                                      | pre-commit `notebook_uniformity.py`                                                       |
| 1    | `synthesize(main)` not `create_model()+synthesize()`  | 🟡 partial — 19 safe collapses done; ~67 complex left (`execution_preferences`, multi-call) | `one_off_fixes/collapse_synthesize.py` (safe subset); agent/manual for the rest           |
| 2    | exec-outcome var = `result` / `job` / `df` (by type)  | ✅ done (all 216)                                                                           | **`agents/notebook-variable-names.md`** + `tools/rename_var.py`; detector: report point 2 |
| 2b   | synth-output var = `qprog` / `qprog_<suffix>`         | ✅ done (all 216)                                                                           | `tools/rename_var.py`; detector: report point 2b                                          |
| 3    | `.result_value()` not `.result()[0].value`            | ✅ done + **enforced**                                                                      | `one_off_fixes/fix_result_value.py`; hook                                                 |
| 4    | title casing (Title Case)                             | ⛔ open                                                                                     | agent — needs context (QAOA/Grover proper nouns); detector: report point 4                |
| 5    | `## References` (plural)                              | ✅ done + **enforced**                                                                      | pre-commit hook                                                                           |
| 6    | exactly one H1 (the title)                            | ✅ done (main)                                                                              | `one_off_fixes/fix_single_h1.py` (+ `check_fences.py`, `h1_outline.py`)                   |
| 7    | heading hierarchy (levels & nesting)                  | ✅ done (main)                                                                              | **`agents/notebook-heading-hierarchy.md`** + `tools/heading_outline.py`                   |
| 8    | intro opener phrasing                                 | ⛔ open                                                                                     | agent (pick common phrasing); detector: report point 8                                    |
| 9    | section-heading vocabulary                            | ⛔ open                                                                                     | agent; detector: report point 9                                                           |
| 12   | math: display→`$$`, unicode→LaTeX                     | ✅ done (main)                                                                              | **`agents/notebook-math-notation.md`** + `tools/md_replace.py`, `math_lint.py`            |
| 15   | defines `@qfunc def main(...)`                        | 🔎 investigate-only                                                                         | report point 15 (comparison notebooks are documented exceptions)                          |
| B/11 | opens with an H1 title (no code-first)                | ✅ done (main)                                                                              | folded into point 6                                                                       |
| —    | stray unicode typography (dashes/quotes/spaces→ASCII) | ✅ done (main)                                                                              | **`agents/notebook-unicode-cleanup.md`** + `tools/nonascii.py`, `unicode_audit.py`        |
| 10   | sidecar files (.qmod/.synth/.metadata)                | skipped (out of scope)                                                                      | —                                                                                         |

## To extend an agent-driven point to community / functions

1. `python3 tools/<detector or audit>` to list the affected notebooks in the target folder.
2. Batch them (~6 per agent) and run the relevant `agents/*.md` definition on each,
   editing **markdown cells only** via `tools/md_replace.py`.
3. Verify per notebook: `tools/math_lint.py` and/or `tools/nonascii.py`, plus a
   `jupyter nbconvert --to markdown` render (no `--execute`).

## Branches / PRs (names as opened; some may already be merged)

- `__result_value` — points 3, 5, A + the `notebook-uniformity` pre-commit hook
- `__synthesize_main` — point 1 (safe subset)
- `__single_h1` — points 6, 7, B/11
- `__math` — point 12 (+ one malformed-`$$` fix)
- `__unicode_cleanup` — typography cleanup (+ accent repairs in citations)
- `__uniformity_report` — the audit tool + archived exploration scripts
- `__qprog_var` — point 2b (all 216: synth-output var -> `qprog` / `qprog_<suffix>`)
- `__result_var` — point 2 (all 216; commit 1 = main, commit 2 = community & other)
- `__report_details` — report tool: fence-fix, offender listing, result/job/df families
- `__resume_kit` — this `.internal/conventions/` kit
