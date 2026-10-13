# P2 adversarial audit — sympy__sympy-18211

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 3/3 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 3 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 3: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control + Req1.1/1.2/1.3: transcendental relation falls back to ConditionSet.
Holds patched, fails at base (raises NotImplementedError)."""
import sys
from sympy import Symbol, cos, sin, Eq, S
from sympy.sets.conditionset import ConditionSet

x = Symbol('x')
rel = Eq(x*cos(x) - 3*sin(x), 0)
try:
    got = rel.as_set()
except NotImplementedError as e:
    print("FAIL: as_set raised NotImplementedError:", e)
    sys.exit(1)

print("got:", got, type(got))
expected = ConditionSet(x, rel, S.Reals)
if got != expected:
    print("FAIL: not equal to ConditionSet(x, rel, S.Reals):", expected)
    sys.exit(1)
if not isinstance(got, ConditionSet):
    print("FAIL: not a ConditionSet instance")
    sys.exit(1)
print("PASS: returned ConditionSet equal to expected")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.2: solvable strict/non-strict inequalities bounding x -> intervals, NOT ConditionSet."""
import sys
from sympy import Symbol, S, Interval, oo
from sympy.sets.conditionset import ConditionSet

x = Symbol('x')
cases = [
    (x > 0, Interval(0, oo, True, True)),
    (x >= 0, Interval(0, oo, False, True)),
    (x < 0, Interval(-oo, 0, True, True)),
    (x <= 0, Interval(-oo, 0, True, False)),
]
ok = True
for rel, exp in cases:
    got = rel.as_set()
    print(rel, "->", got, "expected", exp)
    if isinstance(got, ConditionSet):
        print("FAIL: got ConditionSet fallback for", rel); ok = False
    if got != exp:
        print("FAIL: mismatch for", rel); ok = False
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.3: solvable equality -> FiniteSet, NOT ConditionSet."""
import sys
from sympy import Symbol, Eq, FiniteSet
from sympy.sets.conditionset import ConditionSet

x = Symbol('x')
got = Eq(x, 0).as_set()
print("Eq(x,0).as_set() ->", got, type(got))
if isinstance(got, ConditionSet):
    print("FAIL: ConditionSet fallback"); sys.exit(1)
if got != FiniteSet(0):
    print("FAIL: expected FiniteSet(0)"); sys.exit(1)
print("PASS"); sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.4: solvable Ne -> real line minus point (union of open intervals), NOT ConditionSet."""
import sys
from sympy import Symbol, Ne, Interval, oo, Union
from sympy.sets.conditionset import ConditionSet

x = Symbol('x')
got = Ne(x, 0).as_set()
exp = Union(Interval(-oo, 0, True, True), Interval(0, oo, True, True))
print("Ne(x,0).as_set() ->", got, "expected", exp)
if isinstance(got, ConditionSet):
    print("FAIL: ConditionSet fallback"); sys.exit(1)
if got != exp:
    print("FAIL: mismatch"); sys.exit(1)
print("PASS"); sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req2.5: solvable polynomial inequality x**2>=4 -> union of intervals, NOT ConditionSet."""
import sys
from sympy import Symbol, Interval, oo, Union
from sympy.sets.conditionset import ConditionSet

x = Symbol('x')
got = (x**2 >= 4).as_set()
exp = Union(Interval(-oo, -2), Interval(2, oo))
print("(x**2>=4).as_set() ->", got, "expected", exp)
if isinstance(got, ConditionSet):
    print("FAIL: ConditionSet fallback"); sys.exit(1)
if got != exp:
    print("FAIL: mismatch"); sys.exit(1)
print("PASS"); sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req1.4: fallback triggered ONLY by NotImplementedError; unrelated errors NOT suppressed.
We monkeypatch solve_univariate_inequality to raise a ValueError and confirm it propagates."""
import sys
import sympy.solvers.inequalities as ineq
from sympy import Symbol, cos, sin, Eq

x = Symbol('x')

orig = ineq.solve_univariate_inequality
def boom(*a, **k):
    raise ValueError("unrelated boom")
ineq.solve_univariate_inequality = boom
try:
    rel = Eq(x*cos(x) - 3*sin(x), 0)
    try:
        rel.as_set()
    except ValueError as e:
        print("PASS: ValueError propagated:", e); sys.exit(0)
    except NotImplementedError:
        print("FAIL: converted to NotImplementedError"); sys.exit(1)
    print("FAIL: no error raised, unrelated error suppressed"); sys.exit(1)
finally:
    ineq.solve_univariate_inequality = orig
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req2.6: single-relation conversion requires univariate (exactly one free symbol).
A multivariate relational's _eval_as_set must not silently succeed."""
import sys
from sympy import Symbol, cos, sin, Eq

x, y = Symbol('x'), Symbol('y')
rel = Eq(x*cos(y) - 3*sin(x), 0)  # two free symbols
try:
    res = rel._eval_as_set()
    print("FAIL: multivariate _eval_as_set returned", res); sys.exit(1)
except (AssertionError, Exception) as e:
    print("PASS: multivariate rejected:", type(e).__name__, e); sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req1.1/1.2/1.3: transcendental relation falls back to ConditionSet.
Holds patched, fails at base (raises NotImplementedError)."""
import sys
from sympy import Symbol, cos, sin, Eq, S
from sympy.sets.conditionset import ConditionSet

x = Symbol('x')
rel = Eq(x*cos(x) - 3*sin(x), 0)
try:
    got = rel.as_set()
except NotImplementedError as e:
    print("FAIL: as_set raised NotImplementedError:", e)
    sys.exit(1)

print("got:", got, type(got))
expected = ConditionSet(x, rel, S.Reals)
if got != expected:
    print("FAIL: not equal to ConditionSet(x, rel, S.Reals):", expected)
    sys.exit(1)
if not isinstance(got, ConditionSet):
    print("FAIL: not a ConditionSet instance")
    sys.exit(1)
print("PASS: returned ConditionSet equal to expected")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover every acceptance criterion:
- probe_1 (Req1.1/1.2/1.3, POSITIVE CONTROL): Eq(x*cos(x)-3*sin(x),0).as_set() returns ConditionSet(x, rel, S.Reals) rather than raising; equals an independently constructed ConditionSet. HOLDS patched, VIOLATED at base (raises NotImplementedError) => discriminates.
- probe_2 (Req2.2): x>0/x>=0/x<0/x<=0 -> correct open/closed unbounded intervals, not ConditionSet. HOLDS patched.
- probe_3 (Req2.3): Eq(x,0) -> FiniteSet(0). HOLDS.
- probe_4 (Req2.4): Ne(x,0) -> Union of open intervals around 0. HOLDS.
- probe_5 (Req2.5): x**2>=4 -> Union(Interval(-oo,-2),Interval(2,oo)). HOLDS.
- probe_6 (Req1.4): only NotImplementedError triggers fallback; a monkeypatched ValueError must propagate. HOLDS patched (and at base). This is the discriminator that rejects the bare-except candidate.
- probe_7 (Req2.6): multivariate relation rejected by _eval_as_set (AssertionError). HOLDS.

All 7 hold on the gold-patched tree.

Candidate patches (all REJECTED by the suite => discriminating):
- weak_always_cs (always returns ConditionSet, never solves): rejected by probe_2,3,4,5,6 (loses exact solvable sets and suppresses unrelated errors).
- weak_bareexcept (except Exception instead of NotImplementedError): rejected by probe_6 (Req1.4 — suppresses unrelated ValueError).
- weak_wrongbase (ConditionSet base S.UniversalSet instead of S.Reals): rejected by probe_1 (Req1.2 — wrong base set / not equal to expected ConditionSet).

Note: meta.json records G-PANEL-3=fail (leakage) — that is a separate leakage judgment (Req2 enumerates exact hidden-test values incl. the x**2>=4 case). It is not an EQ spec-fidelity defect; the requirements are faithful and discriminating, so this G-EQ audit is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 3/3 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 3 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 3: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

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
"""Positive control + Req1.1/1.2/1.3: transcendental relation falls back to ConditionSet.
Holds patched, fails at base (raises NotImplementedError)."""
import sys
from sympy import Symbol, cos, sin, Eq, S
from sympy.sets.conditionset import ConditionSet

x = Symbol('x')
rel = Eq(x*cos(x) - 3*sin(x), 0)
try:
    got = rel.as_set()
except NotImplementedError as e:
    print("FAIL: as_set raised NotImplementedError:", e)
    sys.exit(1)

print("got:", got, type(got))
expected = ConditionSet(x, rel, S.Reals)
if got != expected:
    print("FAIL: not equal to ConditionSet(x, rel, S.Reals):", expected)
    sys.exit(1)
if not isinstance(got, ConditionSet):
    print("FAIL: not a ConditionSet instance")
    sys.exit(1)
print("PASS: returned ConditionSet equal to expected")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

7 probes cover every acceptance criterion:
- probe_1 (Req1.1/1.2/1.3, POSITIVE CONTROL): Eq(x*cos(x)-3*sin(x),0).as_set() returns ConditionSet(x, rel, S.Reals) rather than raising; equals an independently constructed ConditionSet. HOLDS patched, VIOLATED at base (raises NotImplementedError) => discriminates.
- probe_2 (Req2.2): x>0/x>=0/x<0/x<=0 -> correct open/closed unbounded intervals, not ConditionSet. HOLDS patched.
- probe_3 (Req2.3): Eq(x,0) -> FiniteSet(0). HOLDS.
- probe_4 (Req2.4): Ne(x,0) -> Union of open intervals around 0. HOLDS.
- probe_5 (Req2.5): x**2>=4 -> Union(Interval(-oo,-2),Interval(2,oo)). HOLDS.
- probe_6 (Req1.4): only NotImplementedError triggers fallback; a monkeypatched ValueError must propagate. HOLDS patched (and at base). This is the discriminator that rejects the bare-except candidate.
- probe_7 (Req2.6): multivariate relation rejected by _eval_as_set (AssertionError). HOLDS.

All 7 hold on the gold-patched tree.

Candidate patches (all REJECTED by the suite => discriminating):
- weak_always_cs (always returns ConditionSet, never solves): rejected by probe_2,3,4,5,6 (loses exact solvable sets and suppresses unrelated errors).
- weak_bareexcept (except Exception instead of NotImplementedError): rejected by probe_6 (Req1.4 — suppresses unrelated ValueError).
- weak_wrongbase (ConditionSet base S.UniversalSet instead of S.Reals): rejected by probe_1 (Req1.2 — wrong base set / not equal to expected ConditionSet).

Note: meta.json records G-PANEL-3=fail (leakage) — that is a separate leakage judgment (Req2 enumerates exact hidden-test values incl. the x**2>=4 case). It is not an EQ spec-fidelity defect; the requirements are faithful and discriminating, so this G-EQ audit is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness verdict only. The requirements correctly pin the changed behavior at the right boundary (both the new ConditionSet fallback AND the preserved exact-solution path in _eval_as_set). Base vs patched divergence confirmed via probe. NOTE (out of scope for faithfulness): G-PANEL-3 separately failed for LEAKAGE — Requirement 2 criteria 2-5, especially the x**2>=4 -> [-oo,-2]U[2,oo] case with arbitrary constants, reconstruct the hidden PASS_TO_PASS test rather than being derivable from the problem_statement. That is a leakage concern, not a faithfulness one; the requirements remain behaviorally faithful to the patched code.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements stay at the behavioral/localization level. Named entities (Relational._eval_as_set, solve_univariate_inequality, ConditionSet, S.Reals, sympy/core/relational.py) are legitimate change-localization. The central fallback behavior (return ConditionSet(x, self, Reals) instead of raising NotImplementedError for unsolvable univariate relations) is fully public in the problem_statement, including the Eq(n*cos(n)-3*sin(n),0) example. No hidden-test content is transmitted: no test names/paths (test_issue_18188, test_relational.py), no parametrization ids, no gold-invented identifier (the patch's local 'xset'), and crucially NOT the second hidden test case (Eq(x**2+sqrt(x*2)+sin(x),0)). Requirement 2's enumeration (interval open/closed, finite set, Ne union, polynomial root union) describes general preserved solver behavior for the 'preserve existing conversions' clause of the problem statement; the hidden test contains ONLY two equality cases and no inequality/Ne/polynomial cases, so the enumeration mirrors documented behavior rather than reconstructing the test parametrization. No leakage.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
