# Hardware Efficient Ansatz

In NISQ-era devices, to reduce noise, use short and hardware-fitting quantum programs.

Hardware-efficient ansatz is generated to fit a specific hardware with given connectivity map and basis gates [ [1] ](#HWEA).
The hardware-efficient ansatz is built from a layer of single qubit gates followed by a layer of entangling two qubit gates.
Repeating this structure allows a more expressive ansatz at the cost of increased depth.

## Syntax

`HEAParameters`:

-   `num_qubits: int` – Number of qubits in the ansatz.
-   `connectivity_map: List[Tuple[int]]` – Hardware connectivity map, in the form [ [x0, x1], [x1, x2],...].
-   `reps: int` – Number of layers in the ansatz.
-   `one_qubit_gates: List[str]` – List of gates for the one qubit gates layer, e.g., ["x", "ry"].
-   `two_qubit_gates: List[str]` – List of gates for the two qubit gates entangling layer, e.g., ["cx", "cry"].

If the number of qubits is not specified, the number of the qubits from the connectivity map is used.
If the connectivity map is not specified, the connectivity map from the model hardware settings is used. If that is also not specified, all qubit pairs are connected.

<!-- cspell:ignore iswap -->

The allowed one_qubit_gates: '["x", "y", "z", "h", "p", "i", "rx", "ry", "rz", "s", "sdg", "t", "tdg"]'.

The allowed two_qubit_gates: '["cx", "cy", "cz", "ch", "cp", "crx", "cry", "crz", "rxx", "ryy", "rzz", "swap"]'.

## Example

This example demonstrates how to generate a hardware-efficient ansatz.
It uses a four qubit hardware with full connectivity.

<!-- prettier-ignore -->
=== "SDK"

    ```python
    from classiq import construct_chemistry_model, synthesize, OptimizerType
    from classiq.applications.chemistry import Molecule, MoleculeProblem
    from classiq.applications.chemistry import HEAParameters, ChemistryExecutionParameters

    from classiq import execute

    molecule = Molecule(
        atoms=[("H", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 0.735))],
    )
    gs_problem = MoleculeProblem(
        molecule=molecule,
        mapping="jordan_wigner",
    )

    ansatz_parameters = HEAParameters(
        reps=3,
        num_qubits=4,
        connectivity_map=[(0, 1), (1, 2), (2, 3)],
        one_qubit_gates=["x", "ry"],
        two_qubit_gates=["cx"],
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

![alt text](../../resources/chemistry/hwe_ansatz_circuit.png)

<a name="HWEA">[1]</a> Abhinav Kandala, Antonio Mezzacapo, Kristan Temme, Maika Takita, Markus Brink, Jerry M. Chow, Jay M. Gambetta [Hardware-efficient variational quantum eigensolver for small molecules and quantum magnets](https://arxiv.org/abs/1704.05018). Nature 549, 242 (2017).
