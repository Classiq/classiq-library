# Support

Welcome to the Classiq Support Center. This page is designed to help you quickly resolve common issues and get additional support if needed.

---

## Frequently Asked Questions (FAQs)

### Getting Started

<!-- prettier-ignore-start -->
??? note "What is Classiq?"
    Classiq is quantum-computing software that enables the design, optimization, analysis, and execution of quantum algorithms. Check out how to get started [here](/latest/getting-started/).

??? note "I'm new to the Classiq Platform—what are my first steps?"
    - Start with [Registration and Installation](/latest/getting-started/registration_installations/) to get access to the Classiq Platform.
    - [The Classiq Tutorial](/latest/getting-started/classiq_tutorial/) will help with your first steps in coding.
    - When you feel confident, try some of our [real-world applications](/latest/explore/applications/).

??? note "Can I execute algorithms on quantum computers using Classiq?"
    Yes! With Classiq, you can run quantum algorithms on the quantum computers you have access to. Check out our list of [quantum providers](/latest/sdk-reference/providers/).
<!-- prettier-ignore-end -->

### Technical Questions

<!-- prettier-ignore-start -->
??? note "How can I fix `ClassiqAuthenticationError: Request to Auth0 failed with error code 403`?"
    This error arises when your authentication credentials are denied. Try overriding your authentication credentials by executing `authenticate(overwrite=True)`.

??? note "My Classiq Studio cannot reconnect"
    If you’re experiencing failed attempts to reconnect to Classiq Studio or long loading times, please try closing and reopening your web browser.

??? note "Example notebooks in Classiq Studio aren’t working"
    Some example notebooks (e.g., chemistry) require additional packages in Classiq Studio. First, try:

    ```bash
    pip install "classiq[chemistry]"
    ```

    If it still doesn’t work, reset the virtual environment by running:

    ```bash
    reset-user-env
    ```

    If none of these options work, reach out to us on the [Community Slack](https://short.classiq.io/join-slack).

??? note "How do I import a QASM file using the Python SDK?"
    Use `quantum_program_from_qasm()`.
<!-- prettier-ignore-end -->

### Contributing to the Library

<!-- prettier-ignore-start -->
??? note "How can I contribute to the Classiq Library?"
    You can find contribution guidelines on [this page](https://github.com/Classiq/classiq-library/blob/main/CONTRIBUTING.md).
<!-- prettier-ignore-end -->

### Designing Quantum Models

<!-- prettier-ignore-start -->
??? note "How do I define an observable?"
    In Classiq, you can define any observable as a linear combination of Pauli strings. To measure a set of observables from a quantum program, see [Execution Session](/latest/user-guide/execution/ExecutionSession/) and the [Execution Tutorial](/latest/explore/tutorials/basic_tutorials/the_classiq_tutorial/execution_tutorial_part2/).

??? note "How can I transform a circuit with many gates into a shallower circuit using more qubits?"
    You can synthesize the quantum circuit using `Constraints`. See [Quantum Program Constraints](/latest/user-guide/synthesis/constraints/).

??? note "How do I target a hardware’s native gate set?"
    You can synthesize the quantum program using hardware-aware synthesis. See [Hardware-Aware Synthesis](/latest/user-guide/synthesis/hardware-aware-synthesis/).

??? note "How do I create a multi-control, multi-target gate?"
    Using `control`, you can define multi-qubit controls and gates. You can also use `if_` for classical control of quantum gates. See [Classical Control Flow](/latest/qmod-reference/language-reference/statements/classical-control-flow/).

??? note "How do I use controlled operations on multiple qubits instead of QArrays?"
    There are two ways to work around this: either bind the qubits you want to a QArray (see [bind](/latest/qmod-reference/language-reference/statements/bind/)) or slice the QArrays (see [Path Operators](/latest/qmod-reference/language-reference/statements/numeric-assignment/#relational-operators)).

??? note "How do I apply a single-qubit gate to multiple qubits?"
    Use the `apply_to_all` function. See [Utility functions](/latest/qmod-reference/api-reference/functions/open_library/utility_functions/).

??? note "How can I uncompute a qubit?"
    You can use the `free()` function. For more information, see [Uncomputation](/latest/qmod-reference/language-reference/uncomputation/).

??? note "How do I obtain the width and depth of my quantum program?"
    Use `qprog.data.width` and `qprog.transpiled_circuit.depth`.
<!-- prettier-ignore-end -->

### Execution

<!-- prettier-ignore-start -->
??? note "How do I execute a quantum program on hardware?"
    Use `ExecutionPreferences` and set the backend appropriately. The [Execution Tutorial](/latest/explore/tutorials/basic_tutorials/the_classiq_tutorial/execution_tutorial/) shows this step by step.

??? note "How do I convert a combinatorial optimization problem into a problem Hamiltonian?"
    In Qmod, it is possible to use Pyomo to formulate the optimization problem. See [Problem Formulation](https://docs.classiq.io/latest/user-guide/applications/optimization/problem-formulation/).

??? note "How can I change the number of shots when executing a quantum program?"
    Use `ExecutionPreferences` and set the number of shots. See the [Execution Tutorial](/latest/explore/tutorials/basic_tutorials/the_classiq_tutorial/execution_tutorial/).

??? note "How do I run a VQA on IBM hardware using `ExecutionSession`?"
    After defining the quantum program, use `ExecutionSession.minimize()` or `ExecutionSession.estimate()` for VQAs. See [Execution Tutorial 2: Expectation Values and Parameterized Quantum Programs](/latest/explore/tutorials/basic_tutorials/the_classiq_tutorial/execution_tutorial_part2/).
<!-- prettier-ignore-end -->

---

## Need More Help?

If your question is not answered here, please:

-   Reach out in the `#support-and-questions` channel on [our community Slack](https://short.classiq.io/join-slack).
-   For additional assistance, to report a bug, or to request a feature, submit a ticket via our [Support Center](https://classiq-community.freshdesk.com/support/home).
