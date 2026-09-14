import os

from tests.utils_for_error_silencing import COLLECTED_SILENCED_ERRORS


def pytest_sessionfinish(session, exitstatus):
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    if not COLLECTED_SILENCED_ERRORS:
        return

    with open(summary_file, "a") as f:
        f.write("### Pytest Warnings :warning:\n\n```text\n")
        for warning in COLLECTED_SILENCED_ERRORS:
            f.write(f"{warning}\n")
        f.write("```\n")
