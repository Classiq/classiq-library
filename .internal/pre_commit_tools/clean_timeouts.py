#!/usr/bin/env python3

import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

PROJECT_ROOT = Path(subprocess.getoutput("git rev-parse --show-toplevel"))  # noqa: S605
TIMEOUTS_FILE = PROJECT_ROOT / "tests" / "resources" / "timeouts.yaml"


def main() -> bool:
    keys = _get_all_timeout_keys()
    duplicate_keys = [key for key, count in Counter(keys).items() if count > 1]
    if duplicate_keys:
        print(
            "While looking at the `timeouts.yaml` file, a duplicate key was found.\n"
            f"    Please open '{str(TIMEOUTS_FILE)}' and remove one of the duplicate keys.\n"
            f"    The duplicate keys are: ({duplicate_keys})"
        )
        return False

    all_files = {p.name for p in PROJECT_ROOT.rglob("*") if p.is_file()}
    missing_files = {key for key in keys if key not in all_files}
    if missing_files:
        print(
            "While looking at the `timeouts.yaml` file, some old keys were found.\n"
            "    These keys point to notebooks/qmods which are long gone.\n"
            "    We'll automatically remove them. Make sure to `git add` these new changes."
        )
        _remove_keys(missing_files)
        return False

    return True


def _get_all_timeout_keys() -> list[str]:
    with TIMEOUTS_FILE.open("r") as f:
        data = f.read()

    return [line.split(":")[0].strip() for line in data.splitlines()]


def _remove_keys(keys: set[str]) -> None:
    with TIMEOUTS_FILE.open("r") as f:
        timeouts = yaml.safe_load(f)

    for key in keys:
        del timeouts[key]

    with open(TIMEOUTS_FILE, "w") as f:
        yaml.dump(timeouts, f, sort_keys=True)


if __name__ == "__main__":
    if not main():
        sys.exit(1)
