# P2 adversarial audit — django__django-16263

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk8.py`, `atk9.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk2.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -132,53 +132,7 @@
     )
     # post-conditions-end
     # impl-start
-    found = False
-    i = len(selected)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(selected), 1 / 2))
-        Invariant(Acc(list_pred(summ), 1 / 2))
-        Invariant(len(selected) == len(summ))
-        Invariant(0 <= i and i <= len(selected))
-        Invariant(len(ToSeq(selected).drop(i)) == len(ToSeq(summ).drop(i)))
-        Invariant(
-            found
-            == any_selected_summary(ToSeq(selected).drop(i), ToSeq(summ).drop(i))
-        )
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        s = selected[i - 1]
-        m = summ[i - 1]
-        Assert(ToSeq(selected).drop(i - 1)[0] == s)
-        Assert(ToSeq(selected).drop(i - 1).drop(1) == ToSeq(selected).drop(i))
-        Assert(ToSeq(summ).drop(i - 1)[0] == m)
-        Assert(ToSeq(summ).drop(i - 1).drop(1) == ToSeq(summ).drop(i))
-        Assert(len(ToSeq(selected).drop(i - 1)) == len(ToSeq(summ).drop(i - 1)))
-        # any_selected_summary(drop(i-1)) unfolds to its head bit OR the tail
-        # (== drop(i)); this links the loop body's update to the fold.
-        Assert(
-            any_selected_summary(
-                ToSeq(selected).drop(i - 1), ToSeq(summ).drop(i - 1)
-            )
-            == (
-                (s != 0 and m != 0)
-                or any_selected_summary(
-                    ToSeq(selected).drop(i), ToSeq(summ).drop(i)
-                )
-            )
-        )
-        if s != 0 and m != 0:
-            found = True
-        i = i - 1
-    # At exit i == 0: drop(0) is the full sequence, so the invariant gives
-    # found == any_selected_summary(full). Surface the length equality the
-    # postcondition's own call needs.
-    Assert(ToSeq(selected).drop(0) == ToSeq(selected))
-    Assert(ToSeq(summ).drop(0) == ToSeq(summ))
-    Assert(len(ToSeq(selected)) == len(ToSeq(summ)))
-    return found or filter_summary != 0
+    return True
     # impl-end
 
 
```

Attack 2 — `atk2.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -132,53 +132,9 @@
     )
     # post-conditions-end
     # impl-start
-    found = False
-    i = len(selected)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(selected), 1 / 2))
-        Invariant(Acc(list_pred(summ), 1 / 2))
-        Invariant(len(selected) == len(summ))
-        Invariant(0 <= i and i <= len(selected))
-        Invariant(len(ToSeq(selected).drop(i)) == len(ToSeq(summ).drop(i)))
-        Invariant(
-            found
-            == any_selected_summary(ToSeq(selected).drop(i), ToSeq(summ).drop(i))
-        )
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        s = selected[i - 1]
-        m = summ[i - 1]
-        Assert(ToSeq(selected).drop(i - 1)[0] == s)
-        Assert(ToSeq(selected).drop(i - 1).drop(1) == ToSeq(selected).drop(i))
-        Assert(ToSeq(summ).drop(i - 1)[0] == m)
-        Assert(ToSeq(summ).drop(i - 1).drop(1) == ToSeq(summ).drop(i))
-        Assert(len(ToSeq(selected).drop(i - 1)) == len(ToSeq(summ).drop(i - 1)))
-        # any_selected_summary(drop(i-1)) unfolds to its head bit OR the tail
-        # (== drop(i)); this links the loop body's update to the fold.
-        Assert(
-            any_selected_summary(
-                ToSeq(selected).drop(i - 1), ToSeq(summ).drop(i - 1)
-            )
-            == (
-                (s != 0 and m != 0)
-                or any_selected_summary(
-                    ToSeq(selected).drop(i), ToSeq(summ).drop(i)
-                )
-            )
-        )
-        if s != 0 and m != 0:
-            found = True
-        i = i - 1
-    # At exit i == 0: drop(0) is the full sequence, so the invariant gives
-    # found == any_selected_summary(full). Surface the length equality the
-    # postcondition's own call needs.
-    Assert(ToSeq(selected).drop(0) == ToSeq(selected))
-    Assert(ToSeq(summ).drop(0) == ToSeq(summ))
-    Assert(len(ToSeq(selected)) == len(ToSeq(summ)))
-    return found or filter_summary != 0
+    while True:
+        pass
+    return filter_summary != 0
     # impl-end
 
 
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -225,30 +225,5 @@
         if c == alias:
             in_added = True
         i = i - 1
-    in_refs = False
-    j = len(ref_tree)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(ref_tree), 1 / 2))
-        Invariant(0 <= j and j <= len(ref_tree))
-        Invariant(in_refs == seq_contains(collect_refs(ToSeq(ref_tree).drop(j)), alias))
-        # The loop consumes the termination obligation: j is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(j))
-        # invariants-end
-        node = ref_tree[j - 1]
-        Assert(ToSeq(ref_tree).drop(j - 1)[0] == node)
-        Assert(ToSeq(ref_tree).drop(j - 1).drop(1) == ToSeq(ref_tree).drop(j))
-        if node != 0:
-            # collect_refs unfolds to PSeq(node) + collect_refs(drop(j)); the
-            # singleton head's first element is node and its tail is the rest.
-            tail_refs = collect_refs(ToSeq(ref_tree).drop(j))  # type: PSeq[int]
-            cons = PSeq(node) + tail_refs  # type: PSeq[int]
-            Assert(cons[0] == node)
-            Assert(cons.drop(1) == tail_refs)
-            Assert(seq_contains(cons, alias) == (node == alias or seq_contains(tail_refs, alias)))
-        if node != 0 and node == alias:
-            in_refs = True
-        j = j - 1
-    return in_added or in_refs
+    return in_added
     # impl-end
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -208,47 +208,5 @@
     )
     # post-conditions-end
     # impl-start
-    in_added = False
-    i = len(added)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(added), 1 / 2))
-        Invariant(0 <= i and i <= len(added))
-        Invariant(in_added == seq_contains(ToSeq(added).drop(i), alias))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        c = added[i - 1]
-        Assert(ToSeq(added).drop(i - 1)[0] == c)
-        Assert(ToSeq(added).drop(i - 1).drop(1) == ToSeq(added).drop(i))
-        if c == alias:
-            in_added = True
-        i = i - 1
-    in_refs = False
-    j = len(ref_tree)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(ref_tree), 1 / 2))
-        Invariant(0 <= j and j <= len(ref_tree))
-        Invariant(in_refs == seq_contains(collect_refs(ToSeq(ref_tree).drop(j)), alias))
-        # The loop consumes the termination obligation: j is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(j))
-        # invariants-end
-        node = ref_tree[j - 1]
-        Assert(ToSeq(ref_tree).drop(j - 1)[0] == node)
-        Assert(ToSeq(ref_tree).drop(j - 1).drop(1) == ToSeq(ref_tree).drop(j))
-        if node != 0:
-            # collect_refs unfolds to PSeq(node) + collect_refs(drop(j)); the
-            # singleton head's first element is node and its tail is the rest.
-            tail_refs = collect_refs(ToSeq(ref_tree).drop(j))  # type: PSeq[int]
-            cons = PSeq(node) + tail_refs  # type: PSeq[int]
-            Assert(cons[0] == node)
-            Assert(cons.drop(1) == tail_refs)
-            Assert(seq_contains(cons, alias) == (node == alias or seq_contains(tail_refs, alias)))
-        if node != 0 and node == alias:
-            in_refs = True
-        j = j - 1
-    return in_added or in_refs
+    return True
     # impl-end
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -133,51 +133,16 @@
     # post-conditions-end
     # impl-start
     found = False
-    i = len(selected)
+    i = len(summ)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(selected), 1 / 2))
         Invariant(Acc(list_pred(summ), 1 / 2))
-        Invariant(len(selected) == len(summ))
-        Invariant(0 <= i and i <= len(selected))
-        Invariant(len(ToSeq(selected).drop(i)) == len(ToSeq(summ).drop(i)))
-        Invariant(
-            found
-            == any_selected_summary(ToSeq(selected).drop(i), ToSeq(summ).drop(i))
-        )
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
+        Invariant(0 <= i and i <= len(summ))
         Invariant(MustTerminate(i))
-        # invariants-end
-        s = selected[i - 1]
         m = summ[i - 1]
-        Assert(ToSeq(selected).drop(i - 1)[0] == s)
-        Assert(ToSeq(selected).drop(i - 1).drop(1) == ToSeq(selected).drop(i))
-        Assert(ToSeq(summ).drop(i - 1)[0] == m)
-        Assert(ToSeq(summ).drop(i - 1).drop(1) == ToSeq(summ).drop(i))
-        Assert(len(ToSeq(selected).drop(i - 1)) == len(ToSeq(summ).drop(i - 1)))
-        # any_selected_summary(drop(i-1)) unfolds to its head bit OR the tail
-        # (== drop(i)); this links the loop body's update to the fold.
-        Assert(
-            any_selected_summary(
-                ToSeq(selected).drop(i - 1), ToSeq(summ).drop(i - 1)
-            )
-            == (
-                (s != 0 and m != 0)
-                or any_selected_summary(
-                    ToSeq(selected).drop(i), ToSeq(summ).drop(i)
-                )
-            )
-        )
-        if s != 0 and m != 0:
+        if m != 0:
             found = True
         i = i - 1
-    # At exit i == 0: drop(0) is the full sequence, so the invariant gives
-    # found == any_selected_summary(full). Surface the length equality the
-    # postcondition's own call needs.
-    Assert(ToSeq(selected).drop(0) == ToSeq(selected))
-    Assert(ToSeq(summ).drop(0) == ToSeq(summ))
-    Assert(len(ToSeq(selected)) == len(ToSeq(summ)))
     return found or filter_summary != 0
     # impl-end
 
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -134,7 +134,7 @@
     # impl-start
     found = False
     i = len(selected)
-    while i > 0:
+    while i > 1:
         # invariants-start
         Invariant(Acc(list_pred(selected), 1 / 2))
         Invariant(Acc(list_pred(summ), 1 / 2))
```

Attack 7 — `atk8.py` → rejected (same spec, does not verify — good)

```diff
@@ -208,47 +208,7 @@
     )
     # post-conditions-end
     # impl-start
-    in_added = False
-    i = len(added)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(added), 1 / 2))
-        Invariant(0 <= i and i <= len(added))
-        Invariant(in_added == seq_contains(ToSeq(added).drop(i), alias))
-        # The loop consumes the termination obligation: i is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(i))
-        # invariants-end
-        c = added[i - 1]
-        Assert(ToSeq(added).drop(i - 1)[0] == c)
-        Assert(ToSeq(added).drop(i - 1).drop(1) == ToSeq(added).drop(i))
-        if c == alias:
-            in_added = True
-        i = i - 1
-    in_refs = False
-    j = len(ref_tree)
-    while j > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(ref_tree), 1 / 2))
-        Invariant(0 <= j and j <= len(ref_tree))
-        Invariant(in_refs == seq_contains(collect_refs(ToSeq(ref_tree).drop(j)), alias))
-        # The loop consumes the termination obligation: j is the strictly
-        # decreasing, bounded-below measure.
-        Invariant(MustTerminate(j))
-        # invariants-end
-        node = ref_tree[j - 1]
-        Assert(ToSeq(ref_tree).drop(j - 1)[0] == node)
-        Assert(ToSeq(ref_tree).drop(j - 1).drop(1) == ToSeq(ref_tree).drop(j))
-        if node != 0:
-            # collect_refs unfolds to PSeq(node) + collect_refs(drop(j)); the
-            # singleton head's first element is node and its tail is the rest.
-            tail_refs = collect_refs(ToSeq(ref_tree).drop(j))  # type: PSeq[int]
-            cons = PSeq(node) + tail_refs  # type: PSeq[int]
-            Assert(cons[0] == node)
-            Assert(cons.drop(1) == tail_refs)
-            Assert(seq_contains(cons, alias) == (node == alias or seq_contains(tail_refs, alias)))
-        if node != 0 and node == alias:
-            in_refs = True
-        j = j - 1
-    return in_added or in_refs
+    while True:
+        pass
+    return False
     # impl-end
```

Attack 8 — `atk9.py` → rejected (same spec, does not verify — good)

```diff
@@ -169,7 +169,7 @@
                 )
             )
         )
-        if s != 0 and m != 0:
+        if s != 0 or m != 0:
             found = True
         i = i - 1
     # At exit i == 0: drop(0) is the full sequence, so the invariant gives
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16263.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A row-count over a query that already carries some annotated columns must
  return the same count as the same query without those annotated columns, and
  emitted query must not carry annotated columns that nothing in the count
  refers to. Two decisions realise this:

  (1) WHETHER the count must be computed over a derived (inner) query because of
      the pre-existing annotated columns. Only the annotated columns that are
      actually SELECTED by the query participate in this decision; an annotated
      column that the query merely keeps as a private alias (never selected)
      does not participate. Among the selected annotated columns, one forces the
      derived-query form only when it actually summarises rows (it is itself a
      row-summary, or such a summary is exercised by a retained filter); a
      selected column that summarises nothing and is not filtered on must NOT,
      by itself, force the derived form. (Other independent reasons for a
      derived query — slicing, distinctness, set operations, explicit grouping —
      are out of scope of this decision.)

  (2) WHICH pre-existing annotated columns remain referenced by the inner query
      when a derived query IS used. Only the annotated columns that the count's
      own expressions actually refer to may remain; every other pre-existing
      annotated column is dropped. An annotated column's name is kept exactly
      when it is one of the count's own names OR it is referred to (transitively)
      by one of the count's expressions. The names referred to by an expression
      are the union of the names referred to by its sub-expressions, with a bare
      reference contributing its own referent.

The query's annotated columns are modelled by minimal parallel carriers over
`List[int]` of name/reference codes, a per-column selected flag, and a per-column
summary flag (Nagini bans `str` indexing and cannot carry the live ORM objects).
The reference-gathering fold and the two decisions are spelled out deeply over
those carriers; the equality of the fold to the real reference-gatherer is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Both decisions are bounded scans over finite carriers and MUST terminate and
actually deliver their answer (a total-correctness obligation, carried as
MustTerminate in each precondition): Nagini verifies partial correctness by
default, so without the obligation a diverging implementation (e.g. an
endless loop before the return) would satisfy every Ensures vacuously while
never returning the decision to its caller.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. Both decisions and the reference-gathering fold are pure
# structural logic over the annotated-column carriers, modelled deeply. The deep
# reference fold (`collect_refs`) is validated == the real recursive
# reference-gatherer out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end

# pure-start
@Pure
def any_selected_summary(selected: PSeq[int], summ: PSeq[int]) -> bool:
    """True iff some pre-existing annotated column is BOTH selected by the query
    AND carries a row-summary, i.e. for some index k both `selected[k]` and
    `summ[k]` are non-zero. Front-recursive so a single unfold is available per
    loop step; the two carriers are stepped in lock-step. Total over any pair of
    lengths (both guards) so no equal-length precondition is needed at recursion
    or at the postcondition call site; the carriers are equal-length by the
    decision's own Requires."""
    if len(selected) == 0 or len(summ) == 0:
        return False
    return (selected[0] != 0 and summ[0] != 0) or any_selected_summary(
        selected.drop(1), summ.drop(1)
    )

@Pure
def collect_refs(tree: PSeq[int]) -> PSeq[int]:
    """References reachable from an expression, modelled as the sequence of all
    reference leaves in the expression's flattened tree. A node carrying a
    positive code is a bare reference contributing its referent and is a LEAF
    (its own referent only — its source is not descended into, matching the real
    leaf reference-gatherer); a node coded 0 is a non-referencing sub-expression
    contributing nothing but whose children are still folded. The references of
    a composite expression are the union (here, concatenation; membership is what
    the decision observes) of its sub-expressions' references. Front-recursive
    for a single unfold per step."""
    if len(tree) == 0:
        return PSeq(0).take(0)
    if tree[0] != 0:
        return PSeq(tree[0]) + collect_refs(tree.drop(1))
    return collect_refs(tree.drop(1))

@Pure
def seq_contains(s: PSeq[int], x: int) -> bool:
    """Membership of a code in a sequence. Front-recursive."""
    if len(s) == 0:
        return False
    return s[0] == x or seq_contains(s.drop(1), x)
# pure-end

def existing_summary_forces_derived(
    selected: List[int], summ: List[int], filter_summary: int
) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(selected), 1 / 2))
    Requires(Acc(list_pred(summ), 1 / 2))
    Requires(len(selected) == len(summ))
    # TERMINATION: deciding the derived-query form is one bounded backward
    # pass over the finite carriers and must actually ANSWER. Nagini verifies
    # partial correctness by default, so without this obligation a diverging
    # implementation (e.g. `while True: pass` before the return) satisfies
    # every Ensures vacuously; the real decision always returns to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(selected), 1 / 2))
    Ensures(Acc(list_pred(summ), 1 / 2))
    # The derived form is forced exactly when some SELECTED pre-existing
    # annotated column carries a row-summary OR a retained filter does. A column
    # that is not selected does NOT participate, and a selected column that is
    # not a row-summary does NOT by itself force the derived form.
    Ensures(
        Result()
        == (
            any_selected_summary(ToSeq(selected), ToSeq(summ))
            or filter_summary != 0
        )
    )
    # post-conditions-end
    # impl-start
    found = False
    i = len(selected)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(selected), 1 / 2))
        Invariant(Acc(list_pred(summ), 1 / 2))
        Invariant(len(selected) == len(summ))
        Invariant(0 <= i and i <= len(selected))
        Invariant(len(ToSeq(selected).drop(i)) == len(ToSeq(summ).drop(i)))
        Invariant(
            found
            == any_selected_summary(ToSeq(selected).drop(i), ToSeq(summ).drop(i))
        )
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        s = selected[i - 1]
        m = summ[i - 1]
        Assert(ToSeq(selected).drop(i - 1)[0] == s)
        Assert(ToSeq(selected).drop(i - 1).drop(1) == ToSeq(selected).drop(i))
        Assert(ToSeq(summ).drop(i - 1)[0] == m)
        Assert(ToSeq(summ).drop(i - 1).drop(1) == ToSeq(summ).drop(i))
        Assert(len(ToSeq(selected).drop(i - 1)) == len(ToSeq(summ).drop(i - 1)))
        # any_selected_summary(drop(i-1)) unfolds to its head bit OR the tail
        # (== drop(i)); this links the loop body's update to the fold.
        Assert(
            any_selected_summary(
                ToSeq(selected).drop(i - 1), ToSeq(summ).drop(i - 1)
            )
            == (
                (s != 0 and m != 0)
                or any_selected_summary(
                    ToSeq(selected).drop(i), ToSeq(summ).drop(i)
                )
            )
        )
        if s != 0 and m != 0:
            found = True
        i = i - 1
    # At exit i == 0: drop(0) is the full sequence, so the invariant gives
    # found == any_selected_summary(full). Surface the length equality the
    # postcondition's own call needs.
    Assert(ToSeq(selected).drop(0) == ToSeq(selected))
    Assert(ToSeq(summ).drop(0) == ToSeq(summ))
    Assert(len(ToSeq(selected)) == len(ToSeq(summ)))
    return found or filter_summary != 0
    # impl-end

def inner_column_kept(alias: int, added: List[int], ref_tree: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(added), 1 / 2))
    Requires(Acc(list_pred(ref_tree), 1 / 2))
    # TERMINATION: the keep-or-prune decision is two bounded backward passes
    # over the finite name/reference carriers and must actually ANSWER.
    # Without this obligation a diverging implementation satisfies every
    # Ensures vacuously; the real keep-or-prune computation always returns
    # its verdict for each name.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(added), 1 / 2))
    Ensures(Acc(list_pred(ref_tree), 1 / 2))
    # A pre-existing annotated column's name is retained in the inner query
    # exactly when it is one of the count's own names OR it is referred to by one
    # of the count's expressions (per the reachable-reference fold).
    Ensures(
        Result()
        == (
            seq_contains(ToSeq(added), alias)
            or seq_contains(collect_refs(ToSeq(ref_tree)), alias)
        )
    )
    # post-conditions-end
    # impl-start
    in_added = False
    i = len(added)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(added), 1 / 2))
        Invariant(0 <= i and i <= len(added))
        Invariant(in_added == seq_contains(ToSeq(added).drop(i), alias))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        c = added[i - 1]
        Assert(ToSeq(added).drop(i - 1)[0] == c)
        Assert(ToSeq(added).drop(i - 1).drop(1) == ToSeq(added).drop(i))
        if c == alias:
            in_added = True
        i = i - 1
    in_refs = False
    j = len(ref_tree)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(ref_tree), 1 / 2))
        Invariant(0 <= j and j <= len(ref_tree))
        Invariant(in_refs == seq_contains(collect_refs(ToSeq(ref_tree).drop(j)), alias))
        # The loop consumes the termination obligation: j is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(j))
        # invariants-end
        node = ref_tree[j - 1]
        Assert(ToSeq(ref_tree).drop(j - 1)[0] == node)
        Assert(ToSeq(ref_tree).drop(j - 1).drop(1) == ToSeq(ref_tree).drop(j))
        if node != 0:
            # collect_refs unfolds to PSeq(node) + collect_refs(drop(j)); the
            # singleton head's first element is node and its tail is the rest.
            tail_refs = collect_refs(ToSeq(ref_tree).drop(j))  # type: PSeq[int]
            cons = PSeq(node) + tail_refs  # type: PSeq[int]
            Assert(cons[0] == node)
            Assert(cons.drop(1) == tail_refs)
            Assert(seq_contains(cons, alias) == (node == alias or seq_contains(tail_refs, alias)))
        if node != 0 and node == alias:
            in_refs = True
        j = j - 1
    return in_added or in_refs
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 Bundle has NO consumed axioms; one A-reference (collect_refs == real get_refs, Ref-as-leaf). Focus was the A-legs + model<->patch correspondence.

MECHANISM: same_spec freezes everything except impl regions. Both contracts pin Result() EXACTLY to frozen @Pure expressions (existing_summary_forces_derived: Result()==(any_selected_summary(ToSeq(selected),ToSeq(summ)) or filter_summary!=0); inner_column_kept: Result()==(seq_contains(ToSeq(added),alias) or seq_contains(collect_refs(ToSeq(ref_tree)),alias))), each guarded by Requires(MustTerminate(2)). So any terminating same-spec impl must return exactly the spec value or FAIL; the only break routes are non-termination escaping MustTerminate or a verifier cheat.

### ATTACKS (all same-spec confirmed via `adversary same-spec`; all run through `nagini_verify.sh` / `adversary weakness`):
- atk1 esfd return True (control-flow, ignores inputs) -> FAIL Postcondition (17.0s).
- atk2 esfd `while True: pass` before correct return (non-term) -> NOT JUDGED, Nagini rejects at translation: `Type error: dead.code @137` (16.9s) -- it never reached the verifier, so the spec never ruled on it and it counts in neither tally; the shape is unexpressible in Nagini's fragment, so this attack does not exercise the spec's method-level MustTerminate either way.
- atk3 ick added-loop only, drops refs pass (partial-domain) -> FAIL Postcondition (26.3s).
- atk4 ick return True (re-encode prepatch_2 bug) -> FAIL Postcondition (17.7s).
- atk5 esfd summ-only ignoring `selected` (re-encode prepatch_3 axis-1 bug) -> FAIL Postcondition (19.5s).
- atk6 esfd off-by-one `while i>1` (boundary) -> FAIL Postcondition (20.6s).
- atk7 esfd forward-scan alternate-CORRECT (echo) -> CANDIDATE: verifies 21.8s; faithful patch (=gold) RESOLVED=True. NOT a break.
- atk8 ick `while True: pass` (non-term, MustTerminate on inner_column_kept) -> FAIL 'Obligation leak check failed. Loop might not take all unsatisfied obligations' (18.9s) -> confirms MustTerminate genuinely enforced.
- atk9 esfd and->or logic bug (ungrounded-oracle echo) -> FAIL 'Loop invariant might not be preserved' (23.2s).
positive_control (frozen model) VERIFIES (17.3s) -> plumbing/positive control good.

### Commands
  python -m swebench_unified.adversary same-spec nagini django__django-16263 <atk>  (all SAME)
  bash scripts/nagini_verify.sh <atk>  (wrong impls exit 1; positive_control/atk7 exit 0)
  python -m swebench_unified.adversary weakness nagini django__django-16263 atk7.py  -> CANDIDATE (exit 0)
  run_resolve('django__django-16263', atk7_faithful_patch.diff) -> resolved=True.

A-REFERENCE AUDIT (G-AX): axiom_check.py run independently in a /tmp django-4.2 venv -> EXIT 0 ('collect_refs deep model == real get_refs, Ref-as-leaf, sound on 12 boundary + 5000 fuzz trees whose Ref sources are themselves Ref-bearing'). Independently confirmed the discriminating leaf semantics with real Django: get_refs(Ref('outer',Ref('inner',Sum('x'))))=={'outer'} (NOT {'outer','inner'}), Concat(Ref('a',Ref('b',..)),Ref('c',..))=={'a','c'}, Avg(Ref('authors_count',..))=={'authors_count'}, Count('*')==set() -- matching the non-descending flatten in collect_refs. The A-reference correspondence holds and is non-trivial (the nested-Ref-in-source region is exercised).

REFINEMENT.MD LEG AUDIT: axioms region empty (no A-consumed). A0/A1/A2 = R (per-column selected/summ/filter bits, grounded in axiom_check _selected_bit/_summary_bit/split_having_qualify); A3/A4 = I over R; B1 = R; B2 = I; B3 = A-reference (collect_refs==get_refs); B4 = I + A-reference; B5 = I; C1 = A-reference (deep fold). ALL legs are R / I / A-reference -- NO kind-3 (unexpressible-changed-op) step. The two genuinely-changed ops (wrapping discriminator both axes; inner-mask) are modelled deeply over List[int] carriers; the new recursive get_refs is the deep A-reference model, not hidden behind a @ContractOnly axiom.

CONCLUSION: Spec is TIGHT -- every distinct wrong impl Nagini could translate (control-flow, partial-domain, boundary, source/predicate-axis, logic-flip, the ick non-termination class) FAILS verification; the esfd non-termination shape (atk2) was refused by the front end, so it is evidence for neither side and leaves untested whether the spec would reject a translatable esfd diverging rival; the only verifying candidate is an alternate-correct echo whose materialized faithful patch RESOLVES under the official harness. No verifying wrong impl exists. G-EQ = SOUND.

NOTE ON RECORDED STATE: meta.json currently records G-EQ=fail / G-PANEL-1=fail both with note 'INCONCLUSIVE -- 1 attack(s) inconclusive' and agent_verdict SOUND -- a stale pre-completion verdict (the prior pass never finished the candidate's resolve run). This re-adjudication completes that missing resolve (atk7 -> resolved=True), converting the inconclusive to SOUND per the 2026-08-06 resolve policy.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk8.py`, `atk9.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk2.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk8.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16263.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A row-count over a query that already carries some annotated columns must
  return the same count as the same query without those annotated columns, and
  emitted query must not carry annotated columns that nothing in the count
  refers to. Two decisions realise this:

  (1) WHETHER the count must be computed over a derived (inner) query because of
      the pre-existing annotated columns. Only the annotated columns that are
      actually SELECTED by the query participate in this decision; an annotated
      column that the query merely keeps as a private alias (never selected)
      does not participate. Among the selected annotated columns, one forces the
      derived-query form only when it actually summarises rows (it is itself a
      row-summary, or such a summary is exercised by a retained filter); a
      selected column that summarises nothing and is not filtered on must NOT,
      by itself, force the derived form. (Other independent reasons for a
      derived query — slicing, distinctness, set operations, explicit grouping —
      are out of scope of this decision.)

  (2) WHICH pre-existing annotated columns remain referenced by the inner query
      when a derived query IS used. Only the annotated columns that the count's
      own expressions actually refer to may remain; every other pre-existing
      annotated column is dropped. An annotated column's name is kept exactly
      when it is one of the count's own names OR it is referred to (transitively)
      by one of the count's expressions. The names referred to by an expression
      are the union of the names referred to by its sub-expressions, with a bare
      reference contributing its own referent.

The query's annotated columns are modelled by minimal parallel carriers over
`List[int]` of name/reference codes, a per-column selected flag, and a per-column
summary flag (Nagini bans `str` indexing and cannot carry the live ORM objects).
The reference-gathering fold and the two decisions are spelled out deeply over
those carriers; the equality of the fold to the real reference-gatherer is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Both decisions are bounded scans over finite carriers and MUST terminate and
actually deliver their answer (a total-correctness obligation, carried as
MustTerminate in each precondition): Nagini verifies partial correctness by
default, so without the obligation a diverging implementation (e.g. an
endless loop before the return) would satisfy every Ensures vacuously while
never returning the decision to its caller.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. Both decisions and the reference-gathering fold are pure
# structural logic over the annotated-column carriers, modelled deeply. The deep
# reference fold (`collect_refs`) is validated == the real recursive
# reference-gatherer out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end

# pure-start
@Pure
def any_selected_summary(selected: PSeq[int], summ: PSeq[int]) -> bool:
    """True iff some pre-existing annotated column is BOTH selected by the query
    AND carries a row-summary, i.e. for some index k both `selected[k]` and
    `summ[k]` are non-zero. Front-recursive so a single unfold is available per
    loop step; the two carriers are stepped in lock-step. Total over any pair of
    lengths (both guards) so no equal-length precondition is needed at recursion
    or at the postcondition call site; the carriers are equal-length by the
    decision's own Requires."""
    if len(selected) == 0 or len(summ) == 0:
        return False
    return (selected[0] != 0 and summ[0] != 0) or any_selected_summary(
        selected.drop(1), summ.drop(1)
    )

@Pure
def collect_refs(tree: PSeq[int]) -> PSeq[int]:
    """References reachable from an expression, modelled as the sequence of all
    reference leaves in the expression's flattened tree. A node carrying a
    positive code is a bare reference contributing its referent and is a LEAF
    (its own referent only — its source is not descended into, matching the real
    leaf reference-gatherer); a node coded 0 is a non-referencing sub-expression
    contributing nothing but whose children are still folded. The references of
    a composite expression are the union (here, concatenation; membership is what
    the decision observes) of its sub-expressions' references. Front-recursive
    for a single unfold per step."""
    if len(tree) == 0:
        return PSeq(0).take(0)
    if tree[0] != 0:
        return PSeq(tree[0]) + collect_refs(tree.drop(1))
    return collect_refs(tree.drop(1))

@Pure
def seq_contains(s: PSeq[int], x: int) -> bool:
    """Membership of a code in a sequence. Front-recursive."""
    if len(s) == 0:
        return False
    return s[0] == x or seq_contains(s.drop(1), x)
# pure-end

def existing_summary_forces_derived(
    selected: List[int], summ: List[int], filter_summary: int
) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(selected), 1 / 2))
    Requires(Acc(list_pred(summ), 1 / 2))
    Requires(len(selected) == len(summ))
    # TERMINATION: deciding the derived-query form is one bounded backward
    # pass over the finite carriers and must actually ANSWER. Nagini verifies
    # partial correctness by default, so without this obligation a diverging
    # implementation (e.g. `while True: pass` before the return) satisfies
    # every Ensures vacuously; the real decision always returns to its caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(selected), 1 / 2))
    Ensures(Acc(list_pred(summ), 1 / 2))
    # The derived form is forced exactly when some SELECTED pre-existing
    # annotated column carries a row-summary OR a retained filter does. A column
    # that is not selected does NOT participate, and a selected column that is
    # not a row-summary does NOT by itself force the derived form.
    Ensures(
        Result()
        == (
            any_selected_summary(ToSeq(selected), ToSeq(summ))
            or filter_summary != 0
        )
    )
    # post-conditions-end
    # impl-start
    found = False
    i = len(selected)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(selected), 1 / 2))
        Invariant(Acc(list_pred(summ), 1 / 2))
        Invariant(len(selected) == len(summ))
        Invariant(0 <= i and i <= len(selected))
        Invariant(len(ToSeq(selected).drop(i)) == len(ToSeq(summ).drop(i)))
        Invariant(
            found
            == any_selected_summary(ToSeq(selected).drop(i), ToSeq(summ).drop(i))
        )
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        s = selected[i - 1]
        m = summ[i - 1]
        Assert(ToSeq(selected).drop(i - 1)[0] == s)
        Assert(ToSeq(selected).drop(i - 1).drop(1) == ToSeq(selected).drop(i))
        Assert(ToSeq(summ).drop(i - 1)[0] == m)
        Assert(ToSeq(summ).drop(i - 1).drop(1) == ToSeq(summ).drop(i))
        Assert(len(ToSeq(selected).drop(i - 1)) == len(ToSeq(summ).drop(i - 1)))
        # any_selected_summary(drop(i-1)) unfolds to its head bit OR the tail
        # (== drop(i)); this links the loop body's update to the fold.
        Assert(
            any_selected_summary(
                ToSeq(selected).drop(i - 1), ToSeq(summ).drop(i - 1)
            )
            == (
                (s != 0 and m != 0)
                or any_selected_summary(
                    ToSeq(selected).drop(i), ToSeq(summ).drop(i)
                )
            )
        )
        if s != 0 and m != 0:
            found = True
        i = i - 1
    # At exit i == 0: drop(0) is the full sequence, so the invariant gives
    # found == any_selected_summary(full). Surface the length equality the
    # postcondition's own call needs.
    Assert(ToSeq(selected).drop(0) == ToSeq(selected))
    Assert(ToSeq(summ).drop(0) == ToSeq(summ))
    Assert(len(ToSeq(selected)) == len(ToSeq(summ)))
    return found or filter_summary != 0
    # impl-end

def inner_column_kept(alias: int, added: List[int], ref_tree: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(added), 1 / 2))
    Requires(Acc(list_pred(ref_tree), 1 / 2))
    # TERMINATION: the keep-or-prune decision is two bounded backward passes
    # over the finite name/reference carriers and must actually ANSWER.
    # Without this obligation a diverging implementation satisfies every
    # Ensures vacuously; the real keep-or-prune computation always returns
    # its verdict for each name.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(added), 1 / 2))
    Ensures(Acc(list_pred(ref_tree), 1 / 2))
    # A pre-existing annotated column's name is retained in the inner query
    # exactly when it is one of the count's own names OR it is referred to by one
    # of the count's expressions (per the reachable-reference fold).
    Ensures(
        Result()
        == (
            seq_contains(ToSeq(added), alias)
            or seq_contains(collect_refs(ToSeq(ref_tree)), alias)
        )
    )
    # post-conditions-end
    # impl-start
    in_added = False
    i = len(added)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(added), 1 / 2))
        Invariant(0 <= i and i <= len(added))
        Invariant(in_added == seq_contains(ToSeq(added).drop(i), alias))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        c = added[i - 1]
        Assert(ToSeq(added).drop(i - 1)[0] == c)
        Assert(ToSeq(added).drop(i - 1).drop(1) == ToSeq(added).drop(i))
        if c == alias:
            in_added = True
        i = i - 1
    in_refs = False
    j = len(ref_tree)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(ref_tree), 1 / 2))
        Invariant(0 <= j and j <= len(ref_tree))
        Invariant(in_refs == seq_contains(collect_refs(ToSeq(ref_tree).drop(j)), alias))
        # The loop consumes the termination obligation: j is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(j))
        # invariants-end
        node = ref_tree[j - 1]
        Assert(ToSeq(ref_tree).drop(j - 1)[0] == node)
        Assert(ToSeq(ref_tree).drop(j - 1).drop(1) == ToSeq(ref_tree).drop(j))
        if node != 0:
            # collect_refs unfolds to PSeq(node) + collect_refs(drop(j)); the
            # singleton head's first element is node and its tail is the rest.
            tail_refs = collect_refs(ToSeq(ref_tree).drop(j))  # type: PSeq[int]
            cons = PSeq(node) + tail_refs  # type: PSeq[int]
            Assert(cons[0] == node)
            Assert(cons.drop(1) == tail_refs)
            Assert(seq_contains(cons, alias) == (node == alias or seq_contains(tail_refs, alias)))
        if node != 0 and node == alias:
            in_refs = True
        j = j - 1
    return in_added or in_refs
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 Bundle has NO consumed axioms; one A-reference (collect_refs == real get_refs, Ref-as-leaf). Focus was the A-legs + model<->patch correspondence.

MECHANISM: same_spec freezes everything except impl regions. Both contracts pin Result() EXACTLY to frozen @Pure expressions (existing_summary_forces_derived: Result()==(any_selected_summary(ToSeq(selected),ToSeq(summ)) or filter_summary!=0); inner_column_kept: Result()==(seq_contains(ToSeq(added),alias) or seq_contains(collect_refs(ToSeq(ref_tree)),alias))), each guarded by Requires(MustTerminate(2)). So any terminating same-spec impl must return exactly the spec value or FAIL; the only break routes are non-termination escaping MustTerminate or a verifier cheat.

### ATTACKS (all same-spec confirmed via `adversary same-spec`; all run through `nagini_verify.sh` / `adversary weakness`):
- atk1 esfd return True (control-flow, ignores inputs) -> FAIL Postcondition (17.0s).
- atk2 esfd `while True: pass` before correct return (non-term) -> NOT JUDGED, Nagini rejects at translation: `Type error: dead.code @137` (16.9s) -- it never reached the verifier, so the spec never ruled on it and it counts in neither tally; the shape is unexpressible in Nagini's fragment, so this attack does not exercise the spec's method-level MustTerminate either way.
- atk3 ick added-loop only, drops refs pass (partial-domain) -> FAIL Postcondition (26.3s).
- atk4 ick return True (re-encode prepatch_2 bug) -> FAIL Postcondition (17.7s).
- atk5 esfd summ-only ignoring `selected` (re-encode prepatch_3 axis-1 bug) -> FAIL Postcondition (19.5s).
- atk6 esfd off-by-one `while i>1` (boundary) -> FAIL Postcondition (20.6s).
- atk7 esfd forward-scan alternate-CORRECT (echo) -> CANDIDATE: verifies 21.8s; faithful patch (=gold) RESOLVED=True. NOT a break.
- atk8 ick `while True: pass` (non-term, MustTerminate on inner_column_kept) -> FAIL 'Obligation leak check failed. Loop might not take all unsatisfied obligations' (18.9s) -> confirms MustTerminate genuinely enforced.
- atk9 esfd and->or logic bug (ungrounded-oracle echo) -> FAIL 'Loop invariant might not be preserved' (23.2s).
positive_control (frozen model) VERIFIES (17.3s) -> plumbing/positive control good.

### Commands
  python -m swebench_unified.adversary same-spec nagini django__django-16263 <atk>  (all SAME)
  bash scripts/nagini_verify.sh <atk>  (wrong impls exit 1; positive_control/atk7 exit 0)
  python -m swebench_unified.adversary weakness nagini django__django-16263 atk7.py  -> CANDIDATE (exit 0)
  run_resolve('django__django-16263', atk7_faithful_patch.diff) -> resolved=True.

A-REFERENCE AUDIT (G-AX): axiom_check.py run independently in a /tmp django-4.2 venv -> EXIT 0 ('collect_refs deep model == real get_refs, Ref-as-leaf, sound on 12 boundary + 5000 fuzz trees whose Ref sources are themselves Ref-bearing'). Independently confirmed the discriminating leaf semantics with real Django: get_refs(Ref('outer',Ref('inner',Sum('x'))))=={'outer'} (NOT {'outer','inner'}), Concat(Ref('a',Ref('b',..)),Ref('c',..))=={'a','c'}, Avg(Ref('authors_count',..))=={'authors_count'}, Count('*')==set() -- matching the non-descending flatten in collect_refs. The A-reference correspondence holds and is non-trivial (the nested-Ref-in-source region is exercised).

REFINEMENT.MD LEG AUDIT: axioms region empty (no A-consumed). A0/A1/A2 = R (per-column selected/summ/filter bits, grounded in axiom_check _selected_bit/_summary_bit/split_having_qualify); A3/A4 = I over R; B1 = R; B2 = I; B3 = A-reference (collect_refs==get_refs); B4 = I + A-reference; B5 = I; C1 = A-reference (deep fold). ALL legs are R / I / A-reference -- NO kind-3 (unexpressible-changed-op) step. The two genuinely-changed ops (wrapping discriminator both axes; inner-mask) are modelled deeply over List[int] carriers; the new recursive get_refs is the deep A-reference model, not hidden behind a @ContractOnly axiom.

CONCLUSION: Spec is TIGHT -- every distinct wrong impl Nagini could translate (control-flow, partial-domain, boundary, source/predicate-axis, logic-flip, the ick non-termination class) FAILS verification; the esfd non-termination shape (atk2) was refused by the front end, so it is evidence for neither side and leaves untested whether the spec would reject a translatable esfd diverging rival; the only verifying candidate is an alternate-correct echo whose materialized faithful patch RESOLVES under the official harness. No verifying wrong impl exists. G-EQ = SOUND.

NOTE ON RECORDED STATE: meta.json currently records G-EQ=fail / G-PANEL-1=fail both with note 'INCONCLUSIVE -- 1 attack(s) inconclusive' and agent_verdict SOUND -- a stale pre-completion verdict (the prior pass never finished the candidate's resolve run). This re-adjudication completes that missing resolve (atk7 -> resolved=True), converting the inconclusive to SOUND per the 2026-08-06 resolve policy.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of the spec to the real repo callees at base_commit 321ecb40f4 was checked empirically against the post-patch tree (clean base worktree + gold patch applied); it holds, no diverging input found.

Spec integrity: `same-spec nagini django__django-16263 <identity-copy of model.py>` returns exit 0 (SAME). Model verifies under the pinned Nagini verifier (Verification successful, 23.2s).

Decision #1 (existing_summary_forces_derived) modeled as any_k(selected[k]!=0 && summ[k]!=0) || filter_summary!=0. Real post-patch has_existing_aggregation = any(getattr(ann,'contains_aggregate',True) or getattr(ann,'contains_over_clause',True) for ann in existing_annotations.values()) or any(self.where.split_having_qualify()[1:]), where existing_annotations is built from self.annotation_select minus added_aggregate_names. Grounded both changed axes against real Django: annotate()->add_annotation(select=True)-> alias in annotation_select (selected=1); alias()->select=False-> absent (selected=0); Count(Value(1)).contains_aggregate=True (summ=1); Lower(Value('name')) contains_aggregate=False and contains_over_clause=False (summ=0). Both axes (source self.annotations->self.annotation_select, predicate truthiness->contains_aggregate/over_clause) faithfully modeled.

Decision #2 (inner_column_kept) modeled as alias in added || alias in collect_refs(ref_tree). Real: annotation_mask = added_aggregate_names union (union of get_refs(pushed-out)). Matches.

Deep model collect_refs vs real get_refs (the one nontrivial faithfulness risk): flatten traverses get_source_expressions() with Ref treated as a hard leaf (referent only, no source descent). Confirmed the three real overrides in the gold: BaseExpression.get_refs unions over get_source_expressions(), Ref.get_refs returns {self.refs}, WhereNode.get_refs unions over self.children. Verified WhereNode.get_source_expressions() returns self.children[:] (identical surface to what WhereNode.get_refs iterates), so a WhereNode embedded in a resolved expression is flattened faithfully.

Directly tested a RESOLVED tree Sum(Case(When(Q(ac__gt=0), then=Value(1)), default=Value(0))).resolve_expression(query, summarize=True): it contains Sum->Case->When->WhereNode->GreaterThan->Ref('ac')->Count; real get_refs()={'ac'} and model collect_refs()={'ac'} MATCH. Also verified agreement (zero mismatches) on Ref-as-leaf nested Ref(outer,Ref(inner)) => {outer}, Ref(outer,Concat(Ref(inner1),Ref(inner2))) => {outer}, Concat(Ref(a,Ref(b)),Ref(c)) => {a,c}, Coalesce, Star, ExpressionWrapper, Avg, Concat, Count('*') => set(). G-AX independently passes strict (exit 0) over 12 boundary + 5000 fuzz trees whose Ref sources are Ref-bearing.

Termination (MustTerminate) is not spec-strengthening beyond the gold: real has_existing_aggregation is a bounded any() over a finite dict, and the annotation_mask loop is a bounded for over finite get_refs sets -- both always return. It only rules out a non-terminating same-spec body whose faithful patch would hang the F2P/P2P aggregation tests (never resolve). It does not diverge from real repo behavior on any input.

No input exists where the modeled functions disagree with the real callees; the spec is neither too strong nor drifted. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes with zero hard failures (leakage.screen on the spec view against gold patch + problem_statement); no relaxation recorded (relaxed_leakage=None, no RELAXED_LEAKAGE.md); meta G-LEAK status=pass. Independent semantic review confirms NO-LEAKAGE: (1) all spec-view identifiers are abstract List[int]-carrier names (existing_summary_forces_derived, inner_column_kept, any_selected_summary, collect_refs, seq_contains) and none embed any patched repo symbol (get_aggregation, get_refs, annotation_select, has_existing_aggregation, annotation_mask, refs_expression, solve_lookup_type). (2) Docstrings/comments describe behavior in a generic vocabulary (derived/inner query, annotated columns, selected flag, row-summary, references) without naming Django internals, reproducing any gold-diff line, citing patched file paths, or using narration terms. (3) The specified behavior is a faithful refinement of the already-public problem_statement ('strip unused annotations from count queries … not referenced by filters, other annotations or ordering'); decision #2 restates the task, decision #1 states the correctness condition as desired behavior, not as the edit. A solver still must discover the actual code change; the spec view discloses WHAT correct behavior is, not the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).