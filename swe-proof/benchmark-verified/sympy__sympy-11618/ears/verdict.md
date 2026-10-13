# P2 adversarial audit — sympy__sympy-11618

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (weak.diff) zero-extends only when self is the shorter point, matching zip fall-through otherwise. It gives Point2D(2,0).distance(Point3D(1,0,2))==sqrt(5) but Point3D(1,0,2).distance(Point2D(2,0))==1 (drops the extra coord), violating Req1.4 'in either direction' and Req1.5. Probes 1,2,3 reject it.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req1.4 (positive control): distance((2,0),(1,0,2)) == sqrt(5) in either direction.
import sys
from sympy.geometry import Point2D, Point3D
from sympy import sqrt

p2 = Point2D(2, 0)
p3 = Point3D(1, 0, 2)
d1 = p2.distance(p3)
d2 = p3.distance(p2)
print("Point2D(2,0).distance(Point3D(1,0,2)) =", d1)
print("Point3D(1,0,2).distance(Point2D(2,0)) =", d2)
expected = sqrt(5)
ok = (d1 == expected) and (d2 == expected)
print("expected", expected, "ok", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req1.1-1.3: differing-dimension distance = sqrt(sum of squared diffs over larger count,
# zero-extending the shorter point. Example (1,2) vs (4,6,3): (1,2,0) -> 9+16+9=34.
import sys
from sympy.geometry import Point2D, Point3D
from sympy import sqrt

p2 = Point2D(1, 2)
p3 = Point3D(4, 6, 3)
d = p2.distance(p3)
expected = sqrt(34)
print("distance =", d, "expected", expected)
ok = (d == expected) and (p3.distance(p2) == expected)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req1.5: must NOT discard the extra coordinate of the higher-dimensional point.
# Choose a case where only the extra coord contributes: (0,0) vs (0,0,7) -> 7.
import sys
from sympy.geometry import Point2D, Point3D

p2 = Point2D(0, 0)
p3 = Point3D(0, 0, 7)
d = p2.distance(p3)
print("distance((0,0),(0,0,7)) =", d)
ok = (d == 7) and (p3.distance(p2) == 7)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req2.1/2.2: same-dimension distance unchanged. (0,0)-(3,4)=5; 3D (1,1,1)-(2,3,4)=sqrt(14).
import sys
from sympy.geometry import Point2D, Point3D
from sympy import sqrt

d2 = Point2D(0, 0).distance(Point2D(3, 4))
d3 = Point3D(1, 1, 1).distance(Point3D(2, 3, 4))
print("2D:", d2, "3D:", d3)
ok = (d2 == 5) and (d3 == sqrt(14))
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req2.3: symbolic point distance to origin == sqrt(x**2+y**2).
# Req2.4: accept a plain sequence as p.
import sys
from sympy.geometry import Point2D
from sympy import sqrt, symbols, simplify

x, y = symbols('x y')
d = Point2D(x, y).distance(Point2D(0, 0))
print("symbolic distance:", d)
ok_sym = simplify(d - sqrt(x**2 + y**2)) == 0

# plain sequence argument, same dimension
d_seq = Point2D(0, 0).distance((3, 4))
print("distance to plain seq (3,4):", d_seq)
ok_seq = (d_seq == 5)

print("ok_sym", ok_sym, "ok_seq", ok_seq)
sys.exit(0 if (ok_sym and ok_seq) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req3: unrelated Point behavior preserved: collinearity (3D) and transform, basic properties.
import sys
from sympy.geometry import Point2D, Point3D
from sympy import Rational

# collinearity spatial
coll = Point3D.are_collinear(Point3D(0,0,0), Point3D(1,1,1), Point3D(2,2,2))
noncoll = Point3D.are_collinear(Point3D(0,0,0), Point3D(1,1,1), Point3D(1,0,0))
print("collinear:", coll, "non-collinear:", noncoll)

# transform / translate
p = Point2D(1, 2).translate(3, 4)
print("translate:", p)

# basic properties
q = Point3D(1, 2, 3)
props = (q.x == 1 and q.y == 2 and q.z == 3)
print("props:", props)

ok = coll and (not noncoll) and (p == Point2D(4, 6)) and props
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
#!/usr/bin/env python
# Req1.4 (positive control): distance((2,0),(1,0,2)) == sqrt(5) in either direction.
import sys
from sympy.geometry import Point2D, Point3D
from sympy import sqrt

p2 = Point2D(2, 0)
p3 = Point3D(1, 0, 2)
d1 = p2.distance(p3)
d2 = p3.distance(p2)
print("Point2D(2,0).distance(Point3D(1,0,2)) =", d1)
print("Point3D(1,0,2).distance(Point2D(2,0)) =", d2)
expected = sqrt(5)
ok = (d1 == expected) and (d2 == expected)
print("expected", expected, "ok", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes covering: Req1.4 example both directions (probe_1, positive control); Req1.1-1.3 zero-extension sum-over-larger-count (probe_2, 34); Req1.5 no discard of extra coord (probe_3, (0,0)-(0,0,7)=7); Req2.1-2.2 same-dim unchanged (probe_4); Req2.3 symbolic + Req2.4 plain-sequence arg (probe_5); Req3 collinearity/transform/basic props preserved (probe_6). All 6 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base (base gives distance 1, not sqrt(5)) — discriminates. Candidate patch weak.diff applies at base and is REJECTED by probes 1/2/3 while passing 4/5/6, demonstrating the suite discriminates a plausible partial fix. Env: SBU_PYTHON=swebench-lean conda; runs in /testbed image.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (weak.diff) zero-extends only when self is the shorter point, matching zip fall-through otherwise. It gives Point2D(2,0).distance(Point3D(1,0,2))==sqrt(5) but Point3D(1,0,2).distance(Point2D(2,0))==1 (drops the extra coord), violating Req1.4 'in either direction' and Req1.5. Probes 1,2,3 reject it.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
#!/usr/bin/env python
# Req1.4 (positive control): distance((2,0),(1,0,2)) == sqrt(5) in either direction.
import sys
from sympy.geometry import Point2D, Point3D
from sympy import sqrt

p2 = Point2D(2, 0)
p3 = Point3D(1, 0, 2)
d1 = p2.distance(p3)
d2 = p3.distance(p2)
print("Point2D(2,0).distance(Point3D(1,0,2)) =", d1)
print("Point3D(1,0,2).distance(Point2D(2,0)) =", d2)
expected = sqrt(5)
ok = (d1 == expected) and (d2 == expected)
print("expected", expected, "ok", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes covering: Req1.4 example both directions (probe_1, positive control); Req1.1-1.3 zero-extension sum-over-larger-count (probe_2, 34); Req1.5 no discard of extra coord (probe_3, (0,0)-(0,0,7)=7); Req2.1-2.2 same-dim unchanged (probe_4); Req2.3 symbolic + Req2.4 plain-sequence arg (probe_5); Req3 collinearity/transform/basic props preserved (probe_6). All 6 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base (base gives distance 1, not sqrt(5)) — discriminates. Candidate patch weak.diff applies at base and is REJECTED by probes 1/2/3 while passing 4/5/6, demonstrating the suite discriminates a plausible partial fix. Env: SBU_PYTHON=swebench-lean conda; runs in /testbed image.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patched behavior confirmed via nl_attack probe (exit 0, all asserts pass); base commit violates (Req-4 case returns 1, AssertionError). Requirements accurately describe the new max-dimension zero-extension semantics while preserving equal-dimension behavior.

Counterexample / evidence:

```
None found. Probed possible weak spot: a differing-LENGTH plain tuple arg (Point(2,0).distance((1,0,2))) raises AttributeError in the patched code, but the requirements do not claim this works — Req 2.4 only promises sequences are accepted (same-length sequences do compute correctly), so this is not a divergence between requirements and patched code.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All concrete content in requirements.md is public. The sqrt(5) example (Point(2,0).distance(Point(1,0,2))==sqrt(5)) is verbatim from the problem_statement; the symbolic sqrt(x**2+y**2) case comes from the distance() docstring (visible in gold patch context, and standard public API doc). Naming Point/Point2D/Point3D and the distance method is legitimate localization. The gold-invented identifiers (p1, p2 temporaries, zero-extension loop) are described only as behavior ('treat missing coordinate as 0', 'distance over larger coordinate count'), not transmitted. Requirement 3's preservation clauses (collinearity, coordinate transform, construction) loosely parallel the PASS_TO_PASS categories (test_issue_9214/are_collinear, test_transform, test_Point2D/test_point3D) but are generic 'don't regress' statements — no test names, paths, parametrization ids, or quoted test/gold code. The single FAIL_TO_PASS (test_issue_11617) asserts exactly the public example. No semantic reconstruction of the hidden tests beyond the public spec.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
