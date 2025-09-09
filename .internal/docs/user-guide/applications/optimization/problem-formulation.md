[comment]: SINGLE_FILE

In the PYOMO language, like any other algebraic modeling languages (AMLs),
the optimization problem consists of three main components:
decision variables, constraints, and an objective function.
This section briefly introduces these components and explains the modalities supported by the platform.

### Model

As an object-oriented language, PYOMO organizes the optimization problem into a single object of type
ConcreteModel. It contains all the other components as Python attributes.
The model is declared in the following way:

```python
import pyomo.environ as pyo

model = pyo.ConcreteModel()
```

### Decision Variables

The variables component is the “unknown part” of the model.
The solver aims to assign values that constitute the best possible solution.
Following is a description of the possible arguments for variable declaration in PYOMO.

In many optimization problems, the variables are indexed.
The index set is provided as the first argument to the PYOMO var object.

```python
index_set = [0, 1, 2, 3]
```

[comment]: DO_NOT_TEST

```python
model.x = pyo.Var(index_set)
```

Next, state the variable domain.
It may be a binary variable, an integer variable,
a real variable, etc. The platform currently supports the binary and integer domains:

• Binary:

[comment]: DO_NOT_TEST

```python
model.x = pyo.Var(index_set, domain=pyo.Binary)
```

• Integer:

[comment]: DO_NOT_TEST

```python
model.x = pyo.Var(index_set, domain=pyo.NonNegativeIntegers, bounds=(0, 7))
```

If you know the variable value, fix it now to save qubits:

[comment]: DO_NOT_TEST

```python
model.x[0].fix(3)
```

See [PYOMO variables](https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Variables.html).

### Constraints

Constraints enrich the descriptive power of optimization problems.
Different scenarios, rules, regulations, and variable relations may be phrased as conditions on decision variables that must be satisfied.
In PYOMO, specify the constraints using equality or inequality expressions. There are several ways to integrate them inside the existing PYOMO model:

-   Using the `expr` argument:

```python
model = pyo.ConcreteModel()
model.x = pyo.Var(index_set, domain=pyo.Binary)
model.amount_constraint = pyo.Constraint(expr=sum(model.x[i] for i in model.x) == 3)
```

-   Using a rule argument and a separate Python function:

```python
def amount_rule(model):
    return sum(model.x[i] for i in model.x) == 3


model.amount = pyo.Constraint(rule=amount_rule)
```

-   Using a Python constraint decorator:

```python
@model.Constraint()
def amount_rule(model):
    return sum(model.x[i] for i in model.x) == 3
```

Index the constraints similarly to the variables.

```python
def size_rule(model, i):
    return model.x[i] <= model.x[i + 1]


model.size_rule = pyo.Constraint(index_set[:-1], rule=size_rule)
```

See [PYOMO constraints](https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Constraints.html).

### Objective Function

The objective function encodes the essence of the best solution.
It is a function of the decision variables, which return a real value that the optimization solver tries to minimize or maximize.

It is incorporated into the PYOMO model similarly to the constraints: with an `expr` argument, with a rule argument, or with a decorator.
An additional declaration argument is `sense`, which is set to `minimize` or `maximize`.

```python
model.cost = pyo.Objective(expr=sum(model.x[i] for i in index_set), sense=pyo.maximize)
```

See [PYOMO objective functions](https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Objectives.html).

### Importing

You can import all PYOMO components from the `pyomo.environ` sub-package:

[comment]: DO_NOT_TEST

```python
import pyomo.environ as pyo

Model = pyo.ConcreteModel()
model.variable = pyo.Var()
model.constraint = pyo.Constraint()
```

### Complete Example

```python
from typing import Union, List
import numpy as np
import pyomo.core as pyo
import networkx as nx


def mis(graph: Union[nx.Graph, List[List[int]]]) -> pyo.ConcreteModel:
    if isinstance(graph, list):
        graph = nx.convert_matrix.from_numpy_matrix(np.array(graph))
    model = pyo.ConcreteModel()
    model.Nodes = pyo.Set(initialize=list(graph.nodes))
    model.Arcs = pyo.Set(initialize=list(graph.edges))

    model.x = pyo.Var(model.Nodes, domain=pyo.Binary)

    @model.Constraint(model.Arcs)
    def independent_rule(model, node1, node2):
        return model.x[node1] + model.x[node2] <= 1

    model.cost = pyo.Objective(expr=sum(list(model.x.values())), sense=pyo.maximize)

    return model
```

This example combines all components under a single Python function.
It accepts user-defined inputs, and returns a complete PYOMO model with the assigned parameters.
The function is saved in a file of the same name.
The `graph` may be either an instance of the
`networkx.Graph` class or the adjacency matrix in the form of `List[List[int]]`.
