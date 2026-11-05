"""
Helpers for testing the notebooks in `benchmarking/`

Running these notebooks as-is doesn't test much:
- They store their results in csv files committed to the repo.
    Since these files already have COMPLETED results, the notebooks don't run anything.
- They write a PDF report, which requires `latexmk`.
- They don't raise errors. Instead, errors are written to the results file.

So each test stores the results in a new csv file, skips the report, and checks the results file.
"""

import csv
import tempfile
from pathlib import Path


def benchmark_replacements() -> list[tuple[str, str]]:
    results_file = Path(tempfile.mkdtemp()) / "results.csv"
    return [
        # Store the results in a new csv file
        (
            "FILENAME = example.default_results_filename",
            f"FILENAME = '{results_file}'",
        ),
        # Don't write the report
        ("build_each_time=True", "skip_report=True"),
    ]


def load_results(results_file: str | Path) -> list[dict]:
    with open(results_file) as f:
        return list(csv.DictReader(f))


def validate_completed(results: list[dict], expected_count: int) -> None:
    assert len(results) == expected_count, f"Missing results: {results}"
    for result in results:
        assert (
            result["status"] == "COMPLETED"
        ), f"{result['example']} on {result['backend_name']}: {result['status']} {result.get('error_message', '')}"


def validate_benchmark_results(
    results_file: str, num_backends: int, min_score: float
) -> None:
    results = load_results(results_file)
    validate_completed(results, expected_count=num_backends)
    for result in results:
        score = float(result["score"])
        assert score >= min_score, f"{result['backend_name']}: {score=} < {min_score}"
