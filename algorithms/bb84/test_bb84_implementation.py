from classiq import *

@qfunc
def main() -> None:
    """
    Quantum circuit matching the specific gate pattern
    """
    q = QArray[QBit]()
    allocate(8, q)
    
    X(q[0])
    H(q[0])
    H(q[0])
    
    X(q[1])
    H(q[1])
    H(q[1])

    X(q[2])
    H(q[2])
    H(q[2])

    X(q[3])
    H(q[3])

    X(q[4])
    H(q[4])

    X(q[5])

    H(q[6])
    
    X(q[7])
    H(q[7])
    H(q[7])

def test_quantum_circuit():
    """
    Basic test for the quantum circuit
    """

    # Define and create the model
    qmod = create_model(main)
    if qmod is None:
        print("Test Failed: Model creation failed")
        return

    # Synthesize the circuit
    qprog = synthesize(qmod)
    if qprog is None:
        print("Test Failed: Synthesis failed")
        return

    # Execute the quantum program
    job = execute(qprog)
    if job is None:
        print("Test Failed: Execution failed")
        return

    # Get and print results
    results = job.get_sample_result().parsed_counts
    if results is None:
        print("Test Failed: No results returned")
        return

    print("Test Passed: Quantum circuit executed successfully")
    print("Results:", results)

if __name__ == "__main__":
    test_quantum_circuit()
