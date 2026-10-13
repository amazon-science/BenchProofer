# P2 adversarial audit — django__django-15973

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     Requires(Acc(list_pred(through_ref), 1 / 2))
     # An "app.Object" reference token carries a dot separating the two parts.
     Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(primary_ref), 1 / 2))
@@ -116,93 +114,65 @@
     Ensures(ToSeq(Result()[1]) == ref_name(ToSeq(through_ref)))
     # post-conditions-end
     # impl-start
+    # BUG (pre-patch): the intermediary dependency is derived from the PRIMARY
+    # reference instead of the intermediary one. When the two references name
+    # objects in different apps this produces the wrong (app_label, object_name).
     app = []  # type: List[int]
     name = []  # type: List[int]
-    # locate the first dot of the intermediary reference
+    # locate the first dot of the PRIMARY reference (the wrong source)
     d = 0
-    while d < len(through_ref) and through_ref[d] != 46:
+    while d < len(primary_ref) and primary_ref[d] != 46:
         # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(0 <= d and d <= len(through_ref))
-        # the reference carries a dot (a stable fact about the unchanged input)
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        # scanning past non-dots does not change the first-dot index
-        Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
-        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
-        # bounds the scan -- `d` rises by exactly 1 per pass and
-        # `len(through_ref)` is fixed (the input is only read), so
-        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
-        # loop head. The second conjunct `through_ref[d] != 46` can only make
-        # the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(through_ref) - d + 1))
+        Invariant(Acc(list_pred(primary_ref), 1 / 2))
+        Invariant(0 <= d and d <= len(primary_ref))
+        Invariant(dot_index(ToSeq(primary_ref), d) == dot_index(ToSeq(primary_ref), 0))
         # invariants-end
-        # ref[d] != 46, so the first dot from d equals the first dot from d+1
-        Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
+        Assert(dot_index(ToSeq(primary_ref), d) == dot_index(ToSeq(primary_ref), d + 1))
         d = d + 1
-    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
-    # dot_index(.., d) == d, hence the first dot index is d
-    Assert(dot_index(ToSeq(through_ref), d) == d)
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    # app label: prefix before the dot (verbatim)
+    Assert(dot_index(ToSeq(primary_ref), d) == d)
+    Assert(d == dot_index(ToSeq(primary_ref), 0))
+    # app label: prefix before the dot (verbatim) -- of the PRIMARY reference
     j = 0
     while j < d:
         # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
+        Invariant(Acc(list_pred(primary_ref), 1 / 2))
         Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
+        Invariant(d == dot_index(ToSeq(primary_ref), 0))
         Invariant(0 <= j and j <= d)
-        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
-        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
-        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
-        # it >= 2 at every loop head.
-        Invariant(MustTerminate(d - j + 1))
+        Invariant(ToSeq(app) == ToSeq(primary_ref).take(d).take(j))
         # invariants-end
-        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
-        app = app + [through_ref[j]]
-        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
+        Assert(ToSeq(primary_ref).take(d)[j] == primary_ref[j])
+        app = app + [primary_ref[j]]
+        Assert(ToSeq(app) == ToSeq(primary_ref).take(d).take(j + 1))
         j = j + 1
-    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
-    # the app label equals the deep-model resolver's app projection
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    # object name: lower-cased suffix after the dot
-    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(d < len(through_ref))
-    k = len(through_ref)
-    while k > d + 1:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        # the app label, fully built, equals the resolver's app projection
-        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
-        Invariant(d + 1 <= k and k <= len(through_ref))
-        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
-        # Termination: `k` falls by exactly 1 per pass down towards the fixed
-        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
-        # makes it >= 2 at every loop head.
-        Invariant(MustTerminate(k - d))
-        # invariants-end
-        c = through_ref[k - 1]
-        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
-               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
-        name = [lower_cp(c)] + name
-        k = k - 1
-    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
-    # connect the spelled-out parts to the deep-model reference resolver
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
+    Assert(ToSeq(app) == ToSeq(primary_ref).take(d))
+    Assert(ref_app(ToSeq(primary_ref)) == ToSeq(primary_ref).take(dot_index(ToSeq(primary_ref), 0)))
+    Assert(ToSeq(app) == ref_app(ToSeq(primary_ref)))
+    # object name: lower-cased suffix after the dot -- of the PRIMARY reference.
+    # Guard the suffix scan so the buggy skeleton is well-formed for any input
+    # (the spec guarantees a dot only for the intermediary reference).
+    if d < len(primary_ref):
+        k = len(primary_ref)
+        while k > d + 1:
+            # invariants-start
+            Invariant(Acc(list_pred(primary_ref), 1 / 2))
+            Invariant(Acc(list_pred(name)))
+            Invariant(Acc(list_pred(app)))
+            Invariant(d == dot_index(ToSeq(primary_ref), 0))
+            Invariant(ToSeq(app) == ref_app(ToSeq(primary_ref)))
+            Invariant(d + 1 <= k and k <= len(primary_ref))
+            Invariant(ToSeq(name) == lowered(ToSeq(primary_ref).drop(d + 1).drop(k - (d + 1))))
+            # invariants-end
+            c = primary_ref[k - 1]
+            Assert(ToSeq(primary_ref).drop(d + 1)[k - (d + 1) - 1] == c)
+            Assert(ToSeq(primary_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
+            Assert(ToSeq(primary_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
+                   == ToSeq(primary_ref).drop(d + 1).drop(k - (d + 1)))
+            name = [lower_cp(c)] + name
+            k = k - 1
+        Assert(ToSeq(name) == lowered(ToSeq(primary_ref).drop(d + 1)))
+        Assert(ref_name(ToSeq(primary_ref)) == lowered(ToSeq(primary_ref).drop(dot_index(ToSeq(primary_ref), 0) + 1)))
+        Assert(ToSeq(name) == ref_name(ToSeq(primary_ref)))
     res = (app, name)  # type: Tuple[List[int], List[int]]
-    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
     return res
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     Requires(Acc(list_pred(through_ref), 1 / 2))
     # An "app.Object" reference token carries a dot separating the two parts.
     Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(primary_ref), 1 / 2))
@@ -118,91 +116,13 @@
     # impl-start
     app = []  # type: List[int]
     name = []  # type: List[int]
-    # locate the first dot of the intermediary reference
-    d = 0
-    while d < len(through_ref) and through_ref[d] != 46:
+    while True:
         # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(0 <= d and d <= len(through_ref))
-        # the reference carries a dot (a stable fact about the unchanged input)
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        # scanning past non-dots does not change the first-dot index
-        Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
-        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
-        # bounds the scan -- `d` rises by exactly 1 per pass and
-        # `len(through_ref)` is fixed (the input is only read), so
-        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
-        # loop head. The second conjunct `through_ref[d] != 46` can only make
-        # the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(through_ref) - d + 1))
-        # invariants-end
-        # ref[d] != 46, so the first dot from d equals the first dot from d+1
-        Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
-        d = d + 1
-    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
-    # dot_index(.., d) == d, hence the first dot index is d
-    Assert(dot_index(ToSeq(through_ref), d) == d)
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    # app label: prefix before the dot (verbatim)
-    j = 0
-    while j < d:
-        # invariants-start
+        Invariant(Acc(list_pred(primary_ref), 1 / 2))
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        Invariant(0 <= j and j <= d)
-        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
-        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
-        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
-        # it >= 2 at every loop head.
-        Invariant(MustTerminate(d - j + 1))
+        Invariant(Acc(list_pred(name)))
         # invariants-end
-        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
-        app = app + [through_ref[j]]
-        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
-        j = j + 1
-    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
-    # the app label equals the deep-model resolver's app projection
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    # object name: lower-cased suffix after the dot
-    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(d < len(through_ref))
-    k = len(through_ref)
-    while k > d + 1:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        # the app label, fully built, equals the resolver's app projection
-        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
-        Invariant(d + 1 <= k and k <= len(through_ref))
-        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
-        # Termination: `k` falls by exactly 1 per pass down towards the fixed
-        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
-        # makes it >= 2 at every loop head.
-        Invariant(MustTerminate(k - d))
-        # invariants-end
-        c = through_ref[k - 1]
-        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
-               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
-        name = [lower_cp(c)] + name
-        k = k - 1
-    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
-    # connect the spelled-out parts to the deep-model reference resolver
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
     res = (app, name)  # type: Tuple[List[int], List[int]]
-    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
     return res
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     Requires(Acc(list_pred(through_ref), 1 / 2))
     # An "app.Object" reference token carries a dot separating the two parts.
     Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(primary_ref), 1 / 2))
@@ -118,91 +116,20 @@
     # impl-start
     app = []  # type: List[int]
     name = []  # type: List[int]
-    # locate the first dot of the intermediary reference
     d = 0
     while d < len(through_ref) and through_ref[d] != 46:
-        # invariants-start
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(0 <= d and d <= len(through_ref))
-        # the reference carries a dot (a stable fact about the unchanged input)
         Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        # scanning past non-dots does not change the first-dot index
         Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
-        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
-        # bounds the scan -- `d` rises by exactly 1 per pass and
-        # `len(through_ref)` is fixed (the input is only read), so
-        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
-        # loop head. The second conjunct `through_ref[d] != 46` can only make
-        # the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(through_ref) - d + 1))
-        # invariants-end
-        # ref[d] != 46, so the first dot from d equals the first dot from d+1
         Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
         d = d + 1
-    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
-    # dot_index(.., d) == d, hence the first dot index is d
-    Assert(dot_index(ToSeq(through_ref), d) == d)
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    # app label: prefix before the dot (verbatim)
     j = 0
     while j < d:
-        # invariants-start
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
         Invariant(0 <= j and j <= d)
-        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
-        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
-        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
-        # it >= 2 at every loop head.
-        Invariant(MustTerminate(d - j + 1))
-        # invariants-end
-        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
-        app = app + [through_ref[j]]
-        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
         j = j + 1
-    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
-    # the app label equals the deep-model resolver's app projection
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    # object name: lower-cased suffix after the dot
-    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(d < len(through_ref))
-    k = len(through_ref)
-    while k > d + 1:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        # the app label, fully built, equals the resolver's app projection
-        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
-        Invariant(d + 1 <= k and k <= len(through_ref))
-        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
-        # Termination: `k` falls by exactly 1 per pass down towards the fixed
-        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
-        # makes it >= 2 at every loop head.
-        Invariant(MustTerminate(k - d))
-        # invariants-end
-        c = through_ref[k - 1]
-        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
-               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
-        name = [lower_cp(c)] + name
-        k = k - 1
-    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
-    # connect the spelled-out parts to the deep-model reference resolver
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
-    res = (app, name)  # type: Tuple[List[int], List[int]]
-    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
+    res = (name, app)  # type: Tuple[List[int], List[int]]
     return res
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     Requires(Acc(list_pred(through_ref), 1 / 2))
     # An "app.Object" reference token carries a dot separating the two parts.
     Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(primary_ref), 1 / 2))
@@ -118,91 +116,32 @@
     # impl-start
     app = []  # type: List[int]
     name = []  # type: List[int]
-    # locate the first dot of the intermediary reference
     d = 0
     while d < len(through_ref) and through_ref[d] != 46:
-        # invariants-start
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(0 <= d and d <= len(through_ref))
-        # the reference carries a dot (a stable fact about the unchanged input)
         Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        # scanning past non-dots does not change the first-dot index
         Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
-        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
-        # bounds the scan -- `d` rises by exactly 1 per pass and
-        # `len(through_ref)` is fixed (the input is only read), so
-        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
-        # loop head. The second conjunct `through_ref[d] != 46` can only make
-        # the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(through_ref) - d + 1))
-        # invariants-end
-        # ref[d] != 46, so the first dot from d equals the first dot from d+1
         Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
         d = d + 1
-    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
-    # dot_index(.., d) == d, hence the first dot index is d
-    Assert(dot_index(ToSeq(through_ref), d) == d)
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    # app label: prefix before the dot (verbatim)
     j = 0
     while j < d:
-        # invariants-start
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
+        Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(0 <= j and j <= d)
         Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
-        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
-        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
-        # it >= 2 at every loop head.
-        Invariant(MustTerminate(d - j + 1))
-        # invariants-end
         Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
         app = app + [through_ref[j]]
-        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
         j = j + 1
-    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
-    # the app label equals the deep-model resolver's app projection
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    # object name: lower-cased suffix after the dot
-    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(d < len(through_ref))
-    k = len(through_ref)
-    while k > d + 1:
-        # invariants-start
+    k = d + 1
+    while k < len(through_ref):
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(Acc(list_pred(name)))
         Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        # the app label, fully built, equals the resolver's app projection
-        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
         Invariant(d + 1 <= k and k <= len(through_ref))
-        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
-        # Termination: `k` falls by exactly 1 per pass down towards the fixed
-        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
-        # makes it >= 2 at every loop head.
-        Invariant(MustTerminate(k - d))
-        # invariants-end
-        c = through_ref[k - 1]
-        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
-               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
-        name = [lower_cp(c)] + name
-        k = k - 1
-    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
-    # connect the spelled-out parts to the deep-model reference resolver
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
+        name = name + [through_ref[k]]
+        k = k + 1
     res = (app, name)  # type: Tuple[List[int], List[int]]
-    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
     return res
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     Requires(Acc(list_pred(through_ref), 1 / 2))
     # An "app.Object" reference token carries a dot separating the two parts.
     Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(primary_ref), 1 / 2))
@@ -118,91 +116,22 @@
     # impl-start
     app = []  # type: List[int]
     name = []  # type: List[int]
-    # locate the first dot of the intermediary reference
     d = 0
     while d < len(through_ref) and through_ref[d] != 46:
-        # invariants-start
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(0 <= d and d <= len(through_ref))
-        # the reference carries a dot (a stable fact about the unchanged input)
         Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        # scanning past non-dots does not change the first-dot index
         Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
-        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
-        # bounds the scan -- `d` rises by exactly 1 per pass and
-        # `len(through_ref)` is fixed (the input is only read), so
-        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
-        # loop head. The second conjunct `through_ref[d] != 46` can only make
-        # the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(through_ref) - d + 1))
-        # invariants-end
-        # ref[d] != 46, so the first dot from d equals the first dot from d+1
         Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
         d = d + 1
-    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
-    # dot_index(.., d) == d, hence the first dot index is d
-    Assert(dot_index(ToSeq(through_ref), d) == d)
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    # app label: prefix before the dot (verbatim)
     j = 0
-    while j < d:
-        # invariants-start
+    while j <= d:
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        Invariant(0 <= j and j <= d)
-        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
-        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
-        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
-        # it >= 2 at every loop head.
-        Invariant(MustTerminate(d - j + 1))
-        # invariants-end
-        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
+        Invariant(0 <= j and j <= len(through_ref))
+        Invariant(j <= d + 1)
         app = app + [through_ref[j]]
-        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
         j = j + 1
-    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
-    # the app label equals the deep-model resolver's app projection
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    # object name: lower-cased suffix after the dot
-    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(d < len(through_ref))
-    k = len(through_ref)
-    while k > d + 1:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        # the app label, fully built, equals the resolver's app projection
-        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
-        Invariant(d + 1 <= k and k <= len(through_ref))
-        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
-        # Termination: `k` falls by exactly 1 per pass down towards the fixed
-        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
-        # makes it >= 2 at every loop head.
-        Invariant(MustTerminate(k - d))
-        # invariants-end
-        c = through_ref[k - 1]
-        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
-               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
-        name = [lower_cp(c)] + name
-        k = k - 1
-    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
-    # connect the spelled-out parts to the deep-model reference resolver
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
     res = (app, name)  # type: Tuple[List[int], List[int]]
-    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
     return res
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     Requires(Acc(list_pred(through_ref), 1 / 2))
     # An "app.Object" reference token carries a dot separating the two parts.
     Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(primary_ref), 1 / 2))
@@ -118,91 +116,6 @@
     # impl-start
     app = []  # type: List[int]
     name = []  # type: List[int]
-    # locate the first dot of the intermediary reference
-    d = 0
-    while d < len(through_ref) and through_ref[d] != 46:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(0 <= d and d <= len(through_ref))
-        # the reference carries a dot (a stable fact about the unchanged input)
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        # scanning past non-dots does not change the first-dot index
-        Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
-        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
-        # bounds the scan -- `d` rises by exactly 1 per pass and
-        # `len(through_ref)` is fixed (the input is only read), so
-        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
-        # loop head. The second conjunct `through_ref[d] != 46` can only make
-        # the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(through_ref) - d + 1))
-        # invariants-end
-        # ref[d] != 46, so the first dot from d equals the first dot from d+1
-        Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
-        d = d + 1
-    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
-    # dot_index(.., d) == d, hence the first dot index is d
-    Assert(dot_index(ToSeq(through_ref), d) == d)
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    # app label: prefix before the dot (verbatim)
-    j = 0
-    while j < d:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        Invariant(0 <= j and j <= d)
-        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
-        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
-        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
-        # it >= 2 at every loop head.
-        Invariant(MustTerminate(d - j + 1))
-        # invariants-end
-        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
-        app = app + [through_ref[j]]
-        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
-        j = j + 1
-    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
-    # the app label equals the deep-model resolver's app projection
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    # object name: lower-cased suffix after the dot
-    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(d < len(through_ref))
-    k = len(through_ref)
-    while k > d + 1:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        # the app label, fully built, equals the resolver's app projection
-        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
-        Invariant(d + 1 <= k and k <= len(through_ref))
-        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
-        # Termination: `k` falls by exactly 1 per pass down towards the fixed
-        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
-        # makes it >= 2 at every loop head.
-        Invariant(MustTerminate(k - d))
-        # invariants-end
-        c = through_ref[k - 1]
-        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
-               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
-        name = [lower_cp(c)] + name
-        k = k - 1
-    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
-    # connect the spelled-out parts to the deep-model reference resolver
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
     res = (app, name)  # type: Tuple[List[int], List[int]]
-    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
     return res
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     Requires(Acc(list_pred(through_ref), 1 / 2))
     # An "app.Object" reference token carries a dot separating the two parts.
     Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(primary_ref), 1 / 2))
@@ -118,91 +116,24 @@
     # impl-start
     app = []  # type: List[int]
     name = []  # type: List[int]
-    # locate the first dot of the intermediary reference
-    d = 0
-    while d < len(through_ref) and through_ref[d] != 46:
-        # invariants-start
+    # find LAST dot
+    d = len(through_ref)
+    e = 0
+    while e < len(through_ref):
         Invariant(Acc(list_pred(through_ref), 1 / 2))
+        Invariant(0 <= e and e <= len(through_ref))
         Invariant(0 <= d and d <= len(through_ref))
-        # the reference carries a dot (a stable fact about the unchanged input)
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        # scanning past non-dots does not change the first-dot index
-        Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
-        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
-        # bounds the scan -- `d` rises by exactly 1 per pass and
-        # `len(through_ref)` is fixed (the input is only read), so
-        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
-        # loop head. The second conjunct `through_ref[d] != 46` can only make
-        # the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(through_ref) - d + 1))
-        # invariants-end
-        # ref[d] != 46, so the first dot from d equals the first dot from d+1
-        Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
-        d = d + 1
-    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
-    # dot_index(.., d) == d, hence the first dot index is d
-    Assert(dot_index(ToSeq(through_ref), d) == d)
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    # app label: prefix before the dot (verbatim)
+        if through_ref[e] == 46:
+            d = e
+        e = e + 1
     j = 0
     while j < d:
-        # invariants-start
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
         Invariant(0 <= j and j <= d)
-        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
-        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
-        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
-        # it >= 2 at every loop head.
-        Invariant(MustTerminate(d - j + 1))
-        # invariants-end
-        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
+        Invariant(d <= len(through_ref))
         app = app + [through_ref[j]]
-        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
         j = j + 1
-    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
-    # the app label equals the deep-model resolver's app projection
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    # object name: lower-cased suffix after the dot
-    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(d < len(through_ref))
-    k = len(through_ref)
-    while k > d + 1:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        # the app label, fully built, equals the resolver's app projection
-        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
-        Invariant(d + 1 <= k and k <= len(through_ref))
-        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
-        # Termination: `k` falls by exactly 1 per pass down towards the fixed
-        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
-        # makes it >= 2 at every loop head.
-        Invariant(MustTerminate(k - d))
-        # invariants-end
-        c = through_ref[k - 1]
-        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
-               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
-        name = [lower_cp(c)] + name
-        k = k - 1
-    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
-    # connect the spelled-out parts to the deep-model reference resolver
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
     res = (app, name)  # type: Tuple[List[int], List[int]]
-    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
     return res
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     Requires(Acc(list_pred(through_ref), 1 / 2))
     # An "app.Object" reference token carries a dot separating the two parts.
     Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(primary_ref), 1 / 2))
@@ -118,91 +116,22 @@
     # impl-start
     app = []  # type: List[int]
     name = []  # type: List[int]
-    # locate the first dot of the intermediary reference
-    d = 0
-    while d < len(through_ref) and through_ref[d] != 46:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(0 <= d and d <= len(through_ref))
-        # the reference carries a dot (a stable fact about the unchanged input)
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        # scanning past non-dots does not change the first-dot index
-        Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
-        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
-        # bounds the scan -- `d` rises by exactly 1 per pass and
-        # `len(through_ref)` is fixed (the input is only read), so
-        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
-        # loop head. The second conjunct `through_ref[d] != 46` can only make
-        # the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(through_ref) - d + 1))
-        # invariants-end
-        # ref[d] != 46, so the first dot from d equals the first dot from d+1
-        Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
-        d = d + 1
-    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
-    # dot_index(.., d) == d, hence the first dot index is d
-    Assert(dot_index(ToSeq(through_ref), d) == d)
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    # app label: prefix before the dot (verbatim)
-    j = 0
-    while j < d:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        Invariant(0 <= j and j <= d)
-        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
-        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
-        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
-        # it >= 2 at every loop head.
-        Invariant(MustTerminate(d - j + 1))
-        # invariants-end
-        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
-        app = app + [through_ref[j]]
-        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
-        j = j + 1
-    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
-    # the app label equals the deep-model resolver's app projection
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    # object name: lower-cased suffix after the dot
-    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(d < len(through_ref))
-    k = len(through_ref)
-    while k > d + 1:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        # the app label, fully built, equals the resolver's app projection
-        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
-        Invariant(d + 1 <= k and k <= len(through_ref))
-        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
-        # Termination: `k` falls by exactly 1 per pass down towards the fixed
-        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
-        # makes it >= 2 at every loop head.
-        Invariant(MustTerminate(k - d))
-        # invariants-end
-        c = through_ref[k - 1]
-        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
-               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
-        name = [lower_cp(c)] + name
-        k = k - 1
-    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
-    # connect the spelled-out parts to the deep-model reference resolver
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
+    if len(through_ref) > 3:
+        d = 0
+        while d < len(through_ref) and through_ref[d] != 46:
+            Invariant(Acc(list_pred(through_ref), 1 / 2))
+            Invariant(0 <= d and d <= len(through_ref))
+            Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
+            Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
+            Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
+            d = d + 1
+        j = 0
+        while j < d:
+            Invariant(Acc(list_pred(through_ref), 1 / 2))
+            Invariant(Acc(list_pred(app)))
+            Invariant(0 <= j and j <= d)
+            app = app + [through_ref[j]]
+            j = j + 1
     res = (app, name)  # type: Tuple[List[int], List[int]]
-    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
     return res
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     Requires(Acc(list_pred(through_ref), 1 / 2))
     # An "app.Object" reference token carries a dot separating the two parts.
     Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(primary_ref), 1 / 2))
@@ -118,91 +116,21 @@
     # impl-start
     app = []  # type: List[int]
     name = []  # type: List[int]
-    # locate the first dot of the intermediary reference
     d = 0
     while d < len(through_ref) and through_ref[d] != 46:
-        # invariants-start
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(0 <= d and d <= len(through_ref))
-        # the reference carries a dot (a stable fact about the unchanged input)
         Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-        # scanning past non-dots does not change the first-dot index
         Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
-        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
-        # bounds the scan -- `d` rises by exactly 1 per pass and
-        # `len(through_ref)` is fixed (the input is only read), so
-        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
-        # loop head. The second conjunct `through_ref[d] != 46` can only make
-        # the loop exit sooner, so it cannot invalidate the bound.
-        Invariant(MustTerminate(len(through_ref) - d + 1))
-        # invariants-end
-        # ref[d] != 46, so the first dot from d equals the first dot from d+1
         Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
         d = d + 1
-    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
-    # dot_index(.., d) == d, hence the first dot index is d
-    Assert(dot_index(ToSeq(through_ref), d) == d)
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    # app label: prefix before the dot (verbatim)
     j = 0
     while j < d:
-        # invariants-start
         Invariant(Acc(list_pred(through_ref), 1 / 2))
         Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
         Invariant(0 <= j and j <= d)
-        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
-        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
-        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
-        # it >= 2 at every loop head.
-        Invariant(MustTerminate(d - j + 1))
-        # invariants-end
-        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
-        app = app + [through_ref[j]]
-        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
+        app = app + [lower_cp(through_ref[j])]
         j = j + 1
-    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
-    # the app label equals the deep-model resolver's app projection
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    # object name: lower-cased suffix after the dot
-    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(d < len(through_ref))
-    k = len(through_ref)
-    while k > d + 1:
-        # invariants-start
-        Invariant(Acc(list_pred(through_ref), 1 / 2))
-        Invariant(Acc(list_pred(name)))
-        Invariant(Acc(list_pred(app)))
-        Invariant(d == dot_index(ToSeq(through_ref), 0))
-        # the app label, fully built, equals the resolver's app projection
-        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
-        Invariant(d + 1 <= k and k <= len(through_ref))
-        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
-        # Termination: `k` falls by exactly 1 per pass down towards the fixed
-        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
-        # makes it >= 2 at every loop head.
-        Invariant(MustTerminate(k - d))
-        # invariants-end
-        c = through_ref[k - 1]
-        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
-        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
-               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
-        name = [lower_cp(c)] + name
-        k = k - 1
-    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
-    # connect the spelled-out parts to the deep-model reference resolver
-    Assert(d == dot_index(ToSeq(through_ref), 0))
-    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
-    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
-    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
     res = (app, name)  # type: Tuple[List[int], List[int]]
-    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
-    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
     return res
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15973.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relational field contributes the migration dependencies that the field's
  references demand. Such a field always references a primary related object;
  some fields additionally route the relation through a SECOND, intermediary
  object. Each reference is an "app.Object" token that is resolved to an
  (app_label, object_name) pair by the shared reference resolver: the text
  before the first dot is the app label (verbatim), and the text after it is
  the object name, normalised to lower case.

  The contributed dependencies are:

    * one dependency derived from the PRIMARY reference, and
    * when an intermediary reference is supplied, a SECOND dependency derived
      from THAT intermediary reference -- NOT from the primary one.

  The two references are independent tokens that may name objects in different
  apps; the intermediary dependency must therefore resolve the intermediary
  reference's own app label and object name, so that a relation routed through
  an object in a different app records a dependency on that other app.

The "app.Object" reference tokens are modelled as `List[int]` of Unicode code
points (Nagini bans `str` indexing); resolution is carried by the pure sequence
theory `PSeq[int]`. The reference resolver is modelled DEEPLY as the dot-split
plus lower-casing fold (`ref_app` / `ref_name`), whose equality to the real
resolver is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def lower_cp(c: int) -> int:
    """Lower-case a single code point: ASCII 'A'..'Z' (65..90) map to
    'a'..'z' (97..122); every other code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def dot_index(ref: PSeq[int], i: int) -> int:
    """Index of the first '.' (code point 46) at or after position `i`, or
    `len(ref)` if none. Front-recursive so one unfold is available per step."""
    Requires(0 <= i and i <= len(ref))
    Ensures(i <= Result() and Result() <= len(ref))
    if i == len(ref):
        return i
    if ref[i] == 46:
        return i
    return dot_index(ref, i + 1)


@Pure
def ref_app(ref: PSeq[int]) -> PSeq[int]:
    """App label of a reference token: the prefix before the first dot,
    verbatim (no case change)."""
    return ref.take(dot_index(ref, 0))


@Pure
def lowered(s: PSeq[int]) -> PSeq[int]:
    """Lower-cased sequence: each code point through `lower_cp`. Front-recursive
    so a single unfold is available per fold/loop step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(lower_cp(s[0])) + lowered(s.drop(1))


@Pure
def ref_name(ref: PSeq[int]) -> PSeq[int]:
    """Object name of a reference token: the suffix after the first dot,
    lower-cased."""
    return lowered(ref.drop(dot_index(ref, 0) + 1))
# pure-end


def through_dependency(primary_ref: List[int], through_ref: List[int]
                       ) -> Tuple[List[int], List[int]]:
    """The (app_label, object_name) of the dependency contributed for a
    relation routed through an intermediary object.

    `primary_ref` is the field's primary related reference; `through_ref` is
    the intermediary reference. Both are read-only "app.Object" tokens.
    """
    # pre-conditions-start
    # Both references are read-only: this computation derives a dependency from
    # them but mutates neither (directive 5: fractional permission).
    Requires(Acc(list_pred(primary_ref), 1 / 2))
    Requires(Acc(list_pred(through_ref), 1 / 2))
    # An "app.Object" reference token carries a dot separating the two parts.
    Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(primary_ref), 1 / 2))
    Ensures(Acc(list_pred(through_ref), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The intermediary dependency resolves the INTERMEDIARY reference's own app
    # label and (lower-cased) object name -- never the primary reference's.
    # This is the discriminating clause: when the two references name objects
    # in different apps, the dependency must point at the intermediary's app.
    Ensures(ToSeq(Result()[0]) == ref_app(ToSeq(through_ref)))
    Ensures(ToSeq(Result()[1]) == ref_name(ToSeq(through_ref)))
    # post-conditions-end
    # impl-start
    app = []  # type: List[int]
    name = []  # type: List[int]
    # locate the first dot of the intermediary reference
    d = 0
    while d < len(through_ref) and through_ref[d] != 46:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(0 <= d and d <= len(through_ref))
        # the reference carries a dot (a stable fact about the unchanged input)
        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
        # scanning past non-dots does not change the first-dot index
        Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
        # invariants-end
        # ref[d] != 46, so the first dot from d equals the first dot from d+1
        Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
        d = d + 1
    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
    # dot_index(.., d) == d, hence the first dot index is d
    Assert(dot_index(ToSeq(through_ref), d) == d)
    Assert(d == dot_index(ToSeq(through_ref), 0))
    # app label: prefix before the dot (verbatim)
    j = 0
    while j < d:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(app)))
        Invariant(d == dot_index(ToSeq(through_ref), 0))
        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
        Invariant(0 <= j and j <= d)
        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
        # invariants-end
        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
        app = app + [through_ref[j]]
        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
        j = j + 1
    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
    # the app label equals the deep-model resolver's app projection
    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
    # object name: lower-cased suffix after the dot
    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(d < len(through_ref))
    k = len(through_ref)
    while k > d + 1:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(Acc(list_pred(app)))
        Invariant(d == dot_index(ToSeq(through_ref), 0))
        # the app label, fully built, equals the resolver's app projection
        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
        Invariant(d + 1 <= k and k <= len(through_ref))
        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
        # invariants-end
        c = through_ref[k - 1]
        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
        name = [lower_cp(c)] + name
        k = k - 1
    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
    # connect the spelled-out parts to the deep-model reference resolver
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
    res = (app, name)  # type: Tuple[List[int], List[int]]
    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 9 same-spec attacks (all same-spec exit 0) + correct positive_control run through `adversary weakness nagini django__django-15973`. Verifications launched concurrently in batches of <=3 (each spawns JVM+Z3).

### Results
- positive_control.py (gold-faithful correct impl): CANDIDATE, verifies 15.9s (EXPECTED positive control, not a break).
- atk_1.py = model_prepatch.py (intermediary dep resolved from PRIMARY ref, mirroring pre-patch resolve_relation(remote_field_model,...)): NOT-A-COUNTEREXAMPLE, verification failed => the frozen spec REJECTS the prepatch bug (prepatch reproduced & sensed; consistent with recorded G-DIFF pass).
- atk_2.py (control-flow/vacuity: `while True` non-terminating loop then return): NOT-A-COUNTEREXAMPLE, verification failed => Nagini enforces termination; no partial-correctness vacuity hole.
- atk_3.py (tuple order swapped, return (name,app)): rejected.
- atk_4.py (object name returned VERBATIM, not lower-cased): rejected.
- atk_5.py (app label off-by-one, includes the dot, take d+1): rejected.
- atk_6.py (ungrounded-oracle echo: constant empty ([],[]) return): rejected.
- atk_7.py (boundary: split on LAST dot instead of first): rejected.
- atk_8.py (partial-domain / data-dependent branch: only computes when len>3, else empty): rejected.
- atk_9.py (app label wrongly ASCII-lower-cased): rejected.

Every command: `python -m swebench_unified.adversary weakness nagini django__django-15973 <path>`. Only the correct impl verifies; all 8 distinct wrong impls (partial-domain, boundary, control-flow-effect incl. non-termination, ungrounded-oracle echo, tuple-order, case-fold, off-by-one) FAIL verification. Because no verifying wrong impl exists, there is no CANDIDATE whose faithful refined patch needed to be materialized/run through run_resolve (Step 2 vacuous by construction — no verify=>correct violation found).

WHY THE SPEC IS TIGHT: the postconditions pin Result EXACTLY and universally: ToSeq(Result()[0])==ref_app(ToSeq(through_ref)) and ToSeq(Result()[1])==ref_name(ToSeq(through_ref)). ref_app/ref_name are the DEEP model (not a consumed axiom; axioms region empty) of the unchanged callee resolve_relation. No slack for a wrong impl on any input.

refinement.md A-LEG AUDIT (my focus): A1/A2 = R (str<->List[int] code points, read-only 1/2 perm); A3 = the single A-reference (ref_app/ref_name<->resolve_relation string branch model.split('.',1)->(app_label,name.lower())), validated by G-AX (recorded pass: 13 boundary + 20000 fuzz, exit 0) AND by my INDEPENDENT re-encoding sweep: 0 divergences over 13 boundary + 200000 ASCII-identifier fuzz tokens incl. F2P inputs contract.Contract / testapp.Publisher; the ONLY divergence is on non-ASCII CASED letters (É/Ü/İ), which is the explicitly disclosed out-of-domain boundary (mapping.md §2, deep_model_references.domain) and unreachable by the autodetector/F2P. A4 = I (the behavioral delta: postconditions reference through_ref, so the resolver is fed the intermediary ref, not remote_field_model; prepatch atk_1 fails, confirming this is the discriminating clause). A5 = R (2-tuple<->(app_label,object_name)). NO kind-3 leg; axioms region empty; A-reference correspondence to the real callee holds on the reachable/tested domain. R/I legs mechanically covered by G-CONF (recorded pass: 100090 checked, 0 disagreements).

Verdict: SOUND — >=5 (8) distinct wrong impls run, none verifies, so none breaks the spec; positive control verifies; A-reference correspondence and no-kind-3 confirmed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15973.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relational field contributes the migration dependencies that the field's
  references demand. Such a field always references a primary related object;
  some fields additionally route the relation through a SECOND, intermediary
  object. Each reference is an "app.Object" token that is resolved to an
  (app_label, object_name) pair by the shared reference resolver: the text
  before the first dot is the app label (verbatim), and the text after it is
  the object name, normalised to lower case.

  The contributed dependencies are:

    * one dependency derived from the PRIMARY reference, and
    * when an intermediary reference is supplied, a SECOND dependency derived
      from THAT intermediary reference -- NOT from the primary one.

  The two references are independent tokens that may name objects in different
  apps; the intermediary dependency must therefore resolve the intermediary
  reference's own app label and object name, so that a relation routed through
  an object in a different app records a dependency on that other app.

The "app.Object" reference tokens are modelled as `List[int]` of Unicode code
points (Nagini bans `str` indexing); resolution is carried by the pure sequence
theory `PSeq[int]`. The reference resolver is modelled DEEPLY as the dot-split
plus lower-casing fold (`ref_app` / `ref_name`), whose equality to the real
resolver is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def lower_cp(c: int) -> int:
    """Lower-case a single code point: ASCII 'A'..'Z' (65..90) map to
    'a'..'z' (97..122); every other code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def dot_index(ref: PSeq[int], i: int) -> int:
    """Index of the first '.' (code point 46) at or after position `i`, or
    `len(ref)` if none. Front-recursive so one unfold is available per step."""
    Requires(0 <= i and i <= len(ref))
    Ensures(i <= Result() and Result() <= len(ref))
    if i == len(ref):
        return i
    if ref[i] == 46:
        return i
    return dot_index(ref, i + 1)


@Pure
def ref_app(ref: PSeq[int]) -> PSeq[int]:
    """App label of a reference token: the prefix before the first dot,
    verbatim (no case change)."""
    return ref.take(dot_index(ref, 0))


@Pure
def lowered(s: PSeq[int]) -> PSeq[int]:
    """Lower-cased sequence: each code point through `lower_cp`. Front-recursive
    so a single unfold is available per fold/loop step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(lower_cp(s[0])) + lowered(s.drop(1))


@Pure
def ref_name(ref: PSeq[int]) -> PSeq[int]:
    """Object name of a reference token: the suffix after the first dot,
    lower-cased."""
    return lowered(ref.drop(dot_index(ref, 0) + 1))
# pure-end


def through_dependency(primary_ref: List[int], through_ref: List[int]
                       ) -> Tuple[List[int], List[int]]:
    """The (app_label, object_name) of the dependency contributed for a
    relation routed through an intermediary object.

    `primary_ref` is the field's primary related reference; `through_ref` is
    the intermediary reference. Both are read-only "app.Object" tokens.
    """
    # pre-conditions-start
    # Both references are read-only: this computation derives a dependency from
    # them but mutates neither (directive 5: fractional permission).
    Requires(Acc(list_pred(primary_ref), 1 / 2))
    Requires(Acc(list_pred(through_ref), 1 / 2))
    # An "app.Object" reference token carries a dot separating the two parts.
    Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(primary_ref), 1 / 2))
    Ensures(Acc(list_pred(through_ref), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The intermediary dependency resolves the INTERMEDIARY reference's own app
    # label and (lower-cased) object name -- never the primary reference's.
    # This is the discriminating clause: when the two references name objects
    # in different apps, the dependency must point at the intermediary's app.
    Ensures(ToSeq(Result()[0]) == ref_app(ToSeq(through_ref)))
    Ensures(ToSeq(Result()[1]) == ref_name(ToSeq(through_ref)))
    # post-conditions-end
    # impl-start
    app = []  # type: List[int]
    name = []  # type: List[int]
    # locate the first dot of the intermediary reference
    d = 0
    while d < len(through_ref) and through_ref[d] != 46:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(0 <= d and d <= len(through_ref))
        # the reference carries a dot (a stable fact about the unchanged input)
        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
        # scanning past non-dots does not change the first-dot index
        Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
        # invariants-end
        # ref[d] != 46, so the first dot from d equals the first dot from d+1
        Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
        d = d + 1
    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
    # dot_index(.., d) == d, hence the first dot index is d
    Assert(dot_index(ToSeq(through_ref), d) == d)
    Assert(d == dot_index(ToSeq(through_ref), 0))
    # app label: prefix before the dot (verbatim)
    j = 0
    while j < d:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(app)))
        Invariant(d == dot_index(ToSeq(through_ref), 0))
        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
        Invariant(0 <= j and j <= d)
        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
        # invariants-end
        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
        app = app + [through_ref[j]]
        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
        j = j + 1
    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
    # the app label equals the deep-model resolver's app projection
    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
    # object name: lower-cased suffix after the dot
    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(d < len(through_ref))
    k = len(through_ref)
    while k > d + 1:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(Acc(list_pred(app)))
        Invariant(d == dot_index(ToSeq(through_ref), 0))
        # the app label, fully built, equals the resolver's app projection
        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
        Invariant(d + 1 <= k and k <= len(through_ref))
        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
        # invariants-end
        c = through_ref[k - 1]
        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
        name = [lower_cp(c)] + name
        k = k - 1
    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
    # connect the spelled-out parts to the deep-model reference resolver
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
    res = (app, name)  # type: Tuple[List[int], List[int]]
    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 9 same-spec attacks (all same-spec exit 0) + correct positive_control run through `adversary weakness nagini django__django-15973`. Verifications launched concurrently in batches of <=3 (each spawns JVM+Z3).

### Results
- positive_control.py (gold-faithful correct impl): CANDIDATE, verifies 15.9s (EXPECTED positive control, not a break).
- atk_1.py = model_prepatch.py (intermediary dep resolved from PRIMARY ref, mirroring pre-patch resolve_relation(remote_field_model,...)): NOT-A-COUNTEREXAMPLE, verification failed => the frozen spec REJECTS the prepatch bug (prepatch reproduced & sensed; consistent with recorded G-DIFF pass).
- atk_2.py (control-flow/vacuity: `while True` non-terminating loop then return): NOT-A-COUNTEREXAMPLE, verification failed => Nagini enforces termination; no partial-correctness vacuity hole.
- atk_3.py (tuple order swapped, return (name,app)): rejected.
- atk_4.py (object name returned VERBATIM, not lower-cased): rejected.
- atk_5.py (app label off-by-one, includes the dot, take d+1): rejected.
- atk_6.py (ungrounded-oracle echo: constant empty ([],[]) return): rejected.
- atk_7.py (boundary: split on LAST dot instead of first): rejected.
- atk_8.py (partial-domain / data-dependent branch: only computes when len>3, else empty): rejected.
- atk_9.py (app label wrongly ASCII-lower-cased): rejected.

Every command: `python -m swebench_unified.adversary weakness nagini django__django-15973 <path>`. Only the correct impl verifies; all 8 distinct wrong impls (partial-domain, boundary, control-flow-effect incl. non-termination, ungrounded-oracle echo, tuple-order, case-fold, off-by-one) FAIL verification. Because no verifying wrong impl exists, there is no CANDIDATE whose faithful refined patch needed to be materialized/run through run_resolve (Step 2 vacuous by construction — no verify=>correct violation found).

WHY THE SPEC IS TIGHT: the postconditions pin Result EXACTLY and universally: ToSeq(Result()[0])==ref_app(ToSeq(through_ref)) and ToSeq(Result()[1])==ref_name(ToSeq(through_ref)). ref_app/ref_name are the DEEP model (not a consumed axiom; axioms region empty) of the unchanged callee resolve_relation. No slack for a wrong impl on any input.

refinement.md A-LEG AUDIT (my focus): A1/A2 = R (str<->List[int] code points, read-only 1/2 perm); A3 = the single A-reference (ref_app/ref_name<->resolve_relation string branch model.split('.',1)->(app_label,name.lower())), validated by G-AX (recorded pass: 13 boundary + 20000 fuzz, exit 0) AND by my INDEPENDENT re-encoding sweep: 0 divergences over 13 boundary + 200000 ASCII-identifier fuzz tokens incl. F2P inputs contract.Contract / testapp.Publisher; the ONLY divergence is on non-ASCII CASED letters (É/Ü/İ), which is the explicitly disclosed out-of-domain boundary (mapping.md §2, deep_model_references.domain) and unreachable by the autodetector/F2P. A4 = I (the behavioral delta: postconditions reference through_ref, so the resolver is fed the intermediary ref, not remote_field_model; prepatch atk_1 fails, confirming this is the discriminating clause). A5 = R (2-tuple<->(app_label,object_name)). NO kind-3 leg; axioms region empty; A-reference correspondence to the real callee holds on the reachable/tested domain. R/I legs mechanically covered by G-CONF (recorded pass: 100090 checked, 0 disagreements).

Verdict: SOUND — >=5 (8) distinct wrong impls run, none verifies, so none breaks the spec; positive control verifies; A-reference correspondence and no-kind-3 confirmed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** same-spec confirms the audited model shares the bundle's exact spec (exit 0). The spec's deep model (ref_app/ref_name/lowered/lower_cp) equals the real django.db.migrations.utils.resolve_relation at base_commit 2480554 over the domain the task exercises: 200k random ASCII-identifier tokens gave 0 disagreements. The single divergence is on non-ASCII CASED letters in the object-name part, because lower_cp is an ASCII-only fold whereas str.lower() is Unicode-aware. This boundary is EXPLICITLY DECLARED AND JUSTIFIED by the bundle (mapping.md §2: 'Non-ASCII cased letters are out of domain (real model names are ASCII; the F2P inputs are all ASCII)'; axiom_check.py and conformance_check.py both scope fuzzing to the ASCII identifier alphabet). Django app labels and model references resolved by _get_dependencies_for_foreign_key on this path are ASCII identifiers, and the F2P test (test_create_with_through_model_separate_apps: contract.Contract / testapp.Publisher) is entirely ASCII. The discriminating behavioral change of the patch is fully and correctly modeled: the intermediary dependency resolves through_ref, not primary_ref (spec gives (contract, contract) vs prepatch (testapp, publisher) on the separate-apps case). The gold patch (verbatim, G-RESOLVE) resolves. Therefore the spec is FAITHFUL for its purpose: it is neither too strong nor too weak on the tested/relevant domain, and its only real-vs-model disagreement lies in an explicitly excluded, well-justified out-of-domain region (non-ASCII cased characters) that does not affect resolution. This is a standard disclosed ASCII-fold modeling boundary, not a drift defect.

Counterexample / evidence:

```
None in-domain. An impl faithfully reproducing resolve_relation's Unicode lowering would violate the postcondition Result()[1]==ref_name(through_ref) only on non-ASCII cased through-refs; on the entire ASCII-identifier domain the two agree exactly (200,000 randomized dotted tokens: 0 divergences; matches G-CONF 100k + G-AX 20k passing).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (status=pass, no hard failures), independently reproduced: no diff markers, no reproduced changed lines ('remote_field_model,' / 'field.remote_field.through,'), patched file path 'django/db/migrations/autodetector.py' absent, and none of the patched repo symbols (_get_dependencies_for_foreign_key, remote_field_model, resolve_relation, autodetector, _meta) appear in the spec view.

Gold edit: one line in _get_dependencies_for_foreign_key — the intermediary/through dependency's resolver argument changes from remote_field_model (primary reference) to field.remote_field.through (intermediary reference).

Semantic gold-reconstruction judgment: The spec view (model.py docstring + pure/pre/post regions) states the DESIRED behavior abstractly — a primary reference yields one dependency and an intermediary ('through') reference yields a SECOND dependency resolving the intermediary's own app label/object name, not the primary's. This is precisely what the public problem_statement already implies: a through model defined in ANOTHER app on a ManyToManyField breaks migration (and works in the same app), so correct behavior must account for the through model's own app. The public report already discloses 'through', 'ManyToManyField', 'different app', and 'dependencies'. The spec names no repo symbols under change, reproduces no edited lines, narrates no bug/fix, and reveals no repo-identifier-level data-flow selection. The explicit prepatch/remote_field_model discussion lives ONLY in mapping.md/refinement.md (audit/derivation docs, explicitly 'not referenced from the consumer spec view'), not the consumer spec view. No RELAXED_LEAKAGE.md present; none needed. The spec re-expresses correct behavior derivable from the public bug report and does not leak the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
