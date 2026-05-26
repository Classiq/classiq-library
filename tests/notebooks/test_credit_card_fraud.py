from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("credit_card_fraud", timeout_seconds=1084)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # Pauli ZZ circuit — 1 qubit per feature (N_DIM=3)
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=3,  # actual width: 3
        expected_depth=50,  # actual depth: ~38
    )
    # quantum kernel test accuracy
    assert tb.ref("test_score") >= 0.85
    # quantum kernel prediction accuracy (true_labels assigned in the prediction cell)
    assert (
        tb.ref("sklearn.metrics.accuracy_score(predicted_labels, true_labels)") >= 0.85
    )
