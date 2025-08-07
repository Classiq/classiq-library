# Unitary Coupled Cluster (UCC) Ansatz

The Unitary Coupled Cluster (UCC) is a commonly used chemistry-inspired
ansatz, which is a unitary version of the classical coupled cluster (CC) method [ [1] ](#UCC).

## Syntax

`UCCParameters`:

-   `excitations: List[int]` – List of the desired excitations.

Allowed excitations:

-   1 for singles

-   2 for doubles

-   3 for triples

-   4 for quadruples

## Example

<!-- cspell:ignore UCCSD -->

First the quantum program is initialized to the Hartree-Fock state, then the UCC function is
applied to generate the desired excitations. Here they are single and double, making it a UCCSD ansatz.

<!-- prettier-ignore -->
=== "SDK"

    ```python
    from classiq import construct_chemistry_model, synthesize, OptimizerType
    from classiq.applications.chemistry import Molecule, MoleculeProblem
    from classiq.applications.chemistry import UCCParameters, ChemistryExecutionParameters

    from classiq import execute

    molecule = Molecule(
        atoms=[("H", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 0.735))],
    )
    gs_problem = MoleculeProblem(
        molecule=molecule,
        mapping="jordan_wigner",
    )

    ansatz_parameters = UCCParameters(
        excitations=[1, 2],
    )
    execution_params = ChemistryExecutionParameters(
        optimizer=OptimizerType.COBYLA,
        max_iteration=30,
    )

    model = construct_chemistry_model(
        chemistry_problem=gs_problem,
        use_hartree_fock=True,
        ansatz_parameters=ansatz_parameters,
        execution_parameters=execution_params,
    )
    qprog = synthesize(model)

    result = execute(qprog).result()
    ```

The output quantum program:

![alt text](../../resources/chemistry/ucc_circuit.png)

<a name="UCC">[1]</a>
Panagiotis Kl. Barkoutsos, Jerome F. Gonthier, Igor Sokolov, Nikolaj Moll, Gian Salis, Andreas Fuhrer, Marc Ganzhorn, Daniel J. Egger, Matthias Troyer, Antonio Mezzacapo, Stefan Filipp, and Ivano Tavernelli
[Quantum algorithms for electronic structure calculations: Particle-hole Hamiltonian and optimized wave-function expansions](https://arxiv.org/abs/1805.04340)
Phys. Rev. A 98, 022322 (2018).
