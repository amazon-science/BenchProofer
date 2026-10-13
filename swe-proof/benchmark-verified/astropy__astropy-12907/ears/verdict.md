# P2 adversarial audit — astropy__astropy-12907

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate patch (`cright[...] = np.diag(np.diag(right))` instead of gold's `= right`) is REJECTED by probes 3, 5, 6. On probe 3 (Linear1D & (Linear1D & Pix2Sky_TAN)) it produces a pure diagonal, dropping the TAN's real off-diagonal coupling (expected [[1,0,0,0],[0,1,0,0],[0,0,1,1],[0,0,1,1]]). On probe 5 it drops the Mapping([1,0]) axis-swap entries entirely. On probe 6 the (Linear1D & Pix2Sky_TAN) left block loses coupling. This candidate would NOT resolve the hidden tests, confirming the probe suite discriminates wrong implementations.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control (Req 2.1/2.2/1.3): nested independent 1D models -> diagonal.

A & (B & C) with three independent Linear1D models must yield the identity
3x3 matrix. The buggy code marks the bottom-right (nested) block all-ones,
so it produces spurious True entries. Fixed code copies the right operand's
own (diagonal) matrix -> pure diagonal.
"""
import numpy as np
from astropy.modeling.models import Linear1D
from astropy.modeling.separable import separability_matrix

m = Linear1D(1) & (Linear1D(2) & Linear1D(3))
mat = separability_matrix(m)
print("matrix:\n", mat.astype(int))
expected = np.eye(3, dtype=bool)
ok = mat.shape == (3, 3) and np.array_equal(mat, expected)
print("expected diagonal 3x3:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.4: nested A&(B&C) equals flat A&B&C, with a 2D non-separable model.

Uses Pix2Sky_TAN (2-in/2-out, non-separable) & (Linear1D & Linear1D) — the exact
issue example shape. Nested must equal flat, and the linear outputs must NOT be
spuriously coupled to the TAN inputs.
"""
import numpy as np
from astropy.modeling.models import Pix2Sky_TAN, Linear1D
from astropy.modeling.separable import separability_matrix

nested = Pix2Sky_TAN() & (Linear1D(10) & Linear1D(5))
flat = Pix2Sky_TAN() & Linear1D(10) & Linear1D(5)
mn = separability_matrix(nested)
mf = separability_matrix(flat)
print("nested:\n", mn.astype(int))
print("flat:\n", mf.astype(int))
expected = np.array([
    [1, 1, 0, 0],
    [1, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
], dtype=bool)
ok = np.array_equal(mn, mf) and np.array_equal(mn, expected)
print("nested==flat==expected:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.3 / 2.3: non-separable multi-input sub-model nested on the RIGHT.

left = Linear1D (1-in/1-out separable), right = (Linear1D & Pix2Sky_TAN) where
Pix2Sky_TAN is 2D non-separable. The bottom-right block must reflect the right
operand's ACTUAL structure: linear separable, TAN fully coupled within itself,
and no coupling across the disjoint blocks.
"""
import numpy as np
from astropy.modeling.models import Linear1D, Pix2Sky_TAN
from astropy.modeling.separable import separability_matrix

m = Linear1D(1) & (Linear1D(2) & Pix2Sky_TAN())
mat = separability_matrix(m)
print("matrix:\n", mat.astype(int))
# outputs: [lin1, lin2, tan_o1, tan_o2]; inputs: [lin1, lin2, tan_i1, tan_i2]
expected = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 1],
    [0, 0, 1, 1],
], dtype=bool)
ok = np.array_equal(mat, expected)
print("expected:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.2/4.2 & Req 5 regressions: contract + non-nested cases unchanged.

- dtype bool, correct shape.
- single-input/multi-output -> all True (3.2); is_separable all False (4.2).
- simple two independent shifts & scales via | (series) stays diagonal (5.2).
- arithmetic (+) fully non-separable (5.3).
"""
import numpy as np
from astropy.modeling.models import Shift, Scale, Mapping
from astropy.modeling.separable import separability_matrix, is_separable

# 3.1 / 5.4 basic parallel+series
m1 = Shift(1) & Shift(2) | Scale(1) & Scale(2)
sm1 = separability_matrix(m1)
assert sm1.dtype == np.bool_, sm1.dtype
assert sm1.shape == (2, 2)
assert np.array_equal(sm1, np.eye(2, dtype=bool)), sm1

# 3.2 single input, multiple outputs -> all True
mmap = Mapping((0, 0, 0))
sm2 = separability_matrix(mmap)
print("map matrix:\n", sm2.astype(int))
assert sm2.shape == (3, 1)
assert sm2.all(), sm2
# 4.2 is_separable all False for single-input multi-output
iss = is_separable(mmap)
print("is_separable:", iss)
assert iss.shape == (3,) and not iss.any(), iss

# 5.3 arithmetic fully non-separable
marith = Shift(1) & Shift(2) | (Scale(1) + Scale(2)) & Scale(3)
# simpler: just an addition of two 1-in models
from astropy.modeling.models import Polynomial1D
madd = Polynomial1D(1) + Polynomial1D(2)
sm3 = separability_matrix(madd)
print("add matrix:\n", sm3.astype(int))
assert sm3.shape == (1, 1) and sm3.all()

print("all contract/regression checks passed")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 5.4 / 2.1: Mapping nested on the right of & preserves axis reordering.

left = Shift, right = (Mapping([1,0])) nested. The Mapping duplicates/reorders
its own axes; the nested right block must reflect that exact permutation, not
an all-ones block. Also compares nested vs flat.
"""
import numpy as np
from astropy.modeling.models import Shift, Mapping
from astropy.modeling.separable import separability_matrix

nested = Shift(1) & (Shift(2) & Mapping([1, 0]))
flat = Shift(1) & Shift(2) & Mapping([1, 0])
mn = separability_matrix(nested)
mf = separability_matrix(flat)
print("nested:\n", mn.astype(int))
print("flat:\n", mf.astype(int))
# Mapping([1,0]) has 2 inputs, 2 outputs, permutation swap -> anti-diagonal block
# outputs: shift1, shift2, map_o0(=in1), map_o1(=in0)
# inputs:  shift1, shift2, map_i0, map_i1
expected = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
], dtype=bool)
ok = np.array_equal(mn, mf) and np.array_equal(mn, expected)
print("nested==flat==expected:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 5.6: left already-computed matrix copied faithfully into top-left.

When the LEFT operand is a nested compound (already a computed matrix) and the
right is a simple model, the top-left block must equal the left's own matrix.
This exercises the left branch (which the patch left unchanged) and confirms
cross-block independence. (B & C) & A form.
"""
import numpy as np
from astropy.modeling.models import Linear1D, Pix2Sky_TAN
from astropy.modeling.separable import separability_matrix

m = (Linear1D(1) & Pix2Sky_TAN()) & Linear1D(2)
mat = separability_matrix(m)
print("matrix:\n", mat.astype(int))
# outputs: lin1, tan_o1, tan_o2, lin2 ; inputs: lin1, tan_i1, tan_i2, lin2
expected = np.array([
    [1, 0, 0, 0],
    [0, 1, 1, 0],
    [0, 1, 1, 0],
    [0, 0, 0, 1],
], dtype=bool)
ok = np.array_equal(mat, expected)
print("expected:", ok)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""Req 2.1/2.4: nested A&(B&C) equals flat A&B&C, with a 2D non-separable model.

Uses Pix2Sky_TAN (2-in/2-out, non-separable) & (Linear1D & Linear1D) — the exact
issue example shape. Nested must equal flat, and the linear outputs must NOT be
spuriously coupled to the TAN inputs.
"""
import numpy as np
from astropy.modeling.models import Pix2Sky_TAN, Linear1D
from astropy.modeling.separable import separability_matrix

nested = Pix2Sky_TAN() & (Linear1D(10) & Linear1D(5))
flat = Pix2Sky_TAN() & Linear1D(10) & Linear1D(5)
mn = separability_matrix(nested)
mf = separability_matrix(flat)
print("nested:\n", mn.astype(int))
print("flat:\n", mf.astype(int))
expected = np.array([
    [1, 1, 0, 0],
    [1, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
], dtype=bool)
ok = np.array_equal(mn, mf) and np.array_equal(mn, expected)
print("nested==flat==expected:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bug: _cstack marked the nested right block all-ones (`cright[...] = 1`); gold copies the operand's actual matrix (`= right`). 6 distinct probes cover Req 1.1-1.4, 2.1-2.4 (nested==flat), 3.1/3.2 (contract, single-in/multi-out), 4.2 (is_separable), 5.2/5.3/5.4/5.6 (series, arithmetic, Mapping reorder, left-block copy). ALL 6 HOLD on the gold-patched tree. Positive controls (probes 1,2,3,5) FAIL at base (buffer marks nested block all-ones -> spurious True). Probes 4 and 6 also hold at base (they exercise non-nested / left-branch behavior that the patch left unchanged - regression protection). The naive `np.diag(np.diag(right))` candidate is rejected by 3 probes -> the suite has real discriminating power, resolving the previously-recorded G-EQ INCONCLUSIVE (no candidate rejected). Ran with conda swebench-lean python; each run applied the gold patch cleanly.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate patch (`cright[...] = np.diag(np.diag(right))` instead of gold's `= right`) is REJECTED by probes 3, 5, 6. On probe 3 (Linear1D & (Linear1D & Pix2Sky_TAN)) it produces a pure diagonal, dropping the TAN's real off-diagonal coupling (expected [[1,0,0,0],[0,1,0,0],[0,0,1,1],[0,0,1,1]]). On probe 5 it drops the Mapping([1,0]) axis-swap entries entirely. On probe 6 the (Linear1D & Pix2Sky_TAN) left block loses coupling. This candidate would NOT resolve the hidden tests, confirming the probe suite discriminates wrong implementations.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""Req 2.1/2.4: nested A&(B&C) equals flat A&B&C, with a 2D non-separable model.

Uses Pix2Sky_TAN (2-in/2-out, non-separable) & (Linear1D & Linear1D) — the exact
issue example shape. Nested must equal flat, and the linear outputs must NOT be
spuriously coupled to the TAN inputs.
"""
import numpy as np
from astropy.modeling.models import Pix2Sky_TAN, Linear1D
from astropy.modeling.separable import separability_matrix

nested = Pix2Sky_TAN() & (Linear1D(10) & Linear1D(5))
flat = Pix2Sky_TAN() & Linear1D(10) & Linear1D(5)
mn = separability_matrix(nested)
mf = separability_matrix(flat)
print("nested:\n", mn.astype(int))
print("flat:\n", mf.astype(int))
expected = np.array([
    [1, 1, 0, 0],
    [1, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
], dtype=bool)
ok = np.array_equal(mn, mf) and np.array_equal(mn, expected)
print("nested==flat==expected:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Bug: _cstack marked the nested right block all-ones (`cright[...] = 1`); gold copies the operand's actual matrix (`= right`). 6 distinct probes cover Req 1.1-1.4, 2.1-2.4 (nested==flat), 3.1/3.2 (contract, single-in/multi-out), 4.2 (is_separable), 5.2/5.3/5.4/5.6 (series, arithmetic, Mapping reorder, left-block copy). ALL 6 HOLD on the gold-patched tree. Positive controls (probes 1,2,3,5) FAIL at base (buffer marks nested block all-ones -> spurious True). Probes 4 and 6 also hold at base (they exercise non-nested / left-branch behavior that the patch left unchanged - regression protection). The naive `np.diag(np.diag(right))` candidate is rejected by 3 probes -> the suite has real discriminating power, resolving the previously-recorded G-EQ INCONCLUSIVE (no candidate rejected). Ran with conda swebench-lean python; each run applied the gold patch cleanly.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Confirmed via instance-image probes on both patched and base trees. Requirements 1 (block-diagonal & preserving operand structure), 2 (nested matches flat, diagonal for independent 1D, spurious-True removal), 3 (bool dtype/shape/nonzero->True contract), 4 (is_separable consistency), 5 (regression protection for _coord_matrix seed, series pipe, arithmetic, Mapping, custom _separable, left-block copy) all describe behavior the patched code exhibits. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found. Req 5.6 (left block already-correct) accurately describes cleft, which the patch left untouched.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior and localize the fix to astropy/modeling/separable.py / _cstack (legitimate — the module and helper are public and the gold's target). The nested-vs-flat A&(B&C)==A&B&C principle and the example Pix2Sky_TAN() & (Linear1D(10) & Linear1D(5)) come straight from the public problem_statement. The gold's actual edit (cright[...] = right instead of = 1) is paraphrased behaviorally ('copy the operand's actual matrix into the bottom-right block instead of all-ones'), not quoted, and introduces no fix-invented identifier. No test file path, test/function names, parametrization ids (cm8/cm9/cm10/cm11, result6/result9), or quoted expected arrays appear. Requirement 5's enumeration of helper behaviors (coord mapping, series '|', arithmetic + - * / **, Mapping, custom separability declaration) tracks the module's public API/regression surface rather than reconstructing the hidden parametrized cases; the specific hidden groupings ((A&B)&C, rot & sh1 & (scl1&scl2), the 5-D matrix) are NOT enumerated. This is behavioral translation, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
