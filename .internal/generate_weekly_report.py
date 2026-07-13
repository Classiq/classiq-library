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
from collections import defaultdict
from datetime import datetime

REPO = "Classiq/classiq-library"
WORKFLOWS = {
    "Test-CI-daily-internal.yml": "internal",
    "Test-CI-daily-notebooks-other.yml": "other",
    "Test-CI-daily-notebooks-algorithms.yml": "algorithms",
    "Test-CI-daily-notebooks-applications.yml": "applications",
    "Test-CI-daily-notebooks-tutorials.yml": "tutorials",
}
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


def _fetch_runs() -> dict[str, list[dict]]:
    by_date: dict[str, list[dict]] = defaultdict(list)
    for workflow_file, name in WORKFLOWS.items():
        raw = _gh(
            "run",
            "list",
            "--repo",
            REPO,
            "--workflow",
            workflow_file,
            "--limit",
            str(RUNS_TO_FETCH),
            "--json",
            "databaseId,createdAt,conclusion",
        )
        for run in json.loads(raw):
            run["name"] = name
            by_date[run["createdAt"][:10]].append(run)
    return by_date


def _fetch_summary(run_id: int, name: str) -> str:
    try:
        job_id = _gh(
            "api",
            f"repos/{REPO}/actions/runs/{run_id}/jobs",
            "--jq",
            ".jobs[0].id",
        ).strip()
        log = _gh("api", f"repos/{REPO}/actions/jobs/{job_id}/logs")
    except subprocess.CalledProcessError:
        return f"- {name}: failed to fetch logs"

    return _extract_summary(log) or f"- {name}: summary not found in logs"


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

    by_date = _fetch_runs()
    dates = sorted(by_date, reverse=True)

    if not dates:
        print("No workflow runs found.", file=sys.stderr)
        sys.exit(1)

    if args.n is not None:
        idx = args.n - 1
    else:
        print("Found the following weekly runs:", file=sys.stderr)
        for i, date in enumerate(dates, 1):
            day = datetime.strptime(date, "%Y-%m-%d").strftime("%a")
            workflows = sorted(r["name"] for r in by_date[date])
            print(f"  {i}) {date} ({day}) — {', '.join(workflows)}", file=sys.stderr)

        choice = input(f"\nChoose [1-{len(dates)}, default=1]: ").strip()
        idx = (int(choice) - 1) if choice else 0

    date = dates[idx]
    runs = by_date[date]
    order = list(WORKFLOWS.values())
    runs.sort(key=lambda r: order.index(r["name"]))

    print(f"Fetching summaries for {date}...", file=sys.stderr)

    summaries = [_fetch_summary(r["databaseId"], r["name"]) for r in runs]
    print("\n".join(summaries))


if __name__ == "__main__":
    main()
