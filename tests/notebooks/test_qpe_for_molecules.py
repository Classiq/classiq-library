from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qpe_for_molecules", timeout_seconds=1332)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=10,  # actual width: 7
        expected_depth=85000,  # actual depth: 74356
    )

    # test notebook content
    solution = tb.ref("solution")
    energy_resolution = tb.ref("energy_resolution")

    exact_result = tb.ref("np.real(min( np.linalg.eig(operator.to_matrix())[0] ))")

    for sol in solution:
        assert sol - energy_resolution <= exact_result <= sol + energy_resolution
