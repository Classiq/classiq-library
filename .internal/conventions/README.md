# Notebook convention tooling

The kit for keeping the library's notebooks reading as **one entity**. Each
convention "point" (its status and how to resume it) is tracked in `STATUS.md`.
Run the agents/tools from the **repo root**.

- **`STATUS.md`** — every convention point: done / open, on which branch, and how to resume it
- **`agents/`** — reusable subagent definitions: heading-hierarchy, math-notation, unicode-cleanup, variable-names
- **`tools/`** — helpers used by the agents & audits: `md_replace`, `rename_var`, `nonascii`, `math_lint`, `heading_outline`, `heading_stats`, `unicode_audit`
- **`one_off_fixes/`** — throwaway transform/analysis scripts from past passes (kept for reference, not maintained)

The read-only audit that scores every point lives at `.internal/notebook_uniformity_report.py`.
