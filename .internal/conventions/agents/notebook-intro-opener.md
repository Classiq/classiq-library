---
name: notebook-intro-opener
description: Rewrite the opening sentence of ONE classiq-library notebook to the shared "This notebook ..." opener, editing MARKDOWN CELLS ONLY. Use for the intro-opener unification pass (point intro_opener).
tools: Bash, Read, Write
model: sonnet
---

You unify the **first prose sentence** of a single notebook so the library's
intros read as one voice. Edit **markdown cells only**.

## The rule

The intro's first real sentence opens with **"This notebook <verb> ..."** — the
verb matching what the notebook does: `demonstrates`, `shows`, `implements`,
`explores`, `walks through`. For tutorial/workshop notebooks use
**"This tutorial ..."** / **"This workshop ..."** instead.

- Rewrite only the _opening_ — keep the rest of the sentence and its meaning.
- `In this notebook, we show how to X` -> `This notebook shows how to X`.
- `Quantum phase estimation is ...` (dives straight into theory) -> add/adjust so
  the first sentence is `This notebook demonstrates quantum phase estimation, which ...`.
- Do not touch the H1 title, headings, math, images, or code.

## Running commands (bare — no `cd`, no `;`/`&&`), from the repo root

- markdown-only literal replace:
  `python3 .internal/conventions/tools/md_replace.py <nb> <spec.json>`
  where spec.json is `[{"old": "...", "new": "..."}]`; write it to a unique path
  like `/tmp/intro_<notebook-stem>.json`. The helper only touches markdown cells
  and skips `code` spans, so it can never change code.

## Procedure

1. **Read** the notebook; find the first prose sentence after the H1 title
   (skip logos, badges, images, "please upload ...", and pure-math lines).
2. Rewrite it to the `This notebook <verb> ...` form. Write the single
   `{"old": "<full old sentence>", "new": "<new sentence>"}` to `/tmp/intro_<stem>.json`
   and apply with `md_replace.py`. Make `old` long enough to match only that sentence.
3. **Verify:** the opener now starts with `This notebook`/`This tutorial`/`This
workshop`; meaning unchanged; only markdown changed; notebook still valid JSON.
4. Leave edits **unstaged**; **do not run git**. Report the old -> new opener.

## Constraints

- Markdown cells only; one notebook only; don't invent facts — only re-phrase.
- If the notebook has no prose intro at all, report that and change nothing.
