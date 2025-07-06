import re
from typing import Any

from utils_for_tests import ROOT_DIRECTORY


README_FILE = ROOT_DIRECTORY / "README.md"
PYTHON_CODE_PATTERN = r"(?s)```python\s*\n(.*?)```"
SHOW_PATTERN = r"\s*show\(.*\)"
VERIFY_RESULT_PATTERN = r"print\((.*)\)\n\s*# (.*)"


def _convert_code(code: str) -> str:
    lines = code.splitlines()

    # Add import if missing from block
    if not lines[0].startswith("from classiq import"):
        lines = ["from classiq import *"] + lines

    # Remove calls to show function
    lines = [line for line in lines if not re.match(SHOW_PATTERN, line)]
    code = "\n".join(lines)

    # Verify print statement prints expected value
    code = re.sub(VERIFY_RESULT_PATTERN, r'assert str(\1) == "\2"', code)
    return code


def test_readme_file() -> None:
    with open(README_FILE) as f:
        readme = f.read()

    codes = [_convert_code(code) for code in re.findall(PYTHON_CODE_PATTERN, readme)]
    for code in codes:
        locals_: dict[str, Any] = dict()
        exec(code, locals_, locals_)
