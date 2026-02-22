# Amplitude Amplification and Estimation

Algorithmic variations of the amplitude amplification and estimation algorithm.
Amplitude amplification is a technique to increase the probability of measuring marked ("good") states. The scaling is typically achieved employing the Grover operator as a canonical building block.
Generally, the methods produce a quadratic speedup, relative to classical repetition, so a marked state which
has probability $p$ to be measured, can be found with a probability close to unity by employing $O(1/\sqrt{p})$
measurements. In contrast, the goal of amplitude estimation is to estimate the probability value, $p$. It achieves an additive error $\epsilon$ in $O(1/\epsilon)$ iterations, obtaining a quadratic speed up relative to the classical Monte Carlo.

The directory contains the following methods:

- **Oblivious Amplitude Amplification** - Amplifies a coherent transformation by increasing the probability that a desired
  operation is successfully applied, where success is indicated by the state of an auxiliary qubit. The algorithm is
  oblivious to the input state, meaning it works uniformly for any input, does not rely on efficient state preparation,
  and avoids measurements. As a result, it can be implemented as part of a larger unitary quantum circuit without
  interrupting coherence.
- **Quantum Monte Carlo Integration** - Employs Quantum Amplitude Estimation (QAE) to evaluate a definite integral. Obtains a
  quadratic improvement of the analogous classical method, exhibiting an error which scales as $O(1/M)$, where $M$ is the
  number of controlled applications of the Grover operator within the QAE.
- **Quantum Singular Value Transformation (QSVT) fixed point amplitude amplification** - Solves unstructured
  search problems without requiring prior knowledge of the fraction of marked solutions.
  By leveraging QSVT together with an efficiently block-encoded operator, it implements amplitude amplification
  in a fixed-point manner, guaranteeing monotonic convergence toward the marked subspace and eliminating
  the risk of overshooting the target state.
- **Quantum Counting** - Efficiently estimates the number of valid solutions to a search problem. The algorithm
  employs QAE to obtain a quadratic query complexity speed up relative to classical algorithms.
