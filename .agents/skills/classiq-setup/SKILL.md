---
name: classiq-setup
description: This skill is the first layer on ANY question about installing, setting up, upgrading, version-checking, or authenticating Classiq, even when the user doesn't say "setup" explicitly. It is the authoritative source for these tasks; answering from general knowledge or a raw doc search yields wrong flags and credential paths, so route the question here first. Trigger on "install classiq" / "pip install classiq", "upgrade classiq", "check/which classiq version", "what version of classiq do I have", "is my classiq up to date / on the latest version", "check my classiq version for me", "do I have classiq installed", and any authentication question - how to authenticate, headless or no-browser auth, where credentials are stored, copying credentials between machines, or whether there's a command-line / CLI flag to log in. Also trigger on environment errors such as "classiq command not found" or authentication failures - including auth errors that surface while synthesizing or executing. Do NOT use this skill for writing quantum models (use classiq-modeling) or running/executing programs (use classiq-execution).
---

# Classiq SDK Setup

Guide the user from a bare Python environment to a working, authenticated Classiq SDK. The Classiq SDK is published on PyPI as the `classiq` package. The job of this skill is environment readiness only: install, version checks, upgrades, and authentication. It does not write quantum models or execute programs.

## Setup workflow

Diagnose first, then act. The end state is: a supported Python interpreter, the `classiq` package installed and importable, on a current version, with authentication completed.

### 1. Diagnose the current environment

Run the bundled diagnostic against the interpreter the user intends to use for Classiq work (their active virtualenv, conda env, notebook kernel, or IDE interpreter). Invoke it by its plugin-rooted path so it works regardless of the current directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/classiq-setup/scripts/check_classiq_setup.py" --check-latest
```

The script reports Python version, whether `classiq` is installed and importable, the installed version vs. the latest on PyPI, and a best-effort credentials check. It never installs, upgrades, or triggers a browser login — it only inspects and prints guidance. Use its output to decide which of the steps below are needed; skip steps that already pass.

The `--check-latest` flag is optional and needs network access; without it (or when PyPI is unreachable) the script still runs and just skips the latest-version comparison. If `python` is unavailable, try `python3`, or the project's runner (e.g. `uv run python "${CLAUDE_PLUGIN_ROOT}/skills/classiq-setup/scripts/check_classiq_setup.py"`).

### 2. Verify the Python version

The installed `classiq` package requires Python **3.10–3.12** — the `requires-python` the diagnostic reads is authoritative (the docs page may still cite 3.8–3.12). If the active interpreter is outside this range, create a dedicated environment on a supported version before installing — do not fight the system Python:

```bash
python3.12 -m venv .venv && source .venv/bin/activate   # venv
# or:  conda create -n classiq python=3.12 && conda activate classiq
```

### 3. Install or upgrade the SDK

Install (and upgrade, same command) from PyPI:

```bash
pip install -U classiq
```

Alternatives, matching the user's tooling:
- `uv pip install -U classiq` or `uv add classiq` (uv-managed projects — this plugin's dev container uses uv)
- `conda` environments: still install `classiq` via `pip` inside the env (it is a PyPI package, not on conda-forge)
- Pin a specific version: `pip install classiq=={VERSION}`

Only the last **three** Classiq releases are supported ([docs](https://docs.classiq.io/latest/getting-started/sdk_installation/)), so prefer staying current — the diagnostic flags when a newer release exists, though it checks latest-vs-installed, not the three-release window itself. Always install into the *active* environment — confirm with `pip -V` / `which python` that pip targets the intended interpreter.

### 4. Confirm the installation

```bash
pip show classiq          # name, version, location
python -c "import classiq; print(classiq.__version__)"
```

Re-running the diagnostic from step 1 confirms install + version + latest in one shot.

### 5. Authenticate

Authentication is interactive and must run inside Python (REPL, script, or notebook), not as a shell command:

```python
import classiq
classiq.authenticate()
```

This opens a browser to confirm the device. Authenticate **once per environment**; the SDK then stores tokens in a local credentials file and reuses them. Guidance for specific situations:

- **Device shows as unauthenticated / stale tokens**: `classiq.authenticate(overwrite=True)`
- **Headless Linux (no browser)**: tokens live in a local credentials file. Run the one-time `authenticate()` on a machine that *has* a browser, then copy the credentials file to the headless machine.
- **The definitive auth test** is a real SDK call succeeding — the credentials-file check is only a hint. If a synthesize/execute call later fails with an auth error, re-run `authenticate()`.

## Common gotchas

- **`ModuleNotFoundError: No module named 'classiq'`**: the package is installed in a *different* environment than the one running the code. Match the interpreter — check `which python` and `pip -V`, and in notebooks confirm the active kernel. Reinstall into the active env. (An old/stale version is the same root cause: the upgrade ran in a different env.)
- **Auth error despite installing**: authentication is separate from installation — run `classiq.authenticate()` once in the environment.
- **`pip` not found / using system Python**: prefer a virtual environment; never rely on a system interpreter outside the 3.10–3.12 range.

## Resources

### Scripts

- **`scripts/check_classiq_setup.py`** — read-only environment diagnostic: Python version support, `classiq` install + importability, installed-vs-latest version (`--check-latest`, needs network), and a best-effort credentials check. Run it before and after changes to confirm readiness.

### Documentation

This skill's workflow above is the authoritative, self-contained answer for setup, version, and authentication questions — follow it directly rather than re-researching. The plugin also ships the `classiq-mcp` MCP server; use `search_classiq_docs` only as a secondary reference for details not covered here (and to confirm the supported version window), not as the first step for a setup/auth question.

- SDK installation guide: https://docs.classiq.io/latest/getting-started/sdk_installation/
- PyPI package: https://pypi.org/project/classiq/
