from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient
import numpy as np


@wrap_testbook(
    "classiq_chemistry_application",
    timeout_seconds=80,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for finding the ground state of a molecule using VQE.
    The test verifies that the classical optimizer converges to the expected ground state.
    """

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=6,  # actual width: 8
        expected_depth=300,  # actual depth: 166
    )

    # test notebook content
    assert (
        np.abs(tb.ref("optimizer_res") - tb.ref("expected_energy")) < 0.01
    ), "VQE did not converge to expected ground state."
    pass
