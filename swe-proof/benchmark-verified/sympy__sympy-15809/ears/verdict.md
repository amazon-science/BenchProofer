# P2 adversarial audit — sympy__sympy-15809

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

Counterexample / evidence:

```
Naive fix `if not args: return S.Zero` avoids the ValueError (satisfies Req1.3) but returns 0 for both Max() and Min(); probe_1 (Req1.1/1.2: Max()==-oo, Min()==oo) REJECTS it. Suite discriminates.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from sympy import Max, Min, S

ok = True
try:
    mx = Max()
    mn = Min()
except Exception as e:
    print("RAISED:", repr(e))
    sys.exit(1)

print("Max() =", mx, "Min() =", mn)
if mx != S.NegativeInfinity:
    print("FAIL: Max() should be -oo"); ok = False
if mn != S.Infinity:
    print("FAIL: Min() should be oo"); ok = False
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sympy import Max, Min

# Req1.3: no exception for empty-arg case
try:
    Max()
    Min()
    print("OK: no exception raised for Max()/Min()")
    sys.exit(0)
except Exception as e:
    print("FAIL raised:", repr(e))
    sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sympy import Max, Min
from sympy.abc import x

# Req2: single-argument returns that argument
ok = True
if Max(x) != x:
    print("FAIL Max(x) !=x:", Max(x)); ok = False
if Min(x) != x:
    print("FAIL Min(x) !=x:", Min(x)); ok = False
if Max(5) != 5:
    print("FAIL Max(5):", Max(5)); ok = False
print("Max(x)=", Max(x), "Min(x)=", Min(x))
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sympy import Max, Min
from sympy.abc import x, y, z

# Req3.1 & 3.2: symmetry + associativity/order independence
ok = True
if Min(x, y) != Min(y, x): print("FAIL Min sym"); ok=False
if Max(x, y) != Max(y, x): print("FAIL Max sym"); ok=False
if Min(x, Min(y, z)) != Min(x, y, z): print("FAIL Min assoc"); ok=False
if Min(z, y, x) != Min(x, y, z): print("FAIL Min order"); ok=False
if Max(x, Max(y, z)) != Max(x, y, z): print("FAIL Max assoc"); ok=False
print("symmetry/associativity checks done, ok=", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sympy import Max, Min, Heaviside, Piecewise, Symbol, oo
from sympy.abc import x, y

ok = True
# Req3.3: numeric collapse
if Max(1, 2, 3) != 3: print("FAIL Max(1,2,3)"); ok=False
if Min(1, 2, 3) != 1: print("FAIL Min(1,2,3)"); ok=False
# redundant collapsing
if Max(x, x, y) != Max(x, y): print("FAIL redundant collapse"); ok=False
# Req3.5: rewrite into Heaviside
r = Max(x, y).rewrite(Heaviside)
print("Max rewrite Heaviside:", r)
if r == Max(x, y):
    print("FAIL rewrite unchanged (no rewrite happened)"); ok=False
# Req3.4: assumptions from args
p = Max(Symbol('a', positive=True), Symbol('b', positive=True))
if p.is_positive is not True:
    print("FAIL Max positive assumption:", p.is_positive); ok=False
print("ok=", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy import Max, Min, S

ok = True
try:
    mx = Max()
    mn = Min()
except Exception as e:
    print("RAISED:", repr(e))
    sys.exit(1)

print("Max() =", mx, "Min() =", mn)
if mx != S.NegativeInfinity:
    print("FAIL: Max() should be -oo"); ok = False
if mn != S.Infinity:
    print("FAIL: Min() should be oo"); ok = False
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes cover: probe_1 Req1.1/1.2 (Max()=-oo, Min()=oo); probe_2 Req1.3 (no exception on empty); probe_3 Req2 (single-arg identity); probe_4 Req3.1/3.2 (symmetry+associativity/order); probe_5 Req3.3/3.4/3.5 (numeric+redundant collapse, positive assumption propagation, Heaviside rewrite). PATCHED: all 5 exit 0. BASE: probe_1 & probe_2 exit 1 (positive control discriminates — empty-arg raised ValueError at base), probe_3 holds at base (single-arg unchanged, as expected). WEAK (return S.Zero): probe_1 REJECTS (exit 1), others pass — demonstrates the suite catches the wrong identity value. Gold patch simply removes the `if not args: raise ValueError` guard so empty args fall through to `cls.identity` (Max.identity=-oo, Min.identity=oo). Verdict SOUND: >=5 probes hold patched, positive control discriminates base vs patched, and >=1 wrong-fix candidate is rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Naive fix `if not args: return S.Zero` avoids the ValueError (satisfies Req1.3) but returns 0 for both Max() and Min(); probe_1 (Req1.1/1.2: Max()==-oo, Min()==oo) REJECTS it. Suite discriminates.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy import Max, Min, S

ok = True
try:
    mx = Max()
    mn = Min()
except Exception as e:
    print("RAISED:", repr(e))
    sys.exit(1)

print("Max() =", mx, "Min() =", mn)
if mx != S.NegativeInfinity:
    print("FAIL: Max() should be -oo"); ok = False
if mn != S.Infinity:
    print("FAIL: Min() should be oo"); ok = False
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes cover: probe_1 Req1.1/1.2 (Max()=-oo, Min()=oo); probe_2 Req1.3 (no exception on empty); probe_3 Req2 (single-arg identity); probe_4 Req3.1/3.2 (symmetry+associativity/order); probe_5 Req3.3/3.4/3.5 (numeric+redundant collapse, positive assumption propagation, Heaviside rewrite). PATCHED: all 5 exit 0. BASE: probe_1 & probe_2 exit 1 (positive control discriminates — empty-arg raised ValueError at base), probe_3 holds at base (single-arg unchanged, as expected). WEAK (return S.Zero): probe_1 REJECTS (exit 1), others pass — demonstrates the suite catches the wrong identity value. Gold patch simply removes the `if not args: raise ValueError` guard so empty args fall through to `cls.identity` (Max.identity=-oo, Min.identity=oo). Verdict SOUND: >=5 probes hold patched, positive control discriminates base vs patched, and >=1 wrong-fix candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch simply deletes the `if not args: raise ValueError` guard in MinMaxBase.__new__, so zero args flow into LatticeOp which returns the identity element (-oo for Max, oo for Min) and the single/multi-arg paths are untouched. The requirements model exactly this: R1 pins the new zero-arg behavior (the changed observable), R2/R3 pin the unchanged behavior as regression guards. Boundary is correct — R1 targets the actual changed behavior (empty-set identity), not a narrower slice. Requirement wording matches issue (return oo/-oo). FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirement 1 (Max()=-oo, Min()=oo, no ValueError) is fully public via problem_statement (which cites the extended-reals rationale). The gold patch is a pure deletion of the empty-arg guard, inventing no identifiers; MinMaxBase/Max/Min/module path and real_root are legitimate localization (real_root even appears in the gold patch context). Requirement 2 (single-arg returns itself) restates the new test asserts Min(x)==x/Max(x)==x as behavior, not as test code/names. Requirement 3's preservation enumeration (symmetry, associativity, assumptions, Heaviside/Piecewise/Abs rewrites, root/real_root, instantiation) loosely tracks the PASS_TO_PASS areas and is the closest call, but each is a genuine public Max/Min behavior stated as 'such as' examples of a general no-regression clause — no test names, paths, parametrization ids, quoted test/gold code, or fix-invented identifiers, and the issue-number regression tests are not enumerated. This is sanctioned test-to-behavior translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
