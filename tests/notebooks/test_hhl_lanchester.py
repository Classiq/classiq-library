from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("hhl_lanchester", timeout_seconds=450)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_hhl_swap_test"))
    validate_quantum_model(tb.ref("qmod_hhl_basic"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_hhl_swap"),
        expected_width=tb.ref("MAX_WIDTH_SWAP_TEST"),
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_hhl_basic"),
        expected_width=tb.ref("MAX_WIDTH_BASIC"),
    )

    # Fidelity between basic HHL and classical solutions: 0.9805806756909201
    assert 0.93 <= tb.ref("fidelity_basic") <= 1
    assert 0.98 <= tb.ref("fidelity") <= 1
