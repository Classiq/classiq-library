from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

import numpy as np


@wrap_testbook("molecule_eigensolver", timeout_seconds=84)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_hwea"))
    validate_quantum_model(tb.ref("serialized_chemistry_model"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_hwea"),
        expected_width=4,  # actual width: 4
        expected_depth=15,  # actual depth: 13
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_ucc"),
        expected_width=1,  # actual width: 1
        expected_depth=3,  # actual depth: 3
    )

    # test notebook content
    # operator = tb.ref("operator.to_matrix()")
    # w, v = np.linalg.eig(operator)
    # exact_result = np.real(min(w))
    exact_result = tb.ref("np.real(min( np.linalg.eig(operator.to_matrix())[0] ))")

    chemistry_result_dict = tb.ref("chemistry_result_dict")
    vqe_result = chemistry_result_dict["energy"]

    assert np.isclose(
        vqe_result, exact_result, atol=0.02
    )  # should be 0.01, but sometimes gets larger
