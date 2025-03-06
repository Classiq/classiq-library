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
        # got one error of: 0.5603086719315014 < 0.5586003448231571
        # got another   of: (0.31375670875018297 + 0.01) < 0.3158037121175521
        assert fidelity_classiq + 0.05 < fidelity_qiskit

    for depth_classiq, depth_qiskit in zip(
        tb.ref("classiq_depths"),
        tb.ref("qiskit_depths"),
    ):
        assert depth_classiq < depth_qiskit
