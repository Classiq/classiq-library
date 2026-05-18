# Quantum Review — Classical Shadow Tomography Notebook

**Notebook:** `algorithms/qml/classical_shadow_tomography/classical_shadow_tomography.ipynb`
**Paper:** Huang, Kueng, Preskill — Nature Physics 16, 1050 (2020)
**Date:** 2026-05-10

---

## Verdict

Well-structured pedagogical implementation with clean Classiq integration. Core algorithm (median-of-means, both Pauli and Clifford ensembles, parametric synthesis) is correct. However, two critical bugs must be fixed before publication, plus several minor issues.

---

## Critical Bugs

**1. Pauli shadow norm formula wrong in `error_bound()`**

- Paper (eq 19): `‖O‖²_shadow = 3ᵏ` for a unit k-local Pauli
- Code uses: `np.linalg.norm(O_traceless, ord=np.inf)**2` = 1 for ZZ
- Effect: underestimates required samples by factor 3ᵏ (9× for ZZ)
- Notebook outputs 9,008 samples; correct bound is ~81,065
- The Clifford `error_bound_clifford()` gets this right — inconsistent
- Fix: replace infinity norm with `3**k * norm_inf**2` where k is Pauli weight

**2. Y-basis sign reversed in `estimate_observable()`**

- HS gate maps |+y⟩ (eigenvalue +1) → |1⟩ and |−y⟩ (eigenvalue −1) → |0⟩
- Correct: snapshot=0 → term=−3, snapshot=1 → term=+3
- Code does the opposite: snapshot=0 → +3, snapshot=1 → −3
- Bug hidden because notebook only tests ZZ (no Y operators)
- Any observable with odd number of Y factors gives wrong sign (IY, YZ, YI, etc.)
- `snapshot_reconstruction()` is correct — internal inconsistency between the two paths
- Fix: swap sign assignments for Y-basis in the lookup table

---

## Major Issues

**3. Misleading accuracy claim**

- Cell 49: "excellent estimation with only 200 samples"
- Actual result: 0.45 estimated vs 1.0 true (55% relative error)
- Expected given 200 << 81,065 required samples
- Fix: revise claim or use enough shots to demonstrate convergence

**4. Deprecated API**

- `batch_sample()` raises `ClassiqDeprecationWarning` in cell 25
- Fix: replace with `sample()` passing a list of parameter dicts

---

## Minor Issues

**5. `main()` redefined 3 times**

- Cells 19, 43, 51 each redefine `main()` at module level
- Re-running cells out of order causes wrong circuit to be synthesized
- Fix: use uniquely named functions per section

**6. Equation label mismatch in cell 28**

- Comment references "Eq. (S44)" from Huang et al. supplement
- Notebook's own numbering calls it Eq. (4)
- Fix: align labeling

---

## Cosmetic

**7.** Cell 0 contains raw development notes and `#TODO` — remove before publication
**8.** Typo in cell 4: "unkown" → "unknown"
**9.** Clifford reconstruction gives worse Frobenius distance than Pauli (0.60 vs 0.33) with no explanation — expected behavior but should be noted

---

## What Works Correctly

- Median-of-means estimator structure
- Pauli inverse channel: `3*(U†|b><b|U) - I` ✓
- Clifford inverse channel: `(2ⁿ+1)*U†|b><b|U - I` ✓
- Clifford error bound: `3·tr(O₀²)` ✓
- Basis angles for X, Y, Z rotations ✓
- Parametric synthesis (synthesize once, batch-execute) ✓
- Clifford diagonal-entry optimization ✓
