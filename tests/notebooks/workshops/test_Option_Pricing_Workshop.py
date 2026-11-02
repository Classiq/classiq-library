from classiq import assign_parameters
from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("Option_Pricing_Workshop", timeout_seconds=400)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    # IQAE leaves the number of Grover iterations, k, as a parameter; bind it
    # to measure the circuit size, since parametric programs can't be transpiled.
    validate_quantum_program_size(
        assign_parameters(tb.ref_pydantic("qprog"), {"k": 1}),
        expected_width=15,  # actual width: 7
        expected_depth=1600,  # actual depth: 1395
    )

    # test notebook content
    assert tb.ref_numpy(
        "np.isclose(measured_payoff, expected_payoff, atol=10 * (condidence_interval[1] - condidence_interval[0]))"
    )
