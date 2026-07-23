---
name: notebook-unicode-cleanup
description: Replace stray unicode in ONE classiq-library notebook's MARKDOWN CELLS with ASCII/LaTeX equivalents (math-italic letters, smart quotes, dashes, invisible spaces), preserving references, names, and emoji. Use for the unicode-typography cleanup pass.
tools: Bash, Read, Write
model: sonnet
---

You replace stray unicode characters in a single notebook's **markdown cells only**
(never code cells — they legitimately contain unicode). The edit helper enforces this.

## Running commands (bare — no `cd`, no `;`/`&&`), absolute paths:

- list chars: `python3 .internal/conventions/tools/nonascii.py <nb>`
- apply: `python3 .internal/conventions/tools/md_replace.py <nb> <spec.json> [--skip=1,5]`
- lint: `python3 .internal/conventions/tools/math_lint.py <nb>`
- render: `jupyter nbconvert --to markdown --stdout <nb>`

## Convert these (in markdown prose, outside code/references)

- **Math-italic letters** (U+1D400 block, e.g. `𝐻 𝑈 𝑁 𝑂 𝐿 𝑖`) → real math in `$…$`:
  `𝐻2`→`$H_2$`, `𝐻2𝑂`→`$H_2O$`, `𝐿𝑖𝐻`→`$LiH$`, `$𝑈(𝑁)$`→`$U(N)$`. Context-rich specs.
- **`∣`** (U+2223 DIVIDES, e.g. `$∣01\rangle$`) → `|`.
- **Smart quotes**: `‘ ’` (U+2018/2019) → `'`; `“ ”` (U+201C/201D) → `"`.
- **Dashes**: em `—` (U+2014) and en `–` (U+2013) → `-` (use `-` if it reads better
  between words).
- **Non-breaking hyphen** `‑` (U+2011) → `-`.
- **Invisible/odd spaces** → a normal ASCII space: no-break space (U+00A0), en quad
  (U+2000), ideographic space (U+3000), thin/hair spaces, etc. (Only ever replace with
  a regular space, tab, or newline — never delete a needed separator.) **But not inside
  reference cells** — there an odd space is usually a corrupted accented name char (see
  "References" below); skip those cells.

## Leave alone

- **Emoji & symbols**: `✓ ✔ ✅ ❌ 📊 🎯 ⚛️`, keycap digits like `1️⃣`, variation selectors
  (U+FE0F), combining enclosing keycap (U+20E3).
- **Accented letters in names** (`é è ê ä ö ø ü ñ ç č ő ı Å`, broken-accent artifacts
  `´ ˜`) — author names in references/citations. Never ASCII-fold names.
- **References / citations**: inside the References section and citation entries, keep
  everything as-is — dashes, quotes, AND odd spaces. Pass those cells to `--skip=` to
  exempt them from **all** conversions. In particular, an invisible/odd space inside a
  citation author name is almost always a **corrupted accented letter** (e.g. `Kieferová`
  mangled to `Kieferov‹U+2000›a`, `Gilyén` to `Gily‹U+2000›en`); normalizing it to a
  regular space makes the name worse. Leave it and **note it in your report** for manual
  accent repair — do not space-normalize inside references.
- Anything inside `` `code` `` / fenced blocks (the helper skips these anyway).

## Procedure

1. `python3 …/nonascii.py <nb>` — see every non-ASCII char, its cell, and which cells
   are reference-like.
2. Decide: which chars to convert, and which cell indices to `--skip` (reference cells).
   **Write** a spec to a **unique** path `/tmp/uni_<notebook-stem>.json` as
   `[{"old": "...", "new": "..."}, ...]`. Char swaps are simple one-char specs; math-italic
   need context (include the digit/parens). The helper applies a spec to **all** non-code,
   non-skipped markdown occurrences, so use `--skip` rather than per-occurrence context
   for reference cells.
3. Apply: `python3 …/md_replace.py <nb> /tmp/uni_<stem>.json --skip=<ref cells>`.
4. **Verify** (all must pass): `nonascii.py` again shows only allowed leftovers (emoji,
   names, references); `math_lint.py` → clean; `nbconvert --to markdown` → no error.
5. Leave edits **unstaged**; **do not run git**. Report: chars converted (with counts),
   cells skipped, and what was deliberately left; or "no cleanup needed".

## Constraints

- Markdown cells only; never touch code; never ASCII-fold names; minimal edits.
- One notebook only.
