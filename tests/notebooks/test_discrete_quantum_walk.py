from classiq import assign_parameters
from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("discrete_quantum_walk", timeout_seconds=900)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    validate_quantum_model(tb.ref("qmod_3"))

    # test quantum programs
    # qprog_1/2/3 all have a runtime `t` parameter; get_transpiled_circuit_metrics
    # requires it bound first. Bind to t=1 (a single walk step) purely to measure
    # circuit structure - the notebook itself samples with larger t values.
    validate_quantum_program_size(
        assign_parameters(tb.ref_pydantic("qprog_1"), {"t": 1}),
        expected_width=18,  # actual width: 8
        expected_depth=800,  # actual depth: 177
    )
    validate_quantum_program_size(
        assign_parameters(tb.ref_pydantic("qprog_2"), {"t": 1}),
        expected_width=18,  # actual width: 8
        expected_depth=800,  # actual depth: 177
    )
    validate_quantum_program_size(
        assign_parameters(tb.ref_pydantic("qprog_3"), {"t": 1}),
        expected_width=8,  # actual width: 6
        expected_depth=60,  # actual depth: 46
    )

    # sanity check on the hypercube hitting-probability result (actual ~0.57 vs ~0.06):
    # loose bounds, just to catch a regression like a raw-bitstring key mismatch
    # silently zeroing out the result (see git history)
    prob_corner_quantum = tb.ref("prob_corner")
    prob_corner_classical = tb.ref("prob_corner_classical")
    assert (
        prob_corner_quantum > 0.3
    ), f"Quantum hitting probability at the corner is suspiciously low: {prob_corner_quantum}"
    assert prob_corner_quantum > prob_corner_classical, (
        "The quantum walk should reach the opposite corner with higher probability "
        f"than the classical walk ({prob_corner_quantum} vs {prob_corner_classical})"
    )
