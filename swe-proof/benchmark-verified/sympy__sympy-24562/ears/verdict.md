# P2 adversarial audit — sympy__sympy-24562

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
"""Req 1.3 (positive control): Rational('0.5','100') SHALL equal Rational(1,200)."""
import sys
from sympy import Rational

r = Rational('0.5', '100')
expected = Rational(1, 200)
print("Rational('0.5','100') =", r, " as p/q =", (r.p, r.q))
ok = (r == expected) and (r.p == 1) and (r.q == 200)
print("expected 1/200, equal:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1 & 1.2: two-arg Rational(p,q) SHALL equal the exact quotient of the
exact rational values of p and q, for every mixture of int/float/string.
Exact value of a string = Fraction(text); of a float = Fraction(float) (binary);
of an int = the int. Computed independently with stdlib fractions."""
import sys
from fractions import Fraction
from sympy import Rational

def exact(v):
    if isinstance(v, str):
        return Fraction(v)          # decimal or single '/' fraction
    if isinstance(v, float):
        return Fraction(v)          # exact binary value
    if isinstance(v, int):
        return Fraction(v)
    raise TypeError(v)

vals = ['1.5', 1.5, 2, '0.5', 0.5, '100', 3, '3/4']
bad = []
for p in vals:
    for q in vals:
        want = exact(p) / exact(q)
        r = Rational(p, q)
        got = Fraction(r.p, r.q)
        if got != want:
            bad.append((p, q, str(r), str(want)))
if bad:
    print("MISMATCHES:")
    for b in bad[:20]:
        print("  ", b)
else:
    print("all %d combinations equal exact quotient" % (len(vals) ** 2))
sys.exit(0 if not bad else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1: for integer/numeric-string numerator & denominator, two-arg
Rational(p,q) SHALL equal single-string Rational('p/q')."""
import sys
from sympy import Rational

pairs = [(3, 4), ('3', '4'), ('0.5', '100'), ('7', '14'),
         (2, 8), ('1.5', '3'), ('100', '0.5'), ('-2', '4')]
bad = []
for p, q in pairs:
    two = Rational(p, q)
    one = Rational('%s/%s' % (p, q))
    if two != one:
        bad.append((p, q, str(two), str(one)))
if bad:
    print("MISMATCHES two-arg vs single-string:")
    for b in bad:
        print("  ", b)
else:
    print("all %d pairs: two-arg == single-string" % len(pairs))
sys.exit(0 if not bad else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1 & 3.6: two integer args keep returning the reduced quotient with a
positive denominator (e.g. -2/4 -> -1/2), sign normalization unchanged."""
import sys
from sympy import Rational

cases = {(-2, 4): (-1, 2), (2, 4): (1, 2), (6, 3): (2, 1),
         (2, -4): (-1, 2), (-6, -3): (2, 1), (10, 4): (5, 2)}
bad = []
for (p, q), (ep, eq) in cases.items():
    r = Rational(p, q)
    if (r.p, r.q) != (ep, eq) or r.q <= 0:
        bad.append(((p, q), (r.p, r.q), (ep, eq)))
if bad:
    print("MISMATCHES:", bad)
else:
    print("all integer-arg reductions correct with positive denominator")
sys.exit(0 if not bad else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.2 & 3.3: single-argument construction unchanged, and results that
reduce to an integer / one-half return Integer / the Half singleton."""
import sys
from sympy import Rational, Integer, S
from sympy.core.numbers import Half

ok = True
# single-arg unaffected
a = Rational('0.5'); print("Rational('0.5') =", a, type(a).__name__)
ok &= (a == Rational(1, 2))
b = Rational('3/4'); print("Rational('3/4') =", b)
ok &= (b == Rational(3, 4))
c = Rational(0.5); print("Rational(0.5) =", c)
ok &= (c == Rational(1, 2))
# reduces to integer -> Integer instance
d = Rational(4, 2); print("Rational(4,2) =", d, type(d).__name__)
ok &= isinstance(d, Integer) and d == Integer(2)
# reduces to one-half -> Half singleton
e = Rational(2, 4); print("Rational(2,4) is S.Half:", e is S.Half)
ok &= (e is S.Half) and isinstance(e, Half)
# two-arg producing half from strings still Half
f = Rational('0.5', '1'); print("Rational('0.5','1') is S.Half:", f is S.Half)
ok &= (f is S.Half)
print("all single-arg / singleton behavior held:", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.2 discriminator + Req 3.5.
Float-numerator with string denominator must give the exact quotient (the bug's
core: non-integer numerator times a string denominator). And a string with more
than one '/' SHALL keep raising."""
import sys
from fractions import Fraction
from sympy import Rational

ok = True
# float numerator, string denominator -> exact quotient (binary value of float)
r1 = Rational(1.5, '2'); print("Rational(1.5,'2') =", r1)
ok &= Fraction(r1.p, r1.q) == Fraction(1.5) / Fraction(2)   # 3/4
r2 = Rational(0.5, '100'); print("Rational(0.5,'100') =", r2)
ok &= Fraction(r2.p, r2.q) == Fraction(0.5) / Fraction(100)  # 1/200
r3 = Rational('1.5', '1.5'); print("Rational('1.5','1.5') =", r3)
ok &= (r3 == Rational(1, 1))
# more than one '/' still raises
raised = False
try:
    Rational('1/2/3')
except (TypeError, ValueError) as e:
    raised = True; print("Rational('1/2/3') raised:", type(e).__name__)
ok &= raised
print("discriminator + multi-slash behavior held:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 1.3 (positive control): Rational('0.5','100') SHALL equal Rational(1,200)."""
import sys
from sympy import Rational

r = Rational('0.5', '100')
expected = Rational(1, 200)
print("Rational('0.5','100') =", r, " as p/q =", (r.p, r.q))
ok = (r == expected) and (r.p == 1) and (r.q == 200)
print("expected 1/200, equal:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover the requirements. probe_1 (Req 1.3, positive control): Rational('0.5','100')==1/200 — HOLDS patched, VIOLATED at base (1/100100), so it discriminates. probe_2 (Req 1.1/1.2): all 64 mixtures of int/float/string equal the exact stdlib-Fraction quotient. probe_3 (Req 2.1): two-arg == single-string 'p/q' for 8 int/string pairs. probe_4 (Req 3.1/3.6): integer-arg reductions with positive denominator (-2/4->-1/2 etc). probe_5 (Req 3.2/3.3): single-arg unaffected, Integer/S.Half singletons preserved. probe_6 (Req 1.1/1.2 float-num*string-den discriminator + Req 3.5 multi-'/' raises). All 6 HOLD on the gold-patched tree.

Weak-candidate 'drop_qq_factor': applies the gold Q-accumulator refactor but DROPS the `p *= q.q` factor for a fractional denominator. It still fixes Rational('0.5','100')->1/200 (probe_1 PASSES — the lazy fix a narrow reading of Req 1.3 permits), but is REJECTED by probe_2 (e.g. '0.5','3/4' gives 1/6 vs correct 2/3), probe_3 ('100','0.5' gives 100 vs 200), and probe_6 (Rational('1.5','1.5') etc). So the suite discriminates a wrong-but-plausible fix. 1/1 weak candidates rejected. No probe-conforming alternative found; verdict SOUND.

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
"""Req 1.3 (positive control): Rational('0.5','100') SHALL equal Rational(1,200)."""
import sys
from sympy import Rational

r = Rational('0.5', '100')
expected = Rational(1, 200)
print("Rational('0.5','100') =", r, " as p/q =", (r.p, r.q))
ok = (r == expected) and (r.p == 1) and (r.q == 200)
print("expected 1/200, equal:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover the requirements. probe_1 (Req 1.3, positive control): Rational('0.5','100')==1/200 — HOLDS patched, VIOLATED at base (1/100100), so it discriminates. probe_2 (Req 1.1/1.2): all 64 mixtures of int/float/string equal the exact stdlib-Fraction quotient. probe_3 (Req 2.1): two-arg == single-string 'p/q' for 8 int/string pairs. probe_4 (Req 3.1/3.6): integer-arg reductions with positive denominator (-2/4->-1/2 etc). probe_5 (Req 3.2/3.3): single-arg unaffected, Integer/S.Half singletons preserved. probe_6 (Req 1.1/1.2 float-num*string-den discriminator + Req 3.5 multi-'/' raises). All 6 HOLD on the gold-patched tree.

Weak-candidate 'drop_qq_factor': applies the gold Q-accumulator refactor but DROPS the `p *= q.q` factor for a fractional denominator. It still fixes Rational('0.5','100')->1/200 (probe_1 PASSES — the lazy fix a narrow reading of Req 1.3 permits), but is REJECTED by probe_2 (e.g. '0.5','3/4' gives 1/6 vs correct 2/3), probe_3 ('100','0.5' gives 100 vs 200), and probe_6 (Rational('1.5','1.5') etc). So the suite discriminates a wrong-but-plausible fix. 1/1 weak candidates rejected. No probe-conforming alternative found; verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch: two-arg Rational now uses a separate accumulator Q instead of reusing q, so non-integer p/q denominators multiply correctly. Probes on gold-patched tree: Rational('0.5','100')=1/200 (==Rational(1,200)) [Req1.3 ✓], Rational('1.5','2')=3/4=Rational('1.5/2') [Req1.1/2.1 ✓], Rational(2,'0.5')=4 [Req1.2 non-int denom→numer ✓], Rational(Rational(3,4),Rational(2,5))=15/8 [exact quotient ✓], Rational(-2,4)=-1/2 [Req3.1 sign/reduce unchanged ✓], Rational(0.1,2) gives exact binary [Req2.2 ✓], and it correctly does NOT equal Rational('0.1/2') [Req2.2 explicitly allows this]. Requirement boundary is the changed observable behavior (full two-arg exact-quotient), not a narrow branch. The prior G-PANEL-2=fail stamp cited the 0.1/2 float divergence as unfaithful, but the current requirements text (Req 2.2) now correctly models exact-binary float semantics and explicitly does not require float/decimal-string agreement, so that objection is resolved. Req3 preservation clauses hold. No requirement mandates behavior the code lacks, forbids behavior it has, or invents behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the two-arg Rational(p,q) bug and fix behaviorally. Req 1.3 (Rational('0.5','100')==Rational(1,200)) is fully public via problem_statement, which gives both the buggy result (1/100100) and the correct value (1/200). No hidden content transmitted: the test function name (test_issue_24543), its file path (sympy/core/tests/test_numbers.py), the parametrization loop ('1.5',1.5,2)^2, the as_numer_denom() check, and the fix-invented accumulator identifier 'Q' all appear NOWHERE in the doc. The bug is described conceptually ('reused the denominator argument as its own running accumulator'), which is legitimate localization. Requirement 2 (agreement of Rational(p,q) with single-string Rational('p/q')) originates in hints_text (excluded) but is stated as a GENERAL behavioral property over all same-spelling arguments, not as an enumeration of the 9 parametrized cases, so it is a behavioral translation rather than a reconstruction of the test. Line 9's use of '1.5' as an illustrative numeric string coincides with a parametrization value but is a single incidental example, not a case enumeration mirroring the test. No quoted test/gold code, no test ids/names/paths, no fix-invented identifiers.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
