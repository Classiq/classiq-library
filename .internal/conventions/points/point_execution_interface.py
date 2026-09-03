"""Use the new execution interface, not the old one.

This is not a single rule but a *family* of signals — the SDK moved from
`execute(qprog).result_value()` and nested `ExecutionPreferences` to free
`sample()` / `observe()` (and a flat `ExecutionSession` only for deliberate
multi-call reuse), plus a DataFrame-shaped result. The individual signals live
in `_exec_signals.py`; this point unions them and the report shows a per-family
breakdown underneath it.

Note on backends/credentials: the free API is NOT simulator-only. `sample()`,
`observe()`, and `ExecutionSession` all take `backend="provider/device"` plus a
`config=ProviderConfig(...)` (API keys / tokens / CRNs) and `run_via_classiq=`,
so hardware and credentialed backends ARE expressible without a
`BackendPreferences` object. Exceptions below are kept for real reasons
(deliberate multi-call sessions, async submit/retrieve, shot-count fidelity,
grading-frozen cells, non-regenerable hardware paths, or structural rewrites) —
never because "the flat API can't express it".
"""

from . import _exec_signals
from ._model import Notebook, Point


def detect(nb: Notebook) -> list[str]:
    return _exec_signals.detect(nb)


POINT = Point(
    title="execution_interface",
    detail="execute() / ExecutionPreferences / .estimate / batch_*  ->  sample() / observe() / variational_minimize",
    description="Use the new execution interface: free sample()/observe(), no nested "
    "ExecutionPreferences, observe not .estimate, variational_minimize not .minimize, "
    "no batch_*, and a DataFrame-shaped result (no .parsed_counts / .dataframe).",
    static=True,
    detect=detect,
    fix=None,  # migration reshapes cells; handled per-family (script or agent), not one regex
    subsignals=_exec_signals.SIGNALS,
    exceptions=(
        # --- Deliberate multi-call ExecutionSession: a session reused across a
        # classical optimizer/VQE loop. This IS the correct new-interface pattern. ---
        (
            "search_and_optimization/QAOA/qaoa",
            "keeps ExecutionSession for two scipy optimizer loops (es.estimate_cost); "
            "knapsack output is a QStruct, so parsed_counts stays",
        ),
        (
            "search_and_optimization/grover_mixer_qaoa/gm_qaoa",
            "keeps ExecutionSession for both COBYLA optimizer loops (es.estimate_cost)",
        ),
        (
            "logistics/vehicle_routing_problem/vehicle_routing_problem",
            "keeps ExecutionSession for the scipy COBYLA loop (es.estimate_cost) plus a "
            "final es.sample; .dataframe access on the kept session",
        ),
        (
            "optimization/adapt_qaoa/adapt_qaoa",
            "partially migrated; keeps ExecutionSession for the vanilla-QAOA COBYLA loop "
            "(es.estimate_cost) + final es.sample, the ADAPT COBYLA loop, and the per-mixer "
            "gradient loop (es.observe); res.parsed_counts on the kept-session ExecutionDetails",
        ),
        (
            "optimization/robust_posture_optimization/robust_posture_optimization",
            "keeps ExecutionSession (es_X/es_Y/es_Z) for the scipy COBYLA optimizer loop + "
            "estimate_arm_pos; .counts on the kept-session ExecutionDetails (raw-bitstring "
            "histogram) stays",
        ),
        (
            "telecom/network_traffic_optimization/network_traffic_optimization",
            "keeps ExecutionSession for the scipy COBYLA loop (es.estimate_cost) plus a final "
            "es.sample; .dataframe access on the kept session",
        ),
        (
            "finance_workshops/combi_workshop_Inequality_constriants_PO",
            "keeps ExecutionSession for the scipy COBYLA optimizer loop (es.estimate_cost) "
            "plus a final es.sample; portfolio output is a QStruct, so parsed_counts stays",
        ),
        (
            "finance_workshops/combi_workshop_equality_constriants_PO",
            "keeps ExecutionSession for the scipy COBYLA optimizer loop (es.estimate_cost) "
            "plus a final es.sample; portfolio output is a QStruct, so parsed_counts stays",
        ),
        (
            "combinatorial_workshop/combinatorial_qmod_workshop_for_maxcut",
            "twin of QAOA/qaoa: keeps ExecutionSession for the scipy COBYLA optimizer loop "
            "(es.estimate_cost) plus a final es.sample; parsed_counts kept to match the sibling",
        ),
        (
            "quantum_linear_solvers/vqls/vqls_with_lcu",
            "keeps ExecutionSession for the scipy COBYLA optimizer loop (es.sample); the final "
            "simulator_statevector measurement (df.amplitude) is a deferred calculate_state_vector "
            "refactor, but the session is kept for the loop regardless",
        ),
        (
            "algo_design_QCE_tutorial_part_II.ipynb",
            "keeps two ExecutionSessions (variational_minimize + a follow-up sample of the "
            "optimized params = qprog executed twice); print_statistics needs parsed_counts on "
            "the QStruct output; the single-execution sample_anzatz was migrated to free sample()",
        ),
        (
            "explicit_quantum_circuits_for_block_encoding/quantum_walks_via_efficient_blockencoding",
            "statevector post-selection migrated to calculate_state_vector; keeps one legitimate "
            "ExecutionSession for the ~20-iteration quantum-walk loop (es.sample per k on the "
            "default sampling simulator, reused across the classical loop)",
        ),
        # --- Shot-count fidelity: a minimal old-style construct only to preserve a
        # non-default num_shots (the free helper has no shots parameter there). ---
        (
            "chemistry/molecule_eigensolver/molecule_eigensolver",
            "UCC path keeps a flat ExecutionSession(qprog_ucc, num_shots=1_000_000) for "
            "es.variational_minimize to preserve the non-default shot count (variational_minimize "
            "has no num_shots parameter)",
        ),
        (
            "finance_workshops/rainbow_options_workshop_bruteforce",
            "IQAE.run(..., execution_preferences=ExecutionPreferences(num_shots=20000)) is the "
            "only way to set IQAE's non-default shot count (IQAE.run has no other shots param)",
        ),
        (
            "telecom/radio_access_network/radio_access_network_positioning_antennas",
            "migrated to CombinatorialProblem; keeps ExecutionPreferences(num_shots=3000) passed to "
            "combi.optimize to preserve the non-default shot count (combi.optimize exposes no other "
            "shots parameter) — same fidelity reason as rainbow_options / molecule_eigensolver",
        ),
        # --- Deliberate async submit / retrieve-later, and async batch orchestration. ---
        (
            "the_classiq_tutorial/execution_tutorial_part2",
            "tutorial whose subject IS the async execution API: it deliberately demonstrates "
            "ExecutionSession.submit_sample/submit_observe + ExecutionJob.from_id retrieve-later; "
            "converting it to synchronous free sample() would defeat the tutorial's purpose",
        ),
        (
            "physical_systems/quantum_chaos/quantum_sawtooth_map",
            "simulator run migrated to free sample(); the IonQ hardware path (behind "
            "RUN_ON_HARDWARE, default False) was modernized to ExecutionSession(backend='ionq/...', "
            "config=IonQConfig(...), run_via_classiq=True) but deliberately keeps the async "
            "submit_batch_sample -> ExecutionJob.from_id -> get_batch_sample_result "
            "submit-now/retrieve-later workflow (ExecutionSession + .dataframe on the retrieved batch)",
        ),
        (
            "benchmarking/randomized_benchmarking/randomized_benchmarking",
            "async batch multi-backend orchestration: builds many (qprog, backend) pairs and runs "
            "them concurrently via execute_async + asyncio.gather, then feeds ExecutionDetails.counts "
            "into RBAnalysis. Backends are simulators (no credential blocker) — but rewriting the "
            "concurrent batch pipeline is a substantial async refactor, deferred",
        ),
        # --- Hardware path that cannot be re-executed in CI (no hardware/credentials). ---
        (
            "logical_qubits/logical_qubits_by_alice_and_bob",
            "simulator swap-test run migrated to free sample(); the Alice&Bob cat-qubit hardware "
            "path is expressible as backend='alice_and_bob/...' + AliceBobConfig, but it cannot be "
            "re-executed/validated in CI (real cat-qubit hardware), so left as-is per request",
        ),
        # --- Not the classiq execution API at all. ---
        (
            "telecom/resiliency_planning/resiliency_planning_AMD",
            "does not use the classiq execution API — synthesizes then runs QASM on a Qiskit "
            "Aer (AMD GPU) simulator; parsed_counts belongs to a custom ClassiqSampleResult "
            "shim that mimics classiq, not the SDK's sample(). Left entirely as upstream",
        ),
        # --- Reverted to upstream: migrated code could not be regenerated on the current
        # SDK/backend, so the upstream (old-API) version + outputs ship rather than a
        # half-migrated notebook with stale/broken outputs. ---
        (
            "quantum_state_preparation/adapt_vqe/adapt_vqe",
            "kept upstream (es.estimate / es.minimize on a SIMULATOR_STATEVECTOR backend): "
            "classiq 1.28 rejects statevector backends on ExecutionSession, and the only ways to "
            "run it (a sampling backend, or a calculate_state_vector-based gradient rewrite) would "
            "change the exact/deterministic gradients the ADAPT-VQE notebook depends on — deferred",
        ),
        (
            "QML/quantum_autoencoder/quantum_autoencoder",
            "kept upstream (execute_qnn + set_quantum_program_execution_preferences): the migrated "
            "QNN path would not regenerate on the current backend (reproducible server-side "
            "execution error 133000), so it could not be validated — deferred",
        ),
        # --- Legacy construct_combinatorial_optimization_model + VQE. Most were rewritten to
        # the CombinatorialProblem API; these three do not map mechanically. ---
        (
            "optimization/qaoa_in_qaoa/qaoa_in_qaoa",
            "legacy construct_combinatorial VQE; does not map cleanly — subgraphs keep arbitrary "
            "node labels so combi.sample()['x'] is a sparse bounding-box list (holes zero-filled) "
            "that misaligns the positional zip, and the maxcut sign flip needs the sort inverted; "
            "a correct rewrite must change node2value's indexing + selection, not just swap the API",
        ),
        (
            "technology_demonstrations/qaoa/qaoa_demonstration",
            "legacy construct_combinatorial VQE benchmark: reads VQESolverResult internals "
            "(intermediate_results / mean_all_solutions / time / Hamiltonian) that CombinatorialProblem "
            "does not expose; the high-level API drops the timing/quality benchmark this notebook exists to show",
        ),
        (
            "optimization/rectangles_packing/rectangles_packing_grid",
            "legacy construct_combinatorial VQE; the API swap maps but combi.sample()['place'] is a "
            "nested 3D list vs the legacy flat free-qubit vector, so the floorplan-viz helpers, the "
            "narrating markdown, and the test (sum(best_solution)==3) all need rewriting — a structural "
            "pass beyond an API-only migration",
        ),
        # --- Grading-frozen community hackathon solutions ("don't change" cells). The
        # statevector reads are expressible via calculate_state_vector, but the cells are frozen. ---
        (
            "Challenge/classiq_iQuHack_2025_final.ipynb",
            "grading-critical 'don't change' competition cells; reads a statevector run via "
            "parsed_state_vector amplitudes (expressible via calculate_state_vector, but frozen)",
        ),
        (
            "Challenge_solution/our_solution/classiq_iQuHack_2025_final_sol",
            "grading-critical 'don't change' competition cells; reads a statevector run via "
            "parsed_state_vector amplitudes (expressible via calculate_state_vector, but frozen)",
        ),
        (
            "classiq_iQuHack_2025_quantum_tree_sol.ipynb",
            "grading-critical 'don't change' competition cells; reads a statevector run via "
            "parsed_state_vector amplitudes (expressible via calculate_state_vector, but frozen)",
        ),
        (
            "Workshop/WS_iQuHack_2025_final.ipynb",
            "grading-frozen hackathon workshop; reads parsed_counts_of_outputs('x') on an "
            "ExecutionDetails (expressible via a DataFrame groupby, but the cells are left frozen)",
        ),
    ),
)
