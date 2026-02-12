#!/usr/bin/env python3
# ruff: noqa: F841,E713

import os
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import yaml

PROJECT_ROOT = Path(subprocess.getoutput("git rev-parse --show-toplevel"))  # noqa: S605


def main(full_file_paths: Iterable[str]) -> bool:
    return validate_unique_names() and all(map(is_valid_qmod, full_file_paths))


def is_valid_qmod(
    file_path: str,
    automatically_add_timeout: bool = True,
    assert_if_fails: bool = False,
) -> bool:
    file_name = os.path.basename(file_path)

    errors = []

    if _does_contain_dash_in_file_name(file_name):
        errors.append(
            "File naming format error:\n"
            "    Dash (-) is not allowed in file name. please use underscore (_)\n"
            f"    for example, you may change '{file_path}' to '{file_path.replace('-', '_')}'."
        )

    if _does_contain_space_in_file_name(file_name):
        errors.append(
            "File naming format error:\n"
            "    Space is not allowed in file name. please use underscore (_)\n"
            f"    for example, you may change '{file_path}' to '{file_path.replace(' ', '_')}'."
        )

    spacing = "\n\t"  # f-string cannot include backslash
    errors_combined_message = (
        f"File `{file_path}` has error(s):{spacing}{spacing.join(errors)}"
    )

    if assert_if_fails:
        assert not errors, errors_combined_message
    else:
        if errors:
            print(errors_combined_message)

        return not errors


def should_notebook_be_tested(file_path: str) -> bool:
    return not ("functions/" in file_path or "community/" in file_path)


def _does_contain_dash_in_file_name(file_name: str) -> bool:
    return "-" in file_name


def _does_contain_space_in_file_name(file_name: str) -> bool:
    return " " in file_name


def validate_unique_names() -> bool:
    all_files: Iterable[Path] = PROJECT_ROOT.rglob("*.qmod")
    # exclude `functions/`
    all_files = [
        path
        for path in all_files
        if ("functions" not in path.parts) and (".ipynb_checkpoints" not in path.parts)
    ]
    base_names = [file.name for file in all_files]

    duplicate_names = [name for name, count in Counter(base_names).items() if count > 1]

    if duplicate_names:
        print(
            "File naming error:\n"
            "    There is a requirement that each qmod file will have a unique names. No two files with the same name, even if the files sit in different directories.\n"
            f"    However, the following qmods were found with duplicate names: {duplicate_names}"
        )

    is_ok = not duplicate_names
    return is_ok


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
