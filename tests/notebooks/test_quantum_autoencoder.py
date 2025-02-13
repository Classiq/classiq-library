from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "quantum_autoencoder",
    timeout_seconds=120,
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """
    # test models
    validate_quantum_model(tb.ref("ae_qmod"))
    validate_quantum_model(tb.ref("qmod_validator"))
    validate_quantum_model(tb.ref("qmod_ae_alt"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=10,  # actual width: 7
        expected_depth=50,  # actual depth: 30
    )
    validate_quantum_program_size(
        tb.ref("qprog_validator"),
        expected_width=10,  # actual width: 6
        expected_depth=20,  # actual depth: 13
    )
    validate_quantum_program_size(
        tb.ref("qprog_ae_alt"),
        expected_width=10,  # actual width: 4
        expected_depth=20,  # actual depth: 9
    )

    # test notebook content
    for input_, output in tb.ref(
        "[(data.tolist()[0] , validator_network(data).tolist()[0]) for data, _ in validator_data_loader]"
    ):
        assert input_ == output, "autoencoder failed to encode"
