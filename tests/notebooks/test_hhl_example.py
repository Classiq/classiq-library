from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("hhl_example", timeout_seconds=800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # the `qmod`s and `qprog`s are defined in a function.
    # need to rewrite the notebook in order to test it

    # test notebook content
    for fidelity_classiq, fidelity_qiskit in zip(
        tb.ref("classiq_fidelities"),
        tb.ref("qiskit_fidelities"),
    ):
        assert fidelity_classiq >= fidelity_qiskit - 0.02

    for depth_classiq, depth_qiskit in zip(
        tb.ref("classiq_depths"),
        tb.ref("qiskit_depths"),
    ):
        assert depth_classiq < depth_qiskit
