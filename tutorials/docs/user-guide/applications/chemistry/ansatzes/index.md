# Ansatzes

See these smart ansatz examples for chemistry:

-   [Hardware efficient ansatz](hardware-efficient-ansatz.md)
-   [Unitary coupled cluster (UCC) ansatz](ucc.md)
-   [Hamiltonian variational ansatz (HVA)](hva.md)

A vqe with a user-defined ansatz can be constructed through the SDK by defining
a user-defined variational quantum part `model=Model()`, and a user-defined
classical body with the method `model.vqe()`.
