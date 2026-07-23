import base64
import itertools
import json
import os
import pickle
import re
import shutil
import warnings
from dataclasses import dataclass, field
from typing import Any, Callable
import classiq

import pytest
from testbook import testbook
from testbook.client import TestbookNotebookClient

from tests.utils_for_tests import (
    ROOT_DIRECTORY,
    resolve_notebook_path,
    should_skip_notebook,
)
from tests.utils_for_error_silencing import create_hooks, ALLOWED_ERRORS

from classiq.interface.generator.quantum_program import QuantumProgram

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

5 - if the notebook raised an error we wish to ignore then skip the test
more documentation in the decorator implementation
note that this decorator can be placed pretty much everywhere post `testbook`
as it only requires it's inner function to be run after the notebook was executed

Other - replacements
We allow running "regex replace" on the ipynb file, in order to ease the load on the tests.
"""


def wrap_testbook(
    notebook_name: str,
    timeout_seconds: float = 10,
    replacements_regex: list[tuple[str, str]] | None = None,
    replacements_variables: list[tuple[str, str]] | None = None,
) -> Callable:
    def inner_decorator(func: Callable) -> Any:
        _patch_testbook()

        notebook_path = resolve_notebook_path(notebook_name)

        (
            my_on_cell_error,
            my_on_cell_start,
            maybe_skip_the_entire_test_if_an_expected_error_we_want_to_silence_was_raised,
        ) = create_hooks(notebook_name)

        with NotebookEdit(
            notebook_path, replacements_regex, replacements_variables
        ) as nr:
            for decorator in [
                maybe_skip_the_entire_test_if_an_expected_error_we_want_to_silence_was_raised,
                _build_patch_testbook_client_decorator(notebook_name),
                testbook(
                    notebook_path,
                    execute=True,
                    timeout=timeout_seconds,
                    allow_error_names=[i[0] for i in ALLOWED_ERRORS],
                    on_cell_error=my_on_cell_error,
                    on_cell_start=my_on_cell_start,
                ),
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


FILE_COPY_SUFFIX = ".pre_test_backup"

DEFAULT_CODE_INJECTIONS = [
    # disabling all `!` commands.
    "get_ipython().system = lambda *args: print('no !pip allowed')",
]
_DEFAULT_CODE_INJECTIONS = field(default_factory=lambda: DEFAULT_CODE_INJECTIONS)


@dataclass
class NotebookEdit:
    file_path: str
    replacements_regex: list[tuple[str, str]] | None
    replacements_variables: list[tuple[str, str]] | None
    code_injection_at_start: list[str] = _DEFAULT_CODE_INJECTIONS

    def __post_init__(self):
        self.was_file_copied = False

        self.replacements = self._group_replacements()

    @property
    def file_path_copied(self):
        return self.file_path + FILE_COPY_SUFFIX

    def _group_replacements(self) -> list[tuple[str, str]]:
        replacements = []

        if self.replacements_regex:
            replacements.extend(self.replacements_regex)

        if self.replacements_variables:
            replacements.extend(
                [
                    (f"({variable}\\s*=\\s*)", f"\\1 {new_value}  # ")
                    for variable, new_value in self.replacements_variables
                ]
            )

        return replacements

    @property
    def should_edit(self):
        return self.replacements or self.code_injection_at_start

    def __enter__(self):
        if self.should_edit:
            self._backup_notebook()
            self.was_file_copied = True

            if self.replacements:
                used_replacements = self._replace_notebook_content()
                assert (
                    self.replacements == used_replacements
                ), f"Not all replacements given were used. The onces used are: {used_replacements}. The unused are {[r for r in self.replacements if r not in used_replacements]}"

            self._inject_code()

        return self

    def __exit__(self, *args, **kwargs):
        if not self.should_edit:
            return
        if not self.was_file_copied:
            return  # maybe raise? every `should_edit` must set `was_file_copied=True`

        self._restore_notebook_from_backup()

    def _backup_notebook(self) -> None:
        assert os.path.isfile(
            self.file_path
        ), f"This should not happen. '{self.file_path=}' was supposed to be a file. Aborting backup."

        assert not os.path.exists(
            self.file_path_copied
        ), f"notebook copy (for tests) was not cleaned properly. ({self.file_path_copied}). Aborting backup"
        shutil.copy(self.file_path, self.file_path_copied)
        assert os.path.exists(self.file_path_copied)

    def _replace_notebook_content(self) -> list[tuple[str, str]]:
        with open(self.file_path, "r") as f:
            content = f.read()

        used_replacements = []

        for pattern, replace in self.replacements:
            new_content = re.sub(pattern, replace, content)
            if new_content != content:
                used_replacements.append((pattern, replace))
            content = new_content

        # write edited content
        with open(self.file_path, "w") as f:
            f.write(content)

        return used_replacements

    def _inject_code(self) -> None:
        with open(self.file_path, "r") as f:
            notebook = json.load(f)

        for index, source_code in enumerate(self.code_injection_at_start):
            # split so that each line retains its "\n"
            splitted_source_code: list[str] = re.split("(?<=\\n)\\b", source_code)
            cell = {
                "cell_type": "code",
                "execution_count": 1,
                "id": f"injected_cell_{index}",
                "metadata": {},
                "outputs": [],
                "source": splitted_source_code,
            }
            notebook["cells"].insert(0, cell)

        with open(self.file_path, "w") as f:
            json.dump(notebook, f, indent=1)

    def _restore_notebook_from_backup(self) -> None:
        assert os.path.isfile(
            self.file_path_copied
        ), f"This should not happen. '{self.file_path_copied=}' was supposed to be a file. Aborting restore."
        shutil.move(self.file_path_copied, self.file_path)
        assert not os.path.exists(
            self.file_path_copied
        ), f"notebook copy (for tests) was not cleaned properly. ({self.file_path_copied}). Aborting restore."


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

    def ref_pickle(self, obj_name: str) -> Any:
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

    TestbookNotebookClient.ref_numpy = ref_pickle
    TestbookNotebookClient.ref_pydantic = ref_pickle

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
    quantum_program: QuantumProgram,
    expected_width: int | None = None,
    expected_depth: int | None = None,
    expected_cx_count: int | None = None,
    compare_to: QuantumProgram | None = None,
    allow_zero_size: bool = False,
) -> None:
    if compare_to is not None:
        assert compare_to.transpiled_circuit is not None  # for mypy
        _metrics = classiq.get_transpiled_circuit_metrics(compare_to).circuit_metrics
        return validate_quantum_program_size(
            quantum_program,
            expected_width=compare_to.data.width,
            expected_depth=_metrics.depth,
            expected_cx_count=_metrics.count_ops.get("cx", 0),
        )

    actual_width = quantum_program.data.width
    _validate_size(actual_width, expected_width, "width", allow_zero_size)

    if quantum_program.transpiled_circuit is not None:
        _metrics = classiq.get_transpiled_circuit_metrics(
            quantum_program
        ).circuit_metrics

        actual_depth = _metrics.depth
        _validate_size(actual_depth, expected_depth, "depth", allow_zero_size)

        actual_cx_count = _metrics.count_ops.get("cx", 0)
        # allow_zero_size set to True here since there may be valid circuits with no CX gate.
        _validate_size(actual_cx_count, expected_cx_count, "cx_count", True)
    else:
        if expected_depth is not None:
            warnings.warn("Cannot validate depth, since there is no transpiled_circuit")
        if expected_cx_count is not None:
            warnings.warn(
                "Cannot validate cx count, since there is no transpiled_circuit"
            )


def _validate_size(actual: int, expected: int | None, name: str, allow_zero_size: bool):
    if expected is not None:
        assert (
            actual <= expected
        ), f"The {name} of the circuit changed! (for the worse!). From {expected} to {actual}"

    assert allow_zero_size or actual > 0, f"Got a 0-{name} circuit."
