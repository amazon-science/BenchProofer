# P2 adversarial audit — django__django-16819

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -40,11 +39,6 @@
     (consulted only when it is an index-removal), and its elidable flag."""
 
     def __init__(self, is_remove_index: bool, name: List[int], elidable: bool) -> None:
-        # Three field stores and no loop or call: this constructor obviously
-        # terminates. Level 2 < reduce_add_index's 6 leaves room beneath the
-        # function under specification, so a caller that itself owes termination
-        # may still build the counterpart operation it passes in.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_remove_index) and self.is_remove_index == is_remove_index)  # type: ignore
         Ensures(Acc(self.name) and self.name is name)                                    # type: ignore
         Ensures(Acc(self.elidable) and self.elidable == elidable)                        # type: ignore
@@ -87,7 +81,6 @@
     Requires(Acc(operation.is_remove_index, 1 / 2))
     Requires(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
     Requires(Acc(operation.elidable, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(index_name), 1 / 2))
@@ -105,8 +98,6 @@
     Ensures(Result() == 0 or Result() == 1 or Result() == 2 or Result() == 3)
     # post-conditions-end
     # impl-start
-    if operation.is_remove_index and names_equal(index_name, operation.name):
-        return 1
     if self_elidable:
         return 2
     if operation.elidable:
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -40,11 +39,6 @@
     (consulted only when it is an index-removal), and its elidable flag."""
 
     def __init__(self, is_remove_index: bool, name: List[int], elidable: bool) -> None:
-        # Three field stores and no loop or call: this constructor obviously
-        # terminates. Level 2 < reduce_add_index's 6 leaves room beneath the
-        # function under specification, so a caller that itself owes termination
-        # may still build the counterpart operation it passes in.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_remove_index) and self.is_remove_index == is_remove_index)  # type: ignore
         Ensures(Acc(self.name) and self.name is name)                                    # type: ignore
         Ensures(Acc(self.elidable) and self.elidable == elidable)                        # type: ignore
@@ -87,7 +81,6 @@
     Requires(Acc(operation.is_remove_index, 1 / 2))
     Requires(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
     Requires(Acc(operation.elidable, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(index_name), 1 / 2))
@@ -106,7 +99,7 @@
     # post-conditions-end
     # impl-start
     if operation.is_remove_index and names_equal(index_name, operation.name):
-        return 1
+        return 0
     if self_elidable:
         return 2
     if operation.elidable:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -40,11 +39,6 @@
     (consulted only when it is an index-removal), and its elidable flag."""
 
     def __init__(self, is_remove_index: bool, name: List[int], elidable: bool) -> None:
-        # Three field stores and no loop or call: this constructor obviously
-        # terminates. Level 2 < reduce_add_index's 6 leaves room beneath the
-        # function under specification, so a caller that itself owes termination
-        # may still build the counterpart operation it passes in.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_remove_index) and self.is_remove_index == is_remove_index)  # type: ignore
         Ensures(Acc(self.name) and self.name is name)                                    # type: ignore
         Ensures(Acc(self.elidable) and self.elidable == elidable)                        # type: ignore
@@ -87,7 +81,6 @@
     Requires(Acc(operation.is_remove_index, 1 / 2))
     Requires(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
     Requires(Acc(operation.elidable, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(index_name), 1 / 2))
@@ -105,10 +98,10 @@
     Ensures(Result() == 0 or Result() == 1 or Result() == 2 or Result() == 3)
     # post-conditions-end
     # impl-start
+    if self_elidable:
+        return 2
     if operation.is_remove_index and names_equal(index_name, operation.name):
         return 1
-    if self_elidable:
-        return 2
     if operation.elidable:
         return 3
     return 0
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -40,11 +39,6 @@
     (consulted only when it is an index-removal), and its elidable flag."""
 
     def __init__(self, is_remove_index: bool, name: List[int], elidable: bool) -> None:
-        # Three field stores and no loop or call: this constructor obviously
-        # terminates. Level 2 < reduce_add_index's 6 leaves room beneath the
-        # function under specification, so a caller that itself owes termination
-        # may still build the counterpart operation it passes in.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_remove_index) and self.is_remove_index == is_remove_index)  # type: ignore
         Ensures(Acc(self.name) and self.name is name)                                    # type: ignore
         Ensures(Acc(self.elidable) and self.elidable == elidable)                        # type: ignore
@@ -87,7 +81,6 @@
     Requires(Acc(operation.is_remove_index, 1 / 2))
     Requires(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
     Requires(Acc(operation.elidable, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(index_name), 1 / 2))
@@ -105,7 +98,7 @@
     Ensures(Result() == 0 or Result() == 1 or Result() == 2 or Result() == 3)
     # post-conditions-end
     # impl-start
-    if operation.is_remove_index and names_equal(index_name, operation.name):
+    if names_equal(index_name, operation.name):
         return 1
     if self_elidable:
         return 2
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -40,11 +39,6 @@
     (consulted only when it is an index-removal), and its elidable flag."""
 
     def __init__(self, is_remove_index: bool, name: List[int], elidable: bool) -> None:
-        # Three field stores and no loop or call: this constructor obviously
-        # terminates. Level 2 < reduce_add_index's 6 leaves room beneath the
-        # function under specification, so a caller that itself owes termination
-        # may still build the counterpart operation it passes in.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_remove_index) and self.is_remove_index == is_remove_index)  # type: ignore
         Ensures(Acc(self.name) and self.name is name)                                    # type: ignore
         Ensures(Acc(self.elidable) and self.elidable == elidable)                        # type: ignore
@@ -87,7 +81,6 @@
     Requires(Acc(operation.is_remove_index, 1 / 2))
     Requires(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
     Requires(Acc(operation.elidable, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(index_name), 1 / 2))
@@ -108,8 +101,8 @@
     if operation.is_remove_index and names_equal(index_name, operation.name):
         return 1
     if self_elidable:
+        return 3
+    if operation.elidable:
         return 2
-    if operation.elidable:
-        return 3
     return 0
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -40,11 +39,6 @@
     (consulted only when it is an index-removal), and its elidable flag."""
 
     def __init__(self, is_remove_index: bool, name: List[int], elidable: bool) -> None:
-        # Three field stores and no loop or call: this constructor obviously
-        # terminates. Level 2 < reduce_add_index's 6 leaves room beneath the
-        # function under specification, so a caller that itself owes termination
-        # may still build the counterpart operation it passes in.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_remove_index) and self.is_remove_index == is_remove_index)  # type: ignore
         Ensures(Acc(self.name) and self.name is name)                                    # type: ignore
         Ensures(Acc(self.elidable) and self.elidable == elidable)                        # type: ignore
@@ -87,7 +81,6 @@
     Requires(Acc(operation.is_remove_index, 1 / 2))
     Requires(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
     Requires(Acc(operation.elidable, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(index_name), 1 / 2))
@@ -105,7 +98,7 @@
     Ensures(Result() == 0 or Result() == 1 or Result() == 2 or Result() == 3)
     # post-conditions-end
     # impl-start
-    if operation.is_remove_index and names_equal(index_name, operation.name):
+    if operation.is_remove_index:
         return 1
     if self_elidable:
         return 2
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -40,11 +39,6 @@
     (consulted only when it is an index-removal), and its elidable flag."""
 
     def __init__(self, is_remove_index: bool, name: List[int], elidable: bool) -> None:
-        # Three field stores and no loop or call: this constructor obviously
-        # terminates. Level 2 < reduce_add_index's 6 leaves room beneath the
-        # function under specification, so a caller that itself owes termination
-        # may still build the counterpart operation it passes in.
-        Requires(MustTerminate(2))
         Ensures(Acc(self.is_remove_index) and self.is_remove_index == is_remove_index)  # type: ignore
         Ensures(Acc(self.name) and self.name is name)                                    # type: ignore
         Ensures(Acc(self.elidable) and self.elidable == elidable)                        # type: ignore
@@ -87,7 +81,6 @@
     Requires(Acc(operation.is_remove_index, 1 / 2))
     Requires(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
     Requires(Acc(operation.elidable, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(index_name), 1 / 2))
@@ -109,7 +102,5 @@
         return 1
     if self_elidable:
         return 2
-    if operation.elidable:
-        return 3
-    return 0
+    return 3
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16819.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When two index-management operations on a model are considered for
  combination during migration optimisation, an operation that *adds* a named
  index, immediately considered against an operation that *removes* an index of
  the SAME name, contributes nothing: the pair cancels and the combined result
  is the empty operation list. This is the discriminating behaviour the issue
  asks for — adding an index and then removing the same index is a no-op.

  For every other counterpart operation the add-index operation falls back to
  the generic combination rule shared by all operations: a self-elidable
  operation is replaced by the counterpart alone; otherwise a counterpart that
  is elidable replaces the operation by the operation alone; otherwise the two
  operations cannot be combined.

The combination outcome is modelled as a small tagged code (Nagini has no mixed
list/bool return): 1 = "the pair cancels to nothing", 2 = "replace by the
counterpart alone", 3 = "replace by this operation alone", 0 = "cannot
combine". An operation is modelled as a minimal class carrying only the touched
facets: whether it is an index-removal, its name (a sequence of code points),
and whether it is elidable. The add-index operation carries the name of the
managed index and its own elidable flag.

The generic combination rule is the operation base class's own shared logic and
is modelled deeply (it is the superclass of the function under specification,
not an opaque external callee); there are therefore no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Operand:
    """A counterpart operation considered for combination. Only the touched
    facets are modelled: whether it removes an index, the name it carries
    (consulted only when it is an index-removal), and its elidable flag."""

    def __init__(self, is_remove_index: bool, name: List[int], elidable: bool) -> None:
        Ensures(Acc(self.is_remove_index) and self.is_remove_index == is_remove_index)  # type: ignore
        Ensures(Acc(self.name) and self.name is name)                                    # type: ignore
        Ensures(Acc(self.elidable) and self.elidable == elidable)                        # type: ignore
        self.is_remove_index = is_remove_index
        self.name = name
        self.elidable = elidable


# axioms-start
# (no axioms: the generic combination rule is the function-under-specification's
#  own base-class logic and is modelled deeply, not axiomatized)
# axioms-end


# pure-start
@Pure
def names_equal(a: List[int], b: List[int]) -> bool:
    """Whether two index names denote the same string."""
    Requires(Acc(list_pred(a), 1 / 4) and Acc(list_pred(b), 1 / 4))
    return ToSeq(a) == ToSeq(b)


@Pure
def base_combine(self_elidable: bool, op_elidable: bool) -> int:
    """The generic combination rule shared by every operation: a self-elidable
    operation is replaced by the counterpart alone (2); otherwise an elidable
    counterpart replaces the operation by the operation alone (3); otherwise the
    operations cannot be combined (0)."""
    if self_elidable:
        return 2
    if op_elidable:
        return 3
    return 0
# pure-end


def reduce_add_index(index_name: List[int], self_elidable: bool, operation: Operand) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(index_name), 1 / 2))
    Requires(Acc(operation.is_remove_index, 1 / 2))
    Requires(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
    Requires(Acc(operation.elidable, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(index_name), 1 / 2))
    Ensures(Acc(operation.is_remove_index, 1 / 2))
    Ensures(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
    Ensures(Acc(operation.elidable, 1 / 2))
    # The discriminating guarantee: an index-removal of the same name cancels
    # the add to the empty list (tag 1).
    Ensures(Implies(operation.is_remove_index and names_equal(index_name, operation.name),
                    Result() == 1))
    # Otherwise the outcome is exactly the generic combination rule.
    Ensures(Implies(not (operation.is_remove_index and names_equal(index_name, operation.name)),
                    Result() == base_combine(self_elidable, operation.elidable)))
    # The outcome is always one of the four legal tags.
    Ensures(Result() == 0 or Result() == 1 or Result() == 2 or Result() == 3)
    # post-conditions-end
    # impl-start
    if operation.is_remove_index and names_equal(index_name, operation.name):
        return 1
    if self_elidable:
        return 2
    if operation.elidable:
        return 3
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec for reduce_add_index is a TOTAL functional specification with zero slack: (clause1) is_remove_index & names_equal => Result==1; (clause2) otherwise => Result==base_combine(self_elidable, operation.elidable); (clause3) Result in {0,1,2,3}. base_combine is a @Pure helper in the frozen `pure` region (part of the spec signature — confirmed: a probe altering its tag values is flagged DIFFERENT by same-spec), so it computes a fixed value; every input therefore maps to exactly one legal Result. No verifying-wrong-impl exists, hence no faithful patch to materialize/resolve.

Attacks (all SAME-spec by construction; edited impl region only; `python -m swebench_unified.adversary weakness nagini django__django-16819 <path>`):
- positive_control.py: correct impl -> weakness exit 0 CANDIDATE (verifies in ~13.3s), as expected.
- atk_1.py PREPATCH BUG (no cancel branch, always defers to base rule) -> exit 2, verification failed. Prepatch bug reproduced: spec rejects the pre-patch behaviour (fails clause1 on matching RemoveIndex non-elidable, returns 0 not 1).
- atk_2.py partial-domain (cancel branch returns tag 0 not 1) -> exit 2, rejected.
- atk_3.py control-flow-effect (self_elidable checked BEFORE cancel branch) -> exit 2, rejected (violates clause1 when cancel case is also self_elidable).
- atk_4.py ungrounded-oracle echo (drop is_remove_index guard, cancel on any equal name) -> exit 2, rejected (over-cancels for non-removal counterpart).
- atk_5.py swapped base tags (self_elidable->3, op_elidable->2) -> exit 2, rejected (violates clause2 vs base_combine).
- atk_6.py boundary (drop names_equal check, cancel any RemoveIndex) -> exit 2, rejected.
- atk_7.py off-by fall-through (0 replaced by 3) -> exit 2, rejected.
7 distinct wrong impls, all same-spec, NONE verifies; only the correct impl verifies. No CANDIDATE counterexample => no patch needed resolve-running (nothing to break the spec).

Refinement/A-leg audit: NO axioms in this bundle (axioms region is comment-only; grep ContractOnly in model.py = NONE). The only callee super().reduce == Operation.reduce (base.py:129-139) is modeled DEEPLY as the @Pure base_combine (refinement.md step A6), not axiomatized — no kind-3 legs; every leg R / I / deep-model. axiom_check.py (exit 0) confirms the deep-model<->real-callee correspondence: base_combine == Operation.reduce on all 4 cases, reduce_add_index == gold AddIndex.reduce on 392 boundary + 50000 fuzz inputs, F2P cancellation witness holds. mapping.md MRO (AddIndex->IndexOperation->Operation, IndexOperation has no reduce override) is correct. No axiom-soundness trust point.

Commands used (project root; SBU_BENCHMARK_DIR already set; python python):
  same-spec nagini django__django-16819 <atk> -> exit 0 (SAME) for all 8 files
  weakness nagini django__django-16819 <atk> -> positive_control exit 0; atk_1..7 exit 2
  axiom_check.py -> exit 0

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16819.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When two index-management operations on a model are considered for
  combination during migration optimisation, an operation that *adds* a named
  index, immediately considered against an operation that *removes* an index of
  the SAME name, contributes nothing: the pair cancels and the combined result
  is the empty operation list. This is the discriminating behaviour the issue
  asks for — adding an index and then removing the same index is a no-op.

  For every other counterpart operation the add-index operation falls back to
  the generic combination rule shared by all operations: a self-elidable
  operation is replaced by the counterpart alone; otherwise a counterpart that
  is elidable replaces the operation by the operation alone; otherwise the two
  operations cannot be combined.

The combination outcome is modelled as a small tagged code (Nagini has no mixed
list/bool return): 1 = "the pair cancels to nothing", 2 = "replace by the
counterpart alone", 3 = "replace by this operation alone", 0 = "cannot
combine". An operation is modelled as a minimal class carrying only the touched
facets: whether it is an index-removal, its name (a sequence of code points),
and whether it is elidable. The add-index operation carries the name of the
managed index and its own elidable flag.

The generic combination rule is the operation base class's own shared logic and
is modelled deeply (it is the superclass of the function under specification,
not an opaque external callee); there are therefore no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Operand:
    """A counterpart operation considered for combination. Only the touched
    facets are modelled: whether it removes an index, the name it carries
    (consulted only when it is an index-removal), and its elidable flag."""

    def __init__(self, is_remove_index: bool, name: List[int], elidable: bool) -> None:
        Ensures(Acc(self.is_remove_index) and self.is_remove_index == is_remove_index)  # type: ignore
        Ensures(Acc(self.name) and self.name is name)                                    # type: ignore
        Ensures(Acc(self.elidable) and self.elidable == elidable)                        # type: ignore
        self.is_remove_index = is_remove_index
        self.name = name
        self.elidable = elidable


# axioms-start
# (no axioms: the generic combination rule is the function-under-specification's
#  own base-class logic and is modelled deeply, not axiomatized)
# axioms-end


# pure-start
@Pure
def names_equal(a: List[int], b: List[int]) -> bool:
    """Whether two index names denote the same string."""
    Requires(Acc(list_pred(a), 1 / 4) and Acc(list_pred(b), 1 / 4))
    return ToSeq(a) == ToSeq(b)


@Pure
def base_combine(self_elidable: bool, op_elidable: bool) -> int:
    """The generic combination rule shared by every operation: a self-elidable
    operation is replaced by the counterpart alone (2); otherwise an elidable
    counterpart replaces the operation by the operation alone (3); otherwise the
    operations cannot be combined (0)."""
    if self_elidable:
        return 2
    if op_elidable:
        return 3
    return 0
# pure-end


def reduce_add_index(index_name: List[int], self_elidable: bool, operation: Operand) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(index_name), 1 / 2))
    Requires(Acc(operation.is_remove_index, 1 / 2))
    Requires(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
    Requires(Acc(operation.elidable, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(index_name), 1 / 2))
    Ensures(Acc(operation.is_remove_index, 1 / 2))
    Ensures(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
    Ensures(Acc(operation.elidable, 1 / 2))
    # The discriminating guarantee: an index-removal of the same name cancels
    # the add to the empty list (tag 1).
    Ensures(Implies(operation.is_remove_index and names_equal(index_name, operation.name),
                    Result() == 1))
    # Otherwise the outcome is exactly the generic combination rule.
    Ensures(Implies(not (operation.is_remove_index and names_equal(index_name, operation.name)),
                    Result() == base_combine(self_elidable, operation.elidable)))
    # The outcome is always one of the four legal tags.
    Ensures(Result() == 0 or Result() == 1 or Result() == 2 or Result() == 3)
    # post-conditions-end
    # impl-start
    if operation.is_remove_index and names_equal(index_name, operation.name):
        return 1
    if self_elidable:
        return 2
    if operation.elidable:
        return 3
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec for reduce_add_index is a TOTAL functional specification with zero slack: (clause1) is_remove_index & names_equal => Result==1; (clause2) otherwise => Result==base_combine(self_elidable, operation.elidable); (clause3) Result in {0,1,2,3}. base_combine is a @Pure helper in the frozen `pure` region (part of the spec signature — confirmed: a probe altering its tag values is flagged DIFFERENT by same-spec), so it computes a fixed value; every input therefore maps to exactly one legal Result. No verifying-wrong-impl exists, hence no faithful patch to materialize/resolve.

Attacks (all SAME-spec by construction; edited impl region only; `python -m swebench_unified.adversary weakness nagini django__django-16819 <path>`):
- positive_control.py: correct impl -> weakness exit 0 CANDIDATE (verifies in ~13.3s), as expected.
- atk_1.py PREPATCH BUG (no cancel branch, always defers to base rule) -> exit 2, verification failed. Prepatch bug reproduced: spec rejects the pre-patch behaviour (fails clause1 on matching RemoveIndex non-elidable, returns 0 not 1).
- atk_2.py partial-domain (cancel branch returns tag 0 not 1) -> exit 2, rejected.
- atk_3.py control-flow-effect (self_elidable checked BEFORE cancel branch) -> exit 2, rejected (violates clause1 when cancel case is also self_elidable).
- atk_4.py ungrounded-oracle echo (drop is_remove_index guard, cancel on any equal name) -> exit 2, rejected (over-cancels for non-removal counterpart).
- atk_5.py swapped base tags (self_elidable->3, op_elidable->2) -> exit 2, rejected (violates clause2 vs base_combine).
- atk_6.py boundary (drop names_equal check, cancel any RemoveIndex) -> exit 2, rejected.
- atk_7.py off-by fall-through (0 replaced by 3) -> exit 2, rejected.
7 distinct wrong impls, all same-spec, NONE verifies; only the correct impl verifies. No CANDIDATE counterexample => no patch needed resolve-running (nothing to break the spec).

Refinement/A-leg audit: NO axioms in this bundle (axioms region is comment-only; grep ContractOnly in model.py = NONE). The only callee super().reduce == Operation.reduce (base.py:129-139) is modeled DEEPLY as the @Pure base_combine (refinement.md step A6), not axiomatized — no kind-3 legs; every leg R / I / deep-model. axiom_check.py (exit 0) confirms the deep-model<->real-callee correspondence: base_combine == Operation.reduce on all 4 cases, reduce_add_index == gold AddIndex.reduce on 392 boundary + 50000 fuzz inputs, F2P cancellation witness holds. mapping.md MRO (AddIndex->IndexOperation->Operation, IndexOperation has no reduce override) is correct. No axiom-soundness trust point.

Commands used (project root; SBU_BENCHMARK_DIR already set; python python):
  same-spec nagini django__django-16819 <atk> -> exit 0 (SAME) for all 8 files
  weakness nagini django__django-16819 <atk> -> positive_control exit 0; atk_1..7 exit 2
  axiom_check.py -> exit 0

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break analysis of the modeled function reduce_add_index vs. the real repo callee AddIndex.reduce (django/db/migrations/operations/models.py, added by gold patch) at base_commit 0b0998dc151feb77068e2387c34cc50ef6b356ae.

Real semantics (confirmed against source):
  AddIndex.reduce: if isinstance(operation, RemoveIndex) and self.index.name == operation.name: return []; else return super().reduce(operation, app_label)
  super() resolves to Operation.reduce (base.py:129) since IndexOperation (models.py:803) defines NO reduce override — MRO AddIndex->IndexOperation->Operation confirmed. Operation.reduce: if self.elidable: return [operation]; elif operation.elidable: return [self]; return False. elidable defaults False (base.py:32).

Model: reduce_add_index returns tag 1 when operation.is_remove_index and names_equal(index_name, operation.name); else base_combine(self_elidable, operation.elidable) which is 2 if self_elidable, 3 if op_elidable, else 0. Tag encoding []=1, [operation]=2, [self]=3, False=0 (mapping.md §2), matching optimizer.py's list-vs-False handling.

Verification performed:
1. Exhaustive standalone replication of the exact gold reduce + base reduce over ALL combinations of {index_name, op_name} in {equal, unequal, empty}, self_elidable in {F,T}, op_elidable in {F,T}, and counterpart type in {RemoveIndex, non-RemoveIndex}. Model tag == real encoded outcome on EVERY case; zero mismatches. Notably the cancellation branch correctly takes priority over the elidable branches (matching real short-circuit control flow), and the isinstance/is_remove_index guard short-circuits name comparison exactly as Python's `and`.
2. Short-circuit fidelity: model consults operation.name only under is_remove_index guard, matching the real `isinstance(...) and self.index.name == operation.name`.
3. str<->List[int] (ToSeq) refinement is a faithful bijection of string equality; no drift.
4. same-spec toolkit confirms spec region byte-identical (SAME, exit 0). Bundle model verifies (nagini_verify.sh exit 0, 11.36s).

No axiom present (super().reduce is the function's own base-class logic, modelled deeply as base_combine; refinement.md/mapping.md correctly document no @ContractOnly axiom). No opaque callee to be over-modeled. The spec is neither too strong nor drifting: it agrees with the real callee on every reachable input. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified byte-identical to the recorded spec_view region (sha256 d0e31a05e99fba7f4e59b725ffdffa11bd0a7da6ef4eee7b4fb8ce0c37ee3d70); impl region correctly elided ('...  # implementation elided — supplied by the consumer').

Public problem_statement: 'Reduce Add/RemoveIndex migration operations. We should reduce AddIndex/RemoveIndex operations when optimizing migration operations.' — already names AddIndex, RemoveIndex, and the reduce/optimize concept.

Gold edit: new AddIndex.reduce — `if isinstance(operation, RemoveIndex) and self.index.name == operation.name: return []; return super().reduce(operation, app_label)`.

The spec view discloses only the desired BEHAVIOUR: (1) add-index against a same-named remove-index cancels to the empty operation list (tag 1) — exactly the reduction the issue asks for and the natural add-then-remove-same-index no-op derivable by any engineer from the problem statement; (2) otherwise fall back to the generic base combination rule (self_elidable->2, op_elidable->3, else 0), which is the UNCHANGED base-class default, not new gold-edit-specific code.

Crucially the spec view discloses NO gold-edit mechanics beyond the problem statement: it never names the reduce() method, super().reduce, isinstance, app_label, nor the AddIndex/RemoveIndex/IndexOperation class structure, nor that a new method must be added to a specific class. It is an abstract model (reduce_add_index over an Operand with boolean facets and a 4-tag integer encoding), not a transcription of the gold code. The gold patch verbatim appears only in refinement.md/mapping.md — auditor/reviewer artifacts, NOT part of the consumer spec view (which is model.py projected via markers.spec_view). No spec-view line reconstructs the gold edit beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
