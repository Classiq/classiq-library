import os
import logging

from testbook import testbook  # type: ignore[import]
from utils_for_tests import iterate_notebooks

TIMEOUT: int = 60 * 10  # 10 minutes
LOGGER = logging.getLogger(__name__)


def test_notebooks() -> None:
    current_dir = os.getcwd()
    for notebook_path in iterate_notebooks():
        LOGGER.info(f"Exeucting notebook {notebook_path}")
        os.chdir(os.path.dirname(notebook_path))

        with testbook(os.path.basename(notebook_path), execute=True, timeout=TIMEOUT):
            pass  # we simply wish it to run without errors

        os.chdir(current_dir)
