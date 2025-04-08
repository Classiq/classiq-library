from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("3sat_oracles", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:

    num_models = len(tb.ref("qmods"))

    for i in range(num_models):
        # test models
        validate_quantum_model(tb.ref("qmods")[i])
        # TODO test quantum programs with transpilation is "none"

    # test notebook content
    for i in range(num_models):
        assert (
            tb.ref("cl_times")[i] < 30
        )  # actual time is less than 15 sec for all models
