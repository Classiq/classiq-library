from classiq import *

# Define the size of the qubits used for the vertices and adjacent vertices
size_circle = 2
size_line = 4

@qfunc
def prepare_minus(x: QBit):
    """Prepare a qubit in the |-⟩ state"""
    X(x)  # Pauli-X gate
    H(x)  # Hadamard gate

@qfunc
def diffuser_oracle(aux: Output[QNum], x: QNum):
    """Set the auxiliary qubit based on whether x is not zero"""
    aux ^= (x != 0)

@qfunc
def zero_diffuser(x: QNum):
    """Allocate and prepare the auxiliary qubit, then apply the diffuser oracle"""
    aux = QNum('aux')
    allocate(1, aux)
    within_apply(compute=lambda: prepare_minus(aux),
                 action=lambda: diffuser_oracle(aux, x))

def W_iteration_circle(i: int, vertices: QNum, adjacent_vertices: QNum):
    """Quantum walk iteration for a circle with 4 nodes"""
    prob = [0, 0, 0, 0]
    prob[(i + 1) % 4] = 0.5
    prob[(i - 1) % 4] = 0.5
    print(f'State={i}, prob vec={prob}')
    
    control(ctrl=vertices == i,
            operand=lambda: within_apply(
                compute=lambda: inplace_prepare_state(probabilities=prob, bound=0.01, target=adjacent_vertices),
                action=lambda: zero_diffuser(adjacent_vertices)))

@qfunc
def W_operator_circle(vertices: QNum, adjacent_vertices: QNum):
    for i in range(2 ** size_circle):
        W_iteration_circle(i, vertices, adjacent_vertices)

def W_iteration_line(i: int, vertices: QNum, adjacent_vertices: QNum):
    """Quantum walk iteration for a line with 16 nodes"""
    prob = [0] * 16
    if i > 0:
        prob[i - 1] = 0.5
    if i < 15:
        prob[i + 1] = 0.5
    print(f'State={i}, prob vec={prob}')
    
    control(ctrl=vertices == i,
            operand=lambda: within_apply(
                compute=lambda: inplace_prepare_state(probabilities=prob, bound=0.01, target=adjacent_vertices),
                action=lambda: zero_diffuser(adjacent_vertices)))

@qfunc
def W_operator_line(vertices: QNum, adjacent_vertices: QNum):
    for i in range(2 ** size_line):
        W_iteration_line(i, vertices, adjacent_vertices)

@qfunc
def edge_oracle(res: Output[QBit], vertices: QNum, adjacent_vertices: QNum):
    res |= (((vertices + adjacent_vertices) % 2) == 1)

@qfunc
def bitwise_swap(x: QArray[QBit], y: QArray[QBit]):
    repeat(count=x.len,
           iteration=lambda i: SWAP(x[i], y[i]))

@qfunc
def S_operator(vertices: QNum, adjacent_vertices: QNum):
    res = QNum('res')
    edge_oracle(res, vertices, adjacent_vertices)
    control(ctrl=res == 1,
            operand=lambda: bitwise_swap(vertices, adjacent_vertices))

@qfunc
def main_circle(vertices: Output[QNum], adjacent_vertices: Output[QNum]):
    allocate(size_circle, vertices)
    hadamard_transform(vertices)
    allocate(size_circle, adjacent_vertices)
    
    W_operator_circle(vertices, adjacent_vertices)
    S_operator(vertices, adjacent_vertices)

@qfunc
def main_line(vertices: Output[QNum], adjacent_vertices: Output[QNum]):
    allocate(size_line, vertices)
    hadamard_transform(vertices)
    allocate(size_line, adjacent_vertices)
    
    W_operator_line(vertices, adjacent_vertices)
    S_operator(vertices, adjacent_vertices)

# Synthesize and display the quantum program for a circle with 4 nodes
qmod_circle = create_model(main_circle)
qprog_circle = synthesize(qmod_circle)
print("Quantum walk on a circle with 4 nodes:")
show(qprog_circle)

# Synthesize and display the quantum program for a line with 16 nodes
qmod_line = create_model(main_line)
qprog_line = synthesize(qmod_line)
print("Quantum walk on a line with 16 nodes:")
show(qprog_line)

