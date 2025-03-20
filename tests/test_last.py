from tests.utils_for_testbook import TESTED_NOTEBOOKS
from tests.utils_for_tests import iterate_notebook_names


def test_are_all_notebooks_tested():
    assert sorted(TESTED_NOTEBOOKS) == sorted(iterate_notebook_names())
