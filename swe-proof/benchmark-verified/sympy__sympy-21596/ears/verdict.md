# P2 adversarial audit — sympy__sympy-21596

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Requirement 1.4 + positive control: the canonical example
# imageset(Lambda(n, n + (n-1)*(n+1)*I), Integers).intersect(Reals) == {-1, 1}
import sys
from sympy import I, Lambda, S, FiniteSet
from sympy.abc import n
from sympy import imageset

res = imageset(Lambda(n, n + (n - 1)*(n + 1)*I), S.Integers).intersect(S.Reals)
expected = FiniteSet(-1, 1)
print("result:", res)
print("expected:", expected)
ok = (res == expected)
print("equal:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Requirement 1.5 + 1.6: membership consistency. 2 is not a real image; must be False.
# Also -1 and 1 must be members.
import sys
from sympy import I, Lambda, S
from sympy.abc import n
from sympy import imageset

inter = imageset(Lambda(n, n + (n - 1)*(n + 1)*I), S.Integers).intersect(S.Reals)
m2 = inter.contains(2)
mm1 = inter.contains(-1)
m1 = inter.contains(1)
print("2 in inter:", m2)
print("-1 in inter:", mm1)
print("1 in inter:", m1)
ok = (m2 == False) and (mm1 == True) and (m1 == True)
print("ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Requirement 2.2: non-integer root of vanishing condition excluded.
# im = (n-1)*(n+1/2); over Integers only n=1 gives real -> {1}
import sys
from sympy import I, Lambda, S, FiniteSet
from sympy.abc import n
from sympy import imageset

im = (n - 1)*(n + S.Half)
res = imageset(Lambda(n, n + im*I), S.Integers).intersect(S.Reals)
expected = FiniteSet(1)
print("result:", res)
print("expected:", expected)
ok = (res == expected)
print("equal:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Requirement 2.3 + 3.1: Naturals0 domain, multi-factor imaginary part.
# im*(n+1) with im=(n-1)*(n+1/2); over Naturals0 -> {1}
import sys
from sympy import I, Lambda, S, FiniteSet
from sympy.abc import n
from sympy import imageset

im = (n - 1)*(n + S.Half)
res = imageset(Lambda(n, n + im*(n + 1)*I), S.Naturals0).intersect(S.Reals)
expected = FiniteSet(1)
print("result:", res)
print("expected:", expected)
ok = (res == expected)
print("equal:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Requirement 3.3 + 3.4: non-linear vanishing -> ConditionSet-based ImageSet result.
import sys
from sympy import I, Lambda, S, FiniteSet, ImageSet, ConditionSet, Eq, Symbol
from sympy.abc import n
from sympy import imageset

im = (n - 1)*(n + S.Half)
res = imageset(Lambda(n, n/2 + im.expand()*I), S.Integers).intersect(S.Reals)
x = Symbol('x')
expected = ImageSet(Lambda(x, x/2), ConditionSet(n, Eq(n**2 - n/2 - S(1)/2, 0), S.Integers))
print("result:", res)
print("expected:", expected)
ok = (res == expected)
print("equal:", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Requirement 4.1/4.3/4.5: rational family with parameter-dependent denominator.
# n/(1/n - 1) + im*(n+1)*I over Integers -> {1/2}
import sys
from sympy import I, Lambda, S, FiniteSet
from sympy.abc import n
from sympy import imageset

im = (n - 1)*(n + S.Half)
res = imageset(Lambda(n, n/(1/n - 1) + im*(n + 1)*I), S.Integers).intersect(S.Reals)
expected = FiniteSet(S.Half)
print("result:", res)
print("expected:", expected)
ok = (res == expected)
print("equal:", ok)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Requirement 4.4: after excluding poles, no surviving parameter -> EmptySet.
# n/(n**2-9) + (n-3)*(n+1)*I/(2*n+2) over Integers -> EmptySet
# and the defined non-empty variant -> {-1}
import sys
from sympy import I, Lambda, S, FiniteSet
from sympy.abc import n
from sympy import imageset

res_empty = imageset(Lambda(n, n/(n**2 - 9) + (n - 3)*(n + 1)*I/(2*n + 2)), S.Integers).intersect(S.Reals)
res_neg1 = imageset(Lambda(n, n/(n - 6) + (n - 3)*(n + 1)*I/(2*n + 2)), S.Integers).intersect(S.Reals)
print("empty result:", res_empty)
print("neg1 result:", res_neg1)
ok = (res_empty is S.EmptySet) and (res_neg1 == FiniteSet(-1))
print("ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# Requirement 5.6: complex real-valued construction (log + trig) over integers preserved.
import sys
from sympy import I, Lambda, S, pi, log, Abs, sqrt, ImageSet
from sympy.abc import n
from sympy import imageset

s = ImageSet(Lambda(n, -I*(I*(2*pi*n - pi/4) + log(Abs(sqrt(-I))))), S.Integers)
res = s.intersect(S.Reals)
# expected: canonical image imageset(Lambda(n, 2*n*pi - pi/4), Integers)
expected = imageset(Lambda(n, 2*n*pi - pi/4), S.Integers)
print("result:", res)
print("expected:", expected)
ok = (res == expected)
print("equal:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Requirement 1.4 + positive control: the canonical example
# imageset(Lambda(n, n + (n-1)*(n+1)*I), Integers).intersect(Reals) == {-1, 1}
import sys
from sympy import I, Lambda, S, FiniteSet
from sympy.abc import n
from sympy import imageset

res = imageset(Lambda(n, n + (n - 1)*(n + 1)*I), S.Integers).intersect(S.Reals)
expected = FiniteSet(-1, 1)
print("result:", res)
print("expected:", expected)
ok = (res == expected)
print("equal:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-21596: fix to the `if other == S.Reals:` branch of ImageSet intersection_sets — keep (intersect) rather than remove (set-difference) the imaginary-part zero set, exclude actual denominator poles, and handle multi-factor / non-linear / rational cases.

### PROBES (all HOLD on gold-patched tree; imageset imported from top-level `sympy`, not sympy.sets.fancysets):
- probe_1 (Req 1.2/1.4, POSITIVE CONTROL): imageset(Lambda(n, n+(n-1)*(n+1)*I), Integers).intersect(Reals) == FiniteSet(-1,1). Patched: HOLDS (FiniteSet(-1,1)). Base: VIOLATED (Complement(Integers, FiniteSet((-1,1))) — the pre-fix set-difference bug). Discriminates.
- probe_2 (Req 1.5/1.6): membership consistency — 2 not a member, -1 and 1 are. Patched HOLDS; weak.diff HOLDS.
- probe_3 (Req 2.2): im=(n-1)*(n+1/2) over Integers -> FiniteSet(1) (non-integer root 1/2 excluded). HOLDS.
- probe_4 (Req 2.3/3.1): multi-factor im over Naturals0 -> FiniteSet(1). HOLDS.
- probe_5 (Req 3.3/3.4): non-linear vanishing -> ImageSet(Lambda(x,x/2), ConditionSet(n, Eq(n**2-n/2-1/2,0), Integers)). HOLDS.
- probe_6 (Req 4.1/4.3/4.5): n/(1/n-1)+im*(n+1)*I over Integers -> FiniteSet(1/2) (pole excluded). HOLDS.
- probe_7 (Req 4.4): n/(n**2-9)+... -> EmptySet, and n/(n-6)+... -> FiniteSet(-1). HOLDS.
- probe_8 (Req 5.6): log+trig construction over Integers preserved -> imageset(Lambda(n, 2*n*pi - pi/4), Integers) (canonical). HOLDS. (Expected must use `imageset` for canonicalization; raw ImageSet(2*pi*n - pi/4) is not == to 2*pi*n + 7*pi/4 form.)

CANDIDATE PATCH (weak.diff): gold's imaginary-part fix (intersect zero set via _solution_union over numer(im)) but pole/denominator exclusion INTENTIONALLY OMITTED — the lazy partial reading of Req 4. Generated via git diff at base_commit so hunk offsets are exact; applies cleanly. Under this patch: probes 1-5,8 HOLD but probes 6 and 7 are REJECTED — probe_6 yields FiniteSet(1/2, zoo) (undefined pole value zoo leaked as a real member), probe_7 yields FiniteSet(1/8, zoo) instead of EmptySet and FiniteSet(-1, 1/7) instead of FiniteSet(-1). This demonstrates the suite discriminates a requirements-non-conforming wrong fix; it is NOT a too-weak finding.

All needed runs completed. 8 probes hold patched, positive control fails at base (prepatch_reproduced=true), and >=1 candidate is exercised and REJECTED. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Requirement 1.4 + positive control: the canonical example
# imageset(Lambda(n, n + (n-1)*(n+1)*I), Integers).intersect(Reals) == {-1, 1}
import sys
from sympy import I, Lambda, S, FiniteSet
from sympy.abc import n
from sympy import imageset

res = imageset(Lambda(n, n + (n - 1)*(n + 1)*I), S.Integers).intersect(S.Reals)
expected = FiniteSet(-1, 1)
print("result:", res)
print("expected:", expected)
ok = (res == expected)
print("equal:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-21596: fix to the `if other == S.Reals:` branch of ImageSet intersection_sets — keep (intersect) rather than remove (set-difference) the imaginary-part zero set, exclude actual denominator poles, and handle multi-factor / non-linear / rational cases.

### PROBES (all HOLD on gold-patched tree; imageset imported from top-level `sympy`, not sympy.sets.fancysets):
- probe_1 (Req 1.2/1.4, POSITIVE CONTROL): imageset(Lambda(n, n+(n-1)*(n+1)*I), Integers).intersect(Reals) == FiniteSet(-1,1). Patched: HOLDS (FiniteSet(-1,1)). Base: VIOLATED (Complement(Integers, FiniteSet((-1,1))) — the pre-fix set-difference bug). Discriminates.
- probe_2 (Req 1.5/1.6): membership consistency — 2 not a member, -1 and 1 are. Patched HOLDS; weak.diff HOLDS.
- probe_3 (Req 2.2): im=(n-1)*(n+1/2) over Integers -> FiniteSet(1) (non-integer root 1/2 excluded). HOLDS.
- probe_4 (Req 2.3/3.1): multi-factor im over Naturals0 -> FiniteSet(1). HOLDS.
- probe_5 (Req 3.3/3.4): non-linear vanishing -> ImageSet(Lambda(x,x/2), ConditionSet(n, Eq(n**2-n/2-1/2,0), Integers)). HOLDS.
- probe_6 (Req 4.1/4.3/4.5): n/(1/n-1)+im*(n+1)*I over Integers -> FiniteSet(1/2) (pole excluded). HOLDS.
- probe_7 (Req 4.4): n/(n**2-9)+... -> EmptySet, and n/(n-6)+... -> FiniteSet(-1). HOLDS.
- probe_8 (Req 5.6): log+trig construction over Integers preserved -> imageset(Lambda(n, 2*n*pi - pi/4), Integers) (canonical). HOLDS. (Expected must use `imageset` for canonicalization; raw ImageSet(2*pi*n - pi/4) is not == to 2*pi*n + 7*pi/4 form.)

CANDIDATE PATCH (weak.diff): gold's imaginary-part fix (intersect zero set via _solution_union over numer(im)) but pole/denominator exclusion INTENTIONALLY OMITTED — the lazy partial reading of Req 4. Generated via git diff at base_commit so hunk offsets are exact; applies cleanly. Under this patch: probes 1-5,8 HOLD but probes 6 and 7 are REJECTED — probe_6 yields FiniteSet(1/2, zoo) (undefined pole value zoo leaked as a real member), probe_7 yields FiniteSet(1/8, zoo) instead of EmptySet and FiniteSet(-1, 1/7) instead of FiniteSet(-1). This demonstrates the suite discriminates a requirements-non-conforming wrong fix; it is NOT a too-weak finding.

All needed runs completed. 8 probes hold patched, positive control fails at base (prepatch_reproduced=true), and >=1 candidate is exercised and REJECTED. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces `base_set -= FiniteSet(xis)`/ConditionSet difference with `base_set &= _solution_union(Mul.make_args(numer(im)), n)` and fixes the denominator loop (previously buggily solved `im` inside the denoms loop) to `base_set -= _solution_union(denoms(f), n)`. Requirements 1.2, 1.3, 3.1-3.3, 4.1-4.3 correctly describe _solution_union's linear-root FiniteSet vs ConditionSet fallback and the union-of-factors logic. Requirement 5 (unchanged outer imageset re-wrap, decline when ifree != {n}, empty when im provably nonzero) matches the untouched surrounding code. No divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the behavior of the reals-branch fix (intersect vs difference of the imaginary-part zero set, exclude denominator zeros, multi-factor union, linear→finite root, non-linear→ConditionSet, Naturals0 domain restriction, empty result when none survive). All of this is a behavioral translation of the gold patch's own branch structure (numer/denoms, _solution_union's Union-of-FiniteSet/ConditionSet logic) and is legitimate localization. No hidden-test artifacts are transmitted: the test name test_imageset_intersect_real, the file path sympy/sets/tests/test_fancysets.py, and the parametrized constructions/results unique to the hidden test (im=(n-1)*(n+S.Half), n/(n-6), n/(n**2-9), 2*n+2 denominators, results FiniteSet(1)/FiniteSet(S.Half)/FiniteSet(-1)/EmptySet, and the ConditionSet(n, Eq(n**2 - n/2 - S(1)/2, 0), S.Integers)) do NOT appear. The only concrete example used ({-1,1}, membership of 2 == False, the n+(n-1)*(n+1)*I family) is verbatim from the PUBLIC problem_statement. Fix-invented identifiers (_solution_union, numer) are not leaked—only generic 'numerator'/'denominator' prose. Req 5.6's 'logarithms and trigonometric terms over the integers' gestures at the hidden positive-control test but too abstractly to reconstruct it. No case-enumeration that mirrors the test parametrization rather than the fix's behavior.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
