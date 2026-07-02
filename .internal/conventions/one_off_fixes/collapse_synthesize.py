#!/usr/bin/env python3
"""Point 1 (safe subset): collapse the explicit two-step synthesis flow

    qmod = create_model(main[, constraints=..., preferences=...])
    qprog = synthesize(qmod)
into the modern one-step form
    qprog = synthesize(main[, constraints=..., preferences=...])

A cell is transformed ONLY when every guard holds (otherwise the notebook is
skipped and reported), so this can run over all notebooks safely:
  - the notebook has exactly one `create_model(` call
  - its first positional arg is `main`
  - its only other args are `constraints=` / `preferences=`
  - the result var is used exactly twice (the assignment + a `synthesize(var)`)
  - that `synthesize(var)` is in the same cell

Dry-run by default; pass --apply to write (json; pre-commit canonicalises later).
"""

import glob
import json
import re
import sys

FORBIDDEN_KWARGS = ("execution_preferences", "out_file", "classical_execution_function")


def cell_source(cell: dict) -> str:
    source = cell.get("source", [])
    return "".join(source) if isinstance(source, list) else source


def code_cells(nb: dict) -> list[dict]:
    return [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]


def balanced_close(s: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def split_top_level(args_str: str) -> list[str]:
    args, depth, current = [], 0, ""
    for ch in args_str:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            args.append(current)
            current = ""
        else:
            current += ch
    if current.strip():
        args.append(current)
    return [a.strip() for a in args]


def try_collapse(nb: dict) -> tuple[bool, str]:
    cells = code_cells(nb)
    full_code = "\n".join(cell_source(c) for c in cells)
    if full_code.count("create_model(") != 1:
        return False, "not exactly one create_model call"

    cm_cell = next(c for c in cells if "create_model(" in cell_source(c))
    cm_src = cell_source(cm_cell)
    match = re.search(r"(\w+)\s*=\s*create_model\(", cm_src)
    if not match:
        return False, "create_model not a simple assignment"
    var = match.group(1)
    close = balanced_close(cm_src, match.end() - 1)
    args = split_top_level(cm_src[match.end() : close])
    if not args or args[0] != "main":
        return False, f"first arg is not `main` ({args[:1]})"
    kwargs = args[1:]
    if any(forbidden in kw for kw in kwargs for forbidden in FORBIDDEN_KWARGS):
        return False, "carries execution-time / out_file kwargs"
    if len(re.findall(rf"\b{re.escape(var)}\b", full_code)) != 2:
        return False, f"`{var}` is used elsewhere"

    syn_pattern = rf"synthesize\(\s*{re.escape(var)}\s*\)"
    syn_cell = next((c for c in cells if re.search(syn_pattern, cell_source(c))), None)
    if syn_cell is None:
        return False, f"no synthesize({var}) found"

    new_call = "synthesize(main" + "".join(f", {kw}" for kw in kwargs) + ")"
    stmt_start = cm_src.rfind("\n", 0, match.start()) + 1
    stmt_end = close + 1
    if stmt_end < len(cm_src) and cm_src[stmt_end] == "\n":
        stmt_end += 1

    same_cell = syn_cell is cm_cell
    if same_cell:
        syn = re.search(syn_pattern, cm_src)
        edits = sorted(
            [(stmt_start, stmt_end, ""), (syn.start(), syn.end(), new_call)],
            reverse=True,
        )
        for start, end, replacement in edits:
            cm_src = cm_src[:start] + replacement + cm_src[end:]
        cm_cell["source"] = cm_src.splitlines(keepends=True)
    else:
        cm_cell["source"] = (cm_src[:stmt_start] + cm_src[stmt_end:]).splitlines(
            keepends=True
        )
        syn_src = re.sub(
            syn_pattern, lambda _m: new_call, cell_source(syn_cell), count=1
        )
        syn_cell["source"] = syn_src.splitlines(keepends=True)

    where = "same-cell" if same_cell else "cross-cell"
    return True, f"collapsed (var={var}, {len(kwargs)} kwarg(s), {where})"


def main() -> None:
    apply = "--apply" in sys.argv
    done, skipped = [], []
    for path in sorted(glob.glob("**/*.ipynb", recursive=True)):
        nb = json.load(open(path))
        if "create_model(" not in "\n".join(cell_source(c) for c in code_cells(nb)):
            continue
        changed, note = try_collapse(nb)
        if changed:
            done.append((path, note))
            if apply:
                with open(path, "w") as f:
                    json.dump(nb, f, indent=1, ensure_ascii=False)
                    f.write("\n")
        else:
            skipped.append((path, note))

    print(
        f"{'APPLIED' if apply else 'DRY-RUN'} — collapsed {len(done)}, skipped {len(skipped)}\n"
    )
    print("COLLAPSED:")
    for path, note in done:
        print(f"  {path}\n      {note}")
    reasons: dict[str, int] = {}
    for _path, note in skipped:
        reasons[note] = reasons.get(note, 0) + 1
    print(f"\nSKIPPED ({len(skipped)}) — left for the agent pass:")
    for note, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {note}")


if __name__ == "__main__":
    main()
