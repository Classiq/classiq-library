---
search:
    boost: 3.334
---

# Data Analysis and Graphs

The input to the analyzer tool is a quantum program in OpenQasm or Cirq format.
The analysis data and graphs can be accessed using Classiq's Python
SDK.
After synthesizing a quantum program, initialize the `Analyzer` class using the quantum program
returned from the synthesis process.

[comment]: DO_NOT_TEST

```python
from classiq import (
    qfunc,
    Analyzer,
    Output,
    QBit,
    allocate,
    synthesize,
    QuantumProgram,
    allocate,
)


@qfunc
def main(res: Output[QBit]) -> None:
    allocate(1, res)


qprog = synthesize(main)
analyzer = Analyzer(circuit=qprog)
```

## Graphs and Data

Quantum programs are more than just a beautiful image; they are meant to run on
real quantum hardware to solve and supply interesting and new answers.
The hardware analysis supplies two main insights.

### Available Devices

To perform hardware-aware analysis, you may want to know which devices are
available using the
Classiq Platform. You can get a list of the devices that are both available and
suit the quantum program (i.e., have a sufficient number of qubits).

[comment]: DO_NOT_TEST

```python
analyzer.get_available_devices()
```

This command returns the available devices of all the providers, in dictionary
format, where providers are
the keys, and lists of available devices are the values:

[comment]: DO_NOT_TEST

```python
{
    "IBM Quantum": [
        "almaden",
        "boeblingen",
        "brooklyn",
        "cairo",
        "cambridge",
        "guadalupe",
        "hanoi",
        "johannesburg",
        "kolkata",
        "manhattan",
        "melbourne",
        "montreal",
        "mumbai",
        "paris",
        "poughkeepsie",
        "rochester",
        "rueschlikon",
        "singapore",
        "sydney",
        "tokyo",
        "toronto",
        "washington",
    ],
    "Azure Quantum": ["ionq", "quantinuum"],
}
```

You can also request the devices of a specific provider:

[comment]: DO_NOT_TEST

```python
analyzer.get_available_devices(["IBM Quantum"])
```

### Hardware-Circuit Connection

The Hardware-Circuit Connection graph is a representation of a quantum program as
implemented on a specific (physical) quantum device. You
can interactively select hardware from hardware providers such as IBM Quantum,
Amazon Braket, and Microsoft Azure.
The analyzer compiles the quantum program for the selected hardware, allowing easy
inspection of which physical qubits will be used for execution on the device
and, in turn, modifying the quantum program if needed.
This information is important if you want to execute the quantum program on real quantum
hardware, so you can make modifications to the quantum program.

This graph is accessible from the SDK only if you install the `analyzer_sdk`
extension with the
`pip install classiq[analyzer_sdk]` command and use Jupyter as your coding
platform. Once the extension is installed, run this command:

[comment]: DO_NOT_TEST

```python
# Run inside jupyter
analyzer.plot_hardware_connectivity()
```

![connectivity](../../resources/HardwareConnectivity.png)

Alternatively, you can open the graph directly with a specific provider and
device:

[comment]: DO_NOT_TEST

```python
analyzer.plot_hardware_connectivity(provider="IBM Quantum", device="washington")
```

### Hardware Comparison Table

The hardware comparison table compares the transpiled quantum program on different
hardware backends. The table includes information about the quantum program's depth, number of
multi-qubit gates, and total number of gates.

[comment]: DO_NOT_TEST

```python
providers = ["IBM Quantum", "Azure Quantum", "Amazon Braket"]
analyzer = Analyzer(circuit=qprog)
analyzer.get_hardware_comparison_table(providers=providers)
analyzer.plot_hardware_comparison_table()
```

The `providers` variable is a list of providers ("IBM Quantum", "Azure Quantum",
and "Amazon Braket"), where the table includes only the backends of providers that
appear in the list, and the default is to use all the providers.
The table has the following form:

![comparison_table](../../resources/hardware_comparison_table.png)

Sort the table according to the table properties using the dropdown button on
the upper left of the table. ```

???+ note

    Using the default device/providers option (all) or comparing a large
    number of devices might take a long time, especially when analyzing large quantum programs.
    It is advised to compare a small number of devices when you are interested in analyzing large quantum programs.

???+ note

    The difference between the transpilation in the synthesis process and the comparison table data originates from the fact that the comparison table data is aware of the specific hardware and considers information such as the basis gates and connectivity.

<a name="schmidt rank">[1]</a> M. Van den Nest, W. Dur, G. Vidal, H. J. Briegel,
"Classical simulation versus universality in measurement-based quantum
computation",
Phys. Rev. A 75, 012337 (2007).

<a name="rank width Oum">[2]</a> S. Oum,
"Rank-width: Algorithmic and structural results", Lect. Notes Comput. Sci. 3787,
49 (2005).

<a name="rank width bound">[3]</a> S. Oum,
"Rank-width is less than or equal to branch-width", J. Graph Theory, 57 (3),
239-244 (2008).

<a name="Bodlaender report">[4]</a> Hans L. Bodlaender, "Discovering treewidth".
Institute of
Information and Computing Sciences, Utrecht University, Technical Report.
UU-CS-2005-018.
http://www.cs.uu.nl
