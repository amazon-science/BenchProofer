# P2 adversarial audit — sympy__sympy-17655

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control + Req1.1: k*point (int) returns a Point with each coord scaled by k."""
import sys
from sympy.geometry import Point
from sympy.geometry.point import Point2D

p = Point(1, 2)
r = 2 * p
print("2*Point(1,2) =", repr(r), "type", type(r).__name__)
ok = isinstance(r, Point) and r == Point(2, 4)
print("is Point and equals Point(2,4):", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.2/1.4: k*point == point*k for int and float, 2D."""
import sys
from sympy.geometry import Point

p = Point(3, 5)
cases = [2, 3, -4, 2.0, 0.5]
ok = True
for k in cases:
    left = k * p
    right = p * k
    eq = (left == right)
    print("k=%r  left=%r  right=%r  equal=%s" % (k, left, right, eq))
    if not eq:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.3: works for 3D too; result same concrete type and dimension as operand."""
import sys
from sympy.geometry import Point
from sympy.geometry.point import Point2D, Point3D

p2 = Point(1, 2)
p3 = Point(1, 2, 3)
r2 = 3 * p2
r3 = 3 * p3
print("3*p2 =", repr(r2), type(r2).__name__)
print("3*p3 =", repr(r3), type(r3).__name__)
ok = (isinstance(r2, Point2D) and r2 == Point(3, 6) and len(r2) == 2
      and isinstance(r3, Point3D) and r3 == Point(3, 6, 9) and len(r3) == 3)
print("type/dim preserved and correct scaling:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2: point_a + k*point_b == point_a + point_b*k and does not raise."""
import sys
from sympy.geometry import Point

a = Point(1, 1)
b = Point(2, 3)
try:
    left = a + 2 * b
except Exception as e:
    print("left form raised:", repr(e))
    sys.exit(1)
right = a + b * 2
print("a + 2*b =", repr(left))
print("a + b*2 =", repr(right))
ok = (left == right == Point(5, 7))
print("equal and correct:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3: regressions preserved — right mul, division, add/sub/neg, dot, indexing,
plain-number add raises, and SymPy-scalar left-mul is NOT turned into a Point."""
import sys
from sympy import sympify, Integer
from sympy.geometry import Point
from sympy.core.mul import Mul

ok = True
def check(name, cond):
    global ok
    print(name, "->", cond)
    if not cond:
        ok = False

p = Point(4, 6)
q = Point(1, 2)

check("right mul", (p * 2) == Point(8, 12))
check("division", (p / 2) == Point(2, 3))
check("addition", (p + q) == Point(5, 8))
check("subtraction", (p - q) == Point(3, 4))
check("negation", (-p) == Point(-4, -6))
check("equality", (Point(4, 6) == p))
check("indexing", (p[0] == 4 and p[1] == 6))
check("len", (len(p) == 2))
check("iteration", (list(p) == [p[0], p[1]]))
check("dot", (p.dot(q) == 4*1 + 6*2))

# 3.4: point + plain number raises
raised = False
try:
    _ = p + 5
except Exception:
    raised = True
check("point + plain number raises", raised)

# left mul by SymPy scalar must NOT become a Point (dispatch through sympy object)
r = sympify(2.0) * p
check("sympify(2.0)*Point stays non-Point (Mul)", not isinstance(r, Point))

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req1.1: k*point (int) returns a Point with each coord scaled by k."""
import sys
from sympy.geometry import Point
from sympy.geometry.point import Point2D

p = Point(1, 2)
r = 2 * p
print("2*Point(1,2) =", repr(r), "type", type(r).__name__)
ok = isinstance(r, Point) and r == Point(2, 4)
print("is Point and equals Point(2,4):", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: make scalar*point commutative for built-in python int/float (gold adds Point.__rmul__ = __mul__).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1 + positive control): 2*Point(1,2)==Point(2,4), is a Point. HOLDS patched, FAILS at base (TypeError int*Point2D) => discriminates.
- probe_2 (Req1.2/1.4): k*point==point*k for k in {2,3,-4,2.0,0.5}. HOLDS patched.
- probe_3 (Req1.3): 3*p works for 2D and 3D, preserves concrete type (Point2D/Point3D) and dimension. HOLDS patched.
- probe_4 (Req2.1/2.2): point_a + k*point_b == point_a + point_b*k and does not raise. HOLDS patched, FAILS at base.
- probe_5 (Req3.1-3.5 regressions): right-mul, division, add/sub/neg, equality, indexing, len, iteration, dot all preserved; point+plain-number still raises; sympify(2.0)*Point stays a non-Point Mul (SymPy-scalar left-mul unchanged). HOLDS patched.

Candidate wrong-fix (identity_rmul: __rmul__ returns self, ignoring factor): REJECTED by probes 1,2,3,4 (returns unscaled point). probe_5 still holds under it (regressions untouched), confirming the suite's scaling probes are what catch the wrong fix. Suite discriminates wrong implementations.

Verdict SOUND: 5 distinct probes hold on patched tree, positive control fails at base (prepatch reproduced), and a plausibly-wrong requirements-adjacent candidate is rejected by the probe suite.

Note (informational, not a G-EQ violation): G-PANEL-2 separately flags the spec as slightly generous re: Integer(2)*Point raising AttributeError on gold — but the requirements explicitly scope the new left-mul behavior to built-in python int/float only, and probe_5 confirms sympify-scalar left-mul is unchanged, so the spec is faithful for G-EQ purposes.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req1.1: k*point (int) returns a Point with each coord scaled by k."""
import sys
from sympy.geometry import Point
from sympy.geometry.point import Point2D

p = Point(1, 2)
r = 2 * p
print("2*Point(1,2) =", repr(r), "type", type(r).__name__)
ok = isinstance(r, Point) and r == Point(2, 4)
print("is Point and equals Point(2,4):", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: make scalar*point commutative for built-in python int/float (gold adds Point.__rmul__ = __mul__).

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1 + positive control): 2*Point(1,2)==Point(2,4), is a Point. HOLDS patched, FAILS at base (TypeError int*Point2D) => discriminates.
- probe_2 (Req1.2/1.4): k*point==point*k for k in {2,3,-4,2.0,0.5}. HOLDS patched.
- probe_3 (Req1.3): 3*p works for 2D and 3D, preserves concrete type (Point2D/Point3D) and dimension. HOLDS patched.
- probe_4 (Req2.1/2.2): point_a + k*point_b == point_a + point_b*k and does not raise. HOLDS patched, FAILS at base.
- probe_5 (Req3.1-3.5 regressions): right-mul, division, add/sub/neg, equality, indexing, len, iteration, dot all preserved; point+plain-number still raises; sympify(2.0)*Point stays a non-Point Mul (SymPy-scalar left-mul unchanged). HOLDS patched.

Candidate wrong-fix (identity_rmul: __rmul__ returns self, ignoring factor): REJECTED by probes 1,2,3,4 (returns unscaled point). probe_5 still holds under it (regressions untouched), confirming the suite's scaling probes are what catch the wrong fix. Suite discriminates wrong implementations.

Verdict SOUND: 5 distinct probes hold on patched tree, positive control fails at base (prepatch reproduced), and a plausibly-wrong requirements-adjacent candidate is rejected by the probe suite.

Note (informational, not a G-EQ violation): G-PANEL-2 separately flags the spec as slightly generous re: Integer(2)*Point raising AttributeError on gold — but the requirements explicitly scope the new left-mul behavior to built-in python int/float only, and probe_5 confirms sympify-scalar left-mul is unchanged, so the spec is faithful for G-EQ purposes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary is correctly pinned to the changed observable behavior (left multiplication by a built-in int/float), not a narrow helper/branch. R3 preservation clauses match existing behavior. No forbidden/invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate the public problem_statement (left-multiplication of a geometry Point by a Python number should equal right-multiplication, so `point1 + number*point2` stops raising) into behavioral EARS criteria. Nothing derivable only from the hidden material is transmitted: the fix-invented identifier `__rmul__` is never named (described behaviorally as 'compute k*point by the same coordinate-scaling procedure used for right-side multiplication'); no test names (test_point/test_point3D), file paths, parametrization ids, or verbatim test/gold lines appear. The int/float scoping and the SymPy-scalar caveat (Req 1 note) follow from Python operator-dispatch semantics and the problem_statement's own `sympify(2.0)*point2` example, not from any hidden test. The 2D/3D coverage mirrors the public API (Point2D/Point3D), not the test parametrization. Req 3.5's enumeration (equality, iteration, indexing, length, dimension normalization, dot product, transforms) lists standard public Point methods readable from point.py; it loosely echoes some PASS_TO_PASS names (test_dot, test_transform, test__normalize_dimension) but is a generic no-regression statement, not a reconstruction of hidden test ids. Naming the module/class is legitimate localization.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
