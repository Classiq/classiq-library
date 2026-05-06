import numpy as np

from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("classical_shadow_tomography", timeout_seconds=900)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # Pauli-shadow main: Bell state prep (H, X, CX) + RY/RZ per qubit.
    # Width = NUM_QUBITS = 2; depth/cx very small after transpilation.
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=4,  # actual: 2
        expected_depth=20,  # actual: ~6
        expected_cx_count=3,  # actual: 1
    )

    # ZZ on the |Phi^-> Bell state has true expectation -1 (sign depends on
    # the Bell state convention used by `prepare_bell_state(1, ...)`); the
    # Pauli-shadow protocol with N=400, div=2 should land within ~0.5 of
    # the truth at this sample size with very high probability.
    estimate = tb.ref("estimate")
    assert (
        abs(abs(estimate) - 1.0) < 0.5
    ), f"Pauli-shadow <ZZ> estimate off: got {estimate}, expected |.|≈1"

    # Clifford-shadow estimate should be tighter (every shot is informative).
    estimate_clifford = tb.ref("estimate_clifford")
    assert (
        abs(abs(estimate_clifford) - 1.0) < 0.5
    ), f"Clifford-shadow <ZZ> estimate off: got {estimate_clifford}"

    # Reconstructed density matrix invariants: 4x4, Hermitian, trace ~ 1.
    rho_hat = tb.ref_numpy("reconstructed_state")
    assert rho_hat.shape == (4, 4)
    assert np.allclose(rho_hat, rho_hat.conj().T, atol=0.1)
    assert abs(np.trace(rho_hat).real - 1.0) < 0.1

    # Shadow integrity: snapshot/ids sizes match num_snapshots and NUM_QUBITS.
    num_snapshots = tb.ref("num_snapshots")
    snapshots = tb.ref("snapshots")
    ids = tb.ref("ids")
    assert len(snapshots) == num_snapshots
    assert len(ids) == num_snapshots
    assert all(len(row) == 2 for row in snapshots)
    assert all(len(row) == 2 for row in ids)

    # Sample-complexity bound returns a positive snapshot count and >=1 chunks.
    n_required, k_div = tb.ref("required_snapshots")
    assert n_required > 0
    assert k_div >= 1
