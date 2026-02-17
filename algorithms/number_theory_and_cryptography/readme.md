# Number Theory and Cryptography

Quantum algorithms for number-theoretic problems offer the most striking
speedups over their best known classical counterparts. Because many widely deployed
cryptographic schemes rely on one-way functions whose security is grounded in the computational
hardness of number-theoretic tasks, these polynomial-time quantum algorithms pose a
well-established threat to modern secure communication and key exchange protocols,
including RSA, elliptic-curve cryptography, and the Diffie–Hellman key exchange.

- **Discrete log** - Solves the Discrete logarithm problem, i.e., given an element, $x$, of a cyclic group
  with generator $g$, finds the least positive integer $s$, such that $g^s = x$. The algorithm provides an exponential
  speedup relative to the best known classical algorithm. The hardness of the problem, provides the basis for the
  Diffie-Hellman key exchange protocol. Similarly to order-finding and elliptic curve, the problem
  constitutes an instance of the Abelian Hidden Subgroup Problem (HSP).
- **Elliptic curves** - A quantum algorithm solving the elliptic curve discrete logarithm problem in polynomial running time. The
  hardness of the problem constitutes the basis of elliptic curve cryptography, which is widely used for key-exchange, cryptocurrency
  and high-security communications.
- **Hidden shift problem** - Implementation of an algorithm to find the hidden-shift for the family of Boolean bent functions, which
  are characterized by high non-linearity and a perfectly flat Fourier transform. Given access to queries of a functions $f$,
  the algorithm finds the shift, a boolean string, which satisfies $f(x) = f(x \oplus s)$. The quantum algorithm provides
  an exponential separation in query complexity relative to any (even the best) classical algorithm.
- **Shor's algorithm** - Evaluates the prime factors of a large integer. The algorithm played a foundational role in
  the development of the field, providing an exponential speedup over currently known classical algorithms. The quantum component
  is naturally structured as a Quantum Phase Estimation (QPE) routine, utilizing
  Classiq’s built-in `flexible_qpe` and modular arithmetic.
