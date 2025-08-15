"""
Quantum Modular Arithmetic Functions for Elliptic Curve Cryptography

Based on: Martin Roetteler, Michael Naehrig, Krysta M. Svore, and Kristin Lauter. "Quantum resource estimates for computing elliptic curve   discrete logarithms." *arXiv preprint arXiv:1706.06752* (2017).

"""

from classiq import *
from classiq.qmod.symbolic import subscript


# Basic Modular Arithmetic Operations


@qfunc
def modular_in_place_add(x: Const[QNum], y: Permutable[QNum], modulus: int) -> None:
    """
    Performs the transformation |x>|y> → |x>|(x + y) mod modulus>.
    """
    # Use a carry qubit to detect overflow
    carry = QBit()
    allocate(carry)

    # Create temporary register that combines y and carry
    res_and_carry = QNum("res_and_carry", y.size + 1, SIGNED, 0)

    # Compute-uncompute pattern for reversible arithmetic
    within_apply(
        # COMPUTE: Bind y and carry into combined register
        lambda: bind([y, carry], res_and_carry),
        # APPLY: Perform modular arithmetic operations
        lambda: (
            inplace_add(x, res_and_carry),  # Add x to the combined register
            inplace_add(-modulus, res_and_carry),  # Subtract modulus to check overflow
        ),
    )
    # UNCOMPUTE: y and carry are automatically separated

    # If carry is set (negative result), add modulus back to y
    control(carry, lambda: inplace_add(modulus, y))

    # Update carry qubit based on comparison (y >= x after operation)
    carry ^= y >= x

    # Clean up auxiliary qubit
    free(carry)


@qfunc
def bitwise_negation(arr: Permutable[QArray[QBit]]) -> None:
    """
    Applies an X gate (bitwise NOT) to each qubit in the quantum array `arr`.
    """
    apply_to_all(X, arr)


@qfunc
def modular_in_place_negate(x: Permutable[QNum], modulus: int) -> None:
    """
    Performs the transformation |x> → |(-x) mod modulus>.
    """
    n = x.size
    neg_modulus = 2**n - modulus - 1

    is_all_zeros = QBit()
    allocate(is_all_zeros)

    # Test if the input is all-zeros
    is_all_zeros ^= x == 0

    # If all-zeros, then put the modulus in x
    control(is_all_zeros, lambda: inplace_add(modulus, x))

    # Add neg_modulus to x
    inplace_add(neg_modulus, x)

    # If x=0, then we have neg_modulus + modulus = all ones
    is_all_zeros ^= x == (2**x.size - 1)

    # Bitwise negation: set x to (neg_modulus + x)'
    bitwise_negation(x)

    free(is_all_zeros)


@qfunc
def modular_in_place_subtract(
    x: Const[QNum], y: Permutable[QNum], modulus: int
) -> None:
    """
    Performs the transformation |x>|y> → |x>|(x - y) mod modulus>.
    """
    # Compute -y mod modulus in-place on y
    modular_in_place_negate(y, modulus)
    # Compute x + (-y) mod modulus in-place on y
    modular_in_place_add(x, y, modulus)


# Constant Operations


@qfunc
def modular_in_place_add_constant(
    x: Permutable[QNum], constant: int, modulus: int
) -> None:
    """
    Performs the transformation |x> → |(x + constant) mod modulus>.
    """
    # Allocate a single carry qubit
    carry = QBit()
    allocate(carry)

    # Create and allocate temporary register to hold x + carry
    temp = QNum("temp", x.size + 1, SIGNED, 0)

    # Bind x and carry into temp for addition
    within_apply(
        lambda: bind([x, carry], temp),
        lambda: (
            # Add constant to temp
            inplace_add(constant, temp),
            # Add -modulus to temp to check for overflow
            inplace_add(-modulus, temp),
        ),
    )

    # If carry is set, we need to add modulus back
    control(carry, lambda: inplace_add(modulus, x))
    control(x >= constant, lambda: X(carry))

    # Free the temporary registers
    free(carry)


# Doubling and Shifting


@qfunc
def shift_left(reg: Permutable[QArray[QBit]]) -> None:
    """
    Performs a left shift on the quantum register array `reg` using SWAP gates.
    """
    n = reg.size
    # Shift bits left using SWAP gates
    for i in reversed(range(1, n)):
        SWAP(reg[i], reg[i - 1])


@qfunc
def modular_in_place_double(x: Permutable[QNum], modulus: int) -> None:
    """
    Performs the transformation |x> → |(2x) mod modulus>.
    """
    carry = QBit()
    allocate(carry)
    res_and_carry = QNum("res_and_carry", x.size + 1, SIGNED, 0)

    within_apply(
        lambda: bind([x, carry], res_and_carry),
        lambda: (
            shift_left(res_and_carry),  # holds 2*x
            inplace_add(-modulus, res_and_carry),
        ),
    )

    control(carry, lambda: inplace_add(modulus, x))

    # Update carry based on LSB of original x
    lsb = QNum("lsb", 1)
    rest = QNum("rest", x.size - 1)
    within_apply(
        lambda: bind(x, [lsb, rest]),
        lambda: (
            X(lsb),
            CX(lsb, carry),
            X(lsb),
        ),
    )
    free(carry)


# Multiplication Operations


@qfunc
def modular_out_of_place_multiply(
    x: Const[QArray[QBit]],
    y: Const[QArray[QBit]],
    z: Permutable[QArray[QBit]],
    modulus: int,
) -> None:
    """
    Performs the transformation |x>|y>|0> → |x>|y>|(x * y) mod modulus>.
    """
    n = x.size
    for idx in reversed(range(n)):
        # If x[idx] = 1, add y to z (controlled addition)
        control(x[idx], lambda: modular_in_place_add(y, z, modulus))
        # Double z for next iteration (except for the last iteration)
        if idx != 0:
            modular_in_place_double(z, modulus)


@qfunc
def modular_out_of_place_square(
    x: Const[QArray[QBit]], z: Permutable[QArray[QBit]], p: int
) -> None:
    """
    Performs the transformation |x>|0> → |x>|(x^2) mod p>.
    """
    n = x.size
    assert z.size == n, "Output register z must have the same number of qubits as x"
    anc = QBit()
    # Process bits from MSB-1 down to 1
    for i in range(n - 1, 0, -1):
        within_apply(
            lambda: assign(x[i], anc),
            lambda: control(anc, lambda: modular_in_place_add(x, z, p)),
        )
        modular_in_place_double(z, p)
    # Process LSB (bit 0) - no doubling after this
    within_apply(
        lambda: assign(x[0], anc),
        lambda: control(anc, lambda: modular_in_place_add(x, z, p)),
    )


# Modular Inverse (Mock Implementation for Educational Purposes)


@qfunc
def _set_value(reg: Permutable[QNum], value: int) -> None:
    """Helper function to set a value in a quantum register."""
    reg ^= value


@qfunc
def mock_inverse_modulus(
    x: Const[QNum], result: Permutable[QNum], modulus: int
) -> None:
    """
    Performs the transformation |x>|0> → |x>|x^(-1) mod 7> for x in 1..6.
    This is a mock implementation implemented with a lookup table approach.
    """
    result ^= subscript([0, 1, 4, 5, 2, 3, 6, 0], x)


@qfunc
def mock_inverse_modulus_7(x: Const[QNum], result: Permutable[QNum]) -> None:
    """
    Performs the transformation |x>|0> → |x>|x^(-1) mod 7> for x in 1..6.
    This is a mock implementation implemented with a lookup table approach.
    """
    # Use a series of controlled operations to set the correct inverse
    # For x = 1: result = 1
    control(x == 1, lambda: _set_value(result, 1))

    # For x = 2: result = 4
    control(x == 2, lambda: _set_value(result, 4))

    # For x = 3: result = 5
    control(x == 3, lambda: _set_value(result, 5))

    # For x = 4: result = 2
    control(x == 4, lambda: _set_value(result, 2))

    # For x = 5: result = 3
    control(x == 5, lambda: _set_value(result, 3))

    # For x = 6: result = 6
    control(x == 6, lambda: _set_value(result, 6))
