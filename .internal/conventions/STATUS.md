# Convention points — status & how to resume

This `.internal/conventions/` kit is the home of the notebook-uniformity effort.
The live audit is `python3 .internal/conventions/report.py --table` (from the repo
root) — **trust it for current coverage**, not the prose below.

Scope: unless noted, a point was applied to the **`main` folders** only
(`algorithms/`, `applications/`, `tutorials/`, ~161 notebooks). `community/`,
`functions/`, and `benchmarking/` are reached by re-running the same agent/tool.

> **Provisional — execution-API refactor.** `execution_interface`, `result_value`,
> and `result_var` were shaped _before_ the execution API was refactored. The
> uniformity goal still stands, but their **exact** rule may be rewritten — do not
> treat these three as settled.
>
> **`math` is on hold by design.** The pass is largely done, but finalizing it
> waits on confirming the `$$` / LaTeX changes don't break LaTeX rendering
> _elsewhere_ (e.g. the docs site).
>
> **Not on `main` yet, by design.** Whether this internal tooling is published
> publicly is still being decided, so `report.py` + `points/` live on the
> `update_notebook_convention__conventions_kit` branch, not `main`.

| Point                 | Convention                                            | Status                                                                            | Resume / extend with                                                                |
| --------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `show`                | `show(qprog)`, not `qprog.show()`                     | ✅ done · **enforced** (auto-fix)                                                 | hook `pre_commit_tools/notebook_uniformity.py`                                      |
| `references`          | `## References` (plural)                              | ✅ done · **enforced** (auto-fix)                                                 | hook                                                                                |
| `result_value`        | `.result_value()`, not `.result()[0].value`           | ✅ done · **enforced** (auto-fix) · ⚠ provisional                                | hook; `one_off_fixes/fix_result_value.py`                                           |
| `opens_h1`            | opens with an H1 title                                | ✅ done · **enforced** (check — a title can't be invented)                        | hook                                                                                |
| `single_h1`           | exactly one H1 (the title)                            | ✅ done · auto-fix ready, enforcement pending PR #1642                            | `point_single_h1.fix()`; `one_off_fixes/fix_single_h1.py`                           |
| `headings`            | heading hierarchy (levels & nesting)                  | ✅ main pass done (see report for residuals)                                      | agent `notebook-heading-hierarchy` + `tools/heading_outline.py`, `heading_stats.py` |
| `unicode`             | stray unicode typography → ASCII/LaTeX                | ✅ main pass done (see report for residuals)                                      | agent `notebook-unicode-cleanup` + `tools/nonascii.py`, `unicode_audit.py`          |
| `qprog_var`           | synth-output var `qprog` / `qprog_<suffix>`           | ✅ done                                                                           | agent `notebook-variable-names` + `tools/rename_var.py`                             |
| `synthesize_main`     | `synthesize(main)`, not `create_model()+synthesize()` | 🟡 partial — trivial cases scripted; rest manual / fall out of the exec migration | `one_off_fixes/collapse_synthesize.py`                                              |
| `execution_interface` | new execution-API usage                               | 🟡 in progress · ⚠ provisional                                                   | `report.py --rule execution_interface --list`                                       |
| `result_var`          | exec-result var `result` / `job` (by type)            | 🟡 partial · ⚠ provisional                                                       | agent `notebook-variable-names` + `tools/rename_var.py`                             |
| `math`                | display → `$$`; unicode math → LaTeX                  | ⏸ on hold by design                                                              | agent `notebook-math-notation` + `tools/md_replace.py`, `math_lint.py`              |
| `title_case`          | headings in Title Case                                | ⛔ open (agent doc now added)                                                     | agent `notebook-title-case` + `tools/heading_outline.py`                            |
| `section_vocab`       | shared section-heading vocabulary                     | ⛔ open                                                                           | agent `notebook-section-vocab` + `tools/md_replace.py`                              |
| `intro_opener`        | "This notebook …" opener                              | ⛔ open                                                                           | agent `notebook-intro-opener` + `tools/md_replace.py`                               |
| `def_main`            | builds a circuit (`def main` / known wrapper)         | 🔎 investigate-only; comparison notebooks are documented exceptions               | `report.py --rule def_main`                                                         |

Not a point: **sidecar files** (`.qmod` / `.synth` / `.metadata`) — out of scope here.

## To extend an agent-driven point to community / functions

1. `python3 .internal/conventions/report.py --rule <point> --list` to list the
   offending notebooks.
2. Batch them (~6 per agent) and run the relevant `agents/*.md` on each, editing
   **markdown cells only** via `tools/md_replace.py` (or `tools/rename_var.py` for code).
3. Verify per notebook with `tools/math_lint.py` / `tools/nonascii.py` and a
   `jupyter nbconvert --to markdown` render (no `--execute`).

## History

The passes landed as a family of `update_notebook_convention__*` branches
(show / references / result_value, single_h1 / headings, synthesize_main, unicode,
math, qprog_var / result_var, …). Several are already merged to `main`; the rest,
plus the report and this kit, are consolidated on the `conventions_kit` branch. See
the repo's PR list for the authoritative merged/open state.
