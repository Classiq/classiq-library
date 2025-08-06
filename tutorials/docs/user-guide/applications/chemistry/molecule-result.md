# Molecule Problem Result

Executing a ground state molecule problem returns a list of tuples, with the second element providing the following (as a dictionary):

`energy: float` – The energy reached by VQE, i.e., the electronic part of energy in the Born-Oppenheimer approximation.

`nuclear_repulsion_energy: float` – The energy of the nucleus in the Born-Oppenheimer approximation.

`total_energy: [float]` – The total energy of the molecule, i.e., the sum over nuclear_repulsion_energy and energy.

`hartree_fock_energy: float` – The energy in the Hartree-Fock approximation.

`vqe_result: Dict[str, Any]` – The fields for the `VQESolverResult` object, received from the VQE execution.
