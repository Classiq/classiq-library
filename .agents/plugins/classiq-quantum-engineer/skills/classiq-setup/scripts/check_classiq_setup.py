#!/usr/bin/env python3
"""Diagnose a Classiq Python SDK environment.

Reports, in order:
  1. The active Python interpreter and whether its version is supported.
  2. Whether the `classiq` package is importable and its installed version.
  3. (with --check-latest) the latest version published on PyPI and whether an
     upgrade is available.
  4. A best-effort check of whether authentication credentials are present.

This script only inspects the environment and prints guidance. It never
installs packages, upgrades anything, or triggers an interactive browser login.

Usage:
    python check_classiq_setup.py [--check-latest]

Run it with the SAME interpreter the user intends to use for Classiq work
(their active virtualenv / conda env / notebook kernel), e.g.:
    python -m ... or  /path/to/venv/bin/python check_classiq_setup.py
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

# Documented fallback support window, used only when the installed package's
# own `requires-python` cannot be read. The authoritative constraint is always
# the `requires-python` of the version being installed.
FALLBACK_MIN_PY = (3, 10)
FALLBACK_MAX_PY_EXCLUSIVE = (3, 13)  # i.e. supported < 3.13


def _line(ok: bool | None, msg: str) -> None:
    mark = {True: "[ OK ]", False: "[FAIL]", None: "[ ?? ]"}[ok]
    print(f"{mark} {msg}")


def _installed_requires_python():
    """Return (min, max_exclusive) parsed from the installed package metadata.

    Reads the authoritative `Requires-Python` of the installed `classiq` so the
    support check stays correct as Classiq widens its range. Returns None if the
    package is absent or the specifier cannot be parsed simply.
    """
    try:
        from importlib.metadata import metadata

        spec = metadata("classiq").get("Requires-Python")
    except Exception:
        return None
    if not spec:
        return None

    def _ver(s):
        parts = s.strip().split(".")
        return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)

    lo = hi = None
    try:
        for clause in spec.split(","):
            clause = clause.strip()
            if clause.startswith(">="):
                lo = _ver(clause[2:])
            elif clause.startswith("<"):
                hi = _ver(clause[1:])
    except Exception:
        return None
    if lo is None or hi is None:
        return None
    return lo, hi


def check_python() -> None:
    v = sys.version_info
    cur = (v.major, v.minor)
    parsed = _installed_requires_python()
    min_py, max_py_exclusive = parsed or (FALLBACK_MIN_PY, FALLBACK_MAX_PY_EXCLUSIVE)
    ok = min_py <= cur < max_py_exclusive
    _line(ok, f"Python {v.major}.{v.minor}.{v.micro} at {sys.executable}")
    if not ok:
        print(
            f"       Classiq supports Python {min_py[0]}.{min_py[1]}"
            f"–{max_py_exclusive[0]}.{max_py_exclusive[1] - 1}. "
            "Create a virtual environment on a supported version before installing."
        )


def installed_version() -> str | None:
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("classiq")
        except PackageNotFoundError:
            return None
    except Exception:
        return None


def check_installed() -> str | None:
    ver = installed_version()
    if ver is None:
        _line(False, "classiq is NOT installed in this environment")
        print("       Install it with:  pip install -U classiq")
        return None
    # Confirm it actually imports (catches broken installs).
    try:
        import classiq  # noqa: F401

        _line(True, f"classiq {ver} installed and importable")
    except Exception as exc:  # pragma: no cover - environment dependent
        _line(False, f"classiq {ver} is installed but failed to import: {exc!r}")
    return ver


def latest_pypi_version(timeout: float = 10.0) -> str | None:
    url = "https://pypi.org/pypi/classiq/json"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.load(resp)
        return data["info"]["version"]
    except Exception as exc:
        _line(None, f"could not reach PyPI to check latest version: {exc!r}")
        return None


def check_latest(current: str | None) -> None:
    latest = latest_pypi_version()
    if latest is None:
        return
    if current is None:
        _line(None, f"latest classiq on PyPI is {latest} (nothing installed yet)")
        return
    if current == latest:
        _line(True, f"classiq is up to date (latest on PyPI: {latest})")
    else:
        _line(None, f"a newer classiq is available: {current} -> {latest}")
        print("       Upgrade with:  pip install -U classiq")


def check_auth() -> None:
    """Best-effort detection of stored credentials.

    Classiq persists auth tokens in a local credentials file after a successful
    `authenticate()`. The exact path is an internal detail, so absence here is
    NOT proof the user is unauthenticated. The definitive test is running a real
    SDK call (e.g. synthesize). This check only looks for an obvious token file.
    """
    candidates = [
        Path.home() / ".classiq" / "credentials.json",
        Path.home() / ".config" / "classiq" / "credentials.json",
    ]
    found = next((p for p in candidates if p.exists()), None)
    if found is not None:
        _line(
            None,
            f"credentials file present at {found} "
            "(not a guarantee the tokens are still valid)",
        )
    else:
        _line(
            None,
            "no credentials file found in the usual locations (may still be "
            "authenticated)",
        )
        print(
            "       If SDK calls fail with an auth error, run in Python:\n"
            "         import classiq; classiq.authenticate()\n"
            "       Re-auth a stale device with: classiq.authenticate(overwrite=True)"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-latest",
        action="store_true",
        help="query PyPI for the latest classiq version (requires network)",
    )
    args = parser.parse_args()

    print("== Classiq SDK environment check ==")
    check_python()
    current = check_installed()
    if args.check_latest:
        check_latest(current)
    check_auth()
    print("== done ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
