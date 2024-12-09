import pytest
from tests.utils.utils_for_testbook import (
    assert_unchanged_size,
    assert_valid_model,
    execute_testbook_with_timeout,
)
from tests.utils.utils_for_tests import should_skip_notebook
from testbook.client import TestbookNotebookClient  # type: ignore[import]


@pytest.mark.skipif(should_skip_notebook("bernstein_vazirani"), reason="Didn't change")
@execute_testbook_with_timeout("bernstein_vazirani", timeout_seconds=20)
def test_bernstein_vazirani(tb: TestbookNotebookClient) -> None:
    # test models
    assert_valid_model(tb.ref("qmod"))
    # test quantum programs
    assert_unchanged_size(tb.ref("qprog"), expected_width=6, expected_depth=5)

    # test notebook content
    assert int(tb.ref("secret_integer_q")) == tb.ref("SECRET_INT")
