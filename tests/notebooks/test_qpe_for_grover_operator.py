from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qpe_for_grover_operator", timeout_seconds=2000)  # bump from 1000
def test_notebook(tb: TestbookNotebookClient) -> None:
    # the `qmod`s and `qprog`s are in a for-loop
    # need to rewrite the notebook in order to test them

    # test notebook content
    for depth_classiq_optimize_depth, depth_classiq_optimize_width, depth_qiskit in zip(
        tb.ref("classiq_depths_ae_opt_depth_max_width"),
        tb.ref("classiq_depths_ae_opt_width"),
        tb.ref("qiskit_depths_ae"),
    ):
        assert (
            depth_classiq_optimize_depth < depth_classiq_optimize_width < depth_qiskit
        )
