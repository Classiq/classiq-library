---
search:
    boost: 2.545
---

# Quantum Neural Networks (QNN)

The Classiq QNN package is integrated with PyTorch so you can define `torch` networks with the addition of quantum layers (which are quantum programs).

<!-- prettier-ignore-start -->
!!! note
    This topic assumes basic knowledge of classical neural networks.
<!-- prettier-ignore-end -->

A neural network can be described as a list of layers, where each layer takes in a vector and outputs a different vector.
The vectors are treated as one-dimensional, and other dimensions are identical up to `reshape`.
The input and output of each layer is a vector of classical data; for convenience, called a `list` of `float`s.

This implies that any quantum layer, assuming the structure of the data transfer between the layers does not change, must take in classical data and return classical data.
This is done by renaming the incoming data as `parameters` for the quantum program, measuring the quantum layer, and applying classical post-processing calculations.

## Examples

One example for post-processing outputs of a quantum layer is returning a single number between `0` and `1`, indicating the confidence of a single choice.
This is common in cases of binary classification where a single qubit is measured and the output of the quantum layer is `the amount of |0> measured` divided by `the total number of measurements`.

Another example for post-processing is returning the probability (or amplitude) of each result.
If the measurement result is this:

```
{
	"00": 10,
	"01": 20,
	"10": 30,
	"11": 40,
}
```

Then the output of the quantum layer can be this:

```
[0.1 , 0.2 , 0.3 , 0.4]
```

which is normalized by the number of measurements, and the result is an ordered list of the probabilities of each result.

See a [full working example](a-full-example.md).

## Parameters: Inputs Versus Weights

A complete quantum layer takes two types of parameters: "inputs" and "weights".

The "input" parameters handle the encoding of the data (the classical `list` of `float`s), whereas the "weight" parameters undergo gradient descent in the usual NN way.

The "input" parameters are usually handled by the first sub-layer, while the "weight" parameters are usually handled by the rest of the sub-layers.

The Classiq engine distinguishes between the two types of parameters by their initial name:

-   `input_something` or `i_something` for inputs
-   `weight_something` or `w_something` for weights

## Classiq Engine API

### `QLayer`

Classiq exports the `QLayer` object, which inherits from `torch.nn.Module` (like most objects in the `torch.nn` namespace), and it acts accordingly.
For example:

[comment]: DO_NOT_TEST

```python
class MyNet(nn.Module):
    def __init__(self) -> None:
        self.linear_layer = nn.Linear(...)
        self.quantum_layer = classiq.QLayer(...)

    def forward(self, x: Tensor):
        x = self.linear_layer(x)
        x = self.quantum_layer(x)
        return x
```

The full declaration of the `QLayer` object, with explanations about the parameter it gets, are described [here](qlayer.md).

### Datasets

<!-- cspell:ignore playtesting -->

Classiq provides two [datasets](datasets.md) for play-testing examples.

1. "NOT" takes in a single-qubit state (either |0> or |1>) and returns an $n$-qubit state of all-ones or all-zeros, respectively. For example, for $n=2$: `0 -> |11>`, `1 -> |00>`.

2. "XOR" takes in an $n$-qubit state and returns a single classical bit, equal to the bitwise-xor of all the bits from the input state. For example, `101 -> 0`, `10101 -> 1`, `10 -> 1`, `11 -> 0`.

### Gradients

The Classiq engine automatically calculates the gradient of a PQC.
And there are many more calculations on their way.
Stay tuned!
