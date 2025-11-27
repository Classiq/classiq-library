import re
import os
from pathlib import Path
from typing import Any, Callable


def strip_inners_from_exception(exc: Exception) -> Exception:
    tb = exc.__traceback__
    while (tb is not None) and (
        # strip "inner" functions (inside decorators)
        (tb.tb_frame.f_code.co_name.startswith("inner"))
        # strip "testbook" wrapper
        or (
            tb.tb_frame.f_code.co_filename.endswith("/testbook.py")
            and tb.tb_frame.f_code.co_name == "wrapper"
        )
    ):
        tb = tb.tb_next

    # if we stripped too much, that's probably actually an error from an "inner"
    if tb is None:
        return exc
    else:
        return exc.with_traceback(tb)


class StrippedExceptionGroup(ExceptionGroup):
    def __init__(self, message: str, exceptions: list[Exception]) -> None:
        # super().__init__(message, exceptions)
        exceptions_stripped = list(map(strip_inners_from_exception, exceptions))
        super().__init__(message, exceptions_stripped)

    def __str__(self) -> str:
        return f"{super().__str__()} [{self.exceptions[0]}]"


def qmod_compare_decorator(func: Callable) -> Any:
    def inner_qmod(*args: Any, **kwargs: Any) -> Any:
        qmods_before = _read_qmod_files()

        # collect the error of the test itself, in case of such error
        try:
            result = func(*args, **kwargs)
            error = None
        except Exception as exc:
            error = exc

        qmods_after = _read_qmod_files()
        # collect the errors of the qmod comparison, in case of such errors
        #   prepend all the errors from `compare_qmods`, so that `actions/send_qmod_slack_notification` will have a simpler regex
        comparison_errors = _compare_qmods(qmods_before, qmods_after)

        if comparison_errors or error:
            all_errors = []
            if error is not None:
                # put error from `func` first
                all_errors.append(error)
            all_errors.extend(comparison_errors)

            if len(all_errors) == 1:
                raise strip_inners_from_exception(all_errors[0])
            else:
                raise StrippedExceptionGroup(
                    "Main test + qmod compare errors", all_errors
                )

        return result

    return inner_qmod


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
            ValueError(
                f"Found uncommitted Qmod files: {', '.join(new_files.keys() - old_files.keys())}"
            )
        )

    for file_name, old_content in old_files.items():
        new_content = new_files[file_name]
        if old_content != new_content:
            errors.append(
                ValueError(f"Qmod file {os.path.basename(file_name)} is not up-to-date")
            )

    return errors
