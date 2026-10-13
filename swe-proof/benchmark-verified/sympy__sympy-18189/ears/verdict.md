# P2 adversarial audit — sympy__sympy-18189

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
"""Positive control / Req 1.1,1.2,1.4: permute=True with non-canonical syms=(y,x)
returns the complete set of 8 permutations, arranged in syms order."""
import sys
from sympy.abc import x, y
from sympy.solvers.diophantine import diophantine

expected = set([(-3, -2), (-3, 2), (-2, -3), (-2, 3),
                (2, -3), (2, 3), (3, -2), (3, 2)])
res = diophantine(y**4 + x**4 - 2**4 - 3**4, syms=(y, x), permute=True)
print("syms=(y,x) permute=True ->", sorted(res), "n=", len(res))
if res != expected:
    print("FAIL: expected", sorted(expected))
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.3: two different syms orderings yield same COUNT and, after reordering
into a common variable order, the SAME set. Use a NON-symmetric equation so the
count/reorder check is meaningful (x**2 + y**2 + 3*x - 5)."""
import sys
from sympy.abc import x, y
from sympy.solvers.diophantine import diophantine

eq = x**2 + y**2 + 3*x - 5
r_xy = diophantine(eq, syms=(x, y), permute=True)   # tuples (x,y)
r_yx = diophantine(eq, syms=(y, x), permute=True)   # tuples (y,x)
print("n(x,y)=", len(r_xy), "n(y,x)=", len(r_yx))
# reorder r_yx tuples (y,x)->(x,y)
r_yx_common = set((b, a) for (a, b) in r_yx)
print("xy   :", sorted(r_xy))
print("yx->xy:", sorted(r_yx_common))
if len(r_xy) != len(r_yx):
    print("FAIL: counts differ")
    sys.exit(1)
if r_xy != r_yx_common:
    print("FAIL: sets differ after common reorder")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.1: non-canonical syms result equals the default (canonical) permute
result, up to the syms-imposed reorder. Default order is canonical (x before y)."""
import sys
from sympy.abc import x, y
from sympy.solvers.diophantine import diophantine

eq = y**4 + x**4 - 2**4 - 3**4
default = diophantine(eq, permute=True)              # canonical tuples (x,y)
r_yx = diophantine(eq, syms=(y, x), permute=True)    # tuples (y,x)
r_yx_as_xy = set((b, a) for (a, b) in r_yx)
print("default(canonical):", sorted(default), "n=", len(default))
print("syms=(y,x)->(x,y) :", sorted(r_yx_as_xy), "n=", len(r_yx_as_xy))
if default != r_yx_as_xy:
    print("FAIL: non-canonical syms result differs from canonical")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.2 / 3.2: permute=False (default) with an explicit non-canonical syms
returns exactly the base solution set, components in syms order, unchanged.
For x**2 + y**2 + 3*x - 5 the base solution (canonical) is {(-1,1)} ... verify
that syms=(y,x) gives the same base tuples reordered, and NOT permuted."""
import sys
from sympy.abc import x, y
from sympy.solvers.diophantine import diophantine

eq = x**2 + y**2 + 3*x - 5
base_xy = diophantine(eq, syms=(x, y))         # permute default False
base_yx = diophantine(eq, syms=(y, x))
perm_xy = diophantine(eq, syms=(x, y), permute=True)
print("base xy:", sorted(base_xy))
print("base yx:", sorted(base_yx))
print("perm xy:", sorted(perm_xy), "n=", len(perm_xy))
# base must be reorder-equivalent between the two syms orders
if set((b, a) for (a, b) in base_yx) != base_xy:
    print("FAIL: base set changed with syms order")
    sys.exit(1)
# base must be a STRICT subset (smaller) than permuted -> permute=False did not permute
if not (base_xy < perm_xy):
    print("FAIL: permute=False did not return the smaller base set")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.4 + 3.2 + 3.5 regressions:
- syms not a sequence -> TypeError
- permute default False without syms returns base set
- no-solution equation returns empty set"""
import sys
from sympy.abc import x, y
from sympy.solvers.diophantine import diophantine

ok = True

# 3.4 TypeError when syms not a sequence
try:
    diophantine(x**2 + y**2 - 25, syms=x)
    print("FAIL: no TypeError for non-sequence syms")
    ok = False
except TypeError as e:
    print("TypeError raised as expected:", e)

# 3.2 default permute False without syms
base = diophantine(x**2 + y**2 - 25)
print("base 25:", sorted(base))
if not base:
    print("FAIL: expected non-empty base for x^2+y^2=25")
    ok = False

# 3.5 empty set for no integer solution: x^2 + y^2 + 3 = 0 has none
empty = diophantine(x**2 + y**2 + 3)
print("empty case:", empty)
if empty != set():
    print("FAIL: expected empty set")
    ok = False

if not ok:
    sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req 1.1,1.2,1.4: permute=True with non-canonical syms=(y,x)
returns the complete set of 8 permutations, arranged in syms order."""
import sys
from sympy.abc import x, y
from sympy.solvers.diophantine import diophantine

expected = set([(-3, -2), (-3, 2), (-2, -3), (-2, 3),
                (2, -3), (2, 3), (3, -2), (3, 2)])
res = diophantine(y**4 + x**4 - 2**4 - 3**4, syms=(y, x), permute=True)
print("syms=(y,x) permute=True ->", sorted(res), "n=", len(res))
if res != expected:
    print("FAIL: expected", sorted(expected))
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover Req1 (completeness/order-independence of permute=True across syms orderings), Req2 (syms only reorders; permute=False keeps base set), Req3 regressions (TypeError on non-sequence syms, base set default, empty set no-solution).

Probe->requirement->results (exit0=HOLDS):
- probe_1 (Req1.1/1.2/1.4, POSITIVE CONTROL): syms=(y,x),permute=True on y^4+x^4-2^4-3^4 returns all 8 perms. PATCHED HOLDS(8 sols); BASE VIOLATED(only 1 sol -> reproduces bug); WEAK HOLDS.
- probe_2 (Req1.3): non-symmetric eq x^2+y^2+3x-5, syms=(x,y) vs (y,x) same count(8) and equal after common reorder. PATCHED HOLDS; BASE VIOLATED (8 vs 4).
- probe_3 (Req1.1): non-canonical syms result equals canonical default permute result after reorder. PATCHED HOLDS; BASE VIOLATED (8 vs 1).
- probe_4 (Req2.2/3.2): permute=False + non-canonical syms returns base set (reorder-invariant, strict subset of permuted). PATCHED HOLDS; BASE HOLDS; WEAK REJECTED (base_yx wrongly permuted to 8 sols).
- probe_5 (Req3.4/3.2/3.5): TypeError on non-sequence syms; base set for x^2+y^2-25; empty set for x^2+y^2+3. PATCHED HOLDS; BASE HOLDS.

Discriminating power: probes 1,2,3 all FAIL at base and HOLD patched (positive control probe_1 confirmed: base=1 sol, patched=8). 

CANDIDATE PATCH (weak.diff): forwards permute=True hardcoded instead of permute=permute in the recursive call. This satisfies the permute=True completeness probes (1,2,3 pass) but is REJECTED by probe_4 because it also permutes when the caller passed permute=False + non-canonical syms, violating Req2.2/3.2. Demonstrates the suite discriminates the lazy fix; the gold patch's permute=permute is the faithful fix. All 5 probes hold on the gold-patched tree; verdict SOUND.

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
"""Positive control / Req 1.1,1.2,1.4: permute=True with non-canonical syms=(y,x)
returns the complete set of 8 permutations, arranged in syms order."""
import sys
from sympy.abc import x, y
from sympy.solvers.diophantine import diophantine

expected = set([(-3, -2), (-3, 2), (-2, -3), (-2, 3),
                (2, -3), (2, 3), (3, -2), (3, 2)])
res = diophantine(y**4 + x**4 - 2**4 - 3**4, syms=(y, x), permute=True)
print("syms=(y,x) permute=True ->", sorted(res), "n=", len(res))
if res != expected:
    print("FAIL: expected", sorted(expected))
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

5 probes cover Req1 (completeness/order-independence of permute=True across syms orderings), Req2 (syms only reorders; permute=False keeps base set), Req3 regressions (TypeError on non-sequence syms, base set default, empty set no-solution).

Probe->requirement->results (exit0=HOLDS):
- probe_1 (Req1.1/1.2/1.4, POSITIVE CONTROL): syms=(y,x),permute=True on y^4+x^4-2^4-3^4 returns all 8 perms. PATCHED HOLDS(8 sols); BASE VIOLATED(only 1 sol -> reproduces bug); WEAK HOLDS.
- probe_2 (Req1.3): non-symmetric eq x^2+y^2+3x-5, syms=(x,y) vs (y,x) same count(8) and equal after common reorder. PATCHED HOLDS; BASE VIOLATED (8 vs 4).
- probe_3 (Req1.1): non-canonical syms result equals canonical default permute result after reorder. PATCHED HOLDS; BASE VIOLATED (8 vs 1).
- probe_4 (Req2.2/3.2): permute=False + non-canonical syms returns base set (reorder-invariant, strict subset of permuted). PATCHED HOLDS; BASE HOLDS; WEAK REJECTED (base_yx wrongly permuted to 8 sols).
- probe_5 (Req3.4/3.2/3.5): TypeError on non-sequence syms; base set for x^2+y^2-25; empty set for x^2+y^2+3. PATCHED HOLDS; BASE HOLDS.

Discriminating power: probes 1,2,3 all FAIL at base and HOLD patched (positive control probe_1 confirmed: base=1 sol, patched=8). 

CANDIDATE PATCH (weak.diff): forwards permute=True hardcoded instead of permute=permute in the recursive call. This satisfies the permute=True completeness probes (1,2,3 pass) but is REJECTED by probe_4 because it also permutes when the caller passed permute=False + non-canonical syms, violating Req2.2/3.2. Demonstrates the suite discriminates the lazy fix; the gold patch's permute=permute is the faithful fix. All 5 probes hold on the gold-patched tree; verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch forwards permute=permute into the recursive reorder call. Probe on patched tree: len 8 == 8, equal-after-reorder True. Base: 8 vs 1 (VIOLATED). Also verified diophantine(eq, syms=(n,m)) -> {(3,2)} vs base {(2,3)} (Req 2.2/2.3) and TypeError 'syms should be given as a sequence' (Req 3.4). Requirements are faithful to the actual change.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md contains no hidden-test/gold-derived content. (1) The failing scenario — diophantine(n**4+m**4-2**4-3**4, syms=(m,n) vs (n,m), permute=True) yielding incomplete results — is entirely in the PUBLIC problem_statement, including the full 8-tuple solution set. The document does NOT even reproduce that specific solution set or equation; it describes the ordering-independence property abstractly. (2) The gold fix (forwarding permute= into the recursive call) is described in prose (Req 2.1) but the fix is also fully disclosed in the public problem_statement/hints diff; describing the fixed behavior is the whole point and localizing to the recursive reorder branch of diophantine is legitimate. (3) No test function names (test_diophantine), no file path (sympy/solvers/tests/test_diophantine.py), no test variable names (x,y vs the problem's m,n), no parametrization ids, no verbatim gold lines, no fix-invented identifiers. (4) The equation-type enumeration in Req 3.3 (linear, binary quadratic, univariate, general-sum-of-squares, general-sum-of-even-powers, general-Pythagorean, ternary quadratic) is diophantine's own documented classification vocabulary / public API scope, not a mirror of the PASS_TO_PASS test list — it reads as regression-protection scope, not test reconstruction. (5) Req 3.4 (TypeError when syms not a sequence) is existing documented API behavior, not test-derived. No semantic leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
