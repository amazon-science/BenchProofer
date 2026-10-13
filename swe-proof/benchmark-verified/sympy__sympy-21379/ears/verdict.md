# P2 adversarial audit — sympy__sympy-21379

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control -- Req 3.2 / core fix.
subs({1:1.0}) on exp(sinh(Piecewise(...)/z)) with real symbols must NOT raise.
On base it raises PolynomialError; on patched it completes.
"""
import sys
from sympy import symbols, exp
from sympy.functions.elementary.hyperbolic import sinh
from sympy.functions.elementary.piecewise import Piecewise
from sympy.core.cache import clear_cache

clear_cache()
x, y, z = symbols('x y z', real=True)
expr = exp(sinh(Piecewise((x, y > x), (y, True)) / z))
try:
    r = expr.subs({1: 1.0})
    print("subs completed:", r)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.3 / 3.3 -- constructing a Mod on a Piecewise-based quotient must complete.
(Piecewise((x,y>x),(y,True))/z) % 1 must return without raising.
"""
import sys
from sympy import symbols
from sympy.functions.elementary.piecewise import Piecewise
from sympy.core.cache import clear_cache

clear_cache()
x, y, z = symbols('x_r y_r z', real=True)
from sympy.core.mod import Mod
try:
    r = (Piecewise((x, y > x), (y, True)) / z) % 1
    print("Mod constructed:", r)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
# Req 1.2: factor treated as unit 1, operands unchanged -> result is the
# unevaluated Mod(Piecewise/z, 1), NOT collapsed to 0 (which would happen if
# the failing gcd were treated as 0 instead of 1).
if not isinstance(r, Mod):
    print("Req1.2 VIOLATED: result is not an unevaluated Mod:", r)
    sys.exit(1)
if r == 0:
    print("Req1.2 VIOLATED: operands were altered, result collapsed to 0")
    sys.exit(1)
expected = Mod(Piecewise((x, y > x), (y, True)) / z, 1)
print("expected:", expected)
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.1 / 3.4 -- is_zero assumption query through Mod must complete (no raise),
and be deterministic across repeated evaluation (cache independence).
"""
import sys
from sympy import symbols
from sympy.functions.elementary.hyperbolic import sinh
from sympy.functions.elementary.piecewise import Piecewise
from sympy.core.cache import clear_cache

results = []
for i in range(3):
    clear_cache()
    x, y, z = symbols('x_r y_r z', real=True)
    e = sinh(Piecewise((x, y > x), (y, True)) * z ** -1.0)
    try:
        r = e.is_zero
    except Exception as ex:
        print("RAISED:", type(ex).__name__, ex)
        sys.exit(1)
    results.append(r)
print("is_zero results across 3 runs:", results)
if len(set(str(r) for r in results)) != 1:
    print("non-deterministic!")
    sys.exit(1)
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 1.4 / 2.3 regression -- Mod by zero must still raise ZeroDivisionError,
and numeric Mod rules preserved. The tolerance must be scoped to gcd only.
"""
import sys
from sympy import symbols, Integer, S
from sympy.core.mod import Mod

x = symbols('x')

# Mod by zero still raises
try:
    Mod(x, 0)
    print("ERROR: Mod(x,0) did not raise")
    sys.exit(1)
except ZeroDivisionError:
    print("Mod(x,0) raised ZeroDivisionError as required")

# numeric remainder
assert Mod(Integer(7), Integer(3)) == 3 % 3 or True
r = Mod(Integer(7), Integer(3))
print("Mod(7,3)=", r)
if r != 1:
    sys.exit(1)

# p==q -> 0
if Mod(x, x) != 0:
    print("Mod(x,x) != 0"); sys.exit(1)
print("Mod(x,x)=0 ok")

# integer p, q==1 -> 0
n = symbols('n', integer=True)
if Mod(n, 1) != 0:
    print("Mod(n,1)!=0"); sys.exit(1)
print("Mod(n,1)=0 ok")

# non-finite -> nan
if Mod(S.Infinity, 3) is not S.NaN:
    print("Mod(oo,3) not nan:", Mod(S.Infinity,3)); sys.exit(1)
print("Mod(oo,3)=nan ok")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.1 / 2.2 -- successful common-factor extraction must still simplify.
When gcd succeeds with G!=1, Mod divides it out (as before);
when gcd gives 1, operands unchanged. Verify prior-behavior results preserved.
"""
import sys
from sympy import symbols
from sympy.core.mod import Mod

x, y = symbols('x y')

# Common factor case: Mod(2*x, 4) should reduce like before -> 2*Mod(x,2)
r = Mod(2*x, 4)
print("Mod(2*x,4)=", r)
if r != 2*Mod(x, 2):
    print("factor-out simplification changed!"); sys.exit(1)

# gcd==1 case: Mod(x, y) stays symbolic Mod(x,y)
r2 = Mod(x, y)
print("Mod(x,y)=", r2)
if r2 != Mod(x, y):
    sys.exit(1)

# sign follows divisor
r3 = Mod(x, -2)
print("Mod(x,-2)=", r3)
# Just check it evaluates for a numeric case sign
rn = Mod(5, -3)
print("Mod(5,-3)=", rn)
if rn != -1:
    print("sign of divisor not followed"); sys.exit(1)
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control -- Req 3.2 / core fix.
subs({1:1.0}) on exp(sinh(Piecewise(...)/z)) with real symbols must NOT raise.
On base it raises PolynomialError; on patched it completes.
"""
import sys
from sympy import symbols, exp
from sympy.functions.elementary.hyperbolic import sinh
from sympy.functions.elementary.piecewise import Piecewise
from sympy.core.cache import clear_cache

clear_cache()
x, y, z = symbols('x y z', real=True)
expr = exp(sinh(Piecewise((x, y > x), (y, True)) / z))
try:
    r = expr.subs({1: 1.0})
    print("subs completed:", r)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on gold-patched tree.

Probe->criterion->result:
- probe_1 (Req 3.2 / core fix; POSITIVE CONTROL): subs({1:1.0}) on exp(sinh(Piecewise(...)/z)) with real symbols must not raise. PATCHED: holds. BASE: fails (PolynomialError). weak_zero: holds. weak_broad: holds.
- probe_2 (Req 1.3/3.3 + Req 1.2 value): (Piecewise(...)/z) % 1 constructs without raising AND result is the unevaluated Mod (operands unchanged, NOT collapsed to 0). PATCHED: holds (Mod(Piecewise/z,1)). BASE: fails (raises). weak_zero: REJECTED (result collapses to 0 -> Req 1.2 violated). weak_broad: holds.
- probe_3 (Req 3.1/3.4): sinh(Piecewise*z**-1.0).is_zero completes without raising and is deterministic across 3 clear_cache runs (all None). PATCHED holds; BASE fails.
- probe_4 (Req 1.4/2.3 regression): Mod by zero still raises ZeroDivisionError; numeric Mod(7,3)=1; Mod(x,x)=0; Mod(n,1)=0; Mod(oo,3)=nan. Holds patched & base (regression).
- probe_5 (Req 2.1/2.2): successful gcd extraction still simplifies -- Mod(2*x,4)=2*Mod(x,2); Mod(x,y) unchanged; Mod(5,-3)=-1 (sign follows divisor). Holds patched & base (regression).

Positive control (probe_1) discriminates: exit 1 at base, exit 0 patched. prepatch_reproduced=true.

Candidate patches (>=1 exercised, >=1 rejected -- floor met):
- weak_zero.diff (catches PolynomialError but sets G=S.Zero instead of S.One): REJECTED by probe_2 -- dividing by G=0 collapses the Mod to 0, violating Req 1.2's 'leave operands unchanged / treat factor as unit 1'. Demonstrates the suite discriminates a wrong reading.
- weak_broad.diff (catches broad Exception instead of PolynomialError): passes ALL 5 probes. This is NOT a too-weak finding: it still resolves the hidden test (F2P test_Mod only checks that these operations complete without raising) and does not violate any requirement -- it is merely a slightly broader-but-valid fix. Reported for completeness; runner may confirm it resolves.

Conclusion: 5 probes hold on patched, positive control discriminates base vs patched, and the requirements-derived probe suite REJECTS the naive G=S.Zero wrong-fix. No probe fails on the patched tree; no probe-conforming alternative that also resolves is a weakness. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Positive control -- Req 3.2 / core fix.
subs({1:1.0}) on exp(sinh(Piecewise(...)/z)) with real symbols must NOT raise.
On base it raises PolynomialError; on patched it completes.
"""
import sys
from sympy import symbols, exp
from sympy.functions.elementary.hyperbolic import sinh
from sympy.functions.elementary.piecewise import Piecewise
from sympy.core.cache import clear_cache

clear_cache()
x, y, z = symbols('x y z', real=True)
expr = exp(sinh(Piecewise((x, y > x), (y, True)) / z))
try:
    r = expr.subs({1: 1.0})
    print("subs completed:", r)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on gold-patched tree.

Probe->criterion->result:
- probe_1 (Req 3.2 / core fix; POSITIVE CONTROL): subs({1:1.0}) on exp(sinh(Piecewise(...)/z)) with real symbols must not raise. PATCHED: holds. BASE: fails (PolynomialError). weak_zero: holds. weak_broad: holds.
- probe_2 (Req 1.3/3.3 + Req 1.2 value): (Piecewise(...)/z) % 1 constructs without raising AND result is the unevaluated Mod (operands unchanged, NOT collapsed to 0). PATCHED: holds (Mod(Piecewise/z,1)). BASE: fails (raises). weak_zero: REJECTED (result collapses to 0 -> Req 1.2 violated). weak_broad: holds.
- probe_3 (Req 3.1/3.4): sinh(Piecewise*z**-1.0).is_zero completes without raising and is deterministic across 3 clear_cache runs (all None). PATCHED holds; BASE fails.
- probe_4 (Req 1.4/2.3 regression): Mod by zero still raises ZeroDivisionError; numeric Mod(7,3)=1; Mod(x,x)=0; Mod(n,1)=0; Mod(oo,3)=nan. Holds patched & base (regression).
- probe_5 (Req 2.1/2.2): successful gcd extraction still simplifies -- Mod(2*x,4)=2*Mod(x,2); Mod(x,y) unchanged; Mod(5,-3)=-1 (sign follows divisor). Holds patched & base (regression).

Positive control (probe_1) discriminates: exit 1 at base, exit 0 patched. prepatch_reproduced=true.

Candidate patches (>=1 exercised, >=1 rejected -- floor met):
- weak_zero.diff (catches PolynomialError but sets G=S.Zero instead of S.One): REJECTED by probe_2 -- dividing by G=0 collapses the Mod to 0, violating Req 1.2's 'leave operands unchanged / treat factor as unit 1'. Demonstrates the suite discriminates a wrong reading.
- weak_broad.diff (catches broad Exception instead of PolynomialError): passes ALL 5 probes. This is NOT a too-weak finding: it still resolves the hidden test (F2P test_Mod only checks that these operations complete without raising) and does not violate any requirement -- it is merely a slightly broader-but-valid fix. Reported for completeness; runner may confirm it resolves.

Conclusion: 5 probes hold on patched, positive control discriminates base vs patched, and the requirements-derived probe suite REJECTS the naive G=S.Zero wrong-fix. No probe fails on the patched tree; no probe-conforming alternative that also resolves is a weakness. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The requirements correctly pin the CHANGED observable behavior (tolerance of PolynomialError in the factor-extraction step and preservation of everything else), not a narrow slice. Requirement 1.4's scoping claim (only extraction-step errors tolerated; ZeroDivisionError still propagates) matches the code — the try/except is narrowly around gcd/gcd_terms only, and ZeroDivisionError is raised earlier in doit/eval, outside the guard. No mandated-but-absent, forbidden-but-present, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md legitimately localizes the fix to Mod.eval / sympy.polys.polytools.gcd / gcd_terms in sympy/core/mod.py and translates test-checked behavior into EARS acceptance criteria — which is the intended purpose. No hidden-test artifacts are transmitted: no test names/paths (test_Mod, test_arit.py absent), no parametrization ids, no verbatim test or gold code, and no fix-invented identifiers (the gold patch introduces none — PolynomialError, S.One, gcd all pre-exist). The one verbatim expression it quotes, exp(sinh(Piecewise((x, y > x), (y, True)) / z)) with subs({1: 1.0}), is drawn from the PUBLIC problem_statement, and it uses the problem_statement's x,y,z naming rather than the test's x_r,y_r symbols. R3.1 (is_zero/is_real via im%pi) and R3.3 (Piecewise-quotient % integer) mirror the two non-public test lines, but they are expressed as mechanism-derived behavioral scenarios (sinh.is_real internally computes im%pi; Mod.eval's gcd fails on Piecewise) rather than as reproduced test code — legitimate source-level localization, and the test is not parametrized so there is no case-enumeration to mirror. This is behavior description, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
