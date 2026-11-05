from tests.utils_for_benchmark_tests import (
    benchmark_replacements,
    validate_benchmark_results,
)
from tests.utils_for_testbook import wrap_testbook
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "benchmark_ghz",
    timeout_seconds=600,
    replacements_regex=benchmark_replacements(),
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    validate_benchmark_results(
        tb.ref("FILENAME"),
        num_backends=len(tb.ref("benchmark_hardware")),
        min_score=0.9,
    )
