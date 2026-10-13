# P2 adversarial audit — sympy__sympy-12481

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
"""R1.1 + R1.3 (POSITIVE CONTROL): non-disjoint cycles accepted; [[0,1],[0,1]] == identity.
Also R1.4 core: [[0,1],[0,2]] == Permutation(0,1,2). Fails at base (ValueError), holds patched."""
import sys
from sympy.combinatorics.permutations import Permutation

# R1.1: does not raise
try:
    p = Permutation([[0, 1], [0, 1]])
except Exception as e:
    print("FAIL R1.1: raised", repr(e))
    sys.exit(1)
print("R1.1 ok: got", p)

# R1.3: identity
ident = Permutation([], size=2)
if p != ident:
    print("FAIL R1.3: [[0,1],[0,1]] =", p, "expected identity", ident)
    sys.exit(1)
print("R1.3 ok: identity")

# R1.4 core (the hidden-test operand pair)
q = Permutation([[0, 1], [0, 2]])
expect = Permutation(0, 1, 2)
if q != expect:
    print("FAIL R1.4: [[0,1],[0,2]] =", q, "expected", expect)
    sys.exit(1)
print("R1.4 ok: [[0,1],[0,2]] ==", expect)
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.4 + R1.5: overlapping cycles equal product of same cycles applied in same order,
and array form has one entry per point 0..max, i-th = image of i."""
import sys
from sympy.combinatorics.permutations import Permutation

# R1.4: [[0,1],[0,2]] equals product Permutation(0,1)*... via separate-cycles route.
# Separate positional cycle args build product left-to-right (Cycle(*args)).
combined = Permutation([[0, 1], [0, 2]])
# "product of the same cycles constructed separately", applied left-to-right:
via_sep = Permutation([[0, 1]], size=3) * Permutation([[0, 2]], size=3)
if combined != via_sep:
    print("FAIL R1.4: list-of-lists", combined, "!= product-of-separate-cycles", via_sep)
    sys.exit(1)
print("R1.4 ok: both routes ==", combined)

# R1.5: array form covers 0..max named point, images match left-to-right composition.
af = combined.array_form
# largest named point is 2 -> at least 3 entries
if len(af) < 3:
    print("FAIL R1.5: array_form too short", af)
    sys.exit(1)
# manual left-to-right composition of (0 1) then (0 2):
def apply_cycle(cyc, x):
    if x in cyc:
        i = cyc.index(x)
        return cyc[(i+1) % len(cyc)]
    return x
for i in range(3):
    y = apply_cycle([0,1], i)
    y = apply_cycle([0,2], y)
    if af[i] != y:
        print("FAIL R1.5: image of", i, "=", af[i], "expected", y, "af=", af)
        sys.exit(1)
print("R1.5 ok: array_form", af, "matches left-to-right composition")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.1 + R2.2 + R2.3: array-form rejection preserved.
Repeated element in array form -> ValueError mentioning repeated; missing point -> ValueError."""
import sys
from sympy.combinatorics.permutations import Permutation

# R2.1 + R2.2: array form with dup
try:
    Permutation([1, 1, 0])
    print("FAIL R2.1: no error for array-form dup")
    sys.exit(1)
except ValueError as e:
    msg = str(e)
    print("R2.1 ok: raised ValueError:", msg)
    if 'repeated' not in msg.lower():
        print("FAIL R2.2: message does not mention repeated:", msg)
        sys.exit(1)
    print("R2.2 ok: message mentions repeated")
except Exception as e:
    print("FAIL R2.1: wrong exception type", repr(e))
    sys.exit(1)

# R2.3: array form omitting a required point
try:
    Permutation([2, 1])  # missing 0
    print("FAIL R2.3: no error for missing point")
    sys.exit(1)
except ValueError as e:
    print("R2.3 ok: raised ValueError for missing point:", e)
except Exception as e:
    print("FAIL R2.3: wrong exception", repr(e))
    sys.exit(1)
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R3.1 + R3.2: size extension and fixed points for cyclic form.
Uses the disjoint-cycle example from the regression tests."""
import sys
from sympy.combinatorics.permutations import Permutation

# R3.2: points not named are fixed; singleton [1] just names a max point.
p = Permutation([[1], [4, 2]], size=1)
if p != Permutation([0, 1, 4, 3, 2]):
    print("FAIL R3.2:", p.array_form, "expected", [0,1,4,3,2])
    sys.exit(1)
print("R3.2 ok:", p.array_form)

# R3.1: size larger than max named point extends with fixed points.
p6 = Permutation([[1], [4, 2]], size=6)
if p6 != Permutation([0, 1, 4, 3, 2, 5]):
    print("FAIL R3.1:", p6.array_form, "expected", [0,1,4,3,2,5])
    sys.exit(1)
if p6.size != 6:
    print("FAIL R3.1: size", p6.size, "expected 6")
    sys.exit(1)
print("R3.1 ok:", p6.array_form, "size", p6.size)

# empty cycles with size -> identity of that size
e = Permutation([], size=3)
if e != Permutation([0, 1, 2]):
    print("FAIL R3.1 empty:", e.array_form)
    sys.exit(1)
print("R3.1 ok empty:", e.array_form)
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.3 + R3.4: separate positional cycle args build product; malformed mixed arg rejected."""
import sys
from sympy.combinatorics.permutations import Permutation

# R3.3: separate positional cycles unaffected.
if Permutation(4, 5) != Permutation([0, 1, 2, 3, 5, 4]):
    print("FAIL R3.3:", Permutation(4,5).array_form)
    sys.exit(1)
print("R3.3 ok:", Permutation(4,5).array_form)

# R3.4: mixed integer + sequence at same level -> ValueError
try:
    Permutation([[1, 2], 0])  # a list whose elements are not uniform
    print("FAIL R3.4: no error for mixed list")
    sys.exit(1)
except ValueError as e:
    print("R3.4 ok: raised ValueError:", e)
except Exception as e:
    print("FAIL R3.4: wrong exception", repr(e))
    sys.exit(1)
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R1.2 + R3.5: left-to-right order matters; produced permutations behave under mul/equality.
Left-to-right composition of overlapping cycles joins points into a longer orbit."""
import sys
from sympy.combinatorics.permutations import Permutation

# R1.2: order-sensitivity. [[0,1],[0,2]] vs [[0,2],[0,1]] should differ (both are 3-cycles
# but in opposite directions).
a = Permutation([[0, 1], [0, 2]])
b = Permutation([[0, 2], [0, 1]])
if a == b:
    print("FAIL R1.2: order ignored, both ==", a)
    sys.exit(1)
print("R1.2 ok: a=", a.array_form, "b=", b.array_form, "differ")

# a should send 0->1->2->0 (the 3-cycle Permutation(0,1,2)); b the reverse.
if a != Permutation(0, 1, 2):
    print("FAIL R1.2: a", a.array_form, "!= (0 1 2)")
    sys.exit(1)
if b != Permutation(0, 2, 1):
    print("FAIL R1.2: b", b.array_form, "!= (0 2 1)")
    sys.exit(1)

# R3.5: equality with product of the same transpositions built separately, and mul behaves.
t01 = Permutation([[0, 1]], size=3)
t02 = Permutation([[0, 2]], size=3)
# left-to-right composition == t01 then t02 == product with sympy rmul convention.
# Permutation multiplication *a*b applies a then b (left-to-right) in sympy.
prod = t01 * t02
if prod != a:
    print("FAIL R3.5: t01*t02 =", prod.array_form, "!= a", a.array_form)
    sys.exit(1)
print("R3.5 ok: t01*t02 ==", prod.array_form, "== a")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.1 + R1.3 (POSITIVE CONTROL): non-disjoint cycles accepted; [[0,1],[0,1]] == identity.
Also R1.4 core: [[0,1],[0,2]] == Permutation(0,1,2). Fails at base (ValueError), holds patched."""
import sys
from sympy.combinatorics.permutations import Permutation

# R1.1: does not raise
try:
    p = Permutation([[0, 1], [0, 1]])
except Exception as e:
    print("FAIL R1.1: raised", repr(e))
    sys.exit(1)
print("R1.1 ok: got", p)

# R1.3: identity
ident = Permutation([], size=2)
if p != ident:
    print("FAIL R1.3: [[0,1],[0,1]] =", p, "expected identity", ident)
    sys.exit(1)
print("R1.3 ok: identity")

# R1.4 core (the hidden-test operand pair)
q = Permutation([[0, 1], [0, 2]])
expect = Permutation(0, 1, 2)
if q != expect:
    print("FAIL R1.4: [[0,1],[0,2]] =", q, "expected", expect)
    sys.exit(1)
print("R1.4 ok: [[0,1],[0,2]] ==", expect)
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-12481: gold patch lets the Permutation constructor accept non-disjoint cyclic-form input (removes the is_cycle branch of the repeated-elements ValueError), so overlapping cycles compose left-to-right via the pre-existing Cycle-application loop.

Probes (all HOLD on patched tree):
PATCHED exit0, BASE exit1 -> discriminates.
- probe_2: R1.4/R1.5 [[0,1],[0,2]] equals product of same cycles built separately (Permutation([[0,1]],size=3)*Permutation([[0,2]],size=3)); array_form has one entry per point 0..max and i-th entry = image of i under left-to-right composition.
- probe_3: R2.1/R2.2/R2.3 array-form dup -> ValueError mentioning 'repeated'; array-form missing point ([2,1]) -> ValueError.
- probe_4: R3.1/R3.2 size extension ([[1],[4,2]],size=6 -> [0,1,4,3,2,5], size 6), fixed points, empty cycles with size -> identity.
- probe_5: R3.3 separate positional cycles Permutation(4,5)==[0,1,2,3,5,4]; R3.4 mixed list [[1,2],0] -> ValueError.
- probe_6: R1.2 order sensitivity ([[0,1],[0,2]]==(0 1 2) vs [[0,2],[0,1]]==(0 2 1)); R3.5 t01*t02 equals combined, mul/equality behave.

Wrong-fix candidate (weak.diff, 'only_first_cycle'): applies the gold ValueError relaxation but replaces the `for ci in args: c=c(*ci)` composition loop with `if args: c=c(*args[0])` (only the first cycle applied). It satisfies R1.1 (no error) and R2/R3 array-form and separate-arg criteria (probe_3, probe_5 HOLD) but is REJECTED by probe_1, probe_2, probe_4, probe_6 because it does not compose the later cycles. This demonstrates the suite discriminates a plausibly-wrong partial fix. It would also fail the hidden test assert Permutation([[0,1],[0,2]])==Permutation(0,1,2). Note probe_4 also fails under it because [[1],[4,2]] uses only the singleton first cycle -> wrong array form, an incidental but valid rejection.

Verdict SOUND: >=6 distinct probes cover R1-R3 including 'SHALL keep' regressions; positive control discriminates base vs patched; one requirements-adjacent wrong-fix candidate is rejected by the probe suite.

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
"""R1.1 + R1.3 (POSITIVE CONTROL): non-disjoint cycles accepted; [[0,1],[0,1]] == identity.
Also R1.4 core: [[0,1],[0,2]] == Permutation(0,1,2). Fails at base (ValueError), holds patched."""
import sys
from sympy.combinatorics.permutations import Permutation

# R1.1: does not raise
try:
    p = Permutation([[0, 1], [0, 1]])
except Exception as e:
    print("FAIL R1.1: raised", repr(e))
    sys.exit(1)
print("R1.1 ok: got", p)

# R1.3: identity
ident = Permutation([], size=2)
if p != ident:
    print("FAIL R1.3: [[0,1],[0,1]] =", p, "expected identity", ident)
    sys.exit(1)
print("R1.3 ok: identity")

# R1.4 core (the hidden-test operand pair)
q = Permutation([[0, 1], [0, 2]])
expect = Permutation(0, 1, 2)
if q != expect:
    print("FAIL R1.4: [[0,1],[0,2]] =", q, "expected", expect)
    sys.exit(1)
print("R1.4 ok: [[0,1],[0,2]] ==", expect)
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-12481: gold patch lets the Permutation constructor accept non-disjoint cyclic-form input (removes the is_cycle branch of the repeated-elements ValueError), so overlapping cycles compose left-to-right via the pre-existing Cycle-application loop.

Probes (all HOLD on patched tree):
PATCHED exit0, BASE exit1 -> discriminates.
- probe_2: R1.4/R1.5 [[0,1],[0,2]] equals product of same cycles built separately (Permutation([[0,1]],size=3)*Permutation([[0,2]],size=3)); array_form has one entry per point 0..max and i-th entry = image of i under left-to-right composition.
- probe_3: R2.1/R2.2/R2.3 array-form dup -> ValueError mentioning 'repeated'; array-form missing point ([2,1]) -> ValueError.
- probe_4: R3.1/R3.2 size extension ([[1],[4,2]],size=6 -> [0,1,4,3,2,5], size 6), fixed points, empty cycles with size -> identity.
- probe_5: R3.3 separate positional cycles Permutation(4,5)==[0,1,2,3,5,4]; R3.4 mixed list [[1,2],0] -> ValueError.
- probe_6: R1.2 order sensitivity ([[0,1],[0,2]]==(0 1 2) vs [[0,2],[0,1]]==(0 2 1)); R3.5 t01*t02 equals combined, mul/equality behave.

Wrong-fix candidate (weak.diff, 'only_first_cycle'): applies the gold ValueError relaxation but replaces the `for ci in args: c=c(*ci)` composition loop with `if args: c=c(*args[0])` (only the first cycle applied). It satisfies R1.1 (no error) and R2/R3 array-form and separate-arg criteria (probe_3, probe_5 HOLD) but is REJECTED by probe_1, probe_2, probe_4, probe_6 because it does not compose the later cycles. This demonstrates the suite discriminates a plausibly-wrong partial fix. It would also fail the hidden test assert Permutation([[0,1],[0,2]])==Permutation(0,1,2). Note probe_4 also fails under it because [[1],[4,2]] uses only the singleton first cycle -> wrong array form, an incidental but valid rejection.

Verdict SOUND: >=6 distinct probes cover R1-R3 including 'SHALL keep' regressions; positive control discriminates base vs patched; one requirements-adjacent wrong-fix candidate is rejected by the probe suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch changes exactly one guard: `if has_dups(temp): if is_cycle: raise ... else: raise` becomes `if has_dups(temp) and not is_cycle: raise`. This lifts the duplicate-element rejection ONLY for cyclic-form input (is_cycle=True) while preserving it for array-form. Requirements pin precisely this changed observable boundary: Req1 mandates acceptance + left-to-right composition for non-disjoint cycles (the newly-permitted behavior), Req2 preserves array-form dup rejection (the retained branch), Req3 preserves untouched constructor behaviors. Boundary is correct — it targets the changed behavior (non-disjoint cyclic acceptance) rather than a narrow slice or an unrelated helper. Verified against base (rejects) and patched (composes) trees via probes; no invented or forbidden behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to Permutation.__new__ in sympy/combinatorics/permutations.py (legitimate). Its only worked example, Permutation([[0,1],[0,1]]) -> identity, is taken verbatim from the PUBLIC problem_statement, not the hidden test. The hidden test's actual new assertion (Permutation([[0,1],[0,2]]) == Permutation(0,1,2)) and its removed raises-case (Permutation([[1],[1,2]])) are NOT reproduced; the overlapping-orbit description is general behavioral prose. No test name (test_args), test path, parametrization id, or gold-invented identifier (has_dups, is_cycle) appears. Array-form/malformed/size requirements describe pre-existing behavior being preserved. Translating test-checked behavior into requirements is the intended purpose; no test material is transmitted.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
