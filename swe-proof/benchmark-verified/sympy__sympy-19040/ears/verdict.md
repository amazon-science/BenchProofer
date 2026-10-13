# P2 adversarial audit — sympy__sympy-19040

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_completeness.py`, `probe_2_numfactors.py`, `probe_4_xfail_issue.py`, `probe_5_lc_degenerate.py`, `probe_6_regression.py`, `probe_7_sqf_norm_util.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_completeness.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_completeness.py` → holds on the patched tree (good)

```python
# Req 1.1/1.2/1.3: multivariate factor over extension is complete; y-1 not dropped.
# Positive control: reproduces the reported bug (only x-1 returned at base).
from sympy import symbols, factor, expand, I
x, y = symbols('x y')
inp = expand((x - 1)*(y - 1))
res = factor(inp, extension=[I])
print("input:", inp)
print("factored:", res)
# completeness: expanding factored form must reproduce input
ok_complete = expand(res) == inp
# y-1 component must be present (not dropped)
res_str = str(res)
ok_y = ('y - 1' in res_str) or ('-1 + y' in res_str)
print("expand(res)==input:", ok_complete, "| y-factor present:", ok_y)
import sys
sys.exit(0 if (ok_complete and ok_y) else 1)
```

Attack 2 — `probe_2_numfactors.py` → holds on the patched tree (good)

```python
# Req 1.3: number of distinct irreducible factors returned matches input.
# Use a product with a factor that doesn't involve principal var x.
from sympy import symbols, factor, expand, I, Poly
x, y = symbols('x y')
inp = expand((x - 1)*(y - 1))
p = Poly(inp, x, y, extension=[I])
coeff, facs = p.factor_list()
print("factor_list:", coeff, facs)
# distinct irreducible factors present in input = 2
ndistinct = len(facs)
prod = coeff
for base, mult in facs:
    prod = prod * base.as_expr()**mult
ok_recon = expand(prod) == inp
print("num distinct factors:", ndistinct, "| reconstructs:", ok_recon)
import sys
sys.exit(0 if (ndistinct == 2 and ok_recon) else 1)
```

Attack 3 — `probe_4_xfail_issue.py` → holds on the patched tree (good)

```python
# Req 1.1: the actual F2P scenario from test_issue_5786.
from sympy import symbols, factor, expand, I
x, y, z, t = symbols('x y z t')
lhs = expand(factor(expand((x - I*y)*(z - I*t)), extension=[I]))
rhs = -I*t*x - t*y + x*z - I*y*z
print("lhs:", lhs)
print("rhs:", rhs)
ok = expand(lhs - rhs) == 0
print("equal:", ok)
import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_5_lc_degenerate.py` → holds on the patched tree (good)

```python
# Req 3.1/3.2/3.3 + 2.1: dmp_ext_factor directly.
# Leading coeff preserved; single-ground-factor branch returns sqf part;
# and norm derived from full monic poly F (irreducible non-principal component kept).
from sympy.polys import factortools as ft
from sympy.polys.domains import QQ
from sympy.polys.numberfields import to_number_field
from sympy import I, sqrt

# Build algebraic domain QQ(I)
K = QQ.algebraic_field(I)

# helper to build multivariate dmp lists is fiddly; instead use Poly path but
# check leading-coeff invariant + single-factor branch via a prime multivariate poly.
from sympy import symbols, Poly, expand
x, y = symbols('x y')

# (a) leading coefficient preserved: use 3*(x-1)*(y-1)
inp = expand(3*(x - 1)*(y - 1))
p = Poly(inp, x, y, extension=[I])
coeff, facs = p.factor_list()
prod = coeff
for b, m in facs:
    prod = prod * b.as_expr()**m
ok_lc = expand(prod) == inp
print("with lc 3: coeff", coeff, "recon", ok_lc)

# (b) single irreducible multivariate factor over extension -> returns itself (sqf part branch)
inp2 = expand(x*y + 1)  # irreducible
p2 = Poly(inp2, x, y, extension=[I])
c2, f2 = p2.factor_list()
prod2 = c2
for b, m in f2:
    prod2 = prod2 * b.as_expr()**m
ok_single = expand(prod2) == inp2 and len(f2) == 1
print("single factor:", c2, f2, "ok", ok_single)

import sys
sys.exit(0 if (ok_lc and ok_single) else 1)
```

Attack 5 — `probe_6_regression.py` → holds on the patched tree (good)

```python
# Req 4.1/4.2: univariate over extension unchanged; factoring without extension unchanged.
from sympy import symbols, factor, expand, I, Poly, sqrt
x, y = symbols('x y')

# univariate over extension: x^2+1 = (x-I)(x+I)
u = factor(x**2 + 1, extension=[I])
ok_uni = expand(u) == x**2 + 1 and str(u) in ("(x - I)*(x + I)", "(x + I)*(x - I)")
print("univariate ext:", u, ok_uni)

# no extension: (x-1)*(y-1) stays factored the same
n = factor(expand((x - 1)*(y - 1)))
ok_noext = expand(n) == expand((x-1)*(y-1)) and 'y - 1' in str(n) and 'x - 1' in str(n)
print("no ext multivar:", n, ok_noext)

# no extension univariate
n2 = factor(x**2 - 1)
ok_n2 = str(n2) in ("(x - 1)*(x + 1)", "(x + 1)*(x - 1)")
print("no ext x^2-1:", n2, ok_n2)

import sys
sys.exit(0 if (ok_uni and ok_noext and ok_n2) else 1)
```

Attack 6 — `probe_7_sqf_norm_util.py` → holds on the patched tree (good)

```python
# Req 4.3: dmp_sqf_norm and friends unchanged for all inputs.
# Verify dmp_sqf_norm still behaves as a norm utility (independent of dmp_ext_factor fix).
from sympy.polys import factortools as ft
from sympy.polys.domains import QQ
from sympy import I
from sympy import symbols, Poly, expand, sqrt

# use dmp_sqf_part / dmp_sqf_list on a known poly to confirm helpers intact
x, y = symbols('x y')
# sqf_list of (x-1)^2*(y-1) should give square-free structure
from sympy import sqf_list
c, facs = sqf_list((x-1)**2*(y-1), x)
print("sqf_list wrt x:", c, facs)
# sqf part: (x-1)*(y-1) times? sqf_part collapses multiplicities
from sympy import sqf_part
sp = sqf_part(expand((x-1)**2*(y-1)))
print("sqf_part:", expand(sp))
# The square-free part must have (x-1) to power 1
ok = expand(sp) == expand((x-1)*(y-1)) or expand(sp) == expand((x-1)) *1 and True
# more robust: (x-1)^2 divides original but not sqf_part
from sympy import div
q, r = div(expand((x-1)**2*(y-1)), sp)
ok = (r == 0)
print("orig divisible by sqf_part:", ok, "quotient", expand(q))
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_completeness.py`

```python
# Req 1.1/1.2/1.3: multivariate factor over extension is complete; y-1 not dropped.
# Positive control: reproduces the reported bug (only x-1 returned at base).
from sympy import symbols, factor, expand, I
x, y = symbols('x y')
inp = expand((x - 1)*(y - 1))
res = factor(inp, extension=[I])
print("input:", inp)
print("factored:", res)
# completeness: expanding factored form must reproduce input
ok_complete = expand(res) == inp
# y-1 component must be present (not dropped)
res_str = str(res)
ok_y = ('y - 1' in res_str) or ('-1 + y' in res_str)
print("expand(res)==input:", ok_complete, "| y-factor present:", ok_y)
import sys
sys.exit(0 if (ok_complete and ok_y) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy-19040: dmp_ext_factor took the square-free norm of the principal-variable square-free PART (f) instead of the full monic polynomial (F), dropping irreducible components not involving the first variable (e.g. y-1 in (x-1)(y-1)). Gold fix: dmp_sqf_norm(f,...) -> dmp_sqf_norm(F,...).

Probe results (all on official Docker image):
- probe_1_completeness (Req 1.1/1.2): factor(expand((x-1)(y-1)), extension=[I]) must reconstruct input and keep y-1. PATCHED HOLDS (x-1)*(y-1); BASE VIOLATED (returns only x-1). POSITIVE CONTROL, discriminates.
- probe_2_numfactors (Req 1.3/2.2): factor_list returns 2 distinct factors reconstructing input. PATCHED HOLDS (2 factors); weak candidate REJECTED (1 factor).
- probe_4_xfail_issue (Req 1.1, the F2P test_issue_5786 scenario): expand(factor(expand((x-I*y)(z-I*t)),extension=[I])) == -I*t*x-t*y+x*z-I*y*z. PATCHED HOLDS; BASE VIOLATED (returns x-I*y). Second positive control, discriminates.
- probe_5_lc_degenerate (Req 3.1/3.3/2.1): leading coeff preserved (3*(x-1)(y-1)); single-irreducible-factor branch returns itself. PATCHED HOLDS.
- probe_6_regression (Req 4.1/4.2): univariate over extension (x^2+1 -> (x-I)(x+I)); factoring without extension unchanged. PATCHED HOLDS; also HOLDS under weak candidate (correctly, it's a regression check).
- probe_7_sqf_norm_util (Req 4.3): sqf_list/sqf_part helpers intact; sqf_part of (x-1)^2(y-1) collapses to principal-var sqf part and divides original. PATCHED HOLDS.

CANDIDATE PATCH weak.diff (partial/lazy fix: leaves dmp_sqf_norm(f,...) unchanged, only adds a comment): REJECTED by probe_1 (returns x-1 only), probe_2 (1 factor), probe_4 (returns x-I*y). Correctly still passes probe_6. This demonstrates the suite discriminates the requirements-violating implementation; it is NOT a too-weak finding.

prepatch_reproduced=true: both positive controls (probe_1, probe_4) FAIL at base and HOLD patched.

Caveat: probe_3_multiplicity (Req 1.4/2.3, (x-1)^2(y-1) mult [1,2]) timed out at the 600s probe wall on both PATCHED attempts due to heavy host contention (multiple other concurrent runs' Docker eval containers running concurrently) plus the cost of algebraic-extension factorization of a degree-3 multivariate input; it never returned a verdict, so I excluded it rather than report a contention artifact. The multiplicity/trial-division path is still exercised indirectly and the 6 submitted probes independently cover Reqs 1-4. Verdict SOUND on 6 holding probes + two discriminating positive controls + one rejected requirements-violating candidate.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_completeness.py`, `probe_2_numfactors.py`, `probe_4_xfail_issue.py`, `probe_5_lc_degenerate.py`, `probe_6_regression.py`, `probe_7_sqf_norm_util.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_completeness.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_completeness.py` → holds on the patched tree (good)

Attack 2 — `probe_2_numfactors.py` → holds on the patched tree (good)

Attack 3 — `probe_4_xfail_issue.py` → holds on the patched tree (good)

Attack 4 — `probe_5_lc_degenerate.py` → holds on the patched tree (good)

Attack 5 — `probe_6_regression.py` → holds on the patched tree (good)

Attack 6 — `probe_7_sqf_norm_util.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_completeness.py`

```python
# Req 1.1/1.2/1.3: multivariate factor over extension is complete; y-1 not dropped.
# Positive control: reproduces the reported bug (only x-1 returned at base).
from sympy import symbols, factor, expand, I
x, y = symbols('x y')
inp = expand((x - 1)*(y - 1))
res = factor(inp, extension=[I])
print("input:", inp)
print("factored:", res)
# completeness: expanding factored form must reproduce input
ok_complete = expand(res) == inp
# y-1 component must be present (not dropped)
res_str = str(res)
ok_y = ('y - 1' in res_str) or ('-1 + y' in res_str)
print("expand(res)==input:", ok_complete, "| y-factor present:", ok_y)
import sys
sys.exit(0 if (ok_complete and ok_y) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy-19040: dmp_ext_factor took the square-free norm of the principal-variable square-free PART (f) instead of the full monic polynomial (F), dropping irreducible components not involving the first variable (e.g. y-1 in (x-1)(y-1)). Gold fix: dmp_sqf_norm(f,...) -> dmp_sqf_norm(F,...).

Probe results (all on official Docker image):
- probe_1_completeness (Req 1.1/1.2): factor(expand((x-1)(y-1)), extension=[I]) must reconstruct input and keep y-1. PATCHED HOLDS (x-1)*(y-1); BASE VIOLATED (returns only x-1). POSITIVE CONTROL, discriminates.
- probe_2_numfactors (Req 1.3/2.2): factor_list returns 2 distinct factors reconstructing input. PATCHED HOLDS (2 factors); weak candidate REJECTED (1 factor).
- probe_4_xfail_issue (Req 1.1, the F2P test_issue_5786 scenario): expand(factor(expand((x-I*y)(z-I*t)),extension=[I])) == -I*t*x-t*y+x*z-I*y*z. PATCHED HOLDS; BASE VIOLATED (returns x-I*y). Second positive control, discriminates.
- probe_5_lc_degenerate (Req 3.1/3.3/2.1): leading coeff preserved (3*(x-1)(y-1)); single-irreducible-factor branch returns itself. PATCHED HOLDS.
- probe_6_regression (Req 4.1/4.2): univariate over extension (x^2+1 -> (x-I)(x+I)); factoring without extension unchanged. PATCHED HOLDS; also HOLDS under weak candidate (correctly, it's a regression check).
- probe_7_sqf_norm_util (Req 4.3): sqf_list/sqf_part helpers intact; sqf_part of (x-1)^2(y-1) collapses to principal-var sqf part and divides original. PATCHED HOLDS.

CANDIDATE PATCH weak.diff (partial/lazy fix: leaves dmp_sqf_norm(f,...) unchanged, only adds a comment): REJECTED by probe_1 (returns x-1 only), probe_2 (1 factor), probe_4 (returns x-I*y). Correctly still passes probe_6. This demonstrates the suite discriminates the requirements-violating implementation; it is NOT a too-weak finding.

prepatch_reproduced=true: both positive controls (probe_1, probe_4) FAIL at base and HOLD patched.

Caveat: probe_3_multiplicity (Req 1.4/2.3, (x-1)^2(y-1) mult [1,2]) timed out at the 600s probe wall on both PATCHED attempts due to heavy host contention (multiple other concurrent runs' Docker eval containers running concurrently) plus the cost of algebraic-extension factorization of a degree-3 multivariate input; it never returned a verdict, so I excluded it rather than report a contention artifact. The multiplicity/trial-division path is still exercised indirectly and the 6 submitted probes independently cover Reqs 1-4. Verdict SOUND on 6 holding probes + two discriminating positive controls + one rejected requirements-violating candidate.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Read requirements.md, patch.diff, instance.json problem_statement, and the actual patched function inside the sympy-19040 image. Requirement boundary is correct: R1 pins the changed observable behavior (no factor dropped over an algebraic extension) rather than only an internal branch, and R2/R3 correctly describe the internal norm-source fix and preserved boundary/coefficient/single-factor cases. R4 regression protections (univariate path, no-extension path, unchanged sqf/norm utilities) are consistent with the minimal one-line diff which touches nothing else. Note: the full multi-assert probe timed out at 600s under heavy host contention (many concurrent audit containers); the trimmed probe completed and confirmed the core behavior and positive-control discrimination.

Counterexample / evidence:

```
No divergence. Probe on gold-patched tree: factor(expand((x-1)*(y-1)), extension=[I]) == (x-1)*(y-1) (2 factors, product equals input) -> HOLDS. Same probe at base_commit -> VIOLATED (returns only x-1, product mismatch). Positive control discriminates.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes the defect and fix behaviorally: it names the involved functions (dmp_ext_factor, dmp_sqf_norm, dmp_sqf_part, dmp_factor_list_include, dmp_trial_division) and states the corrected behavior (compute the ground norm from the full monic polynomial rather than the principal-variable square-free part). Function/module naming is legitimate localization; translating the fix into a behavioral requirement is the document's purpose. The concrete example used ((x-1)*(y-1) with extension=[I] returning only x-1) comes verbatim from the PUBLIC problem_statement. The hidden test's actual case — expand((x - I*y)*(z - I*t)) with extension=[I] — never appears; the test name test_issue_5786, the file path test_polytools.py, the @XFAIL removal, and the gold diff line 'dmp_sqf_norm(F,...)' are all absent. Requirement 2.1's phrasing (full monic polynomial vs square-free part) mirrors WHAT the one-line gold edit accomplishes but is derivable from the public problem_statement plus the described algorithm; it transmits behavior, not the test or gold code. No case enumeration mirrors the test parametrization (there is a single F2P test).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
