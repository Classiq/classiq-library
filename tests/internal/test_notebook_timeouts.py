from pathlib import Path
import subprocess

import pytest
import yaml

Seconds = float

ROOT = Path(__file__).parents[2]
TIMEOUTS_FILE = "timeouts.yaml"
TIMEOUTS_PATH = ROOT / "tests" / "resources" / TIMEOUTS_FILE


@pytest.fixture
def timeouts() -> dict[str, float]:
    try:
        with TIMEOUTS_PATH.open("r") as fobj:
            return yaml.safe_load(fobj)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "Make sure not to alter the timeout file without consent from Classiq's R&D team."
        ) from e


def _can_skip(filename: Path) -> bool:
    if TIMEOUTS_FILE == filename.suffix or filename.suffix not in [".ipynb", ".qmod"]:
        return True
    if filename.parts[0] == "functions" and len(filename.parts[0]) > 1:
        if filename.parts[1] in ("function_declarations", "open_library_definitions"):
            return True
    return False


def test_notebook_timeouts(timeouts: dict[str, float]) -> None:
    missing_notebooks: list[Path] = []
    for file_path in ROOT.rglob("*"):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(ROOT)
        if _can_skip(relative_path):
            continue
        if str(relative_path) not in timeouts:
            missing_notebooks.append(file_path)

    assert (
        not missing_notebooks
    ), f"Timeouts are missing for the following notebooks: {missing_notebooks}"


def test_unused_timeouts(timeouts: dict[str, float]) -> None:
    unused_timeouts: list[str] = []
    for notebook in timeouts:
        full_notebook_path = ROOT / notebook
        if not full_notebook_path.exists():
            unused_timeouts.append(notebook)

    assert (
        not unused_timeouts
    ), f"Timeouts are unused for the following notebooks: {unused_timeouts}"
