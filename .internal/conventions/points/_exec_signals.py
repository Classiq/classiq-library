"""The execution-API migration, split into its family of signals.

Each entry maps a family name to a `detect(nb) -> list[str]` over a notebook's
code (empty list == clean). The `execution_interface` point unions these; the
report renders one sub-row per family so we can see per-pattern scope.

Target interface (per PR #1643 + the migration ticket):
- free `sample()` / `observe()` instead of `execute()` and instead of an
  `ExecutionSession` context manager for one-shot calls (a session is still fine
  when you deliberately reuse it across many calls);
- no nested `ExecutionPreferences(...)` / `set_*_preferences(...)` — pass
  `num_shots` / backend directly;
- `observe` not `.estimate`, `variational_minimize` not `.minimize`;
- no `batch_*` — the regular methods take a list of params;
- the sample result *is* the DataFrame: `result["x"]` and `.iterrows()`,
  not `.dataframe["x"]` / `.parsed_counts`.

NOTE: the ticket's `calculate_statevector` is a typo — the real SDK function is
`calculate_state_vector` (verified against classiq 1.27.0), which is current and
correct, so it is deliberately NOT a signal here.
"""

import re

from ._model import Notebook

# --- individual family detectors -----------------------------------------


def _finder(pattern: str):
    """A detector that returns every match of `pattern` in the code."""
    rx = re.compile(pattern)
    return lambda nb: [m.group(0) for m in rx.finditer(nb.code)]


_EXECUTE = re.compile(r"(?<![\w.])execute\s*\(")


def _execute(nb: Notebook) -> list[str]:
    """Old free `execute(...)`, excluding a notebook's own `def execute(` helper."""
    out = []
    for m in _EXECUTE.finditer(nb.code):
        if not nb.code[max(0, m.start() - 4) : m.start()].endswith("def "):
            out.append(m.group(0))
    return out


_MINIMIZE = re.compile(r"(\w+)\.minimize\s*\(")


def _minimize(nb: Notebook) -> list[str]:
    """`.minimize(` on a session, but not SciPy's `optimize.minimize(`."""
    return [m.group(0) for m in _MINIMIZE.finditer(nb.code) if m.group(1) != "optimize"]


# --- the family, in migration-priority order -----------------------------

SIGNALS = {
    # structural — reshape cells (agent territory)
    "execute(": _execute,
    "ExecutionPreferences(": _finder(r"\bExecutionPreferences\s*\("),
    "ExecutionSession": _finder(r"\bExecutionSession\b"),
    "parsed_counts": _finder(r"\bparsed_counts\b"),
    ".dataframe": _finder(r"\.dataframe\b"),
    # mechanical — localized renames / removals (scriptable)
    "set_*_preferences": _finder(
        r"\bset_(?:execution|quantum_program_execution)_preferences\b"
    ),
    ".estimate(": _finder(r"\.estimate\s*\("),
    ".minimize(": _minimize,
    "batch_*": _finder(r"\bbatch_(?:sample|estimate|observe)\b"),
}


def detect(nb: Notebook) -> list[str]:
    """Union of every family — the offenders for the umbrella point."""
    return [hit for det in SIGNALS.values() for hit in det(nb)]
