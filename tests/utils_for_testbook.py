import base64
import json
import os
import pytest
import pickle
import re
from typing import Any, Callable

from testbook import testbook  # type: ignore[import]
from testbook.client import TestbookNotebookClient  # type: ignore[import]
from utils_for_tests import resolve_notebook_path, should_test_notebook

from classiq.interface.generator.quantum_program import QuantumProgram


def execute_testbook_with_timeout(
    notebook_name: str, timeout_seconds: float = 10
) -> Callable:
    def inner_decorator(func: Callable) -> Any:
        notebook_path = resolve_notebook_path(notebook_name)

        if not should_test_notebook(notebook_path):
            pytest.skip("Skipped")

        for decorator in [
            testbook(notebook_path, execute=True, timeout=timeout_seconds),
            _build_cd_decorator(notebook_path),
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
            os.chdir(os.path.dirname(file_path))

            func(*args, **kwargs)

            os.chdir(previous_dir)

        return inner

    return cd_decorator


def assert_valid_model(model: str) -> None:
    # currently that's some dummy test - only checking that it's a valid dict
    assert isinstance(json.loads(model), dict)


def assert_unchanged_size(
    quantum_program: str,
    expected_width: int | None = None,
    expected_depth: int | None = None,
) -> None:
    qp = QuantumProgram.model_validate_json(quantum_program)

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


def get_pydantic_object(tb: TestbookNotebookClient, variable_name: str) -> Any:
    try:
        # get the name, plus full path, of the class of the value
        output_type_raw: str = tb.ref(f"str(type({variable_name}))")
        match = re.match("<class '(.*?)'>", output_type_raw)
        assert match is not None
        output_type: str = match.group(1)
        # example output_type: "classiq.interface.executor.execution_result.TaggedExecutionDetails""

        # now, we need to dynamically get that class.
        # so we will call `__import__(classiq.something.some_file)`
        import_names = output_type.split(".")
        assert len(import_names) >= 2  # at least `some_file.some_class`
        # `__import__(a.b.c)` returns a pointer to `a`
        obj_class = __import__(".".join(import_names[:-1]))
        # so we call `getattr` on all the inner files
        # and the last `getattr` will get the class itself
        for name in import_names[1:]:
            obj_class = getattr(obj_class, name)

        # after getting the class, we call `.json` on the object, and feed it into `.parse_raw`
        return obj_class.model_validate_json(
            tb.ref(f"{variable_name}.model_dump_json()")
        )
    except Exception:
        # if that fails, call pickle
        pickle_string = tb.ref(
            f"__import__('base64').b64encode(__import__('pickle').dumps({variable_name})).decode('utf-8')"
        )
        return pickle.loads(base64.b64decode(pickle_string))  # noqa: S301


def get_results(
    tb: TestbookNotebookClient, results_variable_name: str = "results"
) -> list[Any]:
    """
    Warning: difficult code ahead.
    Why do we have this function?
    since testbook, like any communication with jupyter notebook kernel, can only return strings
    thus, when we ask to get a variable, we actually get a `json.dumps` version of it
    for most variables all will be fine
    but for pydantic types, then pydantic overrides its behavior
    thus, `tb.ref` will fail.
    and so, we override it : we get the `obj.json()` of the obj we wish to get, and call `.parse_raw`
    """

    # we're expecting `execute(qprog).result()` to return a list
    type_of_results = tb.ref(f"type({results_variable_name}).__name__")
    # we can't call `isinstance`, since we don't get a pointer to the class, but the string of `repr(type(...))`
    #   thus, we request `type(...).__name__`, and to strcmp
    assert type_of_results == "list"

    # a list comprehension
    return [
        get_pydantic_object(tb, f"{results_variable_name}[{i}]")
        for i in range(tb.ref(f"len({results_variable_name})"))
    ]
