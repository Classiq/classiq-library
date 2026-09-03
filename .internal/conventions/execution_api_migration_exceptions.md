# Execution-API migration — notebooks left as-is

This migration moved library notebooks from the old execution surface
(`execute()`, nested `ExecutionPreferences`, `ExecutionSession` around single
calls, `.estimate`/`.minimize`, `parsed_counts`/`.dataframe`, `batch_*`,
statevector backends read via `parsed_state_vector`) to the new one: free
`sample()` / `observe()`, `variational_minimize`, `calculate_state_vector`, the
high-level `CombinatorialProblem` API, DataFrame-shaped results, and a flat
`ExecutionSession` kept only for genuine multi-call loops.

**On backends and credentials:** the new free API is _not_ simulator-only.
`sample()`, `observe()`, and `ExecutionSession` all accept
`backend="provider/device"` plus `config=ProviderConfig(...)` (API keys, tokens,
CRNs) and `run_via_classiq=`. So hardware and credentialed backends **are**
expressible without a `BackendPreferences` object — e.g. `quantum_volume` now
uses `sample(qprog, backend="simulator")` with commented `backend="ibm/…"` +
`IBMConfig(...)` examples. The exceptions below are kept for _real_ reasons, never
because "the flat API can't express it".

The convention report shows `execution_interface` at **219/219 (100%)**: every
notebook is either migrated or one of the **29 reviewed exceptions** registered
in `.internal/conventions/points/point_execution_interface.py`. They are grouped
below by reason.

## 1. Deliberate multi-call `ExecutionSession` (11) — the correct new pattern

A session reused across a classical optimizer/VQE loop is _the_ intended
new-interface shape, not an old-API leftover:

- `search_and_optimization/QAOA/qaoa`, `.../grover_mixer_qaoa/gm_qaoa`,
  `logistics/vehicle_routing_problem`, `optimization/adapt_qaoa`,
  `optimization/robust_posture_optimization`, `telecom/network_traffic_optimization`,
  `finance_workshops/combi_workshop_Inequality_constriants_PO` and
  `.../combi_workshop_equality_constriants_PO`,
  `combinatorial_workshop/combinatorial_qmod_workshop_for_maxcut` — each keeps an
  `ExecutionSession` for a scipy/COBYLA optimizer loop (`es.estimate_cost` /
  `es.observe` / `es.sample`); several keep `parsed_counts` because the output is a
  `QStruct`.
- `quantum_linear_solvers/vqls/vqls_with_lcu` — keeps the session for the COBYLA
  loop; its final `simulator_statevector` measurement is a deferred
  `calculate_state_vector` refactor, but the session is kept for the loop regardless.
- `algo_design_QCE_tutorial_part_II` — two sessions (`variational_minimize` + a
  follow-up sample of the optimized params = the program run twice); needs
  `parsed_counts` on a `QStruct`. The single-execution sample was migrated to free `sample()`.
- `explicit_quantum_circuits_for_block_encoding/quantum_walks_via_efficient_blockencoding`
  — statevector post-selection **was migrated** to `calculate_state_vector`; it keeps
  one legitimate session for the ~20-iteration walk loop (`es.sample` per `k` on the
  sampling simulator).

## 2. Shot-count fidelity (3) — preserve a non-default `num_shots`

The free helper has no `num_shots` there, so a minimal old-style construct stays
purely to keep the original shot count (behavior fidelity):

- `chemistry/molecule_eigensolver` — flat `ExecutionSession(qprog_ucc, num_shots=1_000_000)` for `es.variational_minimize`.
- `finance_workshops/rainbow_options_workshop_bruteforce` — `iqae.run(..., execution_preferences=ExecutionPreferences(num_shots=20000))`.
- `telecom/radio_access_network` — migrated to `CombinatorialProblem`; keeps `combi.optimize(execution_preferences=ExecutionPreferences(num_shots=3000), …)`.

## 3. Async submit/retrieve and async batch (3)

- `the_classiq_tutorial/execution_tutorial_part2` — the tutorial's _subject_ is the
  async API; it deliberately demonstrates `ExecutionSession.submit_sample` /
  `ExecutionJob.from_id` retrieve-later. Making it synchronous would defeat its purpose.
- `physical_systems/quantum_chaos/quantum_sawtooth_map` — simulator run migrated to free
  `sample()`; the IonQ hardware path (behind `RUN_ON_HARDWARE`, default `False`) was
  **modernized** to `ExecutionSession(backend="ionq/…", config=IonQConfig(...),
run_via_classiq=True)` but deliberately keeps the async
  `submit_batch_sample → ExecutionJob.from_id → get_batch_sample_result` workflow.
- `benchmarking/randomized_benchmarking` — async batch multi-backend orchestration
  (`execute_async` + `asyncio.gather` over many (qprog, backend) pairs, feeding
  `ExecutionDetails.counts` to `RBAnalysis`). Backends are simulators (no credential
  blocker); rewriting the concurrent batch pipeline is a substantial async refactor, deferred.

## 4. Hardware path not runnable in CI (1)

- `community/.../logical_qubits/logical_qubits_by_alice_and_bob` — the simulator
  swap-test run was migrated to free `sample()`. The Alice&Bob cat-qubit hardware path
  _is_ expressible as `backend="alice_and_bob/…"` + `AliceBobConfig`, but it can't be
  re-executed/validated in CI (real cat-qubit hardware), so it's left as-is.

## 5. Not the classiq execution API (1)

- `telecom/resiliency_planning/resiliency_planning_AMD` — synthesizes with classiq, then
  runs QASM on a Qiskit Aer (AMD GPU) simulator; `parsed_counts` belongs to a custom
  shim, not the SDK. Left entirely as upstream.

## 6. Reverted to upstream — not regenerable on the current SDK/backend (2)

Migrated in an earlier wave but they cannot be re-executed on the current stack, so we
ship the upstream (old-API) version + outputs rather than a half-migrated notebook with
stale/broken outputs:

- `quantum_state_preparation/adapt_vqe/adapt_vqe` — computes exact ADAPT-VQE gradients on
  a `SIMULATOR_STATEVECTOR` backend, which classiq 1.28 rejects on `ExecutionSession`; the
  only fixes (sampling backend, or a `calculate_state_vector` gradient rewrite) change the
  exact/deterministic behavior. Deferred.
- `QML/quantum_autoencoder/quantum_autoencoder` — the migrated QNN path fails to regenerate
  (reproducible server-side error 133000), so it could not be validated. Deferred.

## 7. Legacy combinatorial VQE — 3 of 7 kept

Four legacy `construct_combinatorial_optimization_model` notebooks were rewritten to
`CombinatorialProblem` (`task_scheduling_problem`, `link_monitoring`,
`evidence_scaling_labs`, `radio_access_network`). Three do not map mechanically:

- `optimization/qaoa_in_qaoa` — subgraphs keep arbitrary node labels, so `combi.sample()["x"]`
  is a sparse bounding-box list that misaligns the legacy positional zip, and the maxcut sign
  flip needs the selection inverted.
- `technology_demonstrations/qaoa/qaoa_demonstration` — a benchmark reading `VQESolverResult`
  internals that `CombinatorialProblem` does not expose.
- `optimization/rectangles_packing/rectangles_packing_grid` — `combi.sample()["place"]` is a
  nested 3D list vs the legacy flat vector, so the floorplan-viz helpers, markdown, and test
  need a structural rewrite.

(PR #1643 left all seven untouched.)

## 8. Grading-frozen hackathon solutions (4)

Competition/workshop notebooks with "don't change" grading cells. Their statevector reads are
expressible via `calculate_state_vector` (and `parsed_counts_of_outputs` via a DataFrame
groupby), but the cells are intentionally frozen:

- `iQuHack_2025/Challenge/classiq_iQuHack_2025_final`,
  `.../Challenge_solution/our_solution/..._final_sol`,
  `.../Challenge_solution/winning_solution/..._quantum_tree_sol`,
  `iQuHack_2025/Workshop/WS_iQuHack_2025_final`.

---

## Notable migrations (for reviewers)

- **Statevector → `calculate_state_vector`:** the block-encoding trio
  (`hamiltonian_simulation_qsvt`/`_gqsp`/`_qubitization`, via the shared helper) plus the
  community notebooks `harmonic_oscillator`, `stateprep_guassian_using_qsvt`,
  `select_structures_BE`, `quantum_walks_via_efficient_blockencoding` (statevector part),
  both `advection_equation` submissions, and `algo_design_QCE_tutorial_part_I` (Ex/Sol 6A).
- **Backends via strings:** `quantum_volume` and `quantumwalk_complex_network` now use
  `backend="provider/device"` (+ `config=` for the commented hardware examples) instead of
  `BackendPreferences` objects.
- **`CombinatorialProblem`:** four combinatorial notebooks (see group 7).
- **`verbose=False`** added to `sample`/`observe`/`variational_minimize`/`calculate_state_vector`
  calls that run in loops, so regenerated outputs are not flooded with per-request
  "Submitting job to simulator" logging.
