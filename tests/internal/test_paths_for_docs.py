import os
import subprocess
from pathlib import Path

import yaml

ROOT = Path(subprocess.getoutput("git rev-parse --show-toplevel"))  # noqa: S605
PATHS_FOR_DOCS = ROOT / ".internal" / "paths_for_docs.yaml"
DOCS_DIRECTORIES = ROOT / ".internal" / "docs_directories.txt"

"""
This test checks if all paths in the files_to_copy_for_docs.yaml file exist.
The files are required for building the documentation, and are copied to the
docs after the Jupyter to Markdown conversion.
"""


def test_paths_to_copy_for_docs():
    with open(PATHS_FOR_DOCS, "r") as file:
        paths_to_copy = yaml.safe_load(file)

    missing_paths: list[str] = []
    for path in paths_to_copy.values():
        # png files are byproduct of the conversion from Jupyter to Markdown and cannot
        # be checked for existence in advance
        if not (ROOT / path).exists() and Path(path).suffix != ".png":
            missing_paths.append(path)

    assert not missing_paths, f"The following paths do not exist: {missing_paths}"


def test_docs_directories():
    dir_list = DOCS_DIRECTORIES.read_text().splitlines()
    assert all(
        (ROOT / path).exists() for path in dir_list
    ), f"Make sure all directories in {DOCS_DIRECTORIES} actually exist"
