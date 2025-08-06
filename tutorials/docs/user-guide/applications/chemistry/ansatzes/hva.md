# Hamiltonian Variational Ansatz (HVA)

The Hamiltonian Variational Ansatz (HVA) is inspired by the quantum approximate optimization algorithm [ [1] ](#HVA1), [ [2] ](#HVA2).

## Syntax

`HVAParameters`:

-   `reps: int` – Number of layers in the ansatz.

## Example

Initialize the quantum program to the Hartree-Fock state and then apply the HVA function.

<!-- prettier-ignore -->
=== "SDK"

    ```python
    from classiq import construct_chemistry_model, synthesize, OptimizerType
    from classiq.applications.chemistry import Molecule, MoleculeProblem
    from classiq.applications.chemistry import HVAParameters, ChemistryExecutionParameters

    from classiq import execute

    molecule = Molecule(
        atoms=[("H", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 0.735))],
    )
    gs_problem = MoleculeProblem(
        molecule=molecule,
        mapping="jordan_wigner",
    )

    ansatz_parameters = HVAParameters(
        reps=3,
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

![alt text](../../resources/chemistry/hva_circuit.png)

<a name="HVA1">[1]</a> Dave Wecker, Matthew B. Hastings, and Matthias Troye [Towards Practical Quantum Variational Algorithms](https://arxiv.org/abs/1507.08969). Phys. Rev. A 92, 042303 (2015).

<a name="HVA2">[2]</a> Roeland Wiersema, Cunlu Zhou, Yvette de Sereville, Juan Felipe Carrasquilla, Yong Baek Kim, Henry Yuen
[Exploring entanglement and optimization within the Hamiltonian Variational Ansatz
](https://arxiv.org/abs/2008.02941). PRX Quantum 1, 020319 (2020).
