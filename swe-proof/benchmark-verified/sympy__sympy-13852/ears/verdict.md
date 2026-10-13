# P2 adversarial audit — sympy__sympy-13852

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
"""R1.1 & R1.2: polylog(2,1/2) and polylog(2,2) closed forms.
Positive control leg (also standalone). Holds patched, fails at base."""
import sys
from sympy import polylog, S, pi, log, I, simplify

r_half = polylog(2, S.Half)
expect_half = pi**2/12 - log(2)**2/2
ok_half = simplify(r_half - expect_half) == 0

r_two = polylog(2, 2)
expect_two = pi**2/4 - I*pi*log(2)
ok_two = simplify(r_two - expect_two) == 0

print("polylog(2,1/2) =", r_half, "expected", expect_half, "ok=", ok_half)
print("polylog(2,2)   =", r_two, "expected", expect_two, "ok=", ok_two)

sys.exit(0 if (ok_half and ok_two) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.3 & R1.4: all six recognized order-2 args evaluate to closed form (no
unevaluated polylog) AND numerically agree with unevaluated polylog(2,z)."""
import sys
from sympy import polylog, S, sqrt, N, Abs

args = [S.Half, S(2),
        (sqrt(5)-1)/2, -(sqrt(5)-1)/2, -(sqrt(5)+1)/2, (3-sqrt(5))/2]

allok = True
for z in args:
    r = polylog(2, z)
    is_unevaluated = r.func == polylog
    # numeric agreement vs unevaluated form evaluated numerically
    unev = polylog(2, z, evaluate=False)
    try:
        diff = complex(N(r - unev, 30))
    except Exception as e:
        diff = None
    num_ok = diff is not None and abs(diff) < 1e-12
    ok = (not is_unevaluated) and num_ok
    allok = allok and ok
    print("z=", z, "-> ", r, "| unevaluated?", is_unevaluated, "| numdiff=", diff, "ok=", ok)

sys.exit(0 if allok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.5: order 2 with an UNrecognized argument stays unevaluated polylog(2,z)."""
import sys
from sympy import polylog, S, Rational

allok = True
for z in [Rational(1,3), S(3), Rational(2,5), S(7)]:
    r = polylog(2, z)
    unevaluated = r.func == polylog
    print("z=", z, "-> ", r, "unevaluated?", unevaluated)
    allok = allok and unevaluated

sys.exit(0 if allok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.1, R2.2, R2.3: polylog(0,z)=z/(1-z); polylog(-1,z)=z/(1-z)**2;
and numeric agreement for a concrete z."""
import sys
from sympy import polylog, symbols, simplify, S, N, Rational

z = symbols('z')
r0 = polylog(0, z)
r1 = polylog(-1, z)
ok0 = simplify(r0 - z/(1-z)) == 0
ok1 = simplify(r1 - z/(1-z)**2) == 0
print("polylog(0,z) =", r0, "ok=", ok0)
print("polylog(-1,z) =", r1, "ok=", ok1)

# numeric agreement at a concrete complex z away from 1
zc = S(1)/3 + S(1)/2  # 5/6, real away from 1
num0 = complex(N(polylog(0, zc) - polylog(0, zc, evaluate=False), 30))
num1 = complex(N(polylog(-1, zc) - polylog(-1, zc, evaluate=False), 30))
okn = abs(num0) < 1e-12 and abs(num1) < 1e-12
print("numdiff0=", num0, "numdiff1=", num1, "ok=", okn)

sys.exit(0 if (ok0 and ok1 and okn) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R5.1 & R5.2: expand_func(polylog(1,z)) == -log(1-z) with NO exp_polar factor;
expand_func(polylog(0,z)) == z/(1-z)."""
import sys
from sympy import polylog, symbols, expand_func, log, simplify

z = symbols('z')
e1 = expand_func(polylog(1, z))
has_polar = 'exp_polar' in str(e1)
ok1 = (simplify(e1 - (-log(1 - z))) == 0) and (not has_polar)
print("expand_func(polylog(1,z)) =", e1, "has_exp_polar?", has_polar, "ok=", ok1)

e0 = expand_func(polylog(0, z))
ok0 = simplify(e0 - z/(1 - z)) == 0
print("expand_func(polylog(0,z)) =", e0, "ok=", ok0)

sys.exit(0 if (ok1 and ok0) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R3 & R6 & R4: order-1 numeric consistency; derivative & lerchphi rewrite;
z=1 -> zeta(s); z=-1 -> -dirichlet_eta(s); z=0 -> 0."""
import sys
from sympy import (polylog, symbols, S, N, zeta, dirichlet_eta, lerchphi,
                   simplify, diff)

s, z = symbols('s z')

# R4 special cases (must be preserved)
ok_z1 = polylog(3, 1) == zeta(3)
ok_zm1 = polylog(3, -1) == -dirichlet_eta(3)
r0 = polylog(3, 0)
ok_z0 = (r0 == 0) and hasattr(r0, 'is_zero')
print("z=1->", polylog(3,1), ok_z1, "| z=-1->", polylog(3,-1), ok_zm1, "| z=0->", r0, ok_z0)

# R6.1 derivative
d = polylog(s, z).diff(z)
ok_d = simplify(d - polylog(s-1, z)/z) == 0
print("d/dz polylog(s,z) =", d, "ok=", ok_d)

# R6.2 lerchphi rewrite
rw = polylog(s, z).rewrite(lerchphi)
ok_rw = simplify(rw - z*lerchphi(z, s, 1)) == 0
print("rewrite lerchphi =", rw, "ok=", ok_rw)

# R6.3 fully symbolic stays unevaluated
ok_sym = polylog(s, z).func == polylog
print("polylog(s,z) unevaluated?", ok_sym)

# R3.1 order-1 numeric consistency at a concrete z
zc = S(3)/7
num = complex(N(polylog(1, zc) - polylog(1, zc, evaluate=False), 30))
ok_num = abs(num) < 1e-12
print("order1 numdiff=", num, "ok=", ok_num)

sys.exit(0 if all([ok_z1, ok_zm1, ok_z0, ok_d, ok_rw, ok_sym, ok_num]) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 & R1.2: polylog(2,1/2) and polylog(2,2) closed forms.
Positive control leg (also standalone). Holds patched, fails at base."""
import sys
from sympy import polylog, S, pi, log, I, simplify

r_half = polylog(2, S.Half)
expect_half = pi**2/12 - log(2)**2/2
ok_half = simplify(r_half - expect_half) == 0

r_two = polylog(2, 2)
expect_two = pi**2/4 - I*pi*log(2)
ok_two = simplify(r_two - expect_two) == 0

print("polylog(2,1/2) =", r_half, "expected", expect_half, "ok=", ok_half)
print("polylog(2,2)   =", r_two, "expected", expect_two, "ok=", ok_two)

sys.exit(0 if (ok_half and ok_two) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree; all discriminating ones (1,2,4,5) FAIL at base. Coverage: probe_1=R1.1/R1.2 (polylog(2,1/2) and polylog(2,2) exact closed forms; positive control); probe_2=R1.3/R1.4 (all six recognized order-2 args -> closed form, no unevaluated polylog, numeric agreement <1e-12); probe_3=R1.5 (unrecognized order-2 args stay unevaluated); probe_4=R2.1/R2.2/R2.3 (polylog(0,z)=z/(1-z), polylog(-1,z)=z/(1-z)^2, numeric agreement); probe_5=R5.1/R5.2 (expand_func(polylog(1,z))=-log(1-z) with no exp_polar; expand_func(polylog(0,z))=z/(1-z)); probe_6=R3/R4/R6 regressions (order-1 numeric consistency, z=1->zeta(s), z=-1->-dirichlet_eta(s), z=0->0, derivative polylog(s-1,z)/z, lerchphi rewrite z*lerchphi(z,s,1), fully-symbolic stays unevaluated). Candidate patch 'partial_fix_no_expand_func_cleanup' implements the eval closed-forms exactly but OMITS the _eval_expand_func cleanup (leaves spurious exp_polar factor). Suite REJECTS it via probe_5 (exit 1), demonstrating discriminating power against the lazy/partial fix a weak reading permits. No requirements-conforming candidate found that would fail hidden tests. Verdict advisory; runner re-runs.

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
"""R1.1 & R1.2: polylog(2,1/2) and polylog(2,2) closed forms.
Positive control leg (also standalone). Holds patched, fails at base."""
import sys
from sympy import polylog, S, pi, log, I, simplify

r_half = polylog(2, S.Half)
expect_half = pi**2/12 - log(2)**2/2
ok_half = simplify(r_half - expect_half) == 0

r_two = polylog(2, 2)
expect_two = pi**2/4 - I*pi*log(2)
ok_two = simplify(r_two - expect_two) == 0

print("polylog(2,1/2) =", r_half, "expected", expect_half, "ok=", ok_half)
print("polylog(2,2)   =", r_two, "expected", expect_two, "ok=", ok_two)

sys.exit(0 if (ok_half and ok_two) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree; all discriminating ones (1,2,4,5) FAIL at base. Coverage: probe_1=R1.1/R1.2 (polylog(2,1/2) and polylog(2,2) exact closed forms; positive control); probe_2=R1.3/R1.4 (all six recognized order-2 args -> closed form, no unevaluated polylog, numeric agreement <1e-12); probe_3=R1.5 (unrecognized order-2 args stay unevaluated); probe_4=R2.1/R2.2/R2.3 (polylog(0,z)=z/(1-z), polylog(-1,z)=z/(1-z)^2, numeric agreement); probe_5=R5.1/R5.2 (expand_func(polylog(1,z))=-log(1-z) with no exp_polar; expand_func(polylog(0,z))=z/(1-z)); probe_6=R3/R4/R6 regressions (order-1 numeric consistency, z=1->zeta(s), z=-1->-dirichlet_eta(s), z=0->0, derivative polylog(s-1,z)/z, lerchphi rewrite z*lerchphi(z,s,1), fully-symbolic stays unevaluated). Candidate patch 'partial_fix_no_expand_func_cleanup' implements the eval closed-forms exactly but OMITS the _eval_expand_func cleanup (leaves spurious exp_polar factor). Suite REJECTS it via probe_5 (exit 1), demonstrating discriminating power against the lazy/partial fix a weak reading permits. No requirements-conforming candidate found that would fail hidden tests. Verdict advisory; runner re-runs.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probes p1/p2 both exit 0 (assertion-guarded). Requirements accurately mirror the exact six-argument table and the two formula-string values (pi**2/4-I*pi*log(2) for z=2 matches patch), and correctly cover the exp_polar removal at s=1. Boundary is the observable changed behavior (eval + expand_func), not one branch. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md translates the gold edit into behavioral requirements without transmitting the hidden tests. The problem_statement already discloses polylog(2,1/2)=pi**2/12-log(2)**2/2, the exp_polar(-I*pi) bug, that expand_func(polylog(1,z)) should be -log(1-z), and the derivative z/(1-z). The doc's additions (polylog(2,2)=pi**2/4-I*pi*log(2); the four golden-ratio arguments; polylog(0,z)=z/(1-z); polylog(-1,z)=z/(1-z)**2) are the mathematically correct closed forms being added by the gold patch to polylog.eval — legitimate behavioral description of the change, and standard dilogarithm special values a domain expert derives, not fix-invented identifiers. The six-argument enumeration (Req 1.3) mirrors the test's z-list, but these are the actual math special cases the eval implements, not test-only artifacts; describing them is the point of the spec. Naming zeta/dirichlet_eta/stieltjes/zeta_functions is legitimate module localization of sibling behavior to preserve. No test file paths, no test/class/function names (test_polylog_values, test_zeta_eval, etc. do NOT appear), no parametrization ids, no verbatim test code, no evaluate=False API detail leaked. The 1e-15 tolerance is hedged as 'on the order of' generic float precision, not a distinctive test constant.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
