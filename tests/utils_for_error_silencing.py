import logging
import re
from typing import Any

from nbclient.exceptions import CellExecutionError  # as type hint
from nbformat import NotebookNode  # as type hint

logger = logging.getLogger(__name__)


# a list of [error-name, regex-pattern-of-error-message]
# for example, to catch `ValueError("abcd")` add
#   ("ValueError", "abcd")
#   or
#   ("ValueError", "....")
ALLOWED_ERRORS: list[tuple[str, str]] = [
    ("ClassiqAPIError", ".*\\b429\\b.*"),
]

COLLECTED_SILENCED_ERRORS: list[str] = []


def create_hooks(notebook_name):
    # we have a function that defines 3 functions in order
    # to make those functions share a 'global' variable
    # but we want this variable to be global-per-notebook
    # thus, each @wrap_testbook creates it's own triplet

    did_the_notebook_raise_an_error_we_wish_to_ignore = False
    index = -1

    def my_on_cell_error(
        cell: NotebookNode, cell_index: int, execute_reply: dict[str, Any]
    ):
        # the caller is
        #   site-packages/nbclient/client.py:1062:async_execute_cell
        # the caller verifies that
        # - `execute_reply["content"]` is indeed a dict
        # - `execute_reply["content"]["status"]` is indeed "error"
        ename = execute_reply["content"].get("ename")
        evalue = execute_reply["content"].get("evalue")

        for error_name, error_pattern in ALLOWED_ERRORS:
            if ename == error_name and re.match(error_pattern, evalue):
                nonlocal did_the_notebook_raise_an_error_we_wish_to_ignore
                did_the_notebook_raise_an_error_we_wish_to_ignore = True
                nonlocal index
                index = cell_index

                logger.warning(
                    f"Silencing error: '{notebook_name}': '{error_name}'('{error_pattern}')"
                )
                logger.info(f"error message (cell {cell_index}): '{evalue}'")
                COLLECTED_SILENCED_ERRORS.append(
                    f"'{notebook_name}': '{error_name}'('{error_pattern}')"
                )

                break
        else:
            raise CellExecutionError.from_cell_and_msg(cell, execute_reply["content"])

    def my_on_cell_start(cell: NotebookNode, cell_index: int):
        if did_the_notebook_raise_an_error_we_wish_to_ignore:
            # just some verification
            print(cell_index > index)

            if cell.cell_type == "code":
                cell.source = ""

    def maybe_skip_the_entire_test_if_an_expected_error_we_want_to_silence_was_raised(
        func,
    ):
        # this will be a decorator for the test.
        # We cannot have it be: `if ...: return lambda no-op ; else return func`
        # since at the time in which the decorator decorates the test function,
        #   the notebook hasn't been run, thus we'll always get `did_..._raise = False`
        # thus, we create a function that will be evaluated "in order of decorators"
        # which promises that it will run after the `testbook` decorator
        #   thus making sure that the notebook finished running, and the error-silencing is done.
        def evaluate_only_when_called(*args, **kwargs):
            if did_the_notebook_raise_an_error_we_wish_to_ignore:
                return None
            else:
                return func(*args, **kwargs)

        return evaluate_only_when_called

    return (
        my_on_cell_error,
        my_on_cell_start,
        maybe_skip_the_entire_test_if_an_expected_error_we_want_to_silence_was_raised,
    )
