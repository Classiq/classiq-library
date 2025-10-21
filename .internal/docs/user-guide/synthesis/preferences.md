---
search:
    boost: 3.084
---

# Synthesis Preferences

You can modify these synthesis process preferences:

-   [Output formats](#output-formats)
-   [Hardware-aware settings](hardware-aware-synthesis.md)
-   [Timeouts](#timeouts)
-   [Optimization level](#optimization-level)
-   [Toggling quantum program visualization support](#toggling-circuit-visualization-support)

In this example, the chosen output format includes both Q# and OpenQASM.
Specific basis gates are selected for the synthesis:
controlled not, controlled phase, square root of not, Z-rotation,
and not gates.

=== "SDK"

```python
from classiq import (
    qfunc,
    Output,
    QBit,
    allocate,
    synthesize,
    show,
    CustomHardwareSettings,
    Preferences,
    QuantumProgram,
    allocate,
)


@qfunc
def main(res: Output[QBit]) -> None:
    allocate(1, res)


custom_hardware_settings = CustomHardwareSettings(
    basis_gates=["cx", "cp", "sx", "rz", "x"]
)
preferences = Preferences(
    output_format=["qasm", "qsharp"], custom_hardware_settings=custom_hardware_settings
)

qprog = synthesize(main, preferences=preferences)
show(qprog)

print(qprog.qsharp)
```

## Output Formats

The Classiq platform provides different ways to format the output of
synthesized quantum programs. You can choose multiple output formats.

-   In the SDK, you can print or save the desired output format after synthesizing.
-   In the IDE, you can download the desired output format after synthesizing.

The output options:

-   `"qasm"` - OpenQASM. The qasm circuit is in `qprog.qasm`.
-   By default, the Classiq platform uses OpenQASM 2.0. To use OpenQASM 3.0 instead, set the
    `qasm3` field of the preferences to `True`.
-   `"qsharp"` - Q#. The qsharp circuit is in `qprog.qsharp`.
-   `"qir"` - Microsoft's QIR. The QIR circuit is in `qprog.qir`.
-   `"ionq"` - IonQ Json format is in `qprog.ionq`.
-   `"cirq_json"` - Cirq Json format is in `qprog.cirq_json`.
-   `"qasm_cirq_compatible"` - OpenQASM 2.0 is compatible with Cirq, which is in `qprog.qasm_cirq_compatible`.

## Optimization Level

Some optimization strategies employed by the synthesis engine are computationally heavy.
You can control the tradeoff between synthesis time and the exhaustiveness of the search for
optimal circuit. Use `optimization_level` with the following values:

-   `NONE` (0) - take the most time-efficient path
-   `LOW` (1) - perform only light-optimizations
-   `MEDIUM` (2) - skip the most time-consuming optimizations
-   `HIGH` (3) - employ the most aggressive and time-consuming optimizations

Notes:

-   Lower optimization levels may fail to satisfy user-specified synthesis constraints
    (see [Quantum Program Constraints](constraints.md#optimization-parameter)). In such cases you can retry with a higher
    optimization level.
-   Lower optimization levels may result in missing details in the quantum-program visualization
    in the IDE. This limitation will be lifted in future releases.
-   Higher optimization levels may take longer to complete, and may yield better results, but
    neither is guaranteed.

## Timeouts

The Classiq platform offers two timeouts:

-   `timeout_seconds` – A timeout value for the end-to-end synthesis process.

-   `optimization_timeout_seconds` – A timeout value specifically controlling the search process
    when given constraints and optimization directives
    (see [Quantum Program Constraints](constraints.md#optimization-parameter)).

You can specify both timeouts. Just make sure that the optimization timeout is
smaller than the generation timeout. Both timeouts are specified in a whole number of seconds.

## Toggling Quantum Program Debug Information

The Classiq platform allows users to toggle quantum program debug information:

-   `debug_mode` - When the flag is set to `True` (default), the quantum program
    will contain debug information for enhanced visualization (See [Quantum
    Program Visualization Tool](../analysis/visualization-of-quantum-programs.md)).

Setting this flag to `False` can potentially decrease the quantum program's size
and increase synthesis speeds.
