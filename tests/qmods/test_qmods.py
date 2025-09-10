import json
import os
from pathlib import Path
from typing import Iterator

import pytest
from _pytest.mark.structures import ParameterSet
from classiq import Constraints, Preferences, synthesize
from classiq.interface.exceptions import ClassiqAPIError
from classiq.interface.model.model import Model

ROOT_DIRECTORY = Path(__file__).parents[2]
CHANGED_QMODS = os.environ.get("LIST_OF_QMOD_CHANGED", "").split()


def _should_test_file(qmod_file: Path) -> bool:
    return str(qmod_file.relative_to(ROOT_DIRECTORY)) in CHANGED_QMODS


def all_qmods_params() -> Iterator[ParameterSet]:
    iterator = ROOT_DIRECTORY.rglob("*.qmod")
    if os.environ.get("SHOULD_TEST_ALL_FILES", "") != "true":
        iterator = filter(_should_test_file, iterator)

    return (pytest.param(qmod_file, id=qmod_file.name) for qmod_file in iterator)


@pytest.mark.parametrize("qmod_file", all_qmods_params())
def test_qmod(qmod_file: Path) -> None:
    from qmod_parser.public.functions import parse_model

    synthesis_options_file = qmod_file.with_suffix(".synthesis_options.json")
    assert (
        synthesis_options_file.is_file()
    ), f"Missing {synthesis_options_file.name} file for {qmod_file.name}"
    synthesis_options = json.loads(synthesis_options_file.read_text())
    qmod_text = qmod_file.read_text()
    model: Model = parse_model(qmod_text)
    if (constraints := synthesis_options.get("constraints")) is not None:
        model.constraints = Constraints.model_validate(constraints)

    if (preferences := synthesis_options.get("preferences")) is not None:
        model.preferences = Preferences.model_validate(preferences)

    try:
        synthesize(model.get_model())
    except ClassiqAPIError as e:
        raise AssertionError(f"Failed to synthesize {qmod_file.name}: {e}") from e
