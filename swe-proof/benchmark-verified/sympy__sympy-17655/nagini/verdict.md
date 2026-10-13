# P2 adversarial audit — sympy__sympy-17655

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -50,7 +49,6 @@
     """Scale a point by a factor on the right (point * factor)."""
     # pre-conditions-start
     Requires(Acc(list_pred(point), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(point), 1 / 2))
@@ -70,12 +68,11 @@
         Invariant(0 <= i and i <= len(point))
         Invariant(len(result) == len(point) - i)
         Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = point[i - 1]
         Assert(ToSeq(point).drop(i - 1)[0] == c)
         Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
-        result = [c * factor] + result
+        result = [c + factor] + result
         i = i - 1
     Assert(ToSeq(point).drop(0) == ToSeq(point))
     return result
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -50,7 +49,6 @@
     """Scale a point by a factor on the right (point * factor)."""
     # pre-conditions-start
     Requires(Acc(list_pred(point), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(point), 1 / 2))
@@ -70,12 +68,14 @@
         Invariant(0 <= i and i <= len(point))
         Invariant(len(result) == len(point) - i)
         Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = point[i - 1]
         Assert(ToSeq(point).drop(i - 1)[0] == c)
         Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
-        result = [c * factor] + result
+        if i == 1:
+            result = [c] + result
+        else:
+            result = [c * factor] + result
         i = i - 1
     Assert(ToSeq(point).drop(0) == ToSeq(point))
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -50,7 +49,6 @@
     """Scale a point by a factor on the right (point * factor)."""
     # pre-conditions-start
     Requires(Acc(list_pred(point), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(point), 1 / 2))
@@ -70,7 +68,6 @@
         Invariant(0 <= i and i <= len(point))
         Invariant(len(result) == len(point) - i)
         Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = point[i - 1]
         Assert(ToSeq(point).drop(i - 1)[0] == c)
@@ -98,5 +95,19 @@
     Ensures(ToSeq(Result()) == scaled(ToSeq(point), factor))
     # post-conditions-end
     # impl-start
-    return mul_right(point, factor)
+    result = []  # type: List[int]
+    i = len(point)
+    while i > 0:
+        Invariant(Acc(list_pred(point), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= i and i <= len(point))
+        Invariant(len(result) == len(point) - i)
+        Invariant(ToSeq(result) == ToSeq(point).drop(i))
+        c = point[i - 1]
+        Assert(ToSeq(point).drop(i - 1)[0] == c)
+        Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
+        result = [c] + result
+        i = i - 1
+    Assert(ToSeq(point).drop(0) == ToSeq(point))
+    return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -50,7 +49,6 @@
     """Scale a point by a factor on the right (point * factor)."""
     # pre-conditions-start
     Requires(Acc(list_pred(point), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(point), 1 / 2))
@@ -70,12 +68,14 @@
         Invariant(0 <= i and i <= len(point))
         Invariant(len(result) == len(point) - i)
         Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = point[i - 1]
         Assert(ToSeq(point).drop(i - 1)[0] == c)
         Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
-        result = [c * factor] + result
+        if factor == 0:
+            result = [c] + result
+        else:
+            result = [c * factor] + result
         i = i - 1
     Assert(ToSeq(point).drop(0) == ToSeq(point))
     return result
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -50,7 +49,6 @@
     """Scale a point by a factor on the right (point * factor)."""
     # pre-conditions-start
     Requires(Acc(list_pred(point), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(point), 1 / 2))
@@ -70,12 +68,11 @@
         Invariant(0 <= i and i <= len(point))
         Invariant(len(result) == len(point) - i)
         Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = point[i - 1]
         Assert(ToSeq(point).drop(i - 1)[0] == c)
         Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
-        result = [c * factor] + result
+        result = result + [c * factor]
         i = i - 1
     Assert(ToSeq(point).drop(0) == ToSeq(point))
     return result
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -24,7 +24,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -50,7 +49,6 @@
     """Scale a point by a factor on the right (point * factor)."""
     # pre-conditions-start
     Requires(Acc(list_pred(point), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(point), 1 / 2))
@@ -70,12 +68,11 @@
         Invariant(0 <= i and i <= len(point))
         Invariant(len(result) == len(point) - i)
         Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = point[i - 1]
         Assert(ToSeq(point).drop(i - 1)[0] == c)
         Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
-        result = [c * factor] + result
+        result = [c * factor * factor] + result
         i = i - 1
     Assert(ToSeq(point).drop(0) == ToSeq(point))
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-17655.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A point in n-dimensional space is described by its sequence of coordinate
  values.  Scaling a point by a numeric factor yields a NEW point whose i-th
  coordinate is the i-th coordinate of the original multiplied by the factor;
  the dimension (the number of coordinates) is preserved and the original
  point is left unchanged.

  The essential property: scaling is COMMUTATIVE between the point and the
  factor.  Multiplying the factor by the point on the left produces exactly the
  same scaled point as multiplying the point by the factor on the right -- for
  every coordinate, factor * coordinate.

A point is modelled as a `List[int]` of coordinate values (the tested
coordinates and factor are concrete integers); the scaling of a whole point is
carried in the specification by `PSeq[int]` via `ToSeq`, as the per-coordinate
multiplication `scaled` (a front-recursive fold giving one unfold per loop
step).  The factor is a read-only int; the input point is read-only and carries
fractional permission only.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms: the per-coordinate scaling is the changed operation
# and is modelled DEEPLY as integer multiplication -- see refinement.md
# A-reference rows; there is no opaque callee the proof consumes.)
# axioms-end


# pure-start
@Pure
def scaled(s: PSeq[int], factor: int) -> PSeq[int]:
    """The per-coordinate scaling of a whole point: every coordinate of ``s``
    multiplied by ``factor``, in order.  Front-recursive so a single unfold is
    available to callers per loop step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(s[0] * factor) + scaled(s.drop(1), factor)
# pure-end


def mul_right(point: List[int], factor: int) -> List[int]:
    """Scale a point by a factor on the right (point * factor)."""
    # pre-conditions-start
    Requires(Acc(list_pred(point), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(point), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The dimension is preserved.
    Ensures(len(Result()) == len(point))
    # Every coordinate of the result is the corresponding coordinate scaled.
    Ensures(ToSeq(Result()) == scaled(ToSeq(point), factor))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(point)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(point), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(point))
        Invariant(len(result) == len(point) - i)
        Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
        # invariants-end
        c = point[i - 1]
        Assert(ToSeq(point).drop(i - 1)[0] == c)
        Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
        result = [c * factor] + result
        i = i - 1
    Assert(ToSeq(point).drop(0) == ToSeq(point))
    return result
    # impl-end


def mul_left(factor: int, point: List[int]) -> List[int]:
    """Scale a point by a factor on the left (factor * point)."""
    # pre-conditions-start
    Requires(Acc(list_pred(point), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(point), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The dimension is preserved.
    Ensures(len(Result()) == len(point))
    # Left scaling reproduces the per-coordinate scaling exactly -- the same
    # scaled point that right scaling produces (commutativity of the factor and
    # the point).
    Ensures(ToSeq(Result()) == scaled(ToSeq(point), factor))
    # post-conditions-end
    # impl-start
    return mul_right(point, factor)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of nagini sympy__sympy-17655 (G-EQ refinement fidelity, adversarial A-leg focus).

SPEC SHAPE: fully functional, no slack. Both mul_right and mul_left postconditions pin ToSeq(Result()) == scaled(ToSeq(point), factor) (exact element-wise integer product) AND len(Result())==len(point). The axioms region is EMPTY -> NO @ContractOnly axioms, so there is no opaque oracle to echo (ungrounded-oracle attack class is inapplicable). scaled is a @Pure deep model, byte-identical in every attack.

POSITIVE CONTROL: cp of model.py -> positive_control.py. `bash scripts/nagini_verify.sh positive_control.py` exit=0 (verifies).

PREPATCH: model_prepatch.py -> prepatch.py. same-spec IDENTICAL(0); verify exit=1, failure = 'Postcondition of mul_left might not hold. Assertion (ToSeq(Result()) == scaled(ToSeq(point), factor)) might not hold' at line 95. => spec senses the change (G-DIFF), prepatch_reproduced=true.

ATTACKS (6 distinct wrong impls; all edit ONLY the impl region, axioms/@Pure/Requires/Ensures byte-identical; all same-spec IDENTICAL(0)):
  atk_1 wrong-op: c+factor instead of c*factor in mul_right.
  atk_2 boundary: leave first coord (i==1) unscaled, length preserved, one value wrong.
  atk_3 control-flow-effect: mul_left loops returning coords unchanged (discriminating change omitted).
  atk_4 partial-domain: correct except factor==0 leaves coords unchanged.
  atk_5 order/permutation: append (result+[c*factor]) instead of prepend -> reversed coords.
  atk_6 wrong-magnitude: c*factor*factor (double application).

Commands run (concurrent, <=3 JVMs/batch):
  same-spec: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-17655 <atk>` -> all exit 0 (IDENTICAL).
  weakness: `python -m swebench_unified.adversary weakness nagini sympy__sympy-17655 <atk>` -> atk_1..6 all exit=2 (NOT-A-COUNTEREXAMPLE: does not verify).
  raw verify: `bash scripts/nagini_verify.sh <atk>` -> all exit=1. Failure lands on the discriminating content: atk_1/2/4/5/6 fail loop invariant 'ToSeq(result) == scaled(ToSeq(point).drop(i), factor)' (line 70); atk_3 fails 'Postcondition of mul_left ... ToSeq(Result()) == scaled(...)' (line 95). Not parse/infra errors.

NO CANDIDATE: zero attacks are same-spec AND verifying, so there is NO faithful refined patch to materialize; run_resolve is inapplicable (nothing to run). patches={}.

G-AX / A-reference correspondence: ran axiom_check.py under sympy 1.14.0 -> exit 0, 'deep model scaled == real Point.__mul__ and Point.__rmul__ (commutative) on 12 boundary + 2000 fuzz inputs'. Confirms A2/A4 deep-model legs correspond to the real callees.

refinement.md AUDIT: A1=R (point<->List[int], factor<->int, tested inputs concrete). A2=A-reference (per-coord scaling modeled deeply as scaled; validated == real Point.__mul__ by G-AX). A3=I (mul_left delegates return mul_right; matches __rmul__ delegating to __mul__). A4=A-reference+I (commutativity; holds via delegation + G-AX). Every leg is R / A-reference / I. NO kind-3, NO consumed axioms. A-legs' correspondence to real callees holds (axiom_check pass). Correspondence is tight: functional postcondition leaves no verifying-wrong-impl room.

VERDICT: SOUND. >=5 adversarial attacks (6 run) spanning wrong-op, boundary, control-flow-effect, partial-domain, permutation, wrong-magnitude; none verifies, so verify => the exact scaled product => resolves. No verify-not-correct gap found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-17655.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A point in n-dimensional space is described by its sequence of coordinate
  values.  Scaling a point by a numeric factor yields a NEW point whose i-th
  coordinate is the i-th coordinate of the original multiplied by the factor;
  the dimension (the number of coordinates) is preserved and the original
  point is left unchanged.

  The essential property: scaling is COMMUTATIVE between the point and the
  factor.  Multiplying the factor by the point on the left produces exactly the
  same scaled point as multiplying the point by the factor on the right -- for
  every coordinate, factor * coordinate.

A point is modelled as a `List[int]` of coordinate values (the tested
coordinates and factor are concrete integers); the scaling of a whole point is
carried in the specification by `PSeq[int]` via `ToSeq`, as the per-coordinate
multiplication `scaled` (a front-recursive fold giving one unfold per loop
step).  The factor is a read-only int; the input point is read-only and carries
fractional permission only.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms: the per-coordinate scaling is the changed operation
# and is modelled DEEPLY as integer multiplication -- see refinement.md
# A-reference rows; there is no opaque callee the proof consumes.)
# axioms-end


# pure-start
@Pure
def scaled(s: PSeq[int], factor: int) -> PSeq[int]:
    """The per-coordinate scaling of a whole point: every coordinate of ``s``
    multiplied by ``factor``, in order.  Front-recursive so a single unfold is
    available to callers per loop step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(s[0] * factor) + scaled(s.drop(1), factor)
# pure-end


def mul_right(point: List[int], factor: int) -> List[int]:
    """Scale a point by a factor on the right (point * factor)."""
    # pre-conditions-start
    Requires(Acc(list_pred(point), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(point), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The dimension is preserved.
    Ensures(len(Result()) == len(point))
    # Every coordinate of the result is the corresponding coordinate scaled.
    Ensures(ToSeq(Result()) == scaled(ToSeq(point), factor))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(point)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(point), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(point))
        Invariant(len(result) == len(point) - i)
        Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
        # invariants-end
        c = point[i - 1]
        Assert(ToSeq(point).drop(i - 1)[0] == c)
        Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
        result = [c * factor] + result
        i = i - 1
    Assert(ToSeq(point).drop(0) == ToSeq(point))
    return result
    # impl-end


def mul_left(factor: int, point: List[int]) -> List[int]:
    """Scale a point by a factor on the left (factor * point)."""
    # pre-conditions-start
    Requires(Acc(list_pred(point), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(point), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The dimension is preserved.
    Ensures(len(Result()) == len(point))
    # Left scaling reproduces the per-coordinate scaling exactly -- the same
    # scaled point that right scaling produces (commutativity of the factor and
    # the point).
    Ensures(ToSeq(Result()) == scaled(ToSeq(point), factor))
    # post-conditions-end
    # impl-start
    return mul_right(point, factor)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT of nagini sympy__sympy-17655 (G-EQ refinement fidelity, adversarial A-leg focus).

SPEC SHAPE: fully functional, no slack. Both mul_right and mul_left postconditions pin ToSeq(Result()) == scaled(ToSeq(point), factor) (exact element-wise integer product) AND len(Result())==len(point). The axioms region is EMPTY -> NO @ContractOnly axioms, so there is no opaque oracle to echo (ungrounded-oracle attack class is inapplicable). scaled is a @Pure deep model, byte-identical in every attack.

POSITIVE CONTROL: cp of model.py -> positive_control.py. `bash scripts/nagini_verify.sh positive_control.py` exit=0 (verifies).

PREPATCH: model_prepatch.py -> prepatch.py. same-spec IDENTICAL(0); verify exit=1, failure = 'Postcondition of mul_left might not hold. Assertion (ToSeq(Result()) == scaled(ToSeq(point), factor)) might not hold' at line 95. => spec senses the change (G-DIFF), prepatch_reproduced=true.

ATTACKS (6 distinct wrong impls; all edit ONLY the impl region, axioms/@Pure/Requires/Ensures byte-identical; all same-spec IDENTICAL(0)):
  atk_1 wrong-op: c+factor instead of c*factor in mul_right.
  atk_2 boundary: leave first coord (i==1) unscaled, length preserved, one value wrong.
  atk_3 control-flow-effect: mul_left loops returning coords unchanged (discriminating change omitted).
  atk_4 partial-domain: correct except factor==0 leaves coords unchanged.
  atk_5 order/permutation: append (result+[c*factor]) instead of prepend -> reversed coords.
  atk_6 wrong-magnitude: c*factor*factor (double application).

Commands run (concurrent, <=3 JVMs/batch):
  same-spec: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-17655 <atk>` -> all exit 0 (IDENTICAL).
  weakness: `python -m swebench_unified.adversary weakness nagini sympy__sympy-17655 <atk>` -> atk_1..6 all exit=2 (NOT-A-COUNTEREXAMPLE: does not verify).
  raw verify: `bash scripts/nagini_verify.sh <atk>` -> all exit=1. Failure lands on the discriminating content: atk_1/2/4/5/6 fail loop invariant 'ToSeq(result) == scaled(ToSeq(point).drop(i), factor)' (line 70); atk_3 fails 'Postcondition of mul_left ... ToSeq(Result()) == scaled(...)' (line 95). Not parse/infra errors.

NO CANDIDATE: zero attacks are same-spec AND verifying, so there is NO faithful refined patch to materialize; run_resolve is inapplicable (nothing to run). patches={}.

G-AX / A-reference correspondence: ran axiom_check.py under sympy 1.14.0 -> exit 0, 'deep model scaled == real Point.__mul__ and Point.__rmul__ (commutative) on 12 boundary + 2000 fuzz inputs'. Confirms A2/A4 deep-model legs correspond to the real callees.

refinement.md AUDIT: A1=R (point<->List[int], factor<->int, tested inputs concrete). A2=A-reference (per-coord scaling modeled deeply as scaled; validated == real Point.__mul__ by G-AX). A3=I (mul_left delegates return mul_right; matches __rmul__ delegating to __mul__). A4=A-reference+I (commutativity; holds via delegation + G-AX). Every leg is R / A-reference / I. NO kind-3, NO consumed axioms. A-legs' correspondence to real callees holds (axiom_check pass). Correspondence is tight: functional postcondition leaves no verifying-wrong-impl room.

VERDICT: SOUND. >=5 adversarial attacks (6 run) spanning wrong-op, boundary, control-flow-effect, partial-domain, permutation, wrong-magnitude; none verifies, so verify => the exact scaled product => resolves. No verify-not-correct gap found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attempt failed to find any divergence. The spec models the changed operation (Point.__rmul__ left scaling, delegating to __mul__) as per-coordinate integer multiplication `scaled` over a List[int] carrier, with dimension preservation and left==right commutativity. Verified against the REAL patched sympy callee at base_commit f5e965947a (gold __rmul__ = `return self.__mul__(factor)` inserted after __mul__): (1) axiom_check.py G-AX OK, 0 disagreements (12 boundary + 2000 fuzz); (2) conformance_check.py G-CONF OK, 0 disagreements over 100,018 inputs (seed 17655); (3) independent 20k random fuzz over dim 2-6, coords/factor in +-1000, and adversarial edge cases (huge factor 1e18, near-int64, all-negative, zero*zero) -- 0 mismatches. On the integer carrier stated in mapping.md section 2, simplify(x*factor) is the exact integer product and result args are exact Integer (int() lifting lossless), so the modeled function equals the real callee on every input in the spec's domain (precondition only requires read permission -> all int inputs valid). Model verifies in Nagini (15.75s). No diverging input exists; spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view of model.py) discloses only behaviour already public in the problem_statement. The problem_statement states that `number * point` raises TypeError while `point * number` works and that 'both lines give the same result' is expected — i.e. the existence of a missing left-multiplication and its commutativity with right-multiplication are already public. The spec docstring/comments restate exactly that desired behaviour ('scaling is COMMUTATIVE ... factor by the point on the left produces exactly the same scaled point as ... on the right'), not the edit. The gold discriminator — that the fix is adding `Point.__rmul__` delegating to `self.__mul__` — is NOT revealed: functions are named generically (mul_left/mul_right), the distinctive patched symbol `__rmul__` (screen token 'rmul') appears nowhere in the spec view (only in hints_text, correctly out of scope), no patched file path (sympy/geometry/point.py) or module path, no diff markers, no gold-patch line reproduced, and no bug/fix narration. The __rmul__/file-path/delegation specifics live only in refinement.md and mapping.md, which are auditor docs, not the consumer spec view. Mechanical G-LEAK screen also passes (hard_failures empty); no relaxed_leakage flag or RELAXED_LEAKAGE.md present, so no deferral needed. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
