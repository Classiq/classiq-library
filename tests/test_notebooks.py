import os
from testbook import testbook  # type: ignore[import]
from utils_for_tests import iterate_notebooks

TIMEOUT: int = 60 * 3  # 3 minutes


def test_notebooks() -> None:
    for notebook_path in iterate_notebooks():
        os.chdir(os.path.dirname(notebook_path))
        with testbook(notebook_path, execute=True, timeout=TIMEOUT):
            pass  # we simply wish it to run without errors
