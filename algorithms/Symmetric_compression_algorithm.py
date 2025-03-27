from classiq import *
from classiq.qmod.symbolic import pi
from scipy.special import comb
import numpy as np
from math import sqrt

# authenticate()

#####################################################################################################################
#                                                                                                                   #
#   Implementation of the paper "Efficient compression of quantum information" (https://arxiv.org/pdf/0907.1764)    #
#                                                                                                                   #
#                                                                                                                   #
#                                                                                                                   #
#####################################################################################################################




###
# Defining the function that is creating the gate U_ab. This is part of the gate U from the paper and represents
# a three qubit gate that is constructed based on values b, b + 1 and a. This is the first operation of gate U. 
# 
# 
# 
# a - integer value representing the index of qubit a
# b - integer value representing the index of qubit b
# 
# ###
def U_ab(a, b):
    
    U = np.eye(8, dtype=complex)
    
    # Compute coefficients as illustrated in the paper
    alpha_101 = np.sqrt(comb(a - 1, b, exact=True))
    alpha_010 = np.sqrt(comb(a - 1, b + 1, exact=True))
    beta_010 = np.sqrt(comb(a, b + 1, exact=True))
    
    x = alpha_010 / beta_010
    y = alpha_101 / beta_010
    
    # Performing the superposition swap as presented in the paper.
    i_rot, j_rot = (2, 5)
    U[i_rot, i_rot] = x
    U[i_rot, j_rot] = y
    U[j_rot, i_rot] = y
    U[j_rot, j_rot] = -x
    
    return U



###
# Defining the function that is creating the gate U_f. This is part of the gate U from the paper and represents
# a three qubit gate that is constructed based on values 0, a-1 and a. This is the second operation of gate U. 
# 
# 
# 
# a - integer value representing the index of qubit a
# 
# ###
def U_final(a):
    
    # Compute coefficients as illustrated in the paper
    alpha_001 = 1
    alpha_100 = sqrt((a-1))
    beta_100 = sqrt(a)
    
    x = alpha_100 / beta_100
    y = alpha_001 / beta_100
    
    
    # Performing the superposition swap as presented in the paper.
    U = np.eye(8, dtype=complex)
    i_rot, j_rot = (1, 4)
    U[i_rot, i_rot] = x
    U[i_rot, j_rot] = y
    U[j_rot, i_rot] = -y
    U[j_rot, j_rot] = x
    
    return U


####
# This function is going to be used for applying the U_ab and U_f gates over the specific qubits in the circuit.
# 
# 
# 
# matrix - input matrix that needs to be constructed before 
# q - QArray
# p1, p2, p3 - the qubits on which the gate given my matrix needs to be applied
# 
####
@qfunc(generative=True)
def apply_matrix(matrix: CArray[CArray[CReal]], q: QArray[QBit], p1: CInt, p2: CInt, p3: CInt):
    
    ## constructing a temporary QArray of qubits representing the specific qubits in q given by p1, p2, p3
    qubits = []
    temp_array = QArray()
    for k in range(q.len):
        qubits.append(QBit(f'q{k}'))
    bind(q, qubits)
    bind([qubits[p1], qubits[p2], qubits[p3]], temp_array)
    
    
    ## aplying the matrix using the unitary built-in function
    unitary(matrix, temp_array)
        
    ## constructing back the original QArray
    bind(temp_array, [qubits[p1], qubits[p2], qubits[p3]])
    bind(qubits, q)
    
       
       
####
# This function is a wrapper of the function U_ab and has the purpose of applying the gate for as many times as needed
# as it is ilustrated in the paper. U_ab needs to be applied for every qubit b from 1 to a-2.
# 
# 
# 
# a - index of the current qubit a
# q - QArray
# 
####    
@qfunc(generative=True)
def apply_Uab(a: CReal, q: QArray[QBit]):
    
    for b in range(a-1):
        Uab = U_ab(a+1, b+1)
        apply_matrix(Uab, q, b, b+1, a)
        


####
# This function is a wrapper of the function U_f and has the purpose of applying the gate 1 time as stated in paper.
# The gate is going to be applied on qubits 0, a-1 and a.
# 
# 
# 
# a - index of the current qubit a
# q - QArray
# 
####           
@qfunc(generative=True)
def apply_Uf(a: CReal, q: QArray[QBit]):
    
    Uf = U_final(a+1)
    apply_matrix(Uf, q, 0, a-1, a)    



####
# This function has the role of creating and applying a multi-controlled NOT operation given a set of qubit indeces.
# The controls list contains the list of the qubits that needs to be the ocntroll qubits and the last element in the 
# list represents the target element.
# 
# 
# 
# q - QArray
# controls - list of integers containing the indexes of qubits that need to be the control qubits (controls[0:-1])
#            and the index of the target qubit (controls[-1])
#
####      
@qfunc(generative=True)
def apply_MultiCNOT(q: QArray[QBit], controls: CArray[CInt]):
    
    ## constructing a temporary QArray of qubits representing the specific qubits in q given by the indexes in controls
    qubits = []
    temp_array = QArray()
    for qb in range(q.len):
        qubits.append(QBit(f'q{qb}'))
    bind(q, qubits)
    bind([qubits[i] for i in controls], temp_array)    
    
    ## applying the CONTROL operation
    control(temp_array[0:len(controls)-1], lambda:X(temp_array[len(controls)-1]))
    
    
    ## constructing back the original QArray
    bind(temp_array, [qubits[i] for i in controls])
    bind(qubits, q)



##########################
# THE PRINCIPAL FUNCTION #
##########################
@qfunc(generative=True)
def symmetric_compression_algorithm(q_array: QArray[QBit]):
    
    ## Implementing the V gate from the paper
    control(q_array[1], lambda: X(q_array[0]))
    control(q_array[0], lambda: H(q_array[1]))
    
    
    ## Applying the U gates as in paper. This sequence will construct the |C>_k bases for the symmetric states.
    for i in range(2, q_array.len):
        apply_Uab(i, q_array)
        apply_Uf(i, q_array)
        
        # The last CNOT is the personal addition because the description in the paper is not quite exact on the 
        # implentation part. They are just describing what the functions should do.
        control(q_array[i], lambda: X(q_array[i-1]))
        
    
    ## Applying the last sequence described in paper for converting the |C>_k into |B>_k. Implementing the indications
    ## from the paper.
    for k in range(2, q_array.len):
        index = 0
        indeces = []
        for i in range(len(bin(k+1)[2:])):
            if bin(k+1)[2:][i] == '1':
                
                control(q_array[k], lambda: X(q_array[len(bin(k+1)[2:])-i-1]))
                
                indeces.append(len(bin(k+1)[2:])-i-1)
                index += 1
        indeces = indeces[::-1]
        indeces.append(k)
        apply_MultiCNOT(q_array, indeces) 
    


