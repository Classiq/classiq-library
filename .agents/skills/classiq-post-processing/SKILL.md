---
name: classiq-post-processing
description: Use this skill every time the user wants to extract, interpret, or visualize results from a Classiq quantum program execution - even when they don't say "post-processing" explicitly. Trigger whenever the user asks to plot results, read a measurement DataFrame, find the most probable state, extract counts or probabilities, visualize a bitstring distribution, plot an energy convergence curve, analyze a parameter sweep, interpret expectation values, parse QAOA or VQE outputs, or make sense of what came back from sample/observe/minimize/variational_minimize. Also trigger for questions such as "what does this result mean", "how do I get the solution from this", "plot the histogram", "show the energy landscape", "extract the optimal parameters". Do NOT use this skill for executing circuits (use classiq-execution) or modeling circuits (use classiq-modeling).
---

# Classiq Post-Processing

You are a quantum software engineer specializing in extracting insight from Classiq execution results. Your input is always a result object returned by `sample`, `observe`, `calculate_state_vector`, `minimize`, `variational_minimize`, or `ExecutionSession` methods. You do not run circuits - you work with what they returned.

## Critical: result types differ by how the circuit was run

The return type depends on **which function** was called. This is the most common source of mistakes.

| Call | Returns |
|---|---|
| `sample(qprog, ...)` | `DataFrame` (directly) |
| `sample(qprog, parameters=[...])` | `list[DataFrame]` |
| `calculate_state_vector(qprog, ...)` | `DataFrame` (directly) |
| `observe(qprog, observable, ...)` | `float` (directly) |
| `observe(qprog, observable, parameters=[...])` | `list[float]` |
| `observe(qprog, observable=[obs_0, obs_1], ...)` | `list[float]`, one per observable |
| `observe(qprog, observable=[...], parameters=[...])` | `list[list[float]]`, `values[observable][parameter_set]` |
| `variational_minimize(...)` | `list[tuple[float, dict]]` |
| `es.sample()` | `ExecutionDetails` |
| `es.sample(parameters=[...])` | `list[ExecutionDetails]` |
| `es.observe(observable, ...)` | `EstimationResult` - `.value.real` for the scalar |
| `es.observe(observable, parameters=[...])` | `list[EstimationResult]` - unwrap each with `.value.real` |
| `es.variational_minimize(...)` | `list[tuple[float, dict]]` |
| `job.get_sample_result()` (async) | `ExecutionDetails` - use `.dataframe` |
| `job.result_value()` (async observe) | object with `.value` (`complex`) |

Top-level convenience functions (`sample`, `calculate_state_vector`, `observe`) return **plain Python objects** - DataFrame or float. There is no wrapper object with a `.dataframe` attribute on top of them.

`ExecutionSession` methods return **result objects**: `es.sample` gives `ExecutionDetails`, `es.observe` gives `EstimationResult`. The top-level functions do not - `observe` gives a bare float. Same number, different shape, so the unwrapping you need depends entirely on which call produced the data.

**There is no `estimate` API.** `estimate`, `es.estimate`, `batch_estimate`, `submit_estimate`, and `get_estimate_result` were all removed. Expectation values come from `observe` (preferred) or `es.observe`. Note that `EstimationResult` itself did *not* go away - it is what `es.observe` still returns.

---

## Top-level `sample()` - returns DataFrame directly

```python
from classiq import *

# Single execution -> DataFrame
df = sample(qprog, num_shots=2048)
# df IS the DataFrame - there is no .dataframe attribute

# Batch execution -> list[DataFrame]
dfs = sample(qprog, parameters=[{"angle": 0.1}, {"angle": 0.5}], num_shots=1000)
df_0 = dfs[0]
df_1 = dfs[1]
```

### DataFrame structure

Columns (in order): output variable columns first, then `counts`, `probability`, `bitstring`.

```
x    y    counts    probability    bitstring
2    1    537       0.262          10010
0    0    521       0.254          00000
```

Variable columns contain decoded values:
- `QNum` -> `int` or `float`
- `QArray` -> `list[int]` (list of 0s and 1s)
- `QBit` -> `int` (0 or 1)

### Working with the DataFrame

```python
df = sample(qprog, num_shots=2048)

# Most probable state
best = df.loc[df["probability"].idxmax()]

# All states above 5% probability
significant = df[df["probability"] > 0.05]

# Decode a specific variable's distribution
x_dist = df[["x", "probability"]].sort_values("probability", ascending=False)
```

---

## Top-level `calculate_state_vector()` - returns DataFrame directly

```python
from classiq import *

# Returns DataFrame directly (not a wrapper object)
sv_df = calculate_state_vector(qprog)
# sv_df IS the DataFrame
```

### State vector DataFrame columns

`amplitude`, `magnitude`, `phase`, `probability`, `bitstring` (plus output variable columns first):

```
x    amplitude              magnitude    phase    probability    bitstring
0    (0.707+0j)             0.71         0.00π    0.500          0
1    (0+0.707j)             0.71         0.50π    0.500          1
```

`amplitude` is a Python `complex`. `magnitude` and `phase` are formatted strings (e.g. `"0.71"`, `"0.50π"`).

---

## Top-level `observe()` - returns float directly

```python
from classiq import *

# Single -> float
val = observe(qprog, observable=Pauli.Z(0), num_shots=1000)
print(val)        # e.g. 0.342

# Batch over parameters -> list[float]
vals = observe(qprog, observable=Pauli.Z(0), parameters=[{"a": 0.1}, {"a": 0.5}])
print(vals[0])    # float for first parameter set

# Batch over observables -> list[float], one per observable
z_val, x_val = observe(qprog, observable=[Pauli.Z(0), Pauli.X(0)], num_shots=1000)

# Both -> list[list[float]], observable first
grid = observe(
    qprog,
    observable=[Pauli.Z(0), Pauli.X(0)],
    parameters=[{"a": 0.1}, {"a": 0.5}],
)
grid[0][1]   # <Z> at a=0.5
```

The nesting order is **observable, then parameter set**. When plotting a sweep of several observables, iterate the outer index to get one curve per operator:

```python
import numpy as np
import matplotlib.pyplot as plt

angles = np.linspace(0, 2 * np.pi, 30)
observables = [Pauli.Z(0), Pauli.X(0)]
labels = ["⟨Z⟩", "⟨X⟩"]

curves = observe(qprog, observable=observables,
                 parameters=[{"angle": a} for a in angles])

for curve, label in zip(curves, labels):
    plt.plot(angles / np.pi, curve, label=label)
plt.xlabel("Angle (π)"); plt.ylabel("Expectation value")
plt.legend(); plt.grid(True); plt.tight_layout(); plt.show()
```

Transposing this by mistake (`curves[i][j]` read as parameter-first) yields a plot with the right shape and the wrong meaning, so verify the outer length equals the number of observables.

---

## ExecutionSession: `es.sample()` - returns `ExecutionDetails`

`ExecutionDetails` is a rich result object with multiple ways to access the data.

```python
with ExecutionSession(qprog) as es:
    result = es.sample()              # ExecutionDetails
    results = es.sample(parameters=[{"a": 0.1}, {"a": 0.5}])  # list[ExecutionDetails]
```

### `ExecutionDetails` attributes

| Attribute | Type | Description |
|---|---|---|
| `.counts` | `dict[str, int]` | Bitstring -> measurement count |
| `.probabilities` | `dict[str, float]` | Bitstring -> normalized probability |
| `.parsed_states` | `dict[str, dict]` | Bitstring -> decoded variable values |
| `.parsed_counts` | `list[SampledState]` | Sorted by shots (most common first) |
| `.state_vector` | `dict[str, complex] \| None` | Full state vector (simulator only) |
| `.parsed_state_vector` | `list[SimulatedState] \| None` | Parsed state vector entries |
| `.num_shots` | `int \| None` | Total shots executed |
| `.output_qubits_map` | `dict[str, tuple[int, ...]]` | Output register -> qubit indices |
| `.hardware_execution_duration_ms` | `int \| None` | Provider-reported execution time |
| `.warnings` | `list[str]` | Execution warnings |
| `.dataframe` | `pd.DataFrame` | Cached property - same layout as top-level `sample()` |

### Methods on `ExecutionDetails`

```python
# Counts for a specific output variable (bitstring keys)
x_counts = result.counts_of_output("x")        # {"0": 512, "1": 536}

# Parsed counts filtered to specific outputs
filtered = result.parsed_counts_of_outputs("x")

# Counts for specific physical qubits
qubit_counts = result.counts_of_qubits(0, 2)
```

### `SampledState` (entries in `.parsed_counts`)

```python
for pc in result.parsed_counts:
    state = pc.state    # dict: {"x": 3, "y": 10}
    shots = pc.shots    # int
    prob = shots / result.num_shots
    print(f"state={state}  p={prob:.3f}")

# Sort by a derived cost function
ranked = sorted(result.parsed_counts, key=lambda pc: my_cost(pc.state["x"]))
```

---

## ExecutionSession: `es.observe()` - returns `EstimationResult`, not float

`es.observe` is **not** interchangeable with the top-level `observe`. It returns `EstimationResult` objects that must be unwrapped with `.value.real`, and when batching it returns a *list* of them — each unwrapped individually.

```python
with ExecutionSession(qprog) as es:
    ev = es.observe(hamiltonian)                              # EstimationResult
    evs = es.observe(hamiltonian, [{"a": 0.1}, {"a": 0.5}])   # list[EstimationResult]

energy = ev.value.real                    # required
energies = [r.value.real for r in evs]    # required, per element
```

Because of that, results produced with top-level `observe` and results produced with `es.observe` are **not** the same shape, even though the numbers are. Before you index, filter, or plot, check which call produced the data — `[r.value.real for r in data]` on a `list[float]` raises `AttributeError`, and passing raw `EstimationResult` objects to matplotlib fails just as loudly.

If you control the code that produced the results, prefer top-level `observe` — plain floats, nothing to unwrap.

---

## Async results: `job.result_value()` and `job.get_sample_result()`

Submitted jobs also arrive wrapped. Recover by job ID, then unwrap according to what was submitted:

```python
# Sampling
retrieved_sample = ExecutionJob.from_id(sample_job_id)
df = retrieved_sample.get_sample_result().dataframe    # DataFrame

# Observable
retrieved = ExecutionJob.from_id(observe_job_id)
value = retrieved.result_value().value                 # complex
energy = value.real                                    # float
```

`result_value().value` is **complex**, so take `.real` before plotting or comparing it numerically - matplotlib will otherwise warn and discard the imaginary part silently.

---

## Variational results: `variational_minimize()` and `es.variational_minimize()`

Both return `list[tuple[float, dict]]` - one tuple per optimizer iteration.

```python
# res: [(cost_0, params_0), (cost_1, params_1), ...]
final_cost, final_params = res[-1]
print("Optimal energy:", final_cost)
print("Optimal parameters:", final_params)

# Convergence history
costs = [r[0] for r in res]
```

---

## Visualizations

### Probability histogram (from `sample()`)

```python
import matplotlib.pyplot as plt

df = sample(qprog, num_shots=2048)
df_sorted = df.sort_values("probability", ascending=False)

plt.figure(figsize=(10, 4))
plt.bar(df_sorted["bitstring"], df_sorted["probability"])
plt.xlabel("Bitstring")
plt.ylabel("Probability")
plt.xticks(rotation=45, ha="right")
plt.title("Measurement distribution")
plt.tight_layout()
plt.show()
```

### Decoded variable histogram

```python
plt.figure(figsize=(8, 4))
plt.bar(df["x"].astype(str), df["probability"])
plt.xlabel("x")
plt.ylabel("Probability")
plt.title("Output distribution of x")
plt.tight_layout()
plt.show()
```

### State vector plot (from `calculate_state_vector()`)

```python
sv_df = calculate_state_vector(qprog)

plt.figure(figsize=(10, 4))
plt.bar(sv_df["bitstring"], sv_df["probability"])
plt.xlabel("Basis state")
plt.ylabel("Probability |amplitude|²")
plt.xticks(rotation=45, ha="right")
plt.title("State vector probabilities")
plt.tight_layout()
plt.show()
```

Note: `sv_df["magnitude"]` and `sv_df["phase"]` are formatted strings (e.g. `"0.71"`, `"0.50π"`). Convert to float for numeric plots:

```python
magnitudes = sv_df["magnitude"].astype(float)
phases = sv_df["phase"].str.rstrip("π").astype(float)
```

### Expectation value vs parameter

```python
import numpy as np

angles = np.linspace(0, 2 * np.pi, 30)
vals = observe(qprog, observable=Pauli.Z(0), parameters=[{"angle": a} for a in angles])

plt.figure(figsize=(8, 4))
plt.plot(angles / np.pi, vals)
plt.xlabel("Angle (π)")
plt.ylabel("⟨Z⟩")
plt.title("Expectation value vs rotation angle")
plt.grid(True)
plt.show()
```

### Energy convergence plot

```python
res = variational_minimize(qprog, cost_function=hamiltonian,
                           initial_params={"params": [0.0, 0.0]}, max_iteration=50)
costs = [r[0] for r in res]

plt.figure(figsize=(8, 4))
plt.plot(costs)
plt.xlabel("Optimizer iteration")
plt.ylabel("Cost / Energy")
plt.title("Variational convergence")
plt.grid(True)
plt.show()
```

---

## Common patterns

### Best solution (highest probability)

```python
df = sample(qprog, num_shots=4096)
best = df.loc[df["probability"].idxmax()]
# Drop the metadata columns to get just variable values
solution = best.drop(["counts", "probability", "bitstring"]).to_dict()
```

### QAOA / combinatorial solution extraction

After variational optimization, sample with optimal parameters and rank by cost:

```python
res = variational_minimize(qprog, cost_function=hamiltonian,
                           initial_params={"params": [0.0, 0.0]}, max_iteration=100)
_, final_params = res[-1]

# Sample with optimized parameters
df = sample(qprog, parameters=final_params, num_shots=4096)
df_sorted = df.sort_values("probability", ascending=False)

# Or rank by classical cost function using es.sample() for parsed access
with ExecutionSession(qprog) as es:
    result = es.sample(parameters=final_params)
    ranked = sorted(result.parsed_counts,
                    key=lambda pc: my_cost_function(pc.state))
    for pc in ranked[:5]:
        prob = pc.shots / result.num_shots
        print(f"solution={pc.state}  p={prob:.3f}  cost={my_cost_function(pc.state):.4f}")
```

### Filter low-probability states

```python
df = sample(qprog, num_shots=2048)
clean = df[df["probability"] > 0.01].sort_values("probability", ascending=False)
```

### Multi-variable marginal distribution

```python
df = sample(qprog, num_shots=4096)

# Marginal over one variable
x_marginal = df.groupby("x")["probability"].sum().reset_index()
plt.bar(x_marginal["x"].astype(str), x_marginal["probability"])
plt.xlabel("x"); plt.ylabel("P(x)"); plt.title("Marginal P(x)")
plt.show()

# Joint distribution heatmap
import seaborn as sns
pivot = df.pivot_table(values="probability", index="x", columns="y",
                       aggfunc="sum", fill_value=0)
sns.heatmap(pivot, annot=True, fmt=".2f", cmap="Blues")
plt.title("Joint distribution P(x, y)")
plt.show()
```

### Check uniformity after Hadamard

```python
df = sample(qprog, num_shots=4096)
expected = 1.0 / len(df)
df["deviation"] = (df["probability"] - expected).abs()
print("Max deviation from uniform:", df["deviation"].max())
```

---

## Verification checklist

Before returning post-processing code, check:

- [ ] **Top-level `sample()` returns DataFrame directly** - do NOT call `.dataframe` on it; `df = sample(...)` already IS the DataFrame
- [ ] **Top-level `calculate_state_vector()` returns DataFrame directly** - same rule; `sv_df = calculate_state_vector(...)` IS the DataFrame
- [ ] **Top-level `observe()` returns float directly** - access it directly, not via `.value.real`
- [ ] **`es.sample()` returns `ExecutionDetails`** - this is where `.counts`, `.parsed_counts`, `.counts_of_output()`, `.dataframe` live
- [ ] **`es.observe()` returns `EstimationResult`** - unwrap with `.value.real`, and per element when it returns a list. Not interchangeable with top-level `observe`, which is already a float
- [ ] **Unwrapping matches the producing call** - `[r.value.real for r in data]` on floats raises `AttributeError`; a raw `EstimationResult` passed to matplotlib fails too. Check which call made the data before indexing or plotting
- [ ] **No `estimate` API** - `es.estimate`, `batch_estimate`, and `get_estimate_result` are gone; expectation values come from `observe` (preferred) or `es.observe`
- [ ] **Batch via list of dicts** - `sample(qprog, parameters=[...])` returns `list[DataFrame]`; `es.sample(parameters=[...])` returns `list[ExecutionDetails]`
- [ ] **Multiple observables give one entry per observable** - and with a parameter list too, the result is nested `values[observable][parameter_set]`; check the outer length against the observable count before plotting
- [ ] **No deprecated batch APIs** - use `es.sample(parameters=list)` not `es.batch_sample(list)`; use `es.observe(h, parameters=list)` not `es.batch_estimate(h, list)` (and prefer top-level `observe`)
- [ ] **Async results are wrapped** - `job.get_sample_result().dataframe` for shots; `job.result_value().value` for observables, and `.value` is complex so take `.real`
- [ ] **Variational result is `list[tuple[float, dict]]`** - `res[-1][0]` is cost, `res[-1][1]` is params dict
- [ ] **State vector magnitude/phase are strings** - convert with `.astype(float)` / `.str.rstrip("π").astype(float)` before numeric operations
- [ ] **Matplotlib figures have labels** - `xlabel`, `ylabel`, `title`; add `legend()` for multiple series; `tight_layout()` before `show()`
