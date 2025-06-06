from classiq import *
from ec_point_addition import ell_double

authenticate(overwrite=True)


def test_ell_double():
    print("(test_ell_double)")
    from ec_point_addition import EllipticCurve

    print(
        "Running classical ell_double test (input (4,1) mod 7, curve a=5, b=4, p=7)..."
    )
    curve = EllipticCurve(
        p=7,
        a=1,
        b=3,
    )
    P = [4, 1]
    x, y = ell_double(P, curve)
    # Classical expected result (for doubling (4,1) on the curve y^2 = x^3 + 1x + 3 over F_7) is (6, 6)
    expected_x, expected_y = 6, 6
    print("Computed (x, y) = ({}, {})".format(x, y))
    print("Expected (x, y) = ({}, {})".format(expected_x, expected_y))
    assert x == expected_x, "ell_double computed x = {} (expected {})".format(
        x, expected_x
    )
    assert y == expected_y, "ell_double computed y = {} (expected {})".format(
        y, expected_y
    )
    print("Test PASSED.")


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
        allocate(3, k)
        # (For example, set k to a fixed classical value (e.g. 1) (using k ^= 1) so that ell_mult_add computes (1 * P) (mod p).)
        prepare_uniform_trimmed_state(5, k)
        # k ^= 3
        P = [4, 1]
        x ^= P[0]
        y ^= P[1]
        curve = EllipticCurve(p=7, a=1, b=3)
        ell_mult_add(x, y, t0, l, k, P, curve.p, curve.a, curve.b)

    constraints = Constraints(
        optimization_parameter="width",
    )  # Optimize for minimum width
    preferences = Preferences(timeout_seconds=3600, optimization_level=1)

    qmod = create_model(main, constraints=constraints, preferences=preferences)
    print(
        "Synthesizing quantum circuit for ell_mult_add (with P=[4,1], k=1, curve (p=7, a=1, b=3))..."
    )
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
    # (Optionally, you can also print (or assert) the classical expected result (for (1 * [4,1] (mod 7) on curve (p=7, a=1, b=3)) (if known).)
    # (For example, (1 * [4,1] (mod 7) (on curve (p=7, a=1, b=3)) is (classically) (4, 1).)
    # (You can then assert (or print) that the quantum (x,y) (from result[0].state) equals (4, 1).)
    quantum_x = result[0].value.parsed_counts[0].state["x"]
    quantum_y = result[0].value.parsed_counts[0].state["y"]
    quantum_res = (quantum_x, quantum_y)
    print("Quantum (x,y) (after ell_mult_add) (keys 'x', 'y'):", quantum_res)
    expected = (
        4,
        1,
    )  # (classical (1 * [4,1] (mod 7) (on curve (p=7, a=1, b=3)) (for example, (4, 1)) (if known).)
    print(
        "Expected (classical) (1 * [4,1] (mod 7) (on curve (p=7, a=1, b=3))):", expected
    )

    # assert quantum_res == expected, "Quantum (x,y) (after ell_mult_add) (keys 'x', 'y') = {} (expected {})".format(quantum_res, expected)
    # print("Test ell_mult_add PASSED.")


if __name__ == "__main__":
    print("(if __name__ == '__main__')")
    # test_ell_double()
    test_ell_mult_add()
