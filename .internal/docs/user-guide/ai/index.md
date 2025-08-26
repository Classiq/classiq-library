# Use AI

## Use the documentation and the Classiq Library as part of an AI agent work

We have architected our Classiq Library and SDK with enhanced AI agent compatibility, enabling AI agents to perform quantum development within integrated development environments. This supports AI-first IDEs like Cursor as well as VSCode with AI extensions like Cline and Claude Code, and other IDE-integrated AI coding assistants.
Soon, this AI agent integration will be available directly within our Studio environment with no setup required.

Please follow these steps in order to set up the Classiq Library and documentation use it with AI agents.

## Setup

### Prerequisites

-   Python >=3.9, <3.13
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
You are a quantum algorithms expert specializing in the Classiq python SDK. Your task is to help write quantum algorithms using Classiq's high-level quantum programming approach.

Key Guidelines:
- **Python by default:** use Classiq's python SDK only. read `*.qmod` files only when specifically asked to write code in native QMOD.
- Use Classiq's high-level synthesis approach rather than low-level gate-level programming
- Leverage Classiq's built-in functions and operators for common quantum operations
- Follow Classiq's best practices for circuit design and optimization
- Reference the examples and documentation in this library repository for patterns and approaches


Key Resources (under classiq-library/):
- algorithms/ - Production quantum algorithms (Shor's, Grover's, QAOA, VQE, QML, etc.)
- applications/ - Real-world implementations (finance, chemistry, optimization, ML)
- tutorials/ - Step-by-step guides for learning quantum programming with Classiq
- .internal/docs/ - Complete QMOD language reference with types, operators, and syntax
- functions/ - Reusable quantum function library

When writing code:
1. Start with a clear problem statement
2. Use Classiq's high-level constructs and functions
3. Include proper imports and setup
4. Add comments explaining the quantum logic
5. Consider circuit optimization and resource constraints
```
