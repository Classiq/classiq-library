#!/usr/bin/env python3

import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

# nbformat is imported lazily inside load_notebook / save_notebook

_VERSION_MAJOR = 4

PROJECT_ROOT = Path(subprocess.getoutput("git rev-parse --show-toplevel"))  # noqa: S605

_UNTESTED_DIRS = ("functions", "community")


#
# Pre-commit entry point
#


def _always_true(_: str) -> bool:
    return True


def _resolve_file_paths(file_paths: list[str] | None, extension: str) -> list[str]:
    if file_paths is not None:
        return file_paths

    if "--all-files" in sys.argv:
        sys.argv.remove("--all-files")
        return [
            str(p)
            for p in PROJECT_ROOT.rglob(extension)
            if ".ipynb_checkpoints" not in p.parts
        ]

    return sys.argv[1:]


def run_precommit(
    verify_file: Callable[[str], bool],
    file_paths: list[str] | None = None,
    filter_file: Callable[[str], bool] = _always_true,
    verify_all: Callable[[], bool] | None = None,
    extension: str = "*.ipynb",
) -> None:
    paths = _resolve_file_paths(file_paths, extension)

    per_file_ok = all(list(map(verify_file, filter(filter_file, paths))))
    all_ok = verify_all() if verify_all is not None else True

    sys.exit(not (per_file_ok and all_ok))


#
# File validation
#


def is_tested(path) -> bool:
    parts = Path(path).parts
    return not any(area in parts for area in _UNTESTED_DIRS)


def iter_files(pattern: str, exclude_parts: Iterable[str] = ()) -> list[Path]:
    skip = (".ipynb_checkpoints", ".git", *exclude_parts)
    return [
        p
        for p in PROJECT_ROOT.rglob(pattern)
        if not any(part in p.parts for part in skip)
    ]


def validate_unique_names(
    pattern: str, label: str, exclude_parts: Iterable[str] = ()
) -> bool:
    names = [p.name for p in iter_files(pattern, exclude_parts)]
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if duplicates:
        print(
            f"File naming error: every {label} must have a unique basename "
            f"(even across directories). Duplicates found: {duplicates}"
        )
    return not duplicates


def validate_filename(file_path: str) -> bool:
    name = Path(file_path).name
    result = True
    if "-" in name:
        report(
            file_path,
            f"dash (-) is not allowed; use underscore (_), "
            f"e.g. rename to '{file_path.replace('-', '_')}'",
        )
        result = False
    if " " in name:
        report(
            file_path,
            f"space is not allowed; use underscore (_), "
            f"e.g. rename to '{file_path.replace(' ', '_')}'",
        )
        result = False
    return result


#
# Notebook I/O
#


def load_notebook(path: str) -> "nbformat.NotebookNode":
    import nbformat

    return nbformat.read(path, as_version=_VERSION_MAJOR)


def save_notebook(path: str, nb: "nbformat.NotebookNode") -> None:
    import nbformat

    nbformat.validate(nb)
    nbformat.write(nb, path)


#
# Cell helpers
#


def iter_cells(
    nb: "nbformat.NotebookNode", cell_type: str = "markdown"
) -> Iterator[tuple[int, dict]]:
    for idx, cell in enumerate(nb.cells):
        if cell.get("cell_type") == cell_type:
            yield idx, cell


def get_cell_source(cell: dict) -> str:
    source = cell.get("source", [])
    if type(source) is str:
        return source
    elif type(source) is list:
        return "".join(source)
    else:
        raise ValueError(f"Unknown cell[source] type ({type(source)})")


#
# Reporting
#


def report(
    path: str,
    message: str,
    cell_idx: int | None = None,
    line: str = "",
    fixed: bool = False,
) -> None:
    tag = "fixed" if fixed else "error"

    location = path

    if cell_idx is not None:
        location += f" | cell {cell_idx}"

    if line.strip():
        snippet = line.strip()[:60]
        if len(line.strip()) > 60:
            snippet += "..."
        location += f', line "{snippet}"'

    print(f"{location}:")
    print(f"    {tag:8s}: {message}")
