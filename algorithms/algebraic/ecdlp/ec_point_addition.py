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
    authenticate,
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
from classiq.execution import (
    ClassiqBackendPreferences,
    ClassiqSimulatorBackendNames,
    ClassiqNvidiaBackendNames,
    ExecutionPreferences,
)

# authenticate(overwrite=True)


class EllipticCurve:
    def __init__(self, p, a, b):
        """
        Represents an elliptic curve of the form y^2 = x^3 + a*x + b (mod p)
        :param p: The prime modulus of the field
        :param a: The 'a' parameter of the curve
        :param b: The 'b' parameter of the curve
        """
        self.p = p
        self.a = a
        self.b = b

    def __repr__(self):
        return f"EllipticCurve(p={self.p}, a={self.a}, b={self.b})"


@qfunc
def ec_point_add(
    x: QNum,  # x-coordinate of quantum point
    y: QNum,  # y-coordinate of quantum point
    t0: QNum,  # aux quantum register
    l: QNum,  # aux quantum register
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
        t0: Auxiliary quantum register for temporary storage
        l: Lamda
        G: List of 2 classical coordinates [Gx, Gy] representing a point on the curve.
        p: Prime modulus for the elliptic curve operations.
    """
    temp = QNum("temp")
    allocate(3, temp)
    # Extract classical coordinates
    Gx = G[0]  # x-coordinate of classical point
    Gy = G[1]  # y-coordinate of classical point

    # 1
    print("STEP 0")
    modular_in_place_subtract_constant(y, Gy, p)  # y becomes (y - Gy) mod p
    # 2
    modular_in_place_subtract_constant(x, Gx, p)  # x becomes (x - Gx) mod p
    # 3

    print("STEP 1")
    within_apply(
        lambda: mock_kaliski_inverse_modulus_7(x, t0),
        lambda: modular_out_of_place_multiply(t0, y, l, p),
    )

    print("STEP 2")
    within_apply(
        lambda: modular_out_of_place_multiply(l, x, t0, p),
        lambda: modular_in_place_subtract(t0, y, p),
    )

    print("STEP 3")
    within_apply(
        lambda: modular_square(l, t0, p),
        lambda: (
            modular_in_place_subtract(t0, x, p),
            modular_in_place_negate(x, p),
            modular_in_place_add_constant(x, (3 * Gx) % p, p),
        ),
    )

    print("STEP 4")
    modular_out_of_place_multiply(l, x, y, p)

    print("Clean L..")

    within_apply(
        lambda: mock_kaliski_inverse_modulus_7(x, t0),
        lambda: within_apply(
            lambda: modular_out_of_place_multiply(t0, y, temp, p),
            lambda: modular_in_place_subtract(temp, l, p),
        ),
    )

    print("STEP 5")
    modular_in_place_subtract_constant(y, Gy, p)

    modular_in_place_negate(x, p)
    modular_in_place_add_constant(x, Gx, p)

    free(temp)


def ell_double(P: list, curve):
    """
    Return 2P for a point P on the elliptic curve.
    P: [x, y] coordinates of the point.
    curve: an object with attributes p (modulus) and a (curve parameter).
    """
    p = curve.p
    x, y = P
    # Slope calculation: s = (3*x^2 + a) / (2*y) mod p
    numerator = (3 * (x * x % p) + curve.a) % p
    denominator = (2 * y) % p
    s = (numerator * pow(denominator, -1, p)) % p
    # x-coordinate of the result
    xr = (s * s - 2 * x) % p
    # y-coordinate of the result
    yr = (y - s * ((x - xr) % p)) % p
    # Return the result, with y in the standard form (p - yr) % p
    return [xr, (p - yr) % p]


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
    anc_0: Output[QNum], anc_1: Output[QNum], t0: Output[QNum], l: Output[QNum]
) -> None:
    """
    Test function for elliptic curve point addition.
    Uses a sample curve: y^2 = x^3 + 2x + 3 (mod 7)
    """
    # Curve parameters
    p = 7
    # Points on the curve:
    P = [5, 0]
    Q = [4, 1]
    print(f"[main] Adding point P = {P} and Q = {Q}")
    allocate(3, anc_0)
    allocate(3, anc_1)
    allocate(3, t0)
    allocate(3, l)
    c = QBit()
    allocate(1, c)
    c ^= 1
    anc_0 ^= P[0]
    anc_1 ^= P[1]
    control(c == 1, lambda: ec_point_add(anc_0, anc_1, t0, l, Q, 7))
    # ec_point_add(anc_0, anc_1, t0, l, Q, 7)


# Create and synthesize the model with width optimization

constraints = Constraints(
    optimization_parameter="width",  # Optimize for minimum width
)


# preferences = Preferences(synthesize_all_separately=True,timeout_seconds=3600)
preferences = Preferences(timeout_seconds=3600, optimization_level=1)

# Set up execution preferences for NVIDIA simulator
execution_preferences = ExecutionPreferences(
    backend_preferences=ClassiqBackendPreferences(
        backend_name=ClassiqNvidiaBackendNames.SIMULATOR
    ),
    num_shots=1000,  # You can adjust the number of shots as needed
)

print("Creating model...")
qmod = create_model(main, constraints=constraints, preferences=preferences)
# qmod = create_model(main, constraints=constraints, preferences=preferences, execution_preferences=execution_preferences)
# qmod = create_model(main, execution_preferences=execution_preferences)
# qmod = create_model(main)
print("Synthesizing...")
qprog = synthesize(qmod)
show(qprog)
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

print("Executing...")
result = execute(qprog).result()
print("Execution complete.")
print("\nExecution Results:")
print("Result:", result[0].value.parsed_counts)
