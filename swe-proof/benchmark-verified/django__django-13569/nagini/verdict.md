# P2 adversarial audit — django__django-13569

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py`, `atk_9.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     """The grouping columns offered by a single non-deterministic ordering
     term whose own column identity is `colid`."""
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,7 +106,6 @@
     Requires(Acc(list_pred(ref), 1 / 2))
     Requires(Acc(list_pred(cols), 1 / 2))
     Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(nondet), 1 / 2))
@@ -120,46 +117,20 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(nondet)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(nondet):
         Invariant(Acc(list_pred(nondet), 1 / 2))
         Invariant(Acc(list_pred(ref), 1 / 2))
         Invariant(Acc(list_pred(cols), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
         Invariant(0 <= i and i <= len(nondet))
-        # `result` already holds the columns gathered from the tail [i, n).
-        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
-                                            ToSeq(ref).drop(i),
-                                            ToSeq(cols).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
-        # unfolding `gathered` on it takes the recursive branch. Link the list
-        # values to the head elements of the dropped tails so the unfold's
-        # internal head reads agree with the branch taken below.
-        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
-        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
-        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
-        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
-        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
-        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
-        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
-        if ref[i - 1] != 0:
-            # A reference term offers nothing: gathered(tail j) == gathered(i).
+        if ref[i] != 0:
             result = result
-        elif nondet[i - 1] != 0:
-            contributed = random_group_by_cols(cols[i - 1])
-            # `offered_cols(nondet[i-1], ...)` and `offered_cols(1, ...)` agree:
-            # both arguments are non-zero, so both are the empty sequence.
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   offered_cols(1, cols[i - 1]))
-            result = contributed + result
+        elif nondet[i] != 0:
+            result = result
         else:
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   PSeq(cols[i - 1]))
-            result = [cols[i - 1]] + result
-        i = i - 1
+            result = result + [cols[i]]
+        i = i + 1
     return result
     # impl-end
```

Attack 2 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     """The grouping columns offered by a single non-deterministic ordering
     term whose own column identity is `colid`."""
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,7 +106,6 @@
     Requires(Acc(list_pred(ref), 1 / 2))
     Requires(Acc(list_pred(cols), 1 / 2))
     Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(nondet), 1 / 2))
@@ -120,46 +117,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(nondet)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(nondet), 1 / 2))
-        Invariant(Acc(list_pred(ref), 1 / 2))
-        Invariant(Acc(list_pred(cols), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
-        Invariant(0 <= i and i <= len(nondet))
-        # `result` already holds the columns gathered from the tail [i, n).
-        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
-                                            ToSeq(ref).drop(i),
-                                            ToSeq(cols).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
-        # unfolding `gathered` on it takes the recursive branch. Link the list
-        # values to the head elements of the dropped tails so the unfold's
-        # internal head reads agree with the branch taken below.
-        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
-        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
-        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
-        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
-        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
-        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
-        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
-        if ref[i - 1] != 0:
-            # A reference term offers nothing: gathered(tail j) == gathered(i).
-            result = result
-        elif nondet[i - 1] != 0:
-            contributed = random_group_by_cols(cols[i - 1])
-            # `offered_cols(nondet[i-1], ...)` and `offered_cols(1, ...)` agree:
-            # both arguments are non-zero, so both are the empty sequence.
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   offered_cols(1, cols[i - 1]))
-            result = contributed + result
-        else:
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   PSeq(cols[i - 1]))
-            result = [cols[i - 1]] + result
-        i = i - 1
     return result
     # impl-end
```

Attack 3 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     """The grouping columns offered by a single non-deterministic ordering
     term whose own column identity is `colid`."""
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -92,7 +90,7 @@
     Ensures(ToSeq(Result()) == offered_cols(1, colid))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
+    result = [colid]  # type: List[int]
     return result
     # impl-end
 
@@ -108,7 +106,6 @@
     Requires(Acc(list_pred(ref), 1 / 2))
     Requires(Acc(list_pred(cols), 1 / 2))
     Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(nondet), 1 / 2))
@@ -133,7 +130,6 @@
         Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
                                             ToSeq(ref).drop(i),
                                             ToSeq(cols).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
         # unfolding `gathered` on it takes the recursive branch. Link the list
```

Attack 4 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     """The grouping columns offered by a single non-deterministic ordering
     term whose own column identity is `colid`."""
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,7 +106,6 @@
     Requires(Acc(list_pred(ref), 1 / 2))
     Requires(Acc(list_pred(cols), 1 / 2))
     Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(nondet), 1 / 2))
@@ -120,45 +117,19 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(nondet)
+    i = len(nondet) - 1
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(nondet), 1 / 2))
         Invariant(Acc(list_pred(ref), 1 / 2))
         Invariant(Acc(list_pred(cols), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
         Invariant(0 <= i and i <= len(nondet))
-        # `result` already holds the columns gathered from the tail [i, n).
-        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
-                                            ToSeq(ref).drop(i),
-                                            ToSeq(cols).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
-        # unfolding `gathered` on it takes the recursive branch. Link the list
-        # values to the head elements of the dropped tails so the unfold's
-        # internal head reads agree with the branch taken below.
-        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
-        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
-        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
-        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
-        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
-        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
-        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
         if ref[i - 1] != 0:
-            # A reference term offers nothing: gathered(tail j) == gathered(i).
             result = result
         elif nondet[i - 1] != 0:
-            contributed = random_group_by_cols(cols[i - 1])
-            # `offered_cols(nondet[i-1], ...)` and `offered_cols(1, ...)` agree:
-            # both arguments are non-zero, so both are the empty sequence.
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   offered_cols(1, cols[i - 1]))
-            result = contributed + result
+            result = result
         else:
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   PSeq(cols[i - 1]))
             result = [cols[i - 1]] + result
         i = i - 1
     return result
```

Attack 5 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     """The grouping columns offered by a single non-deterministic ordering
     term whose own column identity is `colid`."""
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,7 +106,6 @@
     Requires(Acc(list_pred(ref), 1 / 2))
     Requires(Acc(list_pred(cols), 1 / 2))
     Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(nondet), 1 / 2))
@@ -119,47 +116,11 @@
                                          ToSeq(cols)))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    i = len(nondet)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(nondet), 1 / 2))
-        Invariant(Acc(list_pred(ref), 1 / 2))
-        Invariant(Acc(list_pred(cols), 1 / 2))
+    result = [cols[0]]  # type: List[int]
+    i = 0
+    while i >= 0:
         Invariant(Acc(list_pred(result)))
-        Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
-        Invariant(0 <= i and i <= len(nondet))
-        # `result` already holds the columns gathered from the tail [i, n).
-        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
-                                            ToSeq(ref).drop(i),
-                                            ToSeq(cols).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
-        # unfolding `gathered` on it takes the recursive branch. Link the list
-        # values to the head elements of the dropped tails so the unfold's
-        # internal head reads agree with the branch taken below.
-        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
-        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
-        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
-        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
-        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
-        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
-        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
-        if ref[i - 1] != 0:
-            # A reference term offers nothing: gathered(tail j) == gathered(i).
-            result = result
-        elif nondet[i - 1] != 0:
-            contributed = random_group_by_cols(cols[i - 1])
-            # `offered_cols(nondet[i-1], ...)` and `offered_cols(1, ...)` agree:
-            # both arguments are non-zero, so both are the empty sequence.
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   offered_cols(1, cols[i - 1]))
-            result = contributed + result
-        else:
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   PSeq(cols[i - 1]))
-            result = [cols[i - 1]] + result
-        i = i - 1
+        Invariant(i >= 0)
+        i = i + 1
     return result
     # impl-end
```

Attack 6 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     """The grouping columns offered by a single non-deterministic ordering
     term whose own column identity is `colid`."""
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,7 +106,6 @@
     Requires(Acc(list_pred(ref), 1 / 2))
     Requires(Acc(list_pred(cols), 1 / 2))
     Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(nondet), 1 / 2))
@@ -122,43 +119,15 @@
     result = []  # type: List[int]
     i = len(nondet)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(nondet), 1 / 2))
         Invariant(Acc(list_pred(ref), 1 / 2))
         Invariant(Acc(list_pred(cols), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
         Invariant(0 <= i and i <= len(nondet))
-        # `result` already holds the columns gathered from the tail [i, n).
-        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
-                                            ToSeq(ref).drop(i),
-                                            ToSeq(cols).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
-        # unfolding `gathered` on it takes the recursive branch. Link the list
-        # values to the head elements of the dropped tails so the unfold's
-        # internal head reads agree with the branch taken below.
-        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
-        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
-        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
-        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
-        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
-        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
-        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
         if ref[i - 1] != 0:
-            # A reference term offers nothing: gathered(tail j) == gathered(i).
             result = result
-        elif nondet[i - 1] != 0:
-            contributed = random_group_by_cols(cols[i - 1])
-            # `offered_cols(nondet[i-1], ...)` and `offered_cols(1, ...)` agree:
-            # both arguments are non-zero, so both are the empty sequence.
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   offered_cols(1, cols[i - 1]))
-            result = contributed + result
         else:
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   PSeq(cols[i - 1]))
             result = [cols[i - 1]] + result
         i = i - 1
     return result
```

Attack 7 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     """The grouping columns offered by a single non-deterministic ordering
     term whose own column identity is `colid`."""
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -108,7 +106,6 @@
     Requires(Acc(list_pred(ref), 1 / 2))
     Requires(Acc(list_pred(cols), 1 / 2))
     Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(nondet), 1 / 2))
@@ -122,43 +119,15 @@
     result = []  # type: List[int]
     i = len(nondet)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(nondet), 1 / 2))
         Invariant(Acc(list_pred(ref), 1 / 2))
         Invariant(Acc(list_pred(cols), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
         Invariant(0 <= i and i <= len(nondet))
-        # `result` already holds the columns gathered from the tail [i, n).
-        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
-                                            ToSeq(ref).drop(i),
-                                            ToSeq(cols).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
-        # unfolding `gathered` on it takes the recursive branch. Link the list
-        # values to the head elements of the dropped tails so the unfold's
-        # internal head reads agree with the branch taken below.
-        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
-        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
-        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
-        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
-        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
-        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
-        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
-        if ref[i - 1] != 0:
-            # A reference term offers nothing: gathered(tail j) == gathered(i).
+        if nondet[i - 1] != 0:
             result = result
-        elif nondet[i - 1] != 0:
-            contributed = random_group_by_cols(cols[i - 1])
-            # `offered_cols(nondet[i-1], ...)` and `offered_cols(1, ...)` agree:
-            # both arguments are non-zero, so both are the empty sequence.
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   offered_cols(1, cols[i - 1]))
-            result = contributed + result
         else:
-            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
-                   PSeq(cols[i - 1]))
             result = [cols[i - 1]] + result
         i = i - 1
     return result
```

Attack 8 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -83,7 +82,6 @@
     """The grouping columns offered by a single non-deterministic ordering
     term whose own column identity is `colid`."""
     # pre-conditions-start
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -92,7 +90,7 @@
     Ensures(ToSeq(Result()) == offered_cols(1, colid))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
+    result = [colid, colid]  # type: List[int]
     return result
     # impl-end
 
@@ -108,7 +106,6 @@
     Requires(Acc(list_pred(ref), 1 / 2))
     Requires(Acc(list_pred(cols), 1 / 2))
     Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(nondet), 1 / 2))
@@ -133,7 +130,6 @@
         Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
                                             ToSeq(ref).drop(i),
                                             ToSeq(cols).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
         # unfolding `gathered` on it takes the recursive branch. Link the list
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13569.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the columns that an ORDER BY clause contributes to a GROUP BY clause are
  assembled, each ordering term offers the set of grouping columns it depends
  on. A term that selects rows in a *non-deterministic* order — an order that
  is not a function of any stored column — depends on NO column, and must
  therefore contribute NOTHING to the grouping.

  Concretely, two behaviours are pinned:

    (1) The grouping columns offered by a single non-deterministic ordering
        term are EMPTY. A deterministic ordering term over a stored column
        still offers exactly that one column.

    (2) The grouping columns gathered from a whole list of ordering terms are
        the concatenation, in order, of the columns each term offers, with
        reference terms (those already represented in the selected columns)
        skipped. Because a non-deterministic term offers nothing, no such term
        ever appears among the gathered grouping columns — so an aggregation
        accompanied by a non-deterministic ordering is grouped exactly as it
        would be without that ordering.

An ordering term is modelled as a minimal record exposing only the touched
fields: whether it is non-deterministic, whether it is a reference into the
already-selected columns, and the identity of the single stored column a
deterministic term depends on. A list of terms is carried by index-aligned
`List[int]`; the gathered grouping columns are a `List[int]` of column
identities, specified via `PSeq[int]`.

No callee is axiomatized: the per-term column contribution and its gathering
are modelled deeply. The default per-term contribution (a deterministic term
offers its one column) is the unchanged base behaviour; the non-deterministic
term offering nothing is the behaviour under change, modelled directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# No consumed axioms: the per-term grouping-column contribution and its
# gathering over an ordering list are pure data-flow, modelled deeply.
# axioms-end

# pure-start
@Pure
def offered_cols(is_nondet: int, colid: int) -> PSeq[int]:
    """The grouping columns a single ordering term offers.

    A non-deterministic ordering term (is_nondet != 0) depends on no stored
    column, so it offers the empty sequence. A deterministic term offers
    exactly the one stored column it depends on."""
    if is_nondet != 0:
        return PSeq(0).take(0)
    return PSeq(colid)

@Pure
def gathered(nondet: PSeq[int], ref: PSeq[int], cols: PSeq[int]) -> PSeq[int]:
    """Grouping columns gathered from a whole list of ordering terms.

    Front-recursive on the sequence structure (drop the head, recurse on the
    tail) so a single unfold is available per loop step: the head term (unless
    it is a reference) offers `offered_cols`, prepended to the columns gathered
    from the tail. The three index-aligned sequences are consumed in lockstep;
    the recursion stops as soon as any of them is exhausted (in use they are of
    equal length, so this is precisely 'all terms consumed')."""
    if len(nondet) == 0 or len(ref) == 0 or len(cols) == 0:
        return PSeq(0).take(0)
    if ref[0] != 0:
        return gathered(nondet.drop(1), ref.drop(1), cols.drop(1))
    return offered_cols(nondet[0], cols[0]) + gathered(
        nondet.drop(1), ref.drop(1), cols.drop(1))
# pure-end

def random_group_by_cols(colid: int) -> List[int]:
    """The grouping columns offered by a single non-deterministic ordering
    term whose own column identity is `colid`."""
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # A non-deterministic ordering term offers NO grouping column.
    Ensures(len(Result()) == 0)
    Ensures(ToSeq(Result()) == offered_cols(1, colid))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    return result
    # impl-end

def group_by_columns_for_ordering(nondet: List[int], ref: List[int],
                                  cols: List[int]) -> List[int]:
    """Gather, in order, the grouping columns offered by a list of ordering
    terms. `nondet[k]`/`ref[k]`/`cols[k]` describe term k: whether it is
    non-deterministic, whether it is a reference into the selected columns
    (then skipped), and its own column identity."""
    # pre-conditions-start
    Requires(Acc(list_pred(nondet), 1 / 2))
    Requires(Acc(list_pred(ref), 1 / 2))
    Requires(Acc(list_pred(cols), 1 / 2))
    Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(nondet), 1 / 2))
    Ensures(Acc(list_pred(ref), 1 / 2))
    Ensures(Acc(list_pred(cols), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == gathered(ToSeq(nondet), ToSeq(ref),
                                         ToSeq(cols)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(nondet)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(nondet), 1 / 2))
        Invariant(Acc(list_pred(ref), 1 / 2))
        Invariant(Acc(list_pred(cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
        Invariant(0 <= i and i <= len(nondet))
        # `result` already holds the columns gathered from the tail [i, n).
        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
                                            ToSeq(ref).drop(i),
                                            ToSeq(cols).drop(i)))
        # invariants-end
        # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
        # unfolding `gathered` on it takes the recursive branch. Link the list
        # values to the head elements of the dropped tails so the unfold's
        # internal head reads agree with the branch taken below.
        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        if ref[i - 1] != 0:
            # A reference term offers nothing: gathered(tail j) == gathered(i).
            result = result
        elif nondet[i - 1] != 0:
            contributed = random_group_by_cols(cols[i - 1])
            # `offered_cols(nondet[i-1], ...)` and `offered_cols(1, ...)` agree:
            # both arguments are non-zero, so both are the empty sequence.
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   offered_cols(1, cols[i - 1]))
            result = contributed + result
        else:
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   PSeq(cols[i - 1]))
            result = [cols[i - 1]] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of django__django-13569 (nagini). verifier venv python; commands run as `python -m swebench_unified.adversary weakness/same-spec nagini django__django-13569 <atk>` and `bash scripts/nagini_verify.sh <atk>`; resolve via swebench_unified.harness.run_resolve.

SPEC SHAPE: both functions have fully-pinned postconditions. random_group_by_cols: Ensures(len(Result())==0) AND ToSeq(Result())==offered_cols(1,colid) (empty). group_by_columns_for_ordering: ToSeq(Result())==gathered(ToSeq(nondet),ToSeq(ref),ToSeq(cols)). offered_cols/gathered are DEEP models (A-references), no @ContractOnly consumed.

### LEGITIMATE (terminating, hygiene-clean) WRONG IMPLS — ALL REJECTED (spec is tight)
Each edits only an impl region; same-spec EXIT 0; `weakness` EXIT 2 (does not verify); check_attack -> same_spec=True, verifies=False, verify_completed=True:
- atk_3.py loop appends at tail (wrong order): REJECTED.
- atk_4.py loop always returns [] (drops deterministic cols): REJECTED.
- atk_5.py PREPATCH BUG: random_group_by_cols returns [colid] (=[self]), terminating: REJECTED -> spec senses the change (G-DIFF). This is prepatch_reproduced=True.
- atk_8.py loop off-by-one (i=len-1, drops last term): REJECTED.
- atk_9.py loop reads cols[0] on possibly-empty list: REJECTED (bounds precondition).
- atk_11.py loop treats nondet terms as deterministic (offers cols[i]) = the exact RANDOM-leaks-into-GROUP-BY bug the patch fixes: REJECTED.
- atk_12.py loop does NOT skip is_ref reference terms: REJECTED.
- atk_13.py random_group_by_cols returns [colid,colid] (len!=0): REJECTED.
POSITIVE CONTROL pos_control.py (verbatim gold model): check_attack verifies=True (nagini_verify.sh EXIT 0, 13.7s). Distinct file from all attacks.

=== TWO `weakness`-TOOL CANDIDATES — BOTH VERIFIER-GAMING ARTIFACTS, NOT GENUINE COUNTEREXAMPLES (deliberately EXCLUDED from the attacks list; disclosed here in full) ===

(1) atk_6.py / atk_7.py: verify ONLY via Assume(False) prepended to a wrong impl (`weakness` EXIT 0). `Assume(` is a BANNED TOKEN in nagini G-HYGIENE (backends/nagini.py banned_tokens=('Assume(','Refute('); quickref: 'No Assume/Refute'). A model.py using it can never be a bundle. AST check confirms banned call {'Assume'} present. Trivial reductio: Assume(False) verifies any postcondition -> not a spec weakness.

(2) atk_10.py: verifies ONLY via NON-TERMINATION. impl = `result=[colid]; i=0; while i>=0: Invariant(Acc(list_pred(result))); Invariant(i>=0); i=i+1; return result`. The negated guard (i<0) contradicts Invariant(i>=0), so the post-loop state is infeasible and the wrong `return [colid]` (=[self], prepatch bug) is covered vacuously (partial correctness). No banned tokens; imports clean (typing, nagini_contracts) -> PASSES G-HYGIENE. check_attack -> same_spec=True, verifies=True, verify_completed=True (nagini_verify EXIT 0, 12.3s).

WHY IT IS NOT A GENUINE BREAK: (a) REDUCTIO — prepending such a loop to ANY nagini model verifies it vacuously and its faithful refinement hangs the F2P test -> never resolves; if this counted as BROKEN, no nagini bundle without MustTerminate (420/500) could ever be SOUND, contradicting quickref 'Termination proofs are NOT required by default' and the existing SOUND nagini board. (b) The terminating impl computing the same value (atk_5) is REJECTED, so atk_10 buys 'verification' purely by diverging — it does not actually compute a wrong terminating output. (c) G-CONF BACKSTOP: atk_10's contract-stripped shadow (what G-CONF executes) HANGS (measured exit 124) -> G-CONF times out -> such a bundle can never be green. This parallels atk_6's G-HYGIENE rejection.

### MANDATORY RESOLVE EVIDENCE (executed, machine-checked)
Materialized the faithful refined patch for the [self]/prepatch behaviour the candidates encode (gold context with `return []` -> `return [self]`; faithful_patch_selfcol.diff).
- run_resolve(faithful [self] patch): completed=True, resolved=False, note='patch did not resolve in 3 attempts (consistent — not flaky)'. (run_id sbu-eq-atk-faithful-selfcol-v2)
- run_resolve(GOLD patch.diff, positive control): completed=True, resolved=True, note='resolved'. (run_id sbu-eq-gold-poscontrol-v2)
The harness is sound and discriminating. The non-resolving [self] patch is the faithful refinement of the TERMINATING prepatch impl (atk_5) which the spec REJECTS — it is NOT the refinement of any legitimately-verifying same-spec impl. atk_10's own faithful refinement (a diverging get_group_by_cols) would hang the test rather than resolve; either way the non-resolution stems from the excluded non-termination/prepatch behaviour, not from a genuine verify->wrong-terminating-output admitted by the spec.

### refinement.md LEG AUDIT (no kind-3)
A1=R, A2=R+I, A3=A-reference, B1=R+(directive 5), B2=I, B3=A-reference+I, B4=A-reference+I, B5=A-reference. Every leg is R / A-reference / I — NO kind-3 (unexpressible-changed-op). The single changed op ([self]->[]) is modeled DEEPLY in the postcondition (len==0 / offered_cols(is_nondet!=0)==PSeq()), not axiomatized. A-references grounded in real callees (axiom_check.py asserts Random().get_group_by_cols()==[], incl. alias= kwarg, and OrderBy(Random())==[]; gathering loop mirrored; verdict.md records G-AX OK over 3003 observations post-patch, prepatch A-ref-1 fails as expected). conformance_check.py shadows the impl regions verbatim (contract-stripped) against the REAL patched Random/OrderBy/RawSQL + the SQLCompiler.get_group_by gathering slice, 100k fuzz + exhaustive n=0..4, seed 13569.

VERDICT: SOUND. 8 legitimate terminating same-spec wrong impls (incl. the exact prepatch bug) all rejected; positive control verifies; the only two 'verifying' impls found game the verifier via a banned construct (G-HYGIENE) and non-termination (G-CONF; generic partial-correctness reductio), neither being a genuine spec-fidelity defect. Refinement legs sound with no kind-3.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py`, `atk_9.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_13.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13569.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the columns that an ORDER BY clause contributes to a GROUP BY clause are
  assembled, each ordering term offers the set of grouping columns it depends
  on. A term that selects rows in a *non-deterministic* order — an order that
  is not a function of any stored column — depends on NO column, and must
  therefore contribute NOTHING to the grouping.

  Concretely, two behaviours are pinned:

    (1) The grouping columns offered by a single non-deterministic ordering
        term are EMPTY. A deterministic ordering term over a stored column
        still offers exactly that one column.

    (2) The grouping columns gathered from a whole list of ordering terms are
        the concatenation, in order, of the columns each term offers, with
        reference terms (those already represented in the selected columns)
        skipped. Because a non-deterministic term offers nothing, no such term
        ever appears among the gathered grouping columns — so an aggregation
        accompanied by a non-deterministic ordering is grouped exactly as it
        would be without that ordering.

An ordering term is modelled as a minimal record exposing only the touched
fields: whether it is non-deterministic, whether it is a reference into the
already-selected columns, and the identity of the single stored column a
deterministic term depends on. A list of terms is carried by index-aligned
`List[int]`; the gathered grouping columns are a `List[int]` of column
identities, specified via `PSeq[int]`.

No callee is axiomatized: the per-term column contribution and its gathering
are modelled deeply. The default per-term contribution (a deterministic term
offers its one column) is the unchanged base behaviour; the non-deterministic
term offering nothing is the behaviour under change, modelled directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# No consumed axioms: the per-term grouping-column contribution and its
# gathering over an ordering list are pure data-flow, modelled deeply.
# axioms-end

# pure-start
@Pure
def offered_cols(is_nondet: int, colid: int) -> PSeq[int]:
    """The grouping columns a single ordering term offers.

    A non-deterministic ordering term (is_nondet != 0) depends on no stored
    column, so it offers the empty sequence. A deterministic term offers
    exactly the one stored column it depends on."""
    if is_nondet != 0:
        return PSeq(0).take(0)
    return PSeq(colid)

@Pure
def gathered(nondet: PSeq[int], ref: PSeq[int], cols: PSeq[int]) -> PSeq[int]:
    """Grouping columns gathered from a whole list of ordering terms.

    Front-recursive on the sequence structure (drop the head, recurse on the
    tail) so a single unfold is available per loop step: the head term (unless
    it is a reference) offers `offered_cols`, prepended to the columns gathered
    from the tail. The three index-aligned sequences are consumed in lockstep;
    the recursion stops as soon as any of them is exhausted (in use they are of
    equal length, so this is precisely 'all terms consumed')."""
    if len(nondet) == 0 or len(ref) == 0 or len(cols) == 0:
        return PSeq(0).take(0)
    if ref[0] != 0:
        return gathered(nondet.drop(1), ref.drop(1), cols.drop(1))
    return offered_cols(nondet[0], cols[0]) + gathered(
        nondet.drop(1), ref.drop(1), cols.drop(1))
# pure-end

def random_group_by_cols(colid: int) -> List[int]:
    """The grouping columns offered by a single non-deterministic ordering
    term whose own column identity is `colid`."""
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # A non-deterministic ordering term offers NO grouping column.
    Ensures(len(Result()) == 0)
    Ensures(ToSeq(Result()) == offered_cols(1, colid))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    return result
    # impl-end

def group_by_columns_for_ordering(nondet: List[int], ref: List[int],
                                  cols: List[int]) -> List[int]:
    """Gather, in order, the grouping columns offered by a list of ordering
    terms. `nondet[k]`/`ref[k]`/`cols[k]` describe term k: whether it is
    non-deterministic, whether it is a reference into the selected columns
    (then skipped), and its own column identity."""
    # pre-conditions-start
    Requires(Acc(list_pred(nondet), 1 / 2))
    Requires(Acc(list_pred(ref), 1 / 2))
    Requires(Acc(list_pred(cols), 1 / 2))
    Requires(len(ref) == len(nondet) and len(cols) == len(nondet))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(nondet), 1 / 2))
    Ensures(Acc(list_pred(ref), 1 / 2))
    Ensures(Acc(list_pred(cols), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == gathered(ToSeq(nondet), ToSeq(ref),
                                         ToSeq(cols)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(nondet)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(nondet), 1 / 2))
        Invariant(Acc(list_pred(ref), 1 / 2))
        Invariant(Acc(list_pred(cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(ref) == len(nondet) and len(cols) == len(nondet))
        Invariant(0 <= i and i <= len(nondet))
        # `result` already holds the columns gathered from the tail [i, n).
        Invariant(ToSeq(result) == gathered(ToSeq(nondet).drop(i),
                                            ToSeq(ref).drop(i),
                                            ToSeq(cols).drop(i)))
        # invariants-end
        # The tail starting at j = i-1 is non-empty (i > 0, lengths equal), so
        # unfolding `gathered` on it takes the recursive branch. Link the list
        # values to the head elements of the dropped tails so the unfold's
        # internal head reads agree with the branch taken below.
        Assert(len(ToSeq(nondet).drop(i - 1)) == len(nondet) - (i - 1))
        Assert(ToSeq(nondet).drop(i - 1)[0] == nondet[i - 1])
        Assert(ToSeq(ref).drop(i - 1)[0] == ref[i - 1])
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(nondet).drop(i - 1).drop(1) == ToSeq(nondet).drop(i))
        Assert(ToSeq(ref).drop(i - 1).drop(1) == ToSeq(ref).drop(i))
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        if ref[i - 1] != 0:
            # A reference term offers nothing: gathered(tail j) == gathered(i).
            result = result
        elif nondet[i - 1] != 0:
            contributed = random_group_by_cols(cols[i - 1])
            # `offered_cols(nondet[i-1], ...)` and `offered_cols(1, ...)` agree:
            # both arguments are non-zero, so both are the empty sequence.
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   offered_cols(1, cols[i - 1]))
            result = contributed + result
        else:
            Assert(offered_cols(nondet[i - 1], cols[i - 1]) ==
                   PSeq(cols[i - 1]))
            result = [cols[i - 1]] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of django__django-13569 (nagini). verifier venv python; commands run as `python -m swebench_unified.adversary weakness/same-spec nagini django__django-13569 <atk>` and `bash scripts/nagini_verify.sh <atk>`; resolve via swebench_unified.harness.run_resolve.

SPEC SHAPE: both functions have fully-pinned postconditions. random_group_by_cols: Ensures(len(Result())==0) AND ToSeq(Result())==offered_cols(1,colid) (empty). group_by_columns_for_ordering: ToSeq(Result())==gathered(ToSeq(nondet),ToSeq(ref),ToSeq(cols)). offered_cols/gathered are DEEP models (A-references), no @ContractOnly consumed.

### LEGITIMATE (terminating, hygiene-clean) WRONG IMPLS — ALL REJECTED (spec is tight)
Each edits only an impl region; same-spec EXIT 0; `weakness` EXIT 2 (does not verify); check_attack -> same_spec=True, verifies=False, verify_completed=True:
- atk_3.py loop appends at tail (wrong order): REJECTED.
- atk_4.py loop always returns [] (drops deterministic cols): REJECTED.
- atk_5.py PREPATCH BUG: random_group_by_cols returns [colid] (=[self]), terminating: REJECTED -> spec senses the change (G-DIFF). This is prepatch_reproduced=True.
- atk_8.py loop off-by-one (i=len-1, drops last term): REJECTED.
- atk_9.py loop reads cols[0] on possibly-empty list: REJECTED (bounds precondition).
- atk_11.py loop treats nondet terms as deterministic (offers cols[i]) = the exact RANDOM-leaks-into-GROUP-BY bug the patch fixes: REJECTED.
- atk_12.py loop does NOT skip is_ref reference terms: REJECTED.
- atk_13.py random_group_by_cols returns [colid,colid] (len!=0): REJECTED.
POSITIVE CONTROL pos_control.py (verbatim gold model): check_attack verifies=True (nagini_verify.sh EXIT 0, 13.7s). Distinct file from all attacks.

=== TWO `weakness`-TOOL CANDIDATES — BOTH VERIFIER-GAMING ARTIFACTS, NOT GENUINE COUNTEREXAMPLES (deliberately EXCLUDED from the attacks list; disclosed here in full) ===

(1) atk_6.py / atk_7.py: verify ONLY via Assume(False) prepended to a wrong impl (`weakness` EXIT 0). `Assume(` is a BANNED TOKEN in nagini G-HYGIENE (backends/nagini.py banned_tokens=('Assume(','Refute('); quickref: 'No Assume/Refute'). A model.py using it can never be a bundle. AST check confirms banned call {'Assume'} present. Trivial reductio: Assume(False) verifies any postcondition -> not a spec weakness.

(2) atk_10.py: verifies ONLY via NON-TERMINATION. impl = `result=[colid]; i=0; while i>=0: Invariant(Acc(list_pred(result))); Invariant(i>=0); i=i+1; return result`. The negated guard (i<0) contradicts Invariant(i>=0), so the post-loop state is infeasible and the wrong `return [colid]` (=[self], prepatch bug) is covered vacuously (partial correctness). No banned tokens; imports clean (typing, nagini_contracts) -> PASSES G-HYGIENE. check_attack -> same_spec=True, verifies=True, verify_completed=True (nagini_verify EXIT 0, 12.3s).

WHY IT IS NOT A GENUINE BREAK: (a) REDUCTIO — prepending such a loop to ANY nagini model verifies it vacuously and its faithful refinement hangs the F2P test -> never resolves; if this counted as BROKEN, no nagini bundle without MustTerminate (420/500) could ever be SOUND, contradicting quickref 'Termination proofs are NOT required by default' and the existing SOUND nagini board. (b) The terminating impl computing the same value (atk_5) is REJECTED, so atk_10 buys 'verification' purely by diverging — it does not actually compute a wrong terminating output. (c) G-CONF BACKSTOP: atk_10's contract-stripped shadow (what G-CONF executes) HANGS (measured exit 124) -> G-CONF times out -> such a bundle can never be green. This parallels atk_6's G-HYGIENE rejection.

### MANDATORY RESOLVE EVIDENCE (executed, machine-checked)
Materialized the faithful refined patch for the [self]/prepatch behaviour the candidates encode (gold context with `return []` -> `return [self]`; faithful_patch_selfcol.diff).
- run_resolve(faithful [self] patch): completed=True, resolved=False, note='patch did not resolve in 3 attempts (consistent — not flaky)'. (run_id sbu-eq-atk-faithful-selfcol-v2)
- run_resolve(GOLD patch.diff, positive control): completed=True, resolved=True, note='resolved'. (run_id sbu-eq-gold-poscontrol-v2)
The harness is sound and discriminating. The non-resolving [self] patch is the faithful refinement of the TERMINATING prepatch impl (atk_5) which the spec REJECTS — it is NOT the refinement of any legitimately-verifying same-spec impl. atk_10's own faithful refinement (a diverging get_group_by_cols) would hang the test rather than resolve; either way the non-resolution stems from the excluded non-termination/prepatch behaviour, not from a genuine verify->wrong-terminating-output admitted by the spec.

### refinement.md LEG AUDIT (no kind-3)
A1=R, A2=R+I, A3=A-reference, B1=R+(directive 5), B2=I, B3=A-reference+I, B4=A-reference+I, B5=A-reference. Every leg is R / A-reference / I — NO kind-3 (unexpressible-changed-op). The single changed op ([self]->[]) is modeled DEEPLY in the postcondition (len==0 / offered_cols(is_nondet!=0)==PSeq()), not axiomatized. A-references grounded in real callees (axiom_check.py asserts Random().get_group_by_cols()==[], incl. alias= kwarg, and OrderBy(Random())==[]; gathering loop mirrored; verdict.md records G-AX OK over 3003 observations post-patch, prepatch A-ref-1 fails as expected). conformance_check.py shadows the impl regions verbatim (contract-stripped) against the REAL patched Random/OrderBy/RawSQL + the SQLCompiler.get_group_by gathering slice, 100k fuzz + exhaustive n=0..4, seed 13569.

VERDICT: SOUND. 8 legitimate terminating same-spec wrong impls (incl. the exact prepatch bug) all rejected; positive control verifies; the only two 'verifying' impls found game the verifier via a banned construct (G-HYGIENE) and non-termination (G-CONF; generic partial-correctness reductio), neither being a genuine spec-fidelity defect. Refinement legs sound with no kind-3.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo) confirmed for django__django-13569 nagini bundle.

Gold patch is minimal: adds `Random.get_group_by_cols(self, alias=None): return []` in django/db/models/functions/math.py. Modeled functions and their real callees:

1. `random_group_by_cols(colid)` -> [] models real `Random.get_group_by_cols()` (post-patch) -> []. Verified directly against the freshly-patched worktree at base_commit 257f8495 (incl. the alias=None kwarg variant).
2. `offered_cols(is_nondet,colid)`: nondet!=0 -> [], else -> [colid]; models a leaf ordering term's contribution — Random offers nothing, a deterministic RawSQL leaf offers `[self]` (one column). Matches BaseExpression/RawSQL.get_group_by_cols default `[self]`.
3. `gathered(nondet,ref,cols)` mirrors the UNCHANGED compiler order-by loop `for expr,(sql,params,is_ref) in order_by: if not is_ref: expressions.extend(expr.get_group_by_cols())` (compiler.py:128-131). Kind-I mirror.

Abstraction domain is explicitly disclosed in mapping.md §2 (leaf ordering terms: a bare Random vs a stored-column/RawSQL leaf vs a reference term), which is exactly the F2P scenario (Count annotation ordered by '?'). Within that domain no input distinguishes the model from the real callee.

Evidence: re-ran bundle G-CONF against patched worktree -> OK, 101,355 inputs, 0 disagreements; re-ran G-AX -> OK, 3,003 observations. Additionally authored an INDEPENDENT differential probe (real Django Random/RawSQL/OrderBy + compiler-loop mirror vs a fresh transcription of model.py's gathered/offered_cols) over 300,000 randomized term lists (lengths 0..12, non-canonical truthy/falsy flags, wide colid range) -> 0 divergences. The postconditions (len(Result())==0 for random_group_by_cols; ToSeq(Result())==gathered(...) for the loop) are exactly the observable repo behavior, neither stronger nor weaker. No diverging input exists; spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed byte-identical (same-spec EXIT 0). Mechanical G-LEAK screen passes: no diff markers, no reproduced gold line, no patched file/module path, no spec-view identifier or comment naming a patched symbol (changed symbols get_group_by_cols/as_oracle absent), no narration. 

Spec view = docstring + axioms note + pure region (offered_cols/gathered) + two function signatures with pre/post-conditions (impl elided to ...). It states only the abstract correctness property under invented model names: a non-deterministic ordering term offers the empty set of grouping columns (offered_cols(is_nondet!=0)==PSeq(); random_group_by_cols len==0), a deterministic term offers exactly its one column, and `gathered` concatenates each non-reference term's contribution in order. 

The gold edit — adding Random.get_group_by_cols(self, alias=None): return [] in django/db/models/functions/math.py — is NOT localizable from the spec view: math.py, get_group_by_cols, class Random, return [], expressions.py, compiler.py all absent. 

Critically, the public problem_statement is STRICTLY MORE revealing than the spec: it names the bug (order_by('?') breaks aggregation because RANDOM() leaks into GROUP BY), pinpoints SQLCompiler.get_group_by combining non-aggregate/non-ref order_by expressions, and even ships a candidate patch filtering out Random. Stating the correctness property is the legitimate function of a spec and leaks nothing beyond what the problem_statement already discloses. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
