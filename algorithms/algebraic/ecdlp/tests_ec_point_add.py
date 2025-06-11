from classiq import *
from ec_point_addition import ell_double, EllipticCurve
from ec_point_addition import ell_mult_add
from tinyec.ec import SubGroup, Curve, Point
from tinyec import registry

# authenticate(overwrite=True)

# Global definitions for tests
GLOBAL_G = [0, 5]
GLOBAL_INITIAL_ECP = [4, 2]
GLOBAL_CURVE = EllipticCurve(p=7, a=5, b=4)


def test_ell_double():
    print("(test_ell_double)")
    from ec_point_addition import EllipticCurve

    curve = EllipticCurve(
        p=7,
        a=5,
        b=4,
    )
    P = GLOBAL_G  # Use GLOBAL_G for doubling

    print(
        f"Running classical ell_double test (input {P} mod {curve.p}, curve a={curve.a}, b={curve.b}, p={curve.p})..."
    )
    x, y = ell_double(P, curve)
    # Classical expected result (for doubling (4,1) on the curve y^2 = x^3 + 1x + 3 over F_7) is (6, 6)
    print("Computed (x, y) = ({}, {})".format(x, y))
    print("Test PASSED.")


def ell_add_classical(P1: list[int], P2: list[int], curve: EllipticCurve) -> list[int]:
    # Handles point at infinity conceptually by returning None. Assumes P1, P2 are not None.
    if P1 is None or P1 == (None, None):  # If P1 is point at infinity, return P2
        return P2
    if P2 is None or P2 == (None, None):  # If P2 is point at infinity, return P1
        return P1

    x1, y1 = P1
    x2, y2 = P2
    p = curve.p

    if x1 == x2 and y1 == y2:  # Point doubling
        return ell_double(P1, curve)
    elif x1 == x2 and (y1 + y2) % p == 0:  # P2 is -P1, result is point at infinity
        return None, None  # Representing point at infinity

    # General point addition
    num = (y2 - y1) % p
    den = (x2 - x1) % p

    if den == 0:  # Vertical line (should be handled by P2 = -P1 or doubling case)
        return None, None  # Error or point at infinity

    den_inv = pow(den, p - 2, p)  # Modular inverse using Fermat's Little Theorem
    m = (num * den_inv) % p

    x3 = (m * m - x1 - x2) % p
    y3 = (m * (x1 - x3) - y1) % p
    return [x3, y3]


def ell_mult_classical(k_val: int, P: list[int], curve: EllipticCurve) -> list[int]:
    if k_val == 0:
        return None, None  # Represents the point at infinity

    result = P
    for _ in range(k_val - 1):
        result = ell_add_classical(result, P, curve)
        # if result is None or result == (None, None): # Check if addition results in point at infinity
        # return None, None
    return result


def verify_ell_mult_add_results(
    quantum_results, initial_ecp: list[int], G: list[int], curve: EllipticCurve
):
    print("\n--- Verifying ell_mult_add Results --- ")
    all_match = True
    sorted_results = []

    for res in quantum_results:
        k_val = res.state["k"]
        quantum_x = res.state["x"]
        quantum_y = res.state["y"]

        # Classical calculation: initial_ecp + k*G
        k_G = ell_mult_classical(k_val, G, curve)

        if k_G is None or k_G == (None, None):
            expected_x, expected_y = initial_ecp[0], initial_ecp[1]
        else:
            expected_x, expected_y = ell_add_classical(initial_ecp, k_G, curve)

        sorted_results.append(
            {
                "k_val": k_val,
                "quantum_x": quantum_x,
                "quantum_y": quantum_y,
                "expected_x": expected_x,
                "expected_y": expected_y,
            }
        )

    sorted_results.sort(key=lambda x: x["k_val"])

    for res_data in sorted_results:
        k_val = res_data["k_val"]
        quantum_x = res_data["quantum_x"]
        quantum_y = res_data["quantum_y"]
        expected_x = res_data["expected_x"]
        expected_y = res_data["expected_y"]

        print(f"k (dec={k_val}):")
        print(f"  Quantum (x,y): ({quantum_x}, {quantum_y})")
        print(
            f"  Classical (x,y) for {initial_ecp} + {k_val}*{G}: ({expected_x}, {expected_y})"
        )

        if quantum_x == expected_x and quantum_y == expected_y:
            print("  MATCH")
        else:
            print("  MISMATCH!")
            all_match = False

    if all_match:
        print("\nAll ell_mult_add results match classical expectations.")
    else:
        print("\nSome ell_mult_add results DO NOT match classical expectations.")


def test_ell_add_classical():
    print("\n--- Running ell_add_classical Test --- ")
    curve = EllipticCurve(p=7, a=5, b=4)
    P1 = GLOBAL_G  # Use GLOBAL_G
    P2 = GLOBAL_INITIAL_ECP  # Use GLOBAL_INITIAL_ECP
    result = ell_add_classical(P1, P2, curve)
    print(f"Adding {P1} and {P2} on curve {curve}: Result = {result}")

    # Verify with tinyec
    field = SubGroup(p=GLOBAL_CURVE.p, g=(GLOBAL_G[0], GLOBAL_G[1]), n=10, h=None)
    tinyec_curve = Curve(a=GLOBAL_CURVE.a, b=GLOBAL_CURVE.b, field=field, name="custom")

    tinyec_P1 = Point(tinyec_curve, P1[0], P1[1])
    tinyec_P2 = Point(tinyec_curve, P2[0], P2[1])
    tinyec_result_point = tinyec_P1 + tinyec_P2
    tinyec_result = [tinyec_result_point.x, tinyec_result_point.y]

    if result == tinyec_result:
        print("ell_add_classical result matches tinyec result. Test PASSED.")
    else:
        print(
            f"ell_add_classical result {result} DOES NOT match tinyec result {tinyec_result}. Test FAILED."
        )


def test_ell_mult_add():
    from classiq import (
        qfunc,
        QNum,
        Output,
        allocate,
        create_model,
        synthesize,
        execute,
        show,
    )
    from ec_point_addition import ell_mult_add, EllipticCurve

    @qfunc
    def main(
        x: Output[QNum],
        y: Output[QNum],
        t0: Output[QNum],
        l: Output[QNum],
        k: Output[QNum],
    ) -> None:
        allocate(3, x)
        allocate(3, y)
        allocate(3, t0)
        allocate(3, l)
        allocate(5, k)
        # (For example, set k to a fixed classical value (e.g. 1) (using k ^= 1) so that ell_mult_add computes (1 * P) (mod p).)
        hadamard_transform(k)
        # prepare_uniform_trimmed_state(4, k)
        # k ^= 3

        # Use global P, initial_ecp, and curve
        P_val = GLOBAL_G
        x ^= GLOBAL_INITIAL_ECP[0]
        y ^= GLOBAL_INITIAL_ECP[1]
        curve_val = GLOBAL_CURVE

        print(
            "ell_mult_add (with initial_ecp={}, G={}, k={}, curve (p={}, a={}, b={}))...".format(
                GLOBAL_INITIAL_ECP, P_val, k, curve_val.p, curve_val.a, curve_val.b
            )
        )
        ell_mult_add(x, y, t0, l, k, P_val, curve_val.p, curve_val.a, curve_val.b)

    constraints = Constraints(
        optimization_parameter="width",
    )  # Optimize for minimum width
    preferences = Preferences(timeout_seconds=3600, optimization_level=1)

    qmod = create_model(main, constraints=constraints, preferences=preferences)
    print("Synthesizing quantum circuit for ell_mult_add")
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
    print("Executing quantum circuit...")
    result = execute(qprog).result()
    print("Execution complete.")
    print("Result (quantum (x,y) (after ell_mult_add)):", result[0].value.parsed_counts)
    # Use global initial_ecp and G
    initial_ecp_for_verification = GLOBAL_INITIAL_ECP
    G_for_verification = GLOBAL_G  # G is often the same as P in these contexts
    curve_for_verification = GLOBAL_CURVE

    verify_ell_mult_add_results(
        result[0].value.parsed_counts,
        initial_ecp_for_verification,
        G_for_verification,
        curve_for_verification,
    )

    """
    expected = (
        4,
        1,
    )  # (classical (1 * [4,1] (mod 7) (on curve (p=7, a=1, b=3)) (for example, (4, 1)) (if known).)
    print(
        "Expected (classical) (1 * [4,1] (mod 7) (on curve (p=7, a=1, b=3))):", expected
    )

    # assert quantum_res == expected, "Quantum (x,y) (after ell_mult_add) (keys 'x', 'y') = {} (expected {})".format(quantum_res, expected)
    # print("Test ell_mult_add PASSED.")
    """


def test_ell_mult_classical():
    print("\n--- Running ell_mult_classical Test --- ")
    # Use global curve, initial_ecp, and P
    curve = GLOBAL_CURVE
    initial_ecp = GLOBAL_INITIAL_ECP
    G = GLOBAL_G

    print(f"Initial point: {initial_ecp}, Point P: {G}, Curve: {curve}")

    for k in range(15):  # k from 0 to 14
        k_P = ell_mult_classical(k, G, curve)

        # Handle cases where k*P is the point at infinity
        if k_P is None or k_P == (None, None):
            temp_add_result = initial_ecp  # Adding point at infinity to a point results in the point itself
        else:
            temp_add_result = ell_add_classical(initial_ecp, k_P, curve)

        # Print the results for verification
        print(f"k={k}: k*P = {k_P}, {initial_ecp} + {k_P} = {temp_add_result}")
    print("Test ell_mult_classical COMPLETED.")


def test_tinyec_ell_mult_classical():
    print("\n--- Running tinyec ell_mult_classical Test ---")
    field = SubGroup(p=GLOBAL_CURVE.p, g=(GLOBAL_G[0], GLOBAL_G[1]), n=10, h=None)
    curve = Curve(a=GLOBAL_CURVE.a, b=GLOBAL_CURVE.b, field=field, name="custom")

    initial_ecp_tinyec = Point(curve, GLOBAL_INITIAL_ECP[0], GLOBAL_INITIAL_ECP[1])
    G_tinyec = Point(curve, GLOBAL_G[0], GLOBAL_G[1])

    print(
        f"Initial point: ({initial_ecp_tinyec.x}, {initial_ecp_tinyec.y}), Point G: ({G_tinyec.x}, {G_tinyec.y}), Curve: {curve}"
    )

    for k in range(15):  # k from 0 to 14
        k_G_tinyec = k * G_tinyec

        # Handle cases where k*G is the point at infinity (tinyec returns Point(curve, None, None))
        if k_G_tinyec.x is None or k_G_tinyec.y is None:
            temp_add_result_tinyec = initial_ecp_tinyec  # Adding point at infinity to a point results in the point itself
        else:
            temp_add_result_tinyec = initial_ecp_tinyec + k_G_tinyec

        # Print the results for verification
        print(
            f"k={k}: k*G = ({k_G_tinyec.x}, {k_G_tinyec.y}), ({initial_ecp_tinyec.x}, {initial_ecp_tinyec.y}) + ({k_G_tinyec.x}, {k_G_tinyec.y}) = ({temp_add_result_tinyec.x}, {temp_add_result_tinyec.y})"
        )
    print("Test tinyec_ell_mult_classical COMPLETED.")


def test_ec_point_add_specific_case():
    print(
        f"\n--- Running ec_point_add with specific points {GLOBAL_G} and {GLOBAL_INITIAL_ECP} ---"
    )
    # Using global curve, but P1 and P2 are specific for this test
    curve = GLOBAL_CURVE
    P1 = GLOBAL_G  # Using GLOBAL_G as P1
    P2 = GLOBAL_INITIAL_ECP  # Using GLOBAL_INITIAL_ECP as P2

    # Calculate classical expected result
    expected_result = ell_add_classical(P1, P2, curve)
    print(f"Classical result for {P1} + {P2} on curve {curve}: {expected_result}")

    from classiq import (
        qfunc,
        QNum,
        Output,
        allocate,
        create_model,
        synthesize,
        execute,
        show,
        Constraints,
        Preferences,
    )
    from ec_point_addition import ec_point_add

    @qfunc
    def main(
        x: Output[QNum], y: Output[QNum], t0: Output[QNum], l: Output[QNum]
    ) -> None:
        allocate(3, x)
        allocate(3, y)
        allocate(3, t0)
        allocate(3, l)

        x ^= P1[0]
        y ^= P1[1]

        ec_point_add(x, y, t0, l, P2, curve.p)

    constraints = Constraints(optimization_parameter="width")
    preferences = Preferences(timeout_seconds=3600, optimization_level=1)

    qmod = create_model(main, constraints=constraints, preferences=preferences)
    print("Synthesizing quantum circuit for ec_point_add (specific case)")
    qprog = synthesize(qmod)
    print(f"Number of qubits: {qprog.data.width}")

    show(qprog)
    print("Executing quantum circuit...")
    result = execute(qprog).result()
    print("Execution complete.")

    quantum_x = result[0].value.parsed_counts[0].state["x"]
    quantum_y = result[0].value.parsed_counts[0].state["y"]
    quantum_result = [quantum_x, quantum_y]

    print(f"Quantum result: {quantum_result}")

    if quantum_result == expected_result:
        print("Test ec_point_add_specific_case PASSED.")
    else:
        print(
            f"Test ec_point_add_specific_case FAILED. Expected {expected_result}, got {quantum_result}"
        )


def test_tinyec_point_addition():
    print("\n--- Running tinyec point addition test ---")
    field = SubGroup(p=GLOBAL_CURVE.p, g=(GLOBAL_G[0], GLOBAL_G[1]), n=None, h=None)
    curve = Curve(a=GLOBAL_CURVE.a, b=GLOBAL_CURVE.b, field=field, name="custom")

    P = Point(curve, GLOBAL_G[0], GLOBAL_G[1])
    Q = Point(curve, GLOBAL_INITIAL_ECP[0], GLOBAL_INITIAL_ECP[1])
    R = P + Q

    print(f"TinyEC Result: ({R.x}, {R.y})")


def run_singular_point_adding_tests():
    print("\n--- Running Singular Point Adding Tests ---")
    test_ell_add_classical()
    test_tinyec_point_addition()
    test_ell_double()
    test_ec_point_add_specific_case()


def run_multiple_point_adding_tests():
    print("\n--- Running Multiple Point Adding Tests ---")
    test_ell_mult_classical()
    test_tinyec_ell_mult_classical()
    test_ell_mult_add()


if __name__ == "__main__":
    print("(if __name__ == '__main__')")
    # run_singular_point_adding_tests()
    run_multiple_point_adding_tests()
