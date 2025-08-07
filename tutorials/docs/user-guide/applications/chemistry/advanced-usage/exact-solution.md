# Exact Solution

Currently, quantum algorithms for chemistry investigate relatively small molecules.
For many of these molecules, the exact ground state can be calculated using full Hamiltonian diagonalization.
This can serve as the ground truth for evaluating the results obtained by quantum methods.

The following example shows how to get the exact ground state of a hydrogen molecule.

```python
from classiq.applications.chemistry import Molecule, MoleculeProblem
import numpy as np

molecule = Molecule(
    atoms=[
        ("H", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 0.735)),
    ],
)
gs_problem = MoleculeProblem(
    molecule=molecule,
    mapping="jordan_wigner",
)

operator = gs_problem.generate_hamiltonian()
mat = operator.to_matrix()
w, v = np.linalg.eig(mat)
result_exact = np.real(min(w))
```

This calculation does not consider the nuclear repulsion energy.
