---
search:
    boost: 2.434
---

# Automatic Registers Resolution

The Classiq engine supports the automatic merging of registers. This means that the quantum program opens with all the known registers already collapsed.
This feature completes the [manual](./quantum-program-visualization-tool/basic-version.md#merging-wires-into-registers) feature.

## Introduction

Each function contains information on its registers, which is mainly provided by the Classiq synthesis engine.
The information includes the register type (input, output, zero, auxiliary), the name, and the qubits it contains.

You can get information about the function's registers by clicking the function and looking in the **Information**
tab.

![Opening info tab](../../resources/registers_tab_better.gif)

## Wire Merging Criteria

Two or more wires can be merged only if:

1. The wire's source and destination are the same gates.
2. The wires operate on sequential qubits.
   For example, a register merges if the wires are between qubits 4, 5, and 6, but a register with wires on qubits
   1, 4, and 5 does not merge.

## Input Registers

Currently, the Classiq platform only supports input registers. To see if a register is an input register, look in the **Information** tab.

![Register info](../../resources/single_register_info.png)

If a gate's input register meets the merge criteria, wires are automatically merged when a quantum program loads.
Output registers may be supported in future Classiq versions.

Visual cues:

-   label - a label appears on the **right** of the wire next to the gate (left of the gate),
    containing the register's name
-   color - wires are color-coded as described below

![QuantumProgram](../../resources/circuit_with_registers.png)

If the engine cannot merge wires, it displays them separately.

![Disjoint case](../../resources/disjoint_wires.png)

Special registers:

-   Zero - A register that always contains the |0⟩ state appears with the color <span style="color:green">**green**</span>
-   Auxiliary - A register that is used as a helper to a function appears with the color <span style="color:red">**red**</span>

## Disclaimer

This is an experimental feature. Your feedback is appreciated.
