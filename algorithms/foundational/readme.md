# Foundational

Fundamental quantum algorithms, providing the foundations for future advancements
and demonstrating query complexity advantages.

- **Bernstein Vazirani**-
  Demonstrating a linear query complexity advantage over deterministic and
  probabilistic classical method.
  The algorithm finds the hidden-bit string $a$ by a single query call to an oracle function
  $f(x) = (a\cdot x) \mod 2$, where $x$ is also a bit string and $\cdot$ denotes the bitwise multiplication.
  This problem constitutes a specific case of the general hidden-shift problem.
- **Deutsch Jozsa** - Widely regarded as the first quantum algorithm, it demonstrates an exponential advantage in query
  complexity over classical deterministic approaches. Given oracle access to a Boolean function promised to be either
  constant or balanced, the algorithm deterministically identifies which case holds using a single query to
  the function.
- **Quantum Teleportation** - A foundational quantum communication protocol, employing quantum entanglement and
  classical communication to transfer ("teleport") an arbitrary qubit state from one place to another.
- **Simon** - Given an oracle binary function, satisfying $f(x)=f(y)$ if and only if $y=x\oplus s$ for some secret key $s$, the
  algorithm recovers $s$. It does so using a number of oracle queries linear in the input size, yielding an exponential
  improvement in query complexity compared to the best classical approaches.
