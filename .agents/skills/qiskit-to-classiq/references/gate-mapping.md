# Gate Mapping Reference: Qiskit -> Classiq

## Conventions

- Classiq uses `from classiq import *` which brings all standard gates into scope.
- Qiskit qubit arguments are positional; Classiq gates use keyword arguments
  (`ctrl`, `target`, `qbit0`, `qbit1`). Keyword form is preferred for clarity but
  positional works too.
- All rotation angles are in radians and use the same convention in both frameworks
  unless noted.

---

## Single-qubit gates

| Qiskit gate | Classiq function | Notes |
|---|---|---|
| `I(q)` | `I(q)` | Identity |
| `H(q)` / `h(q)` | `H(q)` | Single qubit only; use `hadamard_transform(reg)` for whole registers |
| `X(q)` / `x(q)` | `X(q)` | |
| `Y(q)` / `y(q)` | `Y(q)` | |
| `Z(q)` / `z(q)` | `Z(q)` | |
| `S(q)` / `s(q)` | `S(q)` | |
| `Sdg(q)` / `sdg(q)` | `SDG(q)` | S-dagger |
| `T(q)` / `t(q)` | `T(q)` | |
| `Tdg(q)` / `tdg(q)` | `TDG(q)` | T-dagger |
| `SX(q)` / `sx(q)` | `SX(q)` | √X gate |
| `SXdg(q)` / `sxdg(q)` | `SXDG(q)` | |
| `RX(θ)(q)` / `rx(θ, q)` | `RX(theta=θ, target=q)` | Same convention |
| `RY(θ)(q)` / `ry(θ, q)` | `RY(theta=θ, target=q)` | Same convention |
| `RZ(φ)(q)` / `rz(φ, q)` | `RZ(theta=φ, target=q)` | Same convention |
| `P(λ)(q)` / `p(λ, q)` | `PHASE(theta=λ, target=q)` | Phase gate: `diag(1, e^{iλ})` |
| `U(θ,φ,λ)(q)` / `u(θ,φ,λ,q)` | `U(theta=θ, phi=φ, lam=λ, gam=0, target=q)` | Qiskit U has no global phase; set `gam=0` |
| `U1(λ)(q)` / `u1(λ,q)` | `PHASE(theta=λ, target=q)` | U1 ≡ P |
| `U2(φ,λ)(q)` / `u2(φ,λ,q)` | `U(theta=pi/2, phi=φ, lam=λ, gam=0, target=q)` | |
| `U3(θ,φ,λ)(q)` / `u3(θ,φ,λ,q)` | `U(theta=θ, phi=φ, lam=λ, gam=0, target=q)` | Same as U gate |

---

## Two-qubit gates

| Qiskit gate | Classiq function | Notes |
|---|---|---|
| `CX(c,t)` / `cx(c,t)` / `cnot(c,t)` | `CX(ctrl=c, target=t)` | |
| `CY(c,t)` / `cy(c,t)` | `CY(ctrl=c, target=t)` | |
| `CZ(c,t)` / `cz(c,t)` | `CZ(ctrl=c, target=t)` | |
| `CH(c,t)` / `ch(c,t)` | `CH(ctrl=c, target=t)` | |
| `CSX(c,t)` / `csx(c,t)` | `CSX(ctrl=c, target=t)` | |
| `SWAP(a,b)` / `swap(a,b)` | `SWAP(qbit0=a, qbit1=b)` | |
| `iSWAP` | `ISWAP(qbit0=a, qbit1=b)` | |
| `ECR` | `ECR(qbit0=a, qbit1=b)` | |
| `CRX(θ,c,t)` / `crx(θ,c,t)` | `CRX(theta=θ, ctrl=c, target=t)` | |
| `CRY(θ,c,t)` / `cry(θ,c,t)` | `CRY(theta=θ, ctrl=c, target=t)` | |
| `CRZ(φ,c,t)` / `crz(φ,c,t)` | `CRZ(theta=φ, ctrl=c, target=t)` | |
| `CP(λ,c,t)` / `cp(λ,c,t)` | `CPhase(theta=λ, ctrl=c, target=t)` | |
| `CU(θ,φ,λ,γ,c,t)` / `cu(...)` | `CU(theta=θ, phi=φ, lam=λ, gam=γ, ctrl=c, target=t)` | |
| `RXX(θ)(q)` / `rxx(θ,q0,q1)` | `RXX(theta=θ, target=q)` | `q` is a 2-qubit QArray |
| `RYY(θ)(q)` / `ryy(θ,q0,q1)` | `RYY(theta=θ, target=q)` | `q` is a 2-qubit QArray |
| `RZZ(θ)(q)` / `rzz(θ,q0,q1)` | `RZZ(theta=θ, target=q)` | `q` is a 2-qubit QArray |
| `RZX(θ)(q)` / `rzx(θ,q0,q1)` | `RZX(theta=θ, target=q)` | `q` is a 2-qubit QArray |

---

## Three-qubit gates

| Qiskit gate | Classiq approach | Notes |
|---|---|---|
| `CCX(c1,c2,t)` / `toffoli(c1,c2,t)` | `CCX(ctrl=ctrl_pair, target=t)` or `control((c1==1)&(c2==1), lambda: X(t))` | `ctrl_pair` is a 2-qubit QArray |
| `CSWAP(c,a,b)` | `control(c==1, lambda: SWAP(a, b))` | Fredkin gate |
| `CCZ` | `control((c1==1)&(c2==1), lambda: Z(t))` | |
| `C3X` / `c3x` | `control(...)` with a 3-qubit condition | Generalize with `control` |

---

## Multi-qubit and higher-level patterns

| Qiskit pattern | Classiq approach |
|---|---|
| `qc.h(range(n))` — Hadamard on every qubit | `hadamard_transform(reg)` |
| Manual QFT gate sequence | `qft(reg)` — import from classiq library |
| Manual inverse QFT | `invert(lambda: qft(reg))` |
| `UnitaryGate(matrix)` on n qubits | `unitary(elements=matrix.flatten().tolist(), target=reg)` |
| Qiskit Operator / sparse Pauli | Construct via `PauliTerm` and use Classiq Hamiltonian utilities |
| `QuantumCircuit.append(other_circuit)` | Define as a separate `@qfunc` and call it |
| `qc.barrier()` | **Remove** — no Classiq equivalent; barriers are no-ops semantically |
| `qc.measure()` / `qc.measure_all()` | **Remove from model** — measurement happens at execution time |
| `qc.reset(q)` | `free(q)` then `allocate(1, q)` — or restructure to avoid mid-circuit reset |

---

## Parameterized circuits

Qiskit uses `Parameter('θ')` and binds values at transpile/execution time.
In Classiq, parameters are just `CReal` arguments to `@qfunc` functions:

```python
# Qiskit
from qiskit.circuit import Parameter
theta = Parameter('θ')
qc = QuantumCircuit(1)
qc.ry(theta, 0)

# Classiq
@qfunc
def main(q: Output[QBit], theta: CReal) -> None:
    allocate(1, q)
    RY(theta=theta, target=q)
```

`ParameterVector('θ', n)` becomes `CArray[CReal, n]`.

---

## Angle conventions

| Gate | Qiskit matrix | Classiq matrix | Match? |
|---|---|---|---|
| `RX(θ)` | `[[cos(θ/2), -i·sin(θ/2)], ...]` | same | ✓ |
| `RY(θ)` | `[[cos(θ/2), -sin(θ/2)], ...]` | same | ✓ |
| `RZ(φ)` | `diag(e^{-iφ/2}, e^{iφ/2})` | same | ✓ |
| `P(λ)` | `diag(1, e^{iλ})` | `PHASE(λ)` = same | ✓ |
| `U(θ,φ,λ)` | three-angle, no global phase | `U(θ,φ,λ, gam=0)` | ✓ (gam=0) |

All standard rotation angles transcribe directly with no sign change.

---

## Common pitfalls

1. **Register indexing**: Qiskit allows `qc.h(qr[2])` but in Classiq you cannot
   index a `QNum` directly. Bind to a `QArray` first if you need to address
   individual qubits. See `docs/qmod-reference/language-reference/statements/bind.mdx`.

2. **Classical control flow**: Qiskit's `if_test` / `c_if` (classically-controlled
   gates) have no direct Classiq Qmod equivalent. Use `measure()` for mid-circuit
   measurement, then classical post-processing.

3. **Dynamic circuits**: Qiskit's mid-circuit measurement and feed-forward are not
   expressible in standard Qmod. Flag this to the user.

4. **Gate naming**: Qiskit method names are lowercase (`h`, `cx`); Classiq functions
   are upper/mixed case (`H`, `CX`, `RZ`). Don't mix them up.

5. **Two-qubit rotation gate target**: `RZZ`, `RXX`, `RYY` take a single `QArray[QBit, 2]`
   target in Classiq, not two separate qubits. Bundle the two qubits into one register.
