from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("Option_Pricing_Workshop", timeout_seconds=400)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=15,  # actual width: 8
        expected_depth=10000,  # actual depth: 8934
    )

    # test notebook content
    assert tb.ref_numpy(
        "np.isclose(measured_payoff, expected_payoff, atol=10 * (condidence_interval[1] - condidence_interval[0]))"
    )
