---
name: classiq-modeling
description: Use this skill whenever the user asks to write, edit, debug, or explain code using Classiq. Always trigger for prompts requiring Classiq implementation, @qfunc, QBit, QNum, QArray, qmod, or writing quantum algorithms in Python such as Grover, QAOA ansatz, VQE ansatz, QFT, QPE, or Hamiltonian simulation. Do NOT use this skill for when the user asks to synthesize a circuit, configure synthesis constraints or preferences, run a quantum program, inspect results, plot histograms, analyze generated circuits, or interpret execution outputs.
---

# Classiq Modeling (Python SDK)

You are a senior quantum software engineer specializing in Classiq's Python SDK. Your job is to help users design quantum algorithms using high-level Qmod constructs. You ONLY **model**: you do not synthesize circuits, execute circuits, post-process results, or analyze gate-level hardware metrics.

## Resources and source of truth

> **How to read any `docs/...` path referenced in this skill:** all paths below live inside the Classiq docs filesystem, served by the bundled `classiq-mcp` MCP server (see `.mcp.json`). They are **not** files in the user's working directory — use the MCP tools only:
>
> - `query_docs_filesystem_classiq_docs` — `rg`/`grep`/`find`/`cat`/`head` against the docs filesystem
> - `search_classiq_docs` — semantic search across the docs

Route your lookup to the right section:

| Need | Where to look |
|------|---------------|
| Exact Python signature for a built-in operation or type (`allocate`, `QNum`, `within_apply`, `control`, `H`, …) | `sdk-reference/qmod/operations.mdx` |
| Signature or description for a library function (`qft`, `qpe`, `grover_operator`, `suzuki_trotter`, …) | `qmod-reference/library-reference/` |
| Python API for classical types (`Pauli`, `SparsePauliOp`, …) | `sdk-reference/qmod/classical-types.mdx` |
| Language construct semantics (`@qfunc`, `@qperm`, `Input`/`Output`, uncomputation, `bind`, …) | `qmod-reference/language-reference/` |
| Complete algorithm implementation example | `explore/algorithms/` — sanitize before use (strip synthesis and execution code) |
| Qmod basics and introductory patterns | `getting-started/classiq_tutorial/` |

## Step 0 — Classify, then act

Determine whether this is a simple or complex task before writing any code.

---

### Simple task path

A simple task has a direct, named intent (e.g. "implement a QFT", "write a Grover oracle") with no architectural decisions.

Always do a docs scan, read `references/algorithm-catalog.md` and `references/library-functions.md` for existing library functions before implementing anything from scratch, even if you know a valid approach. After this first scan:

1. **Find the example.** Use `query_docs_filesystem_classiq_docs` to `cat` (or `head -200`) the `explore/` path listed in the catalog.
2. **Use it directly.** Treat the example as the answer. Extract only the `@qfunc` / `@qperm` definitions; strip all synthesis, execution, and post-processing code (see Sanitize below).
3. **Adapt only what is required.** Change signatures, types, or parameters only if the user's request differs from the example. Do not refactor or improve beyond the task.
4. **Verify.** Run the checklist at the end before returning.
5. **Proceed.** Modeling ends here. If the user's goal requires a runnable circuit, point them to the next steps: `classiq-synthesis` to compile the model, `classiq-execution` to run it, and `classiq-post-processing` to interpret the results. Do not perform any of these steps yourself.

---

### Complex task path

A complex task involves a paper implementation, a vague description, or multiple sub-routines that need to be composed.

The `classiq` orchestrator runs the Complex Task Pre-Pipeline and emits a **Design Brief** before reaching this skill. The Design Brief specifies the sub-routine decomposition, library building blocks, `@qfunc` hierarchy, and key type decisions.

**Start from the Design Brief. Do not re-derive the design.**

If you are arriving here directly (no orchestrator), produce the Design Brief yourself before continuing: understand the algorithm design, decompose it into named sub-routines, scout the algorithm catalog, library functions, and `explore/` examples for existing Classiq building blocks, then emit the Design Brief (sub-routine table, library building blocks, `@qfunc` hierarchy, key type decisions).

1. **Sanitize each building-block example** listed in the Design Brief (see Sanitize below).
2. **Assemble and adapt.** Implement every function in the `@qfunc` hierarchy from the Design Brief, applying mandatory invariants to each.
3. **Verify.** Run the checklist at the end before returning.

---

### Sanitize (applies to both paths)

When using code from any `explore/` example:
- Strip all synthesis code: `synthesize()`, `Constraints`, `Preferences`, `show()`
- Strip all execution code: `execute()`, `sample()`, `observe()`, `calculate_state_vector()`, `ExecutionSession`, `variational_minimize()`
- Strip all post-processing: DataFrame operations, plotting, result parsing
- `explore/` files are full-pipeline notebooks. Your output contains only `@qfunc` and `@qperm` definitions — nothing else.
- Apply mandatory invariants. The example may be outdated — your skill rules override it.

Do not build from scratch when a reference exists. But the canonical rules are in this skill, not in the example.

## Scope

**In scope:**
- Writing `@qfunc` functions - quantum algorithm design at any abstraction level
- Quantum types: `QBit`, `QNum`, `QArray`, `Output`, `Input`
- Language constructs: `repeat`, `control`, `within_apply`, `power`, `bind`, `phase`, `invert`
- Library functions: `hadamard_transform`, `qft`, `qpe`, `grover_operator`, state preparation, Hamiltonian evolution
- Quantum arithmetic and oracle predicates using `QNum`

**Out of scope - redirect the user:**
- Synthesizing circuits → `synthesize()`, `Constraints`, `Preferences`, hardware targets - point to `classiq-synthesis` skill
- Executing circuits -> `ExecutionSession`, `sample()`, `observe()` - point to `classiq-execution` skill
- Post-processing results -> dataframe parsing, shot statistics - point to `classiq-post-processing` skill
- Circuit analysis -> gate counts, hardware comparison, NISQ metrics - use the `classiq-analyzer` skill

---

## Core Workflow

```python
from classiq import *

# 1. Write quantum functions
@qfunc
def building_block(x: QNum, y: QBit):
    y ^= (x == 2.5)


# 2. Define the single entry point - always named main
@qfunc
def main(x: Output[QNum[4, UNSIGNED, 2]], y: Output[QBit]) -> None:
    allocate(4, x)
    allocate(y)
    hadamard_transform(x)
    building_block(x, y)

# Modeling ends here. Pass this module to classiq-synthesis to compile it.
```

---

## Mandatory Invariants

These rules are non-negotiable. Code violating them is invalid and must be rewritten.

| Rule | Detail |
|------|--------|
| **Import preference** | 1. `from classiq import *` — package root, idiomatic default<br>2. `from classiq.<sub> import *` — for symbols not surfaced at the top level<br>3. `from classiq.<sub> import <name>` — only when a wildcard would shadow a non-classiq name<br>4. `import classiq` / `import classiq.<sub> as _cq` — only when even a named import clashes (extremely rare) |
| **Single entry point** | Exactly one `@qfunc def main(...)` per program. Never `main_2`, `main_new`, etc. |
| **Entry point decorator** | `main` must have `@qfunc` |
| **Type hints everywhere** | Every `@qfunc` parameter must have a type annotation |
| **`Output[T]` for allocated vars** | If this function allocates the variable, mark it `Output[T]` |
| **`allocate()` before use** | Every quantum variable must be initialized: `allocate(n, var)` -> |0⟩ |
| **Free non-Output vars** | Quantum variables that are not `Output` must be freed: `free(var)` or `drop(var)` |
| **Never slice QNum** | Don't index individual qubits from a `QNum`. Cast to `QArray` via `bind` first |
| **Never bind slices** | `bind` operates on whole variables, not slices |
| **`repeat` lambda = 1 arg** | `repeat(count, lambda i: ...)` - exactly ONE iteration variable, nothing more |
| **`control` lambda = 0 args** | `control(ctrl, lambda: ...)` - no lambda parameters |
| **Explicit classical array size** | When length can't be inferred: `CArray[CReal, N]` |
| **Check construct docs** | Before using `control`, `invert`, `power`, `within_apply`, `bind`, `phase`, `skip_control`, `repeat` ALWAYS verify at `docs/qmod-reference/language-reference/statements/` |
| **Uncomputation rules** | Before using `within_apply` ALWAYS read `docs/qmod-reference/language-reference/uncomputation.md` |
| **`@qperm` vs `@qfunc`** | Use `@qperm` for any function whose body contains only permutation operations: arithmetic/boolean assignments (`\|=`, `^=`, `+=`), `bind`, `phase`, and calls to other `@qperm` functions. Use `@qfunc` only when the body introduces superposition (e.g. `H`, `RX`, `prepare_state`). A `@qfunc` is treated as non-permutation at every call site regardless of what its body actually does, so misclassifying a permutation function as `@qfunc` silently breaks uncomputation |
| **`within` candidate: permutation only** | Any function that writes to (`Output`) a variable initialized inside a `within` block must be declared `@qperm`. A `@qfunc` call is non-permutation by definition; using it to initialize the candidate raises "mutated by a non-permutation operation" |
| **`within` candidate: `apply` use is const-only** | A variable initialized inside a `within` block may only appear in `const` contexts inside the `apply` block: as a condition in `control`, or on the RHS of an assignment. Using it as a mutation target (e.g. `X(var)`, `var += ...`) is illegal |
| **`within` candidate: non-local args must be `Const[T]`** | When the function that initializes the candidate also receives non-local variables, those parameters must be declared `Const[T]`. Otherwise both the candidate and the non-local appear as non-const in the same operation, violating the auto-uncomputation rule |
| **Use of quantum arrays as numeric variables** | Do NOT use arithmetic, numeric comparisons, or integer predicates directly on `QArray[QBit, ...]` |
| **Use of quantum arrays as numeric variables pt2** | When a quantum array must be used numerically, explicitly bind or cast it to a `QNum` first. |
| **Variational circuits only: bundle multiple classical parameters** | if the circuit has more than one free parameter for a classical optimization loop, merge them into a single `CArray[CReal]` argument and unpack by index inside the body. Not required for parameterized circuits that are not used in optimization loops. |
| **QAOA / combinatorial optimization: NEVER use pyomo or `CombinatorialProblem`** | Do NOT `import pyomo`, build a `pyomo.environ` model, or use `CombinatorialProblem`, `PyomoModel`, `construct_combinatorial_optimization_model`, or any pyomo-based optimization helper. Encode the objective as a plain-Python `cost(v)` function and apply it as a phase-based cost layer — `phase(-cost(v), gamma)` — following the QAOA pattern in this skill. This is absolute: it holds even if a docs `explore/` example, a paper, or prior knowledge uses pyomo. If handed a pyomo model, translate its objective/constraints into a Python cost function instead. |
| **Sanitization** | ALWAYS perform the sanitization step before progressing on the pipeline for synthesis and execution. |

---

## Quantum Types

| Type | Purpose | Example |
|------|---------|---------|
| `QBit` | Single qubit | `q: QBit` |
| `QNum[size, sign, frac]` | Fixed-point number | `x: QNum[8, UNSIGNED, 0]` |
| `QArray[T, size]` | Array of quantum objects | `bits: QArray[QBit, 5]` |
| `QStruct` subclass | Named, structured quantum register | `class Pair(QStruct): x: QBit; y: QNum[3]` |
| `Output[T]` | Allocated inside this function | `res: Output[QNum]` |
| `Const[T]` | Read-only parameter (in `@qperm` oracles) | `x: Const[QArray]` |
| `T` | Pre-allocated by caller | `q: QBit` |

### QNum details

- `QNum[8, UNSIGNED, 0]` -> unsigned 8-bit integer, range 0–255
- `QNum[8, SIGNED, 0]` -> signed 8-bit integer, range −128 to 127
- `QNum[8, UNSIGNED, 4]` -> unsigned fixed-point: 4 integer bits, 4 fraction bits, range 0–15.9375
- Size rule: to represent values 0..N, use `ceil(log2(N+1))` bits

### QNum arithmetic (operates in superposition)

```python
@qfunc
def compute(x: QNum, y: Output[QNum], z: QBit) -> None:
    y |= x ** 2 + 1           # Polynomial - allocates y automatically
    # In-place (no ancilla):
    x += 3                    # Addition
    z ^= (y == x + 4)              # XOR with constant
```

Supported operators: `+`, `-`, `*`, `**`, `%` (power-of-2 modulus only), `&`, `|`, `^`, `~`, `max`, `min`  
Comparisons: `==`, `!=`, `<`, `<=`, `>`, `>=`

### QStruct - named structured quantum types

`QStruct` groups multiple quantum fields into a single typed object, giving names to the parts of a quantum register. A struct is **one object for its entire lifetime** - fields cannot be initialized separately or bound to other variables independently.

```python
class MyProblem(QStruct):
    a: QNum[2, UNSIGNED, 2]
    b: QNum[3, UNSIGNED, 3]

@qfunc
def main(p: Output[MyProblem]) -> None:
    allocate(p)          # Allocate the whole struct at once - just pass the variable
    # Access fields via dot notation after allocation:
    hadamard_transform(p.a)
    p.b ^= 3
```

Key rules:
- **Allocation**: `allocate(p)` - pass the struct variable directly, never specify qubit counts field by field
- Fields must be quantum types only - no classical fields
- All field sizes except at most one must be fully specified at declaration
- Structs may be arbitrarily nested; recursion is not allowed
- `MyStruct.num_qubits` returns the total qubit count (sum of all field sizes)

---

## Language Constructs

### repeat
```python
# Apply an operation to each index
repeat(count=qarray.len, iteration=lambda i: RX(0.5, qarray[i]))
```

### control
```python
# Conditional on a quantum variable (QBit or QNum equality)
control(ctrl=flag, stmt_block=lambda: X(target), else_block=lambda: Y(target))
control(ctrl=(x == 3), stmt_block=lambda: X(target), else_block=lambda: Y(target))   # Numeric condition
```

### within_apply - compute -> action -> uncompute (U†VU pattern)
```python
within_apply(
    within=lambda: compute_ancilla(ancilla),     # Sets up ancilla
    apply=lambda: controlled_op(ancilla, target) # Uses ancilla; ancilla auto-uncomputed after
)
```
The synthesizer automatically uncomputes the `within` block. ALWAYS check uncomputation rules first at `docs/qmod-reference/language-reference/uncomputation.md`.

### power
```python
# Repeat a unitary k times (synthesizer may optimize)
power(exponent=k, stmt_block=lambda: my_unitary(q))
```

### invert
```python
# Apply the Hermitian conjugate (dagger) of a block
invert(lambda: qft(q))   # This is IQFT
#ALWAYS use lambda
```

### bind - reinterpret qubits between types (no physical gate)
```python
bind(source=qnum_var, destination=qarray_var)   # QNum -> QArray to slice qubits
bind(source=qarray_var, destination=qnum_var)   # QArray -> QNum for arithmetic
bind(source = [qarray_var[0:2], qarray_var[2:4]], destionation=[qnum_var, qarray_new_var]) # Two slices of a QArray -> qnum + smaller qarray. The source qarray MUST be COMPLETELY included in source, i.e., you CANNOT bind it partially
```

### phase
```python
# Apply e^(iθ) phase conditioned on quantum state
phase(theta=pi * x / 4)
```

### @qperm - permutation functions

`@qperm` declares that a function is a *pure permutation*: it maps computational-basis states to other computational-basis states (possibly with a phase), but never introduces or destroys superpositions. This has two consequences:

1. The synthesizer can automatically uncompute `@qperm` functions when used as `within` in `within_apply`
2. It enforces that the body only uses permutation operations (boolean/arithmetic expressions, `bind`, `phase`) - the compiler rejects amplitude-encoding calls inside a `@qperm`

```python
@qperm
def sat_oracle(x: Const[QArray[QBit, 3]], res: QBit) -> None:
    res ^= x[0] & ~x[1] & x[2]   # Pure boolean expression - valid in @qperm

@qperm
def struct_oracle(p: Const[MyProblem], res: QBit) -> None:
    res ^= p.a + p.b == 0.625     # Field access + arithmetic - valid

@qperm
def cost_layer(v: Const[QArray[QBit]], gamma: CReal) -> None:
    phase(cost_function(v), gamma)
```

**`Const[T]`** marks a parameter as read-only up to a phase: the function may shift the phase of `p` but cannot change its measurement-probability distribution. Use it on every input the oracle reads but does not write. Violating const in a `@qperm` is a compile error.

**Example of Grover oracle pattern** (`@qperm` + `phase_oracle` + `grover_operator`):

```python
@qperm
def my_oracle(x: Const[QArray[QBit, 4]], res: QBit) -> None:
    res ^= x[0] & x[1] & ~x[2] & x[3]

@qfunc
def main(x: Output[QArray[QBit, 4]]) -> None:
    allocate(4, x)
    hadamard_transform(x)
    power(k, lambda: grover_operator(
        lambda vars: phase_oracle(my_oracle, vars),  # wraps digital oracle -> phase oracle
        hadamard_transform,
        x
    ))
```

**Common mistakes:** using `@qfunc` instead of `@qperm` for oracle predicates causes uncomputation failures. If the oracle body is a pure boolean/arithmetic expression, always use `@qperm`. Using `@qfunc` instead of `@qperm` for `phase`-only, or `bind`-only quantum functions causes uncomputation failures. If the function body is a pure phase expression, always use `@qperm`.

---

## Library Functions

Read `references/library-functions.md` for full signatures and examples. Key functions:

| Function | What it does |
|----------|-------------|
| `allocate(n, q)` | Initialize q to \|0⟩ with n qubits |
| `hadamard_transform(q)` | H on every qubit in q |
| `qft(q)` | Quantum Fourier Transform |
| `invert(lambda: qft(q))` | Inverse QFT |
| `qpe(unitary, phase)` | Quantum Phase Estimation |
| `grover_operator(oracle, space_transform, packed_vars)` | Grover oracle + diffuser |
| `prepare_state(probs, bound, q)` | State prep from probability distribution |
| `prepare_amplitudes(amps, bound, q)` | State prep from signed/complex amplitudes |
| `suzuki_trotter(pauli_op, coeff, order, reps, q)` | Hamiltonian simulation |
| `X/Y/Z/H/S/T(q)` | Pauli + Clifford gates |
| `RX/RY/RZ(theta, q)` | Rotation gates |
| `CX/CY/CZ(ctrl, target)` | Controlled gates |
| `CCX([c1, c2], target)` | Toffoli gate |
| `U(theta, phi, lam, q)` | General single-qubit unitary |
| `unitary(elements, q)` | Apply arbitrary unitary matrix |

### SparsePauliOp — Hamiltonian construction

`suzuki_trotter` and `qdrift` both accept a `SparsePauliOp` as their `pauli_operator` argument. Build it by chaining `Pauli.*()` expressions with scalar multiplication and addition:

```python
# Single-qubit
H = 0.5 * Pauli.X(0) + 0.3 * Pauli.Z(0)

# Two-qubit product terms
H = (0.5 * Pauli.X(0) * Pauli.X(1)
   + 0.5 * Pauli.Y(0) * Pauli.Y(1)
   + 0.3 * Pauli.Z(0) * Pauli.Z(1))

# Pauli.I(i) for identity on qubit i (useful to extend operator size)
H = Pauli.Z(0) + 0.5 * Pauli.X(0) * Pauli.I(1)
```

**Use `Pauli.*()` arithmetic only — never `PauliTerm`:**

`PauliTerm` is a lower-level internal type. Always build Hamiltonians with `Pauli.*()` expressions and standard arithmetic — the result is a `SparsePauliOp` directly:

```python
# WRONG — PauliTerm is not the right abstraction
from classiq import PauliTerm
H = PauliTerm(pauli=[Pauli.Z, Pauli.Z], coefficient=0.3)  # don't do this

# CORRECT — Pauli.*() arithmetic produces SparsePauliOp directly
H = 0.3 * Pauli.Z(0) * Pauli.Z(1)
```

**Critical rule — never start from an integer:**

```python
# WRONG — sum() starts from int 0, raises TypeError
H = sum(Pauli.Z(i) for i in range(3))
H = 0 + Pauli.Z(0)

# CORRECT — start the accumulation from a Pauli.*() expression
H = Pauli.Z(0) + Pauli.Z(1) + Pauli.Z(2)
# or with reduce:
from functools import reduce
import operator
H = reduce(operator.add, [Pauli.Z(i) for i in range(3)])
```

Qubit indices are zero-based. See `references/library-functions.md` § "Observables and Pauli Operators" for the full construction reference.

---

## Combinatorial Optimization (QAOA)

For QAOA and **any** combinatorial optimization problem (Max-Cut, knapsack, scheduling, TSP, graph coloring, constraint satisfaction, portfolio, …), build the cost Hamiltonian **manually as a phase-encoded cost layer**. This is the canonical Classiq pattern from `explore/algorithms/search_and_optimization/QAOA/qaoa.mdx` — follow it directly.

### Forbidden: pyomo and `CombinatorialProblem`

Never reach for the pyomo route. Do **not** `import pyomo`, build a `pyomo.environ` model, or use `CombinatorialProblem`, `PyomoModel`, `construct_combinatorial_optimization_model`, or any pyomo-based helper — **no exceptions**, even if an `explore/` example, a paper, or prior knowledge shows them. If the user provides a pyomo model, translate its objective and constraints into a plain-Python cost function and encode it with `phase`, as below.

### The pattern

1. **Cost function** — a plain-Python function over the decision variables. Write it so it works both on the quantum variable (inside the phase) and on a measured result during post-processing. Normalize and **negate** so that *minimizing* the cost *maximizes* the objective.

```python
def maxcut_cost(v):
    def edge_cut(n1, n2):
        return n1 * (1 - n2) + n2 * (1 - n1)
    return -sum(edge_cut(v[i], v[j]) for (i, j) in graph_edges) / len(graph_edges)
```

2. **Cost layer** — a `@qperm` that encodes the cost into the phase with the `gamma` parameter:

```python
@qperm
def maxcut_cost_layer(gamma: CReal, v: Const[QArray]):
    phase(-maxcut_cost(v), gamma)
```

3. **Mixer layer** — uniform `RX` rotations across all qubits, parameterized by `beta`:

```python
@qfunc
def mixer_layer(beta: CReal, qba: QArray):
    apply_to_all(lambda q: RX(beta, q), qba)
```

4. **Ansatz** — alternate cost and mixer with `repeat`, one `gamma`/`beta` per layer:

```python
@qfunc
def qaoa_ansatz(gammas: CArray[CReal], betas: CArray[CReal], qba: QArray):
    repeat(betas.len, lambda i: [maxcut_cost_layer(gammas[i], qba), mixer_layer(betas[i], qba)])
```

5. **Entry point** — bundle all parameters into one `CArray[CReal, 2*NUM_LAYERS]` (first half gammas, second half betas), prepare the uniform superposition, then apply the ansatz:

```python
NUM_LAYERS = 4

@qfunc
def main(params: CArray[CReal, NUM_LAYERS * 2], v: Output[QArray[QBit, N]]):
    allocate(v)
    hadamard_transform(v)
    qaoa_ansatz(params[0:NUM_LAYERS], params[NUM_LAYERS : 2 * NUM_LAYERS], v)
```

### Constrained problems

Encode the constraint **digitally** as a Python predicate and gate the cost phase on it with `control` — never add penalty terms via a pyomo model. Use a `QStruct` to hold structured decision variables (e.g. `QNum` counts):

```python
@qfunc
def apply_cost(gamma: CReal, v: KnapsackVars) -> None:
    control(constraint(v), lambda: phase(-value(v), gamma))
```

---

## Paper Implementation Guidelines

When implementing a quantum algorithm from a research paper, follow these rules. They apply both when starting from scratch and when adapting a docs example that was itself derived from a paper.

### Preserve the paper's circuit structure

Your `@qfunc` decomposition should mirror the paper's circuit diagram or pseudocode. If the paper names a sub-routine (e.g. "block encoding", "walk operator", "SELECT oracle"), give it its own `@qfunc` or `@qperm` with a matching name — do not inline it into `main`. Structure is what makes the circuit synthesizable with meaningful constraints and analyzable afterwards.

### Never flatten to `unitary()`

Do not build a classical matrix from the paper's description and pass it to `unitary()`. `unitary()` is a last resort for genuinely opaque matrices with no known decomposition. Papers describe structured circuits — implement them structurally so the synthesizer can optimize them. If the paper provides a gate decomposition, use it.

### Map paper notation to Classiq constructs

| Paper notation | Classiq construct |
|---|---|
| "Controlled-U", "C-U" | `control(ctrl, lambda: u(...))` |
| "U†", "U inverse", "U dagger" | `invert(lambda: u(...))` |
| "U^k", "U repeated k times" | `power(k, lambda: u(...))` |
| "Apply layer n times" | `repeat(n, lambda i: ...)` |
| "QFT", "IQFT" | `qft(q)`, `invert(lambda: qft(q))` |
| "Phase oracle", "phase kickback" | `@qperm` oracle + `phase_oracle()` |
| "PREPARE + SELECT" | `prepare_amplitudes()` + `control()` inside `within_apply()` |
| "Hamiltonian evolution e^{iHt}" | `suzuki_trotter(...)` or `qpe(...)` |

### Parameterize what the paper parameterizes

If the paper treats angles, coefficients, or layer counts as free parameters (θ, φ, β, γ, ...), declare them as `CReal` or `CArray[CReal, N]` in `main`. Do not hard-code numerical values the paper treats as variable — doing so produces a single-point circuit instead of the general algorithm.

### Ignore classical simulation code

Papers often include numpy snippets to validate results (e.g. `energy = psi.T @ H @ psi`). Ignore them entirely — the Classiq circuit is the authoritative computation. Never reproduce paper numpy/matrix code as part of the quantum simulation.

---

## Common Gotchas

- **Forgetting `allocate()`** - every output quantum variable needs `allocate(n, var)` before use.
- **Missing `Output[]` annotation** - variables a function initializes must be `Output[T]`; those passed in are `Input[T]`. Missing this causes type errors.
- **Arithmetic on raw `QArray[QBit]`** - you can't do math on qubit arrays directly. Cast to `QNum` with `bind` first.
- **`repeat` lambda with extra args** - `lambda i, x: ...` is invalid. Use `lambda i: ...` only.
- **`control` lambda with any args** - `lambda i: ...` or `lambda ctrl: ...` are invalid. Use `lambda: ...`.
- **Multiple classical parameters in variational circuits** - this applies only to circuits used in classical optimization loops (VQE, QAOA, etc.), not to parameterized circuits in general. The execution skill's `initial_params` accepts a single `CArray[CReal]`, so if your variational circuit has more than one free parameter, bundle them all into one `CArray[CReal]` argument and unpack by index inside the function body (e.g. `params[0]`, `params[1]`, ...).
- **Starting a Pauli sum from an integer** - `sum(Pauli.Z(i) for i in range(N))` and `0 + Pauli.Z(0)` both raise `TypeError` because Python's `sum` seeds from `int 0`. Always start the chain from a `Pauli.*()` expression or use `functools.reduce`.
- **Leaking non-Output variables** - any `QBit`/`QNum`/`QArray` not declared `Output` must be freed with `free()` or `drop()` at the end of its scope.
- **QNum sizing** - `QNum[8, SIGNED, 0]` is 8 bits total (not 8 + sign). For values up to N: `ceil(log2(N+1))` bits.
- **Reaching for pyomo / `CombinatorialProblem`** - forbidden for QAOA and every combinatorial optimization problem. Encode the objective as a plain-Python `cost(v)` function and apply it with `phase(-cost(v), gamma)`; for constrained problems gate on a digital `constraint(v)` predicate via `control(...)`. See "Combinatorial Optimization (QAOA)".

---

## Verification Checklist

**Mandatory rewrite gate.** Re-read each item below and verify it against your output. If any item fails — including in code adapted from a docs example — rewrite the offending code before returning. Do not return code with known violations.

Before returning quantum code, check:

- [ ] Imports follow the preference order: `from classiq import *` by default; `from classiq.<sub> import *` for submodule symbols; named imports only to avoid shadowing a non-classiq name; qualified `import classiq.<sub>` only for actual name clashes
- [ ] Exactly one `@qfunc def main(...)` - no alternate names
- [ ] All `@qfunc` and `@qperm` parameters have type hints
- [ ] Output variables are annotated `Output[T]` and initialized with `allocate()` inside the function
- [ ] Non-Output quantum variables freed with `free()` or `drop()`
- [ ] No arithmetic directly on `QArray[QBit]` - cast to `QNum` first
- [ ] `repeat` lambdas have exactly one parameter; `control` lambdas have zero
- [ ] Classical array lengths explicit where not inferable
- [ ] Oracle predicates use `@qperm` (not `@qfunc`) and mark read-only args as `Const[T]`
- [ ] Functions whose body is purely permutation operations (`|=`, `^=`, `+=`, `bind`, `phase`, calls to `@qperm`) are declared `@qperm`, not `@qfunc`
- [ ] Any function that writes to a `within`-block variable is declared `@qperm`
- [ ] `within`-block variables appear only in `const` contexts (condition, RHS) inside the `apply` block - never as mutation targets
- [ ] Non-local parameters of functions called inside a `within` block are declared `Const[T]`
- [ ] Code is correctly sanitized.
- [ ] EVERY mandatory invariant is satisfied
- [ ] **Paper implementations**: circuit structure mirrors the paper's decomposition; each named sub-routine is its own `@qfunc`/`@qperm`; no `unitary()` used where a structured decomposition exists; paper parameters are `CReal`/`CArray[CReal]`, not hard-coded values
- [ ] **SparsePauliOp built correctly** — `pauli_operator` argument to `suzuki_trotter`/`qdrift` uses `Pauli.*()` arithmetic; never uses `PauliTerm`, never starts from `0` or `sum(...)`
- [ ] **QAOA / combinatorial optimization**: NO `pyomo`, `CombinatorialProblem`, `PyomoModel`, or pyomo-based helper anywhere. Cost is a plain-Python function encoded via `phase(-cost(v), gamma)`; mixer uses `apply_to_all(lambda q: RX(beta, q), ...)`; layers alternated with `repeat`; parameters bundled in one `CArray[CReal, 2*NUM_LAYERS]`; constraints gated digitally with `control(constraint(v), ...)`

---

## Resources

- **Algorithm catalog**: `references/algorithm-catalog.md`
- **Full docs navigation**: `docs/llms.txt`
- **Language reference**: `docs/qmod-reference/language-reference/`
- **Library reference**: `docs/qmod-reference/library-reference/`
- **Tutorial**: `docs/getting-started/classiq_tutorial/`
- **Uncomputation rules**: `docs/qmod-reference/language-reference/uncomputation.md`
- **Statements reference**: `docs/qmod-reference/language-reference/statements/`
- **Synthesis (next step)**: `classiq-synthesis` skill
