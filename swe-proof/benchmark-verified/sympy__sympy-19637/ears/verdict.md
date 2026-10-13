# P2 adversarial audit — sympy__sympy-19637

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
import sys
from sympy.core.sympify import kernS
from sympy.abc import x
try:
    r = kernS("(2*x)/(x-1)")
except Exception as e:
    print("EXCEPTION:", type(e).__name__, e)
    sys.exit(1)
expected = 2*x/(x-1)
print("got:", r, "expected:", expected)
sys.exit(0 if r == expected else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.1/1.3/2.1: parenthesized input with no space after rewrite must not raise
import sys
from sympy.core.sympify import kernS
# these contain '(' , no quotes, and rewrite to no-space forms
cases = ["(2*x)/(x-1)", "(x)", "(a+b)/(c-d)", "(x/y)"]
for c in cases:
    try:
        r = kernS(c)
        print("OK", repr(c), "->", r)
    except Exception as e:
        print("EXCEPTION on", repr(c), ":", type(e).__name__, e)
        sys.exit(1)
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2: unexpanded product and negated sum preserved (structure kept)
import sys
from sympy.core.sympify import kernS
from sympy.abc import x, y
r1 = kernS('2*(x + y)')
r2 = kernS('-(x + 1)')
print("2*(x+y) ->", r1)
print("-(x+1) ->", r2)
# The whole point of kernS is that the product stays UNEXPANDED.
# str form must show grouping, not the distributed form.
ok = (str(r1) == '2*(x + y)') and (str(r2) == '-(x + 1)')
# and value-wise it should still expand to the distributed form
ok = ok and (r1.expand() == 2*x + 2*y) and (r2.expand() == -x - 1)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 3.9 + core test_kernS discriminator: deferred cancellation stays deferred
import sys
from sympy.core.sympify import kernS
from sympy.abc import x
s = '-1 - 2*(-(-x + 1/x)/(x*(x - 1/x)**2) - 1/(x*(x - 1/x)))'
try:
    ss = kernS(s)
except Exception as e:
    print("EXCEPTION:", type(e).__name__, e)
    sys.exit(1)
print("ss =", ss)
ok = (ss != -1) and (ss.simplify() == -1)
# also the _kern-renamed variant
s2 = s.replace('x', '_kern')
ss2 = kernS(s2)
ok = ok and (ss2 != -1) and (ss2.simplify() == -1)
# x - (x-1) defers
one = kernS('x - (x - 1)')
ok = ok and (one != 1) and (one.expand() == 1)
print("one =", one)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.4/3.6/3.10/3.11/3.8/2.2 (marker cleared): assorted regression behaviors
import sys
from sympy.core.sympify import kernS
from sympy.abc import x, y
from sympy import Interval, Add, Mul, Symbol, exp, sin, cos

fails = []
def chk(name, cond, got):
    print(name, "->", got, "OK" if cond else "FAIL")
    if not cond: fails.append(name)

# 3.4 unevaluated arithmetic inside constructor arg
chk("Interval", kernS('Interval(-1,-2 - 4*(-3))') == Interval(-1, Add(-2, Mul(12,1,evaluate=False), evaluate=False)), "..")
# 3.10 underscore symbol unchanged, no marker residue
chk("_kern sym", kernS('_kern') == Symbol('_kern'), kernS('_kern'))
# 3.8 constant to signed grouped exponent
chk("E**-(x)", kernS('E**-(x)') == exp(-x), kernS('E**-(x)'))
# 3.11 containers
e = 2*(x + y)*y
chk("containers", kernS(['2*(x + y)*y', ('2*(x + y)*y',)]) == [e, (e,)], "..")
# 3.6 float coefficient preserved
r = kernS('(1-2.*(1-y)*x)')
chk("float coeff", r == 1 - 2.*x*(1 - y), r)
# 3.3 nested groups / function args
chk("nested neg", kernS('-(2*sin(x)**2 + 2*sin(x)*cos(x))*y/2') == -y*(2*sin(x)**2 + 2*sin(x)*cos(x))/2, "..")
# 3.7 whitespace/ordering equality
chk("ws/order", kernS('(1 - x)/(1 - x*(1-y))') == kernS('(1-x)/(1-(1-y)*x)'), "..")

sys.exit(1 if fails else 0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy.core.sympify import kernS
from sympy.abc import x
try:
    r = kernS("(2*x)/(x-1)")
except Exception as e:
    print("EXCEPTION:", type(e).__name__, e)
    sys.exit(1)
expected = 2*x/(x-1)
print("got:", r, "expected:", expected)
sys.exit(0 if r == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

kernS fix: marker-presence flag 'hit' was only assigned on the space-present path; gold indents 'hit = kern in s' into the space branch and adds an else: hit=False. Probes: probe_1 (Req1.2) kernS('(2*x)/(x-1)')==2*x/(x-1); probe_2 (Req1.1/1.3/2.1) no UnboundLocalError on paren inputs with no post-rewrite space; probe_3 (Req3.1/3.2) 2*(x+y) and -(x+1) stay unexpanded (str form preserved); probe_4 (Req3.9 + core F2P discriminator) deferred cancellation stays deferred (ss!=-1, simplify==-1; _kern-renamed variant; x-(x-1)); probe_5 (Req3.3/3.4/3.6/3.8/3.10/3.11/2.2 marker-cleared) Interval unevaluated arg, _kern symbol unchanged, E**-(x)==exp(-x), containers, float coeff, nested neg, whitespace/order equality. All 5 HOLD on gold-patched tree.

Positive control probe_1 FAILS at base with UnboundLocalError: local variable 'kern' referenced before assignment (prepatch reproduced). Candidate wrong patch weak.diff sets 'hit = False' unconditionally: it fixes the crash (probe_1, probe_2 pass) but never clears the substituted space-marker '_', so probes 3, 4, and 5 REJECT it (outputs contain residual '_', e.g. 2*_*(x + y), violating Req2.2/3.12 and the unexpanded-grouping regressions). Suite discriminates the weak fix; >=1 candidate exercised and rejected. Verdict SOUND.

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
import sys
from sympy.core.sympify import kernS
from sympy.abc import x
try:
    r = kernS("(2*x)/(x-1)")
except Exception as e:
    print("EXCEPTION:", type(e).__name__, e)
    sys.exit(1)
expected = 2*x/(x-1)
print("got:", r, "expected:", expected)
sys.exit(0 if r == expected else 1)
```

Prepatch bug re-encoded as an attack: `True`.

kernS fix: marker-presence flag 'hit' was only assigned on the space-present path; gold indents 'hit = kern in s' into the space branch and adds an else: hit=False. Probes: probe_1 (Req1.2) kernS('(2*x)/(x-1)')==2*x/(x-1); probe_2 (Req1.1/1.3/2.1) no UnboundLocalError on paren inputs with no post-rewrite space; probe_3 (Req3.1/3.2) 2*(x+y) and -(x+1) stay unexpanded (str form preserved); probe_4 (Req3.9 + core F2P discriminator) deferred cancellation stays deferred (ss!=-1, simplify==-1; _kern-renamed variant; x-(x-1)); probe_5 (Req3.3/3.4/3.6/3.8/3.10/3.11/2.2 marker-cleared) Interval unevaluated arg, _kern symbol unchanged, E**-(x)==exp(-x), containers, float coeff, nested neg, whitespace/order equality. All 5 HOLD on gold-patched tree.

Positive control probe_1 FAILS at base with UnboundLocalError: local variable 'kern' referenced before assignment (prepatch reproduced). Candidate wrong patch weak.diff sets 'hit = False' unconditionally: it fixes the crash (probe_1, probe_2 pass) but never clears the substituted space-marker '_', so probes 3, 4, and 5 REJECT it (outputs contain residual '_', e.g. 2*_*(x + y), violating Req2.2/3.12 and the unexpanded-grouping regressions). Suite discriminates the weak fix; >=1 candidate exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch adds `hit = kern in s` inside the space branch and `else: hit = False`. Probe on gold-patched tree: ALL OK (R1.2, R3.4, R3.6, R3.8, R3.9, R3.10, R3.11 all pass). Probe on base: UnboundLocalError as issue describes. Requirements match the F2P test_kernS assertions and model the real change faithfully.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The one quoted literal that maps to the new FAIL_TO_PASS assertion — Req 1.2's `"(2*x)/(x-1)"` == `2*x/(x - 1)` — is verbatim in the PUBLIC problem_statement (the repro `text = "(2*x)/(x-1)"` and its UnboundLocalError). The regression examples in Req 3.1/3.2 (`"2*(x + y)"`, `"-(x + 1)"`) come from kernS's public docstring, not the tests. Req 3 items 3-11 do enumerate one-per-line behaviors that parallel the hidden test_kernS assertions (E**-(x)=exp(-x); _kern symbol; 2.* float coefficient; nested groups; negative power; x-(x-1) deferred cancellation; list/tuple containers), BUT they are described abstractly as behaviors without transmitting any hidden literal test strings, the Interval example, the exact numeric constants (2**-(4+1)), test function/file names, ids, or fix-invented identifiers. test_kernS is a single non-parametrized function, so there is no parametrization to mirror. The fix touches only `kern`/`hit`, both already public via the problem_statement; the doc even abstracts them to 'marker'/'marker-presence flag'. This is legitimate localization + behavior translation, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
