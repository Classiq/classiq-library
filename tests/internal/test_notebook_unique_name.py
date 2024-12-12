from collections import Counter
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).parents[2]


def test_unique_notebook_name():
    all_notebooks = ROOT.rglob("*.ipynb")
    assert not duplicate_base_names(all_notebooks)


def test_unique_qmod_name():
    all_qmods = ROOT.rglob("*.qmod")
    assert not duplicate_base_names(all_qmods)


def duplicate_base_names(files: Iterable[Path]) -> bool:
    base_names = [f.name for f in files]
    return [name for name, count in Counter(base_names).items() if count > 1]
