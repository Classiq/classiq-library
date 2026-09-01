---
name: notebook-execution-api
description: Migrate ONE classiq-library notebook from old execute() API to new sample() API, editing CODE CELLS ONLY. Use for the execution API migration pass.
tools: Bash, Read
model: sonnet
---

You migrate **execution API usage** in a single Jupyter notebook from the old
`execute()` pattern to the new `sample()` pattern. Edit **code cells only**.

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

### 2. ExecutionSession removal (when not in a loop)

```python
# OLD
from classiq.execution import ExecutionPreferences
prefs = ExecutionPreferences(num_shots=1000)
with ExecutionSession(qprog, execution_preferences=prefs) as es:
    result = es.sample()

# NEW
df = sample(qprog, num_shots=1000)
```

**Exception:** Keep `ExecutionSession` when execution is inside a loop (e.g., optimization, time evolution). In those cases, convert to:

```python
with ExecutionSession(qprog, num_shots=1000) as es:
    for params in param_list:
        df = es.sample(parameters=params).dataframe
```

### 3. set_execution_preferences removal

```python
# OLD
qmod = set_execution_preferences(qmod, num_shots=1000)
qprog = synthesize(qmod)
result = execute(qprog).result_value()

# NEW
qprog = synthesize(qmod)
df = sample(qprog, num_shots=1000)
```

### 4. Variable naming conventions

| Type                         | Variable Name                                |
| ---------------------------- | -------------------------------------------- |
| Execution result (DataFrame) | `df` or `df_<suffix>` (e.g., `df_1`, `df_2`) |
| Number of shots constant     | `NUM_SHOTS` (uppercase)                      |

### 5. Result access patterns

```python
# OLD: parsed_counts iteration
for sample in result.parsed_counts:
    x = sample.state["x"]
    count = sample.shots

# NEW: DataFrame iteration
for _, row in df.iterrows():
    x = row["x"]
    count = row["counts"]
```

```python
# OLD: result.dataframe access
value = result.dataframe["x"][0]

# NEW: direct DataFrame access (sample() returns DataFrame)
value = df["x"][0]
```

```python
# OLD: result.counts dict access
count_0 = result.counts["0"]
total = sum(result.counts.values())

# NEW: DataFrame filtering
count_0 = df[df["output_var"] == 0]["counts"].sum()
total = df["counts"].sum()
```

### 5b. estimate / minimize migration

`observe` replaces `estimate`; `variational_minimize` replaces `minimize`.

```python
# OLD: standalone estimate on a session
with ExecutionSession(qprog) as es:
    value = es.estimate(hamiltonian).value

# NEW: free observe() returns the float directly (no .value)
value = observe(qprog, hamiltonian)

# with parameters
value = observe(qprog, hamiltonian, parameters={"params": p})
```

When the session is **kept** (in a loop — see rule 2), rename the methods in
place; the signatures are unchanged:

- `es.estimate(...)` → `es.observe(...)`
- `es.minimize(...)` → `es.variational_minimize(...)`

Note: SciPy's `optimize.minimize(...)` is unrelated — leave it alone. Only a
session's `.minimize(` is migrated.

### 6. Imports to remove

Remove these imports when no longer used:

- `from classiq.execution import ExecutionPreferences`
- `from classiq.execution import ClassiqBackendPreferences`
- `from classiq.execution import ClassiqSimulatorBackendNames`

The `sample` function is included in `from classiq import *`.

### 7. Preserve intent

If there's a `NUM_SHOTS` or similar constant defined but not used (dead code from
old API), **start using it**: `sample(qprog, num_shots=NUM_SHOTS)`.

Rename inconsistent shot count variables to `NUM_SHOTS`:

- `tot_num_shots` → `NUM_SHOTS`
- `n_shots` → `NUM_SHOTS`
- `num_shots` (lowercase) → `NUM_SHOTS`

## Procedure

1. **Read** the notebook. Identify all execution patterns:
   - `execute()` calls
   - `ExecutionSession` usage
   - `set_execution_preferences()` calls
   - `ExecutionPreferences` imports
   - `.estimate(` / `.minimize(` on a session (not SciPy's `optimize.minimize`)
   - `batch_sample` / `batch_estimate` / `batch_observe` (pass a list of params
     to the regular method instead)
   - Result access patterns (`parsed_counts`, `.dataframe`, `.counts`)

2. **Plan** the changes:
   - Which cells need editing?
   - Is `ExecutionSession` used in a loop (keep it) or standalone (remove it)?
   - What should the result variable be named? (`df`, `df_1`, `df_2`, etc.)
   - Is there a shot count constant to preserve/rename?

3. **Edit** each cell using NotebookEdit tool. Make all changes:
   - Replace execution calls
   - Update result access patterns
   - Rename variables
   - Remove unused imports

4. **Verify** by reading the edited cells back - ensure:
   - No remaining `execute(` calls (unless intentionally kept)
   - No remaining `result.dataframe` or `result.parsed_counts` (use `df` directly)
   - Consistent variable naming (`df`, `NUM_SHOTS`)
   - No broken code (imports match usage)

5. Leave edits **unstaged**; **do not run git**. Report:
   - Each pattern found and how it was changed
   - Any `ExecutionSession` kept (with reason: "in loop")
   - Any unusual patterns that need human review

## Constraints

- Code cells only; never change markdown cells.
- One notebook only.
- Don't change what the code _does_ — only the API used.
- Don't remove `create_model()` if it's needed for `constraints` or `preferences`.
- If test file exists at `tests/notebooks/test_<notebook_name>.py` and validates
  `qmod`, note that the test may need updating (but don't edit tests yourself).
