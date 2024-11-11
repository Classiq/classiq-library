#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

import yaml

from constants import ROOT, TIMEOUTS_PATH


def main() -> bool:
    with TIMEOUTS_PATH.open("r") as fobj:
        timeouts: dict[str, float] = yaml.safe_load(fobj)

    is_ok = True

    new_timeouts = timeouts.copy()

    for key in timeouts:
        file_path = ROOT / key
        if not file_path.exists():
            is_ok = False

            new_timeouts.pop(key)

    if not is_ok:
        print(
            "There exists some entries in timeouts which are long gone. removing them."
        )

        with open(TIMEOUTS_PATH, "w") as f:
            yaml.dump(new_timeouts, f, sort_keys=True)

    return is_ok


if __name__ == "__main__":
    if not main():
        sys.exit(1)
