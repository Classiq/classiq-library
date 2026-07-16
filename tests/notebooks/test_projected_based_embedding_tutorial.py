import numpy as np

from testbook.client import TestbookNotebookClient

from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)


@wrap_testbook("projected_based_embedding_tutorial", timeout_seconds=2400)
def test_notebook(tb: TestbookNotebookClient) -> None:
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=None,
        expected_depth=None,
        expected_cx_count=None,
    )

    # Embedding partition: all 10 electrons assigned to fragment, none to environment
    assert tb.ref("mean_field_data.n_electrons_A") == 10
    assert tb.ref("mean_field_data.n_electrons_B") == 0

    # Active-space shape: (24 AOs, 8 MOs) for cc-pVDZ water
    c_shape = tb.ref("C_active.shape")
    assert c_shape == [24, 8]

    # Qubit counts before and after tapering
    assert tb.ref("num_qubits") == 14

    # Validation checks all pass
    for passed in tb.ref("[v[0] for v in calc.validation_results.values()]"):
        assert passed

    # DFT-in-DFT reproduces full-system energy to high precision
    assert (
        tb.ref("calc.validation_results[ValidationCheck.DFT_IN_DFT][1]['error']")
        < 1e-10
    )

    # VQE energy is above (or close to) the exact diagonalization ground state
    opt_energy = tb.ref("opt_energy")
    ground_state_energy = tb.ref("ground_state_energy")
    assert opt_energy >= ground_state_energy - 0.1

    # VQE relative error below 5%
    rel_error = abs((opt_energy - ground_state_energy) / ground_state_energy)
    assert rel_error < 0.05

    # Final WF-in-DFT total energy is in a physically reasonable range (Ha)
    e_total = tb.ref("E_total")
    assert -80.0 < e_total < -70.0
