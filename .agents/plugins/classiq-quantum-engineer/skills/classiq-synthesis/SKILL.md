---
name: classiq-synthesis
description: Use this skill whenever the user asks to synthesize a Classiq quantum circuit, configure synthesis constraints or preferences, target specific hardware backends, optimize for circuit depth/width/gate count, set output formats, access qprog properties, debug synthesis failures, or control transpilation. Always trigger for synthesize(), Constraints, Preferences, max_width, max_depth, OptimizationParameter, hardware-aware synthesis, IBM Quantum, Amazon Braket, Azure Quantum, IonQ, custom hardware settings, basis gates, connectivity map, transpilation level, qprog width/depth/ops, show(qprog). Use this skill even for simple "synthesize my circuit" requests — it owns everything from plain synthesize(main) to complex hardware-constrained synthesis.
---

# Classiq Synthesis

You are a quantum compilation expert focused on Classiq's synthesis engine. You take a modeled quantum program — a Python module ending with an `@qfunc def main(...)` — and compile it into an optimized gate-level quantum program (`qprog`). You configure constraints and preferences, target hardware backends, and debug synthesis failures.

**Your scope:** running `synthesize()` and everything around it — constraints, preferences, hardware targets, output formats, transpilation, and inspecting `qprog` properties.

**Not your scope:**
- Writing `@qfunc` / `@qperm` code → `classiq-modeling`
- Running / executing circuits → `classiq-execution`
- Analyzing gate counts, depth, hardware fit → `classiq-analyzer`
- Parsing results, plotting histograms → `classiq-post-processing`

---

## Resources

For edge cases, full parameter lists, and provider-specific backend names, read `references/synthesis-guide.md`.

---

## Core Call

If no specification regarding circuit optimization, or hardware-aware synthesis is give, simply use the minimal call.


```python
from classiq import *

# Minimal — synthesizer chooses defaults
qprog = synthesize(main)

# With constraints and preferences (see sections below)
qprog = synthesize(main, constraints=constraints, preferences=prefs)

# Visualize
show(qprog)
```

**`synthesize()` always receives `main` — never another function name.**

---

## Constraints

Constraints set **hard limits**. Synthesis raises an error if any constraint cannot be satisfied — tighten only when required by the user, and relax them when synthesis fails.

```python
from classiq import *

constraints = Constraints(
    max_width=20,                                          # Max qubit count
    max_depth=100,                                         # Max circuit depth
    optimization_parameter=OptimizationParameter.DEPTH,   # What to minimize
)
qprog = synthesize(main, constraints=constraints)
```

### OptimizationParameter

| Value | Minimizes |
|-------|-----------|
| `OptimizationParameter.DEPTH` | Circuit depth (critical path length) |
| `OptimizationParameter.WIDTH` | Qubit count |
| `"cx"` / `"ccx"` / `"ecr"` / any gate name | Count of that specific gate |

Use `optimization_parameter` **without** a matching `max_*` limit to treat it as a soft goal. Pair with `max_*` to enforce both a ceiling and a direction.

### When to use which constraint

| Goal | Constraint |
|------|-----------|
| Fit on an N-qubit device | `max_width=N` |
| Limit decoherence / T2 errors | `optimization_parameter=OptimizationParameter.DEPTH` |
| NISQ noise reduction | `optimization_parameter="cx"` (minimize two-qubit gates) |
| Minimize qubit count | `optimization_parameter=OptimizationParameter.WIDTH` |
| Prototype quickly | No constraints; add them when you know the target |

---

## Preferences

Preferences **guide** synthesis without causing failures if they can't be met.

```python
from classiq import *

prefs = Preferences(
    optimization_level=3,               # 0=none, 1=light (default), 2=medium, 3=high
    timeout_seconds=120,                # Give up after 2 min; returns best so far
    optimization_timeout_seconds=60,    # Timeout on optimization pass only
    debug_mode=True,                    # Verbose error messages (default True)
)
qprog = synthesize(main, preferences=prefs)
```

### optimization_level

`optimization_level` is an integer **0–3**. The `OptimizationLevel` enum is not
exported from `from classiq import *` — always use the integer literal.

| Value | Tradeoff |
|-------|----------|
| `0` | Fastest; no optimization pass |
| `1` | Light optimization (default) |
| `2` | Balanced |
| `3` | Best quality, slowest |

Use `0` or a short `timeout_seconds` when iterating fast; switch to `3` for
production synthesis. Only set optimization_level when the user explicitly asks
for it or when a constraint is failing at the default level.

### Output formats

Use `export(qprog, target_language)` to get a circuit string. Default is QASM 2.0.

```python
qprog = synthesize(main)

qasm2  = export(qprog)                           # OpenQASM 2.0 (default)
qasm3  = export(qprog, TargetLanguage.QASM3)     # OpenQASM 3.0
qsharp = export(qprog, TargetLanguage.QSHARP)    # Q#
qir    = export(qprog, TargetLanguage.QIR)       # QIR
cirq   = export(qprog, TargetLanguage.CIRQ_JSON) # Cirq JSON
```

| `TargetLanguage` value | Format |
|------------------------|--------|
| `TargetLanguage.QASM2` | OpenQASM 2.0 (default) |
| `TargetLanguage.QASM3` | OpenQASM 3.0 |
| `TargetLanguage.QSHARP` | Q# |
| `TargetLanguage.QIR` | Quantum Intermediate Representation |
| `TargetLanguage.CIRQ_JSON` | Cirq JSON |

To apply hardware-aware transpilation during export, pass a `TranspilationConfig`:

```python
config = TranspilationConfig(
    basis_gates=["cx", "u"],
    connectivity_map=[(0, 1), (1, 2), (2, 3)],
)
transpiled_qasm = export(qprog, TargetLanguage.QASM2, transpilation_config=config)
```

For fault-tolerant targets (Clifford+T), use `FaultTolerantTranspilationConfig` instead. It decomposes the circuit into `{h, t, s, tdg, cx, rz}` then approximates remaining RZ gates via gridsynth:

```python
config = FaultTolerantTranspilationConfig(clifford_t_approximation_error=1e-3)
clifford_t_qasm = export(qprog, TargetLanguage.QASM2, transpilation_config=config)
```

`clifford_t_approximation_error` is the total budget split equally across all RZ gates — smaller values give higher accuracy at the cost of greater depth.

---

## Hardware-Aware Synthesis

Pass backend info in `Preferences`. The synthesizer picks basis gates and respects qubit connectivity for that device.

```python
prefs = Preferences(
    backend_service_provider="IBM Quantum",
    backend_name="ibm_boston",
)
qprog = synthesize(main, preferences=prefs)
```

Backend names are **case-sensitive and provider-specific** — always verify against the provider's documentation.

### Supported providers

| Provider string | Example backends |
|----------------|-----------------|
| `"IBM Quantum"` | `"ibm_boston"`, `"ibm_pittsburgh"`, `"ibm_fez"`, `"ibm_marrakesh"` |
| `"Amazon Braket"` | `"SV1"` (simulator), `"TN1"`, `"Aria 1"`, `"Forte 1"` |
| `"Azure Quantum"` | `"ionq.qpu"`, `"quantinuum.hqs-lt-s1"` |
| `"IonQ"` | `"ionq_harmony"`, `"ionq_aria-1"` |
| `"Google"` | `"cirq-simulator"` |
| `"Classiq"` | `"simulator"` (default) |

### Custom hardware

For devices not directly listed, specify basis gates and connectivity manually:

```python
custom_hw = CustomHardwareSettings(
    basis_gates=["cx", "rz", "sx", "x"],
    connectivity_map=[(0, 1), (1, 2), (2, 3), (3, 4)],   # Linear chain
    is_symmetric_connectivity=True,
)
prefs = Preferences(custom_hardware_settings=custom_hw)
qprog = synthesize(main, preferences=prefs)
```

- `connectivity_map`: list of `(source, target)` qubit pairs. Omit for all-to-all connectivity (only set `basis_gates`).
- `is_symmetric_connectivity=True` means both qubits can act as control; `False` means first qubit is always control.
- Valid single-qubit gates: `u`, `p`, `x`, `y`, `z`, `t`, `s`, `sx`, `rx`, `ry`, `rz`, `h`, `id`, and their daggers/variants.
- Valid two-qubit gates: `cx`, `cy`, `cz`, `swap`, `rxx`, `ryy`, `rzz`, `rzx`, `ecr`, `crx`, `cry`, `crz`, `csx`, `cu`, `cp`, `ch`.

### Solovay-Kitaev (Clifford+T targets)

When the basis set has no continuous rotations, the synthesizer uses Solovay-Kitaev to approximate arbitrary angles:

```python
prefs = Preferences(solovay_kitaev_iterations=5)  # More → better approx, more gates
```

---

## Combining Constraints and Preferences

```python
constraints = Constraints(
    max_width=127,
    optimization_parameter="rzz",
)
prefs = Preferences(
    backend_service_provider="IBM Quantum",
    backend_name="ibm_boston",
    optimization_level=3,   # 3 = high; use integer, not OptimizationLevel enum
    timeout_seconds=180,
)
qprog = synthesize(main, constraints=constraints, preferences=prefs)
```

---

## Transpilation

Synthesis includes transpilation automatically. You can control the transpilation level via `Preferences`:

```python
prefs = Preferences(transpilation_option="intensive")
```

| Level | Description |
|-------|-------------|
| `"none"` | Skip transpilation entirely |
| `"decompose"` | Decompose to basis gates only — default |
| `"light"` | Light 1-qubit optimization; best for fully connected hardware |
| `"medium"` | Standard passes; better for partially connected hardware |
| `"auto_optimize"` | Platform selects based on circuit size (recommended when size is unknown) |
| `"intensive"` | Maximum optimization; slowest; best for complex connectivity |
| `"custom"` | Pass a custom Qiskit pass manager |

Heavier transpilation = better-optimized circuit, but longer compile time.

---

## Accessing Synthesis Results

```python
qprog = synthesize(main)

# Default: use get_transpiled_circuit_metrics for all metrics (width, depth, gate counts).
metrics = get_transpiled_circuit_metrics(qprog)
width = metrics.width       # Number of qubits
depth = metrics.depth       # Circuit depth
ops   = metrics.count_ops   # Gate counts: {'cx': N, 'h': M, ...}

# Exception — parametric power / parametric loops:
# get_transpiled_circuit_metrics fails or assumes power=1.
# Use get_circuit_metrics instead; metrics may be symbolic strings.
# metrics = get_circuit_metrics(qprog)

# Extra output formats (only if requested in Preferences.output_format)
print(export(qprog))                        # QASM 2.0 (default)
print(export(qprog, TargetLanguage.QSHARP)) # Q#

# Visualization
show(qprog)   # Opens circuit in platform.classiq.io/circuit
```

---

## Debugging Synthesis Failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Constraint violation error | `max_width` or `max_depth` too tight | Relax or remove the failing constraint |
| Timeout with no result | Circuit too large for time budget | Increase `timeout_seconds`, lower `OptimizationLevel`, or simplify the circuit |
| "Cannot satisfy constraints" with `LOW` optimization | Light level missed a valid solution | Retry with `OptimizationLevel.MEDIUM` or `HIGH` |
| Invalid backend name | Name mismatch (case-sensitive) | Check exact spelling with provider; common mistake: `ibm_` prefix |
| Solovay-Kitaev degrading gate count | Approximation expands circuit | Increase `solovay_kitaev_iterations` or use a basis set with `rz` |
| Circuit too wide for target hardware | Model allocates too many qubits | Add `max_width=N` where N ≤ device qubit count |

When a synthesis error is unclear, set `debug_mode=True` in `Preferences` to get verbose diagnostics from the engine.
