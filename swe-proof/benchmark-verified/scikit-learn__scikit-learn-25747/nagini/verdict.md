# P2 adversarial audit — scikit-learn__scikit-learn-25747

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -44,9 +43,6 @@
         # it still holds after the list permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(columns)))
         Requires(ToSeq(index) == si and ToSeq(columns) == sc)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)      # type: ignore
         Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.columns)))  # type: ignore
@@ -100,12 +96,6 @@
     Requires(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
     Requires(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
     Requires(nrows >= 0 and ncols >= 0)
-    # Placing the data into a container must COMPLETE (total correctness).
-    # Without this obligation every Ensures below is claimed only of runs that
-    # reach the return, so an implementation that never gets there satisfies the
-    # whole postcondition vacuously. Level 3 is strictly above every callee it
-    # invokes (the two label helpers at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().index) and Acc(Result().columns))
@@ -144,8 +134,9 @@
         if columns is not None:
             refreshed = _copy_labels(columns)  # type: List[int]
             df.columns = refreshed
-        # The supplied row labels are intentionally NOT applied here: the
-        # container keeps its own row labels.
+        if index is not None:
+            relabelled = _copy_labels(index)  # type: List[int]
+            df.index = relabelled
         return df
     new_index = []  # type: List[int]
     if index is not None:
@@ -160,50 +151,23 @@
     gi = ToSeq(new_index)    # type: PSeq[int]
     gc = ToSeq(new_columns)  # type: PSeq[int]
     result = Frame(new_index, new_columns, gi, gc)  # type: Frame
-    # Tie the constructed label values to the supplied label values (or the
-    # default positional labelling when none is supplied): the copy / fill
-    # preserved each intended sequence, so the fresh container's labels equal
-    # opt_seq of the supplied sets, or range_labels of the payload shape.
-    if index is not None:
-        Assert(gi == opt_seq(index))
-        Assert(ToSeq(result.index) == opt_seq(index))
-    else:
-        Assert(is_range(gi, nrows))
-        Assert(is_range(ToSeq(result.index), nrows))
-    if columns is not None:
-        Assert(gc == opt_seq(columns))
-        Assert(ToSeq(result.columns) == opt_seq(columns))
-    else:
-        Assert(is_range(gc, ncols))
-        Assert(is_range(ToSeq(result.columns), ncols))
     return result
     # impl-end
 
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying a label set must COMPLETE: level 2 leaves room for the list
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
@@ -212,25 +176,16 @@
 
 def _range_labels(n: int) -> List[int]:
     Requires(n >= 0)
-    # Filling the default positional labelling must COMPLETE: level 2 leaves room
-    # for the list allocation it performs, and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(is_range(ToSeq(Result()), n))
     out = []  # type: List[int]
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= n)
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
             (Implies(0 <= k and k < i, ToSeq(out)[k] == k), [[ToSeq(out)[k]]])))
-        # At most n - i + 1 passes remain: n is a by-value parameter so it cannot
-        # change, and i rises by exactly one per pass, so the bound strictly
-        # decreases; the guard i < n keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         old_seq = ToSeq(out)  # type: PSeq[int]
         out.append(i)
         Assert(ToSeq(out) == old_seq + PSeq(i))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -44,9 +43,6 @@
         # it still holds after the list permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(columns)))
         Requires(ToSeq(index) == si and ToSeq(columns) == sc)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)      # type: ignore
         Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.columns)))  # type: ignore
@@ -100,12 +96,6 @@
     Requires(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
     Requires(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
     Requires(nrows >= 0 and ncols >= 0)
-    # Placing the data into a container must COMPLETE (total correctness).
-    # Without this obligation every Ensures below is claimed only of runs that
-    # reach the return, so an implementation that never gets there satisfies the
-    # whole postcondition vacuously. Level 3 is strictly above every callee it
-    # invokes (the two label helpers at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().index) and Acc(Result().columns))
@@ -141,11 +131,9 @@
     # post-conditions-end
     # impl-start
     if data_is_frame:
-        if columns is not None:
-            refreshed = _copy_labels(columns)  # type: List[int]
-            df.columns = refreshed
-        # The supplied row labels are intentionally NOT applied here: the
-        # container keeps its own row labels.
+        if index is not None:
+            wrong = _copy_labels(index)  # type: List[int]
+            df.columns = wrong
         return df
     new_index = []  # type: List[int]
     if index is not None:
@@ -160,50 +148,23 @@
     gi = ToSeq(new_index)    # type: PSeq[int]
     gc = ToSeq(new_columns)  # type: PSeq[int]
     result = Frame(new_index, new_columns, gi, gc)  # type: Frame
-    # Tie the constructed label values to the supplied label values (or the
-    # default positional labelling when none is supplied): the copy / fill
-    # preserved each intended sequence, so the fresh container's labels equal
-    # opt_seq of the supplied sets, or range_labels of the payload shape.
-    if index is not None:
-        Assert(gi == opt_seq(index))
-        Assert(ToSeq(result.index) == opt_seq(index))
-    else:
-        Assert(is_range(gi, nrows))
-        Assert(is_range(ToSeq(result.index), nrows))
-    if columns is not None:
-        Assert(gc == opt_seq(columns))
-        Assert(ToSeq(result.columns) == opt_seq(columns))
-    else:
-        Assert(is_range(gc, ncols))
-        Assert(is_range(ToSeq(result.columns), ncols))
     return result
     # impl-end
 
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying a label set must COMPLETE: level 2 leaves room for the list
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
@@ -212,25 +173,16 @@
 
 def _range_labels(n: int) -> List[int]:
     Requires(n >= 0)
-    # Filling the default positional labelling must COMPLETE: level 2 leaves room
-    # for the list allocation it performs, and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(is_range(ToSeq(Result()), n))
     out = []  # type: List[int]
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= n)
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
             (Implies(0 <= k and k < i, ToSeq(out)[k] == k), [[ToSeq(out)[k]]])))
-        # At most n - i + 1 passes remain: n is a by-value parameter so it cannot
-        # change, and i rises by exactly one per pass, so the bound strictly
-        # decreases; the guard i < n keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         old_seq = ToSeq(out)  # type: PSeq[int]
         out.append(i)
         Assert(ToSeq(out) == old_seq + PSeq(i))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -44,9 +43,6 @@
         # it still holds after the list permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(columns)))
         Requires(ToSeq(index) == si and ToSeq(columns) == sc)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)      # type: ignore
         Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.columns)))  # type: ignore
@@ -100,12 +96,6 @@
     Requires(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
     Requires(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
     Requires(nrows >= 0 and ncols >= 0)
-    # Placing the data into a container must COMPLETE (total correctness).
-    # Without this obligation every Ensures below is claimed only of runs that
-    # reach the return, so an implementation that never gets there satisfies the
-    # whole postcondition vacuously. Level 3 is strictly above every callee it
-    # invokes (the two label helpers at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().index) and Acc(Result().columns))
@@ -144,14 +134,12 @@
         if columns is not None:
             refreshed = _copy_labels(columns)  # type: List[int]
             df.columns = refreshed
-        # The supplied row labels are intentionally NOT applied here: the
-        # container keeps its own row labels.
         return df
     new_index = []  # type: List[int]
     if index is not None:
         new_index = _copy_labels(index)
     else:
-        new_index = _range_labels(nrows)
+        new_index = _range_labels(ncols)
     new_columns = []  # type: List[int]
     if columns is not None:
         new_columns = _copy_labels(columns)
@@ -160,50 +148,23 @@
     gi = ToSeq(new_index)    # type: PSeq[int]
     gc = ToSeq(new_columns)  # type: PSeq[int]
     result = Frame(new_index, new_columns, gi, gc)  # type: Frame
-    # Tie the constructed label values to the supplied label values (or the
-    # default positional labelling when none is supplied): the copy / fill
-    # preserved each intended sequence, so the fresh container's labels equal
-    # opt_seq of the supplied sets, or range_labels of the payload shape.
-    if index is not None:
-        Assert(gi == opt_seq(index))
-        Assert(ToSeq(result.index) == opt_seq(index))
-    else:
-        Assert(is_range(gi, nrows))
-        Assert(is_range(ToSeq(result.index), nrows))
-    if columns is not None:
-        Assert(gc == opt_seq(columns))
-        Assert(ToSeq(result.columns) == opt_seq(columns))
-    else:
-        Assert(is_range(gc, ncols))
-        Assert(is_range(ToSeq(result.columns), ncols))
     return result
     # impl-end
 
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying a label set must COMPLETE: level 2 leaves room for the list
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
@@ -212,25 +173,16 @@
 
 def _range_labels(n: int) -> List[int]:
     Requires(n >= 0)
-    # Filling the default positional labelling must COMPLETE: level 2 leaves room
-    # for the list allocation it performs, and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(is_range(ToSeq(Result()), n))
     out = []  # type: List[int]
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= n)
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
             (Implies(0 <= k and k < i, ToSeq(out)[k] == k), [[ToSeq(out)[k]]])))
-        # At most n - i + 1 passes remain: n is a by-value parameter so it cannot
-        # change, and i rises by exactly one per pass, so the bound strictly
-        # decreases; the guard i < n keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         old_seq = ToSeq(out)  # type: PSeq[int]
         out.append(i)
         Assert(ToSeq(out) == old_seq + PSeq(i))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -44,9 +43,6 @@
         # it still holds after the list permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(columns)))
         Requires(ToSeq(index) == si and ToSeq(columns) == sc)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)      # type: ignore
         Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.columns)))  # type: ignore
@@ -100,12 +96,6 @@
     Requires(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
     Requires(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
     Requires(nrows >= 0 and ncols >= 0)
-    # Placing the data into a container must COMPLETE (total correctness).
-    # Without this obligation every Ensures below is claimed only of runs that
-    # reach the return, so an implementation that never gets there satisfies the
-    # whole postcondition vacuously. Level 3 is strictly above every callee it
-    # invokes (the two label helpers at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().index) and Acc(Result().columns))
@@ -144,8 +134,9 @@
         if columns is not None:
             refreshed = _copy_labels(columns)  # type: List[int]
             df.columns = refreshed
-        # The supplied row labels are intentionally NOT applied here: the
-        # container keeps its own row labels.
+        else:
+            filler = _range_labels(ncols)  # type: List[int]
+            df.columns = filler
         return df
     new_index = []  # type: List[int]
     if index is not None:
@@ -160,50 +151,23 @@
     gi = ToSeq(new_index)    # type: PSeq[int]
     gc = ToSeq(new_columns)  # type: PSeq[int]
     result = Frame(new_index, new_columns, gi, gc)  # type: Frame
-    # Tie the constructed label values to the supplied label values (or the
-    # default positional labelling when none is supplied): the copy / fill
-    # preserved each intended sequence, so the fresh container's labels equal
-    # opt_seq of the supplied sets, or range_labels of the payload shape.
-    if index is not None:
-        Assert(gi == opt_seq(index))
-        Assert(ToSeq(result.index) == opt_seq(index))
-    else:
-        Assert(is_range(gi, nrows))
-        Assert(is_range(ToSeq(result.index), nrows))
-    if columns is not None:
-        Assert(gc == opt_seq(columns))
-        Assert(ToSeq(result.columns) == opt_seq(columns))
-    else:
-        Assert(is_range(gc, ncols))
-        Assert(is_range(ToSeq(result.columns), ncols))
     return result
     # impl-end
 
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying a label set must COMPLETE: level 2 leaves room for the list
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
@@ -212,25 +176,16 @@
 
 def _range_labels(n: int) -> List[int]:
     Requires(n >= 0)
-    # Filling the default positional labelling must COMPLETE: level 2 leaves room
-    # for the list allocation it performs, and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(is_range(ToSeq(Result()), n))
     out = []  # type: List[int]
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= n)
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
             (Implies(0 <= k and k < i, ToSeq(out)[k] == k), [[ToSeq(out)[k]]])))
-        # At most n - i + 1 passes remain: n is a by-value parameter so it cannot
-        # change, and i rises by exactly one per pass, so the bound strictly
-        # decreases; the guard i < n keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         old_seq = ToSeq(out)  # type: PSeq[int]
         out.append(i)
         Assert(ToSeq(out) == old_seq + PSeq(i))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -44,9 +43,6 @@
         # it still holds after the list permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(columns)))
         Requires(ToSeq(index) == si and ToSeq(columns) == sc)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)      # type: ignore
         Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.columns)))  # type: ignore
@@ -100,12 +96,6 @@
     Requires(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
     Requires(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
     Requires(nrows >= 0 and ncols >= 0)
-    # Placing the data into a container must COMPLETE (total correctness).
-    # Without this obligation every Ensures below is claimed only of runs that
-    # reach the return, so an implementation that never gets there satisfies the
-    # whole postcondition vacuously. Level 3 is strictly above every callee it
-    # invokes (the two label helpers at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().index) and Acc(Result().columns))
@@ -144,14 +134,8 @@
         if columns is not None:
             refreshed = _copy_labels(columns)  # type: List[int]
             df.columns = refreshed
-        # The supplied row labels are intentionally NOT applied here: the
-        # container keeps its own row labels.
         return df
-    new_index = []  # type: List[int]
-    if index is not None:
-        new_index = _copy_labels(index)
-    else:
-        new_index = _range_labels(nrows)
+    new_index = _range_labels(nrows)  # type: List[int]
     new_columns = []  # type: List[int]
     if columns is not None:
         new_columns = _copy_labels(columns)
@@ -160,50 +144,23 @@
     gi = ToSeq(new_index)    # type: PSeq[int]
     gc = ToSeq(new_columns)  # type: PSeq[int]
     result = Frame(new_index, new_columns, gi, gc)  # type: Frame
-    # Tie the constructed label values to the supplied label values (or the
-    # default positional labelling when none is supplied): the copy / fill
-    # preserved each intended sequence, so the fresh container's labels equal
-    # opt_seq of the supplied sets, or range_labels of the payload shape.
-    if index is not None:
-        Assert(gi == opt_seq(index))
-        Assert(ToSeq(result.index) == opt_seq(index))
-    else:
-        Assert(is_range(gi, nrows))
-        Assert(is_range(ToSeq(result.index), nrows))
-    if columns is not None:
-        Assert(gc == opt_seq(columns))
-        Assert(ToSeq(result.columns) == opt_seq(columns))
-    else:
-        Assert(is_range(gc, ncols))
-        Assert(is_range(ToSeq(result.columns), ncols))
     return result
     # impl-end
 
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying a label set must COMPLETE: level 2 leaves room for the list
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
@@ -212,25 +169,16 @@
 
 def _range_labels(n: int) -> List[int]:
     Requires(n >= 0)
-    # Filling the default positional labelling must COMPLETE: level 2 leaves room
-    # for the list allocation it performs, and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(is_range(ToSeq(Result()), n))
     out = []  # type: List[int]
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= n)
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
             (Implies(0 <= k and k < i, ToSeq(out)[k] == k), [[ToSeq(out)[k]]])))
-        # At most n - i + 1 passes remain: n is a by-value parameter so it cannot
-        # change, and i rises by exactly one per pass, so the bound strictly
-        # decreases; the guard i < n keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         old_seq = ToSeq(out)  # type: PSeq[int]
         out.append(i)
         Assert(ToSeq(out) == old_seq + PSeq(i))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -44,9 +43,6 @@
         # it still holds after the list permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(columns)))
         Requires(ToSeq(index) == si and ToSeq(columns) == sc)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)      # type: ignore
         Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.columns)))  # type: ignore
@@ -100,12 +96,6 @@
     Requires(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
     Requires(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
     Requires(nrows >= 0 and ncols >= 0)
-    # Placing the data into a container must COMPLETE (total correctness).
-    # Without this obligation every Ensures below is claimed only of runs that
-    # reach the return, so an implementation that never gets there satisfies the
-    # whole postcondition vacuously. Level 3 is strictly above every callee it
-    # invokes (the two label helpers at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().index) and Acc(Result().columns))
@@ -141,12 +131,14 @@
     # post-conditions-end
     # impl-start
     if data_is_frame:
+        keep_i = _copy_labels(df.index)   # type: List[int]
+        keep_c = _copy_labels(df.columns)  # type: List[int]
         if columns is not None:
-            refreshed = _copy_labels(columns)  # type: List[int]
-            df.columns = refreshed
-        # The supplied row labels are intentionally NOT applied here: the
-        # container keeps its own row labels.
-        return df
+            keep_c = _copy_labels(columns)
+        ki = ToSeq(keep_i)  # type: PSeq[int]
+        kc = ToSeq(keep_c)  # type: PSeq[int]
+        clone = Frame(keep_i, keep_c, ki, kc)  # type: Frame
+        return clone
     new_index = []  # type: List[int]
     if index is not None:
         new_index = _copy_labels(index)
@@ -160,50 +152,23 @@
     gi = ToSeq(new_index)    # type: PSeq[int]
     gc = ToSeq(new_columns)  # type: PSeq[int]
     result = Frame(new_index, new_columns, gi, gc)  # type: Frame
-    # Tie the constructed label values to the supplied label values (or the
-    # default positional labelling when none is supplied): the copy / fill
-    # preserved each intended sequence, so the fresh container's labels equal
-    # opt_seq of the supplied sets, or range_labels of the payload shape.
-    if index is not None:
-        Assert(gi == opt_seq(index))
-        Assert(ToSeq(result.index) == opt_seq(index))
-    else:
-        Assert(is_range(gi, nrows))
-        Assert(is_range(ToSeq(result.index), nrows))
-    if columns is not None:
-        Assert(gc == opt_seq(columns))
-        Assert(ToSeq(result.columns) == opt_seq(columns))
-    else:
-        Assert(is_range(gc, ncols))
-        Assert(is_range(ToSeq(result.columns), ncols))
     return result
     # impl-end
 
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying a label set must COMPLETE: level 2 leaves room for the list
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
@@ -212,25 +177,16 @@
 
 def _range_labels(n: int) -> List[int]:
     Requires(n >= 0)
-    # Filling the default positional labelling must COMPLETE: level 2 leaves room
-    # for the list allocation it performs, and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(is_range(ToSeq(Result()), n))
     out = []  # type: List[int]
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= n)
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
             (Implies(0 <= k and k < i, ToSeq(out)[k] == k), [[ToSeq(out)[k]]])))
-        # At most n - i + 1 passes remain: n is a by-value parameter so it cannot
-        # change, and i rises by exactly one per pass, so the bound strictly
-        # decreases; the guard i < n keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         old_seq = ToSeq(out)  # type: PSeq[int]
         out.append(i)
         Assert(ToSeq(out) == old_seq + PSeq(i))
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Frame:
@@ -44,9 +43,6 @@
         # it still holds after the list permissions move into the fields.
         Requires(Acc(list_pred(index)) and Acc(list_pred(columns)))
         Requires(ToSeq(index) == si and ToSeq(columns) == sc)
-        # Constructing a container is a bounded step (two field writes); its
-        # level (1) sits strictly below every method that allocates one.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.index) and self.index is index)      # type: ignore
         Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
         Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.columns)))  # type: ignore
@@ -100,12 +96,6 @@
     Requires(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
     Requires(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
     Requires(nrows >= 0 and ncols >= 0)
-    # Placing the data into a container must COMPLETE (total correctness).
-    # Without this obligation every Ensures below is claimed only of runs that
-    # reach the return, so an implementation that never gets there satisfies the
-    # whole postcondition vacuously. Level 3 is strictly above every callee it
-    # invokes (the two label helpers at 2, the container constructor at 1).
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().index) and Acc(Result().columns))
@@ -142,39 +132,26 @@
     # impl-start
     if data_is_frame:
         if columns is not None:
-            refreshed = _copy_labels(columns)  # type: List[int]
-            df.columns = refreshed
-        # The supplied row labels are intentionally NOT applied here: the
-        # container keeps its own row labels.
+            df.columns = _copy_labels(columns)
         return df
-    new_index = []  # type: List[int]
+    if columns is not None:
+        nc = _copy_labels(columns)  # type: List[int]
+    else:
+        nc = _range_labels(ncols)
     if index is not None:
-        new_index = _copy_labels(index)
+        ni = _copy_labels(index)  # type: List[int]
     else:
-        new_index = _range_labels(nrows)
-    new_columns = []  # type: List[int]
-    if columns is not None:
-        new_columns = _copy_labels(columns)
-    else:
-        new_columns = _range_labels(ncols)
-    gi = ToSeq(new_index)    # type: PSeq[int]
-    gc = ToSeq(new_columns)  # type: PSeq[int]
-    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
-    # Tie the constructed label values to the supplied label values (or the
-    # default positional labelling when none is supplied): the copy / fill
-    # preserved each intended sequence, so the fresh container's labels equal
-    # opt_seq of the supplied sets, or range_labels of the payload shape.
+        ni = _range_labels(nrows)
+    gi = ToSeq(ni)  # type: PSeq[int]
+    gc = ToSeq(nc)  # type: PSeq[int]
+    result = Frame(ni, nc, gi, gc)  # type: Frame
     if index is not None:
-        Assert(gi == opt_seq(index))
         Assert(ToSeq(result.index) == opt_seq(index))
     else:
-        Assert(is_range(gi, nrows))
         Assert(is_range(ToSeq(result.index), nrows))
     if columns is not None:
-        Assert(gc == opt_seq(columns))
         Assert(ToSeq(result.columns) == opt_seq(columns))
     else:
-        Assert(is_range(gc, ncols))
         Assert(is_range(ToSeq(result.columns), ncols))
     return result
     # impl-end
@@ -182,28 +159,17 @@
 
 def _copy_labels(src: List[int]) -> List[int]:
     Requires(Acc(list_pred(src), 1 / 2))
-    # Copying a label set must COMPLETE: level 2 leaves room for the list
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
@@ -212,25 +178,16 @@
 
 def _range_labels(n: int) -> List[int]:
     Requires(n >= 0)
-    # Filling the default positional labelling must COMPLETE: level 2 leaves room
-    # for the list allocation it performs, and sits strictly below its caller's 3.
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(Result())))
     Ensures(is_range(ToSeq(Result()), n))
     out = []  # type: List[int]
     i = 0
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= n)
         Invariant(len(out) == i)
         Invariant(Forall(int, lambda k:
             (Implies(0 <= k and k < i, ToSeq(out)[k] == k), [[ToSeq(out)[k]]])))
-        # At most n - i + 1 passes remain: n is a by-value parameter so it cannot
-        # change, and i rises by exactly one per pass, so the bound strictly
-        # decreases; the guard i < n keeps it >= 2 on entry to a pass.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         old_seq = ToSeq(out)  # type: PSeq[int]
         out.append(i)
         Assert(ToSeq(out) == old_seq + PSeq(i))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-25747.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A helper places transformed data into a labelled tabular container so the
  configured output format is honoured. Its row labels (the container's
  "index") and column labels are governed by two rules that depend on whether
  the data handed in is ALREADY a labelled tabular container:

    (1) When the incoming data is already a labelled container, the helper
        keeps that container's OWN row labels untouched. A transformer is free
        to change the number of rows (e.g. by aggregating), so the helper must
        NOT overwrite the container's row labels with a separately supplied set
        of labels — even when such a set is supplied. Only the column labels
        are refreshed, and only when a replacement set is supplied; otherwise
        both label axes are left exactly as they were.

    (2) When the incoming data is NOT already a labelled container, the helper
        builds a fresh container, stamping each axis with the supplied set of
        labels for that axis when one is given; when no set is supplied for an
        axis, that axis receives the default positional labelling
        ``[0, 1, ..., k-1]`` sized to the data payload (k = the payload's row
        count for the row axis, its column count for the column axis).

The labelled container is modelled as a minimal class carrying only its two
touched facets — its row labels and its column labels, each a sequence of
label codes (``List[int]``). The two optional supplied label sets are modelled
as ``Optional[List[int]]`` (read-only); the payload's row/column counts are the
``nrows``/``ncols`` parameters. Sequence values are compared via the pure
``PSeq[int]`` theory (``ToSeq``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class Frame:
    def __init__(self, index: List[int], columns: List[int],
                 si: PSeq[int], sc: PSeq[int]) -> None:
        # `si`/`sc` are ghost witnesses of the intended label sequences, so the
        # caller can relate the constructed container's label values to values
        # it still holds after the list permissions move into the fields.
        Requires(Acc(list_pred(index)) and Acc(list_pred(columns)))
        Requires(ToSeq(index) == si and ToSeq(columns) == sc)
        Ensures(Acc(self.index) and self.index is index)      # type: ignore
        Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
        Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.columns)))  # type: ignore
        Ensures(ToSeq(self.index) == si)   # type: ignore
        Ensures(ToSeq(self.columns) == sc)  # type: ignore
        self.index = index
        self.columns = columns


# axioms-start
# (no axioms: the behaviour is a self-contained labelling rule; both the
# in-place relabelling of an existing container and the construction of a fresh
# container are modelled deeply over the touched facets.)
# axioms-end


# pure-start
@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The sequence value of an optional label set: its element sequence when a
    set is supplied, the empty sequence when none is. Guards the None-case so
    the spec can compare supplied-label values without indexing through None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)


@Pure
def is_range(s: PSeq[int], n: int) -> bool:
    """``s`` is the default positional labelling ``[0, 1, ..., n-1]`` for an axis
    of length ``n``: it has exactly ``n`` elements and element ``k`` is ``k``.
    This is the label set a fresh container assigns to an axis when no
    replacement set is supplied for it (a default positional labelling)."""
    return len(s) == n and Forall(int, lambda k:
        (Implies(0 <= k and k < n, s[k] == k), [[s[k]]]))
# pure-end


def wrap_in_container(data_is_frame: bool,
                      df: Frame,
                      columns: Optional[List[int]],
                      index: Optional[List[int]],
                      nrows: int,
                      ncols: int) -> Frame:
    # `nrows`/`ncols` are the row/column counts of the data payload being
    # placed into the container (the shape the fresh container is built from).
    # pre-conditions-start
    Requires(Acc(df.index) and Acc(df.columns))
    Requires(Acc(list_pred(df.index)) and Acc(list_pred(df.columns)))
    Requires(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
    Requires(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
    Requires(nrows >= 0 and ncols >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().index) and Acc(Result().columns))
    Ensures(Acc(list_pred(Result().index)) and Acc(list_pred(Result().columns)))
    # Read-only supplied label sets are returned at the fractional permission
    # they were lent at (they are never mutated).
    Ensures(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
    Ensures(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
    # (1) Already-a-container branch: the SAME container is returned, its row
    # labels are kept exactly as they were on entry (the discriminating
    # guarantee: a separately supplied set of row labels never overrides them),
    # and its column labels are refreshed only when a replacement set is given.
    Ensures(Implies(data_is_frame, Result() is df))
    Ensures(Implies(data_is_frame,
                    ToSeq(Result().index) == Old(ToSeq(df.index))))
    Ensures(Implies(data_is_frame and columns is not None,
                    ToSeq(Result().columns) == opt_seq(columns)))
    Ensures(Implies(data_is_frame and columns is None,
                    ToSeq(Result().columns) == Old(ToSeq(df.columns))))
    # (2) Not-a-container branch: a fresh container stamped with the supplied
    # row labels and column labels. When a label set is NOT supplied for an
    # axis, that axis gets the default positional labelling [0, 1, ..., k-1]
    # sized to the data payload (k = nrows for the row axis, ncols for the
    # column axis) — NOT an arbitrary set of labels.
    Ensures(Implies(not data_is_frame and index is not None,
                    ToSeq(Result().index) == opt_seq(index)))
    Ensures(Implies(not data_is_frame and index is None,
                    is_range(ToSeq(Result().index), nrows)))
    Ensures(Implies(not data_is_frame and columns is not None,
                    ToSeq(Result().columns) == opt_seq(columns)))
    Ensures(Implies(not data_is_frame and columns is None,
                    is_range(ToSeq(Result().columns), ncols)))
    # post-conditions-end
    # impl-start
    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    # Tie the constructed label values to the supplied label values (or the
    # default positional labelling when none is supplied): the copy / fill
    # preserved each intended sequence, so the fresh container's labels equal
    # opt_seq of the supplied sets, or range_labels of the payload shape.
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
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


def _range_labels(n: int) -> List[int]:
    Requires(n >= 0)
    Ensures(Acc(list_pred(Result())))
    Ensures(is_range(ToSeq(Result()), n))
    out = []  # type: List[int]
    i = 0
    while i < n:
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= n)
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k:
            (Implies(0 <= k and k < i, ToSeq(out)[k] == k), [[ToSeq(out)[k]]])))
        old_seq = ToSeq(out)  # type: PSeq[int]
        out.append(i)
        Assert(ToSeq(out) == old_seq + PSeq(i))
        Assert(len(ToSeq(out)) == i + 1)
        Assert(Forall(int, lambda k:
            (Implies(0 <= k and k < i, ToSeq(out)[k] == old_seq[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == i)
        i = i + 1
    return out
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec = wrap_in_container in model.py; only its impl region (lines 133-169) is elided in the spec view, so only that region was edited. Contracts, @Pure helpers (opt_seq/is_range), and the _copy_labels/_range_labels bodies are part of the spec signature and were left byte-identical; all 7 attacks pass `same-spec` (exit 0). The spec pins EVERY observable facet: FRAME branch -> Result() is df, ToSeq(Result().index)==Old(ToSeq(df.index)) (own index preserved regardless of a supplied index), columns refreshed to opt_seq(columns) iff supplied else kept; ARRAY branch -> both axes pinned to opt_seq(supplied) or is_range([0..k-1], nrows/ncols) at BOTH corners. No unconstrained degree of freedom remains.

ATTACKS (weakness = same-spec AND verifies; run via `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-25747 <atk>` with SBU_BENCHMARK_DIR=benchmark-verified):
- atk_1 PREPATCH reproduction (re-adds deleted DataFrame-branch index write): weakness exit=2, does NOT verify. Failure detail: `Postcondition ... Implies(data_is_frame, ToSeq(Result().index)==Old(ToSeq(df.index))) might not hold` at atk_1.py:112 -> the discriminating clause rejects the bug. prepatch_reproduced=true.
- atk_2 control-flow-effect (frame branch applies supplied index to the COLUMNS axis): weakness exit=2, does NOT verify.
- atk_3 boundary/off-by-axis (array index=None uses _range_labels(ncols) not nrows): weakness exit=2, does NOT verify.
- atk_4 ungrounded-oracle (frame branch, columns None -> overwrite columns with range(ncols) instead of keeping own): weakness exit=2, does NOT verify.
- atk_5 partial-domain (array branch ignores supplied index, always range): weakness exit=2, does NOT verify. Failure detail: `Postcondition ... Implies(not data_is_frame and index is not None, ToSeq(Result().index)==opt_seq(index)) might not hold` at atk_5.py:123.
- atk_6 identity-break (frame branch returns a fresh Frame copying df's labels, not df): weakness exit=2, does NOT verify (violates Result() is df / permission structure).
- atk_7 ECHO gold-equivalent (behaviourally the post-patch helper, reordered/renamed): weakness exit=0 = CANDIDATE (shares spec AND verifies, 14.5s). Per 2026-08-06 policy a resolving echo is NOT a weakness. MANDATORY resolve step EXECUTED: materialized faithful refined patch (atk_7_refined.patch == gold patch) and ran swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-25747', ...) -> RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. F2P test_set_output_pandas_keep_index PASSED; all 14 PASS_TO_PASS passed. So verify=>resolve holds for the only candidate; no verify AND not-resolve pair exists.

Positive control: model.py copy verifies (exit 0, 14.03s) via scripts/nagini_verify.sh.

A-LEG / refinement.md audit: NO consumed @ContractOnly axiom (axioms region empty). Legs A1-A7 are R (type refinement) / I (identical concrete op); discriminating leg A5 (deletion of the DataFrame-branch index write) is modelled directly by omitting the write, sensed by the index-preservation postcondition (confirmed by atk_1's rejection). Exactly ONE A-reference (B1): the whole wrap_in_container deep model validated == the real post-patch _wrap_in_pandas_container by axiom_check.py (G-AX). Re-ran axiom_check.py (swebench-lean env, numpy 1.26.4 / pandas 3.0.5) -> RC=0: fidelity over boundary battery + 2000 fuzz on BOTH corners of BOTH axes on both branches, own-index preservation, and pre-patch divergence raising the reported length-mismatch ValueError in the aggregation case. meta.json deep_model_references matches B1. No kind-3 (unexpressible-changed-op) leg. A-reference correspondence to the real callee holds.

CONCLUSION: >=6 distinct wrong impls (incl. prepatch) all REJECTED by the spec; the only verifying candidate (echo) resolves. verify(model) => resolved is not broken. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-25747.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A helper places transformed data into a labelled tabular container so the
  configured output format is honoured. Its row labels (the container's
  "index") and column labels are governed by two rules that depend on whether
  the data handed in is ALREADY a labelled tabular container:

    (1) When the incoming data is already a labelled container, the helper
        keeps that container's OWN row labels untouched. A transformer is free
        to change the number of rows (e.g. by aggregating), so the helper must
        NOT overwrite the container's row labels with a separately supplied set
        of labels — even when such a set is supplied. Only the column labels
        are refreshed, and only when a replacement set is supplied; otherwise
        both label axes are left exactly as they were.

    (2) When the incoming data is NOT already a labelled container, the helper
        builds a fresh container, stamping each axis with the supplied set of
        labels for that axis when one is given; when no set is supplied for an
        axis, that axis receives the default positional labelling
        ``[0, 1, ..., k-1]`` sized to the data payload (k = the payload's row
        count for the row axis, its column count for the column axis).

The labelled container is modelled as a minimal class carrying only its two
touched facets — its row labels and its column labels, each a sequence of
label codes (``List[int]``). The two optional supplied label sets are modelled
as ``Optional[List[int]]`` (read-only); the payload's row/column counts are the
``nrows``/``ncols`` parameters. Sequence values are compared via the pure
``PSeq[int]`` theory (``ToSeq``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class Frame:
    def __init__(self, index: List[int], columns: List[int],
                 si: PSeq[int], sc: PSeq[int]) -> None:
        # `si`/`sc` are ghost witnesses of the intended label sequences, so the
        # caller can relate the constructed container's label values to values
        # it still holds after the list permissions move into the fields.
        Requires(Acc(list_pred(index)) and Acc(list_pred(columns)))
        Requires(ToSeq(index) == si and ToSeq(columns) == sc)
        Ensures(Acc(self.index) and self.index is index)      # type: ignore
        Ensures(Acc(self.columns) and self.columns is columns)  # type: ignore
        Ensures(Acc(list_pred(self.index)) and Acc(list_pred(self.columns)))  # type: ignore
        Ensures(ToSeq(self.index) == si)   # type: ignore
        Ensures(ToSeq(self.columns) == sc)  # type: ignore
        self.index = index
        self.columns = columns


# axioms-start
# (no axioms: the behaviour is a self-contained labelling rule; both the
# in-place relabelling of an existing container and the construction of a fresh
# container are modelled deeply over the touched facets.)
# axioms-end


# pure-start
@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The sequence value of an optional label set: its element sequence when a
    set is supplied, the empty sequence when none is. Guards the None-case so
    the spec can compare supplied-label values without indexing through None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)


@Pure
def is_range(s: PSeq[int], n: int) -> bool:
    """``s`` is the default positional labelling ``[0, 1, ..., n-1]`` for an axis
    of length ``n``: it has exactly ``n`` elements and element ``k`` is ``k``.
    This is the label set a fresh container assigns to an axis when no
    replacement set is supplied for it (a default positional labelling)."""
    return len(s) == n and Forall(int, lambda k:
        (Implies(0 <= k and k < n, s[k] == k), [[s[k]]]))
# pure-end


def wrap_in_container(data_is_frame: bool,
                      df: Frame,
                      columns: Optional[List[int]],
                      index: Optional[List[int]],
                      nrows: int,
                      ncols: int) -> Frame:
    # `nrows`/`ncols` are the row/column counts of the data payload being
    # placed into the container (the shape the fresh container is built from).
    # pre-conditions-start
    Requires(Acc(df.index) and Acc(df.columns))
    Requires(Acc(list_pred(df.index)) and Acc(list_pred(df.columns)))
    Requires(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
    Requires(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
    Requires(nrows >= 0 and ncols >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().index) and Acc(Result().columns))
    Ensures(Acc(list_pred(Result().index)) and Acc(list_pred(Result().columns)))
    # Read-only supplied label sets are returned at the fractional permission
    # they were lent at (they are never mutated).
    Ensures(Implies(columns is not None, Acc(list_pred(columns), 1 / 2)))
    Ensures(Implies(index is not None, Acc(list_pred(index), 1 / 2)))
    # (1) Already-a-container branch: the SAME container is returned, its row
    # labels are kept exactly as they were on entry (the discriminating
    # guarantee: a separately supplied set of row labels never overrides them),
    # and its column labels are refreshed only when a replacement set is given.
    Ensures(Implies(data_is_frame, Result() is df))
    Ensures(Implies(data_is_frame,
                    ToSeq(Result().index) == Old(ToSeq(df.index))))
    Ensures(Implies(data_is_frame and columns is not None,
                    ToSeq(Result().columns) == opt_seq(columns)))
    Ensures(Implies(data_is_frame and columns is None,
                    ToSeq(Result().columns) == Old(ToSeq(df.columns))))
    # (2) Not-a-container branch: a fresh container stamped with the supplied
    # row labels and column labels. When a label set is NOT supplied for an
    # axis, that axis gets the default positional labelling [0, 1, ..., k-1]
    # sized to the data payload (k = nrows for the row axis, ncols for the
    # column axis) — NOT an arbitrary set of labels.
    Ensures(Implies(not data_is_frame and index is not None,
                    ToSeq(Result().index) == opt_seq(index)))
    Ensures(Implies(not data_is_frame and index is None,
                    is_range(ToSeq(Result().index), nrows)))
    Ensures(Implies(not data_is_frame and columns is not None,
                    ToSeq(Result().columns) == opt_seq(columns)))
    Ensures(Implies(not data_is_frame and columns is None,
                    is_range(ToSeq(Result().columns), ncols)))
    # post-conditions-end
    # impl-start
    if data_is_frame:
        if columns is not None:
            refreshed = _copy_labels(columns)  # type: List[int]
            df.columns = refreshed
        # The supplied row labels are intentionally NOT applied here: the
        # container keeps its own row labels.
        return df
    new_index = []  # type: List[int]
    if index is not None:
        new_index = _copy_labels(index)
    else:
        new_index = _range_labels(nrows)
    new_columns = []  # type: List[int]
    if columns is not None:
        new_columns = _copy_labels(columns)
    else:
        new_columns = _range_labels(ncols)
    gi = ToSeq(new_index)    # type: PSeq[int]
    gc = ToSeq(new_columns)  # type: PSeq[int]
    result = Frame(new_index, new_columns, gi, gc)  # type: Frame
    # Tie the constructed label values to the supplied label values (or the
    # default positional labelling when none is supplied): the copy / fill
    # preserved each intended sequence, so the fresh container's labels equal
    # opt_seq of the supplied sets, or range_labels of the payload shape.
    if index is not None:
        Assert(gi == opt_seq(index))
        Assert(ToSeq(result.index) == opt_seq(index))
    else:
        Assert(is_range(gi, nrows))
        Assert(is_range(ToSeq(result.index), nrows))
    if columns is not None:
        Assert(gc == opt_seq(columns))
        Assert(ToSeq(result.columns) == opt_seq(columns))
    else:
        Assert(is_range(gc, ncols))
        Assert(is_range(ToSeq(result.columns), ncols))
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


def _range_labels(n: int) -> List[int]:
    Requires(n >= 0)
    Ensures(Acc(list_pred(Result())))
    Ensures(is_range(ToSeq(Result()), n))
    out = []  # type: List[int]
    i = 0
    while i < n:
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= n)
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k:
            (Implies(0 <= k and k < i, ToSeq(out)[k] == k), [[ToSeq(out)[k]]])))
        old_seq = ToSeq(out)  # type: PSeq[int]
        out.append(i)
        Assert(ToSeq(out) == old_seq + PSeq(i))
        Assert(len(ToSeq(out)) == i + 1)
        Assert(Forall(int, lambda k:
            (Implies(0 <= k and k < i, ToSeq(out)[k] == old_seq[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == i)
        i = i + 1
    return out
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec = wrap_in_container in model.py; only its impl region (lines 133-169) is elided in the spec view, so only that region was edited. Contracts, @Pure helpers (opt_seq/is_range), and the _copy_labels/_range_labels bodies are part of the spec signature and were left byte-identical; all 7 attacks pass `same-spec` (exit 0). The spec pins EVERY observable facet: FRAME branch -> Result() is df, ToSeq(Result().index)==Old(ToSeq(df.index)) (own index preserved regardless of a supplied index), columns refreshed to opt_seq(columns) iff supplied else kept; ARRAY branch -> both axes pinned to opt_seq(supplied) or is_range([0..k-1], nrows/ncols) at BOTH corners. No unconstrained degree of freedom remains.

ATTACKS (weakness = same-spec AND verifies; run via `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-25747 <atk>` with SBU_BENCHMARK_DIR=benchmark-verified):
- atk_1 PREPATCH reproduction (re-adds deleted DataFrame-branch index write): weakness exit=2, does NOT verify. Failure detail: `Postcondition ... Implies(data_is_frame, ToSeq(Result().index)==Old(ToSeq(df.index))) might not hold` at atk_1.py:112 -> the discriminating clause rejects the bug. prepatch_reproduced=true.
- atk_2 control-flow-effect (frame branch applies supplied index to the COLUMNS axis): weakness exit=2, does NOT verify.
- atk_3 boundary/off-by-axis (array index=None uses _range_labels(ncols) not nrows): weakness exit=2, does NOT verify.
- atk_4 ungrounded-oracle (frame branch, columns None -> overwrite columns with range(ncols) instead of keeping own): weakness exit=2, does NOT verify.
- atk_5 partial-domain (array branch ignores supplied index, always range): weakness exit=2, does NOT verify. Failure detail: `Postcondition ... Implies(not data_is_frame and index is not None, ToSeq(Result().index)==opt_seq(index)) might not hold` at atk_5.py:123.
- atk_6 identity-break (frame branch returns a fresh Frame copying df's labels, not df): weakness exit=2, does NOT verify (violates Result() is df / permission structure).
- atk_7 ECHO gold-equivalent (behaviourally the post-patch helper, reordered/renamed): weakness exit=0 = CANDIDATE (shares spec AND verifies, 14.5s). Per 2026-08-06 policy a resolving echo is NOT a weakness. MANDATORY resolve step EXECUTED: materialized faithful refined patch (atk_7_refined.patch == gold patch) and ran swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-25747', ...) -> RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. F2P test_set_output_pandas_keep_index PASSED; all 14 PASS_TO_PASS passed. So verify=>resolve holds for the only candidate; no verify AND not-resolve pair exists.

Positive control: model.py copy verifies (exit 0, 14.03s) via scripts/nagini_verify.sh.

A-LEG / refinement.md audit: NO consumed @ContractOnly axiom (axioms region empty). Legs A1-A7 are R (type refinement) / I (identical concrete op); discriminating leg A5 (deletion of the DataFrame-branch index write) is modelled directly by omitting the write, sensed by the index-preservation postcondition (confirmed by atk_1's rejection). Exactly ONE A-reference (B1): the whole wrap_in_container deep model validated == the real post-patch _wrap_in_pandas_container by axiom_check.py (G-AX). Re-ran axiom_check.py (swebench-lean env, numpy 1.26.4 / pandas 3.0.5) -> RC=0: fidelity over boundary battery + 2000 fuzz on BOTH corners of BOTH axes on both branches, own-index preservation, and pre-patch divergence raising the reported length-mismatch ValueError in the aggregation case. meta.json deep_model_references matches B1. No kind-3 (unexpressible-changed-op) leg. A-reference correspondence to the real callee holds.

CONCLUSION: >=6 distinct wrong impls (incl. prepatch) all REJECTED by the spec; the only verifying candidate (echo) resolves. verify(model) => resolved is not broken. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The worktree holds the PRE-patch (buggy) code (index-write at _set_output.py:58-59 still present); the callee under specification is the POST-patch helper, which the gold patch produces by deleting that write. Checks: (1) nagini_verify.sh model.py -> Verification successful (12.2s). (2) axiom_check.py G-AX -> exit 0. (3) Direct probes vs real pandas: frame branch keeps its OWN index regardless of supplied index (spec: ToSeq(Result().index)==Old(ToSeq(df.index)) — the whole content of the fix, agree); columns refreshed only when supplied (agree); array branch default RangeIndex(k) on unsupplied axes, incl. empty 0x0 (agree). The discriminating postcondition precisely pins own-index preservation; model_prepatch reintroduces the write and fails it. The only model/real gap is the disclosed label-code abstraction (str/hashable labels <-> List[int], mapping.md §2-3) plus the raises-domain gap above — neither weakens the spec on any gold-relevant input. Spec region byte-verified consistent with the verified/prepatch pair. Verdict FAITHFUL.

Counterexample / evidence:

```
None on-domain. Nagini models total functions and cannot express `raises`; the modeled function's domain is the shape-consistent inputs, which covers every F2P/P2P test and realistic caller. On that entire domain the modeled `wrap_in_container` agrees with the post-patch `_wrap_in_pandas_container` (verified by axiom_check.py: boundary battery + 2000 fuzz, exit 0, on real pandas 3.0.5) and by direct probes.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen over the spec view (model.py) passes with zero hard failures (verified via leakage.screen with the nagini backend). Semantic assessment: the spec view is model.py's docstring + Frame/wrap_in_container contracts, expressed over an abstract Frame/List[int] carrier as DESIRED behaviour, not as an edit. The discriminating guarantee (Ensures(Implies(data_is_frame, ToSeq(Result().index)==Old(ToSeq(df.index)))) plus the docstring 'keeps that container's OWN row labels untouched ... must NOT overwrite ... even when such a set is supplied') describes the fixed behaviour abstractly. Crucially, the PUBLIC problem_statement already discloses far more concretely than the spec: it contains the full traceback naming sklearn/utils/_set_output.py:59, the exact offending line `data_to_wrap.index = index`, and the exact `ValueError: Length mismatch: Expected axis has 4 elements, new values have 96 elements` for the aggregation case. So the spec view reveals nothing about the gold edit's location/identity beyond the public statement. The gold-quoting text (deleted `if index is not None: data_to_wrap.index = index` lines) lives only in refinement.md / mapping.md, which are audit artifacts, NOT the solver-facing spec view screened by G-LEAK. No spec-view line names the gold patch, the changed file, or the deleted lines.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
