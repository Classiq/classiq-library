"""Executes the Qmod_tutorial_part1.ipynb notebook cells sequentially against the live Classiq backend.
Saves outputs and displays execution progress and results for each section.
"""

import json
import traceback
import pandas as pd
import numpy as np
import classiq
from classiq import *
from classiq.qmod.symbolic import pi


def run_tutorial():
    nb_path = "tutorials/basic_tutorials/the_classiq_tutorial/Qmod_tutorial_part1.ipynb"
    print("=" * 70)
    print("  Executing Classiq Qmod Tutorial - Part 1")
    print(f"  Notebook: {nb_path}")
    print(f"  Classiq Version: {classiq.__version__}")
    print("=" * 70)

    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Execution namespace
    exec_globals = {
        "__name__": "__main__",
        "pi": pi,
        "pd": pd,
        "np": np,
    }
    # Import all symbols from classiq into namespace
    for k in dir(classiq):
        if not k.startswith("_"):
            exec_globals[k] = getattr(classiq, k)

    # Safe mocks for notebook-only display functions
    def safe_show(qprog, *args, **kwargs):
        try:
            url = getattr(qprog, "circuit_url", None) or getattr(qprog, "url", None)
            if url:
                print(f"    [Classiq Platform Circuit]: {url}")
            else:
                print("    [show(qprog) called - interactive visualization link generated]")
        except Exception:
            pass

    def safe_display(obj, *args, **kwargs):
        if hasattr(obj, "head"):
            print("    [DataFrame Sample Output]:")
            print(obj.to_string(max_rows=10))
        elif hasattr(obj, "parsed_counts"):
            print("    [Measurement Counts]:", obj.parsed_counts)
        else:
            print(f"    [Display]: {obj}")

    exec_globals["show"] = safe_show
    exec_globals["display"] = safe_display

    code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    print(f"[*] Found {len(code_cells)} code cells to execute.\n")

    executed_count = 0
    passed_count = 0

    for idx, cell in enumerate(code_cells):
        src = "".join(cell["source"]).strip()
        if not src:
            continue

        # Skip commented auth cell
        if "classiq.authenticate()" in src and src.startswith("#"):
            print(f"--- Cell {idx+1}/{len(code_cells)}: [AUTH CHECK] (Already authenticated, skipping) ---")
            continue

        title_line = src.split("\n")[0]
        if len(title_line) > 60:
            title_line = title_line[:57] + "..."
        print(f"--- Cell {idx+1}/{len(code_cells)}: {title_line} ---")

        executed_count += 1
        try:
            exec(src, exec_globals)
            passed_count += 1
            print(f"    [OK] Cell {idx+1} executed successfully.\n")
        except Exception as e:
            # If an exercise cell fails because it has incomplete TODOs before the solution cells, report it gracefully
            if "TODO" in src:
                print(f"    [NOTE] Exercise cell contains TODO placeholders (exercise prompt).")
                print(f"           Expected behavior before solutions. Error: {type(e).__name__}: {e}\n")
            else:
                print(f"    [!] Cell {idx+1} raised: {type(e).__name__}: {e}")
                traceback.print_exc()
                print()

    print("=" * 70)
    print(f"  Execution Complete: {passed_count}/{executed_count} code cells completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    run_tutorial()
