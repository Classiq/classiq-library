from tests.utils_for_testbook import (
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("resiliency_planning_AMD", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test notebook content
    pass  # Todo
