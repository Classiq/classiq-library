import os
import logging
from contextlib import contextmanager

from testbook import testbook  # type: ignore[import]
from utils_for_tests import iterate_notebooks

TIMEOUT: int = 60 * 10  # 10 minutes
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
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)
