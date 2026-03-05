#!/usr/bin/env python3
"""
Build a categorized mapping of all notebooks in algorithms/, applications/, and tutorials/
from their *.metadata.json (description, path, file name). Only includes entries that have
a corresponding .ipynb file. Output: JSON with category name -> list of paths to .ipynb.
"""

import json
from enum import Enum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class Category(str, Enum):
    """Available notebook categories. Value is the display name used in JSON output."""

    CHEMISTRY = "Chemistry"
    QML = "QML"
    FINANCE = "Finance"
    SEARCH_AMPLITUDE = "Search & Amplitude Amplification"
    LINEAR_ALGEBRA = "Linear Algebra & Solvers"
    FOUNDATIONAL = "Foundational & Primitives"
    COMBINATORIAL_OPTIMIZATION = "Combinatorial Optimization"
    PHYSICS_SIMULATION = "Physics & Simulation"
    QUANTUM_WALKS = "Quantum Walks & Advanced"
    TUTORIALS = "Tutorials & Getting Started"
    OTHER = "Other"


METADATA_LISTS = [
    REPO_ROOT / "algorithms_metadata_list.txt",
    REPO_ROOT / "applications_metadata_list.txt",
    REPO_ROOT / "tutorials_metadata_list.txt",
]


def load_metadata_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def get_metadata(rel_path: str) -> dict | None:
    full = REPO_ROOT / rel_path
    if not full.exists():
        return None
    try:
        return json.loads(full.read_text())
    except Exception:
        return None


def ipynb_path(metadata_path: str) -> str:
    return metadata_path.replace(".metadata.json", ".ipynb")


def categorize(rel_metadata_path: str, meta: dict | None) -> Category:
    """Assign one category based on path and description. Returns Category enum member."""
    path_lower = rel_metadata_path.lower()
    desc = (meta.get("description") or "").lower() if meta else ""
    tags = [t.lower() for t in meta.get("problem_domain_tags") or []] if meta else []
    # Path segments
    parts = path_lower.replace(".metadata.json", "").split("/")

    # 1. Chemistry
    if "chemistry" in parts or "molecule" in path_lower or "molecular" in path_lower:
        return Category.CHEMISTRY
    if any(
        k in desc
        for k in (
            "molecule",
            "molecular",
            "vqe",
            "ucc",
            "protein folding",
            "second quantized",
            "tensor hypercontraction",
            "qpe for molecule",
        )
    ) and (
        "chemistry" in path_lower
        or "molecule" in path_lower
        or "quantum_state_preparation" in path_lower
        or "quantum_phase_estimation" in path_lower
        or "protein_folding" in path_lower
    ):
        return Category.CHEMISTRY
    if "chemistry" in tags:
        return Category.CHEMISTRY

    # 2. QML (send algorithm HHL to Linear Algebra, not QML via tags)
    if "quantum_linear_solvers" in path_lower and "/hhl" in path_lower:
        return Category.LINEAR_ALGEBRA
    if (
        "qml" in parts
        or "qsvm" in path_lower
        or "qgan" in path_lower
        or "autoencoder" in path_lower
        or "hybrid_qnn" in path_lower
    ):
        return Category.QML
    if any(
        k in desc
        for k in (
            "quantum support vector",
            "qsvm",
            "qgan",
            "quantum generative",
            "autoencoder",
            "quantum machine learning",
            "qml",
            "hybrid qnn",
        )
    ):
        return Category.QML
    if "credit_card_fraud" in path_lower or "credit card fraud" in desc:
        return Category.QML
    if "machine learning" in tags and "chemistry" not in path_lower:
        return Category.QML

    # 3. Finance
    if "finance" in parts:
        return Category.FINANCE
    if any(
        k in desc
        for k in (
            "option pricing",
            "portfolio optimization",
            "value at risk",
            "autocallable",
            "rainbow option",
            "brownian",
            "monte carlo",
        )
    ):
        return Category.FINANCE

    # 4. Search & Amplitude Amplification
    if (
        "grover" in path_lower
        or "amplitude_amplification" in parts
        or "quantum_counting" in path_lower
        or "dqi" in path_lower
    ):
        return Category.SEARCH_AMPLITUDE
    if "oracle" in path_lower and (
        "workshop" in path_lower or "3sat" in path_lower or "oracles" in path_lower
    ):
        return Category.SEARCH_AMPLITUDE
    if any(
        k in desc
        for k in (
            "grover",
            "amplitude amplification",
            "quantum counting",
            "amplitude estimation",
            "phase oracle",
            "3-sat",
        )
    ):
        return Category.SEARCH_AMPLITUDE

    # 5. Linear Algebra & Solvers (after Physics so Hamiltonian simulation stays in Physics)
    if (
        "hhl" in path_lower
        or "quantum_linear_solvers" in parts
        or "qpe_for_matrix" in path_lower
        or "qsvt_matrix_inversion" in path_lower
    ):
        return Category.LINEAR_ALGEBRA
    if "qpe" in path_lower and ("qpe_for" in path_lower or "phase estimation" in desc):
        if "molecule" in path_lower or "molecular" in desc:
            return Category.CHEMISTRY
        return Category.LINEAR_ALGEBRA
    if (
        "linear_solvers" in path_lower
        or "qls_" in path_lower
        or "verify_block_encoding" in path_lower
        or "chebyshev_approximation" in path_lower
    ):
        return Category.LINEAR_ALGEBRA
    if (
        any(
            k in desc
            for k in (
                "hhl",
                "linear system",
                "matrix inversion",
                "qsvt",
                "block-encoding",
                "phase estimation",
                "qlsp",
            )
        )
        and "hamiltonian_simulation" not in path_lower
    ):
        return Category.LINEAR_ALGEBRA
    if (
        "poisson" in path_lower
        or "time_marching" in path_lower
        or "differential equation" in desc
        or "discrete poisson" in desc
    ):
        return Category.LINEAR_ALGEBRA
    if "vlasov" in path_lower or "vlasov-ampere" in desc:
        return Category.LINEAR_ALGEBRA
    if "lanchester" in path_lower or "lanchester" in desc:
        return Category.LINEAR_ALGEBRA
    if "adiabatic_linear_solvers" in path_lower or "vqls" in path_lower:
        return Category.LINEAR_ALGEBRA

    # 6. Foundational & Primitives
    if (
        "foundational" in parts
        or "deutsch" in path_lower
        or "simon" in path_lower
        or "bernstein" in path_lower
        or "teleportation" in path_lower
    ):
        return Category.FOUNDATIONAL
    if (
        "quantum_primitives" in parts
        or "swap_test" in path_lower
        or "gqsp" in path_lower
    ):
        return Category.FOUNDATIONAL
    if "hadamard_test" in path_lower or "linear_combination_of_unitaries" in path_lower:
        return Category.FOUNDATIONAL
    if any(
        k in desc
        for k in (
            "deutsch–jozsa",
            "deutsch-jozsa",
            "simon's",
            "bernstein-vazirani",
            "quantum teleportation",
            "swap test",
            "hadamard test",
            "lcu",
        )
    ):
        return Category.FOUNDATIONAL

    # 7. Combinatorial Optimization
    if "optimization" in parts and "applications" in parts:
        return Category.COMBINATORIAL_OPTIMIZATION
    if "logistics" in parts or "telecom" in parts or "cybersecurity" in parts:
        return Category.COMBINATORIAL_OPTIMIZATION
    if "automotive" in parts or "cooling_systems" in path_lower:
        return Category.COMBINATORIAL_OPTIMIZATION
    if any(
        k in path_lower
        for k in (
            "max_cut",
            "max_clique",
            "max_independent",
            "min_graph_coloring",
            "set_cover",
            "set_partition",
            "kidney_exchange",
            "qaoa",
            "adapt_qaoa",
            "rectangles_packing",
            "integer_linear",
            "electric_grid",
            "robust_posture",
            "minimum_dominating",
            "max_k_vertex",
            "max_induced_k_color",
            "evidence_scaling",
            "variational_quantum_imaginary",
        )
    ):
        return Category.COMBINATORIAL_OPTIMIZATION
    if any(
        k in desc
        for k in (
            "qaoa",
            "max-cut",
            "max cut",
            "graph coloring",
            "set cover",
            "clique",
            "independent set",
            "traveling salesman",
            "vehicle routing",
            "facility location",
            "task scheduling",
            "resiliency planning",
            "network traffic",
            "antenna",
            "vertex cover",
            "patching",
            "link monitoring",
            "whitebox fuzzing",
            "kidney exchange",
            "number partitioning",
            "dominating set",
            "inverse kinematics",
            "combinatorial optimization",
            "knapsack",
        )
    ):
        return Category.COMBINATORIAL_OPTIMIZATION
    if "gm_qaoa" in path_lower or "grover_mixer" in path_lower:
        return Category.COMBINATORIAL_OPTIMIZATION

    # 8. Physics & Simulation (check before Linear Algebra so Hamiltonian simulation is here)
    if (
        "hamiltonian_simulation" in path_lower
        or "ising_model" in path_lower
        or "quantum_chaos" in path_lower
    ):
        return Category.PHYSICS_SIMULATION
    if (
        "cfd" in parts
        or "heat_eq" in path_lower
        or "qlbm" in path_lower
        or "double_slit" in path_lower
    ):
        return Category.PHYSICS_SIMULATION
    if "plasma" in parts:
        return Category.PHYSICS_SIMULATION
    if any(
        k in desc
        for k in (
            "hamiltonian simulation",
            "ising model",
            "quantum chaos",
            "sawtooth",
            "heat equation",
            "lattice boltzmann",
            "double slit",
            "cfd",
        )
    ):
        return Category.PHYSICS_SIMULATION
    if "quantum_differential_equations" in path_lower and "poisson" not in path_lower:
        return Category.PHYSICS_SIMULATION
    if "quantum_state_preparation" in parts and "gibbs" in path_lower:
        return Category.PHYSICS_SIMULATION
    if "adapt_vqe" in path_lower:
        return Category.CHEMISTRY  # ADAPT-VQE is chemistry
    if "quantum_thermal_state" in path_lower:
        return Category.PHYSICS_SIMULATION

    # 9. Quantum Walks & Advanced
    if (
        "quantum_walk" in path_lower
        or "glued_trees" in path_lower
        or "quantumwalk" in path_lower
    ):
        return Category.QUANTUM_WALKS
    if "discrete_quantum_walk" in path_lower or "quantum walk" in desc:
        return Category.QUANTUM_WALKS

    # 10. Tutorials & Getting Started
    if "the_classiq_tutorial" in path_lower or "classiq_overview" in path_lower:
        return Category.TUTORIALS
    if "basic_tutorials" in parts and path_lower not in [
        p.lower() for p in ["grover", "qml"]
    ]:
        if "qml_with_classiq" in path_lower:
            return Category.QML
        if "grover_graph" in path_lower:
            return Category.COMBINATORIAL_OPTIMIZATION
        if "learning_optimization" in path_lower:
            return Category.COMBINATORIAL_OPTIMIZATION
        if "quantumwalk" in path_lower:
            return Category.QUANTUM_WALKS
        return Category.TUTORIALS
    if (
        "add_bell_states" in path_lower
        or "entanglement" in path_lower
        or "prepare_state" in path_lower
        or "exponentiation" in path_lower
        or "mcx" in path_lower
    ):
        if "basic_tutorials" in parts:
            return Category.TUTORIALS
    if "workshops" in parts:
        if "algo_design" in path_lower:
            return Category.TUTORIALS
        if "grover_workshop" in path_lower:
            return Category.SEARCH_AMPLITUDE
        if "hhl_workshop" in path_lower:
            return Category.LINEAR_ALGEBRA
        if "combinatorial" in path_lower or "maxcut" in path_lower:
            return Category.COMBINATORIAL_OPTIMIZATION
        if "oracle" in path_lower:
            return Category.SEARCH_AMPLITUDE
        if (
            "finance" in path_lower
            or "option_pricing" in path_lower
            or "portfolio" in path_lower
        ):
            return Category.FINANCE
    if "technology_demonstrations" in parts:
        if (
            "classiq_qsvt" in path_lower
            or "qpe_for" in path_lower
            or "hhl" in path_lower
            or "hamiltonian_evolution" in path_lower
        ):
            if "qpe" in path_lower:
                return Category.LINEAR_ALGEBRA
            if "hhl" in path_lower:
                return Category.LINEAR_ALGEBRA
            if "hamiltonian" in path_lower:
                return Category.PHYSICS_SIMULATION
            return Category.LINEAR_ALGEBRA
        if "qaoa_demonstration" in path_lower or "3sat_oracles" in path_lower:
            return (
                Category.COMBINATORIAL_OPTIMIZATION
                if "qaoa" in path_lower
                else Category.SEARCH_AMPLITUDE
            )
        if (
            "approximated_state" in path_lower
            or "auxiliary_management" in path_lower
            or "arithmetic_expressions" in path_lower
            or "hardware_aware" in path_lower
            or "discrete_quantum_walk_circle" in path_lower
        ):
            return Category.TUTORIALS
    if "advanced_tutorials" in parts:
        if (
            "discrete_quantum_walk" in path_lower
            or "high_level_modeling_flexible_qpe" in path_lower
            or "linear_approximation" in path_lower
        ):
            if "qpe" in path_lower:
                return Category.LINEAR_ALGEBRA
            return (
                Category.QUANTUM_WALKS
                if "quantum_walk" in path_lower
                else Category.TUTORIALS
            )

    # 11. Benchmarking & Other (grouped with Tutorials for ~10 categories)
    if (
        "benchmarking" in parts
        or "quantum_volume" in path_lower
        or "randomized_benchmarking" in path_lower
    ):
        return Category.TUTORIALS
    if "image_processing" in path_lower or "edge_detection" in path_lower:
        return Category.TUTORIALS

    # Number theory / cryptography (grouped with Foundational)
    if (
        "number_theory_and_cryptography" in path_lower
        or "number_theory" in parts
        or "shor" in path_lower
        or "discrete_log" in path_lower
        or "elliptic_curve" in path_lower
        or "hidden_shift" in path_lower
    ):
        return Category.FOUNDATIONAL

    # Phase estimation (generic)
    if "quantum_phase_estimation" in parts:
        return Category.LINEAR_ALGEBRA

    # Default for remaining tutorials
    if "tutorials" in parts:
        return Category.TUTORIALS

    return Category.OTHER


def main():
    all_metadata_paths = []
    for list_path in METADATA_LISTS:
        all_metadata_paths.extend(load_metadata_list(list_path))

    categories: dict[str, list[str]] = {}
    for rel in all_metadata_paths:
        ipynb = ipynb_path(rel)
        if not (REPO_ROOT / ipynb).exists():
            continue
        meta = get_metadata(rel)
        cat = categorize(rel, meta)
        key = cat.value  # use display name as JSON key
        categories.setdefault(key, []).append(ipynb)

    # Sort lists for readability
    for k in categories:
        categories[k] = sorted(categories[k])

    out_path = REPO_ROOT / "notebook_categories.json"
    with open(out_path, "w") as f:
        json.dump(categories, f, indent=2)

    print("Categories and counts:")
    for cat in sorted(categories.keys()):
        print(f"  {cat}: {len(categories[cat])}")
    print(f"\nTotal notebooks: {sum(len(v) for v in categories.values())}")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
