# Finance

The Classiq financial package provides a rich interface to automatically generate
and execute quantum programs for various financial problems such as options
pricing and risk analysis.

## Background

Complex models and simulations, borrowed from the world of physics, are very
common in finance.
Many of these models are stochastic. Hence, numerical methods have to
be employed to solve them. The most popular model is Monte
Carlo [ [1] ](#Monte Carlo Methods in Financial) due to its flexibility and
ability to handle stochastic parameters generically.
Classical Monte Carlo methods, however, generally require extensive computational
resources to provide an accurate estimation.
By leveraging the laws of quantum mechanics, a quantum computer may provide novel ways to
solve such computationally intensive financial problems. Relevant financial
applications include risk management and option pricing.
The core of several of these applications is the amplitude estimation
algorithm [ [2] ](#Amplitude estimation and amplification), which can estimate a parameter with a
convergence rate of 1/M, where M is the number of Grover iterations,
representing a theoretical quadratic speed-up over classical Monte Carlo methods.

Other financial models such as portfolio optimizations can be modeled by
the [Classiq optimization](../optimization/index.md) methods.

## References

<a name="Monte Carlo methods in financial">[1]</a> Paul
Glasserman, [Monte Carlo Methods in Financial Engineering](https://link.springer.com/book/10.1007/978-0-387-21617-1).
Springer-Verlag New York, 2003, p. 596.

<a name="Amplitude estimation and amplification">[2]</a> Gilles Brassard, Peter
Hoyer, Michele Mosca, and Alain
Tapp, [Quantum Amplitude Amplification and Estimation](https://arxiv.org/abs/quant-ph/0005055),
Contemporary Mathematics 305 (2002).
