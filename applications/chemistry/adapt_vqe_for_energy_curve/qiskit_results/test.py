from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper, BravyiKitaevMapper,TaperedQubitMapper
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
import numpy as np
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP, COBYLA, CG, NFT
#from qiskit_aer.primitives import Estimator
from qiskit.primitives import Estimator
from qiskit_algorithms import AdaptVQE
from qiskit_nature.second_q.algorithms import GroundStateEigensolver
import matplotlib.pyplot as plt

def run_avqe(el1, el2, dist):
    finalarr=[]
    for arr in (dist):
        dir=str(arr)
        driver = PySCFDriver(atom=el1+" 0 0 0; "+el2+" 0 0 "+dir, basis="sto-3g")
        problem = driver.run()
        mapper = BravyiKitaevMapper()
        ansatz = UCCSD(problem.num_spatial_orbitals,problem.num_particles,mapper,
            initial_state=HartreeFock(problem.num_spatial_orbitals,problem.num_particles,mapper))
        #vqe = VQE(Estimator(backend_options={"method": "statevector", 'shots': None},run_options={"seed": 5678, 'approximation':True},), ansatz, COBYLA())
        vqe = VQE(Estimator(), ansatz, SLSQP())
        vqe.initial_point = np.zeros(ansatz.num_parameters)
        adapt_vqe = AdaptVQE(vqe)
        adapt_vqe.supports_aux_operators = lambda: True  # temporary fix
        solver = GroundStateEigensolver(mapper, adapt_vqe)
        result = solver.solve(problem)
        finalarr.append(result.total_energies[0])
    return finalarr
    
#X= np.arange(0.35, 4, 0.2);Y=run_avqe("H","H",X)
#X= np.arange(0.4, 4, 0.2);Y=run_avqe("H","Li",X)
X= np.arange(0.5, 2.1, 0.2);Y=run_avqe("H","F",X)

fig, ax = plt.subplots(constrained_layout=True, figsize=(16,12))
plt.plot(X,Y, '-o', color='blue', label='qiskit')
ax.legend(fontsize=24, loc="lower right")
ax.tick_params(axis='both', labelsize=24)
ax.set_ylabel(r'$E_h(Ha)$', fontsize=30)
ax.set_xlabel(r'$r(A)$', fontsize=30)
plt.grid()
plt.show()
print((min(Y)))


#X0=np.array([0.3]);Y0=run_avqe("H","Li",X0);print(Y0)

#def run_avqe3(dist):
#    finalarr=[]
#    for arr in (dist):
#        dir=str(arr)
#        driver = PySCFDriver(atom='H 0. 0.558243000 0.; H 0.483452000 -0.279121000 0.; H -0.483452000 -0.279121000 0.', basis="sto-3g")
#        problem = driver.run()
#        mapper = JordanWignerMapper()
#        ansatz = UCCSD(problem.num_spatial_orbitals,problem.num_particles,mapper,
#            initial_state=HartreeFock(problem.num_spatial_orbitals,problem.num_particles,mapper))
#        vqe = VQE(Estimator(), ansatz, SLSQP())
#        vqe.initial_point = np.zeros(ansatz.num_parameters)
#        adapt_vqe = AdaptVQE(vqe)
#        adapt_vqe.supports_aux_operators = lambda: True  # temporary fix
#        solver = GroundStateEigensolver(mapper, adapt_vqe)
#        result = solver.solve(problem)
#        finalarr.append(result.total_energies[0])
#    return finalarr

#orint(run_avqe3(X))
