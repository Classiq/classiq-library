from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qml_with_classiq_guide", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=1,  # actual width: 1
        expected_depth=1,  # actual depth: 1
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=1,  # actual width: 1
        expected_depth=2,  # actual depth: 2
    )

    # test notebook content
    assert (
        tb.ref("check_accuracy(model, data_loader)") > 0
    )  # sometimes 1, sometimes 0.5
