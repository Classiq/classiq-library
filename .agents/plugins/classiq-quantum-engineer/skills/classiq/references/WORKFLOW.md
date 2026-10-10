# Quantum Program Workflow

This document defines the step-by-step workflow to follow whenever you interact with a user. Read it at the start of every quantum task and route to the correct skill at each phase.

---

## Skill Map

Each skill covers exactly one concern. Never mix them.

| Task | Skill |
|------|-------|
| Write, design, model, implement, debug a quantum circuit in Python | `classiq-modeling` |
| Synthesize a circuit: `synthesize()`, constraints, preferences, hardware targets, output formats | `classiq-synthesis` |
| Run, execute, sample, measure, compute expectation values, copmute state vectors, optimize variationally | `classiq-execution` |
| Analyze a synthesized `.qprog`: gate counts, depth, qubit usage, hardware fit | `classiq-analyzer` |
| Parse, interpret, and visualize execution outputs: DataFrames, histograms, energy landscapes, counts | `classiq-post-processing` |

If the user asks for multiple phases in one request (e.g., "write and run"), activate skills **sequentially** in pipeline order — never blend instructions from two skills into a single response pass.

---

## Pipeline

```
[1] MODEL            [2] SYNTHESIZE         [3] EXECUTE                         [4] POST-PROCESS      [5] ANALYZE
@qfunc design  →  synthesize(main, ...)  →  sample / observe / state-vector →  parse / visualize  →  .qprog metrics
(classiq-modeling)  (classiq-synthesis)    (classiq-execution).              (classiq-post-proc.)   (classiq-analyzer)
```

### Step 1 — Model (`classiq-modeling`)

Trigger this skill whenever the user asks to implement a quantum algorithm or write Classiq Python code.

- Write `@qfunc` / `@qperm` helper functions
- Define a single `main` entry point
- Apply all uncomputation rules (check skill invariants)
- Do **not** call `synthesize()` or any execution function here

### Step 2 — Synthesize (`classiq-synthesis`)

Trigger this skill to compile the modeled circuit into a `qprog`.

- Call `synthesize(main)` with appropriate constraints and preferences
- Configure hardware targets, output formats, transpilation level
- `qprog` is the input to all downstream steps
- Call `show(qprog)` to visualize

### Step 3 — Execute (`classiq-execution`)

Trigger this skill whenever the user wants results from a circuit.

Choose the right function:

| Goal | Function |
|------|----------|
| Measurement counts / probabilities | `sample(qprog, ...)` |
| Full quantum state (simulator only) | `calculate_state_vector(qprog, ...)` |
| Single expectation value | `observe(qprog, observable, ...)` |
| Variational minimization (preferred) | `variational_minimize(qprog, ...)` |
| Several expectation values at once | `observe(qprog, observable=[obs_0, obs_1], ...)` |
| Iterative / hybrid loop | `ExecutionSession` + `es.variational_minimize` (do not pair a session with `observe`) |

**Never use `execute()`.**
**Never use `estimate()` or any `*_estimate` variant** - the estimation API was removed; expectation values go through the top-level `observe`. Batching is a list passed to `sample` / `observe`, not a `batch_*` method.

### Step 4 — Post-process (`classiq-post-processing`) — optional

Trigger this skill when the user wants to work with execution outputs: reading result DataFrames, computing derived quantities, plotting histograms or energy landscapes, interpreting bitstring distributions, or extracting meaningful quantities from `sample` / `observe` / `estimate` results.

Input: the DataFrame or scalar returned by Step 3.

### Step 5 — Analyze (`classiq-analyzer`) — optional

Trigger this skill when the user asks about the synthesized circuit itself: gate counts, depth, qubit width, hardware compatibility, NISQ-friendliness.

Input: a `.qprog` file or the `qprog` object from Step 2.

### Failure Recovery

Failure at step N often means the fix belongs at an earlier step. The individual skill files contain detailed debugging tables — use this table to decide *where* to route, not *how* to fix.

| Failure | First try | If still failing |
|---------|-----------|-----------------|
| Synthesis: uncomputation error | `classiq-modeling` — not fixable in synthesis | — |
| Synthesis: timeout or too wide | Relax constraints (`classiq-synthesis`) | Restructure circuit (`classiq-modeling`) |
| Synthesis: constraint violation | Relax or remove the failing constraint (`classiq-synthesis`) | Redesign circuit (`classiq-modeling`) |
| Auth error (any step) | `classiq-setup` | — |
| Execution: wrong parameter shape | `classiq-modeling` — fix CArray bundling | — |

---

## Task Complexity Assessment

Before routing to any skill, classify the task:

**Simple task** — a direct, named request for a single well-known algorithm or subroutine:
- "implement a QFT", "write a Grover oracle", "show me QPE for this unitary"
- The algorithm maps to exactly one catalog entry with a concrete `explore/` example
- No architectural decisions or multi-component design needed

→ Route directly to the appropriate skill. The skill will implement it from knowledge if confident, or use the library example as a reference if needed.

**Complex task** — any of the following:
- Implementing an algorithm from a paper ("implement the LCU from arXiv:XXXX")
- Vague or open-ended descriptions ("build a quantum solver for my Hamiltonian", "help me with a VQE pipeline")
- Tasks that require combining multiple sub-routines or making design decisions
- Requests that span the full pipeline ("build and run", "implement and analyze")

→ Follow the **Complex Task Pre-Pipeline** before routing to any skill:

### Complex Task Pre-Pipeline

1. **Understand the algorithm design.** Read the paper, decompose the algorithm into named sub-routines (e.g. PREPARE, SELECT, block encoding, walk operator, oracle, diffuser). Identify what each sub-routine does and what Classiq constructs map to it.

2. **Scout library building blocks.** For each identified sub-routine, search the algorithm catalog and `explore/` examples for an existing Classiq implementation. Prefer known building blocks (`qpe`, `grover_operator`, `suzuki_trotter`, `prepare_amplitudes`) over hand-rolled equivalents.

3. **Compose the design and emit a Design Brief.** Finalize the `@qfunc` hierarchy, type decisions, and building-block assignments. Then output a Design Brief in exactly this format before routing to any skill:

```
## Design Brief

**Algorithm:** <name / paper reference>

**Sub-routines:**
| Name | Role | Classiq mapping |
|------|------|----------------|
| ... | ... | ... |

**Library building blocks:**
- <function or explore/ path> — <one-line reason>

**@qfunc hierarchy:**
main
├── sub_routine_a(x, y)    @qfunc / @qperm
│   └── helper(x)          @qperm
└── sub_routine_b(z)       @qfunc

**Key type decisions:**
- <variable>: <type and size reasoning>
```

The Design Brief is the handoff artifact. Every downstream skill starts from it — do not re-derive the design inside the skill.

4. **Then follow the pipeline below**, one skill at a time.

---

## Decision Guide

Read the user's request and identify the primary intent:

```
"implement / write / design / build / create" → Task Complexity Assessment → Step 1 (classiq-modeling)
"synthesize / compile / constraints / preferences / hardware / backend / max_width / max_depth" → Step 2 (classiq-synthesis)
"run / execute / sample / measure / get results / plot" → Step 3 (classiq-execution)
"optimize / minimize / VQE / QAOA / variational" → Task Complexity Assessment → Steps 1 + 2 + 3
"plot / histogram / interpret results / parse DataFrame / energy landscape / bitstring" → Step 4 (classiq-post-processing)
"analyze / gate count / depth / which hardware / NISQ" → Step 5 (classiq-analyzer)
```

When in doubt about scope, ask one clarifying question before writing any code.

---

## Common Patterns

### Pure quantum (measure a state)

1. `classiq-modeling` → write the circuit
2. `classiq-synthesis` → `synthesize(main)` → `show(qprog)`
3. `classiq-execution` → `sample(qprog, backend="simulator", num_shots=N)`

### Variational algorithm (VQE, QAOA)

1. `classiq-modeling` → parameterized ansatz with `CReal` / `CArray[CReal, N]` params
2. `classiq-synthesis` → `synthesize(main)`
3. `classiq-execution` → `variational_minimize()` or `ExecutionSession.minimize()`

### Full pipeline with analysis

1. `classiq-modeling` → model the circuit
2. `classiq-synthesis` → synthesize with constraints/preferences
3. `classiq-execution` → run and collect results
4. `classiq-post-processing` → parse and visualize execution outputs
5. `classiq-analyzer` → inspect the synthesized circuit

---

## Hard Rules

- A modeling response must never call `synthesize`, `sample`, `observe`, `execute`, or any synthesis/execution function.
- A synthesis response must never call `sample`, `observe`, or any execution function — it produces `qprog` only.
- An execution response must never call `synthesize` on a new circuit — it receives `qprog` as input.
- Uncomputation rules apply at the modeling step, not the synthesis step. Catch them before synthesizing.
- **When adapting code from any `explore/` example**, sanitize before using it. Examples are full-pipeline notebooks and may be outdated. Strip any code outside the active skill's scope (e.g. strip synthesis and execution code when in the modeling phase). Skill rules override example patterns — never carry a banned pattern forward because the example used it.
