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
    bind,
    X,
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
)
from kaliski import mock_kaliski_inverse


@qfunc
def ec_point_add(
    x: QNum,  # x-coordinate of quantum point
    y: QNum,  # y-coordinate of quantum point
    G: list[int],  # Classical point coordinates [Gx, Gy] on the curve
    p: int,  # Prime modulus
) -> None:
    """
    Performs in-place elliptic curve point addition of a point whose coordinates are
    stored in quantum registers and a classically known point; the result of the
    operation is stored in the registers initially containing the coordinates of the
    input.

    Args:
        x: Quantum register containing the x-coordinate of the quantum point. The result x-coordinate will be stored in-place here.
        y: Quantum register containing the y-coordinate of the quantum point. The result y-coordinate will be stored in-place here.
        G: List of 2 classical coordinates [Gx, Gy] representing a point on the curve.
        p: Prime modulus for the elliptic curve operations.
    """
    # Extract classical coordinates
    Gx = G[0]  # x-coordinate of classical point
    Gy = G[1]  # y-coordinate of classical point

    # STEP 1: Compute terms for lambda (y - Gy) and (x - Gx) mod p (using modular_in_place_subtract_constant)
    # The results are stored back in y and x respectively.
    modular_in_place_subtract_constant(y, Gy, p)  # y becomes (y - Gy) mod p
    modular_in_place_subtract_constant(x, Gx, p)  # x becomes (x - Gx) mod p

    # STEP 2: Compute modular inverse of (x - Gx) mod p (using modular_out_of_place_multiply)
    mock_kaliski_inverse(x)
    temp = QNum("temp", x.size, SIGNED, 0)
    allocate(x.size, temp)
    modular_out_of_place_multiply(p, x, y, temp)
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
def main(anc_0: Output[QNum], anc_1: Output[QNum]) -> None:
    """
    Test function for elliptic curve point addition.
    Uses a sample curve: y^2 = x^3 + 2x + 3 (mod 7)
    """
    # Curve parameters
    p = 7

    # Allocate quantum registers for point coordinates
    allocate(3, anc_0)
    allocate(3, anc_1)

    # Initialize quantum point P = (4,5)
    anc_0 ^= 4  # x-coordinate
    anc_1 ^= 5  # y-coordinate

    # Test modular addition: should add 2 to anc_0 modulo 7
    # anc_0 should become (4 + 2) mod 7 = 6
    ec_point_add(anc_0, anc_1, [2, 3], 7)


# Create and synthesize the model
qmod = create_model(main)
qprog = synthesize(qmod)

show(qprog)  # Let's see what's happening in the circuit
result = execute(qprog).result()
print("Result:", result[0].value.parsed_counts)
