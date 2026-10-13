# P2 adversarial audit — sphinx-doc__sphinx-10466

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.py`, `atk_infloop.py`, `atk_infloop2.py`, `atk_empty.py`, `atk_droplast.py`, `atk_dropfirst.py`, `atk_dupe.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
 def insert_sorted(xs: List[int], key: int) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -96,7 +94,6 @@
         # placed: the answer is `out` followed by the suffix copied verbatim.
         Invariant(Implies(placed,
                           ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
-        Invariant(MustTerminate(len(xs) - j + 1))
         # invariants-end
         cur = xs[j]
         # `ins`/`drop` unfold once on the suffix whose head is `cur`.
@@ -131,7 +128,6 @@
     # it); fractional permission, required and ensured, so no caller can satisfy
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(list_pred(recorded), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recorded), 1 / 2))
@@ -145,18 +141,13 @@
     result = []  # type: List[int]
     i = 0
     while i < len(recorded):
-        # invariants-start
         Invariant(Acc(list_pred(recorded), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(recorded))
-        Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
-        Invariant(MustTerminate(len(recorded) - i + 1))
-        # invariants-end
+        Invariant(ToSeq(result) == ToSeq(recorded).take(i))
         key = recorded[i]
         Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
-        Assert(ToSeq(recorded).take(i + 1)[i] == key)
-        Assert(ToSeq(recorded).take(i + 1).take(i) == ToSeq(recorded).take(i))
-        result = insert_sorted(result, key)
+        result = result + [key]
         i = i + 1
     Assert(ToSeq(recorded).take(len(recorded)) == ToSeq(recorded))
     return result
```

Attack 2 — `atk_infloop.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
 def insert_sorted(xs: List[int], key: int) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -96,7 +94,6 @@
         # placed: the answer is `out` followed by the suffix copied verbatim.
         Invariant(Implies(placed,
                           ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
-        Invariant(MustTerminate(len(xs) - j + 1))
         # invariants-end
         cur = xs[j]
         # `ins`/`drop` unfold once on the suffix whose head is `cur`.
@@ -131,7 +128,6 @@
     # it); fractional permission, required and ensured, so no caller can satisfy
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(list_pred(recorded), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recorded), 1 / 2))
@@ -143,21 +139,8 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(recorded):
-        # invariants-start
+    while True:
         Invariant(Acc(list_pred(recorded), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(recorded))
-        Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
-        Invariant(MustTerminate(len(recorded) - i + 1))
-        # invariants-end
-        key = recorded[i]
-        Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
-        Assert(ToSeq(recorded).take(i + 1)[i] == key)
-        Assert(ToSeq(recorded).take(i + 1).take(i) == ToSeq(recorded).take(i))
-        result = insert_sorted(result, key)
-        i = i + 1
-    Assert(ToSeq(recorded).take(len(recorded)) == ToSeq(recorded))
     return result
     # impl-end
```

Attack 3 — `atk_infloop2.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
 def insert_sorted(xs: List[int], key: int) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -96,7 +94,6 @@
         # placed: the answer is `out` followed by the suffix copied verbatim.
         Invariant(Implies(placed,
                           ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
-        Invariant(MustTerminate(len(xs) - j + 1))
         # invariants-end
         cur = xs[j]
         # `ins`/`drop` unfold once on the suffix whose head is `cur`.
@@ -131,7 +128,6 @@
     # it); fractional permission, required and ensured, so no caller can satisfy
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(list_pred(recorded), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recorded), 1 / 2))
@@ -144,20 +140,10 @@
     # impl-start
     result = []  # type: List[int]
     i = 0
-    while i < len(recorded):
-        # invariants-start
+    while i <= len(recorded):
         Invariant(Acc(list_pred(recorded), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(recorded))
-        Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
-        Invariant(MustTerminate(len(recorded) - i + 1))
-        # invariants-end
-        key = recorded[i]
-        Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
-        Assert(ToSeq(recorded).take(i + 1)[i] == key)
-        Assert(ToSeq(recorded).take(i + 1).take(i) == ToSeq(recorded).take(i))
-        result = insert_sorted(result, key)
-        i = i + 1
-    Assert(ToSeq(recorded).take(len(recorded)) == ToSeq(recorded))
+        Invariant(0 <= i)
+        i = i + 0
     return result
     # impl-end
```

Attack 4 — `atk_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
 def insert_sorted(xs: List[int], key: int) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -96,7 +94,6 @@
         # placed: the answer is `out` followed by the suffix copied verbatim.
         Invariant(Implies(placed,
                           ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
-        Invariant(MustTerminate(len(xs) - j + 1))
         # invariants-end
         cur = xs[j]
         # `ins`/`drop` unfold once on the suffix whose head is `cur`.
@@ -131,7 +128,6 @@
     # it); fractional permission, required and ensured, so no caller can satisfy
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(list_pred(recorded), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recorded), 1 / 2))
@@ -143,21 +139,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(recorded):
-        # invariants-start
-        Invariant(Acc(list_pred(recorded), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(recorded))
-        Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
-        Invariant(MustTerminate(len(recorded) - i + 1))
-        # invariants-end
-        key = recorded[i]
-        Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
-        Assert(ToSeq(recorded).take(i + 1)[i] == key)
-        Assert(ToSeq(recorded).take(i + 1).take(i) == ToSeq(recorded).take(i))
-        result = insert_sorted(result, key)
-        i = i + 1
-    Assert(ToSeq(recorded).take(len(recorded)) == ToSeq(recorded))
     return result
     # impl-end
```

Attack 5 — `atk_droplast.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
 def insert_sorted(xs: List[int], key: int) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -96,7 +94,6 @@
         # placed: the answer is `out` followed by the suffix copied verbatim.
         Invariant(Implies(placed,
                           ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
-        Invariant(MustTerminate(len(xs) - j + 1))
         # invariants-end
         cur = xs[j]
         # `ins`/`drop` unfold once on the suffix whose head is `cur`.
@@ -131,7 +128,6 @@
     # it); fractional permission, required and ensured, so no caller can satisfy
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(list_pred(recorded), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recorded), 1 / 2))
@@ -144,20 +140,16 @@
     # impl-start
     result = []  # type: List[int]
     i = 0
-    while i < len(recorded):
-        # invariants-start
+    while i < len(recorded) - 1:
         Invariant(Acc(list_pred(recorded), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(recorded))
         Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
-        Invariant(MustTerminate(len(recorded) - i + 1))
-        # invariants-end
         key = recorded[i]
         Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
         Assert(ToSeq(recorded).take(i + 1)[i] == key)
         Assert(ToSeq(recorded).take(i + 1).take(i) == ToSeq(recorded).take(i))
         result = insert_sorted(result, key)
         i = i + 1
-    Assert(ToSeq(recorded).take(len(recorded)) == ToSeq(recorded))
     return result
     # impl-end
```

Attack 6 — `atk_dropfirst.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
 def insert_sorted(xs: List[int], key: int) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -96,7 +94,6 @@
         # placed: the answer is `out` followed by the suffix copied verbatim.
         Invariant(Implies(placed,
                           ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
-        Invariant(MustTerminate(len(xs) - j + 1))
         # invariants-end
         cur = xs[j]
         # `ins`/`drop` unfold once on the suffix whose head is `cur`.
@@ -131,7 +128,6 @@
     # it); fractional permission, required and ensured, so no caller can satisfy
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(list_pred(recorded), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recorded), 1 / 2))
@@ -143,21 +139,13 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
+    i = 1
     while i < len(recorded):
-        # invariants-start
         Invariant(Acc(list_pred(recorded), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(recorded))
-        Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
-        Invariant(MustTerminate(len(recorded) - i + 1))
-        # invariants-end
+        Invariant(1 <= i and i <= len(recorded))
         key = recorded[i]
-        Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
-        Assert(ToSeq(recorded).take(i + 1)[i] == key)
-        Assert(ToSeq(recorded).take(i + 1).take(i) == ToSeq(recorded).take(i))
         result = insert_sorted(result, key)
         i = i + 1
-    Assert(ToSeq(recorded).take(len(recorded)) == ToSeq(recorded))
     return result
     # impl-end
```

Attack 7 — `atk_dupe.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
 def insert_sorted(xs: List[int], key: int) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -96,7 +94,6 @@
         # placed: the answer is `out` followed by the suffix copied verbatim.
         Invariant(Implies(placed,
                           ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
-        Invariant(MustTerminate(len(xs) - j + 1))
         # invariants-end
         cur = xs[j]
         # `ins`/`drop` unfold once on the suffix whose head is `cur`.
@@ -131,7 +128,6 @@
     # it); fractional permission, required and ensured, so no caller can satisfy
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(list_pred(recorded), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recorded), 1 / 2))
@@ -145,19 +141,16 @@
     result = []  # type: List[int]
     i = 0
     while i < len(recorded):
-        # invariants-start
         Invariant(Acc(list_pred(recorded), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(recorded))
         Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
-        Invariant(MustTerminate(len(recorded) - i + 1))
-        # invariants-end
         key = recorded[i]
         Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
         Assert(ToSeq(recorded).take(i + 1)[i] == key)
         Assert(ToSeq(recorded).take(i + 1).take(i) == ToSeq(recorded).take(i))
         result = insert_sorted(result, key)
+        result = result + [key]
         i = i + 1
-    Assert(ToSeq(recorded).take(len(recorded)) == ToSeq(recorded))
     return result
     # impl-end
```

Attack 8 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -68,7 +67,6 @@
 def insert_sorted(xs: List[int], key: int) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -96,7 +94,6 @@
         # placed: the answer is `out` followed by the suffix copied verbatim.
         Invariant(Implies(placed,
                           ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
-        Invariant(MustTerminate(len(xs) - j + 1))
         # invariants-end
         cur = xs[j]
         # `ins`/`drop` unfold once on the suffix whose head is `cur`.
@@ -131,7 +128,6 @@
     # it); fractional permission, required and ensured, so no caller can satisfy
     # a postcondition vacuously by overwriting the input.
     Requires(Acc(list_pred(recorded), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recorded), 1 / 2))
@@ -145,13 +141,11 @@
     result = []  # type: List[int]
     i = 0
     while i < len(recorded):
-        # invariants-start
         Invariant(Acc(list_pred(recorded), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(recorded))
         Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
-        Invariant(MustTerminate(len(recorded) - i + 1))
-        # invariants-end
+        Assert(True)
         key = recorded[i]
         Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
         Assert(ToSeq(recorded).take(i + 1)[i] == key)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-10466.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A translatable message accumulates a record of every place it occurs while a
  document set is scanned. Each occurrence carries a source identity and a line
  number, i.e. a comparable position. The same position can be recorded more
  than once (a message may be emitted repeatedly from the very same place), and
  occurrences arrive in scan order, which need not be sorted.

  When the catalogue is later enumerated for output, the sequence of positions
  reported for a message must be the CANONICAL position list: every distinct
  recorded position appears exactly once (no position is repeated) and the
  positions are listed in ascending order. Equivalently, the reported list is
  the ORDERED SET of the recorded positions: the deduplicated, strictly
  ascending arrangement of exactly the positions that were recorded. This makes
  the reported list independent of how many times, and in what order, a position
  happened to be recorded.

A recorded occurrence's position (a source identity together with a line
number) is modelled by a single integer key under the order-preserving,
equality-preserving identification of comparable positions with integers
(mapping.md). The recorded positions are a `List[int]`; the canonical reported
list is a `List[int]`. The specification is carried deeply by a pure
ordered-set construction (`dedup_sort`) over `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: the deduplicate-and-sort behaviour is the operation
# under specification and is modelled deeply, not behind an axiom.)
# axioms-end


# pure-start
@Pure
def ins(x: int, s: PSeq[int]) -> PSeq[int]:
    """Insert `x` into `s` just before the first element that is not below it,
    dropping `x` if it already occurs there. On a strictly-sorted `s` this is
    ordered-set insertion. Total (no quantified precondition) and front-
    recursive over `s` (one unfold per element)."""
    if len(s) == 0:
        return PSeq(x)
    if x < s[0]:
        return PSeq(x) + s
    if x == s[0]:
        return s
    return PSeq(s[0]) + ins(x, s.drop(1))


@Pure
def dedup_sort(s: PSeq[int]) -> PSeq[int]:
    """The ordered set of `s`: deduplicated and strictly ascending. Built by
    inserting the last element into the ordered set of the prefix, so the
    enumeration loop (which appends one recorded position at a time) tracks it
    with the invariant `result == dedup_sort(prefix)`."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return ins(s[len(s) - 1], dedup_sort(s.take(len(s) - 1)))
# pure-end


def insert_sorted(xs: List[int], key: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the impl computes exactly the pure ordered-set insertion.
    Ensures(ToSeq(Result()) == ins(key, ToSeq(xs)))
    # post-conditions-end
    # impl-start
    # Scan front-to-back, emitting each element until the slot for `key` is
    # found. The loop invariant peels `ins` one element at a time off the unseen
    # suffix `drop(j)` (matching `ins`'s own front recursion), so no auxiliary
    # sequence lemma is needed: the full answer always equals what has been
    # emitted, followed by the insertion into the remaining suffix.
    out = []  # type: List[int]
    j = 0
    placed = False  # type: bool
    while j < len(xs):
        # invariants-start
        Invariant(Acc(list_pred(xs), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(xs))
        # not yet placed: the answer is `out` followed by `ins` of the suffix.
        Invariant(Implies(not placed,
                          ins(key, ToSeq(xs)) == ToSeq(out) + ins(key, ToSeq(xs).drop(j))))
        # placed: the answer is `out` followed by the suffix copied verbatim.
        Invariant(Implies(placed,
                          ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
        # invariants-end
        cur = xs[j]
        # `ins`/`drop` unfold once on the suffix whose head is `cur`.
        Assert(ToSeq(xs).drop(j) == PSeq(cur) + ToSeq(xs).drop(j + 1))
        Assert(len(ToSeq(xs).drop(j)) > 0 and ToSeq(xs).drop(j)[0] == cur)
        if placed:
            out = out + [cur]
        elif cur < key:
            out = out + [cur]
        elif cur > key:
            # `ins(key, suffix) == [key] + suffix`; emit `key` then `cur`.
            out = out + [key]
            out = out + [cur]
            placed = True
        else:
            # `cur == key`: `ins(key, suffix) == suffix`; `key` already present.
            out = out + [cur]
            placed = True
        j = j + 1
    Assert(ToSeq(xs).drop(j) == ToSeq(xs).drop(len(xs)))
    Assert(ToSeq(xs).drop(len(xs)) == PSeq(0).take(0))
    if not placed:
        # the suffix is empty: `ins(key, [])== [key]`.
        out = out + [key]
    return out
    # impl-end


def canonical_positions(recorded: List[int]) -> List[int]:
    # pre-conditions-start
    # The recorded-positions list is read-only here (enumeration never mutates
    # it); fractional permission, required and ensured, so no caller can satisfy
    # a postcondition vacuously by overwriting the input.
    Requires(Acc(list_pred(recorded), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(recorded), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reported list is exactly the ordered set of the recorded positions:
    # the deduplicated, strictly ascending arrangement of exactly what was
    # recorded.
    Ensures(ToSeq(Result()) == dedup_sort(ToSeq(recorded)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(recorded):
        # invariants-start
        Invariant(Acc(list_pred(recorded), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(recorded))
        Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
        # invariants-end
        key = recorded[i]
        Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
        Assert(ToSeq(recorded).take(i + 1)[i] == key)
        Assert(ToSeq(recorded).take(i + 1).take(i) == ToSeq(recorded).take(i))
        result = insert_sorted(result, key)
        i = i + 1
    Assert(ToSeq(recorded).take(len(recorded)) == ToSeq(recorded))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sphinx-doc__sphinx-10466 (nagini). project root, env python, SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE: canonical_positions has a TOTAL precondition (Acc(list_pred,1/2) only) and an output-pinning postcondition ToSeq(Result())==dedup_sort(ToSeq(recorded)) with FRESH Acc(list_pred(Result())). dedup_sort/ins are DEEPLY modeled (@Pure); the axioms region is empty (no consumed axiom). Because the postcondition is total and the result permission is fresh, the ONLY way a functionally-wrong impl could verify is vacuously via non-termination; Assume/Refute are banned tokens. This is a tight, functionally-pinning spec.

8 same-spec attacks (adversary same-spec: all SAME) + positive control. weakness runs (adversary weakness nagini sphinx-doc__sphinx-10466 <file>) executed concurrently in 3 batches of <=3 JVM jobs:
- atk_prepatch (prepatch bug, verbatim projection no dedup/sort): NOT-A-COUNTEREXAMPLE, exit2 (rejected) -> prepatch reproduced.
- atk_infloop (while True, ungrounded-oracle/vacuous attempt): rejected.
- atk_infloop2 (while i<=len(recorded), i+=0, non-termination): rejected.
- atk_empty (partial-domain / return []): rejected.
- atk_droplast (boundary off-by-one, loop to len-1): rejected.
- atk_dropfirst (control-flow-effect, start i=1 skipping first): rejected.
- atk_dupe (dedup violation, append each key twice): rejected.
- atk_echo (functionally-correct echo, only added Assert(True)): CANDIDATE-COUNTEREXAMPLE, exit0 (shares spec AND verifies, ~ verify time recorded).
- pos_control (model.py verbatim): nagini_verify.sh -> Verification successful, 18.03s.

MANDATORY RESOLVE ON EVERY VERIFYING CANDIDATE: atk_echo is behaviorally identical to gold (computes exactly dedup_sort == sorted(set(...))), so its faithful refined patch IS the gold hunk. Materialized to atk_echo.patch and EXECUTED through the official harness via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-10466', patch, timeout=3600): RESOLVED=True, COMPLETED=True, ATTEMPTS=1, FLAKY=False, note='resolved'. So the one verifying candidate's patch RESOLVES -> no verify-not-correct gap.

A-LEG / refinement.md audit: every leg is R / A-reference / I; NO kind-3 and NO consumed axiom.
- A1 (recorded:List[int] <-> projected (source,line) tuples): R, tuple<->int order/equality-preserving bijection; validated by axiom_check.py check 2 (F2P + 20000 fuzz position lists) and conformance_check.py type bridge.
- A2 (result == dedup_sort <-> sorted(set(...))): A-reference. Deep model validated == real operation by G-AX. Ran axiom_check.py: exit0, 'dedup_sort deep model == sorted(set(...)) over 8 boundary + 20000 integer fuzz; integer-key abstraction faithful over 1 F2P + 20000 fuzz'. Independent cross-check (my own dedup_sort reimpl vs sorted(set), 50000 random lists) bad=0. Correspondence holds.
- A3 (Result() <-> positions -> Message(message,positions,uuids)): R/I; Message.__init__ stores locations=positions, F2P reads .locations. Holds.
- Section B (insert_sorted/canonical_positions <-> deep model): I; loops compute the pure functions by their loop invariants (result==dedup_sort(take(i))).
- Section C: confirmed no kind-3 step; the single changed op (compose projection with dedup+sort) is modeled deeply (A-reference), not hidden behind an axiom.
Model<->patch correspondence: gold replaces the verbatim projection with sorted(set(...)) at gettext.py:60-61; canonical_positions postcondition pins exactly dedup_sort, matching. Sound.

VERDICT: SOUND. >=5 distinct wrong-impl classes (partial-domain, boundary, control-flow-effect, non-termination x2, dedup-violation, ungrounded-oracle/vacuous, prepatch) all REJECTED by the spec; the only verifying same-spec impl is a correct echo whose materialized faithful patch RESOLVED under the official harness. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.py`, `atk_infloop.py`, `atk_infloop2.py`, `atk_empty.py`, `atk_droplast.py`, `atk_dropfirst.py`, `atk_dupe.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_infloop.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_infloop2.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_empty.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_droplast.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_dropfirst.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_dupe.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-10466.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A translatable message accumulates a record of every place it occurs while a
  document set is scanned. Each occurrence carries a source identity and a line
  number, i.e. a comparable position. The same position can be recorded more
  than once (a message may be emitted repeatedly from the very same place), and
  occurrences arrive in scan order, which need not be sorted.

  When the catalogue is later enumerated for output, the sequence of positions
  reported for a message must be the CANONICAL position list: every distinct
  recorded position appears exactly once (no position is repeated) and the
  positions are listed in ascending order. Equivalently, the reported list is
  the ORDERED SET of the recorded positions: the deduplicated, strictly
  ascending arrangement of exactly the positions that were recorded. This makes
  the reported list independent of how many times, and in what order, a position
  happened to be recorded.

A recorded occurrence's position (a source identity together with a line
number) is modelled by a single integer key under the order-preserving,
equality-preserving identification of comparable positions with integers
(mapping.md). The recorded positions are a `List[int]`; the canonical reported
list is a `List[int]`. The specification is carried deeply by a pure
ordered-set construction (`dedup_sort`) over `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axiomatized callees: the deduplicate-and-sort behaviour is the operation
# under specification and is modelled deeply, not behind an axiom.)
# axioms-end


# pure-start
@Pure
def ins(x: int, s: PSeq[int]) -> PSeq[int]:
    """Insert `x` into `s` just before the first element that is not below it,
    dropping `x` if it already occurs there. On a strictly-sorted `s` this is
    ordered-set insertion. Total (no quantified precondition) and front-
    recursive over `s` (one unfold per element)."""
    if len(s) == 0:
        return PSeq(x)
    if x < s[0]:
        return PSeq(x) + s
    if x == s[0]:
        return s
    return PSeq(s[0]) + ins(x, s.drop(1))


@Pure
def dedup_sort(s: PSeq[int]) -> PSeq[int]:
    """The ordered set of `s`: deduplicated and strictly ascending. Built by
    inserting the last element into the ordered set of the prefix, so the
    enumeration loop (which appends one recorded position at a time) tracks it
    with the invariant `result == dedup_sort(prefix)`."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return ins(s[len(s) - 1], dedup_sort(s.take(len(s) - 1)))
# pure-end


def insert_sorted(xs: List[int], key: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the impl computes exactly the pure ordered-set insertion.
    Ensures(ToSeq(Result()) == ins(key, ToSeq(xs)))
    # post-conditions-end
    # impl-start
    # Scan front-to-back, emitting each element until the slot for `key` is
    # found. The loop invariant peels `ins` one element at a time off the unseen
    # suffix `drop(j)` (matching `ins`'s own front recursion), so no auxiliary
    # sequence lemma is needed: the full answer always equals what has been
    # emitted, followed by the insertion into the remaining suffix.
    out = []  # type: List[int]
    j = 0
    placed = False  # type: bool
    while j < len(xs):
        # invariants-start
        Invariant(Acc(list_pred(xs), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(xs))
        # not yet placed: the answer is `out` followed by `ins` of the suffix.
        Invariant(Implies(not placed,
                          ins(key, ToSeq(xs)) == ToSeq(out) + ins(key, ToSeq(xs).drop(j))))
        # placed: the answer is `out` followed by the suffix copied verbatim.
        Invariant(Implies(placed,
                          ins(key, ToSeq(xs)) == ToSeq(out) + ToSeq(xs).drop(j)))
        # invariants-end
        cur = xs[j]
        # `ins`/`drop` unfold once on the suffix whose head is `cur`.
        Assert(ToSeq(xs).drop(j) == PSeq(cur) + ToSeq(xs).drop(j + 1))
        Assert(len(ToSeq(xs).drop(j)) > 0 and ToSeq(xs).drop(j)[0] == cur)
        if placed:
            out = out + [cur]
        elif cur < key:
            out = out + [cur]
        elif cur > key:
            # `ins(key, suffix) == [key] + suffix`; emit `key` then `cur`.
            out = out + [key]
            out = out + [cur]
            placed = True
        else:
            # `cur == key`: `ins(key, suffix) == suffix`; `key` already present.
            out = out + [cur]
            placed = True
        j = j + 1
    Assert(ToSeq(xs).drop(j) == ToSeq(xs).drop(len(xs)))
    Assert(ToSeq(xs).drop(len(xs)) == PSeq(0).take(0))
    if not placed:
        # the suffix is empty: `ins(key, [])== [key]`.
        out = out + [key]
    return out
    # impl-end


def canonical_positions(recorded: List[int]) -> List[int]:
    # pre-conditions-start
    # The recorded-positions list is read-only here (enumeration never mutates
    # it); fractional permission, required and ensured, so no caller can satisfy
    # a postcondition vacuously by overwriting the input.
    Requires(Acc(list_pred(recorded), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(recorded), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reported list is exactly the ordered set of the recorded positions:
    # the deduplicated, strictly ascending arrangement of exactly what was
    # recorded.
    Ensures(ToSeq(Result()) == dedup_sort(ToSeq(recorded)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(recorded):
        # invariants-start
        Invariant(Acc(list_pred(recorded), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(recorded))
        Invariant(ToSeq(result) == dedup_sort(ToSeq(recorded).take(i)))
        # invariants-end
        key = recorded[i]
        Assert(ToSeq(recorded).take(i + 1) == ToSeq(recorded).take(i) + PSeq(key))
        Assert(ToSeq(recorded).take(i + 1)[i] == key)
        Assert(ToSeq(recorded).take(i + 1).take(i) == ToSeq(recorded).take(i))
        result = insert_sorted(result, key)
        i = i + 1
    Assert(ToSeq(recorded).take(len(recorded)) == ToSeq(recorded))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sphinx-doc__sphinx-10466 (nagini). project root, env python, SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE: canonical_positions has a TOTAL precondition (Acc(list_pred,1/2) only) and an output-pinning postcondition ToSeq(Result())==dedup_sort(ToSeq(recorded)) with FRESH Acc(list_pred(Result())). dedup_sort/ins are DEEPLY modeled (@Pure); the axioms region is empty (no consumed axiom). Because the postcondition is total and the result permission is fresh, the ONLY way a functionally-wrong impl could verify is vacuously via non-termination; Assume/Refute are banned tokens. This is a tight, functionally-pinning spec.

8 same-spec attacks (adversary same-spec: all SAME) + positive control. weakness runs (adversary weakness nagini sphinx-doc__sphinx-10466 <file>) executed concurrently in 3 batches of <=3 JVM jobs:
- atk_prepatch (prepatch bug, verbatim projection no dedup/sort): NOT-A-COUNTEREXAMPLE, exit2 (rejected) -> prepatch reproduced.
- atk_infloop (while True, ungrounded-oracle/vacuous attempt): rejected.
- atk_infloop2 (while i<=len(recorded), i+=0, non-termination): rejected.
- atk_empty (partial-domain / return []): rejected.
- atk_droplast (boundary off-by-one, loop to len-1): rejected.
- atk_dropfirst (control-flow-effect, start i=1 skipping first): rejected.
- atk_dupe (dedup violation, append each key twice): rejected.
- atk_echo (functionally-correct echo, only added Assert(True)): CANDIDATE-COUNTEREXAMPLE, exit0 (shares spec AND verifies, ~ verify time recorded).
- pos_control (model.py verbatim): nagini_verify.sh -> Verification successful, 18.03s.

MANDATORY RESOLVE ON EVERY VERIFYING CANDIDATE: atk_echo is behaviorally identical to gold (computes exactly dedup_sort == sorted(set(...))), so its faithful refined patch IS the gold hunk. Materialized to atk_echo.patch and EXECUTED through the official harness via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-10466', patch, timeout=3600): RESOLVED=True, COMPLETED=True, ATTEMPTS=1, FLAKY=False, note='resolved'. So the one verifying candidate's patch RESOLVES -> no verify-not-correct gap.

A-LEG / refinement.md audit: every leg is R / A-reference / I; NO kind-3 and NO consumed axiom.
- A1 (recorded:List[int] <-> projected (source,line) tuples): R, tuple<->int order/equality-preserving bijection; validated by axiom_check.py check 2 (F2P + 20000 fuzz position lists) and conformance_check.py type bridge.
- A2 (result == dedup_sort <-> sorted(set(...))): A-reference. Deep model validated == real operation by G-AX. Ran axiom_check.py: exit0, 'dedup_sort deep model == sorted(set(...)) over 8 boundary + 20000 integer fuzz; integer-key abstraction faithful over 1 F2P + 20000 fuzz'. Independent cross-check (my own dedup_sort reimpl vs sorted(set), 50000 random lists) bad=0. Correspondence holds.
- A3 (Result() <-> positions -> Message(message,positions,uuids)): R/I; Message.__init__ stores locations=positions, F2P reads .locations. Holds.
- Section B (insert_sorted/canonical_positions <-> deep model): I; loops compute the pure functions by their loop invariants (result==dedup_sort(take(i))).
- Section C: confirmed no kind-3 step; the single changed op (compose projection with dedup+sort) is modeled deeply (A-reference), not hidden behind an axiom.
Model<->patch correspondence: gold replaces the verbatim projection with sorted(set(...)) at gettext.py:60-61; canonical_positions postcondition pins exactly dedup_sort, matching. Sound.

VERDICT: SOUND. >=5 distinct wrong-impl classes (partial-domain, boundary, control-flow-effect, non-termination x2, dedup-violation, ungrounded-oracle/vacuous, prepatch) all REJECTED by the spec; the only verifying same-spec impl is a correct echo whose materialized faithful patch RESOLVED under the official harness. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo) confirmed. Spec postcondition: ToSeq(Result()) == dedup_sort(ToSeq(recorded)) for canonical_positions, plus ToSeq(Result())==ins(key,ToSeq(xs)) for insert_sorted. Real callee: worktree at base_commit cab2d93 has `positions = [(source, line) for source, line, uuid in self.metadata[message]]` (gettext.py:60), gold patch replaces with `sorted(set)`; current tree shows `sorted(set(map(operator.itemgetter, msg_metadata)))` — same dedup+strict-ascending semantics. dedup_sort computes exactly the deduplicated, strictly-ascending arrangement = sorted(set). Evidence: (1) bundle axiom_check.py exit 0 (8 boundary + 20000 int fuzz + F2P + 20000 tuple-abstraction inputs). Independent fuzz (my fb10466_indep.py, seed 999): 200k integer-key lists AND 100k random (source,line) tuple lists over a small alphabet (frequent dups/collisions) — dedup_sort == sorted(set) on every input, zero disagreements. (3) Tuple->int key abstraction is order- and equality-preserving; sorted/set observe only < and ==, so the integer carrier is observationally exact — no drift. (4) model.py verifies (nagini_verify exit 0, 17.9s); model_prepatch (scan-order projection, no dedup/sort) FAILS the postcondition, so the spec genuinely senses the change (not vacuous, not too weak). The spec equals the real operation exactly — neither over- nor under-constrained. No diverging input exists; spec is FAITHFUL to real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view confirmed byte-identical to meta.json region_hashes.spec_view (recomputed sha256 = fc1edf4406ac14e31627e65f1b10d8c64c614cf74ae959921bc99f7d5c367e7e via swebench_unified.markers.spec_view over model.py; impl regions elided). markers.py confirms spec_view is derived from model.py ALONE — mapping.md/refinement.md are audit docs, NOT part of the spec view.

Spec view discloses desired behaviour only: reported position list = ordered set of recorded positions (each distinct position once, strictly ascending), modelled abstractly over opaque integer keys / PSeq[int] via pure dedup_sort; postcondition ToSeq(Result()) == dedup_sort(ToSeq(recorded)).

The PUBLIC problem_statement already discloses the deduplicate requirement (title 'Message.locations duplicate unnecessary'; reporter's own proposed fix loc_set = set(locations); return list(loc_set); 'NO duplications of other locations'; names sphinx/builders/gettext.py). So the core of the gold edit (dedup) is public.

The spec view contains NO repo-identifying leak: never names Catalog.__iter__/Message/.locations, never writes the gold expression sorted(set((source, line) for ...)), never cites gettext.py:60, abstracts positions to integer keys. The verbatim gold expression and repo bindings live only in mapping.md/refinement.md (out of spec view). The strict-ascending/sort aspect is the tested F2P behaviour (test_Catalog_duplicated_message expects the position once, sorted) — legitimate behavioural specification, not gold-edit reconstruction. The lone '(mapping.md)' docstring reference is a pointer to an audit doc, not gold content. No spec-view line reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
