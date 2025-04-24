import json
import itertools
import base64
import pickle
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

from testbook.client import TestbookNotebookClient

_PATCHED = False


"""
Decorator explanation, from bottom to top

1 - skip decorator
this has to be the first, since the pytest decision of whether to skip this test has to be the first to run

2 - cd decorator
this has to come before testbook, since it changes the working directory in which testbook will run the notebook

3 - testbook
that's the main decorator

4 - patch client
this one aims to set `tb.__repr__`
but since `__repr__` is always called from the class's __dict__, rather than the instance's
than we have to use `_path_testbook` (which exists for `ref_numpy`. So it's handy that it's already here)
and add a property - `self._notebook_name`
adding this property must come after the testbook decorator
since before the decorator, the function takes 0 arguments
and after the decorator, it takes 1 - `tb`.
"""


def wrap_testbook(notebook_name: str, timeout_seconds: float = 10) -> Callable:
    def inner_decorator(func: Callable) -> Any:
        _patch_testbook()

        notebook_path = resolve_notebook_path(notebook_name)

        for decorator in [
            _build_patch_testbook_client_decorator(notebook_name),
            testbook(notebook_path, execute=True, timeout=timeout_seconds),
            _build_cd_decorator(notebook_path),
            _build_skip_decorator(notebook_path),
        ]:
            func = decorator(func)
        return func

    return inner_decorator


def _build_patch_testbook_client_decorator(notebook_name: str) -> Callable:
    def patch_testbook_client_decorator(func: Callable) -> Any:
        def inner(*args: Any, **kwargs: Any) -> Any:
            for arg in itertools.chain(args, kwargs.values()):
                if isinstance(arg, TestbookNotebookClient):
                    arg._notebook_name = notebook_name

            return func(*args, *kwargs)

        return inner

    return patch_testbook_client_decorator


# The purpose of the `cd_decorator` is to execute the test in the same folder as the `ipynb` file
#   so that relative files (images, csv, etc.) will be available
def _build_cd_decorator(file_path: str) -> Callable:
    def cd_decorator(func: Callable) -> Any:
        def inner(*args: Any, **kwargs: Any) -> Any:
            previous_dir = os.getcwd()
            os.chdir(ROOT_DIRECTORY)
            os.chdir(os.path.dirname(file_path))

            result = func(*args, **kwargs)

            os.chdir(previous_dir)
            return result

        return inner

    return cd_decorator


def _build_skip_decorator(notebook_path: str) -> Callable:
    notebook_name = os.path.basename(notebook_path)
    return pytest.mark.skipif(
        should_skip_notebook(notebook_name),
        reason="Didn't change",
    )


def _patch_testbook() -> None:
    global _PATCHED

    if _PATCHED:
        return

    def ref_numpy(self, obj_name: str) -> Any:
        """
        s = base64.b64encode( pickle.dumps(obj) ).decode()
        result = pickle.loads(base64.b64decode(s))
        result == obj
        """

        string = self.ref(
            f"__import__('base64').b64encode(__import__('pickle').dumps({obj_name})).decode()"
        )
        result = pickle.loads(base64.b64decode(string))
        return result

    TestbookNotebookClient.ref_numpy = ref_numpy

    original_repr = TestbookNotebookClient.__repr__

    def new_repr(self) -> str:
        if hasattr(self, "_notebook_name"):
            return f"<{self.__class__.__name__} of notebook '{self._notebook_name}'>"
        else:
            return original_repr(self)

    TestbookNotebookClient.__repr__ = new_repr

    _PATCHED = True


def validate_quantum_model(model: str) -> None:
    # currently that's some dummy test - only checking that it's a valid dict
    assert isinstance(json.loads(model), dict)


def validate_quantum_program_size(
    qp: QuantumProgram,
    expected_width: int | None = None,
    expected_depth: int | None = None,
    compare_to: QuantumProgram | None = None,
    allow_zero_size: bool = False,
) -> None:
    if compare_to is not None:
        other_qp = compare_to

        other_width = other_qp.data.width

        assert other_qp.transpiled_circuit is not None  # for mypy
        other_depth = other_qp.transpiled_circuit.depth

        return validate_quantum_program_size(qp, other_width, other_depth)

    actual_width = qp.data.width
    if expected_width is not None:
        assert (
            actual_width <= expected_width
        ), f"The width of the circuit changed! (for the worse!). From {expected_width} to {actual_width}"
    assert allow_zero_size or actual_width > 0, "Got a 0-width circuit."

    assert qp.transpiled_circuit is not None  # for mypy
    actual_depth = qp.transpiled_circuit.depth
    if expected_depth is not None:
        assert (
            actual_depth <= expected_depth
        ), f"The depth of the circuit changed! (for the worse!). From {expected_depth} to {actual_depth}"
    assert allow_zero_size or actual_depth > 0, "Got a 0-depth circuit."
