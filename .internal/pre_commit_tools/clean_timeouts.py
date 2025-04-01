#!/usr/bin/env python3

import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

PROJECT_ROOT = Path(subprocess.getoutput("git rev-parse --show-toplevel"))  # noqa: S605
TIMEOUTS_FILE = PROJECT_ROOT / "tests" / "resources" / "timeouts.yaml"


def main() -> bool:
    return validate_unique_keys() and remove_missing_files()


def validate_unique_keys() -> bool:
    with TIMEOUTS_FILE.open("r") as f:
        data = f.read()

    keys = [line.split(":")[0].strip() for line in data.splitlines()]
    duplicate_keys = [key for key, count in Counter(keys).items() if count > 1]
    if duplicate_keys:
        print(f"duplicate keys found in the timeouts file ({duplicate_keys})")

    return not duplicate_keys


def find_missing_files() -> list[str]:
    with TIMEOUTS_FILE.open("r") as f:
        timeouts = yaml.safe_load(f)

    missing_files = list(
        filter(
            lambda file_name: not any(PROJECT_ROOT.rglob(file_name)),
            timeouts,
        )
    )
    return missing_files


def remove_missing_files() -> bool:
    missing_files = find_missing_files()
    if missing_files:
        print(
            "There exists some entries in timeouts which are long gone. removing them."
        )
        with PRODUCT_DEMOS_INTERNAL_TIMEOUTS_FILE.open("r") as f:
            timeouts = yaml.safe_load(f)

        for file in missing_files:
            del timeouts[file]

        with open(PRODUCT_DEMOS_INTERNAL_TIMEOUTS_FILE, "w") as f:
            yaml.dump(timeouts, f, sort_keys=True)

    is_ok = not missing_files
    return is_ok


if __name__ == "__main__":
    if not main():
        sys.exit(1)
