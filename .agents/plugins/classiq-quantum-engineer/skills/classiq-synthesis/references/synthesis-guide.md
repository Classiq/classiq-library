# Synthesis Guide

Synthesis compiles a high-level Qmod model into an optimized gate-level quantum circuit. Classiq's synthesizer explores the space of circuit implementations and selects the best one according to your constraints and preferences.

```python
from classiq import *
# Minimal synthesis: Just pass main
qprog = synthesize(main)
# Extended version using create_model() - also works:
qprog = synthesize(create_model(main))

```

---

## Constraints

Constraints define **hard limits** the synthesizer must satisfy. Synthesis fails (raises an error) if the constraints cannot be met. Tighten or remove them when that happens.

```python
from classiq import *
constraints = Constraints(
    max_width=20,                                       # Maximum number of qubits
    max_depth=100,                                      # Maximum circuit depth
    optimization_parameter=OptimizationParameter.DEPTH  # What to minimize (Depth)
)
qprog = synthesize(main, constraints=constraints)
```

```python
from classiq import *
constraints = Constraints(
    max_width=20,                                       # Maximum number of qubits
    max_depth=100,                                      # Maximum circuit depth
    optimization_parameter="cx"  # What to minimize (CX counts)
)
qprog = synthesize(main, constraints=constraints)
```


### OptimizationParameter choices

| Value | What the synthesizer minimizes |
|-------|-------------------------------|
| `OptimizationParameter.DEPTH` | Critical path length (circuit depth) |
| `OptimizationParameter.WIDTH` | Number of qubits |
| `"gate"` (e.g. `"cx"`, `"ccx"`, `"ecr"`) | Any available gate count |

### When to use each constraint

| Goal | Constraint |
|------|-----------|
| Must fit on an N-qubit device | `max_width=N` |
| Must complete within N gate layers | `max_depth=N` |
| Minimize decoherence / T2 errors | `optimization_parameter=OptimizationParameter.DEPTH` |
| Minimize qubit count | `optimization_parameter=OptimizationParameter.WIDTH` |
| Minimize noise on NISQ hardware | `optimization_parameter="two_qubit_gate"` |
| No hard requirement - just try to be shallow | `optimization_parameter=OptimizationParameter.DEPTH` (no max_depth) |

---

## Preferences

Preferences **guide** synthesis without causing failures if they can't be met. They control synthesis speed, quality, output formats, and hardware targets.

```python
from classiq import *

prefs = Preferences(
    optimization_level=OptimizationLevel.HIGH,  # Trade synthesis time for circuit quality
    timeout_seconds=120,                         # Give up after 2 min (returns best so far)
    debug_mode=True,                             # Verbose error messages
)
qprog = synthesize(main, preferences=prefs)
```

### OptimizationLevel

| Level | Trade-off |
|-------|-----------|
| `OptimizationLevel.NONE` | Fastest; no optimization pass |
| `OptimizationLevel.LOW` | Light optimization |
| `OptimizationLevel.MEDIUM` | Balanced (default) |
| `OptimizationLevel.HIGH` | Best quality, slowest synthesis |

Only modify optimization level if explicitly asked for optimization. Otherwise, do not use this feature.

Use `OptimizationLevel.NONE` or a short `timeout_seconds` when prototyping to get fast feedback,
then switch to `HIGH` for final synthesis.

### Exporting to other formats

Use `export(qprog, target_language)` to get a circuit string in any format. `TargetLanguage` is a `StrEnum`:

```python
qasm2_str = export(qprog)                            # QASM 2.0 (default)
qasm3_str = export(qprog, TargetLanguage.QASM3)
qsharp_str = export(qprog, TargetLanguage.QSHARP)
qir_str   = export(qprog, TargetLanguage.QIR)
cirq_str  = export(qprog, TargetLanguage.CIRQ_JSON)
```

| `TargetLanguage` value | Format |
|------------------------|--------|
| `TargetLanguage.QASM2` | OpenQASM 2.0 (default) |
| `TargetLanguage.QASM3` | OpenQASM 3.0 |
| `TargetLanguage.QSHARP` | Q# (Microsoft) |
| `TargetLanguage.QIR` | Quantum Intermediate Representation |
| `TargetLanguage.CIRQ_JSON` | Cirq JSON |

---

## Hardware-Aware Synthesis

Pass `Preferences` with backend info to synthesize for a specific device. The synthesizer
selects basis gates and respects qubit connectivity for that backend.

```python
prefs = Preferences(
    backend_service_provider="IBM Quantum",
    backend_name="ibm_brisbane"
)
qprog = synthesize(main, preferences=prefs)
```

Backend names are **case-sensitive and provider-specific** - verify them in the provider's docs.

### Common providers and example backends

| Provider string | Example backends |
|----------------|-----------------|
| `"IBM Quantum"` | `"ibm_brisbane"`, `"ibm_kyoto"`, `"ibm_torino"`, `"ibm_sherbrooke"` |
| `"Amazon Braket"` | `"SV1"` (simulator), `"TN1"`, `"Aria 1"`, `"Forte 1"` |
| `"Azure Quantum"` | `"ionq.qpu"`, `"quantinuum.hqs-lt-s1"` |
| `"IonQ"` | `"ionq_harmony"`, `"ionq_aria-1"` |
| `"Google"` | `"cirq-simulator"` |
| `"Classiq"` | `"simulator"` (default if nothing specified) |

### Custom hardware settings

For novel hardware not directly supported, specify basis gates and connectivity manually:

```python
from classiq import CustomHardwareSettings

custom_hw = CustomHardwareSettings(
    basis_gates=["cx", "u3"],                          # Native gate set
    connectivity_map=[[0,1],[1,2],[2,3],[3,4]],        # Qubit pairs (linear chain)
)
prefs = Preferences(custom_hardware_settings=custom_hw)
qprog = synthesize(main, preferences=prefs)
```

The connectivity map is a list of `[source, target]` pairs. For all-to-all connectivity,
omit `connectivity_map` - only set `basis_gates`.

### Solovay-Kitaev approximation

When the target basis set doesn't include continuous rotations (e.g., Clifford+T only),
Solovay-Kitaev approximates arbitrary rotations as discrete gate sequences:

```python
prefs = Preferences(
    solovay_kitaev_iterations=5   # More iterations -> better approximation, more gates
)
```

---

## Combining Constraints and Preferences

Both can be passed together:

```python
constraints = Constraints(
    max_width=127,
    optimization_parameter=OptimizationParameter.DEPTH
)
prefs = Preferences(
    backend_service_provider="IBM Quantum",
    backend_name="ibm_brisbane",
    optimization_level=OptimizationLevel.HIGH,
    timeout_seconds=180
)
qprog = synthesize(main, constraints=constraints, preferences=prefs)
```

---

## Accessing Synthesis Results

```python
qprog = synthesize(main)

# Default: use get_transpiled_circuit_metrics for all metrics (width, depth, gate counts).
metrics = get_transpiled_circuit_metrics(qprog)
width = metrics.width  # Number of qubits
depth = metrics.depth  # Circuit depth
ops   = metrics.count_ops  # Gate counts: {'cx': N, 'h': M, ...}

# Exception — parametric power / parametric loops:
# get_transpiled_circuit_metrics fails or assumes power=1.
# Use get_circuit_metrics instead; depth and other metrics may be symbolic strings,
# e.g. 'Max(172 * reps, 2315 * reps, ...)'. Evaluate at the relevant parameter value.
# metrics = get_circuit_metrics(qprog)

# Visualization
show(qprog)  # Opens platform.classiq.io/circuit in browser
```
---

## Transpilation

After synthesis the circuit is automatically transpiled to the target backend's basis gates.
Transpilation level can be set explicitly (when not using a specific backend):

| Level | Description |
|-------|-------------|
| `"none"` | Skip transpilation entirely |
| `"decompose"` | Only decompose to basis gates, no optimization |
| `"light"` | Minimal 1-qubit optimization |
| `"medium"` | Standard optimization passes |
| `"auto_optimize"` | Auto-select based on circuit size (recommended for unknown sizes) |
| `"intensive"` | Maximum optimization (can be slow on large circuits) |
| `"custom"` | Pass a custom Qiskit pass manager |
