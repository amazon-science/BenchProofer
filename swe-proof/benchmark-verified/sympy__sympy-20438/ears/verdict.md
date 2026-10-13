# P2 adversarial audit — sympy__sympy-20438

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (Expr guard + ProductSet/FiniteSet is_subset dispatch, but comparison.py left unchanged: Set/Set _eval_is_eq still returns None) is REJECTED by probe_3 (R2.2: Eq(ProductSet({1},{2}), Interval(1,2)) stays unevaluated instead of S.false) and probe_4 (R3.3: Eq(c,b).simplify() stays unevaluated instead of S.true). This candidate would fail the hidden test_Eq/test_issue_19378 assertions.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1.2 (positive control): b.is_subset(c) SHALL be singleton True."""
from sympy import FiniteSet, ProductSet
a = FiniteSet(1, 2)
b = ProductSet(a, a)
c = FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))
res = b.is_subset(c)
print("b.is_subset(c) =", repr(res))
import sys
sys.exit(0 if res is True else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.1 & R1.3: finite ProductSet vs FiniteSet omitting a tuple SHALL be singleton False."""
from sympy import FiniteSet, ProductSet
a = FiniteSet(1, 2)
b = ProductSet(a, a)
d = FiniteSet(1)
res = b.is_subset(d)
print("b.is_subset(FiniteSet(1)) =", repr(res))
# also a partial finite set missing one tuple
c_missing = FiniteSet((1, 1), (1, 2), (2, 1))
res2 = b.is_subset(c_missing)
print("b.is_subset(missing one tuple) =", repr(res2))
import sys
sys.exit(0 if (res is False and res2 is False) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.2: Eq(ProductSet, Interval) SHALL evaluate to singleton False."""
from sympy import ProductSet, Interval, Eq, S, FiniteSet
res = Eq(ProductSet(FiniteSet(1), FiniteSet(2)), Interval(1, 2))
print("Eq(ProductSet({1},{2}), Interval(1,2)) =", repr(res))
import sys
sys.exit(0 if res is S.false else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.3 & R3.4: Eq(c,b).simplify() -> S.true; Eq(a,c).simplify() -> S.false. No error raised (R3.2)."""
from sympy import FiniteSet, ProductSet, Eq, S
a = FiniteSet(1, 2)
b = ProductSet(a, a)
c = FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))
r1 = Eq(c, b).simplify()
r2 = Eq(a, c).simplify()
print("Eq(c,b).simplify() =", repr(r1))
print("Eq(a,c).simplify() =", repr(r2))
import sys
sys.exit(0 if (r1 is S.true and r2 is S.false) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.5 & R3.6: Eq({1},{x}).simplify() returns the equality unchanged (undetermined via free symbol)."""
from sympy import FiniteSet, Eq, Symbol
x = Symbol('x')
e = Eq(FiniteSet(1), FiniteSet(x))
r = e.simplify()
print("Eq({1},{x}).simplify() =", repr(r))
print("original                =", repr(e))
import sys
sys.exit(0 if r == e else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R2.3 regression: kept definite verdicts.
- Eq(ProductSet({1}), ProductSet({1},{2})) is S.false (different #factors)
- Eq(FiniteSet, FiniteSet) equal -> True, unequal -> False
- Eq(Interval, Interval) equal -> True
- Eq(FiniteSet, Interval) -> False
"""
from sympy import FiniteSet, ProductSet, Interval, Eq, S
checks = []
r = Eq(ProductSet(FiniteSet(1)), ProductSet(FiniteSet(1), FiniteSet(2)))
checks.append(("Eq(PS({1}),PS({1},{2}))", r, S.false))
r = Eq(FiniteSet(1, 2), FiniteSet(1, 2))
checks.append(("Eq(FS(1,2),FS(1,2))", r, S.true))
r = Eq(FiniteSet(1, 2), FiniteSet(1, 3))
checks.append(("Eq(FS(1,2),FS(1,3))", r, S.false))
r = Eq(Interval(1, 2), Interval(1, 2))
checks.append(("Eq(I(1,2),I(1,2))", r, S.true))
r = Eq(FiniteSet(1, 2), Interval(1, 2))
checks.append(("Eq(FS(1,2),I(1,2))", r, S.false))
ok = True
for name, got, want in checks:
    good = got is want
    ok = ok and good
    print(f"{name} = {got!r} (want {want!r}) {'OK' if good else 'BAD'}")
import sys
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""R4.3 & R4.4 regression:
- ProductSet iteration yields exactly the cartesian tuples
- FiniteSet/ProductSet contains keeps results
- Simplification of ordinary algebraic Eq keeps behavior: Eq(x, x).simplify() is S.true; Eq(x+x,2*x).simplify() is S.true
"""
from sympy import FiniteSet, ProductSet, Eq, S, Symbol
a = FiniteSet(1, 2)
b = ProductSet(a, a)
tuples = set(iter(b))
expected = {(1, 1), (1, 2), (2, 1), (2, 2)}
print("iter(ProductSet) =", tuples)
ok = tuples == expected
print("contains (1,1):", b.contains((1, 1)), " contains (3,3):", b.contains((3, 3)))
ok = ok and (b.contains((1, 1)) is S.true) and (b.contains((3, 3)) is S.false)
x = Symbol('x')
r1 = Eq(x, x).simplify()
r2 = Eq(x + x, 2 * x).simplify()
print("Eq(x,x).simplify() =", repr(r1), " Eq(x+x,2x).simplify() =", repr(r2))
ok = ok and (r1 is S.true) and (r2 is S.true)
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.2 (positive control): b.is_subset(c) SHALL be singleton True."""
from sympy import FiniteSet, ProductSet
a = FiniteSet(1, 2)
b = ProductSet(a, a)
c = FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))
res = b.is_subset(c)
print("b.is_subset(c) =", repr(res))
import sys
sys.exit(0 if res is True else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover: R1.2 (probe_1, positive control: b.is_subset(c) is True), R1.1/R1.3 (probe_2: False when a tuple is omitted, incl. FiniteSet(1)), R2.2 (probe_3: Eq(ProductSet,Interval) is S.false), R3.2/R3.3/R3.4 (probe_4: Eq(c,b).simplify() S.true, Eq(a,c).simplify() S.false, no crash), R3.5/R3.6 (probe_5: Eq({1},{x}).simplify() unchanged), R2.3 regression (probe_6: PS!=factors, FS/FS, I/I, FS/I kept), R4.3/R4.4 regression (probe_7: ProductSet iter/contains, ordinary-Expr Eq simplify kept). All 7 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base (None) and HOLDS patched (True); probe_4 also crashes with AttributeError at base, confirming the prepatch defect. Weak candidate patch discriminated: rejected by probe_3 and probe_4. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate (Expr guard + ProductSet/FiniteSet is_subset dispatch, but comparison.py left unchanged: Set/Set _eval_is_eq still returns None) is REJECTED by probe_3 (R2.2: Eq(ProductSet({1},{2}), Interval(1,2)) stays unevaluated instead of S.false) and probe_4 (R3.3: Eq(c,b).simplify() stays unevaluated instead of S.true). This candidate would fail the hidden test_Eq/test_issue_19378 assertions.
```

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.2 (positive control): b.is_subset(c) SHALL be singleton True."""
from sympy import FiniteSet, ProductSet
a = FiniteSet(1, 2)
b = ProductSet(a, a)
c = FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))
res = b.is_subset(c)
print("b.is_subset(c) =", repr(res))
import sys
sys.exit(0 if res is True else 1)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover: R1.2 (probe_1, positive control: b.is_subset(c) is True), R1.1/R1.3 (probe_2: False when a tuple is omitted, incl. FiniteSet(1)), R2.2 (probe_3: Eq(ProductSet,Interval) is S.false), R3.2/R3.3/R3.4 (probe_4: Eq(c,b).simplify() S.true, Eq(a,c).simplify() S.false, no crash), R3.5/R3.6 (probe_5: Eq({1},{x}).simplify() unchanged), R2.3 regression (probe_6: PS!=factors, FS/FS, I/I, FS/I kept), R4.3/R4.4 regression (probe_7: ProductSet iter/contains, ordinary-Expr Eq simplify kept). All 7 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base (None) and HOLDS patched (True); probe_4 also crashes with AttributeError at base, confirming the prepatch defect. Weak candidate patch discriminated: rejected by probe_3 and probe_4. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on gold-patched tree: R1.2 b.is_subset(c)=True; R1.3 missing-tuple=False, non-tuple set=False; R2.2 Eq(ProductSet,Interval(0,1))=False; R2.3 Eq(ProductSet(a,a),ProductSet(a))=False, Eq(Interval,Interval) True/False preserved; R3.3 Eq(c,b).simplify()=True; R3.4 Eq(a,c).simplify()=False; R3.5 Eq(FiniteSet(x),FiniteSet(1,2)).simplify() returns unchanged (==original Eq); R3.6/R4 Eq(x+1,2).simplify()=Eq(x,1) single-symbol path intact. The requirements correctly pin the changed observable behavior (subset verdict for finite ProductSet vs FiniteSet, both-ways-containment general set equality, and the non-Expr guard in relational simplify) rather than a narrow internal slice. R2.1 accurately describes the new Set/Set handler = tfn[fuzzy_and(both-way is_subset)]. Boundary is correct.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes behavior and localizes the change to pre-existing real symbols (is_subset_sets in issubset.py, _eval_is_eq in comparison.py, Relational/Equality._eval_simplify in relational.py) — all legitimate. No test names (test_issue_19378, test_Eq), no test file path (sympy/sets/tests/test_sets.py), no parametrization ids, no quoted test/gold code, and no fix-invented identifiers appear. The gold's new dispatch signature (a_ps, b_fs) and its fuzzy_and body are NOT surfaced.

The public problem_statement already exposes: a=FiniteSet(1,2), b=ProductSet(a,a), c=FiniteSet of the four tuples, b.is_subset(c) unknown, c.is_subset(b) True, and the AttributeError on 'Complement' object has no attribute 'equals'. So Req 1.2, Req 3.3, and the Complement/AttributeError detail are all public.

Hidden-only cases DO get translated into requirements — ProductSet vs Interval => False (Req 2.2), ProductSet with differing factor counts => False (Req 2.3), Eq(a,c).simplify() => False (Req 3.4), and the free-symbol undecided case Eq({1},{x}) => unchanged (Req 3.5). But each is stated as abstract behavioral rationale ("a set of tuples and a real interval can never denote the same collection"; "a free symbol leaves a containment direction undetermined") rather than as quoted/enumerated test fixtures. This is exactly the sanctioned activity of translating what tests check into behavioral requirements, not transmitting the tests. Rides close to the line at Req 2.2/2.3/3.5 but stays on the describe-behavior side.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
