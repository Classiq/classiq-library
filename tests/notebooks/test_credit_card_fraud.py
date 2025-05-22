from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("credit_card_fraud", timeout_seconds=1084)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("QSVM_FRAUD_BLOCH_SHPERE"))
    validate_quantum_model(tb.ref("QSVM_FRAUD_PAULI_ZZ"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=5,  # actual width: 3
        expected_depth=50,  # actual depth: 38
    )

    # test notebook content

    # true_labels = np.array(selected_prediction_true_labels.values.tolist())
    # sklearn.metrics.accuracy_score(predicted_labels, true_labels)
    accuracy = tb.ref(
        "sklearn.metrics.accuracy_score(predicted_labels, np.array(selected_prediction_true_labels.values.tolist()))"
    )
    assert accuracy >= 0.9
