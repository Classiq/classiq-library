from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("BE_Sparse_Classiq.ipynb", timeout_seconds=1000)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_ebt"))
    validate_quantum_model(tb.ref("qmod_ebt_lcu"))
    validate_quantum_model(tb.ref("qmod_sbc"))
    validate_quantum_model(tb.ref("qmod_md"))
    validate_quantum_model(tb.ref("qmod_nmd"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog_ebt"),
        expected_width=None,
        expected_depth=None,
    )
    validate_quantum_program_size(
        tb.ref("qprog_ebt_lcu"),
        expected_width=None,
        expected_depth=None,
    )
    validate_quantum_program_size(
        tb.ref("qprog_sbc"),
        expected_width=None,
        expected_depth=None,
    )
    validate_quantum_program_size(
        tb.ref("qprog_md"),
        expected_width=None,
        expected_depth=None,
    )
    validate_quantum_program_size(
        tb.ref("qprog_ebt_nmd"),
        expected_width=None,
        expected_depth=None,
    )
    # test notebook content
    pass  # Todo
