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
def ell_mult_add(
    x: QNum,
    y: QNum,
    t0: QNum,
    l: QNum,
    k: QArray[QBit],
    P: list[int],
    p: int,
    a: int,
    b: int,
) -> None:
    """
    Compute (k * P) (scalar multiplication) and add the result (in-place) to res.
    P is a classical point (list [x, y]), res and k are quantum registers (QNum), and curve is an EllipticCurve object.
    (Quantum implementation using a double-and-add algorithm.)
    """

    n = k.size
    for i in range(n):

        control(k[i] == 1, lambda: ec_point_add(x, y, t0, l, P, p))
        # (Classically) update power (using ell_double) (i.e. power = ell_double(power, curve))
        curve = EllipticCurve(p=p, a=a, b=b)
        P = ell_double(P, curve)


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


if __name__ == "__main__":
    # Create and synthesize the model with width optimization
    constraints = Constraints(
        optimization_parameter="width",
    )  # Optimize for minimum width
    preferences = Preferences(timeout_seconds=3600, optimization_level=1)
    # Set up execution preferences for NVIDIA simulator
    execution_preferences = ExecutionPreferences(
        backend_preferences=ClassiqBackendPreferences(
            backend_name=ClassiqNvidiaBackendNames.SIMULATOR
        ),
        num_shots=1000,
    )
    print("Creating model...")
    qmod = create_model(main, constraints=constraints, preferences=preferences)
    # qmod = create_model(main, constraints=constraints, preferences=preferences, execution_preferences=execution_preferences)
    # qmod = create_model(main, execution_preferences=execution_preferences)
    # qmod = create_model(main)
    print("Synthesizing...")
    qprog = synthesize(qmod)
    show(qprog)
    # Print circuit metrics (number of qubits and circuit depth)
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
    print("Executing...")
    result = execute(qprog).result()
    print("Execution complete.")
    print("\nExecution Results:")
    print("Result:", result[0].value.parsed_counts)
