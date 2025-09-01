[![License](https://img.shields.io/github/license/Classiq/classiq-library)](https://opensource.org/license/mit)
[![Version](https://badge.fury.io/py/classiq.svg)](https://badge.fury.io/py/classiq)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/classiq)
[![Downloads](https://static.pepy.tech/badge/classiq)](https://pepy.tech/project/classiq)
[![DOI](https://zenodo.org/badge/DOI/10.48550/arXiv.2412.07372.svg)](https://doi.org/10.48550/arXiv.2412.07372)

<div align="center">
    <img src="README_resources/classiq-logo.svg" width="300" height="150">
</div>

# Classiq: High-Level Quantum Modeling Language

Classiq provides a powerful platform for **designing, optimizing, analyzing, and executing** quantum programs. This repository hosts a comprehensive collection of quantum functions, algorithms, applications, and tutorials built using the Classiq SDK and our native Qmod language.

Whether you're a researcher, developer, or student, Classiq helps you simplify complex quantum workflows and seamlessly transform quantum logic into optimized circuits by leveraging our **high-level functional design** approach. A user-friendly interface allows you to model, simulate, visualize, and execute quantum programs across various quantum hardware platforms.

<hr> <br>

<p align="center">
   &emsp;
   <a href="https://platform.classiq.io/">⚛️ Platform</a>
   &emsp;|&emsp;
   <a href="https://short.classiq.io/join-slack">👋 Join Slack</a>
   &emsp;|&emsp;
   <a href="https://docs.classiq.io/latest/">📖 Documentation</a>
   &emsp; | &emsp;
   <a href="https://docs.classiq.io/latest/classiq_101/">Getting Started</a>
   &emsp;
</p>

<hr>

# Installation

Working with Classiq's latest GUI requires no installations!
Just head over to [Classiq's platform](https://platform.classiq.io/) and follow the examples below over there :)

If you'd rather work programmatically using Python, Classiq also provides an SDK, which can be installed as follows:

```bash
pip install classiq
```

Alternatively, after cloning this repository, you may run

```bash
pip install --upgrade -r requirements.txt
```

## Running This Repository's Demos

This repository has 2 kinds of demos: `.qmod` and `.ipynb`.

The `.qmod` files are intended for usage with [Classiq's platform](https://platform.classiq.io/).
Upload those `.qmod` files into the [Synthesis tab](https://platform.classiq.io/synthesis)

The `.ipynb` files are intended to be viewed inside [JupyterLab](https://jupyter.org/) (or by programs that support such files, such as VSCode).

## Use the library with AI agents

See the [Classiq documentation](https://docs.classiq.io/latest/user-guide/ai/) to learn how to use the Classiq library with AI agents.

# Create Quantum Programs with Classiq

The simplest quantum circuit has 1 qubit and has a single `X` gate.

Using Classiq's SDK, it would look like this:

```python
from classiq import *

NUM_QUBITS = 1


@qfunc
def main(res: Output[QBit]):
    allocate(NUM_QUBITS, res)
    X(res)


quantum_program = synthesize(main)

show(quantum_program)

result = execute(quantum_program).result_value()
print(result.dataframe)
```

|     | res | count | probability | bitstring |
| --: | --: | ----: | ----------: | --------: |
|   0 |   1 |  2048 |           1 |         1 |

Let's unravel the code above:

1. `def main` : We define the logic of our quantum program. We'll expand on this point soon below.
2. `synthesize` : We synthesize the logic we defined into a Quantum Program. From a logical definition of quantum operations, into a series of quantum gates.
3. `execute` : Executing the quantum program. Can be executed on a physical quantum computer, or on simulations. Defaults to simulations.

## 1) Defining the Logic of Quantum Programs

The function above had 4 lines:

```python
@qfunc
def main(res: Output[QBit]):
    allocate(NUM_QUBITS, res)
    X(res)
```

The 1st line states that the function will be a quantum one. [Further documentation](https://docs.classiq.io/latest/qmod-reference/language-reference/functions/).

The 2nd line defines the type of the output. [Further examples on types](https://docs.classiq.io/latest/qmod-reference/language-reference/classical-types/)

The 3rd line allocates several qubits (in this example, only 1) in this quantum variable. [Further details on allocate](https://docs.classiq.io/latest/qmod-reference/language-reference/quantum-variables/)

The 4th line applies an `X` operator on the quantum variable. [Further details on quantum operators](https://docs.classiq.io/latest/qmod-reference/language-reference/operators/)

### More Examples

Initializing $\ket{-}$ state:

```python
@qfunc
def prep_minus(out: Output[QBit]) -> None:
    allocate(1, out)
    X(out)
    H(out)
```

A part of the Deutsch Jozsa algorithm (see the full algorithm [here](/algorithms/deutsch_jozsa/deutsch_jozsa.ipynb))

```python
@qfunc
def deutsch_jozsa(predicate: QCallable[QNum, QBit], x: QNum) -> None:
    hadamard_transform(x)
    my_oracle(predicate=lambda x, y: predicate(x, y), target=x)
    hadamard_transform(x)
```

A part of a QML encoder (see the full algorithm [here](/algorithms/qml/quantum_autoencoder/quantum_autoencoder.ipynb))

```python
@qfunc
def angle_encoding(exe_params: CArray[CReal], qbv: Output[QArray[QBit]]) -> None:
    allocate(exe_params.len, qbv)
    repeat(
        count=exe_params.len,
        iteration=lambda index: RY(pi * exe_params[index], qbv[index]),
    )
```

For more, see this repository :)

## 2) Synthesis : Logic to Quantum Program

This is where the magic happens.
Taking a the `main` function, which is a set of logical operations, and synthesizing it into physical qubits and the gates entangling them, is not an easy task.

Classiq's synthesis engine is able to optimize this process, whether by requiring the minimal amount of physical qubits, thus reusing as many qubits as possible, or by requiring minimal circuit width, thus lowering execution time and possible errors.

## 3) Execution

Classiq provides an easy-to-use way to execute quantum programs, and provides various insights of the execution results together with a familiar interface: `pandas.DataFrame`.

## Diagrams

1 diagram is worth a thousand words

```mermaid
flowchart
    IDEInput[<a href='https://platform.classiq.io/'>Classiq IDE</a>]

    SDKInput[<a href='https://docs.classiq.io/latest/sdk-reference/'>Classiq python SDK</a>]

    Model[<a href='https://docs.classiq.io/latest/qmod-reference/'>Quantum Model</a>]

    Synthesis[<a href='https://docs.classiq.io/latest/classiq_101/classiq_concepts/optimize/'>Synthesis Engine</a>]

    QuantumProgram[Quantum Program]

    Execution[<a href='https://docs.classiq.io/latest/classiq_101/classiq_concepts/execute/'>Execution</a>]

    Analyze[<a href='https://docs.classiq.io/latest/classiq_101/classiq_concepts/analyze/'>Analyze & Debug</a>]

    IBM[IBM]
    Amazon[Amazon Braket]
    Azure[Azure Quantum]
    Nvidia[Nvidia]


    IDEInput --> Model;
    SDKInput --> Model;
    Model --> Synthesis;
    Synthesis --> QuantumProgram;
    ExternalProgram <--> QuantumProgram;
    QuantumProgram --> Analyze;
    QuantumProgram --> Execution;
    Execution --> IBM
    Execution --> Amazon
    Execution --> Azure
    Execution --> Nvidia
```

# Build Your Own

With Classiq, you can build anything. Classiq provides a powerful modeling language to describe any quantum program, which can then be synthesized and executed on any hardware or simulator. Explore our [Documentation](https://docs.classiq.io/latest/) to learn everything.

## SDK : Classiq's Python Interface

### Example: Calculating 3+5 with Classiq

```python
from classiq import *


@qfunc
def prepare_3(var: Output[QArray]) -> None:
    allocate(2, var)
    X(var[0])
    X(var[1])


@qfunc
def prepare_5(var: Output[QArray]) -> None:
    allocate(3, var)
    X(var[0])
    X(var[2])


@qfunc
def main(res: Output[QNum]) -> None:
    a = QNum("a")
    b = QNum("b")

    prepare_3(a)
    prepare_5(b)

    res |= a + b  # 3+5 should be 8


quantum_program = synthesize(main)

show(quantum_program)

result = execute(quantum_program).result_value()
print(result.dataframe)
```

|     | res | count | probability | bitstring |
| --: | --: | ----: | ----------: | --------: |
|   0 |   8 |  2048 |           1 |      1000 |

For some pre-built state preparations, read [here](https://docs.classiq.io/latest/qmod-reference/api-reference/functions/open_library/state_preparation/?h=state)

## IDE : Classiq's Platform

Every example found in this repository can also be accessed via [Classiq's platform](https://platform.classiq.io/), in the [`model`](https://platform.classiq.io/dsl-synthesis) tab, under the same folder structure.

Additionally, one may write their own model in the model editor (highlighted in green) or upload his own model (highlighted in red)

![writing_models.png](README_resources/writing_models.png)

### Example: 3+5 with Classiq

1. Create a model (paste in the [`model`](https://platform.classiq.io/dsl-synthesis) tab)

```
qfunc get_3(output x: qbit[]){
 allocate(2,x);
 X(x[0]);
 X(x[1]);
}

qfunc get_5(output x: qbit[]){
 allocate(3,x);
 X(x[0]);
 X(x[2]);
}

qfunc main(output res: qnum){
 a: qnum;
 b: qnum;
 get_3(a);
 get_5(b);
 res = a + b;
}
```

2. Press Synthesize:
<center>

![Model_Screenshot_3_plus_5.png](README_resources/Model_Screenshot_3_plus_5.png)

</center>

3. Press Execute:
<center>

![Program_Screenshot_3_plus_5.png](README_resources/Program_Screenshot_3_plus_5.png)

</center>

4. Press Run:
<center>

![Execution_Screenshot_3_plus_5.png](README_resources/Execution_Screenshot_3_plus_5.png)

</center>

5. View Results:
<center>

![Jobs_Screenshot_3_plus_5.png](README_resources/Jobs_Screenshot_3_plus_5.png)

</center>

<hr>

Have questions? Feedback? Something to share?
Welcome to join our open [Slack Community](https://short.classiq.io/join-slack)
