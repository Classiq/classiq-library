from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("quantum_walks_via_efficient_blockencoding.ipynb", timeout_seconds=720)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_ebt"))
    validate_quantum_model(tb.ref("qmod_ebt_lcu"))
    validate_quantum_model(tb.ref("qmod_sbc"))
    validate_quantum_model(tb.ref("qmod_md"))
    validate_quantum_model(tb.ref("qmod_nmd"))

    # test notebook content
    pass  # Todo
