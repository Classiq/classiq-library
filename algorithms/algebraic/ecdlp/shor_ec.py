"""
Shor's algorithm to solve a small instance of the ECDLP using Classiq and custom EC arithmetic.
"""

from classiq import (
    qfunc,
    QNum,
    QArray,
    QBit,
    Output,
    allocate,
    create_model,
    synthesize,
    show,
    execute,
    hadamard_transform,
    qft,
    invert,
    Constraints,
    Preferences,
)
from ec_point_addition import ell_mult_add, EllipticCurve
from tests_ec_point_add import (
    GLOBAL_G,
    GLOBAL_INITIAL_ECP,
    GLOBAL_TARGET_ECP,
    GLOBAL_CURVE,
)
from classiq.qmod.symbolic import ceiling, log

# Elliptic curve parameters
p = 7
a = 5
b = 4
curve = EllipticCurve(p=p, a=a, b=b)

# Number of bits for QPE registers
n = p.bit_length()


@qfunc
def main(
    ecp_x: Output[QNum],
    ecp_y: Output[QNum],
    t0: Output[QNum],
    l: Output[QNum],
    x1: Output[QNum],
    x2: Output[QNum],
) -> None:
    # Allocate quantum registers for the EC point and QPE variables
    allocate(3, ecp_x)
    allocate(3, ecp_y)
    allocate(3, t0)
    allocate(3, l)
    allocate(n, x1)
    allocate(n, x2)

    # Initialize ecp to GLOBAL_INITIAL_ECP
    ecp_x ^= GLOBAL_INITIAL_ECP[0]
    ecp_y ^= GLOBAL_INITIAL_ECP[1]

    # Use global generator and target
    G = GLOBAL_G
    P = GLOBAL_TARGET_ECP
    curve = GLOBAL_CURVE

    # Superposition on x1 and x2
    hadamard_transform(x1)
    hadamard_transform(x2)

    # In-place EC arithmetic step 1: ecp = P0 + x1*G
    ell_mult_add(ecp_x, ecp_y, t0, l, x1, G, curve.p, curve.a, curve.b)
    # In-place EC arithmetic step 2: ecp = P0 + x1*G - x2*P
    # To subtract x2*P, add the negative of P (i.e., [P[0], -P[1] mod p])
    negP = [P[0], (-P[1]) % curve.p]
    ell_mult_add(ecp_x, ecp_y, t0, l, x2, negP, curve.p, curve.a, curve.b)

    # Inverse Quantum Fourier Transform on x1 and x2
    invert(lambda: qft(x1))
    invert(lambda: qft(x2))


def run_shor_quantum():
    constraints = Constraints(
        optimization_parameter="width",
    )  # Optimize for minimum width
    preferences = Preferences(timeout_seconds=3600, optimization_level=1)

    print("Creating model for Shor's ECDLP algorithm...")
    qmod = create_model(main, constraints=constraints, preferences=preferences)
    print("Synthesizing...")
    qprog = synthesize(qmod)
    num_qubits = qprog.data.width
    if hasattr(qprog.data, "circuit_depth"):
        print("Circuit depth:", qprog.data.circuit_depth)
    elif hasattr(qprog, "transpiled_circuit") and hasattr(
        qprog.transpiled_circuit, "depth"
    ):
        print("Circuit depth:", qprog.transpiled_circuit.depth)
    else:
        print("Depth attribute not found. Available attributes:", dir(qprog.data))
    print(f"Number of qubits: {num_qubits}")
    show(qprog)
    print("Executing...")
    result = execute(qprog).result()
    print("Execution complete.")
    print("\nExecution Results:")
    print("Result:", result[0].value.parsed_counts)
    return result[0].value.parsed_counts


if __name__ == "__main__":
    run_shor_quantum()
