[comment]: SINGLE_FILE_SLOW

## Intro

In this example, we will show a simple example of parametric quantum program (PQC).

We will take 1 input from the user, and consider 1 weight, while utilizing 1 qubit in the PQC.
During this example, the goal of the learning process is to assess the right angle for a `Rx` gate for performing a "NOT" operation (spoiler, the correct answer is $\pi$).

## General flow

In [section 1](#step-1-create-our-torchnnmodule) we will see the code required for defining a quantum layer.
This will include:

-   section 1.1: defining the quantum model and synthesizing it to a quantum program
-   section 1.2: defining the post-process callable
-   section 1.3: defining a `torch.nn.Module` network

In section 2 we will choose our dataset, loss function, and optimizer.
Section 3 will demostrate how to handle the learning process, and section 4 will test our network's performance.

If you're not familiar with PyTorch, it is highly recommended that you'll check out the following pages from their documentation:

-   [Creating Models](https://pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html#creating-models)
-   [Build the Neural Network](https://pytorch.org/tutorials/beginner/basics/buildmodel_tutorial.html)
-   [Optimizing the Model Parameters](https://pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html#optimizing-the-model-parameters)
-   [Tensors](https://pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html)
-   [Datasets & DataLoaders](https://pytorch.org/tutorials/beginner/basics/data_tutorial.html)

## Step 1 - Create our `torch.nn.Module`

### Step 1.1 - Create our parametric quantum program

Our quantum model will be defined and synthesized as follows:

```python
from classiq import (
    synthesize,
    qfunc,
    QArray,
    QBit,
    RX,
    Output,
    CReal,
    allocate,
)


@qfunc
def encoding(theta: CReal, q: QArray[QBit]) -> None:
    RX(theta=theta, target=q[0])


@qfunc
def mixing(theta: CReal, q: QArray[QBit]) -> None:
    RX(theta=theta, target=q[0])


@qfunc
def main(input_0: CReal, weight_0: CReal, res: Output[QArray[QBit]]) -> None:
    allocate(1, res)
    encoding(theta=input_0, q=res)
    mixing(theta=weight_0, q=res)


quantum_program = synthesize(main)
```

The input (`input_0`), logically indicating the state `|0>` or `|1>`, is transformed into an angle, either `0` or `pi`.

### Step 1.2 - Create the Post-processing

Post-process the result of executing the quantum program to obtain a single number (`float`) and a single dimension `Tensor`.

```python
import torch

from classiq.applications.qnn.types import SavedResult


# Post-process the result, returning a dict:
# Note: this function assumes that we only care about
#   differentiating a single state (|0>)
#   from all the rest of the states.
#   In case of a different differentiation, this function should change.
def post_process(result: SavedResult) -> torch.Tensor:
    """
    Take in a `SavedResult` with `ExecutionDetails` value type, and return the
    probability of measuring |0> which equals the amount of `|0>` measurements
    divided by the total amount of measurements.
    """
    counts: dict = result.value.counts
    # The probability of measuring |0>
    p_zero: float = counts.get("0", 0.0) / sum(counts.values())
    return torch.tensor(p_zero)
```

### Step 1.3 - Create a network

Now we're going to define a network, just like any other PyTorch network, only that this time, we will have only 1 layer, and it will be a quantum layer.

```python
import torch

from classiq.applications.qnn import QLayer


class Net(torch.nn.Module):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.qlayer = QLayer(
            quantum_program,  # the quantum program, the result of `synthesize()`
            post_process,  # a callable that takes a single `SavedResult`, returning a `torch.Tensor`
            *args,
            **kwargs
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.qlayer(x)
        return x


model = Net()
```

### Step 2 - Choose a dataset, loss function, and optimizer

We will use the `DATALOADER_NOT` dataset, defined [here](datasets.md), as well as [`L1Loss`](https://pytorch.org/docs/stable/generated/torch.nn.L1Loss.html) and [SGD](https://pytorch.org/docs/stable/generated/torch.optim.SGD.html)

```python
from classiq.applications.qnn.datasets import DATALOADER_NOT
import torch.nn as nn
import torch.optim as optim

_LEARNING_RATE = 1.0

# choosing our data
data_loader = DATALOADER_NOT
# choosing our loss function
loss_func = nn.L1Loss()
# choosing our optimizer
optimizer = optim.SGD(model.parameters(), lr=_LEARNING_RATE)
```

### Step 3 - Train

For the training process, we will use a loop similar to [the one recommended by PyTorch](https://pytorch.org/tutorials/beginner/blitz/neural_networks_tutorial.html#update-the-weights)

```python
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader


def train(
    model: nn.Module,
    data_loader: DataLoader,
    loss_func: nn.modules.loss._Loss,
    optimizer: optim.Optimizer,
    epoch: int = 20,
) -> None:
    for index in range(epoch):
        print(index, model.qlayer.weight)
        for data, label in data_loader:
            optimizer.zero_grad()

            output = model(data)

            loss = loss_func(output, label)
            loss.backward()

            optimizer.step()


train(model, data_loader, loss_func, optimizer)
```

### Step 4 - Test

Lastly, we will test our network accuracy, using [the following answer](https://stackoverflow.com/questions/52176178/pytorch-model-accuracy-test#answer-64838681)

```python
def check_accuracy(model: nn.Module, data_loader: DataLoader, atol=1e-4) -> float:
    num_correct = 0
    total = 0
    model.eval()

    with torch.no_grad():
        for data, labels in data_loader:
            # Let the model predict
            predictions = model(data)

            # Get a tensor of booleans, indicating if each label is close to the real label
            is_prediction_correct = predictions.isclose(labels, atol=atol)

            # Count the amount of `True` predictions
            num_correct += is_prediction_correct.sum().item()
            # Count the total evaluations
            #   the first dimension of `labels` is `batch_size`
            total += labels.size(0)

    accuracy = float(num_correct) / float(total)
    print(f"Test Accuracy of the model: {accuracy*100:.2f}")
    return accuracy


check_accuracy(model, data_loader)
```

The results show that the accuracy is $1$, meaning a 100% success rate at performing the required transformation (i.e. the network learned to perform a X-gate).
We may further test it by printing the value of `model.qlayer.weight`, which is a tensor of shape `(1,1)`, which should, after training, be close to $\pi$.

Finally, we safely teardown the `QLayer` instance.

```python
model.qlayer.teardown()
```

## Summary

In this example, we wrote a fully working Quantum Neural Network from scratch, trained it, and saw its success at learning the requested transformation.

In section 1 we defined our parametric quantum program, as well as our post-processing function. Together, these two are sent as arguments to [the `QLayer` object](qlayer.md).
In section 2 we set some hyperparameters, and in section 3 we trained our model.
Section 4 helped us verify that our network is working as intended.
