---
search:
    boost: 3.200
---

# Combinatorial Optimization

The Classiq combinatorial optimization platform is a quantum software engine for optimization problems that you define.
The engine tackles your formulated real-world optimization challenges and generates customized quantum programs.
You choose whether to run the programs on a quantum backend or a classical simulation, and receive the optimized solution.
To gain further insights regarding the synthesis process, you can examine the synthesized program with the
Classiq [analyzer](../../../user-guide/analysis/index.md) module.

## Formulating Problems

You describe new optimization problems using the Python SDK package.
The problem is formulated using [PYOMO](http://www.pyomo.org/), a Python-based, open-source optimization
modeling language. The language supports a wide variety of problem types, such as integer linear
programming, quadratic programming, graph theory problems, and SAT problems.
Read in-depth reviews of the language’s capabilities in
[ [1] ](#pyomo documentation) and [ [2] ](#pyomo cookbook) [ [3] ](#pyomo intro).
The basics of problem modelling in PYOMO and
a complete example are in the [problem formulation](problem-formulation.md) section.

The Classiq platform supports an extensive set of modeling configurations for your use ([supported modeling](supported-modeling.md)).

## Solving Optimization Problems

The core Classiq capabilities are generation of a designated quantum solution,
and execution of the generated algorithm on a quantum backend.

The Classiq platform relies on the QAOA penalty algorithm to solve optimization problems.

## References

<a name="pyomo documentation">[1]</a> Pyomo Documentation 6.0.1, https://pyomo.readthedocs.io/en/stable/.

<a name="pyomo cookbook">[2]</a> Prof. Jeffrey Kantor’s Pyomo Cookbook
[https://jckantor.github.io/ND-Pyomo-Cookbook/](https://jckantor.github.io/ND-Pyomo-Cookbook/).

<a name="pyomo intro">[3]</a> J. D. Siirola, Introduction to Pyomo: The optimization foundation for IDAES,
https://www.osti.gov/servlets/purl/1524963 (2018).
