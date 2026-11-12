from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("skqd", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=12,  # 2 * (L + 1) qubits, with L = 5 bath sites
        expected_depth=450,  # upper-bound guard; actual 397
    )

    # test notebook content
    E_skqd = tb.ref("E_skqd")
    E_exact = tb.ref("E_exact")

    # model regression: the exact ground energy of this SIAM instance is classical and
    # deterministic, so it pins the Hamiltonian construction / mapping.
    assert abs(E_exact - (-9.142690)) < 1e-4, f"exact ground energy changed: {E_exact}"

    # variational bound: subspace diagonalization can never go below the true ground energy.
    assert (
        E_skqd >= E_exact - 1e-9
    ), "SKQD energy below exact — variational bound violated"

    # accuracy: the sample-based estimate should stay close to exact for the default setup.
    assert (
        abs(E_skqd - E_exact) < 5e-2
    ), f"SKQD error too large: {E_skqd - E_exact:+.2e}"
