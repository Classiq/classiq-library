#!/usr/bin/env python3
"""
Fetch and combine weekly CI summaries from classiq-library.

Usage:
    python generate_weekly_report.py                  # interactive date picker
    python generate_weekly_report.py -n 1 | xsel -ib  # most recent, straight to clipboard
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime

REPO = "Classiq/classiq-library"
WORKFLOW = "Test-CI-weekly.yml"
RUNS_TO_FETCH = 5

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s?")
_SUMMARY_NAMES = "|".join(
    ["internal", "algorithms", "applications", "other", "tutorials"]
)
_SUMMARY_START_RE = re.compile(rf"^- ({_SUMMARY_NAMES}) \(")


def _gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=True)
    return result.stdout


def _strip_timestamp(line: str) -> str:
    return _TIMESTAMP_RE.sub("", line)


def _extract_summary(log_text: str) -> str | None:
    lines = log_text.splitlines()
    summary_lines: list[str] = []
    capturing = False

    for line in lines:
        content = _strip_timestamp(line)
        if not capturing and _SUMMARY_START_RE.match(content):
            capturing = True
            summary_lines.append(content)
        elif capturing:
            if content.startswith("    ") or content == "":
                summary_lines.append(content)
            else:
                break

    return "\n".join(summary_lines).rstrip() if summary_lines else None


def _fetch_runs() -> list[dict]:
    raw = _gh(
        "run",
        "list",
        "--repo",
        REPO,
        "--workflow",
        WORKFLOW,
        "--limit",
        str(RUNS_TO_FETCH),
        "--json",
        "databaseId,createdAt,conclusion",
    )
    return json.loads(raw)


def _fetch_summary(job_id: int, name: str) -> str:
    try:
        log = _gh(
            "api",
            "--allow-escape-sequences",
            f"repos/{REPO}/actions/jobs/{job_id}/logs",
        )
    except subprocess.CalledProcessError:
        return f"- {name}: failed to fetch logs"

    return _extract_summary(log) or f"- {name}: summary not found in logs"


# Each job of the run is one suite (internal, other, algorithms, ...)
def _fetch_summaries(run_id: int) -> list[str]:
    raw = _gh(
        "api",
        f"repos/{REPO}/actions/runs/{run_id}/jobs",
        "--jq",
        "[.jobs[] | {id, name}]",
    )
    return [_fetch_summary(job["id"], job["name"]) for job in json.loads(raw)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch weekly CI summaries.")
    parser.add_argument(
        "-n",
        type=int,
        default=None,
        metavar="INDEX",
        help="1-based index of the run to fetch (1 = most recent). Skips the interactive prompt.",
    )
    args = parser.parse_args()

    runs = _fetch_runs()  # most recent first

    if not runs:
        print("No workflow runs found.", file=sys.stderr)
        sys.exit(1)

    if args.n is not None:
        idx = args.n - 1
    else:
        print("Found the following weekly runs:", file=sys.stderr)
        for i, run in enumerate(runs, 1):
            date = run["createdAt"][:10]
            day = datetime.strptime(date, "%Y-%m-%d").strftime("%a")
            status = run["conclusion"] or "in progress"
            print(f"  {i}) {date} ({day}) — {status}", file=sys.stderr)

        choice = input(f"\nChoose [1-{len(runs)}, default=1]: ").strip()
        idx = (int(choice) - 1) if choice else 0

    run = runs[idx]
    print(f"Fetching summaries for {run['createdAt'][:10]}...", file=sys.stderr)

    summaries = _fetch_summaries(run["databaseId"])
    print("\n".join(summaries))


if __name__ == "__main__":
    main()
