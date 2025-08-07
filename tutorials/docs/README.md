## Setup

### Prerequisites

-   Python >=3.8, <3.12
-   Git
-   An IDE of your choice (VS Code, Cursor, etc.)

### Installation Steps

1. **Clone the Library Repository**

    ```bash
    git clone https://github.com/Classiq/classiq-library.git
    cd classiq-library
    ```

2. **Install Classiq SDK**

    ```bash
    pip install classiq
    ```

3. **Verify Installation**

    ```bash
    python -c "import classiq; print('Classiq SDK installed successfully!')"
    ```

### IDE Setup

1. **Open the Repository in Your IDE**

    - Open your preferred IDE
    - Select "Open Folder" or "Open Workspace"
    - Navigate to and select the `classiq-library` directory

2. **Configure Python Environment**
    - Ensure your IDE is using the Python environment where you installed Classiq
    - Set up any virtual environment if desired

## AI Agent Initial Prompt

When working with AI agents to write quantum code using Classiq, use this initial prompt:

```
You are a quantum computing expert specializing in the Classiq SDK. Your task is to help write quantum algorithms and circuits using Classiq's high-level quantum programming approach.

Key Guidelines:
- Use Classiq's high-level synthesis approach rather than low-level gate-level programming
- Leverage Classiq's built-in functions and operators for common quantum operations
- Follow Classiq's best practices for circuit design and optimization
- Reference the examples and documentation in this library repository for patterns and approaches

Key Resources:
- /algorithms/ - Production quantum algorithms (Shor's, Grover's, QAOA, VQE, QML, etc.)
- /applications/ - Real-world implementations (finance, chemistry, optimization, ML)
- /tutorials/ - Step-by-step guides for learning quantum programming with Classiq
- /docs/ - Complete QMOD language reference with types, operators, and syntax
- /functions/ - Reusable quantum function library

When writing code:
1. Start with a clear problem statement
2. Use Classiq's high-level constructs and functions
3. Include proper imports and setup
4. Add comments explaining the quantum logic
5. Consider circuit optimization and resource constraints
```
