import json
import os
from typing import Any, Callable
import pytest

from testbook import testbook
from tests.utils_for_tests import (
    resolve_notebook_path,
    should_skip_notebook,
    ROOT_DIRECTORY,
)

from classiq.interface.generator.quantum_program import QuantumProgram


def wrap_testbook(notebook_name: str, timeout_seconds: float = 10) -> Callable:
    def inner_decorator(func: Callable) -> Any:
        notebook_path = resolve_notebook_path(notebook_name)

        for decorator in [
            testbook(notebook_path, execute=True, timeout=timeout_seconds),
            _build_cd_decorator(notebook_path),
            _build_skip_decorator(notebook_path),
        ]:
            func = decorator(func)
        return func

    return inner_decorator


# The purpose of the `cd_decorator` is to execute the test in the same folder as the `ipynb` file
#   so that relative files (images, csv, etc.) will be available
def _build_cd_decorator(file_path: str) -> Callable:
    def cd_decorator(func: Callable) -> Any:
        def inner(*args: Any, **kwargs: Any) -> Any:
            previous_dir = os.getcwd()
            os.chdir(ROOT_DIRECTORY)
            os.chdir(os.path.dirname(file_path))

            func(*args, **kwargs)

            os.chdir(previous_dir)

        return inner

    return cd_decorator


def _build_skip_decorator(notebook_path: str) -> Callable:
    notebook_name = os.path.basename(notebook_path)
    return pytest.mark.skipif(
        should_skip_notebook(notebook_name),
        reason="Didn't change",
    )


def validate_quantum_model(model: str) -> None:
    # currently that's some dummy test - only checking that it's a valid dict
    assert isinstance(json.loads(model), dict)


def validate_quantum_program_size(
    quantum_program: str | QuantumProgram,
    expected_width: int | None = None,
    expected_depth: int | None = None,
) -> None:
    qp = QuantumProgram.from_qprog(quantum_program)

    actual_width = qp.data.width
    if expected_width is not None:
        assert (
            actual_width <= expected_width
        ), f"The width of the circuit changed! (for the worse!). From {expected_width} to {actual_width}"

    assert qp.transpiled_circuit is not None  # for mypy
    actual_depth = qp.transpiled_circuit.depth
    if expected_depth is not None:
        assert (
            actual_depth <= expected_depth
        ), f"The depth of the circuit changed! (for the worse!). From {expected_depth} to {actual_depth}"
