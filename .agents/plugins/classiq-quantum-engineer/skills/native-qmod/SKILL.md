---
name: native-qmod
description: Use when writing, editing, or debugging native Qmod programs (.qmod files). Trigger whenever the user wants to write quantum programs in Qmod native syntax (not Python SDK), asks how to express something in native Qmod, wants to understand a .qmod file, or asks about Qmod language features (qfunc, qperm, control, within-apply, repeat, qnum, qstruct, bind, power, invert, phase, etc.). Also trigger when the user wants to implement a quantum algorithm from scratch in Qmod, convert a verbal description to native Qmod code, extend an existing .qmod program, or fix a Qmod syntax/type error.
---

# Native Qmod Programmer

You are a senior quantum engineer writing idiomatic native Qmod code. Qmod is Classiq's
quantum programming language: strongly typed and declarative. You describe *what* a
computation does; the Classiq synthesis engine figures out *how* to implement it in gates.

Your outputs are always `.qmod` code blocks or `.qmod` files. Never write Python SDK code
unless the user explicitly asks for it.

---

## Step 0 — Read the docs before writing anything

> **How to read the `docs/...` and `explore/...` paths in this skill:** they are paths
> inside the Classiq docs filesystem, served by the bundled `classiq-mcp` MCP server
> (see this plugin's `.mcp.json`). They are **not** files in the user's working
> directory — do not try to read them with the local file tools. Use the MCP instead:
>
> - `query_docs_filesystem_classiq_docs` — `rg`/`grep`/`find`/`cat` against the docs filesystem
> - `search_classiq_docs` — semantic search across the docs

Before writing a single line of Qmod, read the language reference files relevant to the
constructs you plan to use. This is mandatory: Qmod has precise syntax and semantic rules
that differ from Python SDK code, and writing from memory leads to subtle errors.

**Always read these before starting:**
- `docs/qmod-reference/language-reference/functions.mdx` — qfunc/qperm declaration syntax
- `docs/qmod-reference/language-reference/quantum-types.mdx` — qbit, qnum, qstruct types
- `docs/qmod-reference/language-reference/quantum-variables.mdx` — allocate, free, lifecycle

**Read these when using the relevant construct:**

| Construct | Read |
|---|---|
| `control` | `docs/qmod-reference/language-reference/statements/control.mdx` |
| `within-apply` | `docs/qmod-reference/language-reference/statements/within-apply.mdx` |
| `bind` / `->` | `docs/qmod-reference/language-reference/statements/bind.mdx` |
| `power` / `invert` | `docs/qmod-reference/language-reference/statements/power.mdx`, `…/invert.mdx` |
| `repeat` / `if` | `docs/qmod-reference/language-reference/statements/classical-control-flow.mdx` |
| higher-order / lambda | `docs/qmod-reference/language-reference/operators.mdx` |
| uncomputation rules | `docs/qmod-reference/language-reference/uncomputation.mdx` |
| qft / grover / etc. | the matching file under `docs/qmod-reference/library-reference/open-library-functions/` |

**Also read the closest canonical example** from the list at the bottom of this file before
writing your own program — real `.qmod` files show correct syntax that you should model.

### The `explore/` directory is your pattern library

The Classiq docs include an `explore/` corpus — a rich collection of real Qmod programs
organized by topic, browsable through the `classiq-mcp` MCP server. Before writing
code, search it for implementations related to what you're building.

Structure:
```
explore/
├── algorithms/          — core quantum algorithms (Grover, QPE, QFT, QAOA, QML, …)
├── applications/        — domain applications (finance, chemistry, optimization, logistics, …)
├── functions/           — library function usage examples and arithmetic patterns
├── tutorials/           — basic and advanced tutorials, technology demonstrations
└── community/           — community implementations (block encoding, BB84, …)
```

Each topic folder typically contains two complementary files:
- **`.mdx` file** — explains the algorithm, the problem being solved, and the design decisions
- **`.qmod` file** — the native Qmod implementation you can read and adapt directly

**How to use it:** when asked to implement something, first use
`query_docs_filesystem_classiq_docs` to `find explore/ -name "*.qmod"` (or
`search_classiq_docs` for a semantic search) for related programs. Read the `.mdx` for
context and intent, then the `.qmod` for the exact syntax patterns. Adapt rather than
invent from scratch — the implementations in `explore/` are authoritative, tested
examples of idiomatic Qmod.

---

## Program Structure

Every Qmod program has exactly one entry point named `main`:

```
qfunc main(output reg: qbit[]) {
  allocate(6, reg);
  H(reg[0]);
}
```

Helper functions are declared **above** `main`:

```
qfunc bell_pair(output a: qbit, output b: qbit) {
  allocate(a);
  allocate(b);
  H(a);
  CX(a, b);
}

qfunc main(output a: qbit, output b: qbit) {
  bell_pair(a, b);
}
```

### Function keywords

- **`qfunc`** — general quantum function, can create/destroy superposition.
- **`qperm`** — permutation-only function: only maps computational-basis states to computational-basis states. Use for Boolean oracles, XOR assignments, and classical comparisons. No H, RX/RY, or any gate that creates superposition.

### `main` rules

- All quantum parameters in `main` must have the `output` modifier (the classical executor cannot pass quantum states in).
- Classical parameters are allowed: `qfunc main(r: int, output vars: qbit[])`.

**Canonical examples:**
- Simple: `explore/tutorials/basic_tutorials/entanglement/entanglement.qmod`
- Parameterized quantum program: `explore/algorithms/search_and_optimization/grover/grover.qmod`
- Multiple outputs: `explore/tutorials/basic_tutorials/grover_graph_coloring/grover_graph_coloring.qmod`

**Language reference:** `docs/qmod-reference/language-reference/functions.mdx`, `docs/qmod-reference/language-reference/quantum-entry-point.mdx`

---

## Type System

### Quantum types

| Type | Native syntax | Notes |
|---|---|---|
| Single qubit | `qbit` | |
| Qubit array (size inferred) | `qbit[]` | |
| Qubit array (fixed size) | `qbit[N]` | N is a classical int expr |
| Unsigned integer | `qnum<N, UNSIGNED, 0>` or `qnum<N, False, 0>` | |
| Signed integer | `qnum<N, SIGNED, 0>` or `qnum<N, True, 0>` | Two's complement |
| Fixed-point number | `qnum<N, SIGNED, frac>` | `frac` = fraction bits |
| Inferred qnum | `qnum` | Engine infers size from context |
| Struct | `qstruct Name { field: type; }` | Named group of quantum fields |

Prefer `UNSIGNED` / `SIGNED` over `False` / `True` for readability.

**qstruct definition** (must be at top of file, before functions):

```
qstruct RGB {
  r: qnum<4, UNSIGNED, 0>;
  g: qnum<4, UNSIGNED, 0>;
  b: qnum<4, UNSIGNED, 0>;
}

qfunc main(output pixel: RGB) {
  allocate(pixel.size, pixel);
  hadamard_transform(pixel.r);
}
```

**Type attributes** (accessed with dot notation):
- `var.size` - total qubit count of any quantum variable
- `qbit[].len` - length of a qubit array
- `qnum.is_signed`, `qnum.fraction_digits` - Signess check and number of fraction digits. Both only works for quantum numbers.

### Classical types

`int`, `real`, `bool` and their array forms (`int[]`, `real[]`, `bool[]`).
Use the constant `pi` for π in rotation angles.

**Language reference:** `docs/qmod-reference/language-reference/quantum-types.mdx`, `docs/qmod-reference/language-reference/classical-types.mdx`

---

## Variable Lifecycle

Quantum variables must be **allocated** before any use and must be **uninitialized** (freed or consumed) when they go out of scope.

### Allocation

```
// Fixed-size array
allocate(4, x);

// Let engine infer size (works for output params with a known type)
allocate(x);

// Local variable: declare type first, then allocate
aux: qbit;
allocate(1, aux);
```

### Deallocation

```
// Free a local variable — only valid when var is provably in |0⟩ (unentangled)
free(aux);
```

`free` is the manual escape hatch. Prefer `within-apply` for automatic uncomputation.

**Read the uncomputation rules:** `docs/qmod-reference/language-reference/uncomputation.mdx`

### Bind (`->`) — qubit rewiring

`->` rewires qubits between variables with zero gate cost (pure bookkeeping):

```
// Split: source becomes uninitialized, destinations become initialized
x -> {lsb, msb};

// Rejoin
{lsb, msb} -> x;
```

After the `->`, source variables are uninitialized and destinations are initialized.
Both sides must have matching total qubit counts when the split is into typed variables.

**Canonical example:** `docs/qmod-reference/language-reference/statements/bind.mdx` (Example 1: Cast)

---

## Statements

### `control` — quantum conditional

```
// Trigger when all qubits in ctrl are |1⟩
control (ctrl) {
  operation(target);
}

// Expression control (var == classical int)
control (x == 3) {
  phase(pi);
}

// Optional else block
control (flag) {
  X(a);
} else {
  Z(a);
}
```

Rules:
- The same variable cannot appear in the condition AND inside the block.
- Expression form: `<var> == <classical-expr>` where var is `qbit` or integer `qnum`.

**Language reference:** `docs/qmod-reference/language-reference/statements/control.mdx`

---

### `within-apply` — automatic uncomputation (U†VU)

The most important pattern for ancilla management. Variables initialized in `within` are
**automatically uncomputed** after the `apply` block completes.

```
within {
  // allocate and prepare ancilla
} apply {
  // use ancilla — but ONLY in const (read-only/control) contexts
  // ancilla cannot be a gate target here
}
```

The `const` restriction means: inside `apply`, variables from `within` can only be used
as a **control condition**, never as a gate target (`X(aux)` inside `apply` is illegal).

---

### `power` — unitary exponentiation

Apply a block `n` times (n can be a classical parameter):

```
power (r) {
  grover_operator(oracle, hadamard_transform, nodes);
}
```

**Canonical example:** `explore/algorithms/search_and_optimization/grover/grover.qmod`  
**Language reference:** `docs/qmod-reference/language-reference/statements/power.mdx`

---

### `invert` — adjoint / dagger

Applies the inverse (adjoint) of the enclosed block:

```
invert {
  qft(x);     // equivalent to iqft(x)
}
```

**Language reference:** `docs/qmod-reference/language-reference/statements/invert.mdx`

---

### `repeat` — classical loop

```
repeat (index: n) {
  CX(reg[index], reg[index + 1]);
}
```

`index` runs from 0 to n-1. `n` is a classical expression. Outer variables used inside
must remain initialized for the entire loop body.

**Canonical example:** `explore/tutorials/basic_tutorials/entanglement/entanglement.qmod`  
**Language reference:** `docs/qmod-reference/language-reference/statements/classical-control-flow.mdx`

---

### `if` — classical conditional

Branches at model-generation time (not a quantum superposition branch):

```
if (n > 4) {
  qft(x);
} else {
  hadamard_transform(x);
}
```

---

### `phase` — global phase

```
phase(pi);        // applies e^{iπ} = -1 phase to the current state
phase(pi / 4);
```

Commonly used inside `control` to implement phase oracles.

---

## Higher-Order Functions and Lambdas

Functions can take other functions as parameters (type `qfunc (...)`):

```
qfunc apply_twice(op: qfunc (qbit[]), target: qbit[]) {
  op(target);
  op(target);
}
```

Inline lambdas:

```
apply_twice(lambda(t) {
  H(t);
}, x);
```

Multi-parameter lambda:

```
grover_operator(
  lambda(vars) {
    phase_oracle(lambda(vars, res) {
      my_predicate(vars, res);
    }, vars);
  },
  hadamard_transform,
  nodes
);
```

**Lambda rules:**
- `repeat` iteration lambda takes **exactly one parameter** (the loop index).
- Match the parameter count to the called function's declared type.

**Language reference:** `docs/qmod-reference/language-reference/operators.mdx`

---

## Built-in Gates (Quick Reference)

See `references/gate-library.md` for the full table with notes. Most-used gates:

| Gate | Signature |
|---|---|
| `H(target)` | `qbit` |
| `X(target)` | `qbit` |
| `Y(target)`, `Z(target)` | `qbit` |
| `S(target)`, `T(target)` | `qbit` |
| `RX(theta, target)` | `real, qbit` |
| `RY(theta, target)` | `real, qbit` |
| `RZ(phi, target)` | `real, qbit` |
| `PHASE(theta, target)` | `real, qbit` |
| `CX(ctrl, target)` | `qbit, qbit` |
| `CZ(ctrl, target)` | `qbit, qbit` |
| `SWAP(qbit0, qbit1)` | `qbit, qbit` |
| `CCX(ctrl, target)` | `qbit[2], qbit` — ctrl is a 2-element array |
| `U(theta, phi, lam, gam, target)` | generic single-qubit |

---

## Open Library Functions (Quick Reference)

| Function | Typical signature | Description |
|---|---|---|
| `hadamard_transform(qba)` | `qbit[]` | H on every qubit |
| `apply_to_all(gate, qba)` | `qfunc(qbit), qbit[]` | Apply single-qubit gate to each element |
| `qft(qba)` | `qbit[]` | Quantum Fourier Transform |
| `iqft(qba)` | `qbit[]` | Inverse QFT |
| `prepare_state(probs, bound, var)` | `real[], real, qnum` | State prep from probability vector |
| `grover_operator(oracle, init_fn, vars)` | | Single Grover diffusion step |
| `grover_search(num_iter, oracle, vars)` | | Full Grover search (allocate + diffuse) |
| `phase_oracle(predicate, vars)` | | Build phase oracle from a `qperm` predicate |
| `unitary(matrix, targets)` | `real[][], qbit[]` | Arbitrary unitary from matrix |

Library references:
- `docs/qmod-reference/library-reference/open-library-functions/qft/qft.mdx`
- `docs/qmod-reference/library-reference/open-library-functions/grover-operator/grover-operator.mdx`
- `docs/qmod-reference/library-reference/open-library-functions/amplitude-amplification/`
- `docs/qmod-reference/library-reference/open-library-functions/special-state-preparations/`

---

## Verification Checklist

Before returning any Qmod code:

- [ ] Exactly one `qfunc main(...)` entry point
- [ ] All quantum parameters in `main` have the `output` modifier
- [ ] Every quantum variable is allocated before use
- [ ] Local variables (`name: type;`) are allocated and freed/uninitialized before the function ends
- [ ] Variables in `within` block are only used in **const** (control/condition) contexts in `apply` — never as direct gate targets inside `apply`
- [ ] `qperm` functions contain only permutation-safe operations (XOR assignments, comparisons, arithmetic without H/rotation gates)
- [ ] `repeat` body uses the loop index variable, not a hardcoded literal for the iteration
- [ ] No bare index access on `qnum` without a prior bind
- [ ] Lambda parameter counts match the expected function type
- [ ] `free(var)` is called only for when the variable is provably in |0⟩ (unentangled) and is not an `output`
- [ ] `qstruct` definitions appear at the top of the file, before any `qfunc`/`qperm`