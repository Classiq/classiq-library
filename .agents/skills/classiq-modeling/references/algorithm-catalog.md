# Algorithm Catalog

Before implementing any quantum algorithm or circuit pattern, check this catalog first.
If the algorithm or pattern appears here, read the listed `explore/` path using
`query_docs_filesystem_classiq_docs` and adapt that implementation — do not build from scratch.

```
cat /explore/path/to/file.mdx
# For long files, read the implementation section first:
head -200 /explore/path/to/file.mdx
```

The `explore/` entries are authoritative, tested Python SDK implementations with full
explanations. Adapting them is faster and more correct than building from scratch.

---

## Foundational

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| Bell state / Entanglement | Prepare Bell and GHZ states | `prepare_bell_state`, `prepare_ghz_state`, `CX`, `H` | `explore/tutorials/basic_tutorials/entanglement/entanglement.mdx` |
| Quantum Teleportation | Teleport a qubit state using entanglement + classical bits | `prepare_bell_state`, `control`, measurement | `explore/algorithms/foundational/quantum_teleportation/quantum_teleportation.mdx` |
| Deutsch-Jozsa | Determine if a function is constant or balanced | `hadamard_transform`, `@qperm` oracle | `explore/algorithms/foundational/deutsch_jozsa/deutsch_jozsa.mdx` |
| Bernstein-Vazirani | Find hidden bit string from dot-product oracle | `hadamard_transform`, `@qperm` oracle | `explore/algorithms/foundational/bernstein_vazirani/bernstein_vazirani.mdx` |
| Simon's Algorithm | Find hidden XOR mask using period finding | `hadamard_transform`, `@qperm` oracle | `explore/algorithms/foundational/simon/simon.mdx` |
| State preparation | Prepare arbitrary states from probability/amplitude vectors | `prepare_state`, `prepare_amplitudes` | `explore/tutorials/basic_tutorials/prepare_state/prepare_state.mdx` |

---

## Search & Optimization

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| Grover Search | Amplitude amplification search; oracle + diffuser pattern | `grover_operator`, `power`, `phase_oracle`, `@qperm` | `explore/algorithms/search_and_optimization/grover/grover.mdx` |
| Grover graph coloring | Grover applied to a constraint satisfaction problem | `grover_operator`, `@qperm` oracle, `QStruct` | `explore/tutorials/basic_tutorials/grover_graph_coloring/grover_graph_coloring.mdx` |
| QAOA | Cost + mixer alternation for combinatorial optimization. Encode the cost as a phase-based layer — `phase(-cost(v), gamma)` — with a plain-Python `cost(v)`; mixer via `apply_to_all(RX)`; layers via `repeat`; params in one `CArray[CReal, 2*NUM_LAYERS]`. **NEVER use pyomo / `CombinatorialProblem`.** | `phase`, `apply_to_all`, `RX`, `repeat`, `CArray[CReal]`, `control` (constraints) | `explore/algorithms/search_and_optimization/QAOA/qaoa.mdx` |
| Grover-Mixer QAOA | QAOA with Grover operator as mixer | `grover_operator`, QAOA pattern | `explore/algorithms/search_and_optimization/grover_mixer_qaoa/gm_qaoa.mdx` |
| DQI (Max-XOR-SAT) | Decoded Quantum Interferometry for combinatorial optimization | advanced | `explore/algorithms/search_and_optimization/dqi/dqi_max_xorsat.mdx` |

---

## Quantum Primitives

| Pattern | Description | Key constructs | Path |
|---------|-------------|----------------|------|
| LCU (Linear Combination of Unitaries) | Encode a matrix as a linear combination of unitaries; PREPARE + SELECT pattern | `prepare_amplitudes`, `control`, `within_apply` | `explore/tutorials/basic_tutorials/quantum_primitives/linear_combination_of_unitaries/linear_combination_of_unitaries.mdx` |
| Hadamard Test | Estimate Re⟨ψ\|U\|ψ⟩ via ancilla control qubit | `H`, `control`, `within_apply` | `explore/algorithms/quantum_primitives/hadamard_test/hadamard_test.mdx` |
| SWAP Test | Estimate \|⟨ψ\|φ⟩\|² via ancilla + SWAP | `H`, `control`, `SWAP` | `explore/algorithms/quantum_primitives/swap_test/swap_test.mdx` |
| GQSP | Generalized Quantum Signal Processing — polynomial transformations of block-encoded matrices | `gqsp` open library | `explore/algorithms/quantum_primitives/gqsp/gqsp.mdx` |
| Boolean Oracle Sketching | Randomized sketching of boolean oracle evaluations | `@qperm`, random circuits | `explore/algorithms/quantum_primitives/quantum_oracle_sketching_boolean/quantum_oracle_sketching_boolean.mdx` |

---

## Quantum Phase Estimation

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| QPE (flexible, high-level) | Configurable QPE with synthesis constraints | `qpe`, `power`, `QNum` | `explore/tutorials/advanced_tutorials/high_level_modeling_flexible_qpe/high_level_modeling_flexible_qpe.mdx` |
| QPE for a matrix | Phase estimation where U = e^{2πiA} for a dense matrix A | `qpe`, `unitary`, `matrix_to_hamiltonian` | `explore/algorithms/quantum_phase_estimation/qpe_for_matrix/qpe_for_matrix.mdx` |
| QPE with qubitization | Phase estimation via qubitization block encoding (molecular energies) | `qpe`, qubitization open library | `explore/algorithms/quantum_phase_estimation/qpe_with_qubitization/qpe_for_molecule_with_qubitization.mdx` |

---

## Amplitude Amplification & Estimation

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| Quantum Monte Carlo / QAE | Estimate expectation values with quadratic quantum speedup | `qpe`, amplitude oracle | `explore/algorithms/amplitude_amplification_and_estimation/qmc_user_defined/qmc_user_defined.mdx` |
| Quantum Counting | Count solutions in a search space via QAE | `qpe`, `grover_operator` | `explore/algorithms/amplitude_amplification_and_estimation/quantum_counting/quantum_counting.mdx` |
| QSVT fixed-point amplitude amplification | Amplitude amplification as a polynomial transformation via QSVT | QSVT open library | `explore/algorithms/amplitude_amplification_and_estimation/qsvt_fixed_point_amplitude_amplification/qsvt_fixed_point_amplitude_amplification.mdx` |
| Oblivious Amplitude Amplification | OAA for block-encoded / LCU state preparation | `grover_operator`, LCU pattern | `explore/algorithms/amplitude_amplification_and_estimation/oblivious_amplitude_amplification/oblivious_amplitude_amplification.mdx` |

---

## Hamiltonian Simulation

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| Suzuki-Trotter (guide) | Product formula simulation — how to choose order and repetitions | `suzuki_trotter` | `explore/algorithms/hamiltonian_simulation/hamiltonian_simulation_guide/hamiltonian_simulation_guide.mdx` |
| Block encoding via QSVT | QSVT-based Hamiltonian simulation | QSVT open library | `explore/algorithms/hamiltonian_simulation/hamiltonian_simulation_with_block_encoding/hamiltonian_simulation_qsvt.mdx` |
| Block encoding via qubitization | Qubitization walk operator for Hamiltonian simulation | qubitization open library | `explore/algorithms/hamiltonian_simulation/hamiltonian_simulation_with_block_encoding/hamiltonian_simulation_qubitization.mdx` |
| Block encoding via GQSP | GQSP polynomial for Hamiltonian simulation | `gqsp` open library | `explore/algorithms/hamiltonian_simulation/hamiltonian_simulation_with_block_encoding/hamiltonian_simulation_gqsp.mdx` |
| Jacobi-Anger expansion | Hamiltonian simulation via Jacobi-Anger series | advanced | `explore/algorithms/hamiltonian_simulation/hamiltonian_simulation_with_block_encoding/jacobi_anger_expansion.mdx` |

---

## Quantum Linear Solvers

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| HHL | Solve Ax=b via QPE + controlled eigenvalue inversion + uncomputation | `qpe`, `suzuki_trotter`, `control`, `within_apply` | `explore/algorithms/quantum_linear_solvers/hhl/hhl.mdx` |
| VQLS with LCU | Variational quantum linear solver using LCU block encoding | `prepare_amplitudes`, `control`, variational loop | `explore/algorithms/quantum_linear_solvers/vqls/vqls_with_lcu.mdx` |
| QSVT matrix inversion | Matrix inversion via quantum signal processing polynomial | QSVT open library | `explore/algorithms/quantum_linear_solvers/qsvt_matrix_inversion/qsvt_matrix_inversion.mdx` |
| Adiabatic linear solver | Solve QLSP via adiabatic quantum computing | `suzuki_trotter`, variational | `explore/algorithms/quantum_linear_solvers/adiabatic_linear_solvers/solving_qlsp_with_aqc.mdx` |

---

## Differential Equation Solvers

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| Discrete Poisson solver | Solve the Poisson equation via HHL | `qpe`, `suzuki_trotter`, HHL pattern | `explore/algorithms/quantum_differential_equations_solvers/discrete_poisson_solver/discrete_poisson_solver.mdx` |
| LCHS | Linear Combination of Hamiltonian Simulations for ODEs | `suzuki_trotter`, LCU pattern | `explore/algorithms/quantum_differential_equations_solvers/lchs/lchs.mdx` |
| Time marching | Iterative time-stepping for PDEs using a quantum linear solver | HHL, iterative hybrid | `explore/algorithms/quantum_differential_equations_solvers/time_marching/time_marching.mdx` |

---

## Quantum State Preparation

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| ADAPT-VQE | Adaptive ansatz construction for ground state preparation | variational, `CArray[CReal]` | `explore/algorithms/quantum_state_preparation/adapt_vqe/adapt_vqe.mdx` |
| Fermionic Gaussian state | Prepare fermionic Gaussian states efficiently | open library | `explore/algorithms/quantum_state_preparation/fermionic_gaussian/fermionic_gaussian.mdx` |
| Gibbs / thermal state | Prepare thermal quantum states at temperature T | open library | `explore/algorithms/quantum_state_preparation/gibbs/quantum_thermal_state_preparation.mdx` |

---

## Quantum Machine Learning

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| Hybrid QNN | Quantum neural network for classification tasks | `variational_data_encoding`, `CArray[CReal]`, `observe` | `explore/algorithms/QML/hybrid_qnn/hybrid_qnn_for_subset_majority.mdx` |
| QSVM | Quantum support vector machine via quantum kernel | feature maps, `observe` | `explore/algorithms/QML/qsvm/qsvm.mdx` |
| QGAN | Quantum generative adversarial network | variational, `sample` | `explore/algorithms/QML/qgan/qgan_bars_and_strips.mdx` |
| Quantum autoencoder | Compress and reconstruct quantum states | variational, `observe` | `explore/algorithms/QML/quantum_autoencoder/quantum_autoencoder.mdx` |
| QML guide | End-to-end QML workflow with Classiq | `variational_data_encoding`, `ExecutionSession` | `explore/tutorials/basic_tutorials/qml_with_classiq_guide/qml_with_classiq_guide.mdx` |

---

## Quantum Walks

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| Discrete quantum walk (1D) | Walk on a line graph | walk operator, `control` | `explore/tutorials/advanced_tutorials/discrete_quantum_walk/discrete_quantum_walk.mdx` |
| Discrete quantum walk (2D) | Walk on a 2D grid | walk operator, `QStruct` | `explore/tutorials/advanced_tutorials/discrete_quantum_walk_2d/discrete_time_quantum_walk.mdx` |
| Glued trees walk | Quantum walk on glued binary trees (exponential speedup demo) | walk operator | `explore/algorithms/quantum_walks/glued_trees/glued_trees.mdx` |
| Complex network walk | Quantum walk on complex graphs | walk operator | `explore/tutorials/basic_tutorials/quantumwalk_complex_network/quantumwalk_complex_network.mdx` |

---

## Number Theory & Cryptography

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| Shor's Algorithm | Factor integers via quantum period finding | `qpe`, `qft`, modular arithmetic, `QNum` | `explore/algorithms/number_theory_and_cryptography/shor/shor.mdx` |
| Discrete logarithm | Quantum discrete log via period finding | `qpe`, modular arithmetic | `explore/algorithms/number_theory_and_cryptography/discrete_log/discrete_log.mdx` |
| Elliptic curve discrete log | Quantum attack on elliptic curve cryptography | `qpe`, modular arithmetic | `explore/algorithms/number_theory_and_cryptography/elliptic_curves/elliptic_curve_discrete_log.mdx` |
| Hidden shift | Find hidden shift in Boolean functions | `hadamard_transform`, `@qperm` | `explore/algorithms/number_theory_and_cryptography/hidden_shift/hidden_shift.mdx` |

---

## Metrology

| Algorithm | Description | Key constructs | Path |
|-----------|-------------|----------------|------|
| Classical shadow tomography | Efficient quantum state characterization via random measurements | `sample`, random unitaries | `explore/algorithms/metrology/classical_shadow_tomography.mdx` |

---

## Applications

Domain-specific implementations are in `explore/applications/`. Browse with:

```
query_docs_filesystem_classiq_docs → tree /explore/applications -L 2
```

| Domain | What's available |
|--------|-----------------|
| Chemistry | VQE, molecular energy curves, QPE for molecules, second quantization, Fermi-Hubbard |
| Finance | Option pricing (QAE), portfolio optimization (HHL / QAOA), value at risk, autocallable options |
| CFD | Heat equation (QSVT), quantum lattice-Boltzmann, hybrid HHL solvers, Vlasov-Ampere |
| Optimization | QAOA variants, TSP, VRP, graph problems (max-cut, coloring, clique, independent set) |
| Physical systems | Ising model, Maxwell equations, HHL for Lanchester equations |
| Benchmarking | Quantum volume, randomized benchmarking |
