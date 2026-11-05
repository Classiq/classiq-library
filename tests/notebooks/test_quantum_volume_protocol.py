import tempfile
from pathlib import Path

from tests.utils_for_benchmark_tests import load_results, validate_completed
from tests.utils_for_testbook import wrap_testbook
from testbook.client import TestbookNotebookClient

NUM_TRIALS = 2
RESULTS_DIR = tempfile.mkdtemp()


@wrap_testbook(
    "quantum_volume_protocol",
    timeout_seconds=900,
    replacements_regex=[
        ("num_trials=10", f"num_trials={NUM_TRIALS}"),
        # Store the results in a new directory
        ("results/quantum_volume", RESULTS_DIR),
        # Don't write the report
        ("build_report_each_time=True", "update_report_each_time=False"),
        # The notebook waits until all trials are COMPLETED, so a failed trial would make it wait forever
        ("while True:", "for _ in range(10):"),
    ],
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    results = [r for f in Path(RESULTS_DIR).glob("*.csv") for r in load_results(f)]
    num_widths = len(tb.ref("protocol.widths()"))
    num_backends = len(tb.ref("benchmark_hardware"))
    validate_completed(results, expected_count=num_widths * num_backends * NUM_TRIALS)

    # On an ideal simulator, the heavy output probability is always above 0.5
    for result in results:
        heavy_output_probability = float(result["heavy_output_probability"])
        assert (
            heavy_output_probability > 0.5
        ), f"{result['example']} on {result['backend_name']}: {heavy_output_probability=}"
