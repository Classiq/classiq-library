# Qmod Gate & Library Function Reference

## Built-in Single-Qubit Gates

| Gate | Signature | Description |
|---|---|---|
| `H(target)` | `qbit` | Hadamard |
| `X(target)` | `qbit` | Pauli-X (NOT) |
| `Y(target)` | `qbit` | Pauli-Y |
| `Z(target)` | `qbit` | Pauli-Z |
| `S(target)` | `qbit` | S gate (√Z) |
| `SDG(target)` | `qbit` | S†  |
| `T(target)` | `qbit` | T gate (√S) |
| `TDG(target)` | `qbit` | T† |
| `SX(target)` | `qbit` | √X |
| `RX(theta, target)` | `real, qbit` | Rotation around X: e^{-i·theta/2·X} |
| `RY(theta, target)` | `real, qbit` | Rotation around Y |
| `RZ(phi, target)` | `real, qbit` | Rotation around Z |
| `PHASE(theta, target)` | `real, qbit` | Phase gate: diag(1, e^{i·theta}) |
| `U(theta, phi, lam, gam, target)` | `real×4, qbit` | Generic single-qubit unitary |

## Built-in Two-Qubit Gates

| Gate | Signature | Description |
|---|---|---|
| `CX(ctrl, target)` | `qbit, qbit` | CNOT |
| `CY(ctrl, target)` | `qbit, qbit` | Controlled-Y |
| `CZ(ctrl, target)` | `qbit, qbit` | Controlled-Z |
| `CH(ctrl, target)` | `qbit, qbit` | Controlled-H |
| `CRX(theta, ctrl, target)` | `real, qbit, qbit` | Controlled-RX |
| `CRY(theta, ctrl, target)` | `real, qbit, qbit` | Controlled-RY |
| `CRZ(phi, ctrl, target)` | `real, qbit, qbit` | Controlled-RZ |
| `CPhase(theta, ctrl, target)` | `real, qbit, qbit` | Controlled-PHASE |
| `SWAP(qbit0, qbit1)` | `qbit, qbit` | Swap |
| `ISWAP(qbit0, qbit1)` | `qbit, qbit` | iSWAP |
| `RXX(theta, target)` | `real, qbit[2]` | XX rotation |
| `RYY(theta, target)` | `real, qbit[2]` | YY rotation |
| `RZZ(theta, target)` | `real, qbit[2]` | ZZ rotation |
| `ECR(qbit0, qbit1)` | `qbit, qbit` | Echoed cross-resonance |

## Three-Qubit Gates

| Gate | Signature | Description |
|---|---|---|
| `CCX(ctrl, target)` | `qbit[2], qbit` | Toffoli — `ctrl` must be a 2-element array |
| `CSWAP(ctrl, qbit0, qbit1)` | `qbit, qbit, qbit` | Fredkin |

## Rotation Convention

All `RX/RY/RZ` gates follow: `RX(θ) = e^{-i·θ/2·X}`, same as Qiskit.

`PHASE(θ)` applies diag(1, e^{iθ}) — corresponds to Qiskit's `p(θ)`.

---

## Open Library Functions

### `hadamard_transform`

```
hadamard_transform(qba: qbit[])
```

Applies H to every qubit in the array. Equivalent to:
```
repeat (i: qba.len) { H(qba[i]); }
```

Reference: `docs/qmod-reference/library-reference/open-library-functions/hadamard-transform/`

---

### `apply_to_all`

```
apply_to_all(gate: qfunc(qbit), qba: qbit[])
```

Applies any single-qubit gate to every element:
```
apply_to_all(lambda(q) { X(q); }, reg);
```

---

### `qft` / `iqft`

```
qft(qba: qbit[])
iqft(qba: qbit[])
```

Quantum Fourier Transform and its inverse. Output is in big-endian order.

Reference: `docs/qmod-reference/library-reference/open-library-functions/qft/qft.mdx`

---

### `prepare_state`

```
prepare_state(probabilities: real[], bound: real, out: qnum)
```

Prepares a superposition state with the given probability amplitudes. `bound` is the
approximation error bound (use 0 for exact synthesis).

Example:
```
qfunc main(output x: qnum) {
  prepare_state([0.5, 0.25, 0.25, 0.0], 0, x);
}
```

Reference: `docs/qmod-reference/library-reference/open-library-functions/special-state-preparations/`

---

### `grover_operator`

```
grover_operator(
  oracle: qfunc(qbit[]),
  init_function: qfunc(qbit[]),
  target: qbit[]
)
```

Applies one Grover diffusion step: oracle → invert(init) → phase(pi) on |0…0⟩ → init.
Use inside `power` to run multiple iterations.

Example:
```
power (r) {
  grover_operator(lambda(v) {
    phase_oracle(lambda(v, res) { my_predicate(v, res); }, v);
  }, hadamard_transform, nodes);
}
```

Reference: `docs/qmod-reference/library-reference/open-library-functions/grover-operator/`

---

### `grover_search`

```
grover_search(num_iterations: int, oracle: qfunc(qbit[]), target: qbit[])
```

Combines the initialization (uniform superposition) and repeated Grover operator
application. Allocates `target` internally. `num_iterations` ≈ π/4 · √(2^n / k)
where n = qubits, k = number of solutions.

Example:
```
qfunc main(output vars: qbit[4]) {
  allocate(vars);
  grover_search(2, lambda(v) {
    phase_oracle(my_predicate, v);
  }, vars);
}
```

---

### `phase_oracle`

```
phase_oracle(predicate: qperm(qbit[], qbit), vars: qbit[])
```

Converts a `qperm` Boolean predicate into a phase oracle. Internally allocates an
ancilla, prepares |−⟩, XOR-assigns the predicate, then uncomputes.

The predicate must have signature `qperm(const vars: T, res: qbit)`.

Example:
```
qperm is_even(const x: qnum<4, UNSIGNED, 0>, res: qbit) {
  res ^= (x % 2 == 0);
}

qfunc main(output x: qnum<4, UNSIGNED, 0>) {
  allocate(4, x);
  hadamard_transform(x);
  phase_oracle(is_even, x);
}
```

---

### `unitary`

```
unitary(matrix: real[][], targets: qbit[])
```

Applies an arbitrary unitary specified as a 2^n × 2^n real-valued matrix.
The matrix must be unitary. Classiq decomposes it automatically.

Example:
```
qfunc main(output q: qbit[]) {
  allocate(1, q);
  unitary([[0.0, 1.0], [1.0, 0.0]], q);  // same as X
}
```

Reference: `docs/qmod-reference/library-reference/core-library-functions/unitary/unitary.mdx`

---

## Arithmetic Operators on `qnum`

These work in both `qfunc` and `qperm` contexts for assignment:

| Operator | Notes |
|---|---|
| `a + b`, `a - b` | Addition / subtraction |
| `a * b` | Multiplication |
| `a ** n` | Exponentiation (n is classical) |
| `a % n` | Modulo (n is classical) |
| `max(a, b)`, `min(a, b)` | Extremum |
| `a & b`, `a \| b`, `a ^ b`, `~a` | Bitwise AND, OR, XOR, NOT |
| `a == b`, `a != b` | Equality (returns `bool`) |
| `a < b`, `a > b`, `a <= b`, `a >= b` | Comparison |

**XOR assignment** (only in `qperm`):
```
res ^= boolean_expression;
```

**Standard assignment** (allocates new variable):
```
sum = a + b;    // sum is a new output variable
```
