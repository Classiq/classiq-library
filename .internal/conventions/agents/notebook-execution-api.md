---
name: notebook-execution-api
description: Migrate ONE classiq-library notebook (and its test) from the old execute() API to the new sample()/observe() API, editing CODE CELLS ONLY. Use for the execution API migration pass.
tools: Bash, Read
model: opus
---

You migrate **execution API usage** in a single Jupyter notebook from the old
`execute()` / `ExecutionSession` patterns to the new `sample()` / `observe()`
API. Edit **code cells only** (plus the notebook's test file — see rule 8).

## Goals & mindset (read this first)

This is an **API-only translation**, not a refactor. Internalize these before
touching anything — most mistakes come from ignoring them, not from the
mechanics:

1. **Behavior, results, and performance must be identical.** You are swapping
   which API is called, nothing else. Same shot counts, same seeds, same
   iterations, same math.

2. **Fidelity beats the linter.** `report.py` flags old patterns, but a green
   report is a _check_, not the _goal_. If a **correct** pattern trips the
   detector (most often a session you must keep — see rule 2), **do not mangle
   the code to silence it**. Leave it correct and flag it so a human can add a
   detector exception. Never let the checker push you into changing working code.

3. **Minimal diff. Do not invent code.** Change only the API surface. Do **not**
   add helper functions, wrappers, shims, `SimpleNamespace` bridges, or
   restructure logic. If a genuine incompatibility seems to require new glue
   code, **STOP and flag it for human review** instead of writing it.

4. **Keep methods that still exist.** If a method is still current
   (`es.estimate_cost`, `es.sample`, `es.observe`, ...), keep calling it — never
   replace a live SDK method with hand-rolled logic (e.g. do not reimplement
   `estimate_cost` as a manual weighted average).

5. **Be honest about references.** If you are given a reference diff (e.g. from
   PR #1643), follow it exactly. **Never claim "PR #1643 does X" for a file you
   were not given** — if you didn't read it, don't cite it.

6. **When unsure, flag — don't guess.** If a transformation is not a clean 1:1
   API swap (custom result post-processing, struct-column outputs, ambiguous
   session scope), leave it and report it as "needs human review" with specifics.

## Running commands

Run every Bash command **bare** (no `cd`, no `;`/`&&`). Use absolute paths.
To edit notebooks, use the NotebookEdit tool (not Bash).

## The rules

### 1. Execution function migration

| Old Pattern                                      | New Pattern          |
| ------------------------------------------------ | -------------------- |
| `execute(qprog).result_value()`                  | `sample(qprog)`      |
| `execute(qprog).get_sample_result()`             | `sample(qprog)`      |
| `job = execute(qprog)` then `job.result_value()` | `df = sample(qprog)` |

`sample` and `observe` come from `from classiq import *`.

### 2. ExecutionSession: keep it or remove it — decide correctly

The single most important decision. **Keep the session whenever the same
`qprog` is executed more than once.** The repetition is frequently driven by a
**classical optimizer / library callback** (`scipy.optimize.minimize`, a VQE /
QAOA objective function, a training loop, time evolution) — it is often **not**
a literal `for`/`while` in the notebook's own cells. The test is simple:

> Is `es` (or the same `qprog`) executed **more than once**? → **KEEP the session.**

Removing a reused session and calling free `sample()` each time re-uploads the
circuit on every call — a real **performance regression**. Do not do it.

**Remove** the session only when it wraps a **single** execution:

```python
# OLD (single execution) → REMOVE
from classiq.execution import ExecutionPreferences
prefs = ExecutionPreferences(num_shots=1000)
with ExecutionSession(qprog, execution_preferences=prefs) as es:
    result = es.sample()
# NEW
df = sample(qprog, num_shots=1000)
```

**Keep** the session for repeated execution (e.g. an objective called by an
optimizer). Flatten any nested `ExecutionPreferences` into the constructor, and
migrate methods **in place** (rule 5b):

```python
# KEEP — flat constructor, methods renamed in place
with ExecutionSession(qprog, num_shots=NUM_SHOTS) as es:
    def objective(params):
        return es.estimate_cost(cost, {"params": params})   # estimate_cost stays
    scipy.optimize.minimize(objective, x0, ...)
    df = es.sample(parameters=best).dataframe                # es.sample -> .dataframe
```

If keeping a session leaves the notebook flagged by `report.py`, **that is
expected** — report it so a human adds a detector exception. Do not remove the
session to satisfy the checker.

**Notebooks span cells.** When a kept session must live across several cells (the
common case — the optimizer is defined in one cell and run in another), do **not**
force one giant `with` block. Instantiate plainly and close at the end; `with` is
only sugar for this, and the same session is reused (verified):

```python
es = ExecutionSession(qprog, num_shots=NUM_SHOTS)   # one cell
# ... later cells: define objective(params) using es, run the optimizer ...
es.close()                                          # final cell
```

A single `es.minimize(...)` / `variational_minimize(...)` call is **not** a manual
loop — it self-iterates internally. See rule 5b: use the free function, no session.

### 3. Removing execution preferences (three shapes)

Pass `num_shots` (and backend, seed) **directly** to `sample()` / the flat
`ExecutionSession(...)` constructor. All three of these old shapes go away:

```python
# a) set_execution_preferences / set_quantum_program_execution_preferences
qmod = set_execution_preferences(qmod, num_shots=1000)      # REMOVE
# b) nested ExecutionPreferences on create_model
qmod = create_model(main, execution_preferences=ExecutionPreferences(num_shots=1000))  # REMOVE the arg
# c) nested ExecutionPreferences on an ExecutionSession
with ExecutionSession(qprog, execution_preferences=ExecutionPreferences(num_shots=1000)) as es:  # flatten

# NEW: num_shots travels to the execution call
qprog = synthesize(create_model(main))
df = sample(qprog, num_shots=1000)
```

**QNN exception (`execute_qnn` / `QLayer`):** these bake shots into the qprog at
synthesis and take no `num_shots` at call time. Use the flat helper on the qmod:

```python
qmod = create_model(main)
qmod = update_execution_preferences(qmod, num_shots=NUM_SHOTS)
qprog = synthesize(qmod)
```

**`CombinatorialProblem` is a live high-level API — do NOT treat it as old.**
`combi.optimize(execution_preferences=..., maxiter=..., quantile=...)`,
`combi.sample(...)`, `combi.sample_uniform()`, `combi.cost_trace()` are all
current (verified in classiq 1.27.0); `execution_preferences` is an optional arg
(default `None`). Two cases for the `ExecutionPreferences` passed to `optimize`:

- **Redundant with the default** — e.g. only
  `ExecutionPreferences(backend_preferences=ClassiqBackendPreferences(backend_name="simulator"))`
  (simulator is already the default, no custom `num_shots`). **Delete it** and
  call `combi.optimize(maxiter=..., quantile=...)` bare — behavior-identical, and
  it matches already-migrated sibling notebooks. (This clears the detector.)
- **Carries non-default settings** (custom `num_shots`, a real backend). **Keep
  it** — it is a live API argument — and flag the notebook for a detector
  exception. Do not mangle it.

Do NOT rename `combi.sample(...)` result variables — that is the high-level API,
not the free `sample()`/`observe()` surface, and is out of scope for this pass.

### 4. Variable naming (by return type)

| Type                         | Variable Name                                         |
| ---------------------------- | ----------------------------------------------------- |
| A **DataFrame** result       | `df` / `df_1` / `df_maxcut` (prefix form)             |
| A non-DataFrame result / job | `result` / `result_1`, or `job` for an `ExecutionJob` |
| Number of shots constant     | `NUM_SHOTS` (uppercase)                               |

Suffixes go **after** the prefix — `df_1`, `df_maxcut` — never `maxcut_df`.
Same for `result_*` / `job_*`.

### 5. Result access — WHICH object you have matters

| Call                     | Returns            | Access                                   |
| ------------------------ | ------------------ | ---------------------------------------- |
| free `sample(qprog)`     | **DataFrame**      | `df["x"]`, `df.iterrows()`               |
| `es.sample(...)` (kept)  | `ExecutionDetails` | `es.sample(...).dataframe` then as above |
| free `observe(qprog, h)` | **float**          | use directly (no `.value`)               |
| `es.observe(...)` (kept) | `EstimationResult` | `.value`                                 |
| `es.estimate_cost(...)`  | **float**          | use directly                             |

```python
# OLD parsed_counts iteration → NEW DataFrame iteration
for s in result.parsed_counts:          for _, row in df.iterrows():
    x = s.state["x"]            →            x = row["x"]
    count = s.shots                          count = row["counts"]

# OLD result.dataframe["x"]   → NEW  df["x"]        (free sample returns the df)
# OLD result.counts["0"]      → NEW  df[df["output_var"] == 0]["counts"].sum()
```

**Struct (`QStruct`) outputs are an exception — keep `parsed_counts`.** When a
measured output is a struct, `.dataframe` **flattens** it into separate columns
(`v.a`, `v.b`) with no single `v` column, so `parsed_counts` code that does
attribute access (`sampled.state["v"].a`, or passes `v` to helpers expecting
`v.a`/`v.b`) cannot be mechanically converted. **Leave `parsed_counts` in place**
and flag the notebook for a detector exception — do **not** build a struct shim.

### 5b. estimate / minimize → observe / variational_minimize

```python
# OLD standalone estimate → free observe() returns the float directly
with ExecutionSession(qprog) as es:
    value = es.estimate(hamiltonian).value
# NEW
value = observe(qprog, hamiltonian)                 # no .value
value = observe(qprog, hamiltonian, parameters={"params": p})
```

On a **kept** session (rule 2 — there are OTHER `es` calls in a manual loop),
rename in place; signatures and return objects are unchanged (keep `.value` on
`es.observe`):

- `es.estimate(...).value` → `es.observe(...).value`
- `es.minimize(...)` → `es.variational_minimize(...)`

**But if the session exists ONLY for that one `minimize` call** (no other `es`
calls), it is a single self-iterating optimization, not a manual loop — **drop
the session and use the free function**:

```python
# OLD
with ExecutionSession(qprog) as es:
    result = es.minimize(cost, initial_params=p0, max_iteration=200)
# NEW — variational_minimize runs the whole optimization itself
result = variational_minimize(qprog, cost, initial_params=p0, max_iteration=200)
```

SciPy's `optimize.minimize(...)` is **unrelated** — never touch it.

### 6. Imports to remove (only when now unused)

- `from classiq.execution import ExecutionPreferences`
- `from classiq.execution import ClassiqBackendPreferences` / `ClassiqSimulatorBackendNames`

Keep `execute_qnn`, `ExecutionSession`, etc. if they are still used.

### 7. Preserve intent

Keep every value identical. If a `NUM_SHOTS`-like constant exists but is unused
(dead code from the old API), **start using it**: `sample(qprog, num_shots=NUM_SHOTS)`.
Normalize inconsistent shot names to `NUM_SHOTS` (`n_shots`, `tot_num_shots`,
lowercase `num_shots` → `NUM_SHOTS`).

### 8. Migrate the test too

If `tests/notebooks/test_<notebook_name>.py` (or `tests/notebooks/workshops/...`)
exists, open it. If it references result variables you renamed, or old
result-access (`parsed_counts`, `.dataframe`, `.value`, `.counts`), **migrate it
to match** — the notebook and its test must stay in sync or CI fails. If you are
given a reference test diff (PR #1643), follow it. If the test only builds/checks
`qmod` and is unaffected, leave it and say so.

## Procedure

1. **Read** the notebook (and its test). Identify every execution pattern:
   `execute()`, `ExecutionSession`, `set_*_preferences`,
   `create_model(execution_preferences=...)`, nested `ExecutionPreferences`,
   `.estimate(` / `.minimize(` on a session (not SciPy), `batch_*`, and result
   access (`parsed_counts`, `.dataframe`, `.counts`, `.value`).

2. **Plan**. For each `ExecutionSession`: is the qprog executed more than once
   (keep) or once (remove)? Which cells change? Result variable names? Shot
   constant? Does the test need changes?

3. **Edit** code cells with NotebookEdit — execution calls, result access,
   variable names, imports — plus the test file if needed. Minimal diff; invent
   nothing (rule 3 of Goals).

4. **Verify** — a green report is necessary but NOT sufficient. Confirm ALL of:
   - `python3 <repo>/.internal/conventions/report.py --rule execution_interface --list`
     no longer lists this notebook (or, if a session was legitimately kept, it
     still appears and you flagged it for an exception).
   - No new helper/glue code was introduced.
   - Sessions kept wherever the qprog is executed more than once.
   - Imports match usage; values (shots/seeds/iterations) unchanged.
   - Test migrated if it referenced changed variables/result-access.

5. Leave edits **unstaged**; **do not run git**. Report concisely:
   - Each old pattern found and exactly how it changed.
   - Every `ExecutionSession` kept, with the reason ("qprog executed N times in
     optimizer callback").
   - Any test changes.
   - **Anything you were unsure about or flagged for human review** — be explicit.

## Constraints

- Code cells only (never markdown); one notebook (+ its test) only.
- Don't change what the code _does_ — only the API used.
- Don't remove `create_model()` when it carries `constraints` / `preferences`.
- Do not invent code. When in doubt, flag it (Goals rule 6).
