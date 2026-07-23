# Convention points — status & how to resume

This `.internal/conventions/` kit is the home of the notebook-uniformity effort.
The live audit is `python3 .internal/conventions/report.py` (from the repo
root) — **trust it for current coverage**, not the prose below.

Scope: unless noted, a point was applied to the **`main` folders** only
(`algorithms/`, `applications/`, `tutorials/`, ~161 notebooks). `community/`,
`functions/`, and `benchmarking/` are reached by re-running the same agent/tool.

> **Parked as _old_ — execution-API refactor.** `execution_interface`,
> `result_value`, and `result_var` were shaped _before_ the execution API was
> refactored, which superseded them. They stay in the report marked _old_ (for
> the record), not as active work — `result_value` is still auto-enforced by the
> pre-commit hook.
>
> **`intro_opener` was dropped** — we decided not to pursue the "This notebook …"
> opener convention. It stays in the report marked _dropped_.
>
> **`math` is on hold by design.** The pass is largely done, but finalizing it
> waits on confirming the `$$` / LaTeX changes don't break LaTeX rendering
> _elsewhere_ (e.g. the docs site).
>
> **Not on `main` yet, by design.** Whether this internal tooling is published
> publicly is still being decided, so `report.py` + `points/` live on the
> `update_notebook_convention__conventions_kit` branch, not `main`.

Rows below follow the report's own order (skeleton → prose → code → parked).

| Point                 | Convention                                            | Status                                                     | Resume / extend with                                                                |
| --------------------- | ----------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `opens_h1`            | opens with an H1 title                                | ✅ done · **enforced** (check — a title can't be invented) | hook `pre_commit_tools/notebook_uniformity.py`                                      |
| `single_h1`           | exactly one H1 (the title)                            | ✅ done · **enforced** (auto-fix)                          | `point_single_h1.fix()`; `one_off_fixes/fix_single_h1.py`                           |
| `headings`            | heading hierarchy (levels & nesting)                  | ✅ main pass done (see report for residuals)               | agent `notebook-heading-hierarchy` + `tools/heading_outline.py`, `heading_stats.py` |
| `title_case`          | headings in Title Case                                | ⛔ open (agent doc added)                                  | agent `notebook-title-case` + `tools/heading_outline.py`                            |
| `section_vocab`       | shared section-heading vocabulary                     | ⛔ open                                                    | agent `notebook-section-vocab` + `tools/md_replace.py`                              |
| `math`                | display → `$$`; unicode math → LaTeX                  | ⏸ on hold by design                                        | agent `notebook-math-notation` + `tools/md_replace.py`, `math_lint.py`              |
| `unicode`             | stray unicode typography → ASCII/LaTeX                | ✅ main pass done (see report for residuals)               | agent `notebook-unicode-cleanup` + `tools/nonascii.py`, `unicode_audit.py`          |
| `references`          | `## References` (plural)                              | ✅ done · **enforced** (auto-fix)                          | hook                                                                                |
| `def_main`            | builds a circuit (`def main` / known wrapper)         | 🔎 investigate-only; comparison notebooks are exceptions   | `report.py --rule def_main`                                                         |
| `synthesize_main`     | `synthesize(main)`, not `create_model()+synthesize()` | 🟡 partial — trivial cases scripted; rest manual           | `one_off_fixes/collapse_synthesize.py`                                              |
| `qprog_var`           | synth-output var `qprog` / `qprog_<suffix>`           | ✅ done                                                    | agent `notebook-variable-names` + `tools/rename_var.py`                             |
| `show`                | `show(qprog)`, not `qprog.show()`                     | ✅ done · **enforced** (auto-fix)                          | hook                                                                                |
| `execution_interface` | new execution-API usage                               | 🗄 old — superseded by the exec-API refactor                | `report.py --rule execution_interface --list`                                       |
| `result_value`        | `.result_value()`, not `.result()[0].value`           | 🗄 old — superseded (still hook-enforced)                   | hook; `one_off_fixes/fix_result_value.py`                                           |
| `result_var`          | exec-result var `result` / `job` (by type)            | 🗄 old — superseded by the exec-API refactor                | agent `notebook-variable-names` + `tools/rename_var.py`                             |
| `intro_opener`        | "This notebook …" opener                              | 🗄 dropped — decided not to pursue                          | agent `notebook-intro-opener` + `tools/md_replace.py`                               |

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
