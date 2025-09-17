import re
import os
from pathlib import Path
from typing import Any, Callable


def qmod_compare_decorator(func: Callable) -> Any:
    if os.environ.get("QMOD_COMPARISON_FIRST", "") != "true":
        return func

    def inner(*args: Any, **kwargs: Any) -> Any:
        qmods_before = _read_qmod_files()
        result = func(*args, **kwargs)
        qmods_after = _read_qmod_files()
        _compare_qmods(qmods_before, qmods_after)
        return result

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
    code = re.sub(rf"(?<=\W){float_pattern}", "<NUMBER>", code)
    code = re.sub(r"\s+", "", code)
    code = re.sub(r"Pauli::[IXYZ]", "<PAULI>", code)
    return code


def _compare_qmods(old_files: dict[str, str], new_files: dict[str, str]) -> None:
    errors = []
    if len(new_files) > len(old_files):
        errors.append(
            f"Found uncommitted Qmod files: {', '.join(new_files.keys() - old_files.keys())}"
        )

    for file_name, old_content in old_files.items():
        new_content = new_files[file_name]
        if old_content != new_content:
            errors.append(f"Qmod file {os.path.basename(file_name)} is not up-to-date")

    assert not errors, "\n".join(errors)
