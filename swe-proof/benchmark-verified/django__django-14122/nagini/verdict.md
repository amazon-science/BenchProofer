# P2 adversarial audit — django__django-14122

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_3.py` |

**Non-vacuity.** The positive control `atk_5.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # The ordering source carries one ref-flag per entry.
     Requires(len(order_cols) == len(order_is_backref))
     Requires(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(select_cols), 1 / 2))
@@ -106,7 +104,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # selected-column source (unconditional)
     s = 0
     while s < len(select_cols):
         # invariants-start
@@ -114,54 +111,46 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= s and s <= len(select_cols))
         Invariant(ToSeq(result) == ToSeq(select_cols).take(s))
-        Invariant(MustTerminate(len(select_cols) - s + 1))
         # invariants-end
         result.append(select_cols[s])
         s = s + 1
     Assert(ToSeq(result) == ToSeq(select_cols))
-    # result-ordering source (only when the ordering was explicitly requested)
-    if ordering_was_requested:
-        Assert(order_contrib(ToSeq(order_cols).take(0),
-                             ToSeq(order_is_backref).take(0)) == empty_seq())
-        k = 0
-        while k < len(order_cols):
-            # invariants-start
-            Invariant(Acc(list_pred(select_cols), 1 / 2))
-            Invariant(Acc(list_pred(order_cols), 1 / 2))
-            Invariant(Acc(list_pred(order_is_backref), 1 / 2))
-            Invariant(len(order_cols) == len(order_is_backref))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= k and k <= len(order_cols))
-            Invariant(ToSeq(result)
-                      == ToSeq(select_cols)
-                      + order_contrib(ToSeq(order_cols).take(k),
-                                      ToSeq(order_is_backref).take(k)))
-            Invariant(MustTerminate(len(order_cols) - k + 1))
-            # invariants-end
-            is_ref = order_is_backref[k]
-            col = order_cols[k]
-            # Extending the processed prefix by entry k is a single back-unfold
-            # of order_contrib: take(k+1) is take(k) with one more entry, and
-            # take(k+1).take(k) == take(k), take(k+1)[k] == the entry.
-            Assert(ToSeq(order_cols).take(k + 1)
-                   == ToSeq(order_cols).take(k) + PSeq(col))
-            Assert(ToSeq(order_is_backref).take(k + 1)
-                   == ToSeq(order_is_backref).take(k) + PSeq(is_ref))
-            Assert(ToSeq(order_cols).take(k + 1).take(k) == ToSeq(order_cols).take(k))
-            Assert(ToSeq(order_is_backref).take(k + 1).take(k) == ToSeq(order_is_backref).take(k))
-            Assert(ToSeq(order_cols).take(k + 1)[k] == col)
-            Assert(ToSeq(order_is_backref).take(k + 1)[k] == is_ref)
-            Assert(order_contrib(ToSeq(order_cols).take(k + 1),
-                                 ToSeq(order_is_backref).take(k + 1))
-                   == order_contrib(ToSeq(order_cols).take(k),
-                                    ToSeq(order_is_backref).take(k))
-                   + (empty_seq() if is_ref != 0 else PSeq(col)))
-            if is_ref == 0:
-                result.append(col)
-            k = k + 1
-        Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
-        Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
-    # trailing source (unconditional)
+    Assert(order_contrib(ToSeq(order_cols).take(0),
+                         ToSeq(order_is_backref).take(0)) == empty_seq())
+    k = 0
+    while k < len(order_cols):
+        # invariants-start
+        Invariant(Acc(list_pred(select_cols), 1 / 2))
+        Invariant(Acc(list_pred(order_cols), 1 / 2))
+        Invariant(Acc(list_pred(order_is_backref), 1 / 2))
+        Invariant(len(order_cols) == len(order_is_backref))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= k and k <= len(order_cols))
+        Invariant(ToSeq(result)
+                  == ToSeq(select_cols)
+                  + order_contrib(ToSeq(order_cols).take(k),
+                                  ToSeq(order_is_backref).take(k)))
+        # invariants-end
+        is_ref = order_is_backref[k]
+        col = order_cols[k]
+        Assert(ToSeq(order_cols).take(k + 1)
+               == ToSeq(order_cols).take(k) + PSeq(col))
+        Assert(ToSeq(order_is_backref).take(k + 1)
+               == ToSeq(order_is_backref).take(k) + PSeq(is_ref))
+        Assert(ToSeq(order_cols).take(k + 1).take(k) == ToSeq(order_cols).take(k))
+        Assert(ToSeq(order_is_backref).take(k + 1).take(k) == ToSeq(order_is_backref).take(k))
+        Assert(ToSeq(order_cols).take(k + 1)[k] == col)
+        Assert(ToSeq(order_is_backref).take(k + 1)[k] == is_ref)
+        Assert(order_contrib(ToSeq(order_cols).take(k + 1),
+                             ToSeq(order_is_backref).take(k + 1))
+               == order_contrib(ToSeq(order_cols).take(k),
+                                ToSeq(order_is_backref).take(k))
+               + (empty_seq() if is_ref != 0 else PSeq(col)))
+        if is_ref == 0:
+            result.append(col)
+        k = k + 1
+    Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
+    Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
     t = 0
     while t < len(trailing_cols):
         # invariants-start
@@ -172,17 +161,11 @@
         Invariant(Acc(list_pred(trailing_cols), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= t and t <= len(trailing_cols))
-        Invariant(Implies(
-            ordering_was_requested,
+        Invariant(
             ToSeq(result)
             == ToSeq(select_cols)
             + order_contrib(ToSeq(order_cols), ToSeq(order_is_backref))
-            + ToSeq(trailing_cols).take(t)))
-        Invariant(Implies(
-            not ordering_was_requested,
-            ToSeq(result)
-            == ToSeq(select_cols) + ToSeq(trailing_cols).take(t)))
-        Invariant(MustTerminate(len(trailing_cols) - t + 1))
+            + ToSeq(trailing_cols).take(t))
         # invariants-end
         result.append(trailing_cols[t])
         t = t + 1
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # The ordering source carries one ref-flag per entry.
     Requires(len(order_cols) == len(order_is_backref))
     Requires(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(select_cols), 1 / 2))
@@ -106,7 +104,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # selected-column source (unconditional)
     s = 0
     while s < len(select_cols):
         # invariants-start
@@ -114,13 +111,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= s and s <= len(select_cols))
         Invariant(ToSeq(result) == ToSeq(select_cols).take(s))
-        Invariant(MustTerminate(len(select_cols) - s + 1))
         # invariants-end
         result.append(select_cols[s])
         s = s + 1
     Assert(ToSeq(result) == ToSeq(select_cols))
-    # result-ordering source (only when the ordering was explicitly requested)
-    if ordering_was_requested:
+    if not ordering_was_requested:
         Assert(order_contrib(ToSeq(order_cols).take(0),
                              ToSeq(order_is_backref).take(0)) == empty_seq())
         k = 0
@@ -136,13 +131,9 @@
                       == ToSeq(select_cols)
                       + order_contrib(ToSeq(order_cols).take(k),
                                       ToSeq(order_is_backref).take(k)))
-            Invariant(MustTerminate(len(order_cols) - k + 1))
             # invariants-end
             is_ref = order_is_backref[k]
             col = order_cols[k]
-            # Extending the processed prefix by entry k is a single back-unfold
-            # of order_contrib: take(k+1) is take(k) with one more entry, and
-            # take(k+1).take(k) == take(k), take(k+1)[k] == the entry.
             Assert(ToSeq(order_cols).take(k + 1)
                    == ToSeq(order_cols).take(k) + PSeq(col))
             Assert(ToSeq(order_is_backref).take(k + 1)
@@ -161,7 +152,6 @@
             k = k + 1
         Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
         Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
-    # trailing source (unconditional)
     t = 0
     while t < len(trailing_cols):
         # invariants-start
@@ -182,7 +172,6 @@
             not ordering_was_requested,
             ToSeq(result)
             == ToSeq(select_cols) + ToSeq(trailing_cols).take(t)))
-        Invariant(MustTerminate(len(trailing_cols) - t + 1))
         # invariants-end
         result.append(trailing_cols[t])
         t = t + 1
```

Attack 3 — `atk_3.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # The ordering source carries one ref-flag per entry.
     Requires(len(order_cols) == len(order_is_backref))
     Requires(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(select_cols), 1 / 2))
@@ -106,7 +104,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # selected-column source (unconditional)
     s = 0
     while s < len(select_cols):
         # invariants-start
@@ -114,78 +111,19 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= s and s <= len(select_cols))
         Invariant(ToSeq(result) == ToSeq(select_cols).take(s))
-        Invariant(MustTerminate(len(select_cols) - s + 1))
         # invariants-end
         result.append(select_cols[s])
         s = s + 1
     Assert(ToSeq(result) == ToSeq(select_cols))
-    # result-ordering source (only when the ordering was explicitly requested)
-    if ordering_was_requested:
-        Assert(order_contrib(ToSeq(order_cols).take(0),
-                             ToSeq(order_is_backref).take(0)) == empty_seq())
-        k = 0
-        while k < len(order_cols):
-            # invariants-start
-            Invariant(Acc(list_pred(select_cols), 1 / 2))
-            Invariant(Acc(list_pred(order_cols), 1 / 2))
-            Invariant(Acc(list_pred(order_is_backref), 1 / 2))
-            Invariant(len(order_cols) == len(order_is_backref))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= k and k <= len(order_cols))
-            Invariant(ToSeq(result)
-                      == ToSeq(select_cols)
-                      + order_contrib(ToSeq(order_cols).take(k),
-                                      ToSeq(order_is_backref).take(k)))
-            Invariant(MustTerminate(len(order_cols) - k + 1))
-            # invariants-end
-            is_ref = order_is_backref[k]
-            col = order_cols[k]
-            # Extending the processed prefix by entry k is a single back-unfold
-            # of order_contrib: take(k+1) is take(k) with one more entry, and
-            # take(k+1).take(k) == take(k), take(k+1)[k] == the entry.
-            Assert(ToSeq(order_cols).take(k + 1)
-                   == ToSeq(order_cols).take(k) + PSeq(col))
-            Assert(ToSeq(order_is_backref).take(k + 1)
-                   == ToSeq(order_is_backref).take(k) + PSeq(is_ref))
-            Assert(ToSeq(order_cols).take(k + 1).take(k) == ToSeq(order_cols).take(k))
-            Assert(ToSeq(order_is_backref).take(k + 1).take(k) == ToSeq(order_is_backref).take(k))
-            Assert(ToSeq(order_cols).take(k + 1)[k] == col)
-            Assert(ToSeq(order_is_backref).take(k + 1)[k] == is_ref)
-            Assert(order_contrib(ToSeq(order_cols).take(k + 1),
-                                 ToSeq(order_is_backref).take(k + 1))
-                   == order_contrib(ToSeq(order_cols).take(k),
-                                    ToSeq(order_is_backref).take(k))
-                   + (empty_seq() if is_ref != 0 else PSeq(col)))
-            if is_ref == 0:
-                result.append(col)
-            k = k + 1
-        Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
-        Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
-    # trailing source (unconditional)
-    t = 0
-    while t < len(trailing_cols):
+    while True:
         # invariants-start
         Invariant(Acc(list_pred(select_cols), 1 / 2))
         Invariant(Acc(list_pred(order_cols), 1 / 2))
         Invariant(Acc(list_pred(order_is_backref), 1 / 2))
+        Invariant(Acc(list_pred(trailing_cols), 1 / 2))
         Invariant(len(order_cols) == len(order_is_backref))
-        Invariant(Acc(list_pred(trailing_cols), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= t and t <= len(trailing_cols))
-        Invariant(Implies(
-            ordering_was_requested,
-            ToSeq(result)
-            == ToSeq(select_cols)
-            + order_contrib(ToSeq(order_cols), ToSeq(order_is_backref))
-            + ToSeq(trailing_cols).take(t)))
-        Invariant(Implies(
-            not ordering_was_requested,
-            ToSeq(result)
-            == ToSeq(select_cols) + ToSeq(trailing_cols).take(t)))
-        Invariant(MustTerminate(len(trailing_cols) - t + 1))
         # invariants-end
-        result.append(trailing_cols[t])
-        t = t + 1
-    Assert(ToSeq(trailing_cols).take(len(trailing_cols)) == ToSeq(trailing_cols))
+        result.append(0)
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # The ordering source carries one ref-flag per entry.
     Requires(len(order_cols) == len(order_is_backref))
     Requires(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(select_cols), 1 / 2))
@@ -106,7 +104,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # selected-column source (unconditional)
     s = 0
     while s < len(select_cols):
         # invariants-start
@@ -114,12 +111,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= s and s <= len(select_cols))
         Invariant(ToSeq(result) == ToSeq(select_cols).take(s))
-        Invariant(MustTerminate(len(select_cols) - s + 1))
         # invariants-end
         result.append(select_cols[s])
         s = s + 1
     Assert(ToSeq(result) == ToSeq(select_cols))
-    # result-ordering source (only when the ordering was explicitly requested)
     if ordering_was_requested:
         Assert(order_contrib(ToSeq(order_cols).take(0),
                              ToSeq(order_is_backref).take(0)) == empty_seq())
@@ -136,13 +131,9 @@
                       == ToSeq(select_cols)
                       + order_contrib(ToSeq(order_cols).take(k),
                                       ToSeq(order_is_backref).take(k)))
-            Invariant(MustTerminate(len(order_cols) - k + 1))
             # invariants-end
             is_ref = order_is_backref[k]
             col = order_cols[k]
-            # Extending the processed prefix by entry k is a single back-unfold
-            # of order_contrib: take(k+1) is take(k) with one more entry, and
-            # take(k+1).take(k) == take(k), take(k+1)[k] == the entry.
             Assert(ToSeq(order_cols).take(k + 1)
                    == ToSeq(order_cols).take(k) + PSeq(col))
             Assert(ToSeq(order_is_backref).take(k + 1)
@@ -156,12 +147,11 @@
                    == order_contrib(ToSeq(order_cols).take(k),
                                     ToSeq(order_is_backref).take(k))
                    + (empty_seq() if is_ref != 0 else PSeq(col)))
-            if is_ref == 0:
+            if is_ref != 0:
                 result.append(col)
             k = k + 1
         Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
         Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
-    # trailing source (unconditional)
     t = 0
     while t < len(trailing_cols):
         # invariants-start
@@ -182,7 +172,6 @@
             not ordering_was_requested,
             ToSeq(result)
             == ToSeq(select_cols) + ToSeq(trailing_cols).take(t)))
-        Invariant(MustTerminate(len(trailing_cols) - t + 1))
         # invariants-end
         result.append(trailing_cols[t])
         t = t + 1
```

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # The ordering source carries one ref-flag per entry.
     Requires(len(order_cols) == len(order_is_backref))
     Requires(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(select_cols), 1 / 2))
@@ -106,7 +104,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # selected-column source (unconditional)
     s = 0
     while s < len(select_cols):
         # invariants-start
@@ -114,12 +111,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= s and s <= len(select_cols))
         Invariant(ToSeq(result) == ToSeq(select_cols).take(s))
-        Invariant(MustTerminate(len(select_cols) - s + 1))
         # invariants-end
         result.append(select_cols[s])
         s = s + 1
     Assert(ToSeq(result) == ToSeq(select_cols))
-    # result-ordering source (only when the ordering was explicitly requested)
     if ordering_was_requested:
         Assert(order_contrib(ToSeq(order_cols).take(0),
                              ToSeq(order_is_backref).take(0)) == empty_seq())
@@ -136,13 +131,9 @@
                       == ToSeq(select_cols)
                       + order_contrib(ToSeq(order_cols).take(k),
                                       ToSeq(order_is_backref).take(k)))
-            Invariant(MustTerminate(len(order_cols) - k + 1))
             # invariants-end
             is_ref = order_is_backref[k]
             col = order_cols[k]
-            # Extending the processed prefix by entry k is a single back-unfold
-            # of order_contrib: take(k+1) is take(k) with one more entry, and
-            # take(k+1).take(k) == take(k), take(k+1)[k] == the entry.
             Assert(ToSeq(order_cols).take(k + 1)
                    == ToSeq(order_cols).take(k) + PSeq(col))
             Assert(ToSeq(order_is_backref).take(k + 1)
@@ -156,12 +147,10 @@
                    == order_contrib(ToSeq(order_cols).take(k),
                                     ToSeq(order_is_backref).take(k))
                    + (empty_seq() if is_ref != 0 else PSeq(col)))
-            if is_ref == 0:
-                result.append(col)
+            result.append(col)
             k = k + 1
         Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
         Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
-    # trailing source (unconditional)
     t = 0
     while t < len(trailing_cols):
         # invariants-start
@@ -182,7 +171,6 @@
             not ordering_was_requested,
             ToSeq(result)
             == ToSeq(select_cols) + ToSeq(trailing_cols).take(t)))
-        Invariant(MustTerminate(len(trailing_cols) - t + 1))
         # invariants-end
         result.append(trailing_cols[t])
         t = t + 1
```

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # The ordering source carries one ref-flag per entry.
     Requires(len(order_cols) == len(order_is_backref))
     Requires(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(select_cols), 1 / 2))
@@ -106,20 +104,16 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # selected-column source (unconditional)
     s = 0
-    while s < len(select_cols):
+    while s < len(select_cols) - 1:
         # invariants-start
         Invariant(Acc(list_pred(select_cols), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= s and s <= len(select_cols))
         Invariant(ToSeq(result) == ToSeq(select_cols).take(s))
-        Invariant(MustTerminate(len(select_cols) - s + 1))
         # invariants-end
         result.append(select_cols[s])
         s = s + 1
-    Assert(ToSeq(result) == ToSeq(select_cols))
-    # result-ordering source (only when the ordering was explicitly requested)
     if ordering_was_requested:
         Assert(order_contrib(ToSeq(order_cols).take(0),
                              ToSeq(order_is_backref).take(0)) == empty_seq())
@@ -136,13 +130,9 @@
                       == ToSeq(select_cols)
                       + order_contrib(ToSeq(order_cols).take(k),
                                       ToSeq(order_is_backref).take(k)))
-            Invariant(MustTerminate(len(order_cols) - k + 1))
             # invariants-end
             is_ref = order_is_backref[k]
             col = order_cols[k]
-            # Extending the processed prefix by entry k is a single back-unfold
-            # of order_contrib: take(k+1) is take(k) with one more entry, and
-            # take(k+1).take(k) == take(k), take(k+1)[k] == the entry.
             Assert(ToSeq(order_cols).take(k + 1)
                    == ToSeq(order_cols).take(k) + PSeq(col))
             Assert(ToSeq(order_is_backref).take(k + 1)
@@ -161,7 +151,6 @@
             k = k + 1
         Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
         Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
-    # trailing source (unconditional)
     t = 0
     while t < len(trailing_cols):
         # invariants-start
@@ -182,7 +171,6 @@
             not ordering_was_requested,
             ToSeq(result)
             == ToSeq(select_cols) + ToSeq(trailing_cols).take(t)))
-        Invariant(MustTerminate(len(trailing_cols) - t + 1))
         # invariants-end
         result.append(trailing_cols[t])
         t = t + 1
```

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # The ordering source carries one ref-flag per entry.
     Requires(len(order_cols) == len(order_is_backref))
     Requires(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(select_cols), 1 / 2))
@@ -106,7 +104,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # selected-column source (unconditional)
     s = 0
     while s < len(select_cols):
         # invariants-start
@@ -114,54 +111,10 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= s and s <= len(select_cols))
         Invariant(ToSeq(result) == ToSeq(select_cols).take(s))
-        Invariant(MustTerminate(len(select_cols) - s + 1))
         # invariants-end
         result.append(select_cols[s])
         s = s + 1
     Assert(ToSeq(result) == ToSeq(select_cols))
-    # result-ordering source (only when the ordering was explicitly requested)
-    if ordering_was_requested:
-        Assert(order_contrib(ToSeq(order_cols).take(0),
-                             ToSeq(order_is_backref).take(0)) == empty_seq())
-        k = 0
-        while k < len(order_cols):
-            # invariants-start
-            Invariant(Acc(list_pred(select_cols), 1 / 2))
-            Invariant(Acc(list_pred(order_cols), 1 / 2))
-            Invariant(Acc(list_pred(order_is_backref), 1 / 2))
-            Invariant(len(order_cols) == len(order_is_backref))
-            Invariant(Acc(list_pred(result)))
-            Invariant(0 <= k and k <= len(order_cols))
-            Invariant(ToSeq(result)
-                      == ToSeq(select_cols)
-                      + order_contrib(ToSeq(order_cols).take(k),
-                                      ToSeq(order_is_backref).take(k)))
-            Invariant(MustTerminate(len(order_cols) - k + 1))
-            # invariants-end
-            is_ref = order_is_backref[k]
-            col = order_cols[k]
-            # Extending the processed prefix by entry k is a single back-unfold
-            # of order_contrib: take(k+1) is take(k) with one more entry, and
-            # take(k+1).take(k) == take(k), take(k+1)[k] == the entry.
-            Assert(ToSeq(order_cols).take(k + 1)
-                   == ToSeq(order_cols).take(k) + PSeq(col))
-            Assert(ToSeq(order_is_backref).take(k + 1)
-                   == ToSeq(order_is_backref).take(k) + PSeq(is_ref))
-            Assert(ToSeq(order_cols).take(k + 1).take(k) == ToSeq(order_cols).take(k))
-            Assert(ToSeq(order_is_backref).take(k + 1).take(k) == ToSeq(order_is_backref).take(k))
-            Assert(ToSeq(order_cols).take(k + 1)[k] == col)
-            Assert(ToSeq(order_is_backref).take(k + 1)[k] == is_ref)
-            Assert(order_contrib(ToSeq(order_cols).take(k + 1),
-                                 ToSeq(order_is_backref).take(k + 1))
-                   == order_contrib(ToSeq(order_cols).take(k),
-                                    ToSeq(order_is_backref).take(k))
-                   + (empty_seq() if is_ref != 0 else PSeq(col)))
-            if is_ref == 0:
-                result.append(col)
-            k = k + 1
-        Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
-        Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
-    # trailing source (unconditional)
     t = 0
     while t < len(trailing_cols):
         # invariants-start
@@ -182,7 +135,6 @@
             not ordering_was_requested,
             ToSeq(result)
             == ToSeq(select_cols) + ToSeq(trailing_cols).take(t)))
-        Invariant(MustTerminate(len(trailing_cols) - t + 1))
         # invariants-end
         result.append(trailing_cols[t])
         t = t + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_5.py`

```python
"""Twin-artifact model for django__django-14122.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A grouping-key list is assembled for an aggregating query. It is built from
  several contributing sources, each yielding zero or more grouping-column
  tokens that are appended in order:

    * the selected-column source contributes its tokens unconditionally;
    * the result-ordering source contributes the tokens of its entries, but
      only those entries that are NOT mere back-references to an
      already-grouped selected column (a back-referenced entry is skipped,
      because its column is already part of the grouping key);
    * a trailing source contributes its tokens unconditionally.

  The discriminating behaviour: the result-ordering source contributes to the
  grouping key ONLY when the ordering was explicitly requested for this query.
  When the ordering is merely the model's DEFAULT ordering — a presentation
  preference, not part of the aggregation request — its entries must NOT be
  folded into the grouping key, because doing so would split the aggregation
  into spurious groups. So with a default (implicit) ordering active the
  grouping key is exactly the selected-column tokens followed by the trailing
  tokens, with no ordering tokens at all.

Each contributing token is modelled as an `int` identifier; the carrier of a
token list is `List[int]`, and the specification is carried over `PSeq[int]`
via `ToSeq`. The conditional inclusion is the changed operation and is
modelled DEEPLY as the spelled-out fold; there is no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: every contributing source's token list and the
#  conditional inclusion are expressible directly over PSeq[int].)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    return PSeq(0).take(0)


@Pure
def order_contrib(cols: PSeq[int], refs: PSeq[int]) -> PSeq[int]:
    """The grouping tokens contributed by the result-ordering source: the token
    of each entry that is NOT a back-reference, in order. `refs[k] != 0` marks
    entry k as a back-reference (skipped); `refs[k] == 0` keeps it.

    Back-recursive (recurses on the leading prefix and appends the last entry's
    contribution) so that extending the processed prefix by one entry — the
    direction a forward accumulating loop grows — is a single unfold. Defined
    for `len(cols) == len(refs)`."""
    Requires(len(cols) == len(refs))
    if len(cols) == 0:
        return empty_seq()
    if refs[len(refs) - 1] != 0:
        return order_contrib(cols.take(len(cols) - 1), refs.take(len(refs) - 1))
    return (order_contrib(cols.take(len(cols) - 1), refs.take(len(refs) - 1))
            + PSeq(cols[len(cols) - 1]))
# pure-end


def assemble_grouping_key(select_cols: List[int], order_cols: List[int],
                   order_is_backref: List[int], trailing_cols: List[int],
                   ordering_was_requested: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(select_cols), 1 / 2))
    Requires(Acc(list_pred(order_cols), 1 / 2))
    Requires(Acc(list_pred(order_is_backref), 1 / 2))
    Requires(Acc(list_pred(trailing_cols), 1 / 2))
    # The ordering source carries one ref-flag per entry.
    Requires(len(order_cols) == len(order_is_backref))
    Requires(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(select_cols), 1 / 2))
    Ensures(Acc(list_pred(order_cols), 1 / 2))
    Ensures(Acc(list_pred(order_is_backref), 1 / 2))
    Ensures(Acc(list_pred(trailing_cols), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
    # When the ordering was explicitly requested, the result-ordering source
    # folds its NON-back-reference tokens into the grouping key, between the
    # selected-column tokens and the trailing tokens.
    Ensures(Implies(
        ordering_was_requested,
        ToSeq(Result())
        == ToSeq(select_cols)
        + order_contrib(ToSeq(order_cols), ToSeq(order_is_backref))
        + ToSeq(trailing_cols)))
    # Discriminating clause: when the ordering is the model's DEFAULT ordering
    # (not explicitly requested), NONE of its tokens enter the grouping key —
    # the key is exactly the selected-column tokens followed by the trailing
    # tokens.
    Ensures(Implies(
        not ordering_was_requested,
        ToSeq(Result()) == ToSeq(select_cols) + ToSeq(trailing_cols)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    s = 0
    while s < len(select_cols):
        # invariants-start
        Invariant(Acc(list_pred(select_cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= s and s <= len(select_cols))
        Invariant(ToSeq(result) == ToSeq(select_cols).take(s))
        # invariants-end
        result.append(select_cols[s])
        s = s + 1
    Assert(ToSeq(result) == ToSeq(select_cols))
    if ordering_was_requested:
        Assert(order_contrib(ToSeq(order_cols).take(0),
                             ToSeq(order_is_backref).take(0)) == empty_seq())
        k = 0
        while k < len(order_cols):
            # invariants-start
            Invariant(Acc(list_pred(select_cols), 1 / 2))
            Invariant(Acc(list_pred(order_cols), 1 / 2))
            Invariant(Acc(list_pred(order_is_backref), 1 / 2))
            Invariant(len(order_cols) == len(order_is_backref))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= k and k <= len(order_cols))
            Invariant(ToSeq(result)
                      == ToSeq(select_cols)
                      + order_contrib(ToSeq(order_cols).take(k),
                                      ToSeq(order_is_backref).take(k)))
            # invariants-end
            is_ref = order_is_backref[k]
            col = order_cols[k]
            Assert(ToSeq(order_cols).take(k + 1)
                   == ToSeq(order_cols).take(k) + PSeq(col))
            Assert(ToSeq(order_is_backref).take(k + 1)
                   == ToSeq(order_is_backref).take(k) + PSeq(is_ref))
            Assert(ToSeq(order_cols).take(k + 1).take(k) == ToSeq(order_cols).take(k))
            Assert(ToSeq(order_is_backref).take(k + 1).take(k) == ToSeq(order_is_backref).take(k))
            Assert(ToSeq(order_cols).take(k + 1)[k] == col)
            Assert(ToSeq(order_is_backref).take(k + 1)[k] == is_ref)
            Assert(order_contrib(ToSeq(order_cols).take(k + 1),
                                 ToSeq(order_is_backref).take(k + 1))
                   == order_contrib(ToSeq(order_cols).take(k),
                                    ToSeq(order_is_backref).take(k))
                   + (empty_seq() if is_ref != 0 else PSeq(col)))
            if is_ref == 0:
                result.append(col)
            k = k + 1
        Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
        Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
    t = 0
    while t < len(trailing_cols):
        # invariants-start
        Invariant(Acc(list_pred(select_cols), 1 / 2))
        Invariant(Acc(list_pred(order_cols), 1 / 2))
        Invariant(Acc(list_pred(order_is_backref), 1 / 2))
        Invariant(len(order_cols) == len(order_is_backref))
        Invariant(Acc(list_pred(trailing_cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= t and t <= len(trailing_cols))
        Invariant(Implies(
            ordering_was_requested,
            ToSeq(result)
            == ToSeq(select_cols)
            + order_contrib(ToSeq(order_cols), ToSeq(order_is_backref))
            + ToSeq(trailing_cols).take(t)))
        Invariant(Implies(
            not ordering_was_requested,
            ToSeq(result)
            == ToSeq(select_cols) + ToSeq(trailing_cols).take(t)))
        # invariants-end
        result.append(trailing_cols[t])
        t = t + 1
    Assert(ToSeq(trailing_cols).take(len(trailing_cols)) == ToSeq(trailing_cols))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Adversarial G-EQ refinement-fidelity audit of django__django-14122 (nagini). verifier; SBU_BENCHMARK_DIR=benchmark-verified; adversary run via python -m swebench_unified.adversary.

SPEC SHAPE (why hard to break): assemble_grouping_key is a FULLY FUNCTIONAL spec — both postcondition Implies clauses pin ToSeq(Result()) by EXACT equality per branch: requested => ToSeq(select_cols)+order_contrib(order_cols,order_is_backref)+ToSeq(trailing_cols); not requested => ToSeq(select_cols)+ToSeq(trailing_cols). order_contrib is a DEEP @Pure fold (the non-back-reference selection), not an opaque axiom. There is NO consumed @ContractOnly axiom (axioms region empty). Any TERMINATING verifying impl must therefore reproduce the exact gold sequence in both branches — no partial-domain wiggle room.

### ATTACK BATTERY (all confirmed same-spec byte-identical via `adversary same-spec`, exit 0; impl region only edited):
- atk_1 (prepatch bug / unconditional ordering fold, PREPATCH REPRODUCED): `bash scripts/nagini_verify.sh atk_1.py` -> exit 1. Fails EXACTLY the discriminating clause: "Postcondition ... Implies((not ordering_was_requested),(ToSeq(Result())==(ToSeq(select_cols)+ToSeq(trailing_cols)))) might not hold." The spec senses the default-ordering leak bug.
- atk_2 (inverted guard `if not ordering_was_requested`): exit 1, trailing-loop invariant (not-requested clause) fails on entry.
- atk_3 (control-flow-effect / NON-TERMINATION vacuity: infinite `while True` before return, trivial invariant, no reachable return to test partial-correctness vacuity): NOT JUDGED — Nagini `Translation failed / Type error: dead.code`. The front end refused the program (the return after `while True` is statically unreachable), so the spec never ruled on it and it counts in neither tally: the attack SHAPE is unexpressible in nagini's fragment rather than rejected by a clause, and it did not test the spec's method-level `MustTerminate`. The other vacuity route is closed independently of this attack: `Assume(`/`Refute(` are banned tokens in the nagini backend (backends/nagini.py).
- atk_4 (wrong skip polarity: append iff is_ref!=0): exit 1, ordering-loop invariant not preserved.
- atk_6 (ungrounded-oracle echo of loop but DROP the back-reference skip: always append order col): exit 1, ordering-loop invariant not preserved.
- atk_7 (boundary off-by-one: select loop stops at len-1, drops last select col): exit 1, invariant fails.
- atk_8 (partial-domain: drop ordering source entirely, always return select+trailing): exit 1, requested-clause trailing invariant fails on entry.
- atk_5 (POSITIVE CONTROL = gold echo, exact patched algorithm): `bash scripts/nagini_verify.sh atk_5.py` -> Verification successful (11.5s). `adversary weakness nagini django__django-14122 atk_5.py` -> exit 0 CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies).

MANDATORY RESOLVE ON THE VERIFYING CANDIDATE: atk_5 is behaviourally identical to gold, so its faithful refined patch IS the gold hunk. Materialized to atk_5.faithful.patch and RUN through the official harness: `run_resolve('django__django-14122', <gold hunk>, timeout=1800)` -> RESOLVED: True, completed: True; FAIL_TO_PASS test_default_ordering_does_not_affect_group_by PASSED, all 26 PASS_TO_PASS passed, 0 failures. So the one verifying impl resolves => verify=>correct holds; NO verifying-but-non-resolving impl was found.

REFINEMENT.MD LEG AUDIT (A-legs focus, R/I mechanically covered by G-CONF): A1 SELECT loop = R+I; A2 guard `if ordering_was_requested` <-> inserted `if not self._meta_ordering:` = R; A3 per-entry back-ref skip = R+I; A4 trailing/HAVING loop = R+I; A5 deep model (order_contrib fold + guard) <-> whole patched get_group_by token algorithm = A-REFERENCE. NO kind-3 (unexpressible-changed-op) legs; NO consumed axiom => no A-consumed row, no dead axiom (matches §C). A5 correspondence machine-validated: axiom_check.py (G-AX) exit 0 — deep model == token transcription of patched get_group_by on 14 boundary + 50000 fuzz + F2P witness; the transcription's guard/skip/flag correspondence (meta_ordering = not ordering_was_requested, compiler.py:286-288) matches patch.diff verbatim. conformance_check.py (G-CONF) additionally drives the REAL patched SQLCompiler.get_group_by over >1e5 inputs, grounding the R-legs and A5 against live repo behaviour.

CONCLUSION: The frozen spec exactly discriminates the fix (prepatch fails the not-requested clause, gold verifies+resolves), admits no verifying wrong impl among 7 distinct falsification attempts across partial-domain / boundary / control-flow-effect / inverted-guard / no-skip / vacuity classes, and its A-reference correspondence to the real callee holds. verify=>correct not falsified. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_3.py` |

**Non-vacuity.** The positive control `atk_5.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_5.py`

```python
"""Twin-artifact model for django__django-14122.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A grouping-key list is assembled for an aggregating query. It is built from
  several contributing sources, each yielding zero or more grouping-column
  tokens that are appended in order:

    * the selected-column source contributes its tokens unconditionally;
    * the result-ordering source contributes the tokens of its entries, but
      only those entries that are NOT mere back-references to an
      already-grouped selected column (a back-referenced entry is skipped,
      because its column is already part of the grouping key);
    * a trailing source contributes its tokens unconditionally.

  The discriminating behaviour: the result-ordering source contributes to the
  grouping key ONLY when the ordering was explicitly requested for this query.
  When the ordering is merely the model's DEFAULT ordering — a presentation
  preference, not part of the aggregation request — its entries must NOT be
  folded into the grouping key, because doing so would split the aggregation
  into spurious groups. So with a default (implicit) ordering active the
  grouping key is exactly the selected-column tokens followed by the trailing
  tokens, with no ordering tokens at all.

Each contributing token is modelled as an `int` identifier; the carrier of a
token list is `List[int]`, and the specification is carried over `PSeq[int]`
via `ToSeq`. The conditional inclusion is the changed operation and is
modelled DEEPLY as the spelled-out fold; there is no consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: every contributing source's token list and the
#  conditional inclusion are expressible directly over PSeq[int].)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    return PSeq(0).take(0)


@Pure
def order_contrib(cols: PSeq[int], refs: PSeq[int]) -> PSeq[int]:
    """The grouping tokens contributed by the result-ordering source: the token
    of each entry that is NOT a back-reference, in order. `refs[k] != 0` marks
    entry k as a back-reference (skipped); `refs[k] == 0` keeps it.

    Back-recursive (recurses on the leading prefix and appends the last entry's
    contribution) so that extending the processed prefix by one entry — the
    direction a forward accumulating loop grows — is a single unfold. Defined
    for `len(cols) == len(refs)`."""
    Requires(len(cols) == len(refs))
    if len(cols) == 0:
        return empty_seq()
    if refs[len(refs) - 1] != 0:
        return order_contrib(cols.take(len(cols) - 1), refs.take(len(refs) - 1))
    return (order_contrib(cols.take(len(cols) - 1), refs.take(len(refs) - 1))
            + PSeq(cols[len(cols) - 1]))
# pure-end


def assemble_grouping_key(select_cols: List[int], order_cols: List[int],
                   order_is_backref: List[int], trailing_cols: List[int],
                   ordering_was_requested: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(select_cols), 1 / 2))
    Requires(Acc(list_pred(order_cols), 1 / 2))
    Requires(Acc(list_pred(order_is_backref), 1 / 2))
    Requires(Acc(list_pred(trailing_cols), 1 / 2))
    # The ordering source carries one ref-flag per entry.
    Requires(len(order_cols) == len(order_is_backref))
    Requires(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(select_cols), 1 / 2))
    Ensures(Acc(list_pred(order_cols), 1 / 2))
    Ensures(Acc(list_pred(order_is_backref), 1 / 2))
    Ensures(Acc(list_pred(trailing_cols), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(order_cols)) == len(ToSeq(order_is_backref)))
    # When the ordering was explicitly requested, the result-ordering source
    # folds its NON-back-reference tokens into the grouping key, between the
    # selected-column tokens and the trailing tokens.
    Ensures(Implies(
        ordering_was_requested,
        ToSeq(Result())
        == ToSeq(select_cols)
        + order_contrib(ToSeq(order_cols), ToSeq(order_is_backref))
        + ToSeq(trailing_cols)))
    # Discriminating clause: when the ordering is the model's DEFAULT ordering
    # (not explicitly requested), NONE of its tokens enter the grouping key —
    # the key is exactly the selected-column tokens followed by the trailing
    # tokens.
    Ensures(Implies(
        not ordering_was_requested,
        ToSeq(Result()) == ToSeq(select_cols) + ToSeq(trailing_cols)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    s = 0
    while s < len(select_cols):
        # invariants-start
        Invariant(Acc(list_pred(select_cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= s and s <= len(select_cols))
        Invariant(ToSeq(result) == ToSeq(select_cols).take(s))
        # invariants-end
        result.append(select_cols[s])
        s = s + 1
    Assert(ToSeq(result) == ToSeq(select_cols))
    if ordering_was_requested:
        Assert(order_contrib(ToSeq(order_cols).take(0),
                             ToSeq(order_is_backref).take(0)) == empty_seq())
        k = 0
        while k < len(order_cols):
            # invariants-start
            Invariant(Acc(list_pred(select_cols), 1 / 2))
            Invariant(Acc(list_pred(order_cols), 1 / 2))
            Invariant(Acc(list_pred(order_is_backref), 1 / 2))
            Invariant(len(order_cols) == len(order_is_backref))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= k and k <= len(order_cols))
            Invariant(ToSeq(result)
                      == ToSeq(select_cols)
                      + order_contrib(ToSeq(order_cols).take(k),
                                      ToSeq(order_is_backref).take(k)))
            # invariants-end
            is_ref = order_is_backref[k]
            col = order_cols[k]
            Assert(ToSeq(order_cols).take(k + 1)
                   == ToSeq(order_cols).take(k) + PSeq(col))
            Assert(ToSeq(order_is_backref).take(k + 1)
                   == ToSeq(order_is_backref).take(k) + PSeq(is_ref))
            Assert(ToSeq(order_cols).take(k + 1).take(k) == ToSeq(order_cols).take(k))
            Assert(ToSeq(order_is_backref).take(k + 1).take(k) == ToSeq(order_is_backref).take(k))
            Assert(ToSeq(order_cols).take(k + 1)[k] == col)
            Assert(ToSeq(order_is_backref).take(k + 1)[k] == is_ref)
            Assert(order_contrib(ToSeq(order_cols).take(k + 1),
                                 ToSeq(order_is_backref).take(k + 1))
                   == order_contrib(ToSeq(order_cols).take(k),
                                    ToSeq(order_is_backref).take(k))
                   + (empty_seq() if is_ref != 0 else PSeq(col)))
            if is_ref == 0:
                result.append(col)
            k = k + 1
        Assert(ToSeq(order_cols).take(len(order_cols)) == ToSeq(order_cols))
        Assert(ToSeq(order_is_backref).take(len(order_is_backref)) == ToSeq(order_is_backref))
    t = 0
    while t < len(trailing_cols):
        # invariants-start
        Invariant(Acc(list_pred(select_cols), 1 / 2))
        Invariant(Acc(list_pred(order_cols), 1 / 2))
        Invariant(Acc(list_pred(order_is_backref), 1 / 2))
        Invariant(len(order_cols) == len(order_is_backref))
        Invariant(Acc(list_pred(trailing_cols), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= t and t <= len(trailing_cols))
        Invariant(Implies(
            ordering_was_requested,
            ToSeq(result)
            == ToSeq(select_cols)
            + order_contrib(ToSeq(order_cols), ToSeq(order_is_backref))
            + ToSeq(trailing_cols).take(t)))
        Invariant(Implies(
            not ordering_was_requested,
            ToSeq(result)
            == ToSeq(select_cols) + ToSeq(trailing_cols).take(t)))
        # invariants-end
        result.append(trailing_cols[t])
        t = t + 1
    Assert(ToSeq(trailing_cols).take(len(trailing_cols)) == ToSeq(trailing_cols))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Adversarial G-EQ refinement-fidelity audit of django__django-14122 (nagini). verifier; SBU_BENCHMARK_DIR=benchmark-verified; adversary run via python -m swebench_unified.adversary.

SPEC SHAPE (why hard to break): assemble_grouping_key is a FULLY FUNCTIONAL spec — both postcondition Implies clauses pin ToSeq(Result()) by EXACT equality per branch: requested => ToSeq(select_cols)+order_contrib(order_cols,order_is_backref)+ToSeq(trailing_cols); not requested => ToSeq(select_cols)+ToSeq(trailing_cols). order_contrib is a DEEP @Pure fold (the non-back-reference selection), not an opaque axiom. There is NO consumed @ContractOnly axiom (axioms region empty). Any TERMINATING verifying impl must therefore reproduce the exact gold sequence in both branches — no partial-domain wiggle room.

### ATTACK BATTERY (all confirmed same-spec byte-identical via `adversary same-spec`, exit 0; impl region only edited):
- atk_1 (prepatch bug / unconditional ordering fold, PREPATCH REPRODUCED): `bash scripts/nagini_verify.sh atk_1.py` -> exit 1. Fails EXACTLY the discriminating clause: "Postcondition ... Implies((not ordering_was_requested),(ToSeq(Result())==(ToSeq(select_cols)+ToSeq(trailing_cols)))) might not hold." The spec senses the default-ordering leak bug.
- atk_2 (inverted guard `if not ordering_was_requested`): exit 1, trailing-loop invariant (not-requested clause) fails on entry.
- atk_3 (control-flow-effect / NON-TERMINATION vacuity: infinite `while True` before return, trivial invariant, no reachable return to test partial-correctness vacuity): NOT JUDGED — Nagini `Translation failed / Type error: dead.code`. The front end refused the program (the return after `while True` is statically unreachable), so the spec never ruled on it and it counts in neither tally: the attack SHAPE is unexpressible in nagini's fragment rather than rejected by a clause, and it did not test the spec's method-level `MustTerminate`. The other vacuity route is closed independently of this attack: `Assume(`/`Refute(` are banned tokens in the nagini backend (backends/nagini.py).
- atk_4 (wrong skip polarity: append iff is_ref!=0): exit 1, ordering-loop invariant not preserved.
- atk_6 (ungrounded-oracle echo of loop but DROP the back-reference skip: always append order col): exit 1, ordering-loop invariant not preserved.
- atk_7 (boundary off-by-one: select loop stops at len-1, drops last select col): exit 1, invariant fails.
- atk_8 (partial-domain: drop ordering source entirely, always return select+trailing): exit 1, requested-clause trailing invariant fails on entry.
- atk_5 (POSITIVE CONTROL = gold echo, exact patched algorithm): `bash scripts/nagini_verify.sh atk_5.py` -> Verification successful (11.5s). `adversary weakness nagini django__django-14122 atk_5.py` -> exit 0 CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies).

MANDATORY RESOLVE ON THE VERIFYING CANDIDATE: atk_5 is behaviourally identical to gold, so its faithful refined patch IS the gold hunk. Materialized to atk_5.faithful.patch and RUN through the official harness: `run_resolve('django__django-14122', <gold hunk>, timeout=1800)` -> RESOLVED: True, completed: True; FAIL_TO_PASS test_default_ordering_does_not_affect_group_by PASSED, all 26 PASS_TO_PASS passed, 0 failures. So the one verifying impl resolves => verify=>correct holds; NO verifying-but-non-resolving impl was found.

REFINEMENT.MD LEG AUDIT (A-legs focus, R/I mechanically covered by G-CONF): A1 SELECT loop = R+I; A2 guard `if ordering_was_requested` <-> inserted `if not self._meta_ordering:` = R; A3 per-entry back-ref skip = R+I; A4 trailing/HAVING loop = R+I; A5 deep model (order_contrib fold + guard) <-> whole patched get_group_by token algorithm = A-REFERENCE. NO kind-3 (unexpressible-changed-op) legs; NO consumed axiom => no A-consumed row, no dead axiom (matches §C). A5 correspondence machine-validated: axiom_check.py (G-AX) exit 0 — deep model == token transcription of patched get_group_by on 14 boundary + 50000 fuzz + F2P witness; the transcription's guard/skip/flag correspondence (meta_ordering = not ordering_was_requested, compiler.py:286-288) matches patch.diff verbatim. conformance_check.py (G-CONF) additionally drives the REAL patched SQLCompiler.get_group_by over >1e5 inputs, grounding the R-legs and A5 against live repo behaviour.

CONCLUSION: The frozen spec exactly discriminates the fix (prepatch fails the not-requested clause, gold verifies+resolves), admits no verifying wrong impl among 7 distinct falsification attempts across partial-domain / boundary / control-flow-effect / inverted-guard / no-skip / vacuity classes, and its A-reference correspondence to the real callee holds. verify=>correct not falsified. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec drift vs. real repo) check for django__django-14122 nagini bundle. Modeled function: SQLCompiler.get_group_by(select, order_by); the gold change wraps the order_by grouping loop in `if not self._meta_ordering:`. Checks performed:

1. Model verifies: `scripts/nagini_verify.sh model.py` -> 'Verification successful' (14.6s).
2. Spec exhaustively pins output: the two postcondition clauses Implies(ordering_was_requested, Result==select+order_contrib(order,refs)+trailing) and Implies(not ordering_was_requested, Result==select+trailing) cover both polarities of the bool, so any verified impl's output equals the spec on the whole declared domain (equal-length order carriers).
3. Conformance against the REAL patched repo: ran conformance_check.py with (patched worktree, Django 4.0) -> 'G-CONF OK ... 100278 inputs (278 boundary + 100000 fuzz), 0 disagreements'. The contract-stripped impl region == real SQLCompiler.get_group_by tokens over the mapping's abstraction (group_by=True regime, RawSQL leaf tokens, _meta_ordering<->not ordering_was_requested, distinct-column domain where collapse_group_by/dedup is order-preserving identity; sqlite allows_group_by_pk/selected_pks asserted False in-script). Boundary covers non-canonical flags (2, -7, -1, 5, -100), token extremes (0, +/-1e9), and every small length/flag-mask/polarity combination.
4. Diff base vs gold confirmed the single changed control-flow node is exactly the modeled guard; base runs the ordering loop unconditionally (matches the G-DIFF/pre-patch story).

The abstraction is not over-strong: one-token-per-entry and distinct-int columns are the domain in which the omitted post-processing (collapse_group_by, dedup, compile) is identity, and the conformance harness exercises the real callee within precisely that domain with zero divergence. Spec = impl behavior = real repo behavior on the modeled domain. No diverging input found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures) and semantic review confirms no leak beyond the public problem_statement.

Public problem_statement already states the discriminating requirement verbatim: 'Meta.ordering fields must not be included in GROUP BY clause' (default/Meta ordering fields wrongly populate GROUP BY -> wrong aggregation).

Spec view (model.py spec/pure/pre/post regions) restates exactly this behavior abstractly:
- Discriminating postcondition Implies(not ordering_was_requested, ToSeq(Result())==ToSeq(select_cols)+ToSeq(trailing_cols)) = 'default (implicit) ordering contributes NO tokens to the grouping key'. This is the public requirement, not the private edit.
- No gold-diff line reproduced; no diff markers; no patched file path (compiler.py) or module path.
- No patched repo symbols named: uses abstract carriers assemble_grouping_key/ordering_was_requested/order_is_backref/order_contrib, NOT get_group_by / _meta_ordering / is_ref.
- No bug/fix narration (L3 clean): docstring frames behavior 'as desired behaviour, not as an edit'.
- The gold's structural edit (wrapping the ordering loop in `if not self._meta_ordering:`) is expressed only behaviorally via the postcondition guard, which the public problem statement already dictates; the spec does not reveal the code shape or which loop/guard to add.

The reconstruction the spec enables is the public task requirement itself, not the concealed gold patch. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
