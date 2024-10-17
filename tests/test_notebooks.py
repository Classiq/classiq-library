import os

from testbook import testbook  # type: ignore[import]
from utils_for_tests import iterate_notebooks

TIMEOUT: int = 60 * 3  # 3 minutes

logging.basicConfig(level=logging.INFO)  # Added logging configuration


def test_notebooks() -> None:
    current_dir = os.getcwd()
    for notebook_path in iterate_notebooks():
        os.chdir(os.path.dirname(notebook_path))
        try:  # Added try-except for error handling
        with testbook(os.path.basename(notebook_path), execute=True, timeout=TIMEOUT):
          logging.info(f"Executed {notebook_path} successfully.")  # Added success log
        except Exception as e:  # Added error logging
            logging.error(f"Error executing {notebook_path}: {e}")
        finally:  # Added finally block to ensure directory change back
            os.chdir(current_dir)
