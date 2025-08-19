---
search:
    boost: 3.048
---

# Quantum Program Visualization Tool

The Classiq analyzer application helps you visualize and analyze quantum programs.
The input to the application is a quantum program synthesized by the Classiq [synthesis engine](../../synthesis/getting-started.md), or an OpenQASM quantum program.

## Accessing the Quantum Program Visualization Tool

There are 2 ways to view a quantum program using the visualization tool:

-   Through the Classiq Python SDK

-   Direct access via the Classiq IDE

### Classiq Python SDK

-   Synthesize your model using synthesize() to obtain a quantum program, and pass it as a parameter to the function show(). Here is an example with a trivial model:

[comment]: DO_NOT_TEST

```python
from classiq import qfunc, Output, QBit, synthesize, show, allocate


@qfunc
def main(res: Output[QBit]) -> None:
    allocate(1, res)


qprog = synthesize(main)
show(qprog)
```

### Direct Access

-   Synthesizing a quantum program using the IDE (https://platform.classiq.io/synthesis) automatically redirects you to the visualization tool.
-   Upload (drag and drop) a file that contains a quantum program synthesized using the Classiq engine (either synthesized and downloaded from the IDE or obtained from the python SDK using `qprog.save_result("file-name")`)) into [https://platform.classiq.io/circuit/](https://platform.classiq.io/circuit/).

![upload_qp](../../resources/upload_qp.gif)

## Using Visualization Tool

Within the Quantum Program page you can toggle between 2 versions of the visualization tool:

![toggle_versions](../../resources/toggle_versions.gif)

-   [New Version](new-version.md)
-   [Basic Version](basic-version.md)

## Sharing your Quantum Program Visualization

You can easily share your Quantum Program visualization with anyone, even those who haven’t signed up for the Classiq platform. It’s simple:

-   Copy the Quantum Program URL directly from your browser and share it.
-   Alternatively, click the "Share" button on the Quantum Program page, choose a social media to share in or copy the generated link, and share it with anyone.

![qp_sharing_link](../../resources/qp_sharing_link.gif)
