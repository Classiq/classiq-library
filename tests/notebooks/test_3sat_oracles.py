from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("3sat_oracles", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # the `qmod` and `qprog` are defined in a function
    # need to rewrite the notebook in order to test it

    # test notebook content
    pass  # Todo
    # need to compare classiq times to qiskit times at some num_qubits value
