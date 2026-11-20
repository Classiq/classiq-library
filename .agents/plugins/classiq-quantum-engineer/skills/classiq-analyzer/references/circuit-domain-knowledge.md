# Circuit Domain Knowledge for Quantum Program Analysis

## Circuit Depth

Circuit depth is the number of sequential gate layers - the "critical path" length. It directly determines execution time and decoherence exposure.

### Hardware context (superconducting qubits, 2024–2025 baselines)
- Single-qubit gate time: ~20–50 ns
- Two-qubit (CX/CZ) gate time: ~100–500 ns
- T2 coherence time: ~100–500 µs (best devices); ~50–200 µs (typical)
- Practical depth limit (without error correction): depth × gate_time << T2

### Depth interpretation
| Depth | Assessment |
|---|---|
| < 20 | Trivial; runs well on any NISQ device |
| 20–100 | NISQ-friendly; solid choice for current hardware |
| 100–500 | Marginal; use error mitigation (ZNE, PEC) |
| 500–2000 | Requires low-noise hardware or early fault tolerance |
| > 2000 | Fault-tolerant architecture required |

**Trapped-ion qubits** (IonQ, Quantinuum) have longer coherence times (~1 ms–1 s) but slower gates (~1–10 µs for two-qubit gates). A circuit depth of 500 is more viable on ion traps than superconductors.

## Gate Counts and Noise

### Two-qubit gates (CX, CZ, ECR, iSWAP)
These dominate circuit error because two-qubit gate fidelity is ~99–99.5% on best devices vs. ~99.9%+ for single-qubit gates. For a circuit with N two-qubit gates, approximate error:
- Expected fidelity ≈ 0.995^N (optimistic)
- At N=100: ~60% fidelity; at N=200: ~36%; at N=500: ~8%

This is why CX count is the primary quality metric for NISQ circuits.

### Single-qubit gates (H, X, Y, Z, RX, RY, RZ, U, S, T)
Fidelity is typically > 99.9%. Count matters less than structure - too many can increase depth, but they are rarely the noise bottleneck.

### T-gate significance (fault-tolerant context)
In the Clifford+T gate set (used for fault-tolerant computing):
- Clifford gates (H, S, CX, CNOT, etc.) are "cheap" - implementable directly
- T-gates require magic state distillation - each T-gate needs ~100–1000 distilled ancilla qubits
- T-count is the primary cost metric for fault-tolerant algorithms

If you see T-gates in the `count_ops` dict and the target is fault-tolerant hardware, report T-count explicitly and note that it dominates the resource overhead.

## Circuit Volume

`volume = width × depth` is a rough complexity proxy. The IBM "quantum volume" metric formalizes this as the largest square circuit (n qubits × n depth) that a device can execute reliably. To run a circuit on a device, roughly:

`width ≤ device_qubits` AND `depth ≤ device_quantum_volume_depth`

## Qubit Width

### NISQ device qubit counts (2024–2025)
| Device | Qubits | Notes |
|---|---|---|
| IBM Eagle | 127 | Heavy-hex connectivity |
| IBM Heron | 133 | Improved fidelity |
| IBM Condor | 1127 | Experimental |
| Google Sycamore | 53 | Grid connectivity |
| IonQ Aria | 25 | All-to-all, high fidelity |
| IonQ Forte | 36 | All-to-all |
| Quantinuum H2 | 56 | All-to-all |

### Auxiliary qubit overhead
Classiq synthesis may allocate auxiliary/zero registers beyond what the algorithm strictly requires, to enable more efficient decompositions. Check if `width` is significantly larger than the logical qubit count of the algorithm - this indicates heavy uncomputation or ancilla usage.

## Hardware-Aware Transpilation

When the `Analyzer` comparison table shows different depths/gate counts per backend, this reflects:
1. **Basis gate set**: IBM uses {CX, RZ, SX, X}; IonQ uses native MS gates; Quantinuum uses ZZ gates
2. **Connectivity**: superconducting devices have limited qubit connectivity (need SWAP routing); trapped-ion devices are all-to-all
3. **Hardware calibration**: Classiq synthesizes with hardware-aware routing when a target backend is specified

For NISQ execution, always compare at least 2–3 backends before committing to hardware. The comparison table identifies the optimal backend objectively.
