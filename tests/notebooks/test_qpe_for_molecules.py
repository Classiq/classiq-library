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
        tb.ref_pydantic("qprog"),
        expected_width=16,  # actual width: 13
        expected_depth=50000,  # actual depth: 22412
    )

    # test notebook content
    solution_max_prob = tb.ref("max_prob_energy")
    solution_first_peak = tb.ref("measured_energy")
    resolution = tb.ref("2**(-QPE_SIZE)* normalization")

    exact_result = tb.ref("classical_sol")

    for sol in [solution_max_prob, solution_first_peak]:
        assert sol - resolution <= exact_result <= sol + resolution
