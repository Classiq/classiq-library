from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qsvm_pauli_feature_map", timeout_seconds=68)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    # test models
    validate_quantum_model(tb.ref("QSVM_PAULI_Z_ZZ"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=2,  # actual width: 2
        expected_depth=30,  # actual depth: 30
    )

    # test notebook content
    assert tb.ref("test_score") == 1

    success_rate = tb.ref(
        "100 * np.count_nonzero(predicted_labels == predict_labels) / len(predicted_labels)"
    )
    assert success_rate == 100
