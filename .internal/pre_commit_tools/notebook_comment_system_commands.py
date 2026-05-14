#!/usr/bin/env python3

import sys
import re
import json

REMOVE_PIP_ONLY = True
EXE = "pip" if REMOVE_PIP_ONLY else "system"


PATTERN_FIND_PIP = "^\\s*!\\s*pip\\b"
PATTERN_FIND_BASH = "^\\s*!"


def main() -> bool:
    result = True
    for file in sys.argv[1:]:
        result &= comment_out_system_commands(file)
    return result


def comment_out_system_commands(notebook_path: str, auto_fix: bool = True) -> bool:
    result = True
    did_nb_change = False
    with open(notebook_path) as f:
        nb = json.load(f)

    try:
        for cell_index, cell in enumerate(nb["cells"]):
            if cell["cell_type"] == "code":
                if auto_fix:
                    is_file_ok, new_source = _verify_and_fix_lines(
                        cell["source"], cell_index
                    )
                    if not is_file_ok:
                        did_nb_change = True
                        nb["cells"][cell_index]["source"] = new_source
                else:
                    did_nb_change |= not _verify_all_lines(cell["source"], cell_index)
    except Exception as exc:
        result = False
        print(
            f"Failed commenting out {EXE} commands for '{notebook_path}'. Error: {exc}"
        )

    if did_nb_change:
        result = False
        print(f"Rewriting '{notebook_path}'")
        with open(notebook_path, "w") as f:
            json.dump(nb, f, indent=1)
    return result


def _verify_all_lines(lines: list[str] | str, cell_index: int) -> bool:
    if type(lines) is str:
        lines = [lines]

    pattern = PATTERN_FIND_PIP if REMOVE_PIP_ONLY else PATTERN_FIND_BASH

    result = True
    for line_index, line in enumerate(lines):
        if re.match(pattern, line):
            result = False
            print(f"Cell {cell_index} Line {line_index} has `{EXE}` command: {line}")
    return result


def _verify_and_fix_lines(
    source: list[str] | str, cell_index: int
) -> tuple[bool, list[str] | str]:
    is_file_ok = True

    pattern = PATTERN_FIND_PIP if REMOVE_PIP_ONLY else PATTERN_FIND_BASH

    if type(source) is str:
        new_source = source

        if re.match(pattern, source):
            is_file_ok = False
            new_line = re.sub(f"({pattern})", "# \\1", source)
            print(
                f"Cell {cell_index} Line {1} has `{EXE}` command. Fixing. : {new_line}"
            )
            new_source = new_line
    else:
        new_source = source[::]
        for line_index, line in enumerate(source):
            if re.match(pattern, line):
                is_file_ok = False
                new_line = re.sub(f"({pattern})", "# \\1", line)
                print(
                    f"Cell {cell_index} Line {line_index+1} has `{EXE}` command. Fixing. : {new_line}"
                )
                new_source[line_index] = new_line

    return is_file_ok, new_source


if __name__ == "__main__":
    sys.exit(not main())
