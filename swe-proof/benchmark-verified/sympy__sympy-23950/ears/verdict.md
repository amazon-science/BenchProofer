# P2 adversarial audit — sympy__sympy-23950

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
# R1.1 / R1.3 / R1.4 / positive control:
# as_set() returns the set operand exactly (equal to args[1]) and does not raise.
import sys
from sympy import Contains, Symbol, Integers, Reals, FiniteSet, S

x = Symbol('x')
ok = True
for name, st in [("Integers", Integers), ("Reals", Reals),
                 ("FiniteSet", FiniteSet(1, 2, 3))]:
    c = Contains(x, st)
    try:
        r = c.as_set()
    except Exception as e:
        print("FAIL: as_set raised for", name, repr(e)); ok = False; continue
    print(name, "-> as_set() =", r, "; args[1] =", c.args[1])
    if r != st:
        print("FAIL: as_set() != original set for", name); ok = False
    if r != c.args[1]:
        print("FAIL: as_set() != args[1] for", name); ok = False

sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.1 (exact, no wrapping) + R1.5 (SymPy Set supporting as_relational).
# as_set() returns the SAME object as args[1] (identity), and it is a Set that
# supports as_relational.
import sys
from sympy import Contains, Symbol, Interval, Integers
from sympy.sets.sets import Set

x = Symbol('x')
ok = True
for name, st in [("Interval", Interval(0, 1)), ("Integers", Integers)]:
    c = Contains(x, st)
    r = c.as_set()
    print(name, "as_set() is args[1]:", r is c.args[1])
    if r is not c.args[1]:
        print("FAIL: as_set() not the exact same object (wrapping/modification)", name)
        ok = False
    if not isinstance(r, Set):
        print("FAIL: returned value is not a SymPy Set", name); ok = False
    # supports as_relational protocol
    rel = r.as_relational(x)
    print(name, "as_relational ->", rel)

sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R1 integration: Piecewise whose condition is a Contains builds without error
# (the motivating use case: cond.as_set().as_relational(...)).
import sys
from sympy import Piecewise, Contains, Symbol, Integers

x = Symbol('x')
try:
    p = Piecewise((1, Contains(x, Integers)), (0, True))
    print("Piecewise built:", p)
except Exception as e:
    print("FAIL: Piecewise with Contains condition raised", repr(e))
    sys.exit(1)
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2: preserve construction & evaluation.
import sys
from sympy import Contains, Symbol, Integers, Naturals, Interval, S, oo

ok = True
# R2.1: non-set second arg -> TypeError
try:
    Contains(Symbol('x'), 1)
    print("FAIL: no TypeError for non-set operand"); ok = False
except TypeError:
    print("OK: TypeError for non-set operand")

# R2.2: provable member -> true
r = Contains(S(3), Integers)
print("Contains(3, Integers) =", r)
if r is not S.true:
    print("FAIL: expected true"); ok = False

# R2.3: provable non-member -> false (negative int in naturals)
r = Contains(S(-1), Naturals)
print("Contains(-1, Naturals) =", r)
if r is not S.false:
    print("FAIL: expected false"); ok = False

# R2.4/R2.5: undecided symbolic stays unevaluated
x = Symbol('x')
r = Contains(x, Integers)
print("Contains(x, Integers) =", r, type(r).__name__)
if r != Contains(x, Integers, evaluate=False):
    print("FAIL: not equal to non-evaluated form"); ok = False
if r is S.false:
    print("FAIL: collapsed to false"); ok = False

# R2.6: symbolic element vs interval stays unevaluated; interval.contains yields inequalities
r = Contains(x, Interval(0, 1))
print("Contains(x, Interval(0,1)) =", r, type(r).__name__)
if not isinstance(r, Contains):
    print("FAIL: should remain unevaluated Contains"); ok = False
cq = Interval(0, 1).contains(x)
print("Interval(0,1).contains(x) =", cq)

# R2.7: +/-oo in open interval -> false
r1 = Contains(oo, Interval.open(-oo, oo))
r2 = Contains(-oo, Interval.open(-oo, oo))
print("Contains(oo, open(-oo,oo)) =", r1, "; Contains(-oo,...) =", r2)
if r1 is not S.false or r2 is not S.false:
    print("FAIL: expected false for infinities in open interval"); ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3: binary_symbols preserved.
import sys
from sympy import Contains, Symbol, FiniteSet, Eq

x = Symbol('x'); y = Symbol('y'); z = Symbol('z')
# set operand containing bare symbols and an equality relation
c = Contains(x, FiniteSet(y, Eq(z, True)))
bs = c.binary_symbols
print("binary_symbols =", bs)
expected = {y, z}
if set(bs) != expected:
    print("FAIL: expected", expected, "got", set(bs)); sys.exit(1)
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1 / R1.3 / R1.4 / positive control:
# as_set() returns the set operand exactly (equal to args[1]) and does not raise.
import sys
from sympy import Contains, Symbol, Integers, Reals, FiniteSet, S

x = Symbol('x')
ok = True
for name, st in [("Integers", Integers), ("Reals", Reals),
                 ("FiniteSet", FiniteSet(1, 2, 3))]:
    c = Contains(x, st)
    try:
        r = c.as_set()
    except Exception as e:
        print("FAIL: as_set raised for", name, repr(e)); ok = False; continue
    print(name, "-> as_set() =", r, "; args[1] =", c.args[1])
    if r != st:
        print("FAIL: as_set() != original set for", name); ok = False
    if r != c.args[1]:
        print("FAIL: as_set() != args[1] for", name); ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: Contains.as_set() now returns self.args[1] (was NotImplementedError).

### PROBES (all HOLD on patched tree):
- probe_1 (R1.1/1.3/1.4, POSITIVE CONTROL): as_set() returns the set operand (Integers, Reals, FiniteSet(1,2,3)); equal to args[1] and not raising. HOLDS patched (exit 0), FAILS at base (NotImplementedError, exit 1) -> discriminating.
- probe_2 (R1.1 no-wrapping + R1.5): as_set() returns the EXACT same object (is args[1]) for Interval and Integers, is a SymPy Set, and supports as_relational. HOLDS patched.
- probe_3 (R1 integration): Piecewise((1, Contains(x,Integers)),(0,True)) builds without error. HOLDS patched.
- probe_4 (R2.1-2.7 regression): TypeError on non-set operand; Contains(3,Integers) is true; Contains(-1,Naturals) is false; symbolic Contains stays unevaluated and equals evaluate=False form; interval containment yields inequalities; +/-oo in open(-oo,oo) -> false. HOLDS patched.
- probe_5 (R3): binary_symbols of Contains(x, FiniteSet(y, Eq(z,True))) == {y,z} (corrected from initial Eq(z,0) which yields {y} because Eq(z,0).binary_symbols is empty; matches hidden test_binary_symbols). HOLDS patched.

### Candidate patches
- weak_element (returns FiniteSet(args[0]) = the element, not the asserted set): REJECTED by probe_1 and probe_2 -> demonstrates the suite discriminates wrong implementations.
- weak_imageset (wraps args[1] in single-arg Intersection, which collapses back to the operand): passes all probes because it is behaviorally identical (Intersection(s) == s and is-collapsed to s); it also RESOLVES the hidden test (== comparison). Hence NOT a too-weak finding, just an equivalent correct fix.

The probe suite is strictly stronger than the hidden test_as_set (asserts both value equality AND object identity across FiniteSet/Integers/Reals/Interval), so no requirements-conforming alternative can pass the probes while failing the harness. Positive control reproduced prepatch failure at base. Verdict SOUND.

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
# R1.1 / R1.3 / R1.4 / positive control:
# as_set() returns the set operand exactly (equal to args[1]) and does not raise.
import sys
from sympy import Contains, Symbol, Integers, Reals, FiniteSet, S

x = Symbol('x')
ok = True
for name, st in [("Integers", Integers), ("Reals", Reals),
                 ("FiniteSet", FiniteSet(1, 2, 3))]:
    c = Contains(x, st)
    try:
        r = c.as_set()
    except Exception as e:
        print("FAIL: as_set raised for", name, repr(e)); ok = False; continue
    print(name, "-> as_set() =", r, "; args[1] =", c.args[1])
    if r != st:
        print("FAIL: as_set() != original set for", name); ok = False
    if r != c.args[1]:
        print("FAIL: as_set() != args[1] for", name); ok = False

sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold patch: Contains.as_set() now returns self.args[1] (was NotImplementedError).

### PROBES (all HOLD on patched tree):
- probe_1 (R1.1/1.3/1.4, POSITIVE CONTROL): as_set() returns the set operand (Integers, Reals, FiniteSet(1,2,3)); equal to args[1] and not raising. HOLDS patched (exit 0), FAILS at base (NotImplementedError, exit 1) -> discriminating.
- probe_2 (R1.1 no-wrapping + R1.5): as_set() returns the EXACT same object (is args[1]) for Interval and Integers, is a SymPy Set, and supports as_relational. HOLDS patched.
- probe_3 (R1 integration): Piecewise((1, Contains(x,Integers)),(0,True)) builds without error. HOLDS patched.
- probe_4 (R2.1-2.7 regression): TypeError on non-set operand; Contains(3,Integers) is true; Contains(-1,Naturals) is false; symbolic Contains stays unevaluated and equals evaluate=False form; interval containment yields inequalities; +/-oo in open(-oo,oo) -> false. HOLDS patched.
- probe_5 (R3): binary_symbols of Contains(x, FiniteSet(y, Eq(z,True))) == {y,z} (corrected from initial Eq(z,0) which yields {y} because Eq(z,0).binary_symbols is empty; matches hidden test_binary_symbols). HOLDS patched.

### Candidate patches
- weak_element (returns FiniteSet(args[0]) = the element, not the asserted set): REJECTED by probe_1 and probe_2 -> demonstrates the suite discriminates wrong implementations.
- weak_imageset (wraps args[1] in single-arg Intersection, which collapses back to the operand): passes all probes because it is behaviorally identical (Intersection(s) == s and is-collapsed to s); it also RESOLVES the hidden test (== comparison). Hence NOT a too-weak finding, just an equivalent correct fix.

The probe suite is strictly stronger than the hidden test_as_set (asserts both value equality AND object identity across FiniteSet/Integers/Reals/Interval), so no requirements-conforming alternative can pass the probes while failing the harness. Positive control reproduced prepatch failure at base. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified via nl_attack probe on gold-patched tree: all of R1.1-1.5, R2.1-2.7, R3.1 observed to hold. Requirement modeling boundary is correct: R1 pins the exact changed observable behavior (return the second operand), not a narrower slice. No invented, over-mandated, or forbidden behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch changes Contains.as_set from `raise NotImplementedError()` to `return self.args[1]`; hidden test_as_set asserts as_set()==FiniteSet(y), S.Integers, S.Reals. The requirements translate this into behavioral requirements (return the set operand exactly, no NotImplementedError, supports as_relational) — the whole point of the spec. No test file path, function/class names (test_as_set, test_type_error, etc.), parametrization ids, quoted test/gold code, or fix-invented identifiers appear. Req 1.3/1.4 name finite-set and integers/reals as example domains; these are canonical set categories derivable from the behavior (Reals is already in the public problem_statement), not a fingerprint of the hidden test symbols/assertions. Req 2 describes preserved existing behavior (PASS_TO_PASS) whose test bodies are not even in the provided material — behavioral prose, not transmitted tests. Naming the module/method (sympy/sets/contains.py, Contains.as_set) is legitimate localization. No leakage beyond the public problem_statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
