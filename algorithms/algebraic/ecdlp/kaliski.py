from classiq import (
    qfunc,
    QArray,
    QBit,
    QNum,
    Output,
    SWAP,
    X,
    CX,
    control,
    within_apply,
    bind,
    allocate,
    create_model,
    synthesize,
    show,
    inplace_add,
)
from modular_arithmetic import (
    modular_in_place_add,
    modular_in_place_subtract,
    shift_right,
    modular_in_place_double,
    modular_out_of_place_multiply,
    modular_in_place_negate,
)


@qfunc
def _swap_bits(x_array: QArray[QBit], y_array: QArray[QBit], size: int) -> None:
    for j in range(size):
        SWAP(x_array[j], y_array[j])


@qfunc
def swap_qnum(x: QNum, y: QNum) -> None:
    """
    Helper function to swap two quantum numbers by swapping their bits.
    Args:
        x (QNum): First quantum number
        y (QNum): Second quantum number
    """
    x_array = QArray[QBit]("x_array")
    y_array = QArray[QBit]("y_array")
    within_apply(
        within=lambda: (bind(x, x_array), bind(y, y_array)),
        apply=lambda: _swap_bits(x_array, y_array, x.size),
    )


@qfunc
def kaliski_quantum(v: QNum, p: int, m: QArray[QBit]) -> QNum:
    """
    Quantum implementation of the Kaliski algorithm using modular arithmetic primitives.
    Args:
        v (QNum): Quantum register for the value to process.
        p (int): Classical modulus.
        m (QArray[QBit]): Quantum array for the output bits.
    Returns:
        QNum: The processed quantum register.
    """
    n = p.bit_length()

    # Allocate quantum registers
    u = QNum("u", n)
    u |= p
    r = QNum("r", 2 * n)
    r |= 0
    s = QNum("s", 2 * n)
    s |= 1

    # Create QArrays for u and v bits (no allocation needed as they will be bound)
    u_array = QArray[QBit]("u_array")
    v_array = QArray[QBit]("v_array")
    s_array = QArray[QBit]("s_array")

    # Control qubits
    f = QBit("f")
    a = QBit("a")
    b = QBit("b")
    to_add = QBit("to_add")  # Added add qubit
    allocate(1, f)
    allocate(1, a)
    allocate(1, b)
    allocate(1, to_add)
    f ^= 1  # Set f to True

    # Main loop
    for i in range(2 * n):
        # STEP 0: Basic control structure
        control(f == 0, lambda: X(m[i]))
        CX(m[i], f)

        # STEP 1
        within_apply(
            within=lambda: (bind(u, u_array), bind(v, v_array)),
            apply=lambda: (
                # qrisp.mcx([f, u[0]], a, ctrl_state="10") equivalent
                control(f == 0, lambda: control(u_array[0] == 1, lambda: X(a))),
                # qrisp.mcx([f, a, v[0]], m[i], ctrl_state="100") equivalent
                # control([f == 0, a == 1, v_array[0] == 0], lambda: X(m[i])),
                control(
                    a == 1,
                    lambda: control(
                        f == 0, lambda: control(v_array[0] == 0, lambda: X(m[i]))
                    ),
                ),
                # qrisp.cx(a, b) equivalent
                CX(a, b),
                # qrisp.cx(m[i], b) equivalent
                CX(m[i], b),
            ),
        )

        # STEP 2
        # l = u > v
        # mcx([f, l, b], a, ctrl_state="110")
        control(u > v, lambda: control(f == 1, lambda: control(b == 0, lambda: X(a)))),

        # mcx([f, l, b], m[i], ctrl_state="110")
        control(
            u > v, lambda: control(f == 1, lambda: control(b == 0, lambda: X(m[i])))
        ),
        # l.uncompute()

        # STEP 3
        control(a == 1, lambda: (swap_qnum(u, v), swap_qnum(r, s)))

        # STEP 4
        # qrisp.mcx([f, b], add, ctrl_state="10") equivalent
        control(f == 1, lambda: control(b == 0, lambda: X(to_add)))

        # Control on add to perform modular addition of r to s (using modular_in_place_add and modular_in_place_subtract)
        control(to_add == 1, lambda: modular_in_place_add(r, s, p))
        control(to_add == 1, lambda: modular_in_place_subtract(r, s, p))

        # STEP 5 (using modular_in_place_add, modular_in_place_subtract, modular_in_place_add_constant, modular_in_place_subtract_constant, modular_in_place_double, modular_out_of_place_multiply, and modular_in_place_negate)
        control(f, lambda: control(b == 0, lambda: X(to_add)))
        CX(m[i], b)
        CX(a, b)
        within_apply(
            within=lambda: bind(v, v_array),
            apply=lambda: control(f, lambda: shift_right(v_array)),
        )
        modular_in_place_double(r, p)
        control(a == 1, lambda: (swap_qnum(u, v), swap_qnum(r, s)))

        within_apply(
            within=lambda: bind(s, s_array),
            apply=lambda: control(s_array[0], lambda: X(a)),
        )

    return v


@qfunc
def mock_kaliski_inverse(x: QNum) -> None:
    """
    Mock implementation of Kaliski algorithm for modular inverse modulo 7.
    For input x in range 1-6, computes x^(-1) mod 7.
    The modular inverses modulo 7 are:
    1^(-1) = 1 mod 7
    2^(-1) = 4 mod 7
    3^(-1) = 5 mod 7
    4^(-1) = 2 mod 7
    5^(-1) = 3 mod 7
    6^(-1) = 6 mod 7

    Args:
        x (QNum): Input quantum number (should be in range 1-6)
    """
    # Create a quantum register for the result
    result = QNum("result", 3)  # 3 bits enough for numbers 0-6
    allocate(3, result)

    # Use a series of controlled operations to set the correct inverse
    # For x = 1: result = 1
    control(x == 1, lambda: inplace_add(1, result))

    # For x = 2: result = 4
    control(x == 2, lambda: inplace_add(4, result))

    # For x = 3: result = 5
    control(x == 3, lambda: inplace_add(5, result))

    # For x = 4: result = 2
    control(x == 4, lambda: inplace_add(2, result))

    # For x = 5: result = 3
    control(x == 5, lambda: inplace_add(3, result))

    # For x = 6: result = 6
    control(x == 6, lambda: inplace_add(6, result))

    # Copy result back to x
    swap_qnum(x, result)
