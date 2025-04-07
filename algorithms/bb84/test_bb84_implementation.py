from classiq import *

from tests.utils_for_testbook import (
    validate_quantum_model,        
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient

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

@wrap_testbook(
    "circuit for implementing bb84 quantum key distribution protocol",
    timeout_seconds=100,  
)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a hybrid classical quantum neural network.
    The test verifies that the pre-trained model is indeed well trained.
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
    # test models
    validate_quantum_model(tb.ref("qmod"))
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
    pass

