from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("quantum_autoencoder", timeout_seconds=120)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
    """

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_ae_network"),
        expected_width=10,  # actual width: 7
        expected_depth=50,  # actual depth: 30
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_validator"),
        expected_width=8,  # actual width: 4
        expected_depth=28,  # actual depth: 18
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_ae_alt"),
        expected_width=10,  # actual width: 4
        expected_depth=20,  # actual depth: 9
    )

    # test notebook content
    for data, res in zip(tb.ref("input_data"), tb.ref_pydantic("results_validator")):
        df = res.dataframe
        output = df.loc[df["probability"].idxmax(), "decoded"]
        assert data == output, "autoencoder failed to encode"
