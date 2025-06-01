from classiq import (
    qfunc,
    QArray,
    QNum,
    QBit,
    Output,
    allocate,
    create_model,
    synthesize,
    show,
    inplace_add,
    control,
    free,
    execute,
    within_apply,
    invert,
    bind,
    X,
    Constraints,
    Preferences,
)
from classiq.qmod import SIGNED
from classiq.qmod.symbolic import log, ceiling
from modular_arithmetic import (
    modular_in_place_add,
    modular_in_place_subtract,
    modular_in_place_add_constant,
    modular_in_place_subtract_constant,
    modular_in_place_double,
    modular_out_of_place_multiply,
    modular_in_place_negate,
    modular_square,
)
from kaliski import mock_kaliski_inverse_modulus_7


@qfunc
def ec_point_add(
    x: QNum,  # x-coordinate of quantum point
    y: QNum,  # y-coordinate of quantum point
    t0: QNum,  # aux quantum register
    l: QNum,  # aux quantum register
    G: list[int],  # Classical point coordinates [Gx, Gy] on the curve
    p: int,  # Prime modulus
    c: QBit,  # Control qubit
) -> None:
    """
    Performs in-place elliptic curve point addition of a point whose coordinates are
    stored in quantum registers and a classically known point; the result of the
    operation is stored in the registers initially containing the coordinates of the
    input.

    Args:
        x: Quantum register containing the x-coordinate of the quantum point. The result x-coordinate will be stored in-place here.
        y: Quantum register containing the y-coordinate of the quantum point. The result y-coordinate will be stored in-place here.
        t0: Auxiliary quantum register for temporary storage
        l: Lamda
        G: List of 2 classical coordinates [Gx, Gy] representing a point on the curve.
        p: Prime modulus for the elliptic curve operations.
        ctrl: Control qubit that determines whether the point addition is performed.
    """
    # Extract classical coordinates
    Gx = G[0]  # x-coordinate of classical point
    Gy = G[1]  # y-coordinate of classical point

    # 1
    modular_in_place_subtract_constant(y, Gy, p)  # y becomes (y - Gy) mod p
    # 2
    modular_in_place_subtract_constant(x, Gx, p)  # x becomes (x - Gx) mod p
    # 3

    within_apply(
        lambda: mock_kaliski_inverse_modulus_7(x, t0),
        lambda: modular_out_of_place_multiply(t0, y, l, p),
    )

    within_apply(
        lambda: modular_out_of_place_multiply(l, x, t0, p),
        lambda: modular_in_place_subtract(t0, y, p),
    )

    within_apply(
        lambda: modular_square(l, t0, p),
        lambda: (
            modular_in_place_subtract(t0, x, p),
            modular_in_place_negate(x, p),
            modular_in_place_add_constant(x, 3 * Gx, p),
        ),
    )

    modular_out_of_place_multiply(l, x, y, p)

    within_apply(
        lambda: mock_kaliski_inverse_modulus_7(x, t0),
        lambda: invert(lambda: modular_out_of_place_multiply(t0, y, l, p)),
    )

    modular_in_place_subtract_constant(y, Gy, p)

    modular_in_place_negate(x, p)
    modular_in_place_add_constant(x, Gx, p)

    # modular_square(l,t0,p)
    # 8
    # modular_in_place_subtract(t0,x,p)
    # modular_in_place_negate(p,x)

    # 9

    # 10
    # modular_square(l,t0,p)

    """

    #3,4,5
    within_apply(
        lambda: mock_kaliski_inverse_modulus_7(x,t0),
        lambda: modular_out_of_place_multiply(t0, y, l, p),
    )

    #6
    modular_out_of_place_multiply(p, l, x,y)
    #7
    print("7")
    modular_square(l,t0,p)
    #8
    print("8")
    modular_in_place_subtract(x,t0,p)
    #9
    print("9")
    modular_in_place_add_constant(x,3*Gx,p)
    #10
    print("10")
    modular_square(l,t0,p)
    #11
    print("11)")
    modular_out_of_place_multiply(p, l, x,y)
    """

    # x = temp

    # TODO: Implement the rest of point addition using modular arithmetic operations (using modular_in_place_add, modular_in_place_subtract, modular_in_place_add_constant, modular_in_place_subtract_constant, modular_in_place_double, modular_out_of_place_multiply, and modular_in_place_negate)
    # This will require:
    # 1. Computing modular inverse of (x - Gx) mod p (which is now stored in x) (using modular_out_of_place_multiply)
    # 2. Computing λ = (y - Gy) * (x - Gx)^(-1) mod p (using modular_out_of_place_multiply)
    # 3. Computing new x-coordinate: λ^2 - x_original - Gx mod p (using modular_in_place_add, modular_in_place_subtract, modular_in_place_add_constant, modular_in_place_subtract_constant, modular_in_place_double, modular_out_of_place_multiply, and modular_in_place_negate) (Need original x value!)
    # 4. Computing new y-coordinate: λ(x_original - x3) - y_original mod p (using modular_in_place_add, modular_in_place_subtract, modular_in_place_add_constant, modular_in_place_subtract_constant, modular_in_place_double, modular_out_of_place_multiply, and modular_in_place_negate) (Need original x and y values!)
    # 5. Storing results back in x and y (using modular_in_place_add, modular_in_place_subtract, modular_in_place_add_constant, modular_in_place_subtract_constant, modular_in_place_double, modular_out_of_place_multiply, and modular_in_place_negate)

    # Note: We need to preserve the original x and y values for later steps (using modular_in_place_add, modular_in_place_subtract, modular_in_place_add_constant, modular_in_place_subtract_constant, modular_in_place_double, modular_out_of_place_multiply, and modular_in_place_negate).
    # The current implementation overwrites them in STEP 1.
    # We might need temporary registers or a different approach for STEP 1.

    pass


@qfunc
def ec_point_double(
    x: QNum,  # x-coordinate of point
    y: QNum,  # y-coordinate of point
    a: int,  # curve parameter a
    p: int,  # prime modulus
) -> None:
    """
    Performs elliptic curve point doubling (using modular_in_place_add, modular_in_place_subtract, modular_in_place_add_constant, modular_in_place_subtract_constant, modular_in_place_double, modular_out_of_place_multiply, and modular_in_place_negate): 2P = R where P=(x,y)
    For curve: y^2 = x^3 + ax + b (mod p)

    The doubling is performed using the following formulas (using modular_in_place_add, modular_in_place_subtract, modular_in_place_add_constant, modular_in_place_subtract_constant, modular_in_place_double, modular_out_of_place_multiply, and modular_in_place_negate):
    λ = (3x^2 + a)/(2y) mod p
    x3 = λ^2 - 2x mod p
    y3 = λ(x - x3) - y mod p

    Args:
        x, y: Coordinates of point P
        a: Curve parameter
        p: Prime modulus
    """
    # TODO: Implement point doubling using modular arithmetic operations (using modular_in_place_add, modular_in_place_subtract, modular_in_place_add_constant, modular_in_place_subtract_constant, modular_in_place_double, modular_out_of_place_multiply, and modular_in_place_negate)
    pass


@qfunc
def main(
    anc_0: Output[QNum],
    anc_1: Output[QNum],
    t0: Output[QNum],
    l: Output[QNum],
    c: Output[QBit],
) -> None:
    """
    Test function for elliptic curve point addition.
    Uses a sample curve: y^2 = x^3 + 2x + 3 (mod 7)
    """
    # Curve parameters
    p = 7

    # Allocate quantum registers for point coordinates
    allocate(3, anc_0)
    allocate(3, anc_1)
    allocate(3, t0)
    allocate(3, l)
    allocate(1, c)

    # Initialize quantum point P = (4,5)
    anc_0 ^= 0  # x-coordinate
    anc_1 ^= 1  # y-coordinate

    # Set control qubit to 1 to enable point addition

    # Test modular addition: should add point (2,3) to (4,5) modulo 7
    ec_point_add(anc_0, anc_1, t0, l, [2, 5], 7, c)


# Create and synthesize the model with width optimization

constraints = Constraints(
    optimization_parameter="width",  # Optimize for minimum width
)


preferences = Preferences(synthesize_all_separately=True, timeout_seconds=3600)

# qmod = create_model(main, constraints=constraints, preferences=preferences)
qmod = create_model(main)
qprog = synthesize(qmod)

# Print circuit metrics
# Number of qubits
num_qubits = qprog.data.width

# Circuit depth
if hasattr(qprog.data, "circuit_depth"):
    print("Circuit depth:", qprog.data.circuit_depth)
elif hasattr(qprog, "transpiled_circuit") and hasattr(
    qprog.transpiled_circuit, "depth"
):
    print("Circuit depth:", qprog.transpiled_circuit.depth)
else:
    print("Depth attribute not found. Available attributes:", dir(qprog.data))

print(f"Number of qubits: {num_qubits}")

# Execute and show results
result = execute(qprog).result()
print("\nExecution Results:")
print("Result:", result[0].value.parsed_counts)
