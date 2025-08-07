# Second Quantized Hamiltonian

You can define a chemical problem using the second quantized (fermionic) Hamiltonian
instead of defining the geometry of the molecule.
This approach utilizes the power of quantum chemistry software packages such
as [PYSCF](http://pyscf.org/) and [PSI4](http://psicode.org/) to derive the
most suitable Hamiltonian for the model.

Here is a short example of this method using PYSCF, which converts a molecule to a fermionic operator.

```python
from classiq import construct_chemistry_model, execute, synthesize, OptimizerType
from classiq.applications.chemistry import (
    ChemistryExecutionParameters,
    FermionicOperator,
    HamiltonianProblem,
    HEAParameters,
    SummedFermionicOperator,
)

hamiltonian = SummedFermionicOperator(
    op_list=[
        (FermionicOperator(op_list=[("+", 0), ("-", 0)]), 0.2),
        (FermionicOperator(op_list=[("-", 1), ("-", 1)]), 0.3),
        (FermionicOperator(op_list=[("-", 2), ("-", 2)]), 0.4),
        (FermionicOperator(op_list=[("-", 3), ("-", 3)]), 0.5),
        (FermionicOperator(op_list=[("+", 0), ("+", 1), ("-", 1), ("-", 0)]), -0.1),
        (FermionicOperator(op_list=[("+", 2), ("+", 3), ("-", 2), ("-", 3)]), -0.3),
    ]
)
ham_problem = HamiltonianProblem(hamiltonian=hamiltonian, num_particles=[1, 1])

print(ham_problem.hamiltonian)

hwea_params = HEAParameters(
    num_qubits=4,
    connectivity_map=[(0, 1), (1, 2), (2, 3)],
    reps=3,
    one_qubit_gates=["x", "ry"],
    two_qubit_gates=["cx"],
)

serialized_chemistry_model = construct_chemistry_model(
    chemistry_problem=ham_problem,
    use_hartree_fock=False,
    ansatz_parameters=hwea_params,
    execution_parameters=ChemistryExecutionParameters(
        optimizer=OptimizerType.COBYLA,
        max_iteration=100,
        initial_point=None,
    ),
)

qprog = synthesize(serialized_chemistry_model)

results = execute(qprog).result()
chemistry_result = results[0].value
chemistry_result.energy
```

A basic script to convert `MoleculeProblem` to `HamiltonianProblem` using PYSCF is
given in `classiq.applications.chemistry.pyscf_hamiltonian`.
You can extend it to use more features from PYSCF.

The rest of the solving process is regular.
