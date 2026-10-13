# P2 adversarial audit — sphinx-doc__sphinx-7748

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
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,13 +91,6 @@
     Requires(Acc(list_pred(val), 1 / 2))
     Requires(len(cont) == len(val))
     Requires(len(cont) > 0)
-    # The gathering must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(cont), 1 / 2))
@@ -116,54 +108,6 @@
     Ensures(len(val) > 0 and len(Result()) >= 1 and Result()[0] == val[0])
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    n = len(cont)
-    i = 0
-    while True:
-        # invariants-start
-        Invariant(Acc(list_pred(cont), 1 / 2))
-        Invariant(Acc(list_pred(val), 1 / 2))
-        Invariant(len(cont) == len(val))
-        Invariant(n == len(cont))
-        Invariant(0 <= i and i < n)
-        Invariant(Acc(list_pred(result)))
-        # telescoping fold: what is already collected, concatenated with the
-        # collected run of the remaining suffix, is the whole collected run.
-        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-                  collected(ToSeq(cont), ToSeq(val)))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` no later than the line
-        # index i reaching the last line n - 1, and i rises by exactly one per
-        # pass, so at most n - i + 1 passes remain. It strictly decreases because
-        # only i changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(cont))), and it stays >= 2 because the invariant
-        # Invariant(0 <= i and i < n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0).
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        c = cont[i]
-        v = val[i]
-        # peel the head of the suffix drop(i): head is line i, tail is drop(i+1).
-        Assert(ToSeq(cont).drop(i)[0] == c)
-        Assert(ToSeq(val).drop(i)[0] == v)
-        result = result + [v]
-        if c == 0 or i == n - 1:
-            # the run ends here — either this line terminates it (not open) or
-            # it is the last line of the block (no further line to spill onto).
-            # One unfold of collected on drop(i): when the line is not open the
-            # suffix is PSeq(v); when it is the last line the tail drop(i+1) is
-            # empty so collected of it is empty, again leaving PSeq(v). Either
-            # way the suffix contributes exactly this value.
-            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(v))
-            break
-        # open line that is not the last: one unfold of collected on drop(i)
-        # peels PSeq(v) and recurses on drop(i+1).
-        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-               PSeq(v) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))
-        i = i + 1
+    result = [val[0]]  # type: List[int]
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,13 +91,6 @@
     Requires(Acc(list_pred(val), 1 / 2))
     Requires(len(cont) == len(val))
     Requires(len(cont) > 0)
-    # The gathering must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(cont), 1 / 2))
@@ -119,51 +111,14 @@
     result = []  # type: List[int]
     n = len(cont)
     i = 0
-    while True:
-        # invariants-start
+    while i < n:
         Invariant(Acc(list_pred(cont), 1 / 2))
         Invariant(Acc(list_pred(val), 1 / 2))
         Invariant(len(cont) == len(val))
         Invariant(n == len(cont))
-        Invariant(0 <= i and i < n)
+        Invariant(0 <= i and i <= n)
         Invariant(Acc(list_pred(result)))
-        # telescoping fold: what is already collected, concatenated with the
-        # collected run of the remaining suffix, is the whole collected run.
-        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-                  collected(ToSeq(cont), ToSeq(val)))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` no later than the line
-        # index i reaching the last line n - 1, and i rises by exactly one per
-        # pass, so at most n - i + 1 passes remain. It strictly decreases because
-        # only i changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(cont))), and it stays >= 2 because the invariant
-        # Invariant(0 <= i and i < n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0).
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        c = cont[i]
-        v = val[i]
-        # peel the head of the suffix drop(i): head is line i, tail is drop(i+1).
-        Assert(ToSeq(cont).drop(i)[0] == c)
-        Assert(ToSeq(val).drop(i)[0] == v)
-        result = result + [v]
-        if c == 0 or i == n - 1:
-            # the run ends here — either this line terminates it (not open) or
-            # it is the last line of the block (no further line to spill onto).
-            # One unfold of collected on drop(i): when the line is not open the
-            # suffix is PSeq(v); when it is the last line the tail drop(i+1) is
-            # empty so collected of it is empty, again leaving PSeq(v). Either
-            # way the suffix contributes exactly this value.
-            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(v))
-            break
-        # open line that is not the last: one unfold of collected on drop(i)
-        # peels PSeq(v) and recurses on drop(i+1).
-        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-               PSeq(v) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))
+        result = result + [val[i]]
         i = i + 1
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,13 +91,6 @@
     Requires(Acc(list_pred(val), 1 / 2))
     Requires(len(cont) == len(val))
     Requires(len(cont) > 0)
-    # The gathering must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(cont), 1 / 2))
@@ -120,50 +112,17 @@
     n = len(cont)
     i = 0
     while True:
-        # invariants-start
         Invariant(Acc(list_pred(cont), 1 / 2))
         Invariant(Acc(list_pred(val), 1 / 2))
         Invariant(len(cont) == len(val))
         Invariant(n == len(cont))
         Invariant(0 <= i and i < n)
         Invariant(Acc(list_pred(result)))
-        # telescoping fold: what is already collected, concatenated with the
-        # collected run of the remaining suffix, is the whole collected run.
-        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-                  collected(ToSeq(cont), ToSeq(val)))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` no later than the line
-        # index i reaching the last line n - 1, and i rises by exactly one per
-        # pass, so at most n - i + 1 passes remain. It strictly decreases because
-        # only i changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(cont))), and it stays >= 2 because the invariant
-        # Invariant(0 <= i and i < n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0).
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         c = cont[i]
         v = val[i]
-        # peel the head of the suffix drop(i): head is line i, tail is drop(i+1).
-        Assert(ToSeq(cont).drop(i)[0] == c)
-        Assert(ToSeq(val).drop(i)[0] == v)
-        result = result + [v]
+        result = [v] + result
         if c == 0 or i == n - 1:
-            # the run ends here — either this line terminates it (not open) or
-            # it is the last line of the block (no further line to spill onto).
-            # One unfold of collected on drop(i): when the line is not open the
-            # suffix is PSeq(v); when it is the last line the tail drop(i+1) is
-            # empty so collected of it is empty, again leaving PSeq(v). Either
-            # way the suffix contributes exactly this value.
-            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(v))
             break
-        # open line that is not the last: one unfold of collected on drop(i)
-        # peels PSeq(v) and recurses on drop(i+1).
-        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-               PSeq(v) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))
         i = i + 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,13 +91,6 @@
     Requires(Acc(list_pred(val), 1 / 2))
     Requires(len(cont) == len(val))
     Requires(len(cont) > 0)
-    # The gathering must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(cont), 1 / 2))
@@ -120,50 +112,17 @@
     n = len(cont)
     i = 0
     while True:
-        # invariants-start
         Invariant(Acc(list_pred(cont), 1 / 2))
         Invariant(Acc(list_pred(val), 1 / 2))
         Invariant(len(cont) == len(val))
         Invariant(n == len(cont))
         Invariant(0 <= i and i < n)
         Invariant(Acc(list_pred(result)))
-        # telescoping fold: what is already collected, concatenated with the
-        # collected run of the remaining suffix, is the whole collected run.
-        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-                  collected(ToSeq(cont), ToSeq(val)))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` no later than the line
-        # index i reaching the last line n - 1, and i rises by exactly one per
-        # pass, so at most n - i + 1 passes remain. It strictly decreases because
-        # only i changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(cont))), and it stays >= 2 because the invariant
-        # Invariant(0 <= i and i < n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0).
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         c = cont[i]
         v = val[i]
-        # peel the head of the suffix drop(i): head is line i, tail is drop(i+1).
-        Assert(ToSeq(cont).drop(i)[0] == c)
-        Assert(ToSeq(val).drop(i)[0] == v)
+        if c == 0 or i == n - 1:
+            break
         result = result + [v]
-        if c == 0 or i == n - 1:
-            # the run ends here — either this line terminates it (not open) or
-            # it is the last line of the block (no further line to spill onto).
-            # One unfold of collected on drop(i): when the line is not open the
-            # suffix is PSeq(v); when it is the last line the tail drop(i+1) is
-            # empty so collected of it is empty, again leaving PSeq(v). Either
-            # way the suffix contributes exactly this value.
-            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(v))
-            break
-        # open line that is not the last: one unfold of collected on drop(i)
-        # peels PSeq(v) and recurses on drop(i+1).
-        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-               PSeq(v) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))
         i = i + 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,13 +91,6 @@
     Requires(Acc(list_pred(val), 1 / 2))
     Requires(len(cont) == len(val))
     Requires(len(cont) > 0)
-    # The gathering must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(cont), 1 / 2))
@@ -116,54 +108,21 @@
     Ensures(len(val) > 0 and len(Result()) >= 1 and Result()[0] == val[0])
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
+    result = [val[0]]  # type: List[int]
     n = len(cont)
     i = 0
     while True:
-        # invariants-start
         Invariant(Acc(list_pred(cont), 1 / 2))
         Invariant(Acc(list_pred(val), 1 / 2))
         Invariant(len(cont) == len(val))
         Invariant(n == len(cont))
         Invariant(0 <= i and i < n)
         Invariant(Acc(list_pred(result)))
-        # telescoping fold: what is already collected, concatenated with the
-        # collected run of the remaining suffix, is the whole collected run.
-        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-                  collected(ToSeq(cont), ToSeq(val)))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` no later than the line
-        # index i reaching the last line n - 1, and i rises by exactly one per
-        # pass, so at most n - i + 1 passes remain. It strictly decreases because
-        # only i changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(cont))), and it stays >= 2 because the invariant
-        # Invariant(0 <= i and i < n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0).
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         c = cont[i]
         v = val[i]
-        # peel the head of the suffix drop(i): head is line i, tail is drop(i+1).
-        Assert(ToSeq(cont).drop(i)[0] == c)
-        Assert(ToSeq(val).drop(i)[0] == v)
         result = result + [v]
         if c == 0 or i == n - 1:
-            # the run ends here — either this line terminates it (not open) or
-            # it is the last line of the block (no further line to spill onto).
-            # One unfold of collected on drop(i): when the line is not open the
-            # suffix is PSeq(v); when it is the last line the tail drop(i+1) is
-            # empty so collected of it is empty, again leaving PSeq(v). Either
-            # way the suffix contributes exactly this value.
-            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(v))
             break
-        # open line that is not the last: one unfold of collected on drop(i)
-        # peels PSeq(v) and recurses on drop(i+1).
-        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-               PSeq(v) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))
         i = i + 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,13 +91,6 @@
     Requires(Acc(list_pred(val), 1 / 2))
     Requires(len(cont) == len(val))
     Requires(len(cont) > 0)
-    # The gathering must COMPLETE (total correctness): without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 2 leaves room for the list allocation it performs (at level
-    # 1 the allocation's own obligation has nowhere below the caller to go); it
-    # calls no other obligated method.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(cont), 1 / 2))
@@ -120,50 +112,17 @@
     n = len(cont)
     i = 0
     while True:
-        # invariants-start
         Invariant(Acc(list_pred(cont), 1 / 2))
         Invariant(Acc(list_pred(val), 1 / 2))
         Invariant(len(cont) == len(val))
         Invariant(n == len(cont))
         Invariant(0 <= i and i < n)
         Invariant(Acc(list_pred(result)))
-        # telescoping fold: what is already collected, concatenated with the
-        # collected run of the remaining suffix, is the whole collected run.
-        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-                  collected(ToSeq(cont), ToSeq(val)))
-        # The condition is the constant `True`, so the bound comes from what the
-        # break counts down: the loop leaves via `break` no later than the line
-        # index i reaching the last line n - 1, and i rises by exactly one per
-        # pass, so at most n - i + 1 passes remain. It strictly decreases because
-        # only i changes (n is a local fixed before the loop, pinned by
-        # Invariant(n == len(cont))), and it stays >= 2 because the invariant
-        # Invariant(0 <= i and i < n) holds on entry to every pass (so it never
-        # reaches the unsatisfiable 0).
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         c = cont[i]
         v = val[i]
-        # peel the head of the suffix drop(i): head is line i, tail is drop(i+1).
-        Assert(ToSeq(cont).drop(i)[0] == c)
-        Assert(ToSeq(val).drop(i)[0] == v)
         result = result + [v]
-        if c == 0 or i == n - 1:
-            # the run ends here — either this line terminates it (not open) or
-            # it is the last line of the block (no further line to spill onto).
-            # One unfold of collected on drop(i): when the line is not open the
-            # suffix is PSeq(v); when it is the last line the tail drop(i+1) is
-            # empty so collected of it is empty, again leaving PSeq(v). Either
-            # way the suffix contributes exactly this value.
-            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(v))
+        if c == 0:
             break
-        # open line that is not the last: one unfold of collected on drop(i)
-        # peels PSeq(v) and recurses on drop(i+1).
-        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
-        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
-        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
-               PSeq(v) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))
         i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7748.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documented object may carry, at the top of its documentation block, one or
  more candidate signature lines. The lines form a carry-over run: a line is
  marked as *open* when it ends with a trailing line-spillover marker, meaning
  the signature description carries over to the following line; a line that is
  not so marked *terminates* the run. Each line, once stripped of any spillover
  marker, is parsed into a signature value.

  The behaviour pinned here is how MANY of these candidate signatures are
  gathered: the gatherer collects the values of every line from the top of the
  block up to and including the FIRST terminating (non-open) line. In
  particular:

    * a run whose only line terminates immediately yields exactly that one
      signature;
    * a run whose leading lines are each open yields ALL of them together with
      the first terminating line that follows — never just the first.

  The rendered result is the ordered sequence of those collected signature
  values, in source order. The discriminating case is a run of length >= 2 in
  which the leading line is open: the result must contain every collected
  signature, not merely the leading one.

A documentation block is modelled as two equal-length parallel ``List[int]``
streams aligned to line order: a per-line *carry-over flag* (non-zero iff the
line spills over onto the next) and a per-line *signature value* (an opaque
integer token standing for the parsed ``(args) -> return`` description of that
line). The collected sequence is carried by the pure sequence theory
``PSeq[int]`` as a front-recursive run. No callee is axiomatized: the gathering
is structural logic over the abstract per-line flags and values, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms: the gathering of candidate signatures is structural
#  logic over the abstract per-line carry-over flags and signature values,
#  spelled out in full. There is no unchanged opaque callee whose contract the
#  proof consumes.)
# axioms-end


# pure-start
@Pure
def run_len(cont: PSeq[int]) -> int:
    """Number of lines collected from the top of the block: every leading
    open line plus the first terminating line. A line is *open* iff its flag is
    non-zero. Front-recursive so a single unfold is available per loop step.
    The empty block collects nothing."""
    Ensures(Implies(len(cont) > 0, Result() >= 1 and Result() <= len(cont)))
    Ensures(Implies(len(cont) == 0, Result() == 0))
    if len(cont) == 0:
        return 0
    if cont[0] != 0:
        return 1 + run_len(cont.drop(1))
    return 1


@Pure
def collected(cont: PSeq[int], val: PSeq[int]) -> PSeq[int]:
    """The ordered sequence of collected signature values: the value of every
    line from the top up to and including the first terminating line. While the
    leading line is open, prepend its value and recurse; the first terminating
    line contributes its value and stops the run. Front-recursive (one unfold
    per line) so the forward impl loop can discharge it."""
    Ensures(Implies(len(cont) <= len(val), len(Result()) == run_len(cont)))
    if len(cont) == 0 or len(val) == 0:
        return PSeq(0).take(0)
    if cont[0] != 0:
        return PSeq(val[0]) + collected(cont.drop(1), val.drop(1))
    return PSeq(val[0])
# pure-end


def gather_signatures(cont: List[int], val: List[int]) -> List[int]:
    # pre-conditions-start
    # The two parallel per-line streams of the documentation block: ``cont`` is
    # the carry-over flag of each candidate signature line, ``val`` the parsed
    # signature value of each. Both are read-only (the gatherer mutates neither)
    # and so are required AND ensured at fractional permission (directive 5).
    # The streams are aligned line-for-line, and the block is non-empty (there
    # is at least one candidate signature line to gather).
    Requires(Acc(list_pred(cont), 1 / 2))
    Requires(Acc(list_pred(val), 1 / 2))
    Requires(len(cont) == len(val))
    Requires(len(cont) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(cont), 1 / 2))
    Ensures(Acc(list_pred(val), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the collected run: the values of every line from the
    # top up to and including the first terminating line. This pins the
    # discriminating behaviour — when leading lines are open, ALL their
    # signatures are present, not only the first.
    Ensures(ToSeq(Result()) == collected(ToSeq(cont), ToSeq(val)))
    # The number of collected signatures is exactly the run length, so a run of
    # length >= 2 (an open leading line) yields more than one signature.
    Ensures(len(Result()) == run_len(ToSeq(cont)))
    # The leading signature is always the first collected value.
    Ensures(len(val) > 0 and len(Result()) >= 1 and Result()[0] == val[0])
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    n = len(cont)
    i = 0
    while True:
        # invariants-start
        Invariant(Acc(list_pred(cont), 1 / 2))
        Invariant(Acc(list_pred(val), 1 / 2))
        Invariant(len(cont) == len(val))
        Invariant(n == len(cont))
        Invariant(0 <= i and i < n)
        Invariant(Acc(list_pred(result)))
        # telescoping fold: what is already collected, concatenated with the
        # collected run of the remaining suffix, is the whole collected run.
        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
                  collected(ToSeq(cont), ToSeq(val)))
        # invariants-end
        c = cont[i]
        v = val[i]
        # peel the head of the suffix drop(i): head is line i, tail is drop(i+1).
        Assert(ToSeq(cont).drop(i)[0] == c)
        Assert(ToSeq(val).drop(i)[0] == v)
        result = result + [v]
        if c == 0 or i == n - 1:
            # the run ends here — either this line terminates it (not open) or
            # it is the last line of the block (no further line to spill onto).
            # One unfold of collected on drop(i): when the line is not open the
            # suffix is PSeq(v); when it is the last line the tail drop(i+1) is
            # empty so collected of it is empty, again leaving PSeq(v). Either
            # way the suffix contributes exactly this value.
            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(v))
            break
        # open line that is not the last: one unfold of collected on drop(i)
        # peels PSeq(v) and recurses on drop(i+1).
        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
               PSeq(v) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sphinx-doc__sphinx-7748 (nagini). VERDICT: SOUND — no verifying wrong impl found, so no resolve run was required.

SPEC SHAPE: gather_signatures(cont, val) fully PINS its output over the entire admissible domain (Requires: Acc list_pred at 1/2, len(cont)==len(val), len>0). Postconditions: ToSeq(Result())==collected(ToSeq(cont),ToSeq(val)) AND len(Result())==run_len(ToSeq(cont)) AND Result()[0]==val[0]. Because the output is pinned to the deep folds for ALL inputs (not a partial/weak spec), any deviating impl must fail verification. No @ContractOnly axioms exist (A-consumed count = 0); the only A leg is A2, an A-REFERENCE deep model (run_len/collected + the verified loop).

ATTACKS (6 distinct same-spec wrong impls; all confirmed SAME by `adversary same-spec`; env, SBU_BENCHMARK_DIR=.../benchmark-verified, PY=python, cmd `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-7748 <atk>`; run concurrently <=3 at a time):
- atk_1.py PREPATCH BUG (singleton result=[val[0]]): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). `adversary verify` gives the exact reason: 'Postcondition ... Assertion (ToSeq(Result()) == collected(ToSeq(cont), ToSeq(val))) might not hold' at line 103.
- atk_2.py CONTROL-FLOW-EFFECT (echo ALL lines, ignore carry-over marker): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Overcounts on runs that terminate early.
- atk_3.py ORDER (prepend v -> reversed collected): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Right length/multiset, wrong order — caught by the ToSeq equality + Result()[0]==val[0].
- atk_4.py BOUNDARY (break before appending terminating line -> excludes last value): NOT-A-COUNTEREXAMPLE, does not verify (exit 2).
- atk_5.py PARTIAL-DOMAIN/DUP (seed result=[val[0]] then also append in loop -> duplicates first value): NOT-A-COUNTEREXAMPLE, does not verify (exit 2).
- atk_6.py CONTROL-FLOW (drop the i==n-1 end-of-block guard, stop only on c==0): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). On an all-open block this over-runs / mismatches collected.

POSITIVE CONTROL: positive_control.py (verbatim bundle model.py) VERIFIES — `bash scripts/nagini_verify.sh` => 'Verification successful', 20.66s, exit 0. Infra is healthy, so the six 'does not verify' results are genuine spec rejections, not spurious verifier failures. No verify timeouts (verify_completed on all).

Since zero attacks came back CANDIDATE (spec+verifies), the mandatory materialize-faithful-patch-and-run_resolve step had no triggers; no resolve run was needed and none is missing.

A-LEG / MODEL<->PATCH AUDIT (refinement.md):
- No consumed axioms (axioms region is a comment block only). Sole non-R/I leg is A2 = A-REFERENCE deep model run_len/collected.
- G-AX (axiom_check.py) RUN: 'G-AX OK ... on 20126 clean-run cases (exhaustive lengths 1..6 x all continuation patterns + 20000 fuzz) + F2P E (2 sigs) + D (1 sig)', exit 0. It reimplements the REAL post-patch _find_signature loop + format_signature join with the verbatim py_ext_sig_re and asserts model count AND per-line order == real gather. Correspondence holds.
- Independent corroboration in meta.json faithfulness note: gold-patch loop transcribed directly, exhaustive lengths 1..10 x all 2^n masks (2046 cases), 0 count/order mismatches.
- Every refinement.md leg is R / A-reference / I; NO kind-3 (unexpressible-changed-op) leg. The one genuinely-changed op (gather all continued signatures) is modeled deeply (A2), not hidden behind an axiom about the function under change. B1 (get_doc refactor) = I; B2 (SingledispatchFunctionDocumenter objpath guard) = out-of-modeled-domain guard; neither affects the pinned count/order.

CONCLUSION: verify(model) => output == collected == real gather (G-AX) => renders same ordered signature sequence as post-patch code on tested inputs => resolves. The spec admits no incorrect verifying impl across 6 diverse attacks. SOUND.

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
"""Twin-artifact model for sphinx-doc__sphinx-7748.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documented object may carry, at the top of its documentation block, one or
  more candidate signature lines. The lines form a carry-over run: a line is
  marked as *open* when it ends with a trailing line-spillover marker, meaning
  the signature description carries over to the following line; a line that is
  not so marked *terminates* the run. Each line, once stripped of any spillover
  marker, is parsed into a signature value.

  The behaviour pinned here is how MANY of these candidate signatures are
  gathered: the gatherer collects the values of every line from the top of the
  block up to and including the FIRST terminating (non-open) line. In
  particular:

    * a run whose only line terminates immediately yields exactly that one
      signature;
    * a run whose leading lines are each open yields ALL of them together with
      the first terminating line that follows — never just the first.

  The rendered result is the ordered sequence of those collected signature
  values, in source order. The discriminating case is a run of length >= 2 in
  which the leading line is open: the result must contain every collected
  signature, not merely the leading one.

A documentation block is modelled as two equal-length parallel ``List[int]``
streams aligned to line order: a per-line *carry-over flag* (non-zero iff the
line spills over onto the next) and a per-line *signature value* (an opaque
integer token standing for the parsed ``(args) -> return`` description of that
line). The collected sequence is carried by the pure sequence theory
``PSeq[int]`` as a front-recursive run. No callee is axiomatized: the gathering
is structural logic over the abstract per-line flags and values, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms: the gathering of candidate signatures is structural
#  logic over the abstract per-line carry-over flags and signature values,
#  spelled out in full. There is no unchanged opaque callee whose contract the
#  proof consumes.)
# axioms-end


# pure-start
@Pure
def run_len(cont: PSeq[int]) -> int:
    """Number of lines collected from the top of the block: every leading
    open line plus the first terminating line. A line is *open* iff its flag is
    non-zero. Front-recursive so a single unfold is available per loop step.
    The empty block collects nothing."""
    Ensures(Implies(len(cont) > 0, Result() >= 1 and Result() <= len(cont)))
    Ensures(Implies(len(cont) == 0, Result() == 0))
    if len(cont) == 0:
        return 0
    if cont[0] != 0:
        return 1 + run_len(cont.drop(1))
    return 1


@Pure
def collected(cont: PSeq[int], val: PSeq[int]) -> PSeq[int]:
    """The ordered sequence of collected signature values: the value of every
    line from the top up to and including the first terminating line. While the
    leading line is open, prepend its value and recurse; the first terminating
    line contributes its value and stops the run. Front-recursive (one unfold
    per line) so the forward impl loop can discharge it."""
    Ensures(Implies(len(cont) <= len(val), len(Result()) == run_len(cont)))
    if len(cont) == 0 or len(val) == 0:
        return PSeq(0).take(0)
    if cont[0] != 0:
        return PSeq(val[0]) + collected(cont.drop(1), val.drop(1))
    return PSeq(val[0])
# pure-end


def gather_signatures(cont: List[int], val: List[int]) -> List[int]:
    # pre-conditions-start
    # The two parallel per-line streams of the documentation block: ``cont`` is
    # the carry-over flag of each candidate signature line, ``val`` the parsed
    # signature value of each. Both are read-only (the gatherer mutates neither)
    # and so are required AND ensured at fractional permission (directive 5).
    # The streams are aligned line-for-line, and the block is non-empty (there
    # is at least one candidate signature line to gather).
    Requires(Acc(list_pred(cont), 1 / 2))
    Requires(Acc(list_pred(val), 1 / 2))
    Requires(len(cont) == len(val))
    Requires(len(cont) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(cont), 1 / 2))
    Ensures(Acc(list_pred(val), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the collected run: the values of every line from the
    # top up to and including the first terminating line. This pins the
    # discriminating behaviour — when leading lines are open, ALL their
    # signatures are present, not only the first.
    Ensures(ToSeq(Result()) == collected(ToSeq(cont), ToSeq(val)))
    # The number of collected signatures is exactly the run length, so a run of
    # length >= 2 (an open leading line) yields more than one signature.
    Ensures(len(Result()) == run_len(ToSeq(cont)))
    # The leading signature is always the first collected value.
    Ensures(len(val) > 0 and len(Result()) >= 1 and Result()[0] == val[0])
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    n = len(cont)
    i = 0
    while True:
        # invariants-start
        Invariant(Acc(list_pred(cont), 1 / 2))
        Invariant(Acc(list_pred(val), 1 / 2))
        Invariant(len(cont) == len(val))
        Invariant(n == len(cont))
        Invariant(0 <= i and i < n)
        Invariant(Acc(list_pred(result)))
        # telescoping fold: what is already collected, concatenated with the
        # collected run of the remaining suffix, is the whole collected run.
        Invariant(ToSeq(result) + collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
                  collected(ToSeq(cont), ToSeq(val)))
        # invariants-end
        c = cont[i]
        v = val[i]
        # peel the head of the suffix drop(i): head is line i, tail is drop(i+1).
        Assert(ToSeq(cont).drop(i)[0] == c)
        Assert(ToSeq(val).drop(i)[0] == v)
        result = result + [v]
        if c == 0 or i == n - 1:
            # the run ends here — either this line terminates it (not open) or
            # it is the last line of the block (no further line to spill onto).
            # One unfold of collected on drop(i): when the line is not open the
            # suffix is PSeq(v); when it is the last line the tail drop(i+1) is
            # empty so collected of it is empty, again leaving PSeq(v). Either
            # way the suffix contributes exactly this value.
            Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
            Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
            Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) == PSeq(v))
            break
        # open line that is not the last: one unfold of collected on drop(i)
        # peels PSeq(v) and recurses on drop(i+1).
        Assert(ToSeq(cont).drop(i).drop(1) == ToSeq(cont).drop(i + 1))
        Assert(ToSeq(val).drop(i).drop(1) == ToSeq(val).drop(i + 1))
        Assert(collected(ToSeq(cont).drop(i), ToSeq(val).drop(i)) ==
               PSeq(v) + collected(ToSeq(cont).drop(i + 1), ToSeq(val).drop(i + 1)))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sphinx-doc__sphinx-7748 (nagini). VERDICT: SOUND — no verifying wrong impl found, so no resolve run was required.

SPEC SHAPE: gather_signatures(cont, val) fully PINS its output over the entire admissible domain (Requires: Acc list_pred at 1/2, len(cont)==len(val), len>0). Postconditions: ToSeq(Result())==collected(ToSeq(cont),ToSeq(val)) AND len(Result())==run_len(ToSeq(cont)) AND Result()[0]==val[0]. Because the output is pinned to the deep folds for ALL inputs (not a partial/weak spec), any deviating impl must fail verification. No @ContractOnly axioms exist (A-consumed count = 0); the only A leg is A2, an A-REFERENCE deep model (run_len/collected + the verified loop).

ATTACKS (6 distinct same-spec wrong impls; all confirmed SAME by `adversary same-spec`; env, SBU_BENCHMARK_DIR=.../benchmark-verified, PY=python, cmd `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-7748 <atk>`; run concurrently <=3 at a time):
- atk_1.py PREPATCH BUG (singleton result=[val[0]]): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). `adversary verify` gives the exact reason: 'Postcondition ... Assertion (ToSeq(Result()) == collected(ToSeq(cont), ToSeq(val))) might not hold' at line 103.
- atk_2.py CONTROL-FLOW-EFFECT (echo ALL lines, ignore carry-over marker): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Overcounts on runs that terminate early.
- atk_3.py ORDER (prepend v -> reversed collected): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Right length/multiset, wrong order — caught by the ToSeq equality + Result()[0]==val[0].
- atk_4.py BOUNDARY (break before appending terminating line -> excludes last value): NOT-A-COUNTEREXAMPLE, does not verify (exit 2).
- atk_5.py PARTIAL-DOMAIN/DUP (seed result=[val[0]] then also append in loop -> duplicates first value): NOT-A-COUNTEREXAMPLE, does not verify (exit 2).
- atk_6.py CONTROL-FLOW (drop the i==n-1 end-of-block guard, stop only on c==0): NOT-A-COUNTEREXAMPLE, does not verify (exit 2). On an all-open block this over-runs / mismatches collected.

POSITIVE CONTROL: positive_control.py (verbatim bundle model.py) VERIFIES — `bash scripts/nagini_verify.sh` => 'Verification successful', 20.66s, exit 0. Infra is healthy, so the six 'does not verify' results are genuine spec rejections, not spurious verifier failures. No verify timeouts (verify_completed on all).

Since zero attacks came back CANDIDATE (spec+verifies), the mandatory materialize-faithful-patch-and-run_resolve step had no triggers; no resolve run was needed and none is missing.

A-LEG / MODEL<->PATCH AUDIT (refinement.md):
- No consumed axioms (axioms region is a comment block only). Sole non-R/I leg is A2 = A-REFERENCE deep model run_len/collected.
- G-AX (axiom_check.py) RUN: 'G-AX OK ... on 20126 clean-run cases (exhaustive lengths 1..6 x all continuation patterns + 20000 fuzz) + F2P E (2 sigs) + D (1 sig)', exit 0. It reimplements the REAL post-patch _find_signature loop + format_signature join with the verbatim py_ext_sig_re and asserts model count AND per-line order == real gather. Correspondence holds.
- Independent corroboration in meta.json faithfulness note: gold-patch loop transcribed directly, exhaustive lengths 1..10 x all 2^n masks (2046 cases), 0 count/order mismatches.
- Every refinement.md leg is R / A-reference / I; NO kind-3 (unexpressible-changed-op) leg. The one genuinely-changed op (gather all continued signatures) is modeled deeply (A2), not hidden behind an axiom about the function under change. B1 (get_doc refactor) = I; B2 (SingledispatchFunctionDocumenter objpath guard) = out-of-modeled-domain guard; neither affects the pinned count/order.

CONCLUSION: verify(model) => output == collected == real gather (G-AX) => renders same ordered signature sequence as post-patch code on tested inputs => resolves. The spec admits no incorrect verifying impl across 6 diverse attacks. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attempt FAILED — the spec is faithful (not too strong, no drift over the modeled domain). Independent evidence, all built from scratch (NOT trusting bundle artifacts):

 Rebuilt a CLEAN base_commit (9988d5ce267bf0df4791770b469431b1fb00dcdd) worktree and applied the gold patch.diff verbatim (git apply OK). NOTE: the pre-existing worktree was contaminated with an injected `while True: pass` attack artifact in _find_signature; I did not use it as the oracle.
(2) Nagini verifies model.py (exit 0, 19.3s) via scripts/nagini_verify.sh.
 Bundle conformance_check.py, repointed at my clean, passes: 102048 inputs (2046 exhaustive + 2 fixtures + 100000 fuzz, seed 774801), 0 disagreements.
 My OWN independent differential (mydiff7748.py, distinct seed 999): exhaustive over block lengths 1..12 x all 2^L continuation masks + 200000 fuzz cases with varied args/retann content, running the verbatim real post-patch _find_signature + format_signature (via a minimal DocstringSignatureMixin probe) and decoding collected signatures to tokens, compared against run_len/collected — 208190 cases, 0 divergences. len(model)==run_len(cont) held on every case.
(5) same-spec on model.py returns SAME (exit 0) — spec region intact.

Analysis: model abstracts a doc block to two parallel List[int] streams (cont = line.endswith('\\') continuation flag; val = opaque signature token) over the CLEAN-RUN domain (every modeled line matches py_ext_sig_re and has a valid base name). Within that domain the front-recursive folds mirror the real loop step-for-step: open line (cont!=0) <=> multiline:continue; terminating line (cont==0) or end-of-block <=> else:break / for-loop exhaustion; ordered append <=> [result]+self._signatures join. The last-line-continued edge (real for-loop exhausts -> stop vs model index-terminates) agrees, verified in the all-masks sweep. The real loop's additional behaviors (skip non-matching / wrong-name lines, stop on empty line, iterate multiple blocks) are a NARROWING of the assertion domain — weaker/under-claiming, which cannot make the spec too strong; those interleavings are covered by axiom_check.py's oracle. No modeled-domain input exists where the postconditions (Result==collected, len==run_len) disagree with the real callee. Secondary hunks (get_doc getattr->attr refactor, singledispatch objpath=[None] guard) are outside F2P-tested behavior and correctly unmodeled. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures); no RELAXED_LEAKAGE.md and relaxed_leakage flag is None, so judged strict. Semantic gold-reconstruction review of the spec view (docstring + pure funcs run_len/collected + pre/post-conditions of gather_signatures; impl region elided) finds NO leak beyond the public problem_statement.

Public problem_statement already reveals: autodoc_docstring_signature currently picks up only the FIRST signature and the feature is to 'pick up all of them' (overloaded methods, multiple signatures at the start of a docstring).

Spec view relative to that: (1) No patched file path 'sphinx/ext/autodoc/__init__.py' present. (2) No patched repo symbol (DocstringSignatureMixin, format_signature, get_doc) present — spec-view identifiers are the abstract run_len/collected/gather_signatures/cont/val. (3) No gold-patch code line reproduced; the concrete gold discriminator (line.endswith('\\') backslash continuation, self._signatures.append(...), '\n'.join([sig]+self._signatures)) is NEVER named — the run-boundary is abstracted to an opaque 'trailing line-spillover marker' / non-zero integer flag over parallel List[int] streams with opaque signature tokens. (4) No diff markers, no bug/fix/patch narration in comments.

The behavioral content beyond the problem statement (collect every line from the top up to and including the first terminating line; an open leading line yields ALL collected signatures) is the legitimate specification of the requested behavior, not edit-localization: a solver reading only the spec view cannot recover the file, the changed symbols, the backslash marker syntax, or the join code — the concrete gold specifics live only in refinement.md/mapping.md (audit artifacts, not the consumer spec view). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
