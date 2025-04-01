# Implementation of "Quantum State Preparation without Coherent Arithmetic"

**Related issue:** [classiq-library#792](https://github.com/Classiq/classiq-library/issues/792)

This folder provides working implementations of the state preparation algorithm proposed in the paper, with a particular focus on Gaussian state preparation.
Each notebook varies parameters resolution and exp_rate. For example:
- `resolution=6`, `exp_rate=1`: [stateprep_gaussian_n6_rate1.ipynb](./stateprep_guassian_n6_rate1.ipynb)
- `resolution=7`, `exp_rate=2`: [stateprep_gaussian_n7_rate2.ipynb](./stateprep_guassian_n7_rate2.ipynb)


Additional files:

- [utils.py](./utils.py): Contains utility functions used throughout the implementation.
- [materials/pyqsp_gaussian.ipynb](./materials/pyqsp_gaussian.ipynb): Verifies that the `pyqsp` library is working correctly.
- [materials/finding_exact_amplitude.ipynb](./materials/finding_exact_amplitude.ipynb): Contains experiments related to amplitude calibration.

### Difference from paper

In our implementation, we observed that the formula for the target amplitude—used prior to applying `exact_amplitude_amplification`—did not produce the expected results.
To address this, we performed a numerical analysis using Newton’s method and found that **multiplying the amplitude from the paper by a factor of 1.45** led to improved agreement with the intended state.

The notebook `materials/finding_exact_amplitude.ipynb` documents this investigation and provides supporting numerical evidence.
This difference may be due to implementation-specific details or implicit assumptions in the paper that differ from our setting.