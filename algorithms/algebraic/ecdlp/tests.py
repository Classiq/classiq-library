from classiq import (
    qfunc,
    QNum,
    QBit,
    Output,
    allocate,
    create_model,
    synthesize,
    show,
    execute,
    within_apply,
    bind,
    X,
    control,
    prepare_uniform_trimmed_state,
    QArray,
    Constraints,
)
from classiq.qmod import SIGNED
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

MODULUS = 5


def run_quantum_test(qmod, test_name: str) -> None:
    """
    Helper function to run a quantum test and print results.
    """
    qprog = synthesize(qmod)
    # Uncomment to see the circuit
    show(qprog)

    result = execute(qprog).result()
    print(f"\n{test_name} Test Results:")
    print("Quantum Result:", result[0].value.parsed_counts)
    return result[0].value.parsed_counts


def verify_modular_operation(
    quantum_result: list, expected_result: int, operation: str, result_key: str = "x"
) -> bool:
    """
    Verifies that the quantum result (for the variable changed in place or computed out of place) matches the expected classical value.
    For example, for modular_in_place_add (or modular_in_place_subtract) the quantum result (quantum_result[0].state["x"]) is compared with expected_result.
    For modular_out_of_place_multiply, the quantum result (quantum_result[0].state["z"]) is compared.
    (For modular_in_place_add_constant, modular_in_place_subtract_constant, modular_in_place_double, and modular_in_place_negate, the quantum result (quantum_result[0].state["x"]) is compared.)
    Args:
        quantum_result: A list (of length 1) of SampledState objects (for example, [SampledState(state={"x": 0, "y": 2, "y_copy": 2}, shots=1)]).
        expected_result: The classical (expected) value (for example, (3 + 2) mod 5 = 0).
        operation: A string describing the operation (for example, "(3 + 2) mod 5").
        result_key: (Optional) The key (for example, "x" or "z") in quantum_result[0].state to compare. Default is "x".
    Returns:
        bool: True if quantum_result[0].state[result_key] equals expected_result, False otherwise.
    """
    quantum_value = quantum_result[0].state[result_key]
    print(f"Operation: {operation}")
    print(f"Quantum result (key '{result_key}'): {quantum_value}")
    print(f"Expected (classical) value: {expected_result}")
    is_correct = quantum_value == expected_result
    print(f"Test {'PASSED' if is_correct else 'FAILED'}")
    return is_correct


def run_modular_add_test():
    print("\nRunning Modular Addition Test (using modular_in_place_add)...")

    @qfunc
    def main(x: Output[QNum], y: Output[QNum], y_copy: Output[QNum]) -> None:
        allocate(3, x)
        allocate(3, y)
        x ^= 3  # x = 3
        y ^= 2  # y = 2
        y_copy |= y  # y_copy is allocated here
        modular_in_place_add(x, y, MODULUS)  # y becomes (3 + 2) mod 5 = 0

    qmod = create_model(main)
    result = run_quantum_test(qmod, "Modular Addition")
    expected = (3 + 2) % MODULUS  # Classical calculation for fixed inputs
    verify_modular_operation(result, expected, "(3 + 2) mod 5", result_key="y")


def run_modular_subtract_test():
    print("\nRunning Modular Subtraction Test (using modular_in_place_subtract)...")

    @qfunc
    def main(x: Output[QNum], y: Output[QNum], y_copy: Output[QNum]) -> None:
        allocate(3, x)
        allocate(3, y)
        x ^= 4  # x = 4
        y ^= 2  # y = 2
        y_copy |= y  # y_copy is allocated here
        modular_in_place_subtract(x, y, MODULUS)  # y becomes (4 - 2) mod 5 = 2

    qmod = create_model(main)
    result = run_quantum_test(qmod, "Modular Subtraction")
    expected = (4 - 2) % MODULUS  # Classical calculation for fixed inputs
    verify_modular_operation(result, expected, "(4 - 2) mod 5", result_key="y")


def run_modular_add_constant_test():
    print(
        "\nRunning Modular Addition with Constant Test (using modular_in_place_add_constant)..."
    )

    @qfunc
    def main(x: Output[QNum], x_copy: Output[QNum]) -> None:
        allocate(3, x)
        # Set fixed input value
        x ^= 2  # x = 2
        x_copy |= x  # Copy original x
        constant = 3  # local int var
        modular_in_place_add_constant(
            x, constant, MODULUS
        )  # x becomes (2 + 3) mod 5 = 0

    qmod = create_model(main)
    result = run_quantum_test(qmod, "Modular Addition with Constant")
    expected = (2 + 3) % MODULUS  # Classical calculation for fixed input
    verify_modular_operation(result, expected, "(2 + 3) mod 5")


def run_modular_subtract_constant_test():
    print(
        "\nRunning Modular Subtraction with Constant Test (using modular_in_place_subtract_constant)..."
    )

    @qfunc
    def main(x: Output[QNum], x_copy: Output[QNum]) -> None:
        allocate(3, x)
        # Set fixed input value
        x ^= 4  # x = 4
        x_copy |= x  # Copy original x
        constant = 2  # local int var
        modular_in_place_subtract_constant(
            x, constant, MODULUS
        )  # x becomes (4 - 2) mod 5 = 2

    qmod = create_model(main)
    result = run_quantum_test(qmod, "Modular Subtraction with Constant")
    expected = (4 - 2) % MODULUS  # Classical calculation for fixed input
    verify_modular_operation(result, expected, "(4 - 2) mod 5")


def run_modular_double_test():
    print("\nRunning Modular Doubling Test (using modular_in_place_double)...")

    @qfunc
    def main(x: Output[QNum], x_copy: Output[QNum]) -> None:
        allocate(3, x)
        # Set fixed input value
        x ^= 3  # x = 3
        x_copy |= x  # Copy original x
        modular_in_place_double(x, MODULUS)  # x becomes (2 * 3) mod 5 = 1

    qmod = create_model(main)
    result = run_quantum_test(qmod, "Modular Doubling")
    expected = (2 * 3) % MODULUS  # Classical calculation for fixed input
    verify_modular_operation(result, expected, "(2 * 3) mod 5")


def run_modular_multiply_test():
    print(
        "\nRunning Modular Multiplication Test (using modular_out_of_place_multiply)..."
    )

    @qfunc
    def main(x: Output[QNum], y: Output[QNum], z: Output[QNum]) -> None:
        allocate(3, x)
        allocate(3, y)
        allocate(3, z)
        # Set fixed input values
        x ^= 3  # x = 3
        y ^= 4  # y = 4
        modular_out_of_place_multiply(x, y, z, MODULUS)  # z becomes (3 * 4) mod 5 = 2

    qmod = create_model(main)
    result = run_quantum_test(qmod, "Modular Multiplication")
    expected = (3 * 4) % MODULUS  # Classical calculation for fixed inputs
    verify_modular_operation(result, expected, "(3 * 4) mod 5", result_key="z")


def run_modular_negate_test():
    print("\nRunning Modular Negation Test (using modular_in_place_negate)...")

    @qfunc
    def main(x: Output[QNum], x_copy: Output[QNum]) -> None:
        allocate(3, x)
        x ^= 2  # x = 2
        x_copy |= x  # Copy original x
        modular_in_place_negate(x, MODULUS)  # x becomes (-2) mod 5 = 3

    qmod = create_model(main)
    result = run_quantum_test(qmod, "Modular Negation")
    expected = (-2) % MODULUS  # Classical calculation for fixed input
    verify_modular_operation(result, expected, "(-2) mod 5")


def run_modular_square_test():
    print("\nRunning Modular Square Test (using modular_square)...")

    @qfunc
    def main(x: Output[QNum], z: Output[QNum]) -> None:
        allocate(3, x)
        allocate(3, z)
        x ^= 4  # x = 4
        modular_square(x, z, MODULUS)  # z becomes (4 * 4) mod 5 = 1

    qmod = create_model(main, constraints=Constraints(optimization_parameter="width"))
    result = run_quantum_test(qmod, "Modular Square")
    expected = (4 * 4) % MODULUS  # Classical calculation for fixed input
    verify_modular_operation(result, expected, "(4 * 4) mod 5", result_key="z")


def run_mock_kaliski_modulus_7_test():
    """
    A mock test (for Kaliski) that initializes a quantum variable (x) and then calls mock_kaliski_inverse_modulus_7 (from kaliski.py)
    to compute the inverse of x modulo 7. For example, if x=2, then (2)^(-1) mod 7 = 4.
    """
    print("\nRunning Mock Kaliski (Modulus 7) Test...")

    @qfunc
    def main(x: Output[QNum], result: Output[QNum]) -> None:
        allocate(3, x)
        allocate(3, result)
        x ^= 2  # x = 2 (fixed input)
        mock_kaliski_inverse_modulus_7(x, result)  # (2)^(-1) mod 7 = 4

    qmod = create_model(main)
    result = run_quantum_test(qmod, "Mock Kaliski (Modulus 7)")
    expected = pow(2, -1, 7)  # Classical calculation: (2)^(-1) mod 7 = 4
    verify_modular_operation(result, expected, "(2)^(-1) mod 7", result_key="result")


def run_all_tests():
    """
    Runs all modular arithmetic tests.
    """
    print("Running All Modular Arithmetic Tests...")
    run_modular_add_test()
    run_modular_subtract_test()
    run_modular_add_constant_test()
    run_modular_subtract_constant_test()
    run_modular_double_test()
    run_modular_multiply_test()
    run_modular_negate_test()
    run_modular_square_test()
    run_mock_kaliski_modulus_7_test()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Run specific test based on command line argument
        test_name = sys.argv[1].lower()
        if test_name == "add":
            run_modular_add_test()
        elif test_name == "subtract":
            run_modular_subtract_test()
        elif test_name == "add_constant":
            run_modular_add_constant_test()
        elif test_name == "subtract_constant":
            run_modular_subtract_constant_test()
        elif test_name == "double":
            run_modular_double_test()
        elif test_name == "multiply":
            run_modular_multiply_test()
        elif test_name == "negate":
            run_modular_negate_test()
        elif test_name == "square":
            run_modular_square_test()
        elif test_name == "mock_kaliski":
            run_mock_kaliski_modulus_7_test()
        else:
            print(f"Unknown test: {test_name}")
            print(
                "Available tests: add, subtract, add_constant, subtract_constant, double, multiply, negate, square, mock_kaliski"
            )
    else:
        # Run all tests if no specific test is requested
        # run_mock_kaliski_modulus_7_test()
        run_all_tests()
