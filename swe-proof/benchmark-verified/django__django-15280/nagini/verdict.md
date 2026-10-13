# P2 adversarial audit — django__django-15280

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1_prepatch.py`, `atk2_partial_skip0.py`, `atk3_boundary_short.py`, `atk4_inverted_guard.py`, `atk5_overwrite_effect.py`, `atk7_equiv_guard.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk6_echo_unconditional.py`, `atk8_reverse_loop.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                             slot_full[k] == 0 or slot_full[k] == 1),
                                     [[slot_full[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(slot_value)))
@@ -101,7 +99,6 @@
     # impl-start
     i = 0
     while i < len(slot_value):
-        # invariants-start
         Invariant(Acc(list_pred(slot_value)))
         Invariant(Acc(list_pred(slot_full), 1 / 2))
         Invariant(Acc(list_pred(supplied), 1 / 2))
@@ -109,21 +106,16 @@
         Invariant(len(slot_value) == len(slot_full))
         Invariant(len(slot_value) == len(supplied))
         Invariant(0 <= i and i <= len(slot_value))
-        # Children already processed satisfy the per-child guarantee.
         Invariant(Forall(int, lambda k: (
             Implies(0 <= k and k < i,
                     slot_value[k] == linked_parent(slot_full[k],
                                                    Old(slot_value[k]),
                                                    supplied[k])),
             [[slot_value[k]]])))
-        # Children not yet processed still hold their original parent.
         Invariant(Forall(int, lambda k: (
             Implies(i <= k and k < len(slot_value),
                     slot_value[k] == Old(slot_value[k])),
             [[slot_value[k]]])))
-        Invariant(MustTerminate(len(slot_value) - i + 1))
-        # invariants-end
-        if slot_full[i] != 1:
-            slot_value[i] = supplied[i]
+        slot_value[i] = supplied[i]
         i = i + 1
     # impl-end
```

Attack 2 — `atk2_partial_skip0.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                             slot_full[k] == 0 or slot_full[k] == 1),
                                     [[slot_full[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(slot_value)))
@@ -99,9 +97,8 @@
         [[slot_value[k]]])))
     # post-conditions-end
     # impl-start
-    i = 0
+    i = 1
     while i < len(slot_value):
-        # invariants-start
         Invariant(Acc(list_pred(slot_value)))
         Invariant(Acc(list_pred(slot_full), 1 / 2))
         Invariant(Acc(list_pred(supplied), 1 / 2))
@@ -109,20 +106,16 @@
         Invariant(len(slot_value) == len(slot_full))
         Invariant(len(slot_value) == len(supplied))
         Invariant(0 <= i and i <= len(slot_value))
-        # Children already processed satisfy the per-child guarantee.
         Invariant(Forall(int, lambda k: (
             Implies(0 <= k and k < i,
                     slot_value[k] == linked_parent(slot_full[k],
                                                    Old(slot_value[k]),
                                                    supplied[k])),
             [[slot_value[k]]])))
-        # Children not yet processed still hold their original parent.
         Invariant(Forall(int, lambda k: (
             Implies(i <= k and k < len(slot_value),
                     slot_value[k] == Old(slot_value[k])),
             [[slot_value[k]]])))
-        Invariant(MustTerminate(len(slot_value) - i + 1))
-        # invariants-end
         if slot_full[i] != 1:
             slot_value[i] = supplied[i]
         i = i + 1
```

Attack 3 — `atk3_boundary_short.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                             slot_full[k] == 0 or slot_full[k] == 1),
                                     [[slot_full[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(slot_value)))
@@ -100,8 +98,7 @@
     # post-conditions-end
     # impl-start
     i = 0
-    while i < len(slot_value):
-        # invariants-start
+    while i < len(slot_value) - 1:
         Invariant(Acc(list_pred(slot_value)))
         Invariant(Acc(list_pred(slot_full), 1 / 2))
         Invariant(Acc(list_pred(supplied), 1 / 2))
@@ -109,20 +106,16 @@
         Invariant(len(slot_value) == len(slot_full))
         Invariant(len(slot_value) == len(supplied))
         Invariant(0 <= i and i <= len(slot_value))
-        # Children already processed satisfy the per-child guarantee.
         Invariant(Forall(int, lambda k: (
             Implies(0 <= k and k < i,
                     slot_value[k] == linked_parent(slot_full[k],
                                                    Old(slot_value[k]),
                                                    supplied[k])),
             [[slot_value[k]]])))
-        # Children not yet processed still hold their original parent.
         Invariant(Forall(int, lambda k: (
             Implies(i <= k and k < len(slot_value),
                     slot_value[k] == Old(slot_value[k])),
             [[slot_value[k]]])))
-        Invariant(MustTerminate(len(slot_value) - i + 1))
-        # invariants-end
         if slot_full[i] != 1:
             slot_value[i] = supplied[i]
         i = i + 1
```

Attack 4 — `atk4_inverted_guard.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                             slot_full[k] == 0 or slot_full[k] == 1),
                                     [[slot_full[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(slot_value)))
@@ -101,7 +99,6 @@
     # impl-start
     i = 0
     while i < len(slot_value):
-        # invariants-start
         Invariant(Acc(list_pred(slot_value)))
         Invariant(Acc(list_pred(slot_full), 1 / 2))
         Invariant(Acc(list_pred(supplied), 1 / 2))
@@ -109,21 +106,17 @@
         Invariant(len(slot_value) == len(slot_full))
         Invariant(len(slot_value) == len(supplied))
         Invariant(0 <= i and i <= len(slot_value))
-        # Children already processed satisfy the per-child guarantee.
         Invariant(Forall(int, lambda k: (
             Implies(0 <= k and k < i,
                     slot_value[k] == linked_parent(slot_full[k],
                                                    Old(slot_value[k]),
                                                    supplied[k])),
             [[slot_value[k]]])))
-        # Children not yet processed still hold their original parent.
         Invariant(Forall(int, lambda k: (
             Implies(i <= k and k < len(slot_value),
                     slot_value[k] == Old(slot_value[k])),
             [[slot_value[k]]])))
-        Invariant(MustTerminate(len(slot_value) - i + 1))
-        # invariants-end
-        if slot_full[i] != 1:
+        if slot_full[i] == 1:
             slot_value[i] = supplied[i]
         i = i + 1
     # impl-end
```

Attack 5 — `atk5_overwrite_effect.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                             slot_full[k] == 0 or slot_full[k] == 1),
                                     [[slot_full[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(slot_value)))
@@ -101,7 +99,6 @@
     # impl-start
     i = 0
     while i < len(slot_value):
-        # invariants-start
         Invariant(Acc(list_pred(slot_value)))
         Invariant(Acc(list_pred(slot_full), 1 / 2))
         Invariant(Acc(list_pred(supplied), 1 / 2))
@@ -109,21 +106,18 @@
         Invariant(len(slot_value) == len(slot_full))
         Invariant(len(slot_value) == len(supplied))
         Invariant(0 <= i and i <= len(slot_value))
-        # Children already processed satisfy the per-child guarantee.
         Invariant(Forall(int, lambda k: (
             Implies(0 <= k and k < i,
                     slot_value[k] == linked_parent(slot_full[k],
                                                    Old(slot_value[k]),
                                                    supplied[k])),
             [[slot_value[k]]])))
-        # Children not yet processed still hold their original parent.
         Invariant(Forall(int, lambda k: (
             Implies(i <= k and k < len(slot_value),
                     slot_value[k] == Old(slot_value[k])),
             [[slot_value[k]]])))
-        Invariant(MustTerminate(len(slot_value) - i + 1))
-        # invariants-end
-        if slot_full[i] != 1:
-            slot_value[i] = supplied[i]
+        slot_value[i] = supplied[i]
+        if slot_full[i] == 1:
+            slot_value[i] = slot_value[i]
         i = i + 1
     # impl-end
```

Attack 6 — `atk6_echo_unconditional.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                             slot_full[k] == 0 or slot_full[k] == 1),
                                     [[slot_full[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(slot_value)))
@@ -101,7 +99,6 @@
     # impl-start
     i = 0
     while i < len(slot_value):
-        # invariants-start
         Invariant(Acc(list_pred(slot_value)))
         Invariant(Acc(list_pred(slot_full), 1 / 2))
         Invariant(Acc(list_pred(supplied), 1 / 2))
@@ -109,21 +106,16 @@
         Invariant(len(slot_value) == len(slot_full))
         Invariant(len(slot_value) == len(supplied))
         Invariant(0 <= i and i <= len(slot_value))
-        # Children already processed satisfy the per-child guarantee.
         Invariant(Forall(int, lambda k: (
             Implies(0 <= k and k < i,
                     slot_value[k] == linked_parent(slot_full[k],
                                                    Old(slot_value[k]),
                                                    supplied[k])),
             [[slot_value[k]]])))
-        # Children not yet processed still hold their original parent.
         Invariant(Forall(int, lambda k: (
             Implies(i <= k and k < len(slot_value),
                     slot_value[k] == Old(slot_value[k])),
             [[slot_value[k]]])))
-        Invariant(MustTerminate(len(slot_value) - i + 1))
-        # invariants-end
-        if slot_full[i] != 1:
-            slot_value[i] = supplied[i]
+        slot_value[i] = linked_parent(slot_full[i], slot_value[i], supplied[i])
         i = i + 1
     # impl-end
```

Attack 7 — `atk7_equiv_guard.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                             slot_full[k] == 0 or slot_full[k] == 1),
                                     [[slot_full[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(slot_value)))
@@ -101,7 +99,6 @@
     # impl-start
     i = 0
     while i < len(slot_value):
-        # invariants-start
         Invariant(Acc(list_pred(slot_value)))
         Invariant(Acc(list_pred(slot_full), 1 / 2))
         Invariant(Acc(list_pred(supplied), 1 / 2))
@@ -109,21 +106,17 @@
         Invariant(len(slot_value) == len(slot_full))
         Invariant(len(slot_value) == len(supplied))
         Invariant(0 <= i and i <= len(slot_value))
-        # Children already processed satisfy the per-child guarantee.
         Invariant(Forall(int, lambda k: (
             Implies(0 <= k and k < i,
                     slot_value[k] == linked_parent(slot_full[k],
                                                    Old(slot_value[k]),
                                                    supplied[k])),
             [[slot_value[k]]])))
-        # Children not yet processed still hold their original parent.
         Invariant(Forall(int, lambda k: (
             Implies(i <= k and k < len(slot_value),
                     slot_value[k] == Old(slot_value[k])),
             [[slot_value[k]]])))
-        Invariant(MustTerminate(len(slot_value) - i + 1))
-        # invariants-end
-        if slot_full[i] != 1:
+        if slot_full[i] == 0:
             slot_value[i] = supplied[i]
         i = i + 1
     # impl-end
```

Attack 8 — `atk8_reverse_loop.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                             slot_full[k] == 0 or slot_full[k] == 1),
                                     [[slot_full[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(slot_value)))
@@ -99,31 +97,26 @@
         [[slot_value[k]]])))
     # post-conditions-end
     # impl-start
-    i = 0
-    while i < len(slot_value):
-        # invariants-start
+    i = len(slot_value) - 1
+    while i >= 0:
         Invariant(Acc(list_pred(slot_value)))
         Invariant(Acc(list_pred(slot_full), 1 / 2))
         Invariant(Acc(list_pred(supplied), 1 / 2))
         Invariant(len(slot_value) == Old(len(slot_value)))
         Invariant(len(slot_value) == len(slot_full))
         Invariant(len(slot_value) == len(supplied))
-        Invariant(0 <= i and i <= len(slot_value))
-        # Children already processed satisfy the per-child guarantee.
+        Invariant(-1 <= i and i < len(slot_value))
         Invariant(Forall(int, lambda k: (
-            Implies(0 <= k and k < i,
+            Implies(i < k and k < len(slot_value),
                     slot_value[k] == linked_parent(slot_full[k],
                                                    Old(slot_value[k]),
                                                    supplied[k])),
             [[slot_value[k]]])))
-        # Children not yet processed still hold their original parent.
         Invariant(Forall(int, lambda k: (
-            Implies(i <= k and k < len(slot_value),
+            Implies(0 <= k and k <= i,
                     slot_value[k] == Old(slot_value[k])),
             [[slot_value[k]]])))
-        Invariant(MustTerminate(len(slot_value) - i + 1))
-        # invariants-end
         if slot_full[i] != 1:
             slot_value[i] = supplied[i]
-        i = i + 1
+        i = i - 1
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15280.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a collection of child rows has been fetched for a set of parent rows,
  each child must be linked back to the parent it belongs to so that walking
  from the child to that parent needs no further fetch. Each child carries a
  single slot that remembers the parent it is linked to; that slot is either
  EMPTY or already holds a parent.

  The pinned behaviour is what may write that slot. A child whose slot is
  already populated keeps its existing parent untouched: an earlier, more
  specific link (for instance one established by a separately fetched
  child-to-parent collection) is authoritative and must survive. Only a child
  whose slot is still EMPTY is linked to the parent supplied for it by the
  current collection.

  Concretely, for each child in the collection: if its slot was already
  populated, after the operation it still holds the very same parent it held
  before; if its slot was empty, after the operation it holds exactly the parent
  supplied for that child, and is no longer empty. No populated slot is ever
  overwritten.

Each child is modelled by two parallel integer lists: `slot_full[i]` is 1 iff
child i's parent slot was already populated, and `slot_value[i]` is the parent
identifier stored there (a non-negative id, or the sentinel -1 when empty). The
parent supplied for child i by the current collection is `supplied[i]` (a
non-negative id). The operation mutates the children's slots; `supplied` and the
record of which slots were initially populated are read-only.

The per-child resulting parent is the deep model `linked_parent`; no callee is
axiomatized (the slot test and the slot write are spelled out directly).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The slot-occupancy test and the slot write are ordinary
# concrete operations modelled directly; the behaviour under specification — a
# populated slot is preserved, an empty slot receives the supplied parent — is
# pinned by the pure `linked_parent` map below and the verified loop, not behind
# a @ContractOnly. G-EQ audits the refinement to the real descriptor code.)
# axioms-end


# pure-start
@Pure
def linked_parent(was_full: int, old_value: int, supplied: int) -> int:
    """The parent a child's slot holds after the operation.

    If the slot was already populated (`was_full == 1`) it keeps its prior
    parent `old_value` unchanged; otherwise it receives the parent `supplied`
    for that child by the current collection."""
    if was_full == 1:
        return old_value
    return supplied
# pure-end


def link_children_to_parents(slot_full: List[int],
                             slot_value: List[int],
                             supplied: List[int]) -> None:
    # pre-conditions-start
    # The children's slots are mutated, so full permission on `slot_value`.
    Requires(Acc(list_pred(slot_value)))
    # The record of which slots were initially populated and the supplied
    # parents are read-only: fractional permission, required AND ensured, so no
    # implementation can satisfy a postcondition vacuously by overwriting them.
    Requires(Acc(list_pred(slot_full), 1 / 2))
    Requires(Acc(list_pred(supplied), 1 / 2))
    # The three lists describe the same collection of children.
    Requires(len(slot_full) == len(slot_value))
    Requires(len(supplied) == len(slot_value))
    # `slot_full` is a 0/1 occupancy flag per child.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                            slot_full[k] == 0 or slot_full[k] == 1),
                                    [[slot_full[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(slot_value)))
    Ensures(Acc(list_pred(slot_full), 1 / 2))
    Ensures(Acc(list_pred(supplied), 1 / 2))
    # The collection shape is preserved.
    Ensures(len(slot_value) == Old(len(slot_value)))
    Ensures(len(slot_value) == len(slot_full))
    Ensures(len(slot_value) == len(supplied))
    # Per child: a populated slot keeps its prior parent; an empty slot now
    # holds the parent supplied for that child. No populated slot is overwritten.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(slot_value),
                slot_value[k] == linked_parent(slot_full[k],
                                               Old(slot_value[k]),
                                               supplied[k])),
        [[slot_value[k]]])))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(slot_value):
        # invariants-start
        Invariant(Acc(list_pred(slot_value)))
        Invariant(Acc(list_pred(slot_full), 1 / 2))
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(len(slot_value) == Old(len(slot_value)))
        Invariant(len(slot_value) == len(slot_full))
        Invariant(len(slot_value) == len(supplied))
        Invariant(0 <= i and i <= len(slot_value))
        # Children already processed satisfy the per-child guarantee.
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < i,
                    slot_value[k] == linked_parent(slot_full[k],
                                                   Old(slot_value[k]),
                                                   supplied[k])),
            [[slot_value[k]]])))
        # Children not yet processed still hold their original parent.
        Invariant(Forall(int, lambda k: (
            Implies(i <= k and k < len(slot_value),
                    slot_value[k] == Old(slot_value[k])),
            [[slot_value[k]]])))
        # invariants-end
        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

env, SBU_BENCHMARK_DIR=.../benchmark-verified, python=python (adversary) and scripts/nagini_verify.sh (verify).

**SPEC SHAPE:** link_children_to_parents' postcondition PINS every slot_value[k] exactly to linked_parent(slot_full[k], Old(slot_value[k]), supplied[k]) via a Forall over the whole domain, with read-only fractional perms Acc(list_pred(slot_full),1/2) and Acc(list_pred(supplied),1/2) required AND ensured (blocks vacuous satisfaction by overwriting inputs). meta.json: axioms=[], deep_model_references=[]; single kind-I callee FieldCacheMixin.is_cached/set_cached_value. => functionally-tight spec, no A-consumed / A-reference / kind-3 legs to break.

ATTACKS (all confirmed same-spec via `adversary same-spec`, exit 0; each = model.py with ONLY impl region edited, header lines 1-99 & footer verified byte-identical):
- atk1_prepatch (unconditional write): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). PREPATCH REPRODUCED (spec rejects the bug).
- atk2_partial_skip0 (partial-domain, start i=1, child0 never written): verification failed (exit 2).
- atk3_boundary_short (i<len-1, last child untouched): verification failed (exit 2).
- atk4_inverted_guard (write only when slot_full==1): verification failed (exit 2).
- atk5_overwrite_effect (control-flow: unconditional write then no-op restore): verification failed (exit 2).
- atk7_equiv_guard (guard slot_full==0): verification failed (exit 2) [did not verify here; not a candidate].
- atk6_echo_unconditional (ungrounded-oracle echo: slot_value[i]=linked_parent(...)): CANDIDATE (same-spec AND verifies).
- atk8_reverse_loop (reverse-order guarded loop, different control flow): CANDIDATE (verifies 14.5s).

MANDATORY RESOLVE STEP for every candidate (materialized faithful refined patch -> official harness run_resolve, timeout 1800, retries 1):
 - atk6 faithful patch (patch_atk6.diff: always setattr; cached child gets its cached parent via get_cached_value, else supplied): RESOLVED=True COMPLETED=True; F2P success=['The prefetched relationship is used rather than populating the reverse'], failure=[]; PASS_TO_PASS failures=0.
 - atk8 faithful patch (patch_atk8.diff: reversed(list(queryset)) + gold's `if not is_cached` guard): RESOLVED=True COMPLETED=True; F2P success, P2P failures=0.
 Both candidates' faithful patches RESOLVE => neither exhibits verify-and-not-correct.

**POSITIVE CONTROL:** positive_control.py (=model.py) -> nagini_verify.sh exit 0 (Verification successful, 11.4s).
G-AX / axiom_check.py: exit 0, linked_parent == real FieldCacheMixin over 20007 boundary+fuzz collections (stdlib reconstruction path used since Django not importable outside container; in-container path identical two-line source).

REFINEMENT.md AUDIT: legs A1(R: child collection<->indices), A2(I+R: is_cached bool<->{0,1} occupancy flag, new guard), A3(I+R: setattr->set_cached_value slot store<->slot_value assignment). NO A-consumed axiom, NO A-reference deep model of a changed op, NO kind-3. The only changed op is the added occupancy guard (concrete int compare) around an unchanged concrete store; FieldCacheMixin correspondence to the real callees (mixins.py:21-25, related_descriptors.py:261 forward `__set__`) is kind-I and executably validated by G-AX. Correspondence holds.

**VERDICT:** SOUND. 8 distinct wrong/echo impls run; the 6 behaviourally-wrong impls are all rejected by verification; the 2 verifying candidates (echo + reverse-order) both refine to faithful patches that RESOLVE under the official harness. No verifying wrong-impl whose faithful patch fails to resolve was found; spec is not too weak on this instance.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1_prepatch.py`, `atk2_partial_skip0.py`, `atk3_boundary_short.py`, `atk4_inverted_guard.py`, `atk5_overwrite_effect.py`, `atk7_equiv_guard.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk6_echo_unconditional.py`, `atk8_reverse_loop.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_partial_skip0.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_boundary_short.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_inverted_guard.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_overwrite_effect.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_echo_unconditional.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk7_equiv_guard.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_reverse_loop.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15280.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a collection of child rows has been fetched for a set of parent rows,
  each child must be linked back to the parent it belongs to so that walking
  from the child to that parent needs no further fetch. Each child carries a
  single slot that remembers the parent it is linked to; that slot is either
  EMPTY or already holds a parent.

  The pinned behaviour is what may write that slot. A child whose slot is
  already populated keeps its existing parent untouched: an earlier, more
  specific link (for instance one established by a separately fetched
  child-to-parent collection) is authoritative and must survive. Only a child
  whose slot is still EMPTY is linked to the parent supplied for it by the
  current collection.

  Concretely, for each child in the collection: if its slot was already
  populated, after the operation it still holds the very same parent it held
  before; if its slot was empty, after the operation it holds exactly the parent
  supplied for that child, and is no longer empty. No populated slot is ever
  overwritten.

Each child is modelled by two parallel integer lists: `slot_full[i]` is 1 iff
child i's parent slot was already populated, and `slot_value[i]` is the parent
identifier stored there (a non-negative id, or the sentinel -1 when empty). The
parent supplied for child i by the current collection is `supplied[i]` (a
non-negative id). The operation mutates the children's slots; `supplied` and the
record of which slots were initially populated are read-only.

The per-child resulting parent is the deep model `linked_parent`; no callee is
axiomatized (the slot test and the slot write are spelled out directly).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The slot-occupancy test and the slot write are ordinary
# concrete operations modelled directly; the behaviour under specification — a
# populated slot is preserved, an empty slot receives the supplied parent — is
# pinned by the pure `linked_parent` map below and the verified loop, not behind
# a @ContractOnly. G-EQ audits the refinement to the real descriptor code.)
# axioms-end


# pure-start
@Pure
def linked_parent(was_full: int, old_value: int, supplied: int) -> int:
    """The parent a child's slot holds after the operation.

    If the slot was already populated (`was_full == 1`) it keeps its prior
    parent `old_value` unchanged; otherwise it receives the parent `supplied`
    for that child by the current collection."""
    if was_full == 1:
        return old_value
    return supplied
# pure-end


def link_children_to_parents(slot_full: List[int],
                             slot_value: List[int],
                             supplied: List[int]) -> None:
    # pre-conditions-start
    # The children's slots are mutated, so full permission on `slot_value`.
    Requires(Acc(list_pred(slot_value)))
    # The record of which slots were initially populated and the supplied
    # parents are read-only: fractional permission, required AND ensured, so no
    # implementation can satisfy a postcondition vacuously by overwriting them.
    Requires(Acc(list_pred(slot_full), 1 / 2))
    Requires(Acc(list_pred(supplied), 1 / 2))
    # The three lists describe the same collection of children.
    Requires(len(slot_full) == len(slot_value))
    Requires(len(supplied) == len(slot_value))
    # `slot_full` is a 0/1 occupancy flag per child.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(slot_full),
                                            slot_full[k] == 0 or slot_full[k] == 1),
                                    [[slot_full[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(slot_value)))
    Ensures(Acc(list_pred(slot_full), 1 / 2))
    Ensures(Acc(list_pred(supplied), 1 / 2))
    # The collection shape is preserved.
    Ensures(len(slot_value) == Old(len(slot_value)))
    Ensures(len(slot_value) == len(slot_full))
    Ensures(len(slot_value) == len(supplied))
    # Per child: a populated slot keeps its prior parent; an empty slot now
    # holds the parent supplied for that child. No populated slot is overwritten.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(slot_value),
                slot_value[k] == linked_parent(slot_full[k],
                                               Old(slot_value[k]),
                                               supplied[k])),
        [[slot_value[k]]])))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(slot_value):
        # invariants-start
        Invariant(Acc(list_pred(slot_value)))
        Invariant(Acc(list_pred(slot_full), 1 / 2))
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(len(slot_value) == Old(len(slot_value)))
        Invariant(len(slot_value) == len(slot_full))
        Invariant(len(slot_value) == len(supplied))
        Invariant(0 <= i and i <= len(slot_value))
        # Children already processed satisfy the per-child guarantee.
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < i,
                    slot_value[k] == linked_parent(slot_full[k],
                                                   Old(slot_value[k]),
                                                   supplied[k])),
            [[slot_value[k]]])))
        # Children not yet processed still hold their original parent.
        Invariant(Forall(int, lambda k: (
            Implies(i <= k and k < len(slot_value),
                    slot_value[k] == Old(slot_value[k])),
            [[slot_value[k]]])))
        # invariants-end
        if slot_full[i] != 1:
            slot_value[i] = supplied[i]
        i = i + 1
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

env, SBU_BENCHMARK_DIR=.../benchmark-verified, python=python (adversary) and scripts/nagini_verify.sh (verify).

**SPEC SHAPE:** link_children_to_parents' postcondition PINS every slot_value[k] exactly to linked_parent(slot_full[k], Old(slot_value[k]), supplied[k]) via a Forall over the whole domain, with read-only fractional perms Acc(list_pred(slot_full),1/2) and Acc(list_pred(supplied),1/2) required AND ensured (blocks vacuous satisfaction by overwriting inputs). meta.json: axioms=[], deep_model_references=[]; single kind-I callee FieldCacheMixin.is_cached/set_cached_value. => functionally-tight spec, no A-consumed / A-reference / kind-3 legs to break.

ATTACKS (all confirmed same-spec via `adversary same-spec`, exit 0; each = model.py with ONLY impl region edited, header lines 1-99 & footer verified byte-identical):
- atk1_prepatch (unconditional write): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). PREPATCH REPRODUCED (spec rejects the bug).
- atk2_partial_skip0 (partial-domain, start i=1, child0 never written): verification failed (exit 2).
- atk3_boundary_short (i<len-1, last child untouched): verification failed (exit 2).
- atk4_inverted_guard (write only when slot_full==1): verification failed (exit 2).
- atk5_overwrite_effect (control-flow: unconditional write then no-op restore): verification failed (exit 2).
- atk7_equiv_guard (guard slot_full==0): verification failed (exit 2) [did not verify here; not a candidate].
- atk6_echo_unconditional (ungrounded-oracle echo: slot_value[i]=linked_parent(...)): CANDIDATE (same-spec AND verifies).
- atk8_reverse_loop (reverse-order guarded loop, different control flow): CANDIDATE (verifies 14.5s).

MANDATORY RESOLVE STEP for every candidate (materialized faithful refined patch -> official harness run_resolve, timeout 1800, retries 1):
 - atk6 faithful patch (patch_atk6.diff: always setattr; cached child gets its cached parent via get_cached_value, else supplied): RESOLVED=True COMPLETED=True; F2P success=['The prefetched relationship is used rather than populating the reverse'], failure=[]; PASS_TO_PASS failures=0.
 - atk8 faithful patch (patch_atk8.diff: reversed(list(queryset)) + gold's `if not is_cached` guard): RESOLVED=True COMPLETED=True; F2P success, P2P failures=0.
 Both candidates' faithful patches RESOLVE => neither exhibits verify-and-not-correct.

**POSITIVE CONTROL:** positive_control.py (=model.py) -> nagini_verify.sh exit 0 (Verification successful, 11.4s).
G-AX / axiom_check.py: exit 0, linked_parent == real FieldCacheMixin over 20007 boundary+fuzz collections (stdlib reconstruction path used since Django not importable outside container; in-container path identical two-line source).

REFINEMENT.md AUDIT: legs A1(R: child collection<->indices), A2(I+R: is_cached bool<->{0,1} occupancy flag, new guard), A3(I+R: setattr->set_cached_value slot store<->slot_value assignment). NO A-consumed axiom, NO A-reference deep model of a changed op, NO kind-3. The only changed op is the added occupancy guard (concrete int compare) around an unchanged concrete store; FieldCacheMixin correspondence to the real callees (mixins.py:21-25, related_descriptors.py:261 forward `__set__`) is kind-I and executably validated by G-AX. Correspondence holds.

**VERDICT:** SOUND. 8 distinct wrong/echo impls run; the 6 behaviourally-wrong impls are all rejected by verification; the 2 verifying candidates (echo + reverse-order) both refine to faithful patches that RESOLVE under the official harness. No verifying wrong-impl whose faithful patch fails to resolve was found; spec is not too weak on this instance.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-15280 (nagini). No divergence between the modeled function and the real repo behavior found.

**Spec region:** byte-identical (same-spec command exits 0 on the bundle model). The spec (linked_parent + loop postcondition) models the POST-patch reverse-relation population loop in RelatedManager.get_prefetch_queryset.

**Real callee:** worktree is at base_commit 973fa566521037ac140dcece73fceae50ee522f1 (pre-patch), where related_descriptors.py:647-649 is the UNCONDITIONAL loop `instance = instances_dict[rel_obj_attr(rel_obj)]; setattr(rel_obj, self.field.name, instance)`. The gold patch wraps the body in `if not self.field.is_cached(rel_obj):`. The model matches: guard = slot_full[i]==1 (populated -> keep old_value), write = slot_value[i]=supplied[i] (empty -> take supplied). linked_parent(1,old,s)==old and linked_parent(0,_,s)==s exactly mirror the guarded loop.

Abstraction fidelity (G-AX): axiom_check.py run with binds the REAL django.db.models.fields.mixins.FieldCacheMixin (reported mode 'real django.db.models.fields.mixins.FieldCacheMixin'), is_cached = key membership of `_state`.fields_cache, set_cached_value = key store. Over 7 boundary + 20000 fuzz child collections (20007 total) the FIXED guarded loop == linked_parent for every child, and the buggy loop clobbers populated slots. Exit 0.

**Positive control:** nagini_verify.sh on model.py -> Verification successful (13.13s).

**Not too strong:** precondition slot_full[k] in {0,1} is faithful to is_cached returning bool. The spec scopes only the parent cache slot (the F2P-observed Room.house.is_cached entry); it makes no claim about the FK attname columns or the one-to-one reverse cache that setattr also writes, so it does not over-constrain unrelated state. Per-child independence is faithful because distinct children carry distinct `_state`.fields_cache dicts.

Searched boundary (empty, single empty, single populated supplied-differs/same, mixed, all-populated, all-empty) and 20000 randomized collections for any input where linked_parent disagrees with the real FieldCacheMixin-driven fixed loop; none found. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Reconstructed the exact consumer spec view via markers.spec_view(nagini): docstring + axioms comment + pure `linked_parent` + pre/post-conditions; the impl loop and invariants are elided. Ran the mechanical G-LEAK screen (leakage.screen) — PASSED, zero hard failures. Manual review confirms: no diff markers, no patched file path (django/db/models/fields/related_descriptors.py) or module path, and the single distinctive patched symbol `get_prefetch_queryset` does not appear in the spec view. No Django cache identifiers (is_cached, setattr, set_cached_value, FieldCacheMixin, field.name) appear anywhere in the view — they live only in mapping.md / refinement.md / axiom_check.py, which are auditor artifacts, NOT part of the consumer spec view. The gold discriminator (guard so an already-populated child parent slot is not overwritten by the outer collection) is expressed purely abstractly as a behavioral property over three parallel List[int] with a -1 sentinel (populated slot preserved, empty slot receives supplied parent, no populated slot overwritten) — this is HOW-agnostic WHAT specification, revealing no edit location or code mechanism. It goes beyond the public problem_statement (which states only the symptom: deferred fields inherited from the outer queryset firing an extra query when following a prefetch back to the parent), but abstract specification of the fix's effect is inherent to any faithful twin-artifact spec and does not localize the gold edit. The axioms-comment mention 'G-EQ audits the refinement to the real descriptor code' is process metadata, not a code identifier. No RELAXED_LEAKAGE.md present; no relaxation invoked. Recorded G-LEAK meta gate = pass, G-PANEL-3 prior verdict = NO-LEAKAGE — both consistent.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
