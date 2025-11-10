---
search:
    boost: 2.252
---

# Quantum Program Transpilation

Transpilation is the process of optimizing an already-synthesized quantum program and
matching it to the desired hardware. It includes optimizations, such as
combining a sequence of gates into an equivalent single gate; and
transformations, such as qubit routing (i.e., using swap gates to
apply 2-qubit gates on partially connected hardware).

Classiq synthesis includes transpilation. However, the transformations
applied to the quantum program affect the hierarchical nature of the quantum program. For
example, the gates representing functions are decomposed to basis gates, and
thus do not appear in the transpiled quantum program. To visualize the
hierarchical quantum program in a meaningful way, the [analyzer web application](../analysis/visualization-of-quantum-programs.md)
uses the non-transpiled quantum program. On the other hand, when executing a quantum program,
it is preferable to use the transpiled quantum program, because it is already optimized
for the given hardware. Thus, the [Executor](../execution/index.md) uses the
transpiled quantum program.

The [synthesis results](getting-started.md#synthesis-results) include
both quantum programs, in all [output formats](preferences.md#output-formats)
that you request. In addition, when using [hardware-aware synthesis](hardware-aware-synthesis.md),
the output also includes the quantum program in the format required for running on the
provided hardware.

In certain cases, the Classiq executor re-transpiles quantum programs immediately
before execution. This is to minimize execution errors and make sure that
all executed gates are compatible with the requested hardware.
See [execution preferences](../execution/index.md#execution-preferences').

### Transpilation Options

-   `none` - no transpilation.
-   `decompose` - decompose all of the functions according to the basis gates of the backend. This is the default option.
-   `light` - a heavier transpilation method to better optimize the quantum programs. Best suited for fully connected hardware.
-   `medium` - another heavy transpilation method that optimizes the quantum program even further but takes more time.
    This method is optimal for optimization of hardware with more complex connectivity.
-   `auto optimize` - allows the Classiq platform to choose the transpilation automatically, based on the chosen backend.
-   `intensive` - designed for maximum optimization of quantum programs and is particularly well-suited for quantum hardware with complex connectivity.
-   `custom` - offers a personalized approach to optimizing quantum circuits while considering various factors that contribute to the circuit's performance. The internal decision-making process takes specific optimization criteria into account, ensuring that quantum programs are transpiled in a way that maximizes efficiency and resource utilization for the chosen backend. This option's primary focus is on delivering the best possible circuit performance.

<!-- prettier-ignore-start -->
!!! tip
    The heavier the transpilation method, the better the quantum programs are optimized, but the transpilation process takes longer.
<!-- prettier-ignore-end -->
