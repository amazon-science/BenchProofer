# P2 adversarial audit — sympy__sympy-22714

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(coord_extra), 1 / 2))
     Requires(len(coord_kind) == len(coord_verdict))
     Requires(len(coord_kind) == len(coord_extra))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(coord_kind), 1 / 2))
@@ -89,26 +87,13 @@
     rejected = False
     i = len(coord_kind)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(coord_kind), 1 / 2))
         Invariant(Acc(list_pred(coord_verdict), 1 / 2))
         Invariant(Acc(list_pred(coord_extra), 1 / 2))
         Invariant(0 <= i and i <= len(coord_kind))
         Invariant(len(coord_kind) == len(coord_verdict))
         Invariant(len(coord_kind) == len(coord_extra))
-        Invariant(rejected == any_triggering(
-            ToSeq(coord_kind).drop(i), ToSeq(coord_verdict).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The front-recursive fold unfolds at the head of drop(i-1); supply the
-        # head/tail split so a single unfold relates step i-1 to step i.
-        Assert(ToSeq(coord_kind).drop(i - 1)[0] == coord_kind[i - 1])
-        Assert(ToSeq(coord_verdict).drop(i - 1)[0] == coord_verdict[i - 1])
-        Assert(ToSeq(coord_kind).drop(i - 1).drop(1)
-               == ToSeq(coord_kind).drop(i))
-        Assert(ToSeq(coord_verdict).drop(i - 1).drop(1)
-               == ToSeq(coord_verdict).drop(i))
-        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:
+        if coord_kind[i - 1] == 1 and coord_extra[i - 1] == 1:
             rejected = True
         i = i - 1
     return rejected
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(coord_extra), 1 / 2))
     Requires(len(coord_kind) == len(coord_verdict))
     Requires(len(coord_kind) == len(coord_extra))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(coord_kind), 1 / 2))
@@ -88,20 +86,13 @@
     # impl-start
     rejected = False
     i = len(coord_kind)
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(coord_kind), 1 / 2))
         Invariant(Acc(list_pred(coord_verdict), 1 / 2))
         Invariant(Acc(list_pred(coord_extra), 1 / 2))
-        Invariant(0 <= i and i <= len(coord_kind))
+        Invariant(1 <= i and i <= len(coord_kind))
         Invariant(len(coord_kind) == len(coord_verdict))
         Invariant(len(coord_kind) == len(coord_extra))
-        Invariant(rejected == any_triggering(
-            ToSeq(coord_kind).drop(i), ToSeq(coord_verdict).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The front-recursive fold unfolds at the head of drop(i-1); supply the
-        # head/tail split so a single unfold relates step i-1 to step i.
         Assert(ToSeq(coord_kind).drop(i - 1)[0] == coord_kind[i - 1])
         Assert(ToSeq(coord_verdict).drop(i - 1)[0] == coord_verdict[i - 1])
         Assert(ToSeq(coord_kind).drop(i - 1).drop(1)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(coord_extra), 1 / 2))
     Requires(len(coord_kind) == len(coord_verdict))
     Requires(len(coord_kind) == len(coord_extra))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(coord_kind), 1 / 2))
@@ -89,26 +87,13 @@
     rejected = False
     i = len(coord_kind)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(coord_kind), 1 / 2))
         Invariant(Acc(list_pred(coord_verdict), 1 / 2))
         Invariant(Acc(list_pred(coord_extra), 1 / 2))
         Invariant(0 <= i and i <= len(coord_kind))
         Invariant(len(coord_kind) == len(coord_verdict))
         Invariant(len(coord_kind) == len(coord_extra))
-        Invariant(rejected == any_triggering(
-            ToSeq(coord_kind).drop(i), ToSeq(coord_verdict).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The front-recursive fold unfolds at the head of drop(i-1); supply the
-        # head/tail split so a single unfold relates step i-1 to step i.
-        Assert(ToSeq(coord_kind).drop(i - 1)[0] == coord_kind[i - 1])
-        Assert(ToSeq(coord_verdict).drop(i - 1)[0] == coord_verdict[i - 1])
-        Assert(ToSeq(coord_kind).drop(i - 1).drop(1)
-               == ToSeq(coord_kind).drop(i))
-        Assert(ToSeq(coord_verdict).drop(i - 1).drop(1)
-               == ToSeq(coord_verdict).drop(i))
-        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:
+        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] != 1:
             rejected = True
         i = i - 1
     return rejected
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(coord_extra), 1 / 2))
     Requires(len(coord_kind) == len(coord_verdict))
     Requires(len(coord_kind) == len(coord_extra))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(coord_kind), 1 / 2))
@@ -89,27 +87,13 @@
     rejected = False
     i = len(coord_kind)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(coord_kind), 1 / 2))
         Invariant(Acc(list_pred(coord_verdict), 1 / 2))
         Invariant(Acc(list_pred(coord_extra), 1 / 2))
         Invariant(0 <= i and i <= len(coord_kind))
         Invariant(len(coord_kind) == len(coord_verdict))
         Invariant(len(coord_kind) == len(coord_extra))
-        Invariant(rejected == any_triggering(
-            ToSeq(coord_kind).drop(i), ToSeq(coord_verdict).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The front-recursive fold unfolds at the head of drop(i-1); supply the
-        # head/tail split so a single unfold relates step i-1 to step i.
-        Assert(ToSeq(coord_kind).drop(i - 1)[0] == coord_kind[i - 1])
-        Assert(ToSeq(coord_verdict).drop(i - 1)[0] == coord_verdict[i - 1])
-        Assert(ToSeq(coord_kind).drop(i - 1).drop(1)
-               == ToSeq(coord_kind).drop(i))
-        Assert(ToSeq(coord_verdict).drop(i - 1).drop(1)
-               == ToSeq(coord_verdict).drop(i))
-        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:
-            rejected = True
+        rejected = coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0
         i = i - 1
     return rejected
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(coord_extra), 1 / 2))
     Requires(len(coord_kind) == len(coord_verdict))
     Requires(len(coord_kind) == len(coord_extra))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(coord_kind), 1 / 2))
@@ -89,26 +87,13 @@
     rejected = False
     i = len(coord_kind)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(coord_kind), 1 / 2))
         Invariant(Acc(list_pred(coord_verdict), 1 / 2))
         Invariant(Acc(list_pred(coord_extra), 1 / 2))
         Invariant(0 <= i and i <= len(coord_kind))
         Invariant(len(coord_kind) == len(coord_verdict))
         Invariant(len(coord_kind) == len(coord_extra))
-        Invariant(rejected == any_triggering(
-            ToSeq(coord_kind).drop(i), ToSeq(coord_verdict).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The front-recursive fold unfolds at the head of drop(i-1); supply the
-        # head/tail split so a single unfold relates step i-1 to step i.
-        Assert(ToSeq(coord_kind).drop(i - 1)[0] == coord_kind[i - 1])
-        Assert(ToSeq(coord_verdict).drop(i - 1)[0] == coord_verdict[i - 1])
-        Assert(ToSeq(coord_kind).drop(i - 1).drop(1)
-               == ToSeq(coord_kind).drop(i))
-        Assert(ToSeq(coord_verdict).drop(i - 1).drop(1)
-               == ToSeq(coord_verdict).drop(i))
-        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:
+        if coord_verdict[i - 1] == 0:
             rejected = True
         i = i - 1
     return rejected
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(coord_extra), 1 / 2))
     Requires(len(coord_kind) == len(coord_verdict))
     Requires(len(coord_kind) == len(coord_extra))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(coord_kind), 1 / 2))
@@ -87,29 +85,19 @@
     # post-conditions-end
     # impl-start
     rejected = False
-    i = len(coord_kind)
-    while i > 0:
-        # invariants-start
+    i = 0
+    n = len(coord_kind)
+    while i < n:
         Invariant(Acc(list_pred(coord_kind), 1 / 2))
         Invariant(Acc(list_pred(coord_verdict), 1 / 2))
         Invariant(Acc(list_pred(coord_extra), 1 / 2))
-        Invariant(0 <= i and i <= len(coord_kind))
+        Invariant(0 <= i and i <= n)
         Invariant(len(coord_kind) == len(coord_verdict))
         Invariant(len(coord_kind) == len(coord_extra))
         Invariant(rejected == any_triggering(
-            ToSeq(coord_kind).drop(i), ToSeq(coord_verdict).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The front-recursive fold unfolds at the head of drop(i-1); supply the
-        # head/tail split so a single unfold relates step i-1 to step i.
-        Assert(ToSeq(coord_kind).drop(i - 1)[0] == coord_kind[i - 1])
-        Assert(ToSeq(coord_verdict).drop(i - 1)[0] == coord_verdict[i - 1])
-        Assert(ToSeq(coord_kind).drop(i - 1).drop(1)
-               == ToSeq(coord_kind).drop(i))
-        Assert(ToSeq(coord_verdict).drop(i - 1).drop(1)
-               == ToSeq(coord_verdict).drop(i))
-        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:
+            ToSeq(coord_kind).take(i), ToSeq(coord_verdict).take(i)))
+        if coord_kind[i] == 1 and coord_verdict[i] == 0:
             rejected = True
-        i = i - 1
+        i = i + 1
     return rejected
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(coord_extra), 1 / 2))
     Requires(len(coord_kind) == len(coord_verdict))
     Requires(len(coord_kind) == len(coord_extra))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(coord_kind), 1 / 2))
@@ -86,30 +84,5 @@
                                        ToSeq(coord_verdict)))
     # post-conditions-end
     # impl-start
-    rejected = False
-    i = len(coord_kind)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(coord_kind), 1 / 2))
-        Invariant(Acc(list_pred(coord_verdict), 1 / 2))
-        Invariant(Acc(list_pred(coord_extra), 1 / 2))
-        Invariant(0 <= i and i <= len(coord_kind))
-        Invariant(len(coord_kind) == len(coord_verdict))
-        Invariant(len(coord_kind) == len(coord_extra))
-        Invariant(rejected == any_triggering(
-            ToSeq(coord_kind).drop(i), ToSeq(coord_verdict).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The front-recursive fold unfolds at the head of drop(i-1); supply the
-        # head/tail split so a single unfold relates step i-1 to step i.
-        Assert(ToSeq(coord_kind).drop(i - 1)[0] == coord_kind[i - 1])
-        Assert(ToSeq(coord_verdict).drop(i - 1)[0] == coord_verdict[i - 1])
-        Assert(ToSeq(coord_kind).drop(i - 1).drop(1)
-               == ToSeq(coord_kind).drop(i))
-        Assert(ToSeq(coord_verdict).drop(i - 1).drop(1)
-               == ToSeq(coord_verdict).drop(i))
-        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:
-            rejected = True
-        i = i - 1
-    return rejected
+    return False
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     Requires(Acc(list_pred(coord_extra), 1 / 2))
     Requires(len(coord_kind) == len(coord_verdict))
     Requires(len(coord_kind) == len(coord_extra))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(coord_kind), 1 / 2))
@@ -89,7 +87,6 @@
     rejected = False
     i = len(coord_kind)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(coord_kind), 1 / 2))
         Invariant(Acc(list_pred(coord_verdict), 1 / 2))
         Invariant(Acc(list_pred(coord_extra), 1 / 2))
@@ -98,18 +95,13 @@
         Invariant(len(coord_kind) == len(coord_extra))
         Invariant(rejected == any_triggering(
             ToSeq(coord_kind).drop(i), ToSeq(coord_verdict).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The front-recursive fold unfolds at the head of drop(i-1); supply the
-        # head/tail split so a single unfold relates step i-1 to step i.
         Assert(ToSeq(coord_kind).drop(i - 1)[0] == coord_kind[i - 1])
         Assert(ToSeq(coord_verdict).drop(i - 1)[0] == coord_verdict[i - 1])
         Assert(ToSeq(coord_kind).drop(i - 1).drop(1)
                == ToSeq(coord_kind).drop(i))
         Assert(ToSeq(coord_verdict).drop(i - 1).drop(1)
                == ToSeq(coord_verdict).drop(i))
-        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:
-            rejected = True
+        rejected = rejected or (coord_verdict[i - 1] == 0 and coord_kind[i - 1] == 1)
         i = i - 1
     return rejected
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-22714.

Behaviour under specification (an abstract behavioural contract):

  A constructor screens a list of coordinates and rejects the list (returns
  True, i.e. takes the error branch) exactly when SOME coordinate satisfies a
  two-part condition: the coordinate belongs to a particular kind AND a
  per-coordinate verdict resolves to its NEGATIVE outcome. A coordinate whose
  verdict resolves to its POSITIVE outcome, or whose verdict is left UNDECIDED,
  never triggers the rejection on its own.

Each coordinate is abstracted by two facts the screen reads:

  * `coord_kind[i]` -- a classification of the i-th coordinate
    (1 = the kind the screen looks at, 0 = any other kind);
  * `coord_verdict[i]` -- a verdict for the i-th coordinate, an int in
    {-1, 0, 1}: 1 = positive outcome, 0 = negative outcome, -1 = undecided.

The screen rejects iff there is a coordinate of the looked-at kind whose
verdict is the negative outcome (`coord_verdict[i] == 0`). The positive
outcome (1) and the undecided verdict (-1) are both accepted.

A third, redundant fact `coord_extra[i]` (a 0/1 summary of the same
coordinate) is supplied to every implementation but the specification never
mentions it. It is present only so that every candidate implementation
type-checks against the same signature, whichever fact it chooses to read.

All facts are carried as `int`; the coordinate facts are modelled as
`List[int]` and the specification is carried by `PSeq[int]` via the
front-recursive fold `any_triggering` (one auto-unfold per loop step).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No opaque callees are consumed here: the screening predicate is modelled
#  directly as the fold `any_triggering` below.)
# axioms-end

# pure-start
@Pure
def coord_triggers(kind: int, verdict: int) -> bool:
    """A single coordinate triggers the rejection iff it is of the looked-at
    kind (kind == 1) AND its verdict is the negative outcome (verdict == 0).
    The positive outcome (1) and the undecided verdict (-1) do NOT trigger."""
    return kind == 1 and verdict == 0

@Pure
def any_triggering(kind: PSeq[int], verdict: PSeq[int]) -> bool:
    """Whether SOME coordinate triggers the rejection. Front-recursive over the
    head so one unfold is available per loop step. Total: an exhausted (empty)
    sequence contributes nothing."""
    if len(kind) == 0 or len(verdict) == 0:
        return False
    return (coord_triggers(kind[0], verdict[0])
            or any_triggering(kind.drop(1), verdict.drop(1)))
# pure-end

def screen_coordinates(coord_kind: List[int],
                       coord_verdict: List[int],
                       coord_extra: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(coord_kind), 1 / 2))
    Requires(Acc(list_pred(coord_verdict), 1 / 2))
    Requires(Acc(list_pred(coord_extra), 1 / 2))
    Requires(len(coord_kind) == len(coord_verdict))
    Requires(len(coord_kind) == len(coord_extra))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(coord_kind), 1 / 2))
    Ensures(Acc(list_pred(coord_verdict), 1 / 2))
    Ensures(Acc(list_pred(coord_extra), 1 / 2))
    # The screen rejects iff SOME coordinate is of the looked-at kind and its
    # verdict is the negative outcome. (The positive outcome and the undecided
    # verdict are accepted; the redundant extra fact is irrelevant to the
    # verdict.)
    Ensures(Result() == any_triggering(ToSeq(coord_kind),
                                       ToSeq(coord_verdict)))
    # post-conditions-end
    # impl-start
    rejected = False
    i = len(coord_kind)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(coord_kind), 1 / 2))
        Invariant(Acc(list_pred(coord_verdict), 1 / 2))
        Invariant(Acc(list_pred(coord_extra), 1 / 2))
        Invariant(0 <= i and i <= len(coord_kind))
        Invariant(len(coord_kind) == len(coord_verdict))
        Invariant(len(coord_kind) == len(coord_extra))
        Invariant(rejected == any_triggering(
            ToSeq(coord_kind).drop(i), ToSeq(coord_verdict).drop(i)))
        # invariants-end
        # The front-recursive fold unfolds at the head of drop(i-1); supply the
        # head/tail split so a single unfold relates step i-1 to step i.
        Assert(ToSeq(coord_kind).drop(i - 1)[0] == coord_kind[i - 1])
        Assert(ToSeq(coord_verdict).drop(i - 1)[0] == coord_verdict[i - 1])
        Assert(ToSeq(coord_kind).drop(i - 1).drop(1)
               == ToSeq(coord_kind).drop(i))
        Assert(ToSeq(coord_verdict).drop(i - 1).drop(1)
               == ToSeq(coord_verdict).drop(i))
        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:
            rejected = True
        i = i - 1
    return rejected
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's postcondition `Result() == any_triggering(ToSeq(coord_kind), ToSeq(coord_verdict))` is a FULLY-FUNCTIONAL postcondition: it pins the return value uniquely for every input as a deterministic function of coord_kind/coord_verdict only (coord_extra is a free, unconstrained parameter the spec never mentions). Any impl that verifies therefore computes exactly the deep-model boolean, so the only surviving trust points are (a) no verifying WRONG impl exists, and (b) the A-reference legs A2/A3 (deep model <-> real SymPy).

PROTOCOL RUN (all; project root; SBU_BENCHMARK_DIR=benchmark-verified; verifier env swebench-lean python). Each same-spec confirmed byte-identical spec signature (exit 0). weakness run in 3 background batches of <=3 JVM+Z3 each.

  atk_1.py  PREPATCH BUG (keys off coord_extra instead of coord_verdict). `python -m swebench_unified.adversary weakness nagini sympy__sympy-22714 atk_1.py` -> exit 2 NOT-A-COUNTEREXAMPLE (verification failed). Prepatch reproduced (== model_prepatch.py logic; also G-DIFF pass).
  atk_2.py  PARTIAL-DOMAIN (loop `while i>1`, never screens coordinate 0). weakness -> exit 2, fails verify (postcondition violated on a triggering head coordinate).
  atk_3.py  BOUNDARY (rejects on coord_verdict != 1, over-rejecting the UNDECIDED -1 verdict). weakness -> exit 2, fails verify.
  atk_4.py  CONTROL-FLOW-EFFECT (assigns/overwrites `rejected` each iteration instead of OR-accumulating, so only the last-scanned coordinate counts). weakness -> exit 2, fails verify.
  atk_5.py  UNGROUNDED (drops the kind conjunct: rejects on coord_verdict==0 regardless of coord_kind). weakness -> exit 2, fails verify.
  atk_6.py  forward-loop variant with a `take(i)` invariant lacking the head/tail unfold lemmas -> exit 2, fails verify (proof-technique failure; kept as a distinct attempt).
  atk_7.py  DEGENERATE (constant `return False`). weakness -> exit 2, fails verify.
  atk_8.py  CORRECT ECHO (gold reverse-loop proof structure, conjunct order commuted + OR-accumulation). weakness -> exit 0 CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (11.8s).

MANDATORY MATERIALIZE+RESOLVE for the sole verifying CANDIDATE (atk_8): its faithful refinement (`any(coord_verdict[i]==0 and coord_kind[i]==1)` <-> `any(im(a).is_zero is False and a.is_number for a in coords)`, the gold guard with commuted conjuncts) written to patch_atk_8.diff and run through the OFFICIAL harness: `run_resolve('sympy__sympy-22714', patch_atk_8.diff, run_id='sbu-eqaudit-atk8-mwse56kk')` -> RESOLVED: True, COMPLETED: True (executed, Docker). So the one verifying candidate RESOLVES => it is an echo, NOT a weakness (per the resolved-echo policy). No verifying wrong impl's patch fails to resolve; verify does not admit a non-resolving impl.

A-LEG / CORRESPONDENCE AUDIT (refinement.md): A1=R (Tuple[Expr] -> three parallel List[int] coordinate facts). A2=A-reference (coord_triggers == (kind==1 and verdict==0) <-> real `a.is_number and im(a).is_zero is False`), A3=A-reference+R (any_triggering fold <-> any(...)), A4=I (True<->raise ValueError). NO consumed axioms (meta axioms:[] ; axioms region is a comment only; grep finds no @ContractOnly), NO kind-3 (unexpressible-changed-op) legs. Independent cross-check with real SymPy over 38 coordinate observations x {evaluate True/False} (numbers, symbols, genuine imaginaries, complex, transcendentals, oo/zoo/nan, positive/real/imaginary symbols): gold guard == commuted atk8 guard == deep model, 0 mismatches, including fuzzy `is_number` (None -> kind 0) and `is_zero is None` (-> verdict -1). Consistent with recorded G-AX (8084 obs, 0 mismatch) and G-CONF (100000 tuples vs real patched repo, 0 disagreements, seed 227140).

Positive control (unmodified model.py) verifies: `bash scripts/nagini_verify.sh positive_control.py` -> exit 0 (11.29s). Prepatch fails verify (reproduced). Requirement of >=5 distinct wrong impls exceeded (7 distinct wrong impls: atk_1..atk_7) plus 1 correct echo (atk_8) whose materialized patch was resolve-run. None breaks the spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sympy__sympy-22714.

Behaviour under specification (an abstract behavioural contract):

  A constructor screens a list of coordinates and rejects the list (returns
  True, i.e. takes the error branch) exactly when SOME coordinate satisfies a
  two-part condition: the coordinate belongs to a particular kind AND a
  per-coordinate verdict resolves to its NEGATIVE outcome. A coordinate whose
  verdict resolves to its POSITIVE outcome, or whose verdict is left UNDECIDED,
  never triggers the rejection on its own.

Each coordinate is abstracted by two facts the screen reads:

  * `coord_kind[i]` -- a classification of the i-th coordinate
    (1 = the kind the screen looks at, 0 = any other kind);
  * `coord_verdict[i]` -- a verdict for the i-th coordinate, an int in
    {-1, 0, 1}: 1 = positive outcome, 0 = negative outcome, -1 = undecided.

The screen rejects iff there is a coordinate of the looked-at kind whose
verdict is the negative outcome (`coord_verdict[i] == 0`). The positive
outcome (1) and the undecided verdict (-1) are both accepted.

A third, redundant fact `coord_extra[i]` (a 0/1 summary of the same
coordinate) is supplied to every implementation but the specification never
mentions it. It is present only so that every candidate implementation
type-checks against the same signature, whichever fact it chooses to read.

All facts are carried as `int`; the coordinate facts are modelled as
`List[int]` and the specification is carried by `PSeq[int]` via the
front-recursive fold `any_triggering` (one auto-unfold per loop step).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No opaque callees are consumed here: the screening predicate is modelled
#  directly as the fold `any_triggering` below.)
# axioms-end

# pure-start
@Pure
def coord_triggers(kind: int, verdict: int) -> bool:
    """A single coordinate triggers the rejection iff it is of the looked-at
    kind (kind == 1) AND its verdict is the negative outcome (verdict == 0).
    The positive outcome (1) and the undecided verdict (-1) do NOT trigger."""
    return kind == 1 and verdict == 0

@Pure
def any_triggering(kind: PSeq[int], verdict: PSeq[int]) -> bool:
    """Whether SOME coordinate triggers the rejection. Front-recursive over the
    head so one unfold is available per loop step. Total: an exhausted (empty)
    sequence contributes nothing."""
    if len(kind) == 0 or len(verdict) == 0:
        return False
    return (coord_triggers(kind[0], verdict[0])
            or any_triggering(kind.drop(1), verdict.drop(1)))
# pure-end

def screen_coordinates(coord_kind: List[int],
                       coord_verdict: List[int],
                       coord_extra: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(coord_kind), 1 / 2))
    Requires(Acc(list_pred(coord_verdict), 1 / 2))
    Requires(Acc(list_pred(coord_extra), 1 / 2))
    Requires(len(coord_kind) == len(coord_verdict))
    Requires(len(coord_kind) == len(coord_extra))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(coord_kind), 1 / 2))
    Ensures(Acc(list_pred(coord_verdict), 1 / 2))
    Ensures(Acc(list_pred(coord_extra), 1 / 2))
    # The screen rejects iff SOME coordinate is of the looked-at kind and its
    # verdict is the negative outcome. (The positive outcome and the undecided
    # verdict are accepted; the redundant extra fact is irrelevant to the
    # verdict.)
    Ensures(Result() == any_triggering(ToSeq(coord_kind),
                                       ToSeq(coord_verdict)))
    # post-conditions-end
    # impl-start
    rejected = False
    i = len(coord_kind)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(coord_kind), 1 / 2))
        Invariant(Acc(list_pred(coord_verdict), 1 / 2))
        Invariant(Acc(list_pred(coord_extra), 1 / 2))
        Invariant(0 <= i and i <= len(coord_kind))
        Invariant(len(coord_kind) == len(coord_verdict))
        Invariant(len(coord_kind) == len(coord_extra))
        Invariant(rejected == any_triggering(
            ToSeq(coord_kind).drop(i), ToSeq(coord_verdict).drop(i)))
        # invariants-end
        # The front-recursive fold unfolds at the head of drop(i-1); supply the
        # head/tail split so a single unfold relates step i-1 to step i.
        Assert(ToSeq(coord_kind).drop(i - 1)[0] == coord_kind[i - 1])
        Assert(ToSeq(coord_verdict).drop(i - 1)[0] == coord_verdict[i - 1])
        Assert(ToSeq(coord_kind).drop(i - 1).drop(1)
               == ToSeq(coord_kind).drop(i))
        Assert(ToSeq(coord_verdict).drop(i - 1).drop(1)
               == ToSeq(coord_verdict).drop(i))
        if coord_kind[i - 1] == 1 and coord_verdict[i - 1] == 0:
            rejected = True
        i = i - 1
    return rejected
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's postcondition `Result() == any_triggering(ToSeq(coord_kind), ToSeq(coord_verdict))` is a FULLY-FUNCTIONAL postcondition: it pins the return value uniquely for every input as a deterministic function of coord_kind/coord_verdict only (coord_extra is a free, unconstrained parameter the spec never mentions). Any impl that verifies therefore computes exactly the deep-model boolean, so the only surviving trust points are (a) no verifying WRONG impl exists, and (b) the A-reference legs A2/A3 (deep model <-> real SymPy).

PROTOCOL RUN (all; project root; SBU_BENCHMARK_DIR=benchmark-verified; verifier env swebench-lean python). Each same-spec confirmed byte-identical spec signature (exit 0). weakness run in 3 background batches of <=3 JVM+Z3 each.

  atk_1.py  PREPATCH BUG (keys off coord_extra instead of coord_verdict). `python -m swebench_unified.adversary weakness nagini sympy__sympy-22714 atk_1.py` -> exit 2 NOT-A-COUNTEREXAMPLE (verification failed). Prepatch reproduced (== model_prepatch.py logic; also G-DIFF pass).
  atk_2.py  PARTIAL-DOMAIN (loop `while i>1`, never screens coordinate 0). weakness -> exit 2, fails verify (postcondition violated on a triggering head coordinate).
  atk_3.py  BOUNDARY (rejects on coord_verdict != 1, over-rejecting the UNDECIDED -1 verdict). weakness -> exit 2, fails verify.
  atk_4.py  CONTROL-FLOW-EFFECT (assigns/overwrites `rejected` each iteration instead of OR-accumulating, so only the last-scanned coordinate counts). weakness -> exit 2, fails verify.
  atk_5.py  UNGROUNDED (drops the kind conjunct: rejects on coord_verdict==0 regardless of coord_kind). weakness -> exit 2, fails verify.
  atk_6.py  forward-loop variant with a `take(i)` invariant lacking the head/tail unfold lemmas -> exit 2, fails verify (proof-technique failure; kept as a distinct attempt).
  atk_7.py  DEGENERATE (constant `return False`). weakness -> exit 2, fails verify.
  atk_8.py  CORRECT ECHO (gold reverse-loop proof structure, conjunct order commuted + OR-accumulation). weakness -> exit 0 CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (11.8s).

MANDATORY MATERIALIZE+RESOLVE for the sole verifying CANDIDATE (atk_8): its faithful refinement (`any(coord_verdict[i]==0 and coord_kind[i]==1)` <-> `any(im(a).is_zero is False and a.is_number for a in coords)`, the gold guard with commuted conjuncts) written to patch_atk_8.diff and run through the OFFICIAL harness: `run_resolve('sympy__sympy-22714', patch_atk_8.diff, run_id='sbu-eqaudit-atk8-mwse56kk')` -> RESOLVED: True, COMPLETED: True (executed, Docker). So the one verifying candidate RESOLVES => it is an echo, NOT a weakness (per the resolved-echo policy). No verifying wrong impl's patch fails to resolve; verify does not admit a non-resolving impl.

A-LEG / CORRESPONDENCE AUDIT (refinement.md): A1=R (Tuple[Expr] -> three parallel List[int] coordinate facts). A2=A-reference (coord_triggers == (kind==1 and verdict==0) <-> real `a.is_number and im(a).is_zero is False`), A3=A-reference+R (any_triggering fold <-> any(...)), A4=I (True<->raise ValueError). NO consumed axioms (meta axioms:[] ; axioms region is a comment only; grep finds no @ContractOnly), NO kind-3 (unexpressible-changed-op) legs. Independent cross-check with real SymPy over 38 coordinate observations x {evaluate True/False} (numbers, symbols, genuine imaginaries, complex, transcendentals, oo/zoo/nan, positive/real/imaginary symbols): gold guard == commuted atk8 guard == deep model, 0 mismatches, including fuzzy `is_number` (None -> kind 0) and `is_zero is None` (-> verdict -1). Consistent with recorded G-AX (8084 obs, 0 mismatch) and G-CONF (100000 tuples vs real patched repo, 0 disagreements, seed 227140).

Positive control (unmodified model.py) verifies: `bash scripts/nagini_verify.sh positive_control.py` -> exit 0 (11.29s). Prepatch fails verify (reproduced). Requirement of >=5 distinct wrong impls exceeded (7 distinct wrong impls: atk_1..atk_7) plus 1 correct echo (atk_8) whose materialized patch was resolve-run. None breaks the spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Setup: base_commit worktree (479939f8c6...); patched copy with the gold hunk applied at sympy/geometry/point.py:158 (im -> im.is_zero is False). Ran an INDEPENDENT differential probe (not the bundle's scripts, which import sympy.core.parameters — nonexistent at base_commit; the base API is sympy.core.evaluate) comparing the spec (any_triggering over enc_kind=a.is_number, enc_verdict tri-state of im(a).is_zero) against the real patched screen observed through Point(*coords) (True iff it raises the 'Imaginary coordinates are not permitted' ValueError).

Results within the modeled domain (len>=2):
- Exhaustive ordered pairs of a 34-atom pool x2 evaluation contexts (1568 checks): 0 disagreements.
- Randomized length 2-5 tuples (1500 checks) incl. composed expressions, both contexts: 0 disagreements.

Apparent 'fails' (1440/42034) in the unrestricted run were ALL length-1 tuples: verified Point(2*I)/Point(I)/Point(pi) raise TypeError from `if not is_sequence(coords)` / `len(coords)<2` path, pre-empting the screen. Correctly excluded by the bundle's stated input domain.

Also confirmed: same-spec on a byte-identical copy of model.py -> SAME (exit 0); Nagini verification of model.py -> 'Verification successful' (12.67s), so the spec is non-vacuous. axiom_check obligations (per-coordinate coord_triggers == a.is_number and im(a).is_zero is False; tuple fold == any(...)) hold on the reachable domain by the same probe. Spec is not too strong and does not drift from real repo behavior; the None->-1 undecided and is_zero-is-False==0 encodings are faithful (undecided/positive verdicts accepted, only certified-nonzero-imaginary of a concrete number triggers rejection, matching the gold guard).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement only (not hints_text). The problem_statement reveals only the SYMPTOM: `Point2D(Integer(1),Integer(2))` under `evaluate(False)` wrongly raises 'Imaginary coordinates are not permitted', and works without `evaluate(False)`. It does NOT reveal the fix mechanism. The gold edit is `if any(a.is_number and im(a) for a in coords):` -> `if any(a.is_number and im(a).is_zero is False for a in coords):` in sympy/geometry/point.py.

Mechanical screen (leakage.screen over spec_view): PASS, zero hard_failures. Confirmed independently: no diff markers, no gold-patch line reproduced, no patched file path/module path, changed-symbols set is empty (the patch touches no def/class name), no bug/fix narration terms in spec-view comments/docstrings.

Semantic check of the spec view: it is fully abstracted. It uses only invented identifiers (coord_kind, coord_verdict tri-state {-1,0,1}, coord_extra, coord_triggers, any_triggering) that name no patched repo symbol (im, is_zero, is_number, Point) and no path. The spec necessarily encodes the POST-patch behaviour (reject iff some coordinate of the looked-at kind has the NEGATIVE verdict; positive and undecided are accepted) -- that is unavoidable for any faithful spec and is not a leak.

The SymPy-specific content that IS the edit -- the shift from raw truthiness `im(a)` to certified `im(a).is_zero is False`, the fuzzy-bool None handling, and the fact that coord_extra is the ABANDONED pre-patch discriminator -- lives ONLY in mapping.md / refinement.md / meta.json (reviewer-facing, outside the spec view). In the spec view, coord_extra is described merely as 'a redundant fact the specification never mentions', with no hint that it is the pre-patch predicate. A solver cannot reconstruct `im(a).is_zero is False` from the spec view; the {-1,0,1} verdict abstraction hides the fuzzy-bool semantics. Generic terms present ('coordinates', 'constructor', 'rejects') are already public via the problem statement. No spec-view line localizes the edit beyond the public task.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.