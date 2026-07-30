#!/usr/bin/env python3
"""Validate notebook file names: unique basenames, underscores (no dash/space)."""

import sys
from collections.abc import Iterable

from _common import validate_filename, validate_unique_names


def main(full_file_paths: Iterable[str]) -> bool:
    names_ok = validate_unique_names("*.ipynb", "notebook")
    files_ok = all([validate_filename(path) for path in full_file_paths])
    return names_ok and files_ok


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
