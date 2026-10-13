# P2 adversarial audit — scikit-learn__scikit-learn-25102

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -48,9 +47,6 @@
         # permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
         Requires(ToSeq(index) == si and ToSeq(descs) == sd)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)        # type: ignore
         Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
@@ -92,12 +88,6 @@
     Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
     Requires(Acc(list_pred(mask), 1 / 2))
     Requires(len(df.descs) == len(mask))
-    # The selection must COMPLETE (total correctness). Without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 3 is strictly above both callees it invokes (_copy_labels
-    # at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Read-only inputs are returned at the fractional permission they were lent
@@ -117,10 +107,12 @@
     # post-conditions-end
     # impl-start
     new_index = _copy_labels(df.index)  # type: List[int]
+    homo = 0
+    if len(df.descs) > 0:
+        homo = df.descs[0]
     new_descs = []  # type: List[int]
     i = len(df.descs)
     while i > 0:
-        # invariants-start
         Invariant(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
         Invariant(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
         Invariant(Acc(list_pred(mask), 1 / 2))
@@ -129,23 +121,9 @@
         Invariant(len(df.descs) == len(mask))
         Invariant(0 <= i and i <= len(df.descs))
         Invariant(ToSeq(new_index) == ToSeq(df.index))
-        Invariant(ToSeq(new_descs) ==
-                  kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # columns, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        d = df.descs[i - 1]
         m = mask[i - 1]
-        # Relate the (i-1)-suffix to the i-suffix: dropping i-1 exposes the
-        # element at i-1 as the head, and its tail is the i-suffix.
-        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
-        Assert(ToSeq(mask).drop(i - 1)[0] == m)
-        Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
-        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))
         if m != 0:
-            new_descs = [d] + new_descs
+            new_descs = [homo] + new_descs
         i = i - 1
     gi = ToSeq(new_index)    # type: PSeq[int]
     gd = ToSeq(new_descs)    # type: PSeq[int]
@@ -156,28 +134,17 @@
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying the row labels must COMPLETE: level 2 leaves room for the list
-    # allocation it performs (at level 1 the allocation's own obligation has
-    # nowhere below the caller to go), and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(src), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == ToSeq(src))
     out = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(src))
         Invariant(len(out) == i)
         Invariant(ToSeq(out) == ToSeq(src).take(i))
-        # At most len(src) - i + 1 passes remain: the source is held read-only by
-        # the invariant above so its length cannot change, and i rises by exactly
-        # one per pass, so the bound strictly decreases; the guard i < len(src)
-        # keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         out.append(src[i])
         i = i + 1
     Assert(ToSeq(src).take(len(src)) == ToSeq(src))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -48,9 +47,6 @@
         # permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
         Requires(ToSeq(index) == si and ToSeq(descs) == sd)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)        # type: ignore
         Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
@@ -92,12 +88,6 @@
     Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
     Requires(Acc(list_pred(mask), 1 / 2))
     Requires(len(df.descs) == len(mask))
-    # The selection must COMPLETE (total correctness). Without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 3 is strictly above both callees it invokes (_copy_labels
-    # at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Read-only inputs are returned at the fractional permission they were lent
@@ -116,11 +106,21 @@
     Ensures(ToSeq(Result().index) == ToSeq(df.index))
     # post-conditions-end
     # impl-start
-    new_index = _copy_labels(df.index)  # type: List[int]
+    new_index = []  # type: List[int]
+    nrows = len(df.index)
+    j = 0
+    while j < nrows:
+        Invariant(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
+        Invariant(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
+        Invariant(Acc(list_pred(mask), 1 / 2))
+        Invariant(len(df.descs) == len(mask))
+        Invariant(Acc(list_pred(new_index)))
+        Invariant(0 <= j and j <= nrows and len(new_index) == j)
+        new_index.append(j)
+        j = j + 1
     new_descs = []  # type: List[int]
     i = len(df.descs)
     while i > 0:
-        # invariants-start
         Invariant(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
         Invariant(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
         Invariant(Acc(list_pred(mask), 1 / 2))
@@ -128,18 +128,10 @@
         Invariant(Acc(list_pred(new_descs)))
         Invariant(len(df.descs) == len(mask))
         Invariant(0 <= i and i <= len(df.descs))
-        Invariant(ToSeq(new_index) == ToSeq(df.index))
         Invariant(ToSeq(new_descs) ==
                   kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # columns, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         d = df.descs[i - 1]
         m = mask[i - 1]
-        # Relate the (i-1)-suffix to the i-suffix: dropping i-1 exposes the
-        # element at i-1 as the head, and its tail is the i-suffix.
         Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
         Assert(ToSeq(mask).drop(i - 1)[0] == m)
         Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
@@ -156,28 +148,17 @@
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying the row labels must COMPLETE: level 2 leaves room for the list
-    # allocation it performs (at level 1 the allocation's own obligation has
-    # nowhere below the caller to go), and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(src), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == ToSeq(src))
     out = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(src))
         Invariant(len(out) == i)
         Invariant(ToSeq(out) == ToSeq(src).take(i))
-        # At most len(src) - i + 1 passes remain: the source is held read-only by
-        # the invariant above so its length cannot change, and i rises by exactly
-        # one per pass, so the bound strictly decreases; the guard i < len(src)
-        # keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         out.append(src[i])
         i = i + 1
     Assert(ToSeq(src).take(len(src)) == ToSeq(src))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -48,9 +47,6 @@
         # permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
         Requires(ToSeq(index) == si and ToSeq(descs) == sd)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)        # type: ignore
         Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
@@ -92,12 +88,6 @@
     Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
     Requires(Acc(list_pred(mask), 1 / 2))
     Requires(len(df.descs) == len(mask))
-    # The selection must COMPLETE (total correctness). Without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 3 is strictly above both callees it invokes (_copy_labels
-    # at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Read-only inputs are returned at the fractional permission they were lent
@@ -131,15 +121,9 @@
         Invariant(ToSeq(new_index) == ToSeq(df.index))
         Invariant(ToSeq(new_descs) ==
                   kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # columns, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         d = df.descs[i - 1]
         m = mask[i - 1]
-        # Relate the (i-1)-suffix to the i-suffix: dropping i-1 exposes the
-        # element at i-1 as the head, and its tail is the i-suffix.
         Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
         Assert(ToSeq(mask).drop(i - 1)[0] == m)
         Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
@@ -147,6 +131,18 @@
         if m != 0:
             new_descs = [d] + new_descs
         i = i - 1
+    if len(new_descs) == 0:
+        new_index2 = []  # type: List[int]
+        k = 0
+        while k < len(df.index):
+            Invariant(Acc(df.index, 1 / 2) and Acc(list_pred(df.index), 1 / 2))
+            Invariant(Acc(list_pred(new_index2)))
+            Invariant(0 <= k and k <= len(df.index) and len(new_index2) == k)
+            new_index2.append(k)
+            k = k + 1
+        gi0 = ToSeq(new_index2)  # type: PSeq[int]
+        gd0 = ToSeq(new_descs)   # type: PSeq[int]
+        return Frame(new_index2, new_descs, gi0, gd0)
     gi = ToSeq(new_index)    # type: PSeq[int]
     gd = ToSeq(new_descs)    # type: PSeq[int]
     result = Frame(new_index, new_descs, gi, gd)  # type: Frame
@@ -156,28 +152,17 @@
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying the row labels must COMPLETE: level 2 leaves room for the list
-    # allocation it performs (at level 1 the allocation's own obligation has
-    # nowhere below the caller to go), and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(src), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == ToSeq(src))
     out = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(src))
         Invariant(len(out) == i)
         Invariant(ToSeq(out) == ToSeq(src).take(i))
-        # At most len(src) - i + 1 passes remain: the source is held read-only by
-        # the invariant above so its length cannot change, and i rises by exactly
-        # one per pass, so the bound strictly decreases; the guard i < len(src)
-        # keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         out.append(src[i])
         i = i + 1
     Assert(ToSeq(src).take(len(src)) == ToSeq(src))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -48,9 +47,6 @@
         # permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
         Requires(ToSeq(index) == si and ToSeq(descs) == sd)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)        # type: ignore
         Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
@@ -92,12 +88,6 @@
     Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
     Requires(Acc(list_pred(mask), 1 / 2))
     Requires(len(df.descs) == len(mask))
-    # The selection must COMPLETE (total correctness). Without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 3 is strictly above both callees it invokes (_copy_labels
-    # at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Read-only inputs are returned at the fractional permission they were lent
@@ -119,7 +109,7 @@
     new_index = _copy_labels(df.index)  # type: List[int]
     new_descs = []  # type: List[int]
     i = len(df.descs)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
         Invariant(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
@@ -127,19 +117,13 @@
         Invariant(Acc(list_pred(new_index)))
         Invariant(Acc(list_pred(new_descs)))
         Invariant(len(df.descs) == len(mask))
-        Invariant(0 <= i and i <= len(df.descs))
+        Invariant(1 <= i and i <= len(df.descs))
         Invariant(ToSeq(new_index) == ToSeq(df.index))
         Invariant(ToSeq(new_descs) ==
                   kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # columns, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         d = df.descs[i - 1]
         m = mask[i - 1]
-        # Relate the (i-1)-suffix to the i-suffix: dropping i-1 exposes the
-        # element at i-1 as the head, and its tail is the i-suffix.
         Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
         Assert(ToSeq(mask).drop(i - 1)[0] == m)
         Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
@@ -156,28 +140,17 @@
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying the row labels must COMPLETE: level 2 leaves room for the list
-    # allocation it performs (at level 1 the allocation's own obligation has
-    # nowhere below the caller to go), and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(src), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == ToSeq(src))
     out = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(src))
         Invariant(len(out) == i)
         Invariant(ToSeq(out) == ToSeq(src).take(i))
-        # At most len(src) - i + 1 passes remain: the source is held read-only by
-        # the invariant above so its length cannot change, and i rises by exactly
-        # one per pass, so the bound strictly decreases; the guard i < len(src)
-        # keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         out.append(src[i])
         i = i + 1
     Assert(ToSeq(src).take(len(src)) == ToSeq(src))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -48,9 +47,6 @@
         # permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
         Requires(ToSeq(index) == si and ToSeq(descs) == sd)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)        # type: ignore
         Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
@@ -92,12 +88,6 @@
     Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
     Requires(Acc(list_pred(mask), 1 / 2))
     Requires(len(df.descs) == len(mask))
-    # The selection must COMPLETE (total correctness). Without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 3 is strictly above both callees it invokes (_copy_labels
-    # at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Read-only inputs are returned at the fractional permission they were lent
@@ -129,23 +119,9 @@
         Invariant(len(df.descs) == len(mask))
         Invariant(0 <= i and i <= len(df.descs))
         Invariant(ToSeq(new_index) == ToSeq(df.index))
-        Invariant(ToSeq(new_descs) ==
-                  kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # columns, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         d = df.descs[i - 1]
-        m = mask[i - 1]
-        # Relate the (i-1)-suffix to the i-suffix: dropping i-1 exposes the
-        # element at i-1 as the head, and its tail is the i-suffix.
-        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
-        Assert(ToSeq(mask).drop(i - 1)[0] == m)
-        Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
-        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))
-        if m != 0:
-            new_descs = [d] + new_descs
+        new_descs = [d] + new_descs
         i = i - 1
     gi = ToSeq(new_index)    # type: PSeq[int]
     gd = ToSeq(new_descs)    # type: PSeq[int]
@@ -156,28 +132,17 @@
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying the row labels must COMPLETE: level 2 leaves room for the list
-    # allocation it performs (at level 1 the allocation's own obligation has
-    # nowhere below the caller to go), and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(src), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == ToSeq(src))
     out = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(src))
         Invariant(len(out) == i)
         Invariant(ToSeq(out) == ToSeq(src).take(i))
-        # At most len(src) - i + 1 passes remain: the source is held read-only by
-        # the invariant above so its length cannot change, and i rises by exactly
-        # one per pass, so the bound strictly decreases; the guard i < len(src)
-        # keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         out.append(src[i])
         i = i + 1
     Assert(ToSeq(src).take(len(src)) == ToSeq(src))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -48,9 +47,6 @@
         # permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
         Requires(ToSeq(index) == si and ToSeq(descs) == sd)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)        # type: ignore
         Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
@@ -92,12 +88,6 @@
     Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
     Requires(Acc(list_pred(mask), 1 / 2))
     Requires(len(df.descs) == len(mask))
-    # The selection must COMPLETE (total correctness). Without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 3 is strictly above both callees it invokes (_copy_labels
-    # at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Read-only inputs are returned at the fractional permission they were lent
@@ -129,22 +119,10 @@
         Invariant(len(df.descs) == len(mask))
         Invariant(0 <= i and i <= len(df.descs))
         Invariant(ToSeq(new_index) == ToSeq(df.index))
-        Invariant(ToSeq(new_descs) ==
-                  kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # columns, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         d = df.descs[i - 1]
         m = mask[i - 1]
-        # Relate the (i-1)-suffix to the i-suffix: dropping i-1 exposes the
-        # element at i-1 as the head, and its tail is the i-suffix.
-        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
-        Assert(ToSeq(mask).drop(i - 1)[0] == m)
-        Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
-        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))
-        if m != 0:
+        if m == 0:
             new_descs = [d] + new_descs
         i = i - 1
     gi = ToSeq(new_index)    # type: PSeq[int]
@@ -156,28 +134,17 @@
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying the row labels must COMPLETE: level 2 leaves room for the list
-    # allocation it performs (at level 1 the allocation's own obligation has
-    # nowhere below the caller to go), and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(src), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == ToSeq(src))
     out = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(src))
         Invariant(len(out) == i)
         Invariant(ToSeq(out) == ToSeq(src).take(i))
-        # At most len(src) - i + 1 passes remain: the source is held read-only by
-        # the invariant above so its length cannot change, and i rises by exactly
-        # one per pass, so the bound strictly decreases; the guard i < len(src)
-        # keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         out.append(src[i])
         i = i + 1
     Assert(ToSeq(src).take(len(src)) == ToSeq(src))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -48,9 +47,6 @@
         # permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
         Requires(ToSeq(index) == si and ToSeq(descs) == sd)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)        # type: ignore
         Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
@@ -92,12 +88,6 @@
     Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
     Requires(Acc(list_pred(mask), 1 / 2))
     Requires(len(df.descs) == len(mask))
-    # The selection must COMPLETE (total correctness). Without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 3 is strictly above both callees it invokes (_copy_labels
-    # at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Read-only inputs are returned at the fractional permission they were lent
@@ -118,8 +108,9 @@
     # impl-start
     new_index = _copy_labels(df.index)  # type: List[int]
     new_descs = []  # type: List[int]
-    i = len(df.descs)
-    while i > 0:
+    i = 0
+    n = len(df.descs)
+    while i < n:
         # invariants-start
         Invariant(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
         Invariant(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
@@ -127,26 +118,20 @@
         Invariant(Acc(list_pred(new_index)))
         Invariant(Acc(list_pred(new_descs)))
         Invariant(len(df.descs) == len(mask))
-        Invariant(0 <= i and i <= len(df.descs))
+        Invariant(0 <= i and i <= n and n == len(df.descs))
         Invariant(ToSeq(new_index) == ToSeq(df.index))
         Invariant(ToSeq(new_descs) ==
-                  kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # columns, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
+                  kept_descs(ToSeq(df.descs).take(i), ToSeq(mask).take(i)))
         # invariants-end
-        d = df.descs[i - 1]
-        m = mask[i - 1]
-        # Relate the (i-1)-suffix to the i-suffix: dropping i-1 exposes the
-        # element at i-1 as the head, and its tail is the i-suffix.
-        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
-        Assert(ToSeq(mask).drop(i - 1)[0] == m)
-        Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
-        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))
+        d = df.descs[i]
+        m = mask[i]
+        Assert(ToSeq(df.descs).take(i + 1) == ToSeq(df.descs).take(i) + PSeq(d))
+        Assert(ToSeq(mask).take(i + 1) == ToSeq(mask).take(i) + PSeq(m))
         if m != 0:
-            new_descs = [d] + new_descs
-        i = i - 1
+            new_descs.append(d)
+        i = i + 1
+    Assert(ToSeq(df.descs).take(n) == ToSeq(df.descs))
+    Assert(ToSeq(mask).take(n) == ToSeq(mask))
     gi = ToSeq(new_index)    # type: PSeq[int]
     gd = ToSeq(new_descs)    # type: PSeq[int]
     result = Frame(new_index, new_descs, gi, gd)  # type: Frame
@@ -156,28 +141,17 @@
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying the row labels must COMPLETE: level 2 leaves room for the list
-    # allocation it performs (at level 1 the allocation's own obligation has
-    # nowhere below the caller to go), and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(src), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == ToSeq(src))
     out = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(src))
         Invariant(len(out) == i)
         Invariant(ToSeq(out) == ToSeq(src).take(i))
-        # At most len(src) - i + 1 passes remain: the source is held read-only by
-        # the invariant above so its length cannot change, and i rises by exactly
-        # one per pass, so the bound strictly decreases; the guard i < len(src)
-        # keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         out.append(src[i])
         i = i + 1
     Assert(ToSeq(src).take(len(src)) == ToSeq(src))
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -48,9 +47,6 @@
         # permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
         Requires(ToSeq(index) == si and ToSeq(descs) == sd)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)        # type: ignore
         Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
@@ -92,12 +88,6 @@
     Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
     Requires(Acc(list_pred(mask), 1 / 2))
     Requires(len(df.descs) == len(mask))
-    # The selection must COMPLETE (total correctness). Without this obligation
-    # every Ensures below is claimed only of runs that reach the return, so an
-    # implementation that never gets there satisfies the whole postcondition
-    # vacuously. Level 3 is strictly above both callees it invokes (_copy_labels
-    # at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     # Read-only inputs are returned at the fractional permission they were lent
@@ -116,7 +106,6 @@
     Ensures(ToSeq(Result().index) == ToSeq(df.index))
     # post-conditions-end
     # impl-start
-    new_index = _copy_labels(df.index)  # type: List[int]
     new_descs = []  # type: List[int]
     i = len(df.descs)
     while i > 0:
@@ -124,22 +113,14 @@
         Invariant(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
         Invariant(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
         Invariant(Acc(list_pred(mask), 1 / 2))
-        Invariant(Acc(list_pred(new_index)))
         Invariant(Acc(list_pred(new_descs)))
         Invariant(len(df.descs) == len(mask))
         Invariant(0 <= i and i <= len(df.descs))
-        Invariant(ToSeq(new_index) == ToSeq(df.index))
         Invariant(ToSeq(new_descs) ==
                   kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
-        # At most i + 1 passes remain: the loop counts DOWN over the input
-        # columns, i drops by exactly one per pass, and the guard i > 0 keeps the
-        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         d = df.descs[i - 1]
         m = mask[i - 1]
-        # Relate the (i-1)-suffix to the i-suffix: dropping i-1 exposes the
-        # element at i-1 as the head, and its tail is the i-suffix.
         Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
         Assert(ToSeq(mask).drop(i - 1)[0] == m)
         Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
@@ -147,6 +128,15 @@
         if m != 0:
             new_descs = [d] + new_descs
         i = i - 1
+    new_index = []  # type: List[int]
+    k = 0
+    while k < len(new_descs):
+        Invariant(Acc(df.index, 1 / 2) and Acc(list_pred(df.index), 1 / 2))
+        Invariant(Acc(list_pred(new_index)))
+        Invariant(Acc(list_pred(new_descs)))
+        Invariant(0 <= k and k <= len(new_descs) and len(new_index) == k)
+        new_index.append(k)
+        k = k + 1
     gi = ToSeq(new_index)    # type: PSeq[int]
     gd = ToSeq(new_descs)    # type: PSeq[int]
     result = Frame(new_index, new_descs, gi, gd)  # type: Frame
@@ -156,28 +146,17 @@
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying the row labels must COMPLETE: level 2 leaves room for the list
-    # allocation it performs (at level 1 the allocation's own obligation has
-    # nowhere below the caller to go), and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(src), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     Ensures(ToSeq(Result()) == ToSeq(src))
     out = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(src))
         Invariant(len(out) == i)
         Invariant(ToSeq(out) == ToSeq(src).take(i))
-        # At most len(src) - i + 1 passes remain: the source is held read-only by
-        # the invariant above so its length cannot change, and i rises by exactly
-        # one per pass, so the bound strictly decreases; the guard i < len(src)
-        # keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         out.append(src[i])
         i = i + 1
     Assert(ToSeq(src).take(len(src)) == ToSeq(src))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-25102.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A feature-reducing transformer applied to a labelled tabular container picks
  out a subset of the container's columns according to a per-column boolean
  retention mask, and returns the result as a labelled tabular container that
  keeps the column-wise descriptive metadata of the input. Concretely:

    (1) Per-column metadata is preserved. Each output column is one of the
        input columns chosen by the mask, carried over UNCHANGED — in
        particular its per-column descriptor (the value distinguishing a column
        whose entries are, say, an ordinal category from one whose entries are
        a real number). The output column descriptors are exactly the
        descriptors of the retained input columns, in input order; an output
        column NEVER takes a single shared descriptor coerced across all
        columns. The retained columns are those positions whose mask entry is
        set, and only those.

    (2) Row labels are preserved. The output keeps the input container's OWN row
        labels (its "index") unchanged, whatever the number of retained columns
        — including the degenerate case where the mask retains no column at all
        (the output then has zero columns but still the input's row labels), not
        a freshly invented positional row labelling.

The labelled container is modelled as a minimal class carrying only its two
touched facets: its row labels (the "index", a ``List[int]`` of label codes)
and its per-column descriptors (a ``List[int]`` of descriptor codes, one per
column). The retention mask is a ``List[int]`` of per-column flags (0 = drop,
1 = keep). Sequence values are compared via the pure ``PSeq[int]`` theory
(``ToSeq``). The per-column-descriptor selection is modelled deeply as a
front-recursive compress fold (``kept_descs``); the postconditions pin both the
exact per-column descriptors of the result and its row labels.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Frame:
    def __init__(self, index: List[int], descs: List[int],
                 si: PSeq[int], sd: PSeq[int]) -> None:
        # `si`/`sd` are ghost witnesses of the intended row-label and
        # column-descriptor sequences, so the caller can relate the constructed
        # container's facets to values it still holds after the list
        # permissions move into the fields.
        Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
        Requires(ToSeq(index) == si and ToSeq(descs) == sd)
        Ensures(Acc(self.index) and self.index is index)        # type: ignore
        Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
        Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
        Ensures(ToSeq(self.index) == si)                        # type: ignore
        Ensures(ToSeq(self.descs) == sd)                        # type: ignore
        self.index = index
        self.descs = descs


# axioms-start
# (no axioms: the column-selection behaviour is a self-contained per-column
# compress over the touched facets, modelled deeply; nothing the proof needs is
# delegated to an unchanged opaque callee.)
# axioms-end


# pure-start
@Pure
def kept_descs(descs: PSeq[int], mask: PSeq[int]) -> PSeq[int]:
    """The descriptors of the retained columns, in input order: for each
    position keep the input column's descriptor exactly when its mask flag is
    set, else nothing. Front-recursive so a single unfold is available to the
    matching impl loop. Each kept descriptor is the input column's OWN
    descriptor (never a coerced shared value). Total over any pair of sequences:
    positions past the end of either sequence contribute nothing (the modelled
    inputs always have matching lengths, established by the caller)."""
    if len(descs) == 0 or len(mask) == 0:
        return PSeq(0).take(0)
    if mask[0] != 0:
        return PSeq(descs[0]) + kept_descs(descs.drop(1), mask.drop(1))
    return kept_descs(descs.drop(1), mask.drop(1))
# pure-end


def select_columns(df: Frame, mask: List[int]) -> Frame:
    # `mask` has one flag per input column (0 = drop, 1 = keep), read-only.
    # pre-conditions-start
    Requires(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
    Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
    Requires(Acc(list_pred(mask), 1 / 2))
    Requires(len(df.descs) == len(mask))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs are returned at the fractional permission they were lent
    # at (the input container and the mask are never mutated).
    Ensures(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
    Ensures(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
    Ensures(Acc(list_pred(mask), 1 / 2))
    Ensures(Acc(Result().index) and Acc(Result().descs))
    Ensures(Acc(list_pred(Result().index)) and Acc(list_pred(Result().descs)))
    # (1) Per-column metadata preserved: the output column descriptors are
    # exactly the descriptors of the retained input columns, in input order
    # (each carried over unchanged — never a single coerced shared descriptor).
    Ensures(ToSeq(Result().descs) == kept_descs(ToSeq(df.descs), ToSeq(mask)))
    # (2) Row labels preserved: the output keeps the input's OWN row labels,
    # regardless of how many columns survived (including none).
    Ensures(ToSeq(Result().index) == ToSeq(df.index))
    # post-conditions-end
    # impl-start
    new_index = _copy_labels(df.index)  # type: List[int]
    new_descs = []  # type: List[int]
    i = len(df.descs)
    while i > 0:
        # invariants-start
        Invariant(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
        Invariant(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
        Invariant(Acc(list_pred(mask), 1 / 2))
        Invariant(Acc(list_pred(new_index)))
        Invariant(Acc(list_pred(new_descs)))
        Invariant(len(df.descs) == len(mask))
        Invariant(0 <= i and i <= len(df.descs))
        Invariant(ToSeq(new_index) == ToSeq(df.index))
        Invariant(ToSeq(new_descs) ==
                  kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
        # invariants-end
        d = df.descs[i - 1]
        m = mask[i - 1]
        # Relate the (i-1)-suffix to the i-suffix: dropping i-1 exposes the
        # element at i-1 as the head, and its tail is the i-suffix.
        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
        Assert(ToSeq(mask).drop(i - 1)[0] == m)
        Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))
        if m != 0:
            new_descs = [d] + new_descs
        i = i - 1
    gi = ToSeq(new_index)    # type: PSeq[int]
    gd = ToSeq(new_descs)    # type: PSeq[int]
    result = Frame(new_index, new_descs, gi, gd)  # type: Frame
    return result
    # impl-end


def _copy_labels(src: List[int]) -> List[int]:
    Requires(Acc(list_pred(src), 1 / 2))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(src))
    out = []  # type: List[int]
    i = 0
    while i < len(src):
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(src))
        Invariant(len(out) == i)
        Invariant(ToSeq(out) == ToSeq(src).take(i))
        out.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    return out
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. No same-spec, verifying wrong impl exists; the spec pins BOTH observable facets with exact functional equalities (ToSeq(Result().descs)==kept_descs(ToSeq(df.descs),ToSeq(mask)) and ToSeq(Result().index)==ToSeq(df.index)), so any verifying impl produces exactly the gold output.

ENV: module; SBU_BENCHMARK_DIR=benchmark-verified.

### BASELINE (mandatory):
- positive_control.py = bundle model.py: `adversary weakness nagini ... positive_control.py` -> CANDIDATE (verifies, 12.2s), exit 0.
- prepatch1.py (= model_prepatch.py, homogenized shared descriptor): `bash scripts/nagini_verify.sh prepatch1.py` -> Verification failed, Postcondition (1) ToSeq(Result().descs)==kept_descs(...) might not hold. exit 1. Prepatch bug REPRODUCED (spec rejects it).
- prepatch2.py (= model_prepatch_2.py, fresh positional index): `bash scripts/nagini_verify.sh prepatch2.py` -> Verification failed, Postcondition (2) ToSeq(Result().index)==ToSeq(df.index) might not hold. exit 1. Prepatch bug REPRODUCED.

atk_1 (prepatch bug re-encode: homogenized shared descriptor): weakness exit 2 (does-not-verify; spec rejected). Distinct: ungrounded-oracle/homogenization echo.
- atk_2 (prepatch bug re-encode: fresh positional index [0..n-1]): weakness exit 2.
- atk_3 (partial-domain: correct non-empty, but empty-mask returns positional index): weakness exit 2.
- atk_4 (boundary off-by-one: while i>1, skips column 0): weakness exit 2.
- atk_5 (control-flow-effect: keep ALL columns, ignore mask): weakness exit 2.
- atk_6 (invert mask: keep when m==0): weakness exit 2.
- atk_7 (alternative correct forward-iteration impl / echo): weakness exit 2 — fails on a loop-INVARIANT preservation (take-based fwd invariant vs front-recursive kept_descs), a proof-annotation shortfall, NOT the spec admitting wrong behavior; direct nagini_verify shows 'Loop invariant might not be preserved', not a postcondition weakness.
- atk_8 (index truncation: new_index=[0..len(new_descs)-1], loses rows): weakness exit 2.
Every attack: exit 2 = NOT-A-COUNTEREXAMPLE (does not verify). ZERO candidates besides the positive control.

MANDATORY CANDIDATE-RESOLVE: the only same-spec verifying impl is the positive control (= bundle model.py). Its faithful refined patch is the gold patch verbatim. Materialized to faithful_positive_control.diff and executed through the official harness: harness.run_resolve('scikit-learn__scikit-learn-25102', patch, timeout=2400) -> completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So verify==>correct for the sole verifying impl; no verify-but-not-resolve exists. Spec is NOT broken.

REFINEMENT.MD AUDIT (A-legs / correspondence): all legs are R / A-reference / I; NO kind-3, NO consumed @ContractOnly axiom (section C accurate). A1 (DataFrame X -> Frame{index,descs}) = R; A2 (bool mask -> List[int] 0/1) = R; A3 (kept_descs compress = per-column descriptor selection) = A-reference; A4 (index carry-over) = A-reference+I; A5 (empty-mask X.iloc[:,:0]) = A-reference; A6 (removed dead ValueError raise) = I, guarded by precondition len(df.descs)==len(mask); B1 (cast_to_ndarray routing plumbing) = I. A-reference correspondence VALIDATED: ran axiom_check.py (G-AX) independently in swebench-lean env (sklearn 1.3.0/pandas 3.0.5) -> exit 0, 'G-AX OK' over 5 dtype palettes x 3 indices x 4 masks + empty masks + 1500 fuzz; asserts deep model (index labels, per-column dtypes) == real post-patch _safe_indexing(X,mask,axis=1)/X.iloc[:,:0], and exhibits the pre-patch divergence (X.values[:,mask] homogenises dtypes; empty branch references absent DataFrame.dtype). The two modeled facets are exactly the F2P-observed ones (output.index, output.dtypes).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

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

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-25102.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A feature-reducing transformer applied to a labelled tabular container picks
  out a subset of the container's columns according to a per-column boolean
  retention mask, and returns the result as a labelled tabular container that
  keeps the column-wise descriptive metadata of the input. Concretely:

    (1) Per-column metadata is preserved. Each output column is one of the
        input columns chosen by the mask, carried over UNCHANGED — in
        particular its per-column descriptor (the value distinguishing a column
        whose entries are, say, an ordinal category from one whose entries are
        a real number). The output column descriptors are exactly the
        descriptors of the retained input columns, in input order; an output
        column NEVER takes a single shared descriptor coerced across all
        columns. The retained columns are those positions whose mask entry is
        set, and only those.

    (2) Row labels are preserved. The output keeps the input container's OWN row
        labels (its "index") unchanged, whatever the number of retained columns
        — including the degenerate case where the mask retains no column at all
        (the output then has zero columns but still the input's row labels), not
        a freshly invented positional row labelling.

The labelled container is modelled as a minimal class carrying only its two
touched facets: its row labels (the "index", a ``List[int]`` of label codes)
and its per-column descriptors (a ``List[int]`` of descriptor codes, one per
column). The retention mask is a ``List[int]`` of per-column flags (0 = drop,
1 = keep). Sequence values are compared via the pure ``PSeq[int]`` theory
(``ToSeq``). The per-column-descriptor selection is modelled deeply as a
front-recursive compress fold (``kept_descs``); the postconditions pin both the
exact per-column descriptors of the result and its row labels.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Frame:
    def __init__(self, index: List[int], descs: List[int],
                 si: PSeq[int], sd: PSeq[int]) -> None:
        # `si`/`sd` are ghost witnesses of the intended row-label and
        # column-descriptor sequences, so the caller can relate the constructed
        # container's facets to values it still holds after the list
        # permissions move into the fields.
        Requires(Acc(list_pred(index)) and Acc(list_pred(descs)))
        Requires(ToSeq(index) == si and ToSeq(descs) == sd)
        Ensures(Acc(self.index) and self.index is index)        # type: ignore
        Ensures(Acc(self.descs) and self.descs is descs)        # type: ignore
        Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.descs)))  # type: ignore
        Ensures(ToSeq(self.index) == si)                        # type: ignore
        Ensures(ToSeq(self.descs) == sd)                        # type: ignore
        self.index = index
        self.descs = descs


# axioms-start
# (no axioms: the column-selection behaviour is a self-contained per-column
# compress over the touched facets, modelled deeply; nothing the proof needs is
# delegated to an unchanged opaque callee.)
# axioms-end


# pure-start
@Pure
def kept_descs(descs: PSeq[int], mask: PSeq[int]) -> PSeq[int]:
    """The descriptors of the retained columns, in input order: for each
    position keep the input column's descriptor exactly when its mask flag is
    set, else nothing. Front-recursive so a single unfold is available to the
    matching impl loop. Each kept descriptor is the input column's OWN
    descriptor (never a coerced shared value). Total over any pair of sequences:
    positions past the end of either sequence contribute nothing (the modelled
    inputs always have matching lengths, established by the caller)."""
    if len(descs) == 0 or len(mask) == 0:
        return PSeq(0).take(0)
    if mask[0] != 0:
        return PSeq(descs[0]) + kept_descs(descs.drop(1), mask.drop(1))
    return kept_descs(descs.drop(1), mask.drop(1))
# pure-end


def select_columns(df: Frame, mask: List[int]) -> Frame:
    # `mask` has one flag per input column (0 = drop, 1 = keep), read-only.
    # pre-conditions-start
    Requires(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
    Requires(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
    Requires(Acc(list_pred(mask), 1 / 2))
    Requires(len(df.descs) == len(mask))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs are returned at the fractional permission they were lent
    # at (the input container and the mask are never mutated).
    Ensures(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
    Ensures(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
    Ensures(Acc(list_pred(mask), 1 / 2))
    Ensures(Acc(Result().index) and Acc(Result().descs))
    Ensures(Acc(list_pred(Result().index)) and Acc(list_pred(Result().descs)))
    # (1) Per-column metadata preserved: the output column descriptors are
    # exactly the descriptors of the retained input columns, in input order
    # (each carried over unchanged — never a single coerced shared descriptor).
    Ensures(ToSeq(Result().descs) == kept_descs(ToSeq(df.descs), ToSeq(mask)))
    # (2) Row labels preserved: the output keeps the input's OWN row labels,
    # regardless of how many columns survived (including none).
    Ensures(ToSeq(Result().index) == ToSeq(df.index))
    # post-conditions-end
    # impl-start
    new_index = _copy_labels(df.index)  # type: List[int]
    new_descs = []  # type: List[int]
    i = len(df.descs)
    while i > 0:
        # invariants-start
        Invariant(Acc(df.index, 1 / 2) and Acc(df.descs, 1 / 2))
        Invariant(Acc(list_pred(df.index), 1 / 2) and Acc(list_pred(df.descs), 1 / 2))
        Invariant(Acc(list_pred(mask), 1 / 2))
        Invariant(Acc(list_pred(new_index)))
        Invariant(Acc(list_pred(new_descs)))
        Invariant(len(df.descs) == len(mask))
        Invariant(0 <= i and i <= len(df.descs))
        Invariant(ToSeq(new_index) == ToSeq(df.index))
        Invariant(ToSeq(new_descs) ==
                  kept_descs(ToSeq(df.descs).drop(i), ToSeq(mask).drop(i)))
        # invariants-end
        d = df.descs[i - 1]
        m = mask[i - 1]
        # Relate the (i-1)-suffix to the i-suffix: dropping i-1 exposes the
        # element at i-1 as the head, and its tail is the i-suffix.
        Assert(ToSeq(df.descs).drop(i - 1)[0] == d)
        Assert(ToSeq(mask).drop(i - 1)[0] == m)
        Assert(ToSeq(df.descs).drop(i - 1).drop(1) == ToSeq(df.descs).drop(i))
        Assert(ToSeq(mask).drop(i - 1).drop(1) == ToSeq(mask).drop(i))
        if m != 0:
            new_descs = [d] + new_descs
        i = i - 1
    gi = ToSeq(new_index)    # type: PSeq[int]
    gd = ToSeq(new_descs)    # type: PSeq[int]
    result = Frame(new_index, new_descs, gi, gd)  # type: Frame
    return result
    # impl-end


def _copy_labels(src: List[int]) -> List[int]:
    Requires(Acc(list_pred(src), 1 / 2))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(src))
    out = []  # type: List[int]
    i = 0
    while i < len(src):
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(src))
        Invariant(len(out) == i)
        Invariant(ToSeq(out) == ToSeq(src).take(i))
        out.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    return out
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. No same-spec, verifying wrong impl exists; the spec pins BOTH observable facets with exact functional equalities (ToSeq(Result().descs)==kept_descs(ToSeq(df.descs),ToSeq(mask)) and ToSeq(Result().index)==ToSeq(df.index)), so any verifying impl produces exactly the gold output.

ENV: module; SBU_BENCHMARK_DIR=benchmark-verified.

### BASELINE (mandatory):
- positive_control.py = bundle model.py: `adversary weakness nagini ... positive_control.py` -> CANDIDATE (verifies, 12.2s), exit 0.
- prepatch1.py (= model_prepatch.py, homogenized shared descriptor): `bash scripts/nagini_verify.sh prepatch1.py` -> Verification failed, Postcondition (1) ToSeq(Result().descs)==kept_descs(...) might not hold. exit 1. Prepatch bug REPRODUCED (spec rejects it).
- prepatch2.py (= model_prepatch_2.py, fresh positional index): `bash scripts/nagini_verify.sh prepatch2.py` -> Verification failed, Postcondition (2) ToSeq(Result().index)==ToSeq(df.index) might not hold. exit 1. Prepatch bug REPRODUCED.

atk_1 (prepatch bug re-encode: homogenized shared descriptor): weakness exit 2 (does-not-verify; spec rejected). Distinct: ungrounded-oracle/homogenization echo.
- atk_2 (prepatch bug re-encode: fresh positional index [0..n-1]): weakness exit 2.
- atk_3 (partial-domain: correct non-empty, but empty-mask returns positional index): weakness exit 2.
- atk_4 (boundary off-by-one: while i>1, skips column 0): weakness exit 2.
- atk_5 (control-flow-effect: keep ALL columns, ignore mask): weakness exit 2.
- atk_6 (invert mask: keep when m==0): weakness exit 2.
- atk_7 (alternative correct forward-iteration impl / echo): weakness exit 2 — fails on a loop-INVARIANT preservation (take-based fwd invariant vs front-recursive kept_descs), a proof-annotation shortfall, NOT the spec admitting wrong behavior; direct nagini_verify shows 'Loop invariant might not be preserved', not a postcondition weakness.
- atk_8 (index truncation: new_index=[0..len(new_descs)-1], loses rows): weakness exit 2.
Every attack: exit 2 = NOT-A-COUNTEREXAMPLE (does not verify). ZERO candidates besides the positive control.

MANDATORY CANDIDATE-RESOLVE: the only same-spec verifying impl is the positive control (= bundle model.py). Its faithful refined patch is the gold patch verbatim. Materialized to faithful_positive_control.diff and executed through the official harness: harness.run_resolve('scikit-learn__scikit-learn-25102', patch, timeout=2400) -> completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So verify==>correct for the sole verifying impl; no verify-but-not-resolve exists. Spec is NOT broken.

REFINEMENT.MD AUDIT (A-legs / correspondence): all legs are R / A-reference / I; NO kind-3, NO consumed @ContractOnly axiom (section C accurate). A1 (DataFrame X -> Frame{index,descs}) = R; A2 (bool mask -> List[int] 0/1) = R; A3 (kept_descs compress = per-column descriptor selection) = A-reference; A4 (index carry-over) = A-reference+I; A5 (empty-mask X.iloc[:,:0]) = A-reference; A6 (removed dead ValueError raise) = I, guarded by precondition len(df.descs)==len(mask); B1 (cast_to_ndarray routing plumbing) = I. A-reference correspondence VALIDATED: ran axiom_check.py (G-AX) independently in swebench-lean env (sklearn 1.3.0/pandas 3.0.5) -> exit 0, 'G-AX OK' over 5 dtype palettes x 3 indices x 4 masks + empty masks + 1500 fuzz; asserts deep model (index labels, per-column dtypes) == real post-patch _safe_indexing(X,mask,axis=1)/X.iloc[:,:0], and exhibits the pre-patch divergence (X.values[:,mask] homogenises dtypes; empty branch references absent DataFrame.dtype). The two modeled facets are exactly the F2P-observed ones (output.index, output.dtypes).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of the nagini bundle for scikit-learn__scikit-learn-25102. The spec models the changed SelectorMixin._transform column selection: postconditions pin (1) ToSeq(Result().descs) == kept_descs(ToSeq(df.descs), ToSeq(mask)) — per-column descriptors of retained columns in input order, each carried over unchanged — and (2) ToSeq(Result().index) == ToSeq(df.index) — input row labels preserved for any retained count including zero.

Real repo callee at base_commit f9a1cf07: post-patch _transform selects columns via _safe_indexing(X, mask, axis=1). Traced the dispatch in sklearn/utils/__init__.py: _determine_key_type(bool mask)=='bool' -> hasattr(X,'iloc') -> _pandas_indexing(X, mask, 'bool', axis=1) -> key_dtype!='int' so indexer=X.loc -> returns X.loc[:, mask]. A pandas .loc[:, bool_mask] column slice keeps each retained column's OWN dtype (no homogenizing coercion) and keeps X's row index. Empty-mask branch returns X.iloc[:, :0] (input index, zero columns). This is exactly the per-column compress + index carry-over the spec encodes.

Evidence: (a) axiom_check.py re-run PASS (boundary battery + 1500 fuzz, 0 disagreements). (b) Independent probe of the REAL _safe_indexing vs the deep model over dtype palettes NOT in the battery (datetime64[ns], nullable Int64, boolean, string, object, mixed category) and index shapes NOT in the battery (reversed [2,1,0], duplicate-label [5,5,6], string-labeled ['x','y','z']) with randomized masks incl. empty: 0 divergences across all cases. (c) G-CONF recorded 100255 checks / 0 disagreements.

The modeled function agrees with the real callee on every input; the spec is not too strong and does not drift. No diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Regenerated the spec view with markers.spec_view(model.py, nagini); its sha256 (2fbf1970...e213a3) matches meta.region_hashes.spec_view, so the view judged is authoritative. The spec view exposes only the abstract twin-artifact model: the docstring, `from typing import List` + nagini_contracts import, the `Frame` class, an empty axioms region, the `@Pure kept_descs` per-column compress, `select_columns`'s pre/post-conditions with the impl elided, and the `_copy_labels` helper.

Gold edit (from patch.diff / meta): base.py threads a `cast_to_ndarray` flag through `_validate_data`; `transform` computes `preserve_X = hasattr(X, "iloc") and output_config_dense == "pandas"`; and `_transform` becomes `if hasattr(X, "iloc"): return X.iloc[:, :0]` (empty mask) / `return _safe_indexing(X, mask, axis=1)` (non-empty), replacing `X[:, safe_mask(X, mask)]`.

Leakage check: the spec view names NONE of these repo-level artifacts — no `_safe_indexing`, `safe_mask`, `X[:, ...]`, `X.iloc[:, :0]`, `cast_to_ndarray`, `preserve_X`, `check_array`, `_get_output_config`, nor any `pandas`/`sklearn`/`DataFrame`/`.dtype`. The gold implementation technique is not reconstructible from any spec-view line.

Postcondition (1) 'output column descriptors are exactly the retained input columns' own descriptors, never a single coerced shared value' is a behavioral restatement of the PUBLIC problem_statement's dtype-preservation ask (categorical/float16 -> float64 coercion during pandas feature-selection output), not an edit disclosure. Postcondition (2) 'row labels preserved, including the zero-column degenerate case' is phrased purely as desired behavior; it corresponds behaviorally to the empty-mask iloc[:,:0] branch but reveals no code-level symbol or technique — and whether it broadens the spec beyond the literal issue is a spec-strength question (G-PANEL-1/2), not leakage. All gold-implementation detail (change sites, iloc[:,:0], repo symbols, prepatch reverts) lives only in meta.json / mapping.md, which are outside the solver's spec view. The lexical G-LEAK gate in meta also passed with empty failures. Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
