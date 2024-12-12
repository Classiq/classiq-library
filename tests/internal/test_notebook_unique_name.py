from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).parents[2]


def test_unique_notebook_name():
    all_notebooks = ROOT.rglob("*.ipynb")
    assert _are_all_base_names_unique(all_notebooks)


def test_unique_qmod_name():
    all_qmods = ROOT.rglob("*.qmod")
    assert _are_all_base_names_unique(all_qmods)


def _are_all_base_names_unique(files: Iterable[Path]) -> bool:
    base_names = [f.name for f in files]
    return len(base_names) == len(set(base_names))
