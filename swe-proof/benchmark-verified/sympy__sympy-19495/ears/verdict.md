# P2 adversarial audit — sympy__sympy-19495

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

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
from sympy import Symbol, ConditionSet, S, Contains, pi, asin, Lambda, Interval
from sympy.sets.sets import imageset
x = Symbol('x'); y = Symbol('y'); k = Symbol('k')
img1 = imageset(Lambda(k, 2*k*pi + asin(y)), S.Integers)
img2 = imageset(Lambda(k, 2*k*pi + asin(S.One/3)), S.Integers)
cs = ConditionSet(x, Contains(y, Interval(-1, 1)), img1)
r_subs = cs.subs(y, S.One/3)
r_xr = cs.xreplace({y: S.One/3})
r_sim = cs.subs({y: S.One/3}, simultaneous=True)
print("subs=", r_subs)
print("xreplace=", r_xr)
print("simultaneous=", r_sim)
ok = (r_subs == r_xr) and (r_subs == r_sim) and r_subs.dummy_eq(img2)
print("subs==xr:", r_subs==r_xr, "subs==sim:", r_subs==r_sim, "dummy_eq img2:", r_subs.dummy_eq(img2))
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
from sympy import Symbol, ConditionSet, S, Contains, pi, asin, Lambda, Reals
from sympy.sets.sets import imageset
from sympy.sets.conditionset import ConditionSet as CS
x = Symbol('x'); y = Symbol('y'); n = Symbol('n')
img = imageset(Lambda(n, 2*n*pi + asin(y)), S.Integers)
cs = ConditionSet(x, Contains(y, Reals), img)
r = cs.subs(y, S.One/3)
print("result =", r, "type=", type(r).__name__)
expected = img.subs(y, S.One/3)
print("expected base subst =", expected)
# must equal the substituted base set, and must NOT be a ConditionSet carrying a Contains condition
is_cs = isinstance(r, CS)
ok = (r == expected) and not is_cs
print("== base-subst:", r == expected, " is ConditionSet:", is_cs)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
from sympy import Symbol, ConditionSet, Interval, oo
n = Symbol('n', negative=True); x = Symbol('x'); p = Symbol('p', positive=True)
cs = ConditionSet(n, n < x, Interval(-oo, 0))
r = cs.subs(x, p)
xr = cs.xreplace({x: p})
print("result =", r, "type=", type(r).__name__)
expected = ConditionSet(n, n < p, Interval(-oo, 0))
ok = (r == expected) and (r == xr) and (r != Interval(-oo,0).__class__() if False else True)
# bound var preserved as n, structure preserved, equals xreplace, and NOT collapsed to EmptySet
from sympy import S
ok = (r == expected) and (r == xr) and (r != S.EmptySet)
print("== expected:", r==expected, " ==xreplace:", r==xr, " !=EmptySet:", r!=S.EmptySet)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
from sympy import Symbol, ConditionSet, Interval, S
x = Symbol('x'); y = Symbol('y')
# base set depends on bound var x; substituting x (the bound var) with number 1 applies only to base set
cs = ConditionSet(x, x < y, Interval(0, x))
r = cs.subs(x, 1)
print("result =", r, "type=", type(r).__name__)
# bound var stays x, condition x<y unchanged, base set becomes Interval(0,1)
ok = (r == ConditionSet(x, x < y, Interval(0, 1)))
print("== ConditionSet(x, x<y, Interval(0,1)):", ok)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
from sympy import Symbol, ConditionSet, S, Interval
x = Symbol('x')
false_cs = ConditionSet(x, S.false, Interval(0, 5))
true_cs = ConditionSet(x, S.true, Interval(0, 5))
print("False->", false_cs, " True->", true_cs)
ok = (false_cs == S.EmptySet) and (true_cs == Interval(0, 5))
print("False==EmptySet:", false_cs==S.EmptySet, " True==base:", true_cs==Interval(0,5))
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
from sympy import Symbol, ConditionSet, Interval, oo
x = Symbol('x'); y = Symbol('y'); z = Symbol('z')
cs = ConditionSet(x, x < y, Interval(0, z))
fs = cs.free_symbols
print("free_symbols =", fs)
# should be {y, z}, exclude bound var x
ok = (fs == {y, z})
print("== {y,z}:", ok, " x excluded:", x not in fs)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
from sympy import Symbol, ConditionSet, S, Contains, pi, asin, Lambda, Interval
from sympy.sets.sets import imageset
x = Symbol('x'); y = Symbol('y'); k = Symbol('k')
img1 = imageset(Lambda(k, 2*k*pi + asin(y)), S.Integers)
img2 = imageset(Lambda(k, 2*k*pi + asin(S.One/3)), S.Integers)
cs = ConditionSet(x, Contains(y, Interval(-1, 1)), img1)
r_subs = cs.subs(y, S.One/3)
r_xr = cs.xreplace({y: S.One/3})
r_sim = cs.subs({y: S.One/3}, simultaneous=True)
print("subs=", r_subs)
print("xreplace=", r_xr)
print("simultaneous=", r_sim)
ok = (r_subs == r_xr) and (r_subs == r_sim) and r_subs.dummy_eq(img2)
print("subs==xr:", r_subs==r_xr, "subs==sim:", r_subs==r_sim, "dummy_eq img2:", r_subs.dummy_eq(img2))
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-19495: gold patch removes the `if cond is S.true: return ConditionSet(new, Contains(new, base), base)` special case in ConditionSet._eval_subs so free-symbol substitution just propagates old->new into condition and base_set via self.func(self.sym, cond, base).

6 probes, all HOLD on the gold-patched tree:
- probe_1 (POSITIVE CONTROL; Req 1.4/1.5): imageset base-set free-symbol subs; cs.subs(y,1/3)==xreplace==subs(simultaneous=True) and dummy_eq(img2). HOLDS patched, VIOLATED at base (base gives ConditionSet(1/3, Contains(1/3, ImageSet...), ImageSet...) which != xreplace). Discriminates.
- probe_2 (Req 1.3/3.1): when the substituted condition becomes True the result is the substituted base set (ImageSet), NOT a Contains-rebound ConditionSet. HOLDS patched, VIOLATED at base.
- probe_3 (Req 1.1/1.2): ConditionSet(n<0-neg, n<x, Interval(-oo,0)).subs(x,p) preserves bound var n and equals xreplace (Interval(-oo,0) kept, was EmptySet at base). HOLDS patched, VIOLATED at base — this is the second hidden-test F2P assertion.
- probe_4 (Req 2.1): subs of bound var x with number 1 applies only to base set, leaving x<y unchanged. Regression, HOLDS.
- probe_5 (Req 3.1): construction collapse False->EmptySet, True->base. Regression, HOLDS.
- probe_6 (Req 4.2): free_symbols excludes bound var. Regression, HOLDS.

CANDIDATE PATCH (weak.diff, applies cleanly at base): keeps the special-case branch but rebinds with self.sym instead of new: `return ConditionSet(self.sym, Contains(self.sym, base), base)`. This is the lazy 'just fix the bound-variable name' reading of Req 1.1's 'preserve original sym'. It is REJECTED by probe_1 and probe_2 (still emits a Contains-wrapped ConditionSet instead of collapsing to the ImageSet base set; subs != xreplace), so it would NOT resolve the hidden imageset F2P assertion. Suite discriminates wrong implementations.

Note on meta.json G-PANEL-2 fail: it flags Req 1.1's prose ('bound variable is the original sym, unchanged') as literally false in the imageset case because __new__ collapses cond=True to the base set (ImageSet with bound var n). That is a faithfulness (G-PANEL-2) nuance, not a G-EQ spec-too-weak/spec-violation issue — Req 1.1 explicitly caveats that the outcome MAY collapse to another form per 1.3/3.1, and my probes encode the actual collapse behavior. For G-EQ purposes: >=6 probes hold on patched, positive control discriminates base vs patched, >=1 requirements-plausible weak candidate is rejected by the suite. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

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
from sympy import Symbol, ConditionSet, S, Contains, pi, asin, Lambda, Interval
from sympy.sets.sets import imageset
x = Symbol('x'); y = Symbol('y'); k = Symbol('k')
img1 = imageset(Lambda(k, 2*k*pi + asin(y)), S.Integers)
img2 = imageset(Lambda(k, 2*k*pi + asin(S.One/3)), S.Integers)
cs = ConditionSet(x, Contains(y, Interval(-1, 1)), img1)
r_subs = cs.subs(y, S.One/3)
r_xr = cs.xreplace({y: S.One/3})
r_sim = cs.subs({y: S.One/3}, simultaneous=True)
print("subs=", r_subs)
print("xreplace=", r_xr)
print("simultaneous=", r_sim)
ok = (r_subs == r_xr) and (r_subs == r_sim) and r_subs.dummy_eq(img2)
print("subs==xr:", r_subs==r_xr, "subs==sim:", r_subs==r_sim, "dummy_eq img2:", r_subs.dummy_eq(img2))
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-19495: gold patch removes the `if cond is S.true: return ConditionSet(new, Contains(new, base), base)` special case in ConditionSet._eval_subs so free-symbol substitution just propagates old->new into condition and base_set via self.func(self.sym, cond, base).

6 probes, all HOLD on the gold-patched tree:
- probe_1 (POSITIVE CONTROL; Req 1.4/1.5): imageset base-set free-symbol subs; cs.subs(y,1/3)==xreplace==subs(simultaneous=True) and dummy_eq(img2). HOLDS patched, VIOLATED at base (base gives ConditionSet(1/3, Contains(1/3, ImageSet...), ImageSet...) which != xreplace). Discriminates.
- probe_2 (Req 1.3/3.1): when the substituted condition becomes True the result is the substituted base set (ImageSet), NOT a Contains-rebound ConditionSet. HOLDS patched, VIOLATED at base.
- probe_3 (Req 1.1/1.2): ConditionSet(n<0-neg, n<x, Interval(-oo,0)).subs(x,p) preserves bound var n and equals xreplace (Interval(-oo,0) kept, was EmptySet at base). HOLDS patched, VIOLATED at base — this is the second hidden-test F2P assertion.
- probe_4 (Req 2.1): subs of bound var x with number 1 applies only to base set, leaving x<y unchanged. Regression, HOLDS.
- probe_5 (Req 3.1): construction collapse False->EmptySet, True->base. Regression, HOLDS.
- probe_6 (Req 4.2): free_symbols excludes bound var. Regression, HOLDS.

CANDIDATE PATCH (weak.diff, applies cleanly at base): keeps the special-case branch but rebinds with self.sym instead of new: `return ConditionSet(self.sym, Contains(self.sym, base), base)`. This is the lazy 'just fix the bound-variable name' reading of Req 1.1's 'preserve original sym'. It is REJECTED by probe_1 and probe_2 (still emits a Contains-wrapped ConditionSet instead of collapsing to the ImageSet base set; subs != xreplace), so it would NOT resolve the hidden imageset F2P assertion. Suite discriminates wrong implementations.

Note on meta.json G-PANEL-2 fail: it flags Req 1.1's prose ('bound variable is the original sym, unchanged') as literally false in the imageset case because __new__ collapses cond=True to the base set (ImageSet with bound var n). That is a faithfulness (G-PANEL-2) nuance, not a G-EQ spec-too-weak/spec-violation issue — Req 1.1 explicitly caveats that the outcome MAY collapse to another form per 1.3/3.1, and my probes encode the actual collapse behavior. For G-EQ purposes: >=6 probes hold on patched, positive control discriminates base vs patched, >=1 requirements-plausible weak candidate is rejected by the suite. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified on gold-patched instance image. Req 1.1's careful wording (may collapse to base set rather than always returning a ConditionSet) correctly captures that self.func()==__new__ collapses a True condition to the base set — matches probe. Modeling boundary is the changed _eval_subs free-symbol path, not a narrower helper/branch. Reqs 2-4 (bound-var subs, construction, membership/equality/free_symbols) describe preserved surrounding behavior consistent with the code and PASS_TO_PASS tests.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes behavior at the same level as the PUBLIC problem_statement, which already contains the full worked example (imageset(Lambda(n, 2*n*pi + asin(y)), S.Integers), ConditionSet(x, Contains(y, Interval(-1,1)), _), .subs(y, Rational(1,3)), and the xreplace / subs(simultaneous=True) equivalence). Nothing in the document is derivable only from the hidden test_patch or gold edit: (1) No test function/class names, file paths, or parametrization ids (e.g. test_subs_CondSet, test_conditionset.py) appear. (2) The hidden test's specific artifacts — Symbol('k'), img1/img2, S.One/3, .dummy_eq(img2), and the CHANGED assertion `ConditionSet(n, n < x, Interval(-oo, 0)).subs(x, p) == Interval(-oo, 0)` (flipped from S.EmptySet) — are NOT reproduced. Requirement 1.3/1.4/1.5 phrase the ImageSet-parameter and xreplace/simultaneous equivalence generically, matching the public statement rather than the test code. (3) No fix-invented identifiers leak; the gold edit invents no new identifiers (it removes the Contains(new, base) special case), and the doc names only pre-existing public API (ConditionSet, _eval_subs, conditionset.py, Contains) — legitimate localization. (4) The acceptance criteria are true behavioral requirements (preserve bound var, propagate old->new into condition/base, no rebind-to-new, no Contains), not an enumeration mirroring parametrized cases. The Interval(-oo,0) test outcome is a consequence of the stated general rule, not a transmitted case value.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
