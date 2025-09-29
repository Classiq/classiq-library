---
search:
    boost: 0.900
---

<!-- cspell:ignore qsdk -->

# Execution on Intel Backends

The Classiq executor supports execution on Intel® simulators.

## Usage

In Classiq's [web platform](https://platform.classiq.io/) simply choose Intel in the checkbox menu under "Execution".

In Classiq's Python SDK, use the following code:

[comment]: DO_NOT_TEST

```python
from classiq import IntelBackendPreferences

preferences = IntelBackendPreferences(
    backend_name="intel_qsdk_simulator",
)
```

## Citing Intel® Quantum SDK

To cite the Intel® Quantum SDK, please reference:
Khalate, P., Wu, X.-C., Premaratne, S., Hogaboam, J., Holmes, A., Schmitz, A., Guerreschi, G. G., Zou, X. & Matsuura, A. Y., arXiv:2202.11142 (2022).

## Supported Backends

Included simulators:

-   "intel_qsdk_simulator"
