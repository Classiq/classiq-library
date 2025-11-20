import re
import os
from pathlib import Path
from typing import Any, Callable
import sys


def qmod_compare_decorator(func: Callable) -> Any:
    def inner(*args: Any, **kwargs: Any) -> Any:
        qmods_before = _read_qmod_files()

        try:
            result = func(*args, **kwargs)
        finally:
            qmods_after = _read_qmod_files()

            all_errors = _compare_qmods(qmods_before, qmods_after)

            # intentionally not collection the exception in an `except` block
            #   this way, in case `_compare_qmods` raised errors, we will print all the errors
            #       plus have the full traceback of the error from `func`
            exc_type, exc_value, exc_tb = sys.exc_info()
            if exc_type is not None:
                # prepend all the errors from `compare_qmods`, so that `actions/send_qmod_slack_notification` will have a simpler regex
                all_errors += [f"{exc_type.__name__}({exc_value})"]

            assert not all_errors, "\n".join(all_errors)

    return inner


def _read_qmod_files(file_path: str = ".") -> dict[str, str]:
    return {
        str(qmod_path): _normalize_qmod_code(qmod_path)
        for qmod_path in Path(file_path).parent.glob("*.qmod")
    }


def _normalize_qmod_code(qmod_path: Path) -> str:
    code = qmod_path.read_text()
    code = code.strip()
    float_pattern = r"[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
    code = re.sub(rf"\({float_pattern}\)", "<NUMBER>", code)
    code = re.sub(rf"(?<=[^a-zA-Z0-9_+\-]){float_pattern}", "<NUMBER>", code)
    code = re.sub(r"\s+", "", code)
    code = re.sub(r"Pauli::[IXYZ]", "<PAULI>", code)
    return code


def _compare_qmods(old_files: dict[str, str], new_files: dict[str, str]) -> list[str]:
    errors = []
    if len(new_files) > len(old_files):
        errors.append(
            f"Found uncommitted Qmod files: {', '.join(new_files.keys() - old_files.keys())}"
        )

    for file_name, old_content in old_files.items():
        new_content = new_files[file_name]
        if old_content != new_content:
            errors.append(f"Qmod file {os.path.basename(file_name)} is not up-to-date")

    return errors
