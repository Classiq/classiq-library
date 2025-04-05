from classiq import *

@qfunc
def main(qba: Output[QArray[QBit]]) -> None:
    """
    Implements the quantum part of BB84 protocol with 8 qubits.
    """

    q = QArray[QBit]()
    allocate(8, q)

    X(q[0])
    X(q[2])
    X(q[3])
    X(q[5])
    H(q[1])
    H(q[2])
    H(q[4])
    H(q[7])
    H(q[0])
    H(q[1])
    H(q[4])
    H(q[6])
    H(q[7])
    
    allocate(8, qba)
    for i in range(8):
        qba[i] = q[i]
        

def test_quantum_circuit():
    """
    Test the BB84 quantum circuit implementation from the notebook
    """

    # Create the quantum model using the updated main function
    qmod = create_model(main)
    if qmod is None:
        print("Test Failed: Model creation failed")
        return

    # Synthesize the quantum program
    qprog = synthesize(qmod)
    if qprog is None:
        print("Test Failed: Synthesis failed")
        return

    # Execute the quantum program
    job = execute(qprog)
    if job is None:
        print("Test Failed: Execution failed")
        return

    # Fetch and print parsed results
    results = job.get_sample_result().parsed_counts
    if not results:
        print("Test Failed: No results returned")
        return

    print("Test Passed: BB84 quantum circuit executed successfully")
    print("Results:", results)

if __name__ == "__main__":
    test_quantum_circuit()
