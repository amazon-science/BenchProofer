# P2 adversarial audit — sympy__sympy-13372

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_5.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
At base, probe_5 (and the naive weak patch) raise UnboundLocalError: local variable 'reprec' referenced before assignment (via evalf_mul -> evalf when a part stays symbolic). The naive fix that only defaults reprec/imprec to None avoids UnboundLocalError but then assembles a malformed tuple and downstream raises TypeError: cannot unpack non-iterable Max object instead of NotImplementedError, so evalf does not degrade gracefully.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req2.1/2.2/2.3 + Req1.4 positive control: product with symbolic Max factor
evalf's cleanly (returns expr unchanged, no error) in BOTH argument orders."""
import sys
from sympy import Symbol, Max, Mul

x = Symbol('x'); y = Symbol('y')
ok = True
try:
    a = Mul(x, Max(0, y), evaluate=False).evalf()
    b = Mul(Max(0, y), x, evaluate=False).evalf()
    print("order1:", a)
    print("order2:", b)
    # both must equal the original symbolic product (unchanged)
    if a != x * Max(0, y):
        print("FAIL order1 not unchanged"); ok = False
    if b != x * Max(0, y):
        print("FAIL order2 not unchanged"); ok = False
    if a != b:
        print("FAIL orders differ"); ok = False
except Exception as e:
    print("FAIL raised", type(e).__name__, e); ok = False

sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.1/1.2: fallback numeric reduction raises NotImplementedError (not
UnboundLocalError/other) when a part stays symbolic. Test evalf() directly on
a bare head-without-handler expression whose parts are symbolic. We assert the
PUBLIC .evalf returns unchanged AND the internal evalf raises NotImplementedError."""
import sys
from sympy import Symbol, Max
from sympy.core.evalf import evalf as _evalf

y = Symbol('y')
expr = Max(0, y)  # head Max has no dedicated numeric handler
ok = True
try:
    _evalf(expr, 53, {})
    print("FAIL: internal evalf did not raise"); ok = False
except NotImplementedError:
    print("OK: internal evalf raised NotImplementedError")
except Exception as e:
    print("FAIL: raised", type(e).__name__, e); ok = False

# public entry returns expr unchanged
try:
    r = expr.evalf()
    print("public:", r)
    if r != expr:
        print("FAIL public not unchanged"); ok = False
except Exception as e:
    print("FAIL public raised", type(e).__name__, e); ok = False

sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req3.4/3.5 regression: existing numeric evaluation stays correct."""
import sys
from sympy import (Symbol, sqrt, pi, exp, log, sin, cos, Integer, Rational,
                   Float, floor, ceiling, Integral, Sum, Mul)
from sympy.abc import x

ok = True
def chk(got, exp_str, tol=1e-9):
    global ok
    try:
        g = float(got)
        e = float(exp_str)
        if abs(g - e) > tol:
            print("FAIL", got, "!=", exp_str); ok = False
        else:
            print("ok", got, "~", exp_str)
    except Exception as ex:
        print("FAIL conv", got, ex); ok = False

chk(sqrt(2).evalf(), 1.4142135623730951)
chk(pi.evalf(), 3.141592653589793)
chk(exp(1).evalf(), 2.718281828459045)
chk(log(2).evalf(), 0.6931471805599453)
chk(sin(1).evalf(), 0.8414709848078965)
chk(cos(0).evalf(), 1.0)
chk((Integer(2)**10).evalf(), 1024.0)
chk(floor(pi).evalf(), 3.0)
chk(ceiling(pi).evalf(), 4.0)
chk(Integral(x, (x, 0, 2)).evalf(), 2.0)
chk(Sum(1/Integer(2)**x, (x, 0, 100)).evalf(), 2.0)
# product of numeric factors reduces to numeric value (Req3.5)
chk(Mul(Integer(2), Rational(3, 2), evaluate=False).evalf(), 3.0)
# subs option (Req3.4)
chk((x**2).evalf(subs={x: 3}), 9.0)
# chopping behavior unchanged
r = (exp(pi*sqrt(163))).evalf(chop=True)
print("chop:", r)

sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1/3.2/3.4 (complex): zero component contributes nothing; concrete number
contributes value+prec; complex numeric evaluation stays correct."""
import sys
from sympy import I, sqrt, Float, Symbol
from sympy.core.evalf import evalf as _evalf

ok = True
# complex numeric expression evaluates correctly
r = (sqrt(2) + sqrt(3)*I).evalf()
print("complex:", r)
if abs(complex(r) - (1.4142135623730951 + 1.7320508075688772j)) > 1e-9:
    print("FAIL complex"); ok = False

# purely real concrete number: internal evalf returns (mpf, None, prec, None)
val = _evalf(Float(2.5), 53, {})
print("Float2.5 tuple:", val)
if not (val[1] is None and val[3] is None and val[0] is not None):
    print("FAIL zero-im component not preserved"); ok = False

# purely imaginary: (None, mpf, None, prec)
val2 = _evalf((2*I), 53, {})
print("2I tuple:", val2)
if not (val2[0] is None and val2[2] is None and val2[1] is not None):
    print("FAIL zero-re component not preserved"); ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req1.1 vs Req1.2 independently + Req1.3: exercise the real-symbolic branch and
the imaginary-symbolic branch separately, and confirm the 4-tuple is never
assembled with an unbound precision (would surface as UnboundLocalError)."""
import sys
from sympy import Symbol, Max, I
from sympy.core.evalf import evalf as _evalf

y = Symbol('y', real=True)
ok = True

# Case A: imaginary part symbolic (real part exactly 0)  -> Req1.2 im-branch
exprA = I * Max(0, y)
# Case B: real part symbolic, imaginary concrete         -> Req1.1 re-branch
exprB = Max(0, y) + 2*I

for name, e in [("A(im-symbolic)", exprA), ("B(re-symbolic)", exprB)]:
    try:
        _evalf(e, 53, {})
        print("FAIL", name, "no raise"); ok = False
    except NotImplementedError:
        print("OK", name, "NotImplementedError")
    except UnboundLocalError as ub:
        print("FAIL", name, "UnboundLocalError", ub); ok = False
    except Exception as ex:
        print("FAIL", name, "other", type(ex).__name__, ex); ok = False
    # public must return unchanged
    r = e.evalf()
    if r != e:
        print("FAIL", name, "public changed:", r); ok = False
    else:
        print("  public unchanged:", r)

sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_5.py`

```python
"""Req1.1 vs Req1.2 independently + Req1.3: exercise the real-symbolic branch and
the imaginary-symbolic branch separately, and confirm the 4-tuple is never
assembled with an unbound precision (would surface as UnboundLocalError)."""
import sys
from sympy import Symbol, Max, I
from sympy.core.evalf import evalf as _evalf

y = Symbol('y', real=True)
ok = True

# Case A: imaginary part symbolic (real part exactly 0)  -> Req1.2 im-branch
exprA = I * Max(0, y)
# Case B: real part symbolic, imaginary concrete         -> Req1.1 re-branch
exprB = Max(0, y) + 2*I

for name, e in [("A(im-symbolic)", exprA), ("B(re-symbolic)", exprB)]:
    try:
        _evalf(e, 53, {})
        print("FAIL", name, "no raise"); ok = False
    except NotImplementedError:
        print("OK", name, "NotImplementedError")
    except UnboundLocalError as ub:
        print("FAIL", name, "UnboundLocalError", ub); ok = False
    except Exception as ex:
        print("FAIL", name, "other", type(ex).__name__, ex); ok = False
    # public must return unchanged
    r = e.evalf()
    if r != e:
        print("FAIL", name, "public changed:", r); ok = False
    else:
        print("  public unchanged:", r)

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probe->requirement mapping and results (PATCHED / BASE / WEAK-candidate):
- probe_1 (Req2.1/2.2/2.3, Req1.4): product x*Max(0,y) evalf's unchanged in BOTH argument orders, no error. HOLDS / VIOLATED(base) / VIOLATED(weak).
- probe_2 (Req1.1/1.2, Req1.4): internal evalf(Max(0,y)) raises NotImplementedError; public .evalf returns unchanged. HOLDS / VIOLATED(base) / VIOLATED(weak).
- probe_3 (Req3.4/3.5 regression): sqrt2, pi, exp, log, sin, cos, powers, floor/ceiling, Integral, Sum, numeric product, subs, chop all correct. HOLDS / HOLDS(base) / HOLDS(weak) — pure regression, not discriminating (expected).
- probe_4 (Req3.1/3.2 + complex): complex value correct; zero-component contributes (None,None); concrete component contributes value+prec. HOLDS / HOLDS(base) / HOLDS(weak) — regression leg.
- probe_5 (Req1.1 re-branch AND Req1.2 im-branch separately, Req1.3 no malformed tuple): I*Max(0,y) and Max(0,y)+2*I both raise NotImplementedError internally (not UnboundLocalError) and return unchanged publicly. HOLDS / VIOLATED(base with UnboundLocalError 'reprec') / VIOLATED(weak with TypeError). POSITIVE CONTROL.

Discriminating power: probes 1,2,5 fail at base and reject the naive weak candidate; all 5 hold on the gold-patched tree. Suite distinguishes both the unpatched bug and a requirements-non-conforming lazy fix. The candidate that merely suppresses UnboundLocalError without raising NotImplementedError is correctly REJECTED (violates Req1.1/1.2/1.3 and Req2). No too-weak candidate survived the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_5.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
At base, probe_5 (and the naive weak patch) raise UnboundLocalError: local variable 'reprec' referenced before assignment (via evalf_mul -> evalf when a part stays symbolic). The naive fix that only defaults reprec/imprec to None avoids UnboundLocalError but then assembles a malformed tuple and downstream raises TypeError: cannot unpack non-iterable Max object instead of NotImplementedError, so evalf does not degrade gracefully.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_5.py`

```python
"""Req1.1 vs Req1.2 independently + Req1.3: exercise the real-symbolic branch and
the imaginary-symbolic branch separately, and confirm the 4-tuple is never
assembled with an unbound precision (would surface as UnboundLocalError)."""
import sys
from sympy import Symbol, Max, I
from sympy.core.evalf import evalf as _evalf

y = Symbol('y', real=True)
ok = True

# Case A: imaginary part symbolic (real part exactly 0)  -> Req1.2 im-branch
exprA = I * Max(0, y)
# Case B: real part symbolic, imaginary concrete         -> Req1.1 re-branch
exprB = Max(0, y) + 2*I

for name, e in [("A(im-symbolic)", exprA), ("B(re-symbolic)", exprB)]:
    try:
        _evalf(e, 53, {})
        print("FAIL", name, "no raise"); ok = False
    except NotImplementedError:
        print("OK", name, "NotImplementedError")
    except UnboundLocalError as ub:
        print("FAIL", name, "UnboundLocalError", ub); ok = False
    except Exception as ex:
        print("FAIL", name, "other", type(ex).__name__, ex); ok = False
    # public must return unchanged
    r = e.evalf()
    if r != e:
        print("FAIL", name, "public changed:", r); ok = False
    else:
        print("  public unchanged:", r)

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probe->requirement mapping and results (PATCHED / BASE / WEAK-candidate):
- probe_1 (Req2.1/2.2/2.3, Req1.4): product x*Max(0,y) evalf's unchanged in BOTH argument orders, no error. HOLDS / VIOLATED(base) / VIOLATED(weak).
- probe_2 (Req1.1/1.2, Req1.4): internal evalf(Max(0,y)) raises NotImplementedError; public .evalf returns unchanged. HOLDS / VIOLATED(base) / VIOLATED(weak).
- probe_3 (Req3.4/3.5 regression): sqrt2, pi, exp, log, sin, cos, powers, floor/ceiling, Integral, Sum, numeric product, subs, chop all correct. HOLDS / HOLDS(base) / HOLDS(weak) — pure regression, not discriminating (expected).
- probe_4 (Req3.1/3.2 + complex): complex value correct; zero-component contributes (None,None); concrete component contributes value+prec. HOLDS / HOLDS(base) / HOLDS(weak) — regression leg.
- probe_5 (Req1.1 re-branch AND Req1.2 im-branch separately, Req1.3 no malformed tuple): I*Max(0,y) and Max(0,y)+2*I both raise NotImplementedError internally (not UnboundLocalError) and return unchanged publicly. HOLDS / VIOLATED(base with UnboundLocalError 'reprec') / VIOLATED(weak with TypeError). POSITIVE CONTROL.

Discriminating power: probes 1,2,5 fail at base and reject the naive weak candidate; all 5 hold on the gold-patched tree. Suite distinguishes both the unpatched bug and a requirements-non-conforming lazy fix. The candidate that merely suppresses UnboundLocalError without raising NotImplementedError is correctly REJECTED (violates Req1.1/1.2/1.3 and Req2). No too-weak candidate survived the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `else: raise NotImplementedError` in the KeyError fallback of evalf() for both the real-part branch (guards reprec) and imaginary-part branch (guards imprec), so the four-tuple r=re,im,reprec,imprec is only assembled once value+precision are established. This exactly realizes Req1.1/1.2 (NotImplementedError instead of UnboundLocalError for symbolic re/im), Req1.3 (no tuple unless both value+precision set), Req1.4 (EvalfMixin.evalf catches NotImplementedError and returns expr unchanged — confirmed by probe returning the product). Req2 (order independence) is the exact issue reproduction and is confirmed by the probe: both argument orders give identical, error-free results. Req3 (preserve zero/concrete-number branches and existing numeric evaluation) is untouched by the patch (only the else branches added), so preservation holds. Modeling boundary is the changed observable behavior (graceful unsupported + order-independence), not a narrow helper slice. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The problem_statement is unusually detailed: it already shows BOTH product orderings (Mul(x, Max(0,y)) vs Mul(Max(0,y), x)), the UnboundLocalError, the file sympy/core/evalf.py, the KeyError: Max fallback, and even the proposed fix (else: raise NotImplementedError). Requirements 1 and 2 merely restate this public content as behavioral EARS criteria — nothing derived from the hidden test. The hidden F2P test is a single assertion in test_evalf_bugs (NS(Mul(Max(0,y), x, evaluate=False).evalf()) == 'x*Max(0, y)'); the document contains no test file path, test function/class names, parametrization ids, or quoted test/gold code. Gold-patch identifiers (reprec/imprec/NotImplementedError) that appear are all already present in the public problem_statement/traceback. Closest concern: Req 3.4 enumerates powers/exponentials/logs/trig/sums/products/integrals/floor-ceiling/relationals/subs, which loosely echoes the PASS_TO_PASS test-function set — but these are generic, publicly-obvious categories a numeric evaluator handles, phrased as a no-regressions clause with no test names or assertions. Legitimate localization/behavioral translation, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
