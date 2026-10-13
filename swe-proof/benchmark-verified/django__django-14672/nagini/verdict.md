# P2 adversarial audit — django__django-14672

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,11 +53,6 @@
 
     def __init__(self, kind: int, items: PSeq[int]) -> None:
         Requires(0 <= kind and kind <= 2)
-        # Loop-free constructor: two field stores, no call, no recursion. Level 2
-        # so an obligated caller (level 6) has strict room above it and can hand
-        # its unsatisfied obligation down (Nagini's leak check demands
-        # caller-level > callee-level).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)
         Ensures(Acc(self.items) and self.items == items)
         self.kind = kind  # type: int
@@ -101,7 +95,6 @@
     # The name collection is read-only (directive 5): canonicalisation copies
     # it, it is not mutated.
     Requires(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
@@ -118,5 +111,5 @@
     empty = []  # type: List[int]
     if names is None:
         return Value(KIND_ABSENT, ToSeq(empty))
-    return Value(KIND_IMMUTABLE, ToSeq(names))
+    return Value(KIND_MUTABLE, ToSeq(names))
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,11 +53,6 @@
 
     def __init__(self, kind: int, items: PSeq[int]) -> None:
         Requires(0 <= kind and kind <= 2)
-        # Loop-free constructor: two field stores, no call, no recursion. Level 2
-        # so an obligated caller (level 6) has strict room above it and can hand
-        # its unsatisfied obligation down (Nagini's leak check demands
-        # caller-level > callee-level).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)
         Ensures(Acc(self.items) and self.items == items)
         self.kind = kind  # type: int
@@ -101,7 +95,6 @@
     # The name collection is read-only (directive 5): canonicalisation copies
     # it, it is not mutated.
     Requires(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
@@ -116,7 +109,5 @@
     # post-conditions-end
     # impl-start
     empty = []  # type: List[int]
-    if names is None:
-        return Value(KIND_ABSENT, ToSeq(empty))
-    return Value(KIND_IMMUTABLE, ToSeq(names))
+    return Value(KIND_ABSENT, ToSeq(empty))
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,11 +53,6 @@
 
     def __init__(self, kind: int, items: PSeq[int]) -> None:
         Requires(0 <= kind and kind <= 2)
-        # Loop-free constructor: two field stores, no call, no recursion. Level 2
-        # so an obligated caller (level 6) has strict room above it and can hand
-        # its unsatisfied obligation down (Nagini's leak check demands
-        # caller-level > callee-level).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)
         Ensures(Acc(self.items) and self.items == items)
         self.kind = kind  # type: int
@@ -101,7 +95,6 @@
     # The name collection is read-only (directive 5): canonicalisation copies
     # it, it is not mutated.
     Requires(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
@@ -118,5 +111,5 @@
     empty = []  # type: List[int]
     if names is None:
         return Value(KIND_ABSENT, ToSeq(empty))
-    return Value(KIND_IMMUTABLE, ToSeq(names))
+    return Value(KIND_IMMUTABLE, ToSeq(empty))
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,11 +53,6 @@
 
     def __init__(self, kind: int, items: PSeq[int]) -> None:
         Requires(0 <= kind and kind <= 2)
-        # Loop-free constructor: two field stores, no call, no recursion. Level 2
-        # so an obligated caller (level 6) has strict room above it and can hand
-        # its unsatisfied obligation down (Nagini's leak check demands
-        # caller-level > callee-level).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)
         Ensures(Acc(self.items) and self.items == items)
         self.kind = kind  # type: int
@@ -101,7 +95,6 @@
     # The name collection is read-only (directive 5): canonicalisation copies
     # it, it is not mutated.
     Requires(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
@@ -117,6 +110,6 @@
     # impl-start
     empty = []  # type: List[int]
     if names is None:
-        return Value(KIND_ABSENT, ToSeq(empty))
-    return Value(KIND_IMMUTABLE, ToSeq(names))
+        return Value(KIND_IMMUTABLE, ToSeq(empty))
+    return Value(KIND_ABSENT, ToSeq(names))
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,11 +53,6 @@
 
     def __init__(self, kind: int, items: PSeq[int]) -> None:
         Requires(0 <= kind and kind <= 2)
-        # Loop-free constructor: two field stores, no call, no recursion. Level 2
-        # so an obligated caller (level 6) has strict room above it and can hand
-        # its unsatisfied obligation down (Nagini's leak check demands
-        # caller-level > callee-level).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)
         Ensures(Acc(self.items) and self.items == items)
         self.kind = kind  # type: int
@@ -101,7 +95,6 @@
     # The name collection is read-only (directive 5): canonicalisation copies
     # it, it is not mutated.
     Requires(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
@@ -118,5 +111,5 @@
     empty = []  # type: List[int]
     if names is None:
         return Value(KIND_ABSENT, ToSeq(empty))
-    return Value(KIND_IMMUTABLE, ToSeq(names))
+    return Value(KIND_ABSENT, ToSeq(names))
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,11 +53,6 @@
 
     def __init__(self, kind: int, items: PSeq[int]) -> None:
         Requires(0 <= kind and kind <= 2)
-        # Loop-free constructor: two field stores, no call, no recursion. Level 2
-        # so an obligated caller (level 6) has strict room above it and can hand
-        # its unsatisfied obligation down (Nagini's leak check demands
-        # caller-level > callee-level).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)
         Ensures(Acc(self.items) and self.items == items)
         self.kind = kind  # type: int
@@ -101,7 +95,6 @@
     # The name collection is read-only (directive 5): canonicalisation copies
     # it, it is not mutated.
     Requires(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
@@ -118,5 +111,5 @@
     empty = []  # type: List[int]
     if names is None:
         return Value(KIND_ABSENT, ToSeq(empty))
-    return Value(KIND_IMMUTABLE, ToSeq(names))
+    return Value(KIND_IMMUTABLE, ToSeq(names).drop(1))
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -54,11 +53,6 @@
 
     def __init__(self, kind: int, items: PSeq[int]) -> None:
         Requires(0 <= kind and kind <= 2)
-        # Loop-free constructor: two field stores, no call, no recursion. Level 2
-        # so an obligated caller (level 6) has strict room above it and can hand
-        # its unsatisfied obligation down (Nagini's leak check demands
-        # caller-level > callee-level).
-        Requires(MustTerminate(2))
         Ensures(Acc(self.kind) and self.kind == kind)
         Ensures(Acc(self.items) and self.items == items)
         self.kind = kind  # type: int
@@ -101,7 +95,6 @@
     # The name collection is read-only (directive 5): canonicalisation copies
     # it, it is not mutated.
     Requires(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
@@ -117,6 +110,6 @@
     # impl-start
     empty = []  # type: List[int]
     if names is None:
-        return Value(KIND_ABSENT, ToSeq(empty))
-    return Value(KIND_IMMUTABLE, ToSeq(names))
+        return Value(KIND_ABSENT, ToSeq(empty).take(0))
+    return Value(KIND_IMMUTABLE, ToSeq(names).take(len(names)))
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14672.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A reverse many-to-many relation derives an identity from which it computes a
  hash, so two relations that are equal by identity hash equally and a single
  relation can be placed in a hash-based container. One component carried in
  that identity is an optional, user-supplied collection of intermediate field
  names. That collection may be an ordinary mutable sequence (which is NOT
  hashable). For the identity to be usable as a hash key, EVERY component it
  carries must be hashable; therefore this component must be reduced to a
  hashable, order-preserving canonical form before it enters the identity:

    * an absent collection contributes an absent, hashable value unchanged;
    * a present sequence of names contributes the same names, in the same
      order, in an immutable (hashable) form.

  Two relations whose name collections are element-wise equal therefore yield
  equal canonical components (and hence equal identities and equal hashes).

A runtime value is modelled by a tagged carrier `Value` recording its kind
(absent / mutable-sequence / immutable-sequence) and its element sequence; a
mutable sequence is the only kind that is not hashable. Names are modelled as
`int` atoms and the name collection as `List[int]` (Nagini bans `str`
indexing); the element ordering is carried by the pure sequence theory
`PSeq[int]`.

The canonicalisation of one component is modelled deeply over `Value`; its
agreement with the real canonicaliser is checked out-of-band by axiom_check.py
(G-AX), not consumed as an axiom. Markers (machine-parsed) delimit the spec /
proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
# Carrier kinds. A mutable sequence (KIND_MUTABLE) is the only one that is not
# hashable; an absent value and an immutable sequence are both hashable.
KIND_ABSENT = 0    # None
KIND_MUTABLE = 1   # a Python list
KIND_IMMUTABLE = 2  # a Python tuple


class Value:
    """A minimal model of a runtime value as it enters the identity: a kind tag
    (faithfully reflecting the value's runtime type) plus its element sequence
    (empty when absent)."""

    def __init__(self, kind: int, items: PSeq[int]) -> None:
        Requires(0 <= kind and kind <= 2)
        Ensures(Acc(self.kind) and self.kind == kind)
        Ensures(Acc(self.items) and self.items == items)
        self.kind = kind  # type: int
        self.items = items  # type: PSeq[int]


@Pure
def is_hashable(v: Value) -> bool:
    """Whether a value may participate in a hash. A mutable sequence is not
    hashable; an absent value and an immutable sequence are."""
    Requires(Acc(v.kind, 1 / 4))
    return v.kind != KIND_MUTABLE


@Pure
def canonical_names(names: Optional[List[int]]) -> int:
    """The KIND the name collection contributes to the identity after
    canonicalisation: absent stays absent; any present sequence becomes the
    immutable form."""
    Requires(Implies(names is not None, Acc(list_pred(names), 1 / 4)))
    if names is None:
        return KIND_ABSENT
    return KIND_IMMUTABLE


@Pure
def canonical_items(names: Optional[List[int]]) -> PSeq[int]:
    """The element sequence the name collection contributes after
    canonicalisation: order-preserving, identical to the input names (empty
    when absent)."""
    Requires(Implies(names is not None, Acc(list_pred(names), 1 / 4)))
    if names is None:
        return PSeq(0).take(0)
    return ToSeq(names)
# pure-end


def identity_name_component(names: Optional[List[int]]) -> Value:
    # pre-conditions-start
    # The name collection is read-only (directive 5): canonicalisation copies
    # it, it is not mutated.
    Requires(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
    Ensures(Acc(Result().kind) and Acc(Result().items))
    # The component that enters the identity must be hashable, so the identity
    # itself is hashable and the relation can be used as a hash key.
    Ensures(is_hashable(Result()))
    # It preserves the names, in order (absent stays absent): equal collections
    # produce equal components, hence equal identities and equal hashes.
    Ensures(Result().kind == canonical_names(names))
    Ensures(Result().items == canonical_items(names))
    # post-conditions-end
    # impl-start
    empty = []  # type: List[int]
    if names is None:
        return Value(KIND_ABSENT, ToSeq(empty))
    return Value(KIND_IMMUTABLE, ToSeq(names))
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-14672 (nagini).

SPEC SHAPE: identity_name_component postconditions FULLY PIN the output -- Result().kind == canonical_names(names) (ABSENT if None else IMMUTABLE); Result().items == canonical_items(names) (empty if None else ToSeq(names)); is_hashable(Result()). Output-determining, so genuinely wrong impls must fail verification.

EDIT DISCIPLINE: every attack copies gold model.py; only the impl region (lines 111-114) edited; axioms/@Pure/Requires/Ensures byte-identical (verified by diff of lines 1-110 vs pos_control).

### Results
- pos_control.py (gold): CANDIDATE, verifies 14.6s (exit 0). Positive control OK.
- atk_1.py PREPATCH (present names -> Value(KIND_MUTABLE)): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). => prepatch bug reproduced; spec's is_hashable(Result()) rejects the raw-mutable-list identity slot (models TypeError: unhashable type 'list').
- atk_2.py partial-domain (always Value(KIND_ABSENT, empty), ignores present names): rejected (exit 2).
- atk_3.py boundary (present -> KIND_IMMUTABLE but empty items): rejected (exit 2).
- atk_4.py control-flow swap (IMMUTABLE for None, ABSENT for present): rejected (exit 2).
- atk_5.py ungrounded kind (present names carried as KIND_ABSENT): rejected (exit 2).
- atk_6.py order-mangle (ToSeq(names).drop(1) drops first name): rejected (exit 2).
- atk_7.py EQUIVALENT ECHO (ToSeq(names).take(len(names)), a semantic no-op): CANDIDATE, verifies 14.1s (exit 0).

CANDIDATE HANDLING (mandatory resolve): atk_7 is the only non-gold verifying impl. It produces the identical canonical form (KIND_IMMUTABLE, same names, same order, hashable) as gold, so its faithful refined real patch IS make_hashable(self.through_fields) == the gold patch. Materialized as atk_7_patch.diff and RUN through the official harness: `swebench_unified.harness.run_resolve('django__django-14672', patch)` => RESOLVED: True, COMPLETED: True, note='resolved', attempts=1, flaky=False. So verify does NOT imply an unresolving patch here -- spec is not too weak.

A-LEG / refinement.md AUDIT: axioms region empty => NO A-consumed leg. The one genuinely-changed op (wrapping through_fields with make_hashable) is modeled DEEPLY (canonical_names/canonical_items/is_hashable over Value) as an A-reference, validated == real callee by G-AX -- NOT hidden behind a consumed axiom, so NO kind-3 leg. Legs: A1=R (Optional[list of str] <-> Optional[List[int]]); A2=A-reference (make_hashable(None)->None); A3=A-reference (make_hashable(list)->tuple, same names/order); A4=R/I (unchanged tuple concat + neighbors). A-reference correspondence independently reproduced (standalone make_hashable + is_iterable) on boundary set {None, [], ['event','invitee'], ['a'], ['dup','dup'], ('event','invitee'), ()}: result always hashable, kind matches (None->ABSENT, list->IMMUTABLE), element sequence order-preserved, and raw non-empty list unhashable (prepatch defect) -- all hold. meta.json gates: G-AX pass, G-EQ pass, G-RESOLVE pass, all panels pass.

VERDICT: SOUND. 6 distinct wrong impls (+prepatch) all rejected by the output-pinning spec; the single non-gold verifying candidate is a true semantic equivalent whose materialized faithful patch RESOLVED under the official harness (executed, not speculated). No verify-but-not-correct impl found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14672.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A reverse many-to-many relation derives an identity from which it computes a
  hash, so two relations that are equal by identity hash equally and a single
  relation can be placed in a hash-based container. One component carried in
  that identity is an optional, user-supplied collection of intermediate field
  names. That collection may be an ordinary mutable sequence (which is NOT
  hashable). For the identity to be usable as a hash key, EVERY component it
  carries must be hashable; therefore this component must be reduced to a
  hashable, order-preserving canonical form before it enters the identity:

    * an absent collection contributes an absent, hashable value unchanged;
    * a present sequence of names contributes the same names, in the same
      order, in an immutable (hashable) form.

  Two relations whose name collections are element-wise equal therefore yield
  equal canonical components (and hence equal identities and equal hashes).

A runtime value is modelled by a tagged carrier `Value` recording its kind
(absent / mutable-sequence / immutable-sequence) and its element sequence; a
mutable sequence is the only kind that is not hashable. Names are modelled as
`int` atoms and the name collection as `List[int]` (Nagini bans `str`
indexing); the element ordering is carried by the pure sequence theory
`PSeq[int]`.

The canonicalisation of one component is modelled deeply over `Value`; its
agreement with the real canonicaliser is checked out-of-band by axiom_check.py
(G-AX), not consumed as an axiom. Markers (machine-parsed) delimit the spec /
proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
# Carrier kinds. A mutable sequence (KIND_MUTABLE) is the only one that is not
# hashable; an absent value and an immutable sequence are both hashable.
KIND_ABSENT = 0    # None
KIND_MUTABLE = 1   # a Python list
KIND_IMMUTABLE = 2  # a Python tuple


class Value:
    """A minimal model of a runtime value as it enters the identity: a kind tag
    (faithfully reflecting the value's runtime type) plus its element sequence
    (empty when absent)."""

    def __init__(self, kind: int, items: PSeq[int]) -> None:
        Requires(0 <= kind and kind <= 2)
        Ensures(Acc(self.kind) and self.kind == kind)
        Ensures(Acc(self.items) and self.items == items)
        self.kind = kind  # type: int
        self.items = items  # type: PSeq[int]


@Pure
def is_hashable(v: Value) -> bool:
    """Whether a value may participate in a hash. A mutable sequence is not
    hashable; an absent value and an immutable sequence are."""
    Requires(Acc(v.kind, 1 / 4))
    return v.kind != KIND_MUTABLE


@Pure
def canonical_names(names: Optional[List[int]]) -> int:
    """The KIND the name collection contributes to the identity after
    canonicalisation: absent stays absent; any present sequence becomes the
    immutable form."""
    Requires(Implies(names is not None, Acc(list_pred(names), 1 / 4)))
    if names is None:
        return KIND_ABSENT
    return KIND_IMMUTABLE


@Pure
def canonical_items(names: Optional[List[int]]) -> PSeq[int]:
    """The element sequence the name collection contributes after
    canonicalisation: order-preserving, identical to the input names (empty
    when absent)."""
    Requires(Implies(names is not None, Acc(list_pred(names), 1 / 4)))
    if names is None:
        return PSeq(0).take(0)
    return ToSeq(names)
# pure-end


def identity_name_component(names: Optional[List[int]]) -> Value:
    # pre-conditions-start
    # The name collection is read-only (directive 5): canonicalisation copies
    # it, it is not mutated.
    Requires(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(names is not None, Acc(list_pred(names), 1 / 2)))
    Ensures(Acc(Result().kind) and Acc(Result().items))
    # The component that enters the identity must be hashable, so the identity
    # itself is hashable and the relation can be used as a hash key.
    Ensures(is_hashable(Result()))
    # It preserves the names, in order (absent stays absent): equal collections
    # produce equal components, hence equal identities and equal hashes.
    Ensures(Result().kind == canonical_names(names))
    Ensures(Result().items == canonical_items(names))
    # post-conditions-end
    # impl-start
    empty = []  # type: List[int]
    if names is None:
        return Value(KIND_ABSENT, ToSeq(empty))
    return Value(KIND_IMMUTABLE, ToSeq(names))
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-14672 (nagini).

SPEC SHAPE: identity_name_component postconditions FULLY PIN the output -- Result().kind == canonical_names(names) (ABSENT if None else IMMUTABLE); Result().items == canonical_items(names) (empty if None else ToSeq(names)); is_hashable(Result()). Output-determining, so genuinely wrong impls must fail verification.

EDIT DISCIPLINE: every attack copies gold model.py; only the impl region (lines 111-114) edited; axioms/@Pure/Requires/Ensures byte-identical (verified by diff of lines 1-110 vs pos_control).

### Results
- pos_control.py (gold): CANDIDATE, verifies 14.6s (exit 0). Positive control OK.
- atk_1.py PREPATCH (present names -> Value(KIND_MUTABLE)): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). => prepatch bug reproduced; spec's is_hashable(Result()) rejects the raw-mutable-list identity slot (models TypeError: unhashable type 'list').
- atk_2.py partial-domain (always Value(KIND_ABSENT, empty), ignores present names): rejected (exit 2).
- atk_3.py boundary (present -> KIND_IMMUTABLE but empty items): rejected (exit 2).
- atk_4.py control-flow swap (IMMUTABLE for None, ABSENT for present): rejected (exit 2).
- atk_5.py ungrounded kind (present names carried as KIND_ABSENT): rejected (exit 2).
- atk_6.py order-mangle (ToSeq(names).drop(1) drops first name): rejected (exit 2).
- atk_7.py EQUIVALENT ECHO (ToSeq(names).take(len(names)), a semantic no-op): CANDIDATE, verifies 14.1s (exit 0).

CANDIDATE HANDLING (mandatory resolve): atk_7 is the only non-gold verifying impl. It produces the identical canonical form (KIND_IMMUTABLE, same names, same order, hashable) as gold, so its faithful refined real patch IS make_hashable(self.through_fields) == the gold patch. Materialized as atk_7_patch.diff and RUN through the official harness: `swebench_unified.harness.run_resolve('django__django-14672', patch)` => RESOLVED: True, COMPLETED: True, note='resolved', attempts=1, flaky=False. So verify does NOT imply an unresolving patch here -- spec is not too weak.

A-LEG / refinement.md AUDIT: axioms region empty => NO A-consumed leg. The one genuinely-changed op (wrapping through_fields with make_hashable) is modeled DEEPLY (canonical_names/canonical_items/is_hashable over Value) as an A-reference, validated == real callee by G-AX -- NOT hidden behind a consumed axiom, so NO kind-3 leg. Legs: A1=R (Optional[list of str] <-> Optional[List[int]]); A2=A-reference (make_hashable(None)->None); A3=A-reference (make_hashable(list)->tuple, same names/order); A4=R/I (unchanged tuple concat + neighbors). A-reference correspondence independently reproduced (standalone make_hashable + is_iterable) on boundary set {None, [], ['event','invitee'], ['a'], ['dup','dup'], ('event','invitee'), ()}: result always hashable, kind matches (None->ABSENT, list->IMMUTABLE), element sequence order-preserved, and raw non-empty list unhashable (prepatch defect) -- all hold. meta.json gates: G-AX pass, G-EQ pass, G-RESOLVE pass, all panels pass.

VERDICT: SOUND. 6 distinct wrong impls (+prepatch) all rejected by the output-pinning spec; the single non-gold verifying candidate is a true semantic equivalent whose materialized faithful patch RESOLVED under the official harness (executed, not speculated). No verify-but-not-correct impl found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / model-vs-real disagreement) check for django__django-14672 nagini bundle. All checks re-run independently against the real repo at base_commit 00ea883ef5 (fresh worktree).

FACTS: (1) same-spec exit 0 — bundle model shares the exact frozen spec; spec region byte-identical. (2) nagini_verify on bundle model.py: 'Verification successful' (14.3s, exit 0). (3) axiom_check.py (G-AX) executed against the REAL django.utils.hashable.make_hashable at base_commit: passes on 11 boundary + 20000 fuzz through-fields inputs — result always hashable, kind/element-sequence match the deep model, raw list unhashable. (4) conformance_check.py (G-CONF) against the gold-patched real ManyToManyRel.identity: 100013 inputs, 0 disagreements. (5) My own independent model-vs-real probe on tricky domain inputs (None, [], (), tuples, unicode, 500-char names, 50-element lists, duplicates, empty strings, reordered, single-char): 0/13 divergences.

ANALYSIS: The modeled callee is the through-fields identity slot = make_hashable(self.through_fields). Its real input domain is None or a list/tuple of field-name strings. On this entire domain real make_hashable: None->None (hashable, ABSENT); list/tuple of strings -> a hashable tuple of the same names in the same order (each str already hashable, left untouched -> IMMUTABLE). The deep model (canonical_names: None->KIND_ABSENT else KIND_IMMUTABLE; canonical_items: identity on element sequence, empty for None; is_hashable: kind!=KIND_MUTABLE) matches exactly. The int-atom abstraction of name strings is sound because make_hashable leaves already-hashable atoms untouched, matching the model's identity-on-elements. Every postcondition (is_hashable(Result()), kind==canonical_names, items==canonical_items) holds under the real callee. No diverging input exists; the spec does not overstate real repo behavior. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit is `make_hashable(self.through_fields)` in `ManyToManyRel.identity` (reverse_related.py). The PUBLIC problem_statement already discloses the entire fix in full: it names the file (django/db/models/fields/reverse_related.py, __hash__ -> hash(self.identity)), the exact failure mode (TypeError: unhashable type: 'list'), the mechanism (identity is a tuple whose components must be hashable via make_hashable), and closes with the explicit sentence 'Solution: Add missing make_hashable call on self.through_fields in ManyToManyRel.' Everything the spec view (model.py) conveys — that an optional user-supplied collection of field names must be reduced to a hashable, order-preserving canonical form before entering the relation's identity so the identity can be hashed — is a strict subset of what the public problem_statement already states. model.py abstracts the fix (Value carrier, canonical_names/canonical_items, is_hashable) and never quotes anything beyond the public text; it does not name make_hashable, reverse_related.py, or ManyToManyRel. refinement.md/mapping.md do quote the gold hunk and callee, but they are the audit-side derivation/reference artifacts, not the solver-facing spec view; and even they reveal nothing beyond the public statement. Since the public problem_statement fully contains the gold edit, the spec view cannot leak it BEYOND the public text. No line in the spec view leaks.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
