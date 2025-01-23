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

Seconds = float
DEFAULT_TIMEOUT: Seconds = 20

IS_FILE_VALID = bool


def main(full_file_paths: Iterable[str]) -> bool:
    return validate_unique_names() and all(map(validate_notebook, full_file_paths))


def validate_notebook(file_path: str, automatically_add_timeout: bool = True) -> bool:
    file_name = os.path.basename(file_path)
    with open(file_path) as f:
        file_content = f.read()

    errors = []

    if not _forbid_dash_in_file_name(file_name):
        errors.append(
            "Dash (-) is not allowed in file named. please use underscore (_)"
        )

    if not _is_file_in_timeouts(file_name):
        if automatically_add_timeout:
            _add_file_to_timeouts(file_name)
            errors.append("Automatically adding timeout.")
        else:
            errors.append("File is missing timeout in the timeouts.yaml file.")

    if errors:
        print(f"file `{file_path}` has error:")
    for error in errors:
        print(f'\t"{error}"')

    is_ok = not errors
    return is_ok


def _forbid_dash_in_file_name(file_name: str) -> IS_FILE_VALID:
    return not ("-" in file_name)


def _is_file_in_timeouts(file_name: str) -> IS_FILE_VALID:
    with TIMEOUTS_FILE.open("r") as f:
        timeouts = yaml.safe_load(f)

    return file_name in timeouts


def _add_file_to_timeouts(file_name: str) -> None:
    with TIMEOUTS_FILE.open("r") as f:
        timeouts = yaml.safe_load(f)

    timeouts[file_name] = DEFAULT_TIMEOUT

    with TIMEOUTS_FILE.open("w") as f:
        yaml.dump(timeouts, f, sort_keys=True)


def validate_unique_names():
    all_files = PROJECT_ROOT.rglob("*.ipynb")
    base_names = [file.name for file in all_files]

    duplicate_names = [name for name, count in Counter(base_names).items() if count > 1]

    if duplicate_names:
        print(f"notebooks with duplicate names found: {duplicate_names}")

    is_ok = not duplicate_names
    return is_ok


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
