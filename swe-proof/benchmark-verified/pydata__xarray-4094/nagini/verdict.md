# P2 adversarial audit — pydata__xarray-4094

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_launder.py`, `atk_prepatch.py`, `atk_noassemble.py`, `atk_fresh.py`, `atk_wrongdata.py`, `atk_partial.py`, `atk_control_flow.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_launder.py` → rejected (same spec, does not verify — good)

```diff
@@ -216,40 +216,35 @@
     Ensures(combined_collection(Result(), ToSeq(resid)))
     # post-conditions-end
     # impl-start
-    # one selection flag drives the whole reconstruction: each per-member slice
-    # is taken under the SAME `discard`, which fixes the annotation it carries
-    # over the members' positions; the combination reads exactly those
-    # annotations over those same positions -- there is no separate annotation
-    # the impl can supply, and the result must be the combination's output.
     discard = True
     data_dict = []  # type: List[int]
+    merged_in = []  # type: List[int]
     i = n
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(data), 1 / 2))
         Invariant(Acc(list_pred(resid), 1 / 2))
         Invariant(Acc(list_pred(data_dict)))
+        Invariant(Acc(list_pred(merged_in)))
         Invariant(0 <= i and i <= n)
         Invariant(len(data) == n)
         Invariant(len(resid) == n)
         Invariant(len(data_dict) == n - i)
+        Invariant(len(merged_in) == n - i)
         Invariant(ToSeq(data_dict) == ToSeq(data).drop(i))
+        Invariant(ToSeq(merged_in) == ToSeq(data).drop(i))
         Invariant(distinct_residuals(ToSeq(resid)))
-        # invariants-end
-        # take member i-1's slice under `discard`, recovering its value verbatim.
         selected = data[i - 1]
         data_dict = [selected] + data_dict
+        merged_in = [selected] + merged_in
         i = i - 1
     Assert(ToSeq(data_dict) == ToSeq(data).drop(0))
     Assert(ToSeq(data).drop(0) == ToSeq(data))
-    # under this selection every slice carries the single shared value, so the
-    # annotations agree across members and the combination is not rejected.
+    Assert(ToSeq(merged_in) == ToSeq(data))
     lemma_carried_all_equal(ToSeq(resid))
     Assert(all_equal(carried_seq(discard, ToSeq(resid))))
     Assert(distinct_residuals(ToSeq(resid)))
-    Assert(len(resid) == len(data_dict))
-    # combine the slices under the SAME `discard` over the members' distinct
-    # positions; the result is the combination's output (holding its token).
-    result = assemble(data_dict, resid, discard)
-    return result
+    Assert(len(resid) == len(merged_in))
+    result = assemble(merged_in, resid, discard)
+    Assert(ToSeq(result) == ToSeq(data_dict))
+    return data_dict
     # impl-end
```

Attack 2 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -216,16 +216,10 @@
     Ensures(combined_collection(Result(), ToSeq(resid)))
     # post-conditions-end
     # impl-start
-    # one selection flag drives the whole reconstruction: each per-member slice
-    # is taken under the SAME `discard`, which fixes the annotation it carries
-    # over the members' positions; the combination reads exactly those
-    # annotations over those same positions -- there is no separate annotation
-    # the impl can supply, and the result must be the combination's output.
-    discard = True
+    discard = False
     data_dict = []  # type: List[int]
     i = n
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(data), 1 / 2))
         Invariant(Acc(list_pred(resid), 1 / 2))
         Invariant(Acc(list_pred(data_dict)))
@@ -235,21 +229,15 @@
         Invariant(len(data_dict) == n - i)
         Invariant(ToSeq(data_dict) == ToSeq(data).drop(i))
         Invariant(distinct_residuals(ToSeq(resid)))
-        # invariants-end
-        # take member i-1's slice under `discard`, recovering its value verbatim.
         selected = data[i - 1]
         data_dict = [selected] + data_dict
         i = i - 1
     Assert(ToSeq(data_dict) == ToSeq(data).drop(0))
     Assert(ToSeq(data).drop(0) == ToSeq(data))
-    # under this selection every slice carries the single shared value, so the
-    # annotations agree across members and the combination is not rejected.
     lemma_carried_all_equal(ToSeq(resid))
     Assert(all_equal(carried_seq(discard, ToSeq(resid))))
     Assert(distinct_residuals(ToSeq(resid)))
     Assert(len(resid) == len(data_dict))
-    # combine the slices under the SAME `discard` over the members' distinct
-    # positions; the result is the combination's output (holding its token).
     result = assemble(data_dict, resid, discard)
     return result
     # impl-end
```

Attack 3 — `atk_noassemble.py` → rejected (same spec, does not verify — good)

```diff
@@ -216,16 +216,10 @@
     Ensures(combined_collection(Result(), ToSeq(resid)))
     # post-conditions-end
     # impl-start
-    # one selection flag drives the whole reconstruction: each per-member slice
-    # is taken under the SAME `discard`, which fixes the annotation it carries
-    # over the members' positions; the combination reads exactly those
-    # annotations over those same positions -- there is no separate annotation
-    # the impl can supply, and the result must be the combination's output.
     discard = True
     data_dict = []  # type: List[int]
     i = n
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(data), 1 / 2))
         Invariant(Acc(list_pred(resid), 1 / 2))
         Invariant(Acc(list_pred(data_dict)))
@@ -235,21 +229,14 @@
         Invariant(len(data_dict) == n - i)
         Invariant(ToSeq(data_dict) == ToSeq(data).drop(i))
         Invariant(distinct_residuals(ToSeq(resid)))
-        # invariants-end
-        # take member i-1's slice under `discard`, recovering its value verbatim.
         selected = data[i - 1]
         data_dict = [selected] + data_dict
         i = i - 1
     Assert(ToSeq(data_dict) == ToSeq(data).drop(0))
     Assert(ToSeq(data).drop(0) == ToSeq(data))
-    # under this selection every slice carries the single shared value, so the
-    # annotations agree across members and the combination is not rejected.
     lemma_carried_all_equal(ToSeq(resid))
     Assert(all_equal(carried_seq(discard, ToSeq(resid))))
     Assert(distinct_residuals(ToSeq(resid)))
     Assert(len(resid) == len(data_dict))
-    # combine the slices under the SAME `discard` over the members' distinct
-    # positions; the result is the combination's output (holding its token).
-    result = assemble(data_dict, resid, discard)
-    return result
+    return data_dict
     # impl-end
```

Attack 4 — `atk_fresh.py` → rejected (same spec, does not verify — good)

```diff
@@ -216,16 +216,10 @@
     Ensures(combined_collection(Result(), ToSeq(resid)))
     # post-conditions-end
     # impl-start
-    # one selection flag drives the whole reconstruction: each per-member slice
-    # is taken under the SAME `discard`, which fixes the annotation it carries
-    # over the members' positions; the combination reads exactly those
-    # annotations over those same positions -- there is no separate annotation
-    # the impl can supply, and the result must be the combination's output.
     discard = True
     data_dict = []  # type: List[int]
     i = n
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(data), 1 / 2))
         Invariant(Acc(list_pred(resid), 1 / 2))
         Invariant(Acc(list_pred(data_dict)))
@@ -235,21 +229,28 @@
         Invariant(len(data_dict) == n - i)
         Invariant(ToSeq(data_dict) == ToSeq(data).drop(i))
         Invariant(distinct_residuals(ToSeq(resid)))
-        # invariants-end
-        # take member i-1's slice under `discard`, recovering its value verbatim.
         selected = data[i - 1]
         data_dict = [selected] + data_dict
         i = i - 1
     Assert(ToSeq(data_dict) == ToSeq(data).drop(0))
     Assert(ToSeq(data).drop(0) == ToSeq(data))
-    # under this selection every slice carries the single shared value, so the
-    # annotations agree across members and the combination is not rejected.
     lemma_carried_all_equal(ToSeq(resid))
     Assert(all_equal(carried_seq(discard, ToSeq(resid))))
     Assert(distinct_residuals(ToSeq(resid)))
     Assert(len(resid) == len(data_dict))
-    # combine the slices under the SAME `discard` over the members' distinct
-    # positions; the result is the combination's output (holding its token).
     result = assemble(data_dict, resid, discard)
-    return result
+    fresh = []  # type: List[int]
+    j = n
+    while j > 0:
+        Invariant(Acc(list_pred(data), 1 / 2))
+        Invariant(Acc(list_pred(fresh)))
+        Invariant(0 <= j and j <= n)
+        Invariant(len(data) == n)
+        Invariant(len(fresh) == n - j)
+        Invariant(ToSeq(fresh) == ToSeq(data).drop(j))
+        selm = data[j - 1]
+        fresh = [selm] + fresh
+        j = j - 1
+    Assert(ToSeq(fresh) == ToSeq(data))
+    return fresh
     # impl-end
```

Attack 5 — `atk_wrongdata.py` → rejected (same spec, does not verify — good)

```diff
@@ -216,16 +216,10 @@
     Ensures(combined_collection(Result(), ToSeq(resid)))
     # post-conditions-end
     # impl-start
-    # one selection flag drives the whole reconstruction: each per-member slice
-    # is taken under the SAME `discard`, which fixes the annotation it carries
-    # over the members' positions; the combination reads exactly those
-    # annotations over those same positions -- there is no separate annotation
-    # the impl can supply, and the result must be the combination's output.
     discard = True
     data_dict = []  # type: List[int]
     i = n
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(data), 1 / 2))
         Invariant(Acc(list_pred(resid), 1 / 2))
         Invariant(Acc(list_pred(data_dict)))
@@ -235,21 +229,15 @@
         Invariant(len(data_dict) == n - i)
         Invariant(ToSeq(data_dict) == ToSeq(data).drop(i))
         Invariant(distinct_residuals(ToSeq(resid)))
-        # invariants-end
-        # take member i-1's slice under `discard`, recovering its value verbatim.
         selected = data[i - 1]
         data_dict = [selected] + data_dict
         i = i - 1
     Assert(ToSeq(data_dict) == ToSeq(data).drop(0))
     Assert(ToSeq(data).drop(0) == ToSeq(data))
-    # under this selection every slice carries the single shared value, so the
-    # annotations agree across members and the combination is not rejected.
     lemma_carried_all_equal(ToSeq(resid))
     Assert(all_equal(carried_seq(discard, ToSeq(resid))))
     Assert(distinct_residuals(ToSeq(resid)))
     Assert(len(resid) == len(data_dict))
-    # combine the slices under the SAME `discard` over the members' distinct
-    # positions; the result is the combination's output (holding its token).
-    result = assemble(data_dict, resid, discard)
+    result = assemble(resid, resid, discard)
     return result
     # impl-end
```

Attack 6 — `atk_partial.py` → rejected (same spec, does not verify — good)

```diff
@@ -216,40 +216,24 @@
     Ensures(combined_collection(Result(), ToSeq(resid)))
     # post-conditions-end
     # impl-start
-    # one selection flag drives the whole reconstruction: each per-member slice
-    # is taken under the SAME `discard`, which fixes the annotation it carries
-    # over the members' positions; the combination reads exactly those
-    # annotations over those same positions -- there is no separate annotation
-    # the impl can supply, and the result must be the combination's output.
     discard = True
     data_dict = []  # type: List[int]
     i = n
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(data), 1 / 2))
         Invariant(Acc(list_pred(resid), 1 / 2))
         Invariant(Acc(list_pred(data_dict)))
-        Invariant(0 <= i and i <= n)
+        Invariant(1 <= i and i <= n)
         Invariant(len(data) == n)
         Invariant(len(resid) == n)
         Invariant(len(data_dict) == n - i)
         Invariant(ToSeq(data_dict) == ToSeq(data).drop(i))
         Invariant(distinct_residuals(ToSeq(resid)))
-        # invariants-end
-        # take member i-1's slice under `discard`, recovering its value verbatim.
         selected = data[i - 1]
         data_dict = [selected] + data_dict
         i = i - 1
-    Assert(ToSeq(data_dict) == ToSeq(data).drop(0))
-    Assert(ToSeq(data).drop(0) == ToSeq(data))
-    # under this selection every slice carries the single shared value, so the
-    # annotations agree across members and the combination is not rejected.
     lemma_carried_all_equal(ToSeq(resid))
     Assert(all_equal(carried_seq(discard, ToSeq(resid))))
-    Assert(distinct_residuals(ToSeq(resid)))
-    Assert(len(resid) == len(data_dict))
-    # combine the slices under the SAME `discard` over the members' distinct
-    # positions; the result is the combination's output (holding its token).
     result = assemble(data_dict, resid, discard)
     return result
     # impl-end
```

Attack 7 — `atk_control_flow.py` → rejected (same spec, does not verify — good)

```diff
@@ -216,16 +216,10 @@
     Ensures(combined_collection(Result(), ToSeq(resid)))
     # post-conditions-end
     # impl-start
-    # one selection flag drives the whole reconstruction: each per-member slice
-    # is taken under the SAME `discard`, which fixes the annotation it carries
-    # over the members' positions; the combination reads exactly those
-    # annotations over those same positions -- there is no separate annotation
-    # the impl can supply, and the result must be the combination's output.
     discard = True
     data_dict = []  # type: List[int]
     i = n
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(data), 1 / 2))
         Invariant(Acc(list_pred(resid), 1 / 2))
         Invariant(Acc(list_pred(data_dict)))
@@ -235,21 +229,17 @@
         Invariant(len(data_dict) == n - i)
         Invariant(ToSeq(data_dict) == ToSeq(data).drop(i))
         Invariant(distinct_residuals(ToSeq(resid)))
-        # invariants-end
-        # take member i-1's slice under `discard`, recovering its value verbatim.
         selected = data[i - 1]
         data_dict = [selected] + data_dict
         i = i - 1
     Assert(ToSeq(data_dict) == ToSeq(data).drop(0))
     Assert(ToSeq(data).drop(0) == ToSeq(data))
-    # under this selection every slice carries the single shared value, so the
-    # annotations agree across members and the combination is not rejected.
     lemma_carried_all_equal(ToSeq(resid))
     Assert(all_equal(carried_seq(discard, ToSeq(resid))))
     Assert(distinct_residuals(ToSeq(resid)))
     Assert(len(resid) == len(data_dict))
-    # combine the slices under the SAME `discard` over the members' distinct
-    # positions; the result is the combination's output (holding its token).
     result = assemble(data_dict, resid, discard)
+    if n >= 2:
+        return data_dict
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for pydata__xarray-4094.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A stacked collection is reconstructed back into its original group of named
  members. The collection arranges several named members along one shared axis
  whose tick labels are PAIRS: each tick pairs a member identifier with one
  position label. The reconstruction, for each member identifier `k`, takes the
  slice of the axis whose member-identifier component equals `k`, and combines
  the per-member slices into one collection that must equal the original group.

  A per-member slice is taken by the selection under a flag `discard`. The
  annotation it carries for its member is `carried(discard, position)` -- a value
  determined by that one taking, the same function of `discard` for every member.
  The
  combination step combines the per-member slices into one collection. It
  inspects the annotation each slice carries -- over the members' (pairwise
  distinct) positions, under the SAME selection -- and succeeds, returning the
  members' values verbatim, iff every member carries the same value for that
  shared-name annotation; otherwise it is rejected.

  Desired roundtrip property: the reconstruction recovers every member's value
  verbatim, and the recovered collection is the OUTPUT of the combination over
  the members' positions (it cannot be produced any other way -- the
  reconstruction must go through the combination, which is rejected unless the
  per-member slices carry one common shared-name annotation).

Modelling: the members are indexed `0..n-1`. `data[k]` is the value carried by
member `k`; the reconstruction recovers it verbatim. The position label paired
with member `k` is `resid[k]`, pairwise distinct across members in the shape this
bundle pins. The selection callee `carried(discard, position)` gives the
annotation a slice carries. The combination callee `assemble` combines the
per-member slices: it inspects the annotations the slices carry over the members'
distinct positions under the SAME selection -- `carried_seq(discard, resid)` --
succeeds iff they are all equal (`all_equal`), returns each member's value
verbatim, and grants the `combined_collection` token marking its output. The
reconstruction's result must hold that token, so the combination is mandatory.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def shared_value() -> int:
    """The single annotation value common to every slice when the selection
    yields no distinguishing per-member annotation. A single constant, identical
    across all members. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Ensures(True)


@Pure
@ContractOnly
def carried(discard: bool, position: int) -> int:
    """Selection callee. The annotation value a per-member slice carries for its
    position, as a function of the selection's `discard` flag and the member's
    `position` label: the member's own position label when `discard` is false,
    the single shared value common to every slice when `discard` is true.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(not discard, Result() == position))
    Ensures(Implies(discard, Result() == shared_value()))


# Abstract token marking THE VERY OBJECT that was PRODUCED BY the combination
# step over the members' positions: a capability `assemble` grants on its output
# object and that nothing else can fabricate. It is keyed by the object itself
# (a reference), not by its value, so a value-equal collection built anywhere
# else does not hold it. The reconstruction's result must hold it, so the result
# can only be the output of the combination itself (the combination can neither
# be bypassed nor laundered through a value-equal copy). Provenance + executable
# soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def combined_collection(collection: List[int], positions: PSeq[int]) -> bool:
    pass


@ContractOnly
def assemble(slices: List[int], resid: List[int], discard: bool) -> List[int]:
    """Combination callee that combines the per-member slices into one
    collection. The slices were taken under the flag `discard` and the members
    sit at the pairwise-distinct positions `resid` (the position state intrinsic
    to the slices). The combination inspects the annotation each slice carries
    under that selection -- `carried_seq(discard, resid)` -- and REQUIRES that
    they agree across members (`all_equal`). A shared-name annotation carrying
    two different values is a conflict and the combination is rejected (its
    precondition is violated). On success it returns each member's value verbatim
    and grants the `combined_collection` token on its output over `resid`.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(slices), 1 / 2))
    Requires(Acc(list_pred(resid), 1 / 2))
    Requires(len(resid) == len(slices))
    # the positions intrinsic to the slices are pairwise distinct (the shape this
    # bundle pins) -- not a separate all-equal list the caller can fabricate.
    Requires(distinct_residuals(ToSeq(resid)))
    # the combination is rejected unless the annotations the slices carry under
    # this selection agree across members.
    Requires(all_equal(carried_seq(discard, ToSeq(resid))))
    Ensures(Acc(list_pred(slices), 1 / 2))
    Ensures(Acc(list_pred(resid), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(slices))
    Ensures(ToSeq(Result()) == ToSeq(slices))
    # the output OBJECT is marked as the combination's product over these
    # positions (the token sits on the returned reference itself).
    Ensures(combined_collection(Result(), ToSeq(resid)))
# axioms-end


# pure-start
@Pure
def distinct_residuals(resid: PSeq[int]) -> bool:
    """The members occupy pairwise-distinct position labels -- the shape this
    bundle pins, where each member sits at its own position. (When the slices
    carry that position annotation, distinctness is exactly what makes two
    members disagree on it; it also rules out a fabricated all-equal position
    list.)"""
    return Forall(int, lambda i:
        (Forall(int, lambda j:
            (Implies(0 <= i and i < j and j < len(resid),
                     resid[i] != resid[j]),
             [[resid[i], resid[j]]])),
         []))


@Pure
def all_equal(xs: PSeq[int]) -> bool:
    """The per-slice annotations agree -- the combination succeeds iff the
    shared-name annotation carries one common value across all members. Defined
    by adjacent equality (head equals the next entry and the tail is all-equal),
    equivalent for a sequence to every entry being equal. With pairwise-distinct
    positions and at least two members, the members' own positions are NOT
    all-equal (entries 0 and 1 differ), while the single shared value IS."""
    if len(xs) <= 1:
        return True
    return xs[0] == xs.drop(1)[0] and all_equal(xs.drop(1))


@Pure
def carried_seq(discard: bool, positions: PSeq[int]) -> PSeq[int]:
    """The annotation each slice carries over a sequence of member positions:
    element-wise `carried(discard, .)`. Front-recursive (no contract, so it
    unfolds one level per loop step -- the canonical sequence-fold pattern)."""
    if len(positions) == 0:
        return PSeq(0).take(0)
    return PSeq(carried(discard, positions[0])) + carried_seq(discard, positions.drop(1))
# pure-end


def lemma_carried_len(discard: bool, positions: PSeq[int]) -> None:
    """Lemma: the annotation list has one entry per member:
    `len(carried_seq(discard, positions)) == len(positions)`. Induction on the
    front-recursive fold."""
    Ensures(len(carried_seq(discard, positions)) == len(positions))
    if len(positions) > 0:
        lemma_carried_len(discard, positions.drop(1))


def lemma_carried_all_equal(positions: PSeq[int]) -> None:
    """Lemma: when the selection yields the single shared annotation
    (`discard` true), the annotation list is all-equal:
    `all_equal(carried_seq(True, positions))`. Every entry is the one shared
    value, so adjacent entries agree. Proved by induction on the front-recursive
    fold; phrased with concat indexing / drop only, never PSeq-literal equality
    (which Nagini cannot derive from element equality)."""
    Ensures(all_equal(carried_seq(True, positions)))
    lemma_carried_len(True, positions)
    if len(positions) > 1:
        lemma_carried_all_equal(positions.drop(1))
        lemma_carried_len(True, positions.drop(1))
        Assert(len(carried_seq(True, positions)) == len(positions))
        Assert(carried_seq(True, positions)[0] == carried(True, positions[0]))
        Assert(carried_seq(True, positions).drop(1) ==
               carried_seq(True, positions.drop(1)))
        Assert(carried_seq(True, positions.drop(1))[0] ==
               carried(True, positions.drop(1)[0]))
        Assert(carried(True, positions[0]) == shared_value())
        Assert(carried(True, positions.drop(1)[0]) == shared_value())


def to_unstacked(n: int, data: List[int], resid: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(n >= 0)
    Requires(Acc(list_pred(data), 1 / 2))
    Requires(Acc(list_pred(resid), 1 / 2))
    Requires(len(data) == n)
    Requires(len(resid) == n)
    # at least two members so a shared position annotation has two values to
    # disagree over (the shape this bundle pins)
    Requires(n >= 2)
    # the members sit at pairwise-distinct positions, so a position annotation
    # carried under a shared name would carry conflicting values
    Requires(distinct_residuals(ToSeq(resid)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(data), 1 / 2))
    Ensures(Acc(list_pred(resid), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the reconstruction recovers each member's value verbatim (the roundtrip is
    # the identity)
    Ensures(len(Result()) == n)
    Ensures(ToSeq(Result()) == ToSeq(data))
    # the recovered collection IS the output object of the combination over the
    # members' distinct positions -- it holds the object-keyed token only the
    # combination grants on its own output, so the reconstruction can neither
    # bypass the combination (whose guard is rejected unless every per-member
    # slice carries one common shared-name annotation) nor substitute a
    # value-equal copy that never went through it.
    Ensures(combined_collection(Result(), ToSeq(resid)))
    # post-conditions-end
    # impl-start
    discard = True
    data_dict = []  # type: List[int]
    i = 0
    while i < n:
        Invariant(Acc(list_pred(data), 1 / 2))
        Invariant(Acc(list_pred(resid), 1 / 2))
        Invariant(Acc(list_pred(data_dict)))
        Invariant(0 <= i and i <= n)
        Invariant(len(data) == n)
        Invariant(len(resid) == n)
        Invariant(len(data_dict) == i)
        Invariant(ToSeq(data_dict) == ToSeq(data).take(i))
        Invariant(distinct_residuals(ToSeq(resid)))
        selected = data[i]
        data_dict = data_dict + [selected]
        i = i + 1
    Assert(ToSeq(data_dict) == ToSeq(data).take(n))
    Assert(ToSeq(data).take(n) == ToSeq(data))
    lemma_carried_all_equal(ToSeq(resid))
    Assert(all_equal(carried_seq(discard, ToSeq(resid))))
    Assert(len(resid) == len(data_dict))
    result = assemble(data_dict, resid, discard)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

RE-AUDIT of a repaired Source-2 cell. The recorded G-EQ=BROKEN (2026-08-12, scratch _1mq7r8us) was against an OLD model that keyed the combined_collection token BY VALUE (combined_collection(members: PSeq[int], positions)); that admitted a value-LAUNDER impl (atk_launder: mint the token by calling assemble on merged_in, then return a value-equal pre-merge data_dict) whose faithful patch `return data_dict` did NOT resolve. The current model.py (updated 2026-08-13 05:07) REPAIRS this by re-keying the token to the output OBJECT reference: `combined_collection(collection: List[int], positions: PSeq[int])`. I re-tested the launder hole and 6 further distinct wrong impls against the repaired model.

Env: python -m swebench_unified.adversary (module import) + nagini verifier. Attacks built by copying the bundle model.py into the scratch dir and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); all 8 files pass `adversary same-spec` (exit 0).

Attack results (`adversary weakness nagini pydata__xarray-4094 <file>`), run concurrently ≤3 JVMs at a time:
- atk_launder.py (NAMED prior CE reproduced: two value-equal lists, mint token on merged_in via assemble, return pre-merge data_dict): EXIT 2 — DOES NOT VERIFY. `verify` detail: `Postcondition of to_unstacked might not hold. There might be insufficient permission to access combined_collection(Result(), ToSeq(resid))` at model line 216. The reference-keying repair closes the launder hole exactly.
- atk_prepatch.py (the prepatch bug, discard=False, calls assemble): EXIT 2 — fails all_equal(carried_seq(False, resid)) guard. PREPATCH BUG REPRODUCED as non-verifying.
- atk_noassemble.py (atk_7: build verbatim values, return WITHOUT assemble): EXIT 2 — lacks the token.
- atk_fresh.py (mint token on data_dict, return a freshly rebuilt value-equal list): EXIT 2 — token is on assemble's output object, not the fresh copy.
- atk_wrongdata.py (assemble resid instead of data values): EXIT 2 — violates ToSeq(Result())==ToSeq(data).
- atk_partial.py (partial-domain: skip last member, assemble short list): EXIT 2.
- atk_control_flow.py (control-flow-effect: on branch n>=2 return pre-merge data_dict, else assemble output): EXIT 2 — the returned object on the taken branch lacks the token.
All 7 wrong impls are REJECTED by the spec (none verifies) — no CANDIDATE among them, so no faithful patch needed materializing.

Positive control pc.py (structurally-different FORWARD-append correct impl, calls assemble): `adversary weakness` EXIT 0 (CANDIDATE: same-spec AND verifies, 12.5s) => non-vacuous. Its faithful refined patch is the gold patch (patch_pc.diff = the one-line drop=True addition). EXECUTED through the official harness: `run_resolve('pydata__xarray-4094', patch_pc.diff)` => resolved=True, completed=True, note='resolved'. This validates the harness plumbing (a non-resolve would have been meaningful) and confirms the sole verifying impl resolves.

refinement.md audit: legs A1 (params↔self+loop, R), A2 (discard/slice-value↔.sel(...,drop=True).squeeze, A-consumed carried/shared_value + R), A3 (assemble↔Dataset(data_dict), A-consumed assemble+combined_collection), A4 (return↔returned Dataset, R). All legs are R / A-consumed / I — NO kind-3 step; meta deep_model_references is empty (consistent — no A-reference legs). The A-legs axiomatize ONLY unchanged community callees (DataArray.sel/.squeeze, the Dataset constructor/merge), never the function under change; the object-keyed combined_collection token corresponds to the identity of `return Dataset(data_dict)`'s output (mapping.md §3.3) and is the mechanism forcing the merge onto the result path. Correspondence holds.

VERDICT: SOUND. ≥5 distinct wrong impls (7 total, incl. the named launder CE and the prepatch bug) all fail to verify against the repaired reference-keyed spec; the only verifying candidate (correct positive control) resolves. verify⇒correct is preserved. NOTE for board bookkeeping: the recorded meta gates still carry the pre-repair G-EQ=BROKEN/G-PANEL-1=fail verdicts from 2026-08-12; those were against the old value-keyed model and are stale — this re-audit of the repaired model.py should overwrite them to pass.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_launder.py`, `atk_prepatch.py`, `atk_noassemble.py`, `atk_fresh.py`, `atk_wrongdata.py`, `atk_partial.py`, `atk_control_flow.py` |

**Non-vacuity.** The positive control `pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_launder.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_noassemble.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_fresh.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_wrongdata.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_partial.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_control_flow.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.py`

```python
"""Twin-artifact model for pydata__xarray-4094.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A stacked collection is reconstructed back into its original group of named
  members. The collection arranges several named members along one shared axis
  whose tick labels are PAIRS: each tick pairs a member identifier with one
  position label. The reconstruction, for each member identifier `k`, takes the
  slice of the axis whose member-identifier component equals `k`, and combines
  the per-member slices into one collection that must equal the original group.

  A per-member slice is taken by the selection under a flag `discard`. The
  annotation it carries for its member is `carried(discard, position)` -- a value
  determined by that one taking, the same function of `discard` for every member.
  The
  combination step combines the per-member slices into one collection. It
  inspects the annotation each slice carries -- over the members' (pairwise
  distinct) positions, under the SAME selection -- and succeeds, returning the
  members' values verbatim, iff every member carries the same value for that
  shared-name annotation; otherwise it is rejected.

  Desired roundtrip property: the reconstruction recovers every member's value
  verbatim, and the recovered collection is the OUTPUT of the combination over
  the members' positions (it cannot be produced any other way -- the
  reconstruction must go through the combination, which is rejected unless the
  per-member slices carry one common shared-name annotation).

Modelling: the members are indexed `0..n-1`. `data[k]` is the value carried by
member `k`; the reconstruction recovers it verbatim. The position label paired
with member `k` is `resid[k]`, pairwise distinct across members in the shape this
bundle pins. The selection callee `carried(discard, position)` gives the
annotation a slice carries. The combination callee `assemble` combines the
per-member slices: it inspects the annotations the slices carry over the members'
distinct positions under the SAME selection -- `carried_seq(discard, resid)` --
succeeds iff they are all equal (`all_equal`), returns each member's value
verbatim, and grants the `combined_collection` token marking its output. The
reconstruction's result must hold that token, so the combination is mandatory.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def shared_value() -> int:
    """The single annotation value common to every slice when the selection
    yields no distinguishing per-member annotation. A single constant, identical
    across all members. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Ensures(True)


@Pure
@ContractOnly
def carried(discard: bool, position: int) -> int:
    """Selection callee. The annotation value a per-member slice carries for its
    position, as a function of the selection's `discard` flag and the member's
    `position` label: the member's own position label when `discard` is false,
    the single shared value common to every slice when `discard` is true.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(not discard, Result() == position))
    Ensures(Implies(discard, Result() == shared_value()))


# Abstract token marking THE VERY OBJECT that was PRODUCED BY the combination
# step over the members' positions: a capability `assemble` grants on its output
# object and that nothing else can fabricate. It is keyed by the object itself
# (a reference), not by its value, so a value-equal collection built anywhere
# else does not hold it. The reconstruction's result must hold it, so the result
# can only be the output of the combination itself (the combination can neither
# be bypassed nor laundered through a value-equal copy). Provenance + executable
# soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def combined_collection(collection: List[int], positions: PSeq[int]) -> bool:
    pass


@ContractOnly
def assemble(slices: List[int], resid: List[int], discard: bool) -> List[int]:
    """Combination callee that combines the per-member slices into one
    collection. The slices were taken under the flag `discard` and the members
    sit at the pairwise-distinct positions `resid` (the position state intrinsic
    to the slices). The combination inspects the annotation each slice carries
    under that selection -- `carried_seq(discard, resid)` -- and REQUIRES that
    they agree across members (`all_equal`). A shared-name annotation carrying
    two different values is a conflict and the combination is rejected (its
    precondition is violated). On success it returns each member's value verbatim
    and grants the `combined_collection` token on its output over `resid`.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(slices), 1 / 2))
    Requires(Acc(list_pred(resid), 1 / 2))
    Requires(len(resid) == len(slices))
    # the positions intrinsic to the slices are pairwise distinct (the shape this
    # bundle pins) -- not a separate all-equal list the caller can fabricate.
    Requires(distinct_residuals(ToSeq(resid)))
    # the combination is rejected unless the annotations the slices carry under
    # this selection agree across members.
    Requires(all_equal(carried_seq(discard, ToSeq(resid))))
    Ensures(Acc(list_pred(slices), 1 / 2))
    Ensures(Acc(list_pred(resid), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(slices))
    Ensures(ToSeq(Result()) == ToSeq(slices))
    # the output OBJECT is marked as the combination's product over these
    # positions (the token sits on the returned reference itself).
    Ensures(combined_collection(Result(), ToSeq(resid)))
# axioms-end


# pure-start
@Pure
def distinct_residuals(resid: PSeq[int]) -> bool:
    """The members occupy pairwise-distinct position labels -- the shape this
    bundle pins, where each member sits at its own position. (When the slices
    carry that position annotation, distinctness is exactly what makes two
    members disagree on it; it also rules out a fabricated all-equal position
    list.)"""
    return Forall(int, lambda i:
        (Forall(int, lambda j:
            (Implies(0 <= i and i < j and j < len(resid),
                     resid[i] != resid[j]),
             [[resid[i], resid[j]]])),
         []))


@Pure
def all_equal(xs: PSeq[int]) -> bool:
    """The per-slice annotations agree -- the combination succeeds iff the
    shared-name annotation carries one common value across all members. Defined
    by adjacent equality (head equals the next entry and the tail is all-equal),
    equivalent for a sequence to every entry being equal. With pairwise-distinct
    positions and at least two members, the members' own positions are NOT
    all-equal (entries 0 and 1 differ), while the single shared value IS."""
    if len(xs) <= 1:
        return True
    return xs[0] == xs.drop(1)[0] and all_equal(xs.drop(1))


@Pure
def carried_seq(discard: bool, positions: PSeq[int]) -> PSeq[int]:
    """The annotation each slice carries over a sequence of member positions:
    element-wise `carried(discard, .)`. Front-recursive (no contract, so it
    unfolds one level per loop step -- the canonical sequence-fold pattern)."""
    if len(positions) == 0:
        return PSeq(0).take(0)
    return PSeq(carried(discard, positions[0])) + carried_seq(discard, positions.drop(1))
# pure-end


def lemma_carried_len(discard: bool, positions: PSeq[int]) -> None:
    """Lemma: the annotation list has one entry per member:
    `len(carried_seq(discard, positions)) == len(positions)`. Induction on the
    front-recursive fold."""
    Ensures(len(carried_seq(discard, positions)) == len(positions))
    if len(positions) > 0:
        lemma_carried_len(discard, positions.drop(1))


def lemma_carried_all_equal(positions: PSeq[int]) -> None:
    """Lemma: when the selection yields the single shared annotation
    (`discard` true), the annotation list is all-equal:
    `all_equal(carried_seq(True, positions))`. Every entry is the one shared
    value, so adjacent entries agree. Proved by induction on the front-recursive
    fold; phrased with concat indexing / drop only, never PSeq-literal equality
    (which Nagini cannot derive from element equality)."""
    Ensures(all_equal(carried_seq(True, positions)))
    lemma_carried_len(True, positions)
    if len(positions) > 1:
        lemma_carried_all_equal(positions.drop(1))
        lemma_carried_len(True, positions.drop(1))
        Assert(len(carried_seq(True, positions)) == len(positions))
        Assert(carried_seq(True, positions)[0] == carried(True, positions[0]))
        Assert(carried_seq(True, positions).drop(1) ==
               carried_seq(True, positions.drop(1)))
        Assert(carried_seq(True, positions.drop(1))[0] ==
               carried(True, positions.drop(1)[0]))
        Assert(carried(True, positions[0]) == shared_value())
        Assert(carried(True, positions.drop(1)[0]) == shared_value())


def to_unstacked(n: int, data: List[int], resid: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(n >= 0)
    Requires(Acc(list_pred(data), 1 / 2))
    Requires(Acc(list_pred(resid), 1 / 2))
    Requires(len(data) == n)
    Requires(len(resid) == n)
    # at least two members so a shared position annotation has two values to
    # disagree over (the shape this bundle pins)
    Requires(n >= 2)
    # the members sit at pairwise-distinct positions, so a position annotation
    # carried under a shared name would carry conflicting values
    Requires(distinct_residuals(ToSeq(resid)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(data), 1 / 2))
    Ensures(Acc(list_pred(resid), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the reconstruction recovers each member's value verbatim (the roundtrip is
    # the identity)
    Ensures(len(Result()) == n)
    Ensures(ToSeq(Result()) == ToSeq(data))
    # the recovered collection IS the output object of the combination over the
    # members' distinct positions -- it holds the object-keyed token only the
    # combination grants on its own output, so the reconstruction can neither
    # bypass the combination (whose guard is rejected unless every per-member
    # slice carries one common shared-name annotation) nor substitute a
    # value-equal copy that never went through it.
    Ensures(combined_collection(Result(), ToSeq(resid)))
    # post-conditions-end
    # impl-start
    discard = True
    data_dict = []  # type: List[int]
    i = 0
    while i < n:
        Invariant(Acc(list_pred(data), 1 / 2))
        Invariant(Acc(list_pred(resid), 1 / 2))
        Invariant(Acc(list_pred(data_dict)))
        Invariant(0 <= i and i <= n)
        Invariant(len(data) == n)
        Invariant(len(resid) == n)
        Invariant(len(data_dict) == i)
        Invariant(ToSeq(data_dict) == ToSeq(data).take(i))
        Invariant(distinct_residuals(ToSeq(resid)))
        selected = data[i]
        data_dict = data_dict + [selected]
        i = i + 1
    Assert(ToSeq(data_dict) == ToSeq(data).take(n))
    Assert(ToSeq(data).take(n) == ToSeq(data))
    lemma_carried_all_equal(ToSeq(resid))
    Assert(all_equal(carried_seq(discard, ToSeq(resid))))
    Assert(len(resid) == len(data_dict))
    result = assemble(data_dict, resid, discard)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

RE-AUDIT of a repaired Source-2 cell. The recorded G-EQ=BROKEN (2026-08-12, scratch _1mq7r8us) was against an OLD model that keyed the combined_collection token BY VALUE (combined_collection(members: PSeq[int], positions)); that admitted a value-LAUNDER impl (atk_launder: mint the token by calling assemble on merged_in, then return a value-equal pre-merge data_dict) whose faithful patch `return data_dict` did NOT resolve. The current model.py (updated 2026-08-13 05:07) REPAIRS this by re-keying the token to the output OBJECT reference: `combined_collection(collection: List[int], positions: PSeq[int])`. I re-tested the launder hole and 6 further distinct wrong impls against the repaired model.

Env: python -m swebench_unified.adversary (module import) + nagini verifier. Attacks built by copying the bundle model.py into the scratch dir and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); all 8 files pass `adversary same-spec` (exit 0).

Attack results (`adversary weakness nagini pydata__xarray-4094 <file>`), run concurrently ≤3 JVMs at a time:
- atk_launder.py (NAMED prior CE reproduced: two value-equal lists, mint token on merged_in via assemble, return pre-merge data_dict): EXIT 2 — DOES NOT VERIFY. `verify` detail: `Postcondition of to_unstacked might not hold. There might be insufficient permission to access combined_collection(Result(), ToSeq(resid))` at model line 216. The reference-keying repair closes the launder hole exactly.
- atk_prepatch.py (the prepatch bug, discard=False, calls assemble): EXIT 2 — fails all_equal(carried_seq(False, resid)) guard. PREPATCH BUG REPRODUCED as non-verifying.
- atk_noassemble.py (atk_7: build verbatim values, return WITHOUT assemble): EXIT 2 — lacks the token.
- atk_fresh.py (mint token on data_dict, return a freshly rebuilt value-equal list): EXIT 2 — token is on assemble's output object, not the fresh copy.
- atk_wrongdata.py (assemble resid instead of data values): EXIT 2 — violates ToSeq(Result())==ToSeq(data).
- atk_partial.py (partial-domain: skip last member, assemble short list): EXIT 2.
- atk_control_flow.py (control-flow-effect: on branch n>=2 return pre-merge data_dict, else assemble output): EXIT 2 — the returned object on the taken branch lacks the token.
All 7 wrong impls are REJECTED by the spec (none verifies) — no CANDIDATE among them, so no faithful patch needed materializing.

Positive control pc.py (structurally-different FORWARD-append correct impl, calls assemble): `adversary weakness` EXIT 0 (CANDIDATE: same-spec AND verifies, 12.5s) => non-vacuous. Its faithful refined patch is the gold patch (patch_pc.diff = the one-line drop=True addition). EXECUTED through the official harness: `run_resolve('pydata__xarray-4094', patch_pc.diff)` => resolved=True, completed=True, note='resolved'. This validates the harness plumbing (a non-resolve would have been meaningful) and confirms the sole verifying impl resolves.

refinement.md audit: legs A1 (params↔self+loop, R), A2 (discard/slice-value↔.sel(...,drop=True).squeeze, A-consumed carried/shared_value + R), A3 (assemble↔Dataset(data_dict), A-consumed assemble+combined_collection), A4 (return↔returned Dataset, R). All legs are R / A-consumed / I — NO kind-3 step; meta deep_model_references is empty (consistent — no A-reference legs). The A-legs axiomatize ONLY unchanged community callees (DataArray.sel/.squeeze, the Dataset constructor/merge), never the function under change; the object-keyed combined_collection token corresponds to the identity of `return Dataset(data_dict)`'s output (mapping.md §3.3) and is the mechanism forcing the merge onto the result path. Correspondence holds.

VERDICT: SOUND. ≥5 distinct wrong impls (7 total, incl. the named launder CE and the prepatch bug) all fail to verify against the repaired reference-keyed spec; the only verifying candidate (correct positive control) resolves. verify⇒correct is preserved. NOTE for board bookkeeping: the recorded meta gates still carry the pre-repair G-EQ=BROKEN/G-PANEL-1=fail verdicts from 2026-08-12; those were against the old value-keyed model and are stale — this re-audit of the repaired model.py should overwrite them to pass.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong) review: does the modeled to_unstacked disagree with the real patched DataArray.to_unstacked_dataset on any precondition-satisfying input? No such divergence found.

Decisive machine evidence:
- G-CONF (differential conformance) PASS on 100,064 inputs (64 boundary + 100k fuzz, seed 4094), 0 disagreements. This directly tests my question: the contract-stripped impl region, with `assemble` realized by the REAL xr.Dataset(...) constructor/merge over REAL .sel({variable_dim:k}, drop=discard).squeeze(drop=True) slices, is compared against the REAL PATCHED to_unstacked_dataset across the entire Requires domain (n>=2, len(data)==len(resid)==n, resid pairwise-distinct). Outcome and recovered per-member values agree on every case.
- G-AX PASS (in-container): carried(False,pos)==pos and carried(True,pos)==shared_value() match real .sel(drop=...).squeeze; the Dataset merge rejects the conflicting kept residual (drop=False) and recovers verbatim (drop=True). Axioms model only UNCHANGED callees.
- G-GOLD PASS: gold-faithful model.py verifies.

Postcondition tightness does not overshoot reality: with the gold's discard=True, distinct_residuals implies all_equal(carried_seq(True,resid)) (lemma_carried_all_equal), so the real merge always succeeds, recovers data verbatim (ToSeq(Result())==ToSeq(data)), and grants the combined_collection token. Nothing the spec Ensures fails on the real function for any precondition-satisfying input.

Note on the recorded G-EQ=fail: it is a spec-too-WEAK break (atk_launder verifies but its faithful patch does not resolve — the combined_collection token was value-keyed, allowing a merge-skipping launder impl). That is the OPPOSITE direction from this gate (spec-too-weak admits a wrong impl; it does not make the gold-faithful model diverge from the real callee). It is not a faithfulness/spec-too-strong defect, so it does not support UNFAITHFUL here.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view for pydata__xarray-4094/nagini does not leak the gold edit beyond the public problem_statement. Gold edit = one-line `drop=True` addition at xarray/core/dataarray.py:1964 (`self.sel({variable_dim: k}, drop=True).squeeze(drop=True)`). Checks: (1) impl region is correctly elided to `...` in the spec_view projection (verified via markers.spec_view over NaginiBackend); the discriminating choice `discard = True` lives only in the elided impl, not in the visible spec. (2) The literal `drop=True`, the repo callees (sel/squeeze/Dataset/merge), the file path, and the MergeError are absent from the spec view — they appear only in mapping.md/refinement.md, which are NOT part of the consumer spec view. (3) All spec-view identifiers (to_unstacked, carried, shared_value, assemble, combined_collection, distinct_residuals, carried_seq, all_equal) are invented abstract model names, not patched repo symbols. (4) The only patched repo symbol, to_unstacked_dataset, is already public in the problem_statement title and does not appear verbatim in the spec view. (5) No diff markers, no gold-line reproduction (>=8-char normalized), no narration words. Mechanical confirmation: leakage.screen(model.py, NaginiBackend, real dataset gold patch, problem_statement) returned PASSED with zero hard failures; _patch_changed_symbols={to_unstacked_dataset} (public), _patch_changed_lines contain no >=8-char normalized substring of the spec view. The behavioral narrative faithfully restates the public issue (roundtrip should recover values; combination rejected on conflicting shared-name annotation / MergeError) without disclosing the repo-level fix. NOTE: meta.json's patch_diff field is a placeholder string ('gold patch verbatim...') rather than the real diff; the real gold patch was fetched from data/swe_bench_verified/test.jsonl for the screen.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
