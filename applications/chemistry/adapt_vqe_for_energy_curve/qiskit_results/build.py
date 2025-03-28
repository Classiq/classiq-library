from qiskit import QuantumCircuit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper, BravyiKitaevMapper,TaperedQubitMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit.quantum_info import SparsePauliOp
import numpy as np
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP, COBYLA, CG, NFT
from qiskit.primitives import Estimator
from qiskit_algorithms import AdaptVQE
from qiskit_nature.second_q.algorithms import GroundStateEigensolver
from qiskit.qasm2 import dump
el1, el2 = "H","H"
dist= np.arange(0.5, 2.1, 0.2)
qc = QuantumCircuit(4)
#finalarr=[]
for arr in (dist):
    dir=str(arr)
    driver = PySCFDriver(atom=el1+" 0 0 0; "+el2+" 0 0 "+dir, basis="sto-3g")
    problem = driver.run()
    mapper = BravyiKitaevMapper()
    ansatz = UCCSD(problem.num_spatial_orbitals,problem.num_particles,mapper,
        initial_state=HartreeFock(problem.num_spatial_orbitals,problem.num_particles,mapper))
    vqe = VQE(Estimator(), ansatz, SLSQP())
    vqe.initial_point = np.zeros(ansatz.num_parameters)
    adapt_vqe = AdaptVQE(vqe)
    adapt_vqe.supports_aux_operators = lambda: True  
    solver = GroundStateEigensolver(mapper, adapt_vqe)
    #result = solver.solve(problem)
    #finalarr.append(result.total_energies[0])
    #ham = SparsePauliOp.from_sparse_list(solver.get_qubit_operators(problem)[0], num_qubits=4)
    qops = solver.get_qubit_operators(problem)[0]
    #qc.append(qops,[0,1,2,3])
    #print(ham)  
    print(qops)
    #print(solver.get_qubit_operators(problem)[0])    
    print("---")
#print(finalarr)
