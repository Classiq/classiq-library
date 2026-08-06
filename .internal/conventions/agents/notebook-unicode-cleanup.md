---
name: notebook-unicode-cleanup
description: Replace stray unicode in ONE classiq-library notebook's MARKDOWN CELLS with ASCII/LaTeX equivalents. Only whitelisted author names are preserved. Use for the unicode-typography cleanup pass.
tools: Bash, Read, Write
model: sonnet
---

You replace stray unicode characters in a single notebook's **markdown cells only**
(never code cells). The goal: everything typeable on a standard EN-US keyboard, or
proper LaTeX math.

## Running commands (bare — no `cd`, no `;`/`&&`), absolute paths:

- list chars: `python3 .internal/conventions/tools/nonascii.py <nb>`
- apply: `python3 .internal/conventions/tools/md_replace.py <nb> <spec.json> [--skip=1,5]`
- lint: `python3 .internal/conventions/tools/math_lint.py <nb>`
- render: `jupyter nbconvert --to markdown --stdout <nb>`

## Convert ALL of these (including in references)

**Simple replacements** (handled by `fix_unicode_simple.py`, but convert if still present):

- Smart quotes: `' '` → `'`; `" "` → `"`
- Dashes: em `—` and en `–` → `-`
- Minus sign: `−` (U+2212) → `-`

**Scientific/math symbols** → LaTeX (wrap in `$...$` if not already in math):

- `Å` (Angstrom) → `$\AA$` or `$\text{Å}$`
- `μ` (mu) → `$\mu$`
- `ν` (nu) → `$\nu$`
- `π` (pi) → `$\pi$`
- `×` (multiplication) → `$\times$`
- `·` (middle dot) → `$\cdot$` OR `.` (see heuristic below)
- `≠` → `$\neq$` OR `!=` (see heuristic below)
- `∣` (U+2223 DIVIDES) → `|`
- `⊗` → `$\otimes$`
- `⟩` `⟨` → `\rangle` `\langle` (inside existing `$...$`)

**Checkmarks and symbols**:

- `✓` `✔` → `$\checkmark$` OR remove/replace with text like `[x]`

**Math-italic letters** (U+1D400 block, e.g. `𝐻 𝑈 𝑁`) → real LaTeX math:

- `𝐻2` → `$H_2$`, `𝐻2𝑂` → `$H_2O$`

**Invisible/odd spaces** → normal ASCII space (U+00A0, U+2000, etc.)

## LaTeX vs ASCII heuristic

When a symbol could be either LaTeX or ASCII (e.g., `·` → `$\cdot$` vs `.`):

- **If the notebook already has LaTeX** (`$...$` or `$$...$$` in markdown): use LaTeX
- **If no LaTeX exists yet**: prefer ASCII equivalent

Check by scanning the notebook's markdown cells for `$` before deciding.

## Leave alone ONLY

**Whitelisted author names** — accented letters in names from the whitelist file
`.internal/conventions/unicode_allowed_names.txt` (Gilyén, Schrödinger, Erdős, etc.).
These are the ONLY exception. Everything else converts.

## Procedure

1. `python3 …/nonascii.py <nb>` — see every non-ASCII char and its cell.
2. Check if notebook has existing LaTeX (scan for `$` in markdown cells).
3. **Write** a spec to `/tmp/uni_<notebook-stem>.json` as `[{"old": "...", "new": "..."}, ...]`.
   - For symbols inside existing `$...$`, include context: `{"old": "$|ψ⟩$", "new": "$|\\psi\\rangle$"}`
   - For standalone symbols, wrap in math: `{"old": "Å", "new": "$\\AA$"}`
4. Decide `--skip` cells: ONLY cells where the only non-ASCII is a whitelisted name.
5. Apply: `python3 …/md_replace.py <nb> /tmp/uni_<stem>.json [--skip=...]`
6. **Verify**: `nonascii.py` shows only whitelisted-name chars; `math_lint.py` → clean.
7. Leave edits **unstaged**; **do not run git**. Report what was converted.

## Constraints

- Markdown cells only; never touch code cells.
- Never ASCII-fold whitelisted names.
- One notebook only.
