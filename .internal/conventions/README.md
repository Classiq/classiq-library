# Notebook convention tooling

The kit for keeping the library's notebooks reading as **one entity** — a single
voice across the ~217 notebooks. Run everything from the **repo root**.

- **`report.py`** + **`points/`** — the read-only audit. Each convention is one
  small `points/point_*.py` (a title, a before/after example, a `detect()`, and
  either a static `fix()` or a pointer to its agent); `report.py` loads the
  notebooks, runs every point, and scores coverage:

  ```bash
  python3 .internal/conventions/report.py                    # compact status table (default)
  python3 .internal/conventions/report.py --cards            # detailed per-point cards
  python3 .internal/conventions/report.py --full             # + a legend for the jargon
  python3 .internal/conventions/report.py --rule math --list # offending paths only
  ```

  Add `--files` to list every offender (the card view shows a short preview),
  and `--color`/`--no-color` to override the auto terminal detection.

- **`STATUS.md`** — every point: done / open / enforced, the caveats, and how to resume it.
- **`agents/`** — subagent mission docs for the judgement-heavy points: heading
  hierarchy, math notation, unicode cleanup, title case, section vocabulary, intro
  opener, variable names.
- **`tools/`** — helpers the agents and audits call: `md_replace`, `rename_var`,
  `nonascii`, `math_lint`, `heading_outline`, `heading_stats`, `unicode_audit`.
- **`one_off_fixes/`** — throwaway transform/analysis scripts from past passes,
  kept for reference and not maintained.

The simple, safe rules are also **enforced** in the pre-commit hook at
`.internal/pre_commit_tools/notebook_uniformity.py` (currently: references plural,
`result_value`, `show(qprog)`, and opens-with-an-H1-title).
