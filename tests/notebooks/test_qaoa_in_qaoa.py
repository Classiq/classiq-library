from tests.utils_for_testbook import (
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qaoa_in_qaoa", timeout_seconds=1801)
def test_notebook(tb: TestbookNotebookClient) -> None:

    # test notebook content
    pass  # Todo
