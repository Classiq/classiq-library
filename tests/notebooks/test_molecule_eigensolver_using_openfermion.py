from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient
import numpy as np


@wrap_testbook(
    "molecule_eigensolver_using_openfermion",
    timeout_seconds=120,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for finding the ground state of a molecule using VQE.
    The test verifies that the classical optimizer converges to the expected ground state.
    """
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=8,  # actual width: 8
        expected_depth=650,  # actual depth: 484
    )

    # test notebook content
    assert (
        np.abs(tb.ref("optimizer_res") - tb.ref("expected_energy")) < 0.01
    ), "VQE did not converge to expected ground state."
    pass
