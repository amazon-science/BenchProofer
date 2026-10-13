# P2 adversarial audit — sympy__sympy-13878

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_arcsin_closedform.py`, `probe_2_piecewise_values.py`, `probe_3_antiderivative.py`, `probe_4_density_unchanged.py`, `probe_5_family_closedform.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_arcsin_closedform.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_arcsin_closedform.py` → holds on the patched tree (good)

```python
# Req 1.1 + positive control: arcsin cdf is a closed form, no unevaluated Integral.
import sys
from sympy.stats import Arcsin, cdf
from sympy import Symbol, Integral
z = Symbol('z')
X = Arcsin('x', 1, 3)
e = cdf(X)(z)
print("expr:", e)
print("has Integral:", e.has(Integral))
sys.exit(0 if not e.has(Integral) else 1)
```

Attack 2 — `probe_2_piecewise_values.py` → holds on the patched tree (good)

```python
# Req 1.2,1.3,1.5: three region values 0 / arcsine form / 1.
import sys
from sympy.stats import Arcsin, cdf
from sympy import Symbol, asin, sqrt, pi, nsimplify, simplify, Rational
z = Symbol('z')
a, b = 1, 3
X = Arcsin('x', a, b)
F = cdf(X)(z)
left  = simplify(F.subs(z, 0))          # x<a -> 0
mid   = simplify(F.subs(z, 2))          # in support
right = simplify(F.subs(z, 5))          # x>b -> 1
expected_mid = simplify(2*asin(sqrt(Rational(2-a, b-a)))/pi)
print("left(0)=", left, " mid(2)=", mid, " expected_mid=", expected_mid, " right(5)=", right)
ok = (left == 0) and (right == 1) and simplify(mid - expected_mid) == 0
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_antiderivative.py` → holds on the patched tree (good)

```python
# Req 2.1 derivative recovers density inside (a,b); Req 2.2 boundary 0 and 1.
import sys
from sympy.stats import Arcsin, cdf, density
from sympy import Symbol, diff, simplify, nsimplify, N
z = Symbol('z')
a, b = 1, 3
X = Arcsin('x', a, b)
F = cdf(X)(z)
pdf = density(X)(z)
# pick the on-support branch value symbolically by substituting an interior point
pt = 2  # interior
dF = diff(F, z)
lhs = complex(N(dF.subs(z, pt)))
rhs = complex(N(pdf.subs(z, pt)))
print("dF/dx at 2 =", lhs, " pdf at 2 =", rhs)
b0 = complex(N(F.subs(z, a)))
b1 = complex(N(F.subs(z, b)))
print("F(a)=", b0, " F(b)=", b1)
ok = abs(lhs-rhs) < 1e-9 and abs(b0-0) < 1e-9 and abs(b1-1) < 1e-9
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_density_unchanged.py` → holds on the patched tree (good)

```python
# Req 3.1 / 5.2: arcsin density unchanged.
import sys
from sympy.stats import Arcsin, density
from sympy import Symbol, sqrt, pi, simplify
z = Symbol('z'); a = Symbol('a', real=True); b = Symbol('b', real=True)
X = Arcsin('x', a, b)
d = density(X)(z)
expected = 1/(pi*sqrt((-z + b)*(z - a)))
print("density:", d)
sys.exit(0 if simplify(d - expected) == 0 else 1)
```

Attack 5 — `probe_5_family_closedform.py` → holds on the patched tree (good)

```python
# Req 4.1,4.2: every listed distribution's cdf is explicit (no Integral) and completes.
import sys, signal
from sympy.stats import (Arcsin, Dagum, Frechet, Gamma, Erlang, GammaInverse,
                         Kumaraswamy, Laplace, Logistic, Nakagami, StudentT, UniformSum, cdf)
from sympy import Symbol, Integral, Symbol as Sym

def handler(s,f): raise TimeoutError("hang")
signal.signal(signal.SIGALRM, handler)

z = Symbol('z')
p = Symbol('p', positive=True); a = Symbol('a', positive=True); b = Symbol('b', positive=True)
s = Symbol('s', positive=True); m = Symbol('m', real=True)
k = Symbol('k', positive=True); theta = Symbol('theta', positive=True)
mu = Symbol('mu', real=True); bb = Symbol('bb', positive=True)
nu = Symbol('nu', positive=True); n = Symbol('n', integer=True, positive=True)
omega = Symbol('omega', positive=True)

cases = {
 'Arcsin': Arcsin('x', 1, 3),
 'Dagum': Dagum('x', p, a, b),
 'Frechet': Frechet('x', a, s, m),
 'Gamma': Gamma('x', k, theta),
 'Erlang': Erlang('x', 3, 2),
 'GammaInverse': GammaInverse('x', a, b),
 'Kumaraswamy': Kumaraswamy('x', a, b),
 'Laplace': Laplace('x', mu, bb),
 'Logistic': Logistic('x', mu, s),
 'Nakagami': Nakagami('x', k, omega),
 'StudentT': StudentT('x', nu),
 'UniformSum': UniformSum('x', 3),
}
bad = []
for name, X in cases.items():
    signal.alarm(60)
    try:
        e = cdf(X)(z)
        signal.alarm(0)
        hi = e.has(Integral)
        print(name, "-> Integral?", hi)
        if hi:
            bad.append(name)
    except Exception as ex:
        signal.alarm(0)
        print(name, "EXC", type(ex).__name__, ex)
        bad.append(name)
print("bad:", bad)
sys.exit(0 if not bad else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_arcsin_closedform.py`

```python
# Req 1.1 + positive control: arcsin cdf is a closed form, no unevaluated Integral.
import sys
from sympy.stats import Arcsin, cdf
from sympy import Symbol, Integral
z = Symbol('z')
X = Arcsin('x', 1, 3)
e = cdf(X)(z)
print("expr:", e)
print("has Integral:", e.has(Integral))
sys.exit(0 if not e.has(Integral) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on the gold-patched tree.

Probe results (base / patched / weak-candidate):
- probe_1 (Req 1.1: arcsin cdf(X)(z) is closed form, no unevaluated Integral): VIOLATED base / HOLDS patched / HOLDS weak. Serves as positive control — at base cdf(Arcsin) returns an unevaluated Integral; patched returns Piecewise closed form.
- probe_2 (Req 1.2/1.3/1.5: three-region values 0 at x<a, 2*asin(sqrt((x-a)/(b-a)))/pi on support, 1 at x>b; checked at z=0,2,5 for Arcsin(1,3)): VIOLATED base / HOLDS patched.
- probe_3 (Req 2.1/2.2: d/dx of CDF numerically equals density at interior point 2; F(a)=0, F(b)=1): HOLDS patched.
- probe_4 (Req 3.1/5.2: density(Arcsin) unchanged == 1/(pi*sqrt((-x+b)*(x-a)))): HOLDS patched.
- probe_5 (Req 4.1/4.2: cdf of ALL listed distributions — arcsin, Dagum, Frechet, Gamma, Erlang, GammaInverse, Kumaraswamy, Laplace, Logistic, Nakagami, StudentT, UniformSum — returns explicit expr with no Integral and completes within a 60s per-call SIGALRM guard): VIOLATED base / HOLDS patched / VIOLATED under weak candidate.

Discriminating power: positive control probe_1 fails at base and holds patched (prepatch reproduced=true). probe_5 also fails at base and holds patched.

Candidate patch 'weak_arcsin_only' (adds ONLY the arcsin _cdf, omitting the rest of the Req-4 family — the lazy partial fix a narrow reading permits): PASSES probe_1 (arcsin criteria) but is REJECTED by probe_5 (the family distributions still hang/return unevaluated integrals). This demonstrates the suite discriminates a probe-nonconforming partial fix; it is NOT a too-weak finding. The full family requirement (Req 4) is exercised by probe_5 and is what the weak patch fails.

No violation of any mandated behavior found on the patched tree; a plausible partial fix is rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1_arcsin_closedform.py`, `probe_2_piecewise_values.py`, `probe_3_antiderivative.py`, `probe_4_density_unchanged.py`, `probe_5_family_closedform.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_arcsin_closedform.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_arcsin_closedform.py` → holds on the patched tree (good)

Attack 2 — `probe_2_piecewise_values.py` → holds on the patched tree (good)

Attack 3 — `probe_3_antiderivative.py` → holds on the patched tree (good)

Attack 4 — `probe_4_density_unchanged.py` → holds on the patched tree (good)

Attack 5 — `probe_5_family_closedform.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_arcsin_closedform.py`

```python
# Req 1.1 + positive control: arcsin cdf is a closed form, no unevaluated Integral.
import sys
from sympy.stats import Arcsin, cdf
from sympy import Symbol, Integral
z = Symbol('z')
X = Arcsin('x', 1, 3)
e = cdf(X)(z)
print("expr:", e)
print("has Integral:", e.has(Integral))
sys.exit(0 if not e.has(Integral) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

5 distinct probes, all HOLD on the gold-patched tree.

Probe results (base / patched / weak-candidate):
- probe_1 (Req 1.1: arcsin cdf(X)(z) is closed form, no unevaluated Integral): VIOLATED base / HOLDS patched / HOLDS weak. Serves as positive control — at base cdf(Arcsin) returns an unevaluated Integral; patched returns Piecewise closed form.
- probe_2 (Req 1.2/1.3/1.5: three-region values 0 at x<a, 2*asin(sqrt((x-a)/(b-a)))/pi on support, 1 at x>b; checked at z=0,2,5 for Arcsin(1,3)): VIOLATED base / HOLDS patched.
- probe_3 (Req 2.1/2.2: d/dx of CDF numerically equals density at interior point 2; F(a)=0, F(b)=1): HOLDS patched.
- probe_4 (Req 3.1/5.2: density(Arcsin) unchanged == 1/(pi*sqrt((-x+b)*(x-a)))): HOLDS patched.
- probe_5 (Req 4.1/4.2: cdf of ALL listed distributions — arcsin, Dagum, Frechet, Gamma, Erlang, GammaInverse, Kumaraswamy, Laplace, Logistic, Nakagami, StudentT, UniformSum — returns explicit expr with no Integral and completes within a 60s per-call SIGALRM guard): VIOLATED base / HOLDS patched / VIOLATED under weak candidate.

Discriminating power: positive control probe_1 fails at base and holds patched (prepatch reproduced=true). probe_5 also fails at base and holds patched.

Candidate patch 'weak_arcsin_only' (adds ONLY the arcsin _cdf, omitting the rest of the Req-4 family — the lazy partial fix a narrow reading permits): PASSES probe_1 (arcsin criteria) but is REJECTED by probe_5 (the family distributions still hang/return unevaluated integrals). This demonstrates the suite discriminates a probe-nonconforming partial fix; it is NOT a too-weak finding. The full family requirement (Req 4) is exercised by probe_5 and is what the weak patch fails.

No violation of any mandated behavior found on the patched tree; a plausible partial fix is rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: requirements pin the changed observable behavior (cdf return values across the affected family) rather than a narrow helper slice. Req 1-3 give arcsin in full detail (piecewise structure, exact middle expression, boundary conditions in canonicalized orientation, density preservation), and Req 4 correctly enumerates exactly the 11 distributions given _cdf in the patch (arcsin/Dagum/Frechet/Gamma+Erlang/inverse Gamma/Kumaraswamy/Laplace/Logistic/Nakagami/StudentT/uniform-sum). Req 4.4 correctly anticipates the exact-vs-float shape change (Erlang). No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior. Probes on the gold-patched image passed all assertions (exit 0).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document's content is either public via problem_statement or standard mathematics / legitimate behavioral specification. (1) The Requirement 4 distribution family (arcsin, Dagum, Frechet, Gamma/Erlang, inverse Gamma, Kumaraswamy, Laplace, Logistic, Nakagami, StudentT, uniform-sum) is exactly the set enumerated in the public problem_statement's test cases. (2) The detailed arcsin closed form 2*asin(sqrt((x-a)/(b-a)))/pi is the gold _cdf, but problem_statement already states the CDF 'is basically the arcsin function'; this is standard math and the legitimate purpose of specifying the F2P behavior, with no fix-invented identifiers. (3) Req 2's differentiate-to-recover-PDF test method is stated verbatim in the public problem_statement. (4) Req 4.4's exact form 1-exp(-1) equals the public value 0.632120558828558. Crucially, the document does NOT enumerate the hidden test_long_precomputed_cdf parametrizations (Arcsin('A',-5,9), Dagum('D',4,10,3), Erlang('E',14,5), etc.), and contains no test names, file paths, function/class names, or parametrization ids. Naming ArcsinDistribution/crv_types.py is legitimate localization. No semantic leak beyond the public problem_statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
