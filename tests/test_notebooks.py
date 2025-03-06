import os
import logging
from contextlib import contextmanager

from testbook import testbook  # type: ignore[import]
from utils_for_tests import iterate_notebooks, ROOT_DIRECTORY

# 2025.03.06 : bumping timeout from 10min to 15min to support `approximated_state_preparation.ipynb`
#   it should be reverted ~soon
TIMEOUT: int = 60 * 15  # 15 minutes
LOGGER = logging.getLogger(__name__)


def test_notebooks() -> None:
    for notebook_path in iterate_notebooks():
        LOGGER.info(f"Exeucting notebook {notebook_path}")
        with cwd(os.path.dirname(notebook_path)):
            with testbook(
                os.path.basename(notebook_path), execute=True, timeout=TIMEOUT
            ):
                pass  # we simply wish it to run without errors


@contextmanager
def cwd(path):
    oldpwd = os.getcwd()
    os.chdir(ROOT_DIRECTORY)
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)
