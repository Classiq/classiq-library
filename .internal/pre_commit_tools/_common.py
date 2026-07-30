#!/usr/bin/env python3
"""Shared helpers for the notebook / qmod pre-commit tools.

Pre-commit runs each hook as `python <script>.py`, so the script's own directory
is on sys.path and siblings import directly:

    from _common import PROJECT_ROOT, is_tested, validate_unique_names

(the same pattern metadata_validate uses for metadata_utils / metadata_consts.)
"""

import subprocess
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

PROJECT_ROOT = Path(subprocess.getoutput("git rev-parse --show-toplevel"))  # noqa: S605

# Notebooks under these top-level areas are not part of the CI-tested core.
_UNTESTED_DIRS = ("functions", "community")


def is_tested(path) -> bool:
    """True for a notebook we expect to carry a test (i.e. not community/functions)."""
    parts = Path(path).parts
    return not any(area in parts for area in _UNTESTED_DIRS)


def iter_files(pattern: str, exclude_parts: Iterable[str] = ()) -> list[Path]:
    """Repo files matching `pattern`, skipping checkpoints/.git and any `exclude_parts`."""
    skip = (".ipynb_checkpoints", ".git", *exclude_parts)
    return [
        p
        for p in PROJECT_ROOT.rglob(pattern)
        if not any(part in p.parts for part in skip)
    ]


def validate_unique_names(
    pattern: str, label: str, exclude_parts: Iterable[str] = ()
) -> bool:
    """Fail if two matching files share a basename (tests key off the basename)."""
    names = [p.name for p in iter_files(pattern, exclude_parts)]
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if duplicates:
        print(
            f"File naming error: every {label} must have a unique basename "
            f"(even across directories). Duplicates found: {duplicates}"
        )
    return not duplicates


def validate_filename(file_path: str) -> bool:
    """A notebook/qmod basename uses underscores — no dashes, no spaces."""
    name = Path(file_path).name
    errors = []
    if "-" in name:
        errors.append(
            f"dash (-) is not allowed; use underscore (_), "
            f"e.g. rename to '{file_path.replace('-', '_')}'"
        )
    if " " in name:
        errors.append(
            f"space is not allowed; use underscore (_), "
            f"e.g. rename to '{file_path.replace(' ', '_')}'"
        )
    if errors:
        spacing = "\n\t"  # f-string cannot include a backslash
        print(f"File `{file_path}` has naming error(s):{spacing}{spacing.join(errors)}")
    return not errors
