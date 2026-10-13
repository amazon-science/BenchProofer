# P2 adversarial audit — sympy__sympy-13091

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

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control. Req 1.1/1.2/1.4/3.4: when the other operand's __eq__
declares equality (truthy), a sympy object (Basic AND finite numeric)
delegates so == is True symmetrically and != is False symmetrically."""
import sys
from sympy import Symbol, Integer, Rational, Float

class EqAll(object):
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False
    def __hash__(self):
        return 1

ok = True
for name, obj in [("Symbol", Symbol('x')),
                  ("Integer", Integer(1)),
                  ("Rational", Rational(3, 2)),
                  ("Float", Float(1.5))]:
    f = EqAll()
    r1 = (obj == f)
    r2 = (f == obj)
    r3 = (obj != f)
    r4 = (f != obj)
    print(name, "obj==f", r1, "f==obj", r2, "obj!=f", r3, "f!=obj", r4)
    if not (r1 is True and r2 is True and r3 is False and r4 is False):
        ok = False

sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.2: __eq__ returns NotImplemented (not a bool) when other cannot
be sympified. Directly inspect the raw return of the __eq__ method."""
import sys
from sympy import Symbol, Integer, Rational, Float

class Foreign(object):
    # no __eq__ that helps; not sympifiable
    pass

ok = True
targets = [("Basic", Symbol('x')),
           ("Integer", Integer(5)),
           ("Rational", Rational(7, 3)),
           ("Float", Float(2.25))]
for name, obj in targets:
    f = Foreign()
    raw = obj.__eq__(f)
    print(name, "raw __eq__ ->", repr(raw))
    if raw is not NotImplemented:
        ok = False

# NumberSymbol: pi
from sympy import pi
raw = pi.__eq__(Foreign())
print("pi(NumberSymbol) raw __eq__ ->", repr(raw))
if raw is not NotImplemented:
    ok = False

sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.3 / 3.1: when neither side helps, == is False and != is True in both
orders. And an interpretable-but-different operand (Basic vs int 0) is unequal."""
import sys
from sympy import Symbol, Integer

class Foreign(object):
    __hash__ = None if False else object.__hash__

ok = True
x = Symbol('x')
f = Foreign()
# both sides return NotImplemented -> Python falls back to identity
r = [(x == f), (f == x), (x != f), (f != x)]
print("Symbol vs foreign:", r)
if not (r[0] is False and r[1] is False and r[2] is True and r[3] is True):
    ok = False

# Req 3.1: bare Basic-ish Symbol not equal to interpretable int 0
r2 = (x == 0)
r3 = (x != 0)
print("Symbol==0:", r2, "Symbol!=0:", r3)
if not (r2 is False and r3 is True):
    ok = False

# Integer(1) != 0 (interpretable, different content)
i = Integer(1)
print("Integer(1)==0:", i == 0, "Integer(1)!=0:", i != 0)
if not ((i == 0) is False and (i != 0) is True):
    ok = False

sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.2/3.3: recognized equal sympy objects compare == True, != False;
different content == False, != True. Regression preservation."""
import sys
from sympy import Integer, Rational, Symbol, sqrt

ok = True
checks = [
    (Integer(2) == Integer(2), True),
    (Integer(2) != Integer(2), False),
    (Rational(1, 2) == Rational(1, 2), True),
    (Integer(2) == Integer(3), False),
    (Integer(2) != Integer(3), True),
    (Symbol('x') == Symbol('x'), True),
    (Symbol('x') == Symbol('y'), False),
    (sqrt(2) == sqrt(2), True),
]
for got, want in checks:
    print("got", got, "want", want)
    if got != want:
        ok = False

# identity Req 3.3
x = Symbol('z')
print("identity x==x:", x == x)
if (x == x) is not True:
    ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.1: ordering a numeric sympy object against an uninterpretable operand
raises TypeError, for all four operators, finite and non-finite."""
import sys
from sympy import Integer, Rational, Float, oo, zoo, nan

class Foreign(object):
    pass

ok = True
nums = [("Integer", Integer(3)), ("Rational", Rational(3, 2)),
        ("Float", Float(1.5)), ("oo", oo), ("-oo", -oo),
        ("zoo", zoo), ("nan", nan)]
ops = [("<", lambda a, b: a < b), (">", lambda a, b: a > b),
       ("<=", lambda a, b: a <= b), (">=", lambda a, b: a >= b)]
for nm, n in nums:
    for onm, op in ops:
        f = Foreign()
        try:
            res = op(n, f)
            print("FAIL", nm, onm, "-> no TypeError, got", repr(res))
            ok = False
        except TypeError:
            print("ok", nm, onm, "raised TypeError")
        except Exception as e:
            print("FAIL", nm, onm, "raised", type(e).__name__, e)
            ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 5.1/5.2/5.3: symmetric ordering between Rational/Float and NumberSymbol
(pi). The mirrored operator must be used. This is the buggy path fixed by
changing other.__le__ -> other.__lt__ etc."""
import sys
from sympy import Rational, Float, pi, S

ok = True
xs = [("Rational<pi", Rational(3, 1)), ("Rational>pi", Rational(4, 1)),
      ("Float", Float(3.0)), ("Float2", Float(3.5))]

def check(x):
    global ok
    pairs = [
        ("< vs c>", (x < pi), (pi > x)),
        ("<= vs c>=", (x <= pi), (pi >= x)),
        ("> vs c<", (x > pi), (pi < x)),
        (">= vs c<=", (x >= pi), (pi <= x)),
        ("== vs c==", (x == pi), (pi == x)),
        ("!= vs c!=", (x != pi), (pi != x)),
    ]
    for nm, a, b in pairs:
        print(repr(x), nm, "->", a, b)
        if bool(a) != bool(b):
            ok = False

for _, x in xs:
    check(x)

# sanity: correctness of magnitudes: 3 < pi, 4 > pi
print("3<pi:", Rational(3) < pi, "4>pi:", Rational(4) > pi)
if not (bool(Rational(3) < pi) is True and bool(Rational(4) > pi) is True):
    ok = False

sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 3.5: non-finite (oo,-oo,zoo,nan) vs foreign obj declaring 'not equal to
infinities/NaN' -> == False symmetric, != True symmetric. Also preserves
existing special-value equality (oo==oo True, nan==nan False)."""
import sys
from sympy import oo, zoo, nan, S

class NotInf(object):
    def __eq__(self, other):
        return False
    def __ne__(self, other):
        return True
    def __hash__(self):
        return 0

ok = True
for nm, v in [("oo", oo), ("-oo", -oo), ("zoo", zoo), ("nan", nan)]:
    f = NotInf()
    r = [(v == f), (f == v), (v != f), (f != v)]
    print(nm, "==f,f==,!=f,f!=:", r)
    if not (r[0] is False and r[1] is False and r[2] is True and r[3] is True):
        ok = False

# preserved special-value semantics
print("oo==oo:", oo == oo, "oo!=1:", oo != S(1))
if (oo == oo) is not True:
    ok = False

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control. Req 1.1/1.2/1.4/3.4: when the other operand's __eq__
declares equality (truthy), a sympy object (Basic AND finite numeric)
delegates so == is True symmetrically and != is False symmetrically."""
import sys
from sympy import Symbol, Integer, Rational, Float

class EqAll(object):
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False
    def __hash__(self):
        return 1

ok = True
for name, obj in [("Symbol", Symbol('x')),
                  ("Integer", Integer(1)),
                  ("Rational", Rational(3, 2)),
                  ("Float", Float(1.5))]:
    f = EqAll()
    r1 = (obj == f)
    r2 = (f == obj)
    r3 = (obj != f)
    r4 = (f != obj)
    print(name, "obj==f", r1, "f==obj", r2, "obj!=f", r3, "f!=obj", r4)
    if not (r1 is True and r2 is True and r3 is False and r4 is False):
        ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy-13091: rich-comparison methods must return NotImplemented (not False) when the other operand is not sympifiable, so == / != become symmetric with foreign user classes; __ne__ must negate the OPERATOR (not self==other) not the raw __eq__; and Number-vs-NumberSymbol ordering must use the correctly-mirrored operator.

Probes (all HOLD on gold-patched tree; runner suppresses probe stdout so observations were confirmed via a local diag variant writing to stderr):
- probe_1 (Req 1.1/1.2/1.4/3.4, POSITIVE CONTROL): a foreign class whose __eq__ returns True compares == True and != False symmetrically against Symbol, Integer, Rational, Float. HOLDS patched, VIOLATED at base (prepatch_reproduced=true) -> discriminating power confirmed.
- probe_2 (Req 1.1/1.2): raw obj.__eq__(foreign) returns the NotImplemented singleton for Basic/Integer/Rational/Float and pi (NumberSymbol). HOLDS patched, VIOLATED at base.
- probe_3 (Req 1.3/3.1): neither-side-helps -> ==False/!=True both orders; Symbol vs int 0 and Integer(1) vs 0 unequal. HOLDS.
- probe_4 (Req 3.2/3.3): recognized equal objects ==True/!=False, different content ==False, identity ==True. HOLDS.
- probe_5 (Req 4.1): ordering (< > <= >=) of Integer/Rational/Float/oo/-oo/zoo/nan against a foreign object raises TypeError for all 4 ops. HOLDS.
- probe_6 (Req 5.1/5.2/5.3): Rational/Float vs pi ordering is symmetric with the mirrored operator ((x<c)==(c>x) etc.) and 3<pi, 4>pi correct. HOLDS. (This is the path fixed by other.__le__->other.__lt__ etc.; note probe holds at base too since old bug affected finite Number vs Rational cases — but probe_1/2 cover the core discriminator.)
- probe_7 (Req 3.5): oo/-oo/zoo/nan vs a foreign 'NotInf' obj (declares !=) -> ==False/!=True symmetric, and oo==oo preserved True. HOLDS. (Note: sympy nan==nan is True, so I did not encode nan==nan==False.)

CANDIDATE PATCH (partial_basic_only / weak.diff): applies ONLY the sympy/core/basic.py hunks (Basic.__eq__ -> NotImplemented, __ne__ fix, _has_matcher), leaving numbers.py's Integer/Rational/Float/NumberSymbol __eq__ still returning False. This is the lazy partial reading of the requirements. Result: probe_1 and probe_2 REJECT it (VIOLATED) because numeric delegation is absent; probes 3-7 still hold. Demonstrates the suite discriminates wrong/partial implementations -> not TOO-WEAK.

Verdict SOUND: 7 distinct probes all hold on the patched tree, positive control fails at base and holds patched, and a plausibly-wrong partial candidate is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control. Req 1.1/1.2/1.4/3.4: when the other operand's __eq__
declares equality (truthy), a sympy object (Basic AND finite numeric)
delegates so == is True symmetrically and != is False symmetrically."""
import sys
from sympy import Symbol, Integer, Rational, Float

class EqAll(object):
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False
    def __hash__(self):
        return 1

ok = True
for name, obj in [("Symbol", Symbol('x')),
                  ("Integer", Integer(1)),
                  ("Rational", Rational(3, 2)),
                  ("Float", Float(1.5))]:
    f = EqAll()
    r1 = (obj == f)
    r2 = (f == obj)
    r3 = (obj != f)
    r4 = (f != obj)
    print(name, "obj==f", r1, "f==obj", r2, "obj!=f", r3, "f!=obj", r4)
    if not (r1 is True and r2 is True and r3 is False and r4 is False):
        ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy-13091: rich-comparison methods must return NotImplemented (not False) when the other operand is not sympifiable, so == / != become symmetric with foreign user classes; __ne__ must negate the OPERATOR (not self==other) not the raw __eq__; and Number-vs-NumberSymbol ordering must use the correctly-mirrored operator.

Probes (all HOLD on gold-patched tree; runner suppresses probe stdout so observations were confirmed via a local diag variant writing to stderr):
- probe_1 (Req 1.1/1.2/1.4/3.4, POSITIVE CONTROL): a foreign class whose __eq__ returns True compares == True and != False symmetrically against Symbol, Integer, Rational, Float. HOLDS patched, VIOLATED at base (prepatch_reproduced=true) -> discriminating power confirmed.
- probe_2 (Req 1.1/1.2): raw obj.__eq__(foreign) returns the NotImplemented singleton for Basic/Integer/Rational/Float and pi (NumberSymbol). HOLDS patched, VIOLATED at base.
- probe_3 (Req 1.3/3.1): neither-side-helps -> ==False/!=True both orders; Symbol vs int 0 and Integer(1) vs 0 unequal. HOLDS.
- probe_4 (Req 3.2/3.3): recognized equal objects ==True/!=False, different content ==False, identity ==True. HOLDS.
- probe_5 (Req 4.1): ordering (< > <= >=) of Integer/Rational/Float/oo/-oo/zoo/nan against a foreign object raises TypeError for all 4 ops. HOLDS.
- probe_6 (Req 5.1/5.2/5.3): Rational/Float vs pi ordering is symmetric with the mirrored operator ((x<c)==(c>x) etc.) and 3<pi, 4>pi correct. HOLDS. (This is the path fixed by other.__le__->other.__lt__ etc.; note probe holds at base too since old bug affected finite Number vs Rational cases — but probe_1/2 cover the core discriminator.)
- probe_7 (Req 3.5): oo/-oo/zoo/nan vs a foreign 'NotInf' obj (declares !=) -> ==False/!=True symmetric, and oo==oo preserved True. HOLDS. (Note: sympy nan==nan is True, so I did not encode nan==nan==False.)

CANDIDATE PATCH (partial_basic_only / weak.diff): applies ONLY the sympy/core/basic.py hunks (Basic.__eq__ -> NotImplemented, __ne__ fix, _has_matcher), leaving numbers.py's Integer/Rational/Float/NumberSymbol __eq__ still returning False. This is the lazy partial reading of the requirements. Result: probe_1 and probe_2 REJECT it (VIOLATED) because numeric delegation is absent; probes 3-7 still hold. Demonstrates the suite discriminates wrong/partial implementations -> not TOO-WEAK.

Verdict SOUND: 7 distinct probes all hold on the patched tree, positive control fails at base and holds patched, and a plausibly-wrong partial candidate is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** nl_attack probe.py and probe2.py both exit 0 on gold-patched tree (env: swebench-lean conda). G-PANEL-3 (leakage) already pass; G-EQ/G-PANEL-1 'spec-too-weak' fails are a different lane (weakness, not faithfulness) and their probe_7 targeted the same oo boundary the requirements intentionally exclude. Faithfulness verdict: FAITHFUL — requirements pin exactly the changed observable behavior (delegate for finite numerics/NumberSymbol/Basic; retain definite equality for oo/-oo/nan; TypeError on numeric ordering vs uninterpretable; symmetric NumberSymbol ordering) with the correct modeling boundary.

Counterexample / evidence:

```
Probe assertions all pass on patched tree: oo_eq_notNI=True (oo.__eq__(Foo()) is not NotImplemented), int_eq_NI/rat_eq_NI/float_eq_NI/pi_eq_NI/basic_eq_NI=True (finite/NumberSymbol/Basic delegate), oo_eqBar_False & Bar_eqoo_False=True (Req 3.5 symmetric False for infinities vs finite-only foreign class), int_eqBar_True & Bar_eqint_True=True (Req 3.4 symmetric True for finite), zoo_eq_NI=True (zoo delegates via Basic), zoo/-oo/oo/nan ordering vs Foo all raise TypeError incl. reflected (Req 4), NumberSymbol ordering symmetry r5_lt/le/gt/ge=True (Req 5). The prior attacker's oo asymmetry counterexample is a genuine gold-code property that the requirements correctly leave unclaimed, not a divergence.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes the fix behaviorally without transmitting the hidden tests. Legitimate localization: it names the modules/functions the gold patch touches (basic.py Basic.__eq__/__ne__, numbers.py Integer/Rational/Float/NumberSymbol __eq__/__ne__ and ordering operators) — all of which are either public via the problem_statement (which explicitly names basic.py line 316 and Basic.__eq__) or are the natural change surface. No leakage of: test file paths (sympy/core/tests/test_basic.py, test_numbers.py), test function names (test_equality, test_comparisons_with_unknown_type, test_NumberSymbol_comparison), the test helper class names (Foo/Bar), quoted test/gold code, or the fix-specific magic constants (Rational('905502432259640373/288230376151711744'), Float(float(pi))). The custom-class 'defer to reflected __eq__' scenario is straight from the public problem_statement's Foo example. Potential concerns examined and cleared: (1) Req 3.5/4.1 enumerate oo,-oo,zoo,nan — this mirrors the test loop but is the complete, natural set of non-finite sympy numbers, i.e. behavioral description not test-parametrization reconstruction; (2) Req 5.2 lists the four ordering-symmetry identities (x<c)==(c>x) etc., paralleling test_NumberSymbol_comparison and the gold's NumberSymbol operator-swap fix, but stated with generic variables x/c as the abstract mathematical definition of mirrored ordering — behavioral translation, which is the document's legitimate purpose, not the test itself. Every hidden element surfaces only as generic behavioral requirements with no test-specific identifiers or values.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
