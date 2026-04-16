#!/usr/bin/env python3
"""Parse JUnit XML test results and print a Slack-ready summary."""

import argparse
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# ── Error categorization ──────────────────────────────────────────────────────

_ANSI_RE = re.compile(r"(?:\x1b|\#x1B)\[[0-9;]*m")
_EXCEPTION_LINE_RE = re.compile(
    r"^([A-Za-z][\w.]*(?:Error|Exception|Warning)[^:]*): (.+)$"
)

_DEGRADATION_RE = re.compile(
    r"The (width|depth) of the circuit changed.*?for the worse.*?[Ff]rom (\d+) to (\d+)",
    re.DOTALL | re.IGNORECASE,
)

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"lack.of.resources|InsufficientResources|insufficient.*resources",
            re.IGNORECASE,
        ),
        "lack of resources",
    ),
    (
        re.compile(r"[Qq]mod.*[Uu]pdat|out.of.date.*[Qq]mod|QmodUpdatedException"),
        "out of date qmod",
    ),
    (
        re.compile(r"500.*internal.*server|internal server error", re.IGNORECASE),
        "500 internal server error",
    ),
    (re.compile(r"allclose|np\.allclose", re.IGNORECASE), "allclose failed"),
    # Match timeout as an exception/error/result — not as a parameter name (e.g. timeout_seconds=)
    (
        re.compile(
            r"\bTimeoutError\b|\bCellTimeoutError\b|\btimed out\b|reached timeout",
            re.IGNORECASE,
        ),
        "timeout",
    ),
    (
        re.compile(r"HTTP.*4\d\d|404|broken.*link|link.*broken", re.IGNORECASE),
        "broken link",
    ),
    (
        re.compile(
            r"ClassiqAPIError.*not supported|device.*not.*supported", re.IGNORECASE
        ),
        "device not supported",
    ),
    (
        re.compile(r"VQE.*did not converge|did not converge.*VQE", re.IGNORECASE),
        "VQE did not converge",
    ),
    (
        re.compile(r"[Uu]ncommitted.*[Qq]mod|Found uncommitted"),
        "uncommitted Qmod files",
    ),
]


def _categorize(error_text: str) -> tuple[str, str]:
    """Return (category, detail) for a failure's combined error text."""
    clean = _ANSI_RE.sub("", error_text)
    if m := _DEGRADATION_RE.search(clean):
        dim, old, new = m.group(1), m.group(2), m.group(3)
        return "circuit degradation", f"{dim}: {old} -> {new}"
    for pattern, label in _PATTERNS:
        if pattern.search(clean):
            return label, ""
    # Fallback: last line matching "SomeError: message", else first non-empty line
    last_exception = ""
    for line in clean.splitlines():
        if m := _EXCEPTION_LINE_RE.match(line.strip()):
            last_exception = f"{m.group(1)}: {m.group(2)}"
    if last_exception:
        return "other", last_exception[:80]
    for line in clean.splitlines():
        if stripped := line.strip():
            return "other", stripped[:80]
    return "other", ""


# ── XML parsing ───────────────────────────────────────────────────────────────

_NOTEBOOK_RE = re.compile(r"\[(.+?\.ipynb)\]")
_CLASSNAME_RE = re.compile(r"(?:^|\.)(test_\w+)$")


def _notebook_name(test_name: str, classname: str = "") -> str:
    # Parametrized form: test_notebook[path/to/nb.ipynb]
    if m := _NOTEBOOK_RE.search(test_name):
        return Path(m.group(1)).name
    # classname form: tests.notebooks.test_bernstein_vazirani -> bernstein_vazirani
    if m := _CLASSNAME_RE.search(classname):
        return m.group(1).removeprefix("test_")
    return test_name


def _parse_xml(path: Path) -> tuple[float, list[tuple[str, str, str]]]:
    """Return (duration_seconds, [(notebook_name, category, detail)])."""
    root = ET.parse(path).getroot()
    suites = root.findall("testsuite") if root.tag == "testsuites" else [root]

    total_time = sum(float(s.get("time", 0)) for s in suites)
    failures: list[tuple[str, str, str]] = []

    for suite in suites:
        for tc in suite.findall("testcase"):
            failure = tc.find("failure")
            node = failure if failure is not None else tc.find("error")
            if node is None:
                continue
            notebook = _notebook_name(tc.get("name", ""), tc.get("classname", ""))
            error_text = " ".join(
                filter(None, [node.get("message", ""), node.text or ""])
            )
            category, detail = _categorize(error_text)
            failures.append((notebook, category, detail))

    return total_time, failures


# ── Formatting ────────────────────────────────────────────────────────────────


def _format_duration(seconds: float) -> str:
    minutes = round(seconds / 60)
    if minutes < 60:
        return f"{minutes}m"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h{mins}m" if mins else f"{hours}h"


def _format_summary(
    workflow_name: str, duration: float, failures: list[tuple[str, str, str]]
) -> str:
    dur = _format_duration(duration)
    if not failures:
        return f"- {workflow_name} ({dur}): all pass \u2705"

    lines = [f"- {workflow_name} ({dur}): {len(failures)} failed"]

    by_category: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for notebook, category, detail in failures:
        by_category[category].append((notebook, detail))
    # Most frequent categories first
    sorted_categories = sorted(by_category.items(), key=lambda x: -len(x[1]))

    for category, items in sorted_categories:
        if any(detail for _, detail in items):
            lines.append(f"  - {category}:")
            for notebook, detail in items:
                suffix = f" ({detail})" if detail else ""
                lines.append(f"    - {notebook}{suffix}")
        else:
            notebooks = ", ".join(nb for nb, _ in items)
            lines.append(f"  - {category}: {notebooks}")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", default="pytest-results/test-results.xml")
    parser.add_argument("--workflow-name", required=True)
    args = parser.parse_args()

    junit_path = Path(args.junit)
    if not junit_path.exists():
        msg = f"- {args.workflow_name}: no test results found (XML missing)"
        print(msg)
        if summary_file := os.environ.get("GITHUB_STEP_SUMMARY"):
            Path(summary_file).write_text(f"```\n{msg}\n```\n")
        return

    duration, failures = _parse_xml(junit_path)
    summary = _format_summary(args.workflow_name, duration, failures)

    print(summary)
    if summary_file := os.environ.get("GITHUB_STEP_SUMMARY"):
        Path(summary_file).write_text(f"```\n{summary}\n```\n")


if __name__ == "__main__":
    main()
