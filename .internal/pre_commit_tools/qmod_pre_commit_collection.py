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
TIMEOUTS_FILE = PROJECT_ROOT / "tests" / "resources" / "timeouts.yaml"

DEFAULT_TIMEOUT_SECONDS: float = 10


def main(full_file_paths: Iterable[str]) -> bool:
    return validate_unique_names() and all(map(is_valid_qmod, full_file_paths))


def is_valid_qmod(file_path: str, automatically_add_timeout: bool = True) -> bool:
    file_name = os.path.basename(file_path)

    errors = []

    if _does_contain_dash_in_file_name(file_name):
        errors.append(
            "File naming format error:\n"
            "    Dash (-) is not allowed in file named. please use underscore (_)\n"
            f"    for example, you may change '{file_path}' to '{file_path.replace('-', '_')}'."
        )

    if not _is_file_in_timeouts(file_name):
        if automatically_add_timeout:
            _add_file_to_timeouts(file_name)
            errors.append(
                "A new notebook was detected.\n"
                f"    Automatically adding a timeout entry {{{file_name} : {DEFAULT_TIMEOUT_SECONDS}}}.\n"
                f"    Please make sure to add the changes done to '{TIMEOUTS_FILE}'"
            )
        else:
            errors.append(
                "A new notebook was detected.\n"
                "    However, a coresponding entry in the timeouts file is missing.\n"
                f"    Please add an entry. You may add '{{{file_name} : {DEFAULT_TIMEOUT_SECONDS}}}'\n"
                f"        to {TIMEOUTS_FILE}\n"
                "    Alternatively, you may install pre-commit. It will automatically add a timeout entry in the next time you run 'git commit'."
            )

    if errors:
        spacing = "\n\t"  # f-string cannot include backslash
        print(f"File `{file_path}` has error(s):{spacing}{spacing.join(errors)}")

    return not errors


def _does_contain_dash_in_file_name(file_name: str) -> bool:
    return "-" in file_name


def _is_file_in_timeouts(file_name: str) -> bool:
    with TIMEOUTS_FILE.open("r") as f:
        timeouts = yaml.safe_load(f)

    return file_name in timeouts


def _add_file_to_timeouts(file_name: str) -> None:
    with TIMEOUTS_FILE.open("r") as f:
        timeouts = yaml.safe_load(f)

    timeouts[file_name] = DEFAULT_TIMEOUT_SECONDS

    with TIMEOUTS_FILE.open("w") as f:
        yaml.dump(timeouts, f, sort_keys=True)


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
