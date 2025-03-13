import os
import logging
from contextlib import contextmanager

from testbook import testbook  # type: ignore[import]
from utils_for_tests import iterate_notebooks, ROOT_DIRECTORY

TIMEOUT: int = 60 * 10  # 10 minutes
LOGGER = logging.getLogger(__name__)


def test_notebooks() -> None:
    for notebook_path in iterate_notebooks():
        # a patch, which should be removed soon:
        if os.path.basename(notebook_path) == "approximated_state_preparation.ipynb":
            LOGGER.info(f"Skipping notebook {notebook_path}")
            continue

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
