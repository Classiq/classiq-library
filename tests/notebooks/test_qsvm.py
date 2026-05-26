from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qsvm", timeout_seconds=360)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    Tests the QSVM notebook with two examples:
    1. Bloch sphere feature map on linearly separable data — perfect accuracy expected.
    2. Pauli ZZ and Bloch sphere feature maps on Iris versicolor vs virginica (petal features),
       with a classical RBF SVM as baseline.
    """
    # Example 1: Bloch circuit — 1 qubit encodes a 2-feature data point
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_bloch"),
        expected_width=1,
        expected_depth=10,
    )
    # Example 2: Pauli ZZ circuit — 1 qubit per feature (2 qubits for 2D data)
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_pauli"),
        expected_width=2,
        expected_depth=50,
    )
    # Example 2: Bloch circuit - 1 qubit encodes a 2-feature data point
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_bloch_2"),
        expected_width=1,
        expected_depth=10,
    )
    # Example 1: Bloch achieves near-perfect accuracy on linearly separable data
    assert tb.ref("test_score") >= 0.95
    # Example 2: Pauli ZZ outperforms Bloch on Iris; both tolerate 10% variability
    assert tb.ref("test_score_pauli") >= 0.8
    assert tb.ref("test_score_bloch") >= 0.7
    # Classical RBF sanity check — if this drops, the dataset likely changed
    assert tb.ref("test_score_rbf") >= 0.8
