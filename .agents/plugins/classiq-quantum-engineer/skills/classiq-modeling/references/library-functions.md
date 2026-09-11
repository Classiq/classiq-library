# Library Functions Reference

## Initialization

### allocate
Initialize a quantum variable to |0⟩:
```python
allocate(num_qubits=4, target=q)   # q must be Output[QArray], Output[QNum] or similar. It will be allocated 4 qubits.
allocate(4, q)                     # Positional shorthand
```

---

## Standard Gates (Core Library)

An exhaustive list of core gates used in Classiq can be accessed at `docs/sdk-reference/qmod/functions/core_library/standard_gates.md`. ALWAYS check this list for correct usage of core gates.

### Arbitrary unitary matrix
```python
unitary(
    elements=[[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]],  # Row-major unitary matrix. 
    target=q
)
```

---

## Open Library - Transforms

### hadamard_transform
Apply H to every qubit in the register:
```python
hadamard_transform(target=q)
```

### qft - Quantum Fourier Transform
```python
qft(target=q)          
invert(lambda: qft(q))   # Inverse QFT (IQFT)
```

### qpe - Quantum Phase Estimation
Estimates θ such that U|ψ⟩ = e^(2πiθ)|ψ⟩:
```python
qpe(
    unitary=lambda: my_unitary(eigenstate),   # QCallable — the unitary operator U
    phase=phase_register                       # QNum — must be pre-allocated, initialized to |0⟩
)
```
`phase` is **not** `Output[QNum]` — it must be allocated before the call (e.g. `allocate(n, phase_register)`).
The phase register size determines precision: n qubits → 2ⁿ phase bins.

---

## Open Library - Search & Amplification

### grover_operator
Builds the Grover oracle + diffuser:
```python
grover_operator(
    oracle=lambda: phase_oracle(packed_vars),           # Marks good states with phase flip
    space_transform=lambda: hadamard_transform(vars),   # State preparation (e.g., H^n)
    packed_vars=vars                                    # The register being searched
)
# Apply k times to amplify:
power(exponent=k, stmt_block=lambda: grover_operator(oracle, prep, vars))
```

### exact_amplitude_amplification
Exact amplitude amplification given a **known** amplitude of the good state:
```python
exact_amplitude_amplification(
    amplitude=a,                              # CReal — known amplitude of |ψ_good⟩ in the initial state
    oracle=lambda: phase_oracle(vars),        # QCallable[QArray[QBit]] — marks good states
    space_transform=lambda: prepare(vars),    # QCallable[QArray[QBit]] — state preparation
    packed_qvars=vars                         # QArray[QBit] — the register (note: packed_qvars, not packed_vars)
)
```
This function prepares the initial state internally via `space_transform` and amplifies exactly to |ψ_good⟩.
Use `amplitude_amplification(reps, oracle, space_transform, packed_qvars)` when the amplitude is not known
and you want to specify the number of repetitions manually.

---

## Open Library - State Preparation

### prepare_state
Prepare a quantum state from a **normalized probability distribution** (real, non-negative):
```python
prepare_state(
    probabilities=[0.5, 0.25, 0.125, 0.125],   # Must sum to 1.0
    bound=0.01,                                  # Max L2 approximation error
    out=q                                     # Output QArray
)
```

### prepare_amplitudes
Prepare a quantum state from **signed or complex amplitudes**:
```python
prepare_amplitudes(
    amplitudes=[0.5, -0.5, 0.5, -0.5],   # Can be negative or complex; must be normalized
    bound=0.01,
    out=q
)
```

### Special state preparations

```python
# Bell state |Φ+⟩ = (|00⟩+|11⟩)/√2 (state_num 0–3 selects which Bell state)
prepare_bell_state(state_num=0, qpair=q)       # q: Output[QArray[QBit, 2]]

# GHZ state (|00…0⟩ + |11…1⟩)/√2
prepare_ghz_state(size = 10, q=q)           # q: QArray[QBit, n]

# Uniform superposition over first m basis states (m need not be a power of 2)
prepare_uniform_trimmed_state(m=k, q=q)        # q: QArray[QBit] (uninitialized)

# Uniform superposition over an integer interval [start, end)
prepare_uniform_interval_state(start=a, end=b, q=q)   # q: QNum (uninitialized)

# Exponential distribution state
prepare_exponential_state(rate=c, q=q)         # rate: CInt
```

---

## Open Library - Hamiltonian Simulation

### suzuki_trotter
Simulate Hamiltonian time evolution H via product formula decomposition:
```python
suzuki_trotter(
    pauli_operator=hamiltonian,       # SparsePauliOp (build with Pauli.*() additions)
    evolution_coefficient=t,          # CReal evolution time
    order=2,                          # CInt Trotter order: 1 (Lie-Trotter) or 2 (Suzuki-Trotter)
    repetitions=10,                   # CInt number of Trotter steps (more → more accurate)
    qbv=q                             # QArray[QBit] target register
)
```

Higher `repetitions` improves approximation quality but increases circuit depth.
Second-order (`order=2`) requires ~2× more gates than first-order but is more accurate for the same `repetitions`.

### qdrift
Simulate Hamiltonian time evolution via the stochastic qDRIFT protocol (random
compiler — samples one Pauli term per step according to coefficient weights):
```python
qdrift(
    pauli_operator=hamiltonian,   # SparsePauliOp — same construction as suzuki_trotter
    evolution_coefficient=t,      # CReal evolution time
    num_qdrift=N,                 # CInt number of stochastic steps (N = ceil(2λ²t²/ε))
    qbv=q                         # QArray[QBit] target register
)
```

Prefer `qdrift` over a manual per-term Pauli-rotation loop when the Hamiltonian
has many non-sparse terms. Use `suzuki_trotter` when a deterministic product formula
is preferred.

### linear_pauli_rotations
Apply rotations R(e^(iθ P)) conditioned on a quantum register:
```python
linear_pauli_rotations(
    bases=[Pauli.Z, Pauli.Y],   # CArray[Pauli] — Pauli enum values, NOT strings
    slopes=[2.0, 1.0],          # CArray[CReal] — rotation slopes (angle = slope*x + offset)
    offsets=[0.0, 0.0],         # CArray[CReal] — rotation offsets
    x=register,                 # QArray[QBit] — control register (value drives the angle)
    q=indicator,                # QArray[QBit] — one target qubit per basis entry
)
```

---

## Observables and Pauli Operators

Both `suzuki_trotter` and `qdrift` accept a `SparsePauliOp` as `pauli_operator`.
Build it by adding `Pauli.*()` expressions — the result type is `SparsePauliOp`.

```python
from classiq import *

# Build a SparsePauliOp by adding Pauli.*() terms
term1 = Pauli.Z(0)                        # Z⊗I  (SparsePauliOp)
term2 = 0.5 * Pauli.X(0) * Pauli.Y(1)   # 0.5 * X⊗Y
hamiltonian = term1 + term2               # SparsePauliOp — pass directly to suzuki_trotter / qdrift

# Suzuki-Trotter:
suzuki_trotter(pauli_operator=hamiltonian, evolution_coefficient=0.1, order=2, repetitions=5, qbv=q)

# QDrift:
qdrift(pauli_operator=hamiltonian, evolution_coefficient=0.1, num_qdrift=20, qbv=q)
```

**SparsePauliOp construction rules:**
- Always start the chain from a `Pauli.*()` expression, never from an integer.
- `sum(Pauli.Z(n) for n in range(N))` is **illegal** — `sum` starts from `0`.
- `0 + 0.3 * Pauli.X(0)` is **illegal** for the same reason.
- Correct alternative: `Pauli.Z(0) + Pauli.Z(1) + Pauli.Z(2)` (explicit chain).
- **Never use `PauliTerm`** — it is a lower-level internal type. Use `Pauli.*()` arithmetic exclusively; the result is already a `SparsePauliOp`.

---

## Quantum Arithmetic - Detailed Reference

Arithmetic on `QNum` works through the `|=` operator (allocation + assignment in one step):

```python
@qfunc
def arithmetic_demo(x: QNum[4, UNSIGNED, 0], y: Output[QNum]) -> None:
    y |= x ** 2 + 1        # Squaring then offset
    y |= (x + 3) % 8       # Modular addition (mod must be power of 2)
    y |= x & 7             # Bitwise AND
    y |= x ^ 5             # Bitwise XOR with constant
    y |= max(x, 3)         # Maximum
```

### In-place operations (modify x directly, no ancilla result register)
```python
x += 3       # x ← x + 3
x ^= mask    # x ← x XOR mask
```

### Predicate / oracle pattern
Predicates assign a Boolean expression to a single-qubit indicator:
```python
@qfunc
def mark_good_states(x: QNum, ind: Output[QBit]) -> None:
    ind |= x > 5
    # or:
    ind |= (x ** 2) == 25
    # or complex predicate:
    ind |= (x >= 3) & (x <= 7)
```

### Common arithmetic pitfalls
- `%` only works with **power-of-2 modulus** in Qmod; for arbitrary modulus use Classiq library functions
- Integer overflow wraps around silently - size your `QNum` to fit the full result range
- Floating-point constants in arithmetic expressions are automatically discretized

---

## Variational / Parameterized Circuits

For QAOA, VQE, and other variational algorithms, use `CReal` or `CArray[CReal]` for classical parameters:

```python
from classiq import *

size = 10

@qfunc
def ansatz_layer(theta: CArray[CReal, size], q: QArray[QBit]) -> None:
    repeat(count=q.len, iteration=lambda i: RY(theta[i], q[i]))
    repeat(count=q.len - 1, iteration=lambda i: CX(q[i], q[i+1]))

@qfunc
def main(theta: CReal, result: Output[QArray[QBit, 4]]) -> None:
    allocate(4, result)
    hadamard_transform(result)
    ansatz_layer(theta, result)
```

The classical parameters become execution-time inputs, passed when calling `sample()` or `observe()`.

