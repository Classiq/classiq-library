---
search:
    boost: 3.204
---

# Datasets

Pytorch provides two classes: `DataSet` and `DataLoader`.
If you're not familiar with them, please review them [here](https://pytorch.org/tutorials/beginner/basics/data_tutorial.html)

Classiq provides two simple datasets, which are mainly used in our examples.
They can be found in `classiq/applications/qnn/data_sets.py`.

## DatasetNot

This dataset is used for training a network to learn the "NOT" operation.
More specifically, learning the angle to a parametrized `Rx` gate (spoiler - the correct answer is `pi`).

This dataset has 2 items:

0. the data is `|00...0>`, the label is `|11...1>`.
1. the data is `|11...1>`, the label is `|00...0>`.

The amount of qubits is specified in the constructor (`def DatasetNot.__init__(self, n: int, ...)`).

### Transformers

Additionally, we provide 2 `Transform`s for this class. (Their PyTorch documentation can be found [here](https://pytorch.org/tutorials/beginner/basics/transforms_tutorial.html)), which serve our example.

Note that these transformers are automatically used.
Feel free to keep reading about them, though this is not mandatory.

In our example, we wish to
A) encode the input state onto the quantum circle
B) execute the PQC
C) measure the PQC
D) post-process the measurement results

Our transformers help steps `A` and `D`.

First, `state_to_weights` transforms the state, into parameters for the encoding `Rx` gates. This is used for step `A`
In other words, the state `|0>` is transformed into the angle `0`, and the state `|1>` is transformed into the angle `pi`.

Second, `state_to_label` transforms the expected output state into a single float number.
More specifically, since we generate this data, we set the expected output state to be a pure state (in the `Z` basis).
Additionally, we define the post-processing to return the probability of measuring `|00...0>` in the output state.
Thus, for the output `|00...0>`, the post processed output is `1`, corresponding to `100%`, and for the output `|11...1>`, the post processed output is `0`.

### DatasetXor

This dataset is used for training a network to learn the "XOR" operation.
This may take, similar to `DatasetNot`, the amount of qubits in the constructor.
The "XOR" operation on more than 2 inputs is defined as "a quantum program that outputs a 1 when the number of 1s at its inputs is odd, and a 0 when the number of incoming 1s is even" (credit: [wikipedia](https://en.wikipedia.org/wiki/XOR_gate#More_than_two_inputs))

## Usage examples

### Using pre-configured `DataLoader`s

```python
from classiq.applications.qnn.datasets import DATALOADER_NOT

for data, label in DATALOADER_NOT:
    print(f"Training the following data: {data}")
    print(f"with the following labels: {label}")
```

### Using pre-configures `Dataset`s

```python
from classiq.applications.qnn.datasets import DATASET_NOT
from torch.utils.data import DataLoader

DATALOADER_NOT = DataLoader(DATASET_NOT, batch_size=2, shuffle=True)

for data, label in DATALOADER_NOT:
    print(f"Training the following data: {data}")
    print(f"with the following labels: {label}")
```

### Using the `DatasetNot` class

#### without using our pre-defined transformers

```python
from classiq.applications.qnn.datasets import DatasetNot
from torch.utils.data import DataLoader

NUM_QUBITS = 1

DATASET_NOT = DatasetNot(NUM_QUBITS)

DATALOADER_NOT = DataLoader(DATASET_NOT, batch_size=2, shuffle=True)

for data, label in DATALOADER_NOT:
    print(f"Training the following data: {data}")
    print(f"with the following labels: {label}")
```

#### with our pre-defined transformers

```python
from classiq.applications.qnn.datasets import (
    DatasetNot,
    state_to_weights,
    state_to_label,
)
from torch.utils.data import DataLoader
from torchvision.transforms import Lambda

NUM_QUBITS = 1

DATASET_NOT = DatasetNot(
    1, transform=Lambda(state_to_weights), target_transform=Lambda(state_to_label)
)

DATALOADER_NOT = DataLoader(DATASET_NOT, batch_size=2, shuffle=True)

for data, label in DATALOADER_NOT:
    print(f"Training the following data: {data}")
    print(f"with the following labels: {label}")
```
