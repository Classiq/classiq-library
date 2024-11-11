#!/usr/bin/env python3
import sys
from pathlib import Path

from constants import (
    DEFAULT_TIMEOUT_IPYNB,
    DEFAULT_TIMEOUT_QMOD,
    ROOT,
    TIMEOUTS_FILE,
    TIMEOUTS_PATH,
)
import yaml


def main() -> bool:
    timeouts = _load_timeouts()

    is_ok = True
    for file_path in ROOT.rglob("*"):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(ROOT)
        if _can_skip(relative_path):
            continue
        if not _handle_file(str(relative_path), timeouts):
            is_ok = False

    if is_ok:
        is_ok = _sort_timeouts()

    return is_ok


def _can_skip(filename: Path) -> bool:
    if TIMEOUTS_FILE == filename.suffix or filename.suffix not in [".ipynb", ".qmod"]:
        return True
    if filename.parts[0] == "functions" and len(filename.parts[0]) > 1:
        if filename.parts[1] in ("function_declarations", "open_library_definitions"):
            return True
    return False


def _handle_file(filename: str, timeouts: dict[str, float]) -> bool:
    if filename in timeouts:
        return True
    else:
        print(f"{filename} was not found in timeouts. Adding.")

        if filename.endswith(".ipynb"):
            timeout = DEFAULT_TIMEOUT_IPYNB
        elif filename.endswith(".qmod"):
            timeout = DEFAULT_TIMEOUT_QMOD
        else:
            print(f"Unknown file extension for file {filename}")
            return False

        timeouts[filename] = timeout

        with open(TIMEOUTS_PATH, "w") as f:
            yaml.dump(timeouts, f, sort_keys=True)

        return False


def _load_timeouts() -> dict[str, float]:
    with TIMEOUTS_PATH.open("r") as fobj:
        return yaml.safe_load(fobj)


def _sort_timeouts() -> bool:
    with TIMEOUTS_PATH.open("r") as fobj:
        timeouts = yaml.safe_load(fobj)

    sorted_timeouts = dict(sorted(timeouts.items()))

    if list(timeouts.keys()) != list(sorted_timeouts.keys()):
        with TIMEOUTS_PATH.open("w") as f:
            yaml.dump(sorted_timeouts, f, sort_keys=True)
        print(f"Timeouts were not sorted. Sorted them.")
        return False

    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
