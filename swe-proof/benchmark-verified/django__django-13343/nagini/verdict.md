# P2 adversarial audit — django__django-13343

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,10 +60,6 @@
 
 class AttachmentField:
     def __init__(self) -> None:
-        # Level 1: the constructor is a leaf obligated method (it calls nothing
-        # obligated), so it sits strictly below every method that builds a
-        # field. Obligated callers must outrank it or the construction leaks.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.store))            # type: ignore
         Ensures(Acc(self.has_producer))     # type: ignore
         Ensures(Acc(self.producer_id))      # type: ignore
@@ -87,7 +82,6 @@
     # must respect), and which is itself a real store, not the default.
     Requires(Implies(given_is_producer,
                      evaluated != given and evaluated != default_store_id()))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store))
@@ -125,7 +119,6 @@
     Requires(Acc(field.store, 1 / 2))
     Requires(Acc(field.has_producer, 1 / 2))
     Requires(Acc(field.producer_id, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store, 1 / 2))
@@ -145,7 +138,5 @@
     # impl-start
     if field.store == default_store_id():
         return None
-    if field.has_producer:
-        return field.producer_id
     return field.store
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,10 +60,6 @@
 
 class AttachmentField:
     def __init__(self) -> None:
-        # Level 1: the constructor is a leaf obligated method (it calls nothing
-        # obligated), so it sits strictly below every method that builds a
-        # field. Obligated callers must outrank it or the construction leaks.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.store))            # type: ignore
         Ensures(Acc(self.has_producer))     # type: ignore
         Ensures(Acc(self.producer_id))      # type: ignore
@@ -87,7 +82,6 @@
     # must respect), and which is itself a real store, not the default.
     Requires(Implies(given_is_producer,
                      evaluated != given and evaluated != default_store_id()))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store))
@@ -108,14 +102,9 @@
     # post-conditions-end
     # impl-start
     field.store = given
+    field.has_producer = False
     if given_is_producer:
-        # Record a reference to the original producer, then adopt the concrete
-        # store it yields as the live store.
-        field.has_producer = True
-        field.producer_id = given
         field.store = evaluated
-    else:
-        field.has_producer = False
     # impl-end
 
 
@@ -125,7 +114,6 @@
     Requires(Acc(field.store, 1 / 2))
     Requires(Acc(field.has_producer, 1 / 2))
     Requires(Acc(field.producer_id, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store, 1 / 2))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,10 +60,6 @@
 
 class AttachmentField:
     def __init__(self) -> None:
-        # Level 1: the constructor is a leaf obligated method (it calls nothing
-        # obligated), so it sits strictly below every method that builds a
-        # field. Obligated callers must outrank it or the construction leaks.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.store))            # type: ignore
         Ensures(Acc(self.has_producer))     # type: ignore
         Ensures(Acc(self.producer_id))      # type: ignore
@@ -87,7 +82,6 @@
     # must respect), and which is itself a real store, not the default.
     Requires(Implies(given_is_producer,
                      evaluated != given and evaluated != default_store_id()))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store))
@@ -109,10 +103,8 @@
     # impl-start
     field.store = given
     if given_is_producer:
-        # Record a reference to the original producer, then adopt the concrete
-        # store it yields as the live store.
         field.has_producer = True
-        field.producer_id = given
+        field.producer_id = evaluated
         field.store = evaluated
     else:
         field.has_producer = False
@@ -125,7 +117,6 @@
     Requires(Acc(field.store, 1 / 2))
     Requires(Acc(field.has_producer, 1 / 2))
     Requires(Acc(field.producer_id, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store, 1 / 2))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,10 +60,6 @@
 
 class AttachmentField:
     def __init__(self) -> None:
-        # Level 1: the constructor is a leaf obligated method (it calls nothing
-        # obligated), so it sits strictly below every method that builds a
-        # field. Obligated callers must outrank it or the construction leaks.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.store))            # type: ignore
         Ensures(Acc(self.has_producer))     # type: ignore
         Ensures(Acc(self.producer_id))      # type: ignore
@@ -87,7 +82,6 @@
     # must respect), and which is itself a real store, not the default.
     Requires(Implies(given_is_producer,
                      evaluated != given and evaluated != default_store_id()))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store))
@@ -125,7 +119,6 @@
     Requires(Acc(field.store, 1 / 2))
     Requires(Acc(field.has_producer, 1 / 2))
     Requires(Acc(field.producer_id, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store, 1 / 2))
@@ -146,6 +139,6 @@
     if field.store == default_store_id():
         return None
     if field.has_producer:
-        return field.producer_id
-    return field.store
+        return field.store
+    return field.producer_id
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,10 +60,6 @@
 
 class AttachmentField:
     def __init__(self) -> None:
-        # Level 1: the constructor is a leaf obligated method (it calls nothing
-        # obligated), so it sits strictly below every method that builds a
-        # field. Obligated callers must outrank it or the construction leaks.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.store))            # type: ignore
         Ensures(Acc(self.has_producer))     # type: ignore
         Ensures(Acc(self.producer_id))      # type: ignore
@@ -87,7 +82,6 @@
     # must respect), and which is itself a real store, not the default.
     Requires(Implies(given_is_producer,
                      evaluated != given and evaluated != default_store_id()))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store))
@@ -109,13 +103,12 @@
     # impl-start
     field.store = given
     if given_is_producer:
-        # Record a reference to the original producer, then adopt the concrete
-        # store it yields as the live store.
         field.has_producer = True
         field.producer_id = given
         field.store = evaluated
     else:
         field.has_producer = False
+        field.producer_id = given
     # impl-end
 
 
@@ -125,7 +118,6 @@
     Requires(Acc(field.store, 1 / 2))
     Requires(Acc(field.has_producer, 1 / 2))
     Requires(Acc(field.producer_id, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store, 1 / 2))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,10 +60,6 @@
 
 class AttachmentField:
     def __init__(self) -> None:
-        # Level 1: the constructor is a leaf obligated method (it calls nothing
-        # obligated), so it sits strictly below every method that builds a
-        # field. Obligated callers must outrank it or the construction leaks.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.store))            # type: ignore
         Ensures(Acc(self.has_producer))     # type: ignore
         Ensures(Acc(self.producer_id))      # type: ignore
@@ -87,7 +82,6 @@
     # must respect), and which is itself a real store, not the default.
     Requires(Implies(given_is_producer,
                      evaluated != given and evaluated != default_store_id()))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store))
@@ -125,7 +119,6 @@
     Requires(Acc(field.store, 1 / 2))
     Requires(Acc(field.has_producer, 1 / 2))
     Requires(Acc(field.producer_id, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store, 1 / 2))
@@ -145,7 +138,5 @@
     # impl-start
     if field.store == default_store_id():
         return None
-    if field.has_producer:
-        return field.producer_id
-    return field.store
+    return field.producer_id
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,10 +60,6 @@
 
 class AttachmentField:
     def __init__(self) -> None:
-        # Level 1: the constructor is a leaf obligated method (it calls nothing
-        # obligated), so it sits strictly below every method that builds a
-        # field. Obligated callers must outrank it or the construction leaks.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.store))            # type: ignore
         Ensures(Acc(self.has_producer))     # type: ignore
         Ensures(Acc(self.producer_id))      # type: ignore
@@ -87,7 +82,6 @@
     # must respect), and which is itself a real store, not the default.
     Requires(Implies(given_is_producer,
                      evaluated != given and evaluated != default_store_id()))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store))
@@ -125,7 +119,6 @@
     Requires(Acc(field.store, 1 / 2))
     Requires(Acc(field.has_producer, 1 / 2))
     Requires(Acc(field.producer_id, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store, 1 / 2))
@@ -146,6 +139,6 @@
     if field.store == default_store_id():
         return None
     if field.has_producer:
-        return field.producer_id
+        return None
     return field.store
     # impl-end
```

Attack 8 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -61,10 +60,6 @@
 
 class AttachmentField:
     def __init__(self) -> None:
-        # Level 1: the constructor is a leaf obligated method (it calls nothing
-        # obligated), so it sits strictly below every method that builds a
-        # field. Obligated callers must outrank it or the construction leaks.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.store))            # type: ignore
         Ensures(Acc(self.has_producer))     # type: ignore
         Ensures(Acc(self.producer_id))      # type: ignore
@@ -87,7 +82,6 @@
     # must respect), and which is itself a real store, not the default.
     Requires(Implies(given_is_producer,
                      evaluated != given and evaluated != default_store_id()))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store))
@@ -107,14 +101,12 @@
     Ensures(field.store == (evaluated if given_is_producer else given))
     # post-conditions-end
     # impl-start
-    field.store = given
     if given_is_producer:
-        # Record a reference to the original producer, then adopt the concrete
-        # store it yields as the live store.
         field.has_producer = True
         field.producer_id = given
         field.store = evaluated
     else:
+        field.store = given
         field.has_producer = False
     # impl-end
 
@@ -125,7 +117,6 @@
     Requires(Acc(field.store, 1 / 2))
     Requires(Acc(field.has_producer, 1 / 2))
     Requires(Acc(field.producer_id, 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(field.store, 1 / 2))
@@ -143,9 +134,9 @@
                     Result() is not None and Result() == field.store))
     # post-conditions-end
     # impl-start
-    if field.store == default_store_id():
-        return None
-    if field.has_producer:
+    if field.store != default_store_id():
+        if not field.has_producer:
+            return field.store
         return field.producer_id
-    return field.store
+    return None
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13343.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A file-attachment field may be configured with its backing store given
  either directly as a concrete store, or *indirectly* as a zero-argument
  producer that is evaluated once at configuration time to obtain the concrete
  store actually used at runtime. The point of the indirection is that the
  producer — not whatever concrete store it happens to yield — is the stable,
  reconfigurable description of the field.

  Two cooperating operations are specified.

  (1) Configuration. When the field is configured with a producer, the field
      both (a) records a reference to that original producer and (b) adopts the
      concrete store the producer yields as its live store. Evaluating a
      producer yields a concrete store that is a DISTINCT object from the
      producer itself. When configured directly with a concrete store, the
      field adopts it as the live store and records no producer.

  (2) Description (the inverse-of-configuration query that reproduces how the
      field was configured). The store-description it emits must be the value
      ORIGINALLY supplied at configuration: the original producer when one was
      supplied, otherwise the live store. In particular, when a producer was
      supplied the description must NOT be the concrete store the producer was
      evaluated to — that would defeat the indirection, freezing one runtime
      choice into the field's persisted description. When the live store is the
      ambient default store, no store description is emitted at all.

Store objects and producers are modelled by their object identity, carried as
distinct integer ids; the ambient default store has a reserved constant identity.
A producer's evaluation yields a store id distinct from the producer's id
(faithful to evaluating a real producer, which returns a separate store
object). The two operations communicate only through the field's recorded
state. No library callee is involved; the behaviour is pure state/identity
logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the behaviour is pure object-identity / state logic,
# modelled deeply. The identity-preservation of evaluating a real producer and
# of the identity comparison against the ambient default store are validated
# against their real Python semantics out-of-band by axiom_check.py (G-AX) as
# A-references, not consumed here.
# axioms-end


# pure-start
@Pure
def default_store_id() -> int:
    """The reserved identity of the ambient default store."""
    return 0
# pure-end


class AttachmentField:
    def __init__(self) -> None:
        Ensures(Acc(self.store))            # type: ignore
        Ensures(Acc(self.has_producer))     # type: ignore
        Ensures(Acc(self.producer_id))      # type: ignore
        self.store = 0            # type: int   # live concrete store identity
        self.has_producer = False  # type: bool  # whether a producer was recorded
        self.producer_id = 0      # type: int   # recorded original producer id


def configure(field: AttachmentField, given: int, given_is_producer: bool,
              evaluated: int) -> None:
    # pre-conditions-start
    Requires(Acc(field.store))
    Requires(Acc(field.has_producer))
    Requires(Acc(field.producer_id))
    # A concrete store is supplied (the ambient default is reserved id 0; a
    # supplied store/producer carries a non-default identity).
    Requires(given != default_store_id())
    # Evaluating a producer yields a concrete store that is a DISTINCT object
    # from the producer itself (the discriminating fact the description query
    # must respect), and which is itself a real store, not the default.
    Requires(Implies(given_is_producer,
                     evaluated != given and evaluated != default_store_id()))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(field.store))
    Ensures(Acc(field.has_producer))
    Ensures(Acc(field.producer_id))
    # (1a) a producer is recorded exactly when one was supplied,
    Ensures(field.has_producer == given_is_producer)
    # (1b) and the recorded producer is the original producer supplied.
    Ensures(Implies(given_is_producer, field.producer_id == given))
    # (1b') when configured directly with a concrete store, no producer
    #       reference is written: the recorded producer id is left exactly as
    #       it was (configuration without a producer records nothing).
    Ensures(Implies(not given_is_producer,
                    field.producer_id == Old(field.producer_id)))
    # (1c) the live store is the producer's evaluation when a producer was
    #      supplied, else the supplied store itself.
    Ensures(field.store == (evaluated if given_is_producer else given))
    # post-conditions-end
    # impl-start
    field.store = given
    if given_is_producer:
        # Record a reference to the original producer, then adopt the concrete
        # store it yields as the live store.
        field.has_producer = True
        field.producer_id = given
        field.store = evaluated
    else:
        field.has_producer = False
    # impl-end


def describe_store(field: AttachmentField) -> Optional[int]:
    # pre-conditions-start
    # The field is read-only here: described, not mutated.
    Requires(Acc(field.store, 1 / 2))
    Requires(Acc(field.has_producer, 1 / 2))
    Requires(Acc(field.producer_id, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(field.store, 1 / 2))
    Ensures(Acc(field.has_producer, 1 / 2))
    Ensures(Acc(field.producer_id, 1 / 2))
    # No store description when the live store is the ambient default store.
    Ensures((field.store == default_store_id()) == (Result() is None))
    # When a description IS emitted, it is the originally-supplied value: the
    # recorded original producer if one was recorded, else the live store
    # itself. Crucially, with a recorded producer the description is the
    # producer, never the concrete store it was evaluated to.
    Ensures(Implies(field.store != default_store_id() and field.has_producer,
                    Result() is not None and Result() == field.producer_id))
    Ensures(Implies(field.store != default_store_id() and not field.has_producer,
                    Result() is not None and Result() == field.store))
    # post-conditions-end
    # impl-start
    if field.store == default_store_id():
        return None
    if field.has_producer:
        return field.producer_id
    return field.store
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Project root here; adversary/harness run with the swebench-lean venv. Bundle ships no patch.diff (gold lives in dataset/meta.json); gold = add `self._storage_callable = self.storage` before evaluating the callable in FileField.__init__, and emit getattr(self,'_storage_callable',self.storage) in deconstruct. F2P = test_deconstruction (assertIs(storage, callable_storage)).

SPEC SHAPE: only the two impl regions are editable; same_spec confirmed byte-identical spec for all 9 files. configure's postconditions fully pin store/has_producer/producer_id on BOTH branches (incl. frame clause producer_id==Old(producer_id) on the non-producer branch); describe_store's postconditions pin Result() as a total function of state (None iff default; producer_id iff has_producer; store otherwise). This is an airtight functional spec, so any verifying impl is behaviourally gold at the model level.

### ATTACKS (all same-spec; adversary weakness nagini django__django-13343 <file>):
- atk_1 partial/prepatch-B: describe returns field.store unconditionally -> FAILS verify (fails Result()==producer_id). Reproduces model_prepatch.py site-B bug.
- atk_2 prepatch-A: configure never records producer (has_producer stays False) -> FAILS verify (fails has_producer==given_is_producer). Reproduces model_prepatch_2.py site-A bug.
- atk_3 boundary: producer_id=evaluated instead of given -> FAILS verify (fails producer_id==given).
- atk_4 swapped branches in describe -> FAILS verify.
- atk_5 control-flow-effect: scribble producer_id=given on the non-producer else branch -> FAILS verify (fails producer_id==Old(producer_id) frame clause; the dead-state hole the spec explicitly closes).
- atk_6 ungrounded-oracle: describe returns producer_id whenever non-default -> FAILS verify (breaks the not-has_producer case Result()==store).
- atk_7 boundary: describe returns None when has_producer (drops the key) -> FAILS verify (breaks store==default <=> Result() is None).
All 7 wrong impls REJECTED by the spec (exit 2, does-not-verify). 

CANDIDATE: atk_echo (behaviourally-gold rewrite of both impls, different text) -> adversary weakness = CANDIDATE (shares spec AND verifies, 10.6s). Materialized its faithful refined patch (patch_atk_echo.diff, = gold semantics) and ran it through the official harness: run_resolve('django__django-13343', ...) -> completed=True, resolved=True, flaky=False, note='resolved'. The one verifying candidate RESOLVES, so verify=>correct holds; no verifying wrong impl whose faithful patch fails to resolve was found.

Positive control pos_control.py (exact model.py) verifies (CANDIDATE, 11.0s). prepatch_reproduced=true (atk_1=site B, atk_2=site A each fail verify on the right postcondition).

REFINEMENT.MD A-LEG AUDIT: no consumed @ContractOnly axiom (meta axioms=[]). Two deep_model_references, both kind A-reference (no kind-3): (A-ref 1) producer evaluation yields a distinct real Storage -> configure precondition evaluated!=given & evaluated!=default; (A-ref 2) default-store identity -> describe guard store==default_store_id(). axiom_check.py validates BOTH against the REAL F2P callees (callable_storage, CallableStorage, temp_storage, default_storage): asserts producer() is not producer, isinstance(producer(),Storage), producer() is not default_storage, temp_storage is not default_storage, default_storage is default_storage, plus the real FileField round-trip at identity level (callable->callable, class->class, concrete->concrete, default->suppressed). Both A-references concern UNCHANGED Python semantics the new code relies on; the two genuinely-changed ops (record producer / emit producer) are modeled deeply as field-state logic. Every refinement.md leg is R / A-reference / I; correspondence to the real callees holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13343.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A file-attachment field may be configured with its backing store given
  either directly as a concrete store, or *indirectly* as a zero-argument
  producer that is evaluated once at configuration time to obtain the concrete
  store actually used at runtime. The point of the indirection is that the
  producer — not whatever concrete store it happens to yield — is the stable,
  reconfigurable description of the field.

  Two cooperating operations are specified.

  (1) Configuration. When the field is configured with a producer, the field
      both (a) records a reference to that original producer and (b) adopts the
      concrete store the producer yields as its live store. Evaluating a
      producer yields a concrete store that is a DISTINCT object from the
      producer itself. When configured directly with a concrete store, the
      field adopts it as the live store and records no producer.

  (2) Description (the inverse-of-configuration query that reproduces how the
      field was configured). The store-description it emits must be the value
      ORIGINALLY supplied at configuration: the original producer when one was
      supplied, otherwise the live store. In particular, when a producer was
      supplied the description must NOT be the concrete store the producer was
      evaluated to — that would defeat the indirection, freezing one runtime
      choice into the field's persisted description. When the live store is the
      ambient default store, no store description is emitted at all.

Store objects and producers are modelled by their object identity, carried as
distinct integer ids; the ambient default store has a reserved constant identity.
A producer's evaluation yields a store id distinct from the producer's id
(faithful to evaluating a real producer, which returns a separate store
object). The two operations communicate only through the field's recorded
state. No library callee is involved; the behaviour is pure state/identity
logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the behaviour is pure object-identity / state logic,
# modelled deeply. The identity-preservation of evaluating a real producer and
# of the identity comparison against the ambient default store are validated
# against their real Python semantics out-of-band by axiom_check.py (G-AX) as
# A-references, not consumed here.
# axioms-end


# pure-start
@Pure
def default_store_id() -> int:
    """The reserved identity of the ambient default store."""
    return 0
# pure-end


class AttachmentField:
    def __init__(self) -> None:
        Ensures(Acc(self.store))            # type: ignore
        Ensures(Acc(self.has_producer))     # type: ignore
        Ensures(Acc(self.producer_id))      # type: ignore
        self.store = 0            # type: int   # live concrete store identity
        self.has_producer = False  # type: bool  # whether a producer was recorded
        self.producer_id = 0      # type: int   # recorded original producer id


def configure(field: AttachmentField, given: int, given_is_producer: bool,
              evaluated: int) -> None:
    # pre-conditions-start
    Requires(Acc(field.store))
    Requires(Acc(field.has_producer))
    Requires(Acc(field.producer_id))
    # A concrete store is supplied (the ambient default is reserved id 0; a
    # supplied store/producer carries a non-default identity).
    Requires(given != default_store_id())
    # Evaluating a producer yields a concrete store that is a DISTINCT object
    # from the producer itself (the discriminating fact the description query
    # must respect), and which is itself a real store, not the default.
    Requires(Implies(given_is_producer,
                     evaluated != given and evaluated != default_store_id()))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(field.store))
    Ensures(Acc(field.has_producer))
    Ensures(Acc(field.producer_id))
    # (1a) a producer is recorded exactly when one was supplied,
    Ensures(field.has_producer == given_is_producer)
    # (1b) and the recorded producer is the original producer supplied.
    Ensures(Implies(given_is_producer, field.producer_id == given))
    # (1b') when configured directly with a concrete store, no producer
    #       reference is written: the recorded producer id is left exactly as
    #       it was (configuration without a producer records nothing).
    Ensures(Implies(not given_is_producer,
                    field.producer_id == Old(field.producer_id)))
    # (1c) the live store is the producer's evaluation when a producer was
    #      supplied, else the supplied store itself.
    Ensures(field.store == (evaluated if given_is_producer else given))
    # post-conditions-end
    # impl-start
    field.store = given
    if given_is_producer:
        # Record a reference to the original producer, then adopt the concrete
        # store it yields as the live store.
        field.has_producer = True
        field.producer_id = given
        field.store = evaluated
    else:
        field.has_producer = False
    # impl-end


def describe_store(field: AttachmentField) -> Optional[int]:
    # pre-conditions-start
    # The field is read-only here: described, not mutated.
    Requires(Acc(field.store, 1 / 2))
    Requires(Acc(field.has_producer, 1 / 2))
    Requires(Acc(field.producer_id, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(field.store, 1 / 2))
    Ensures(Acc(field.has_producer, 1 / 2))
    Ensures(Acc(field.producer_id, 1 / 2))
    # No store description when the live store is the ambient default store.
    Ensures((field.store == default_store_id()) == (Result() is None))
    # When a description IS emitted, it is the originally-supplied value: the
    # recorded original producer if one was recorded, else the live store
    # itself. Crucially, with a recorded producer the description is the
    # producer, never the concrete store it was evaluated to.
    Ensures(Implies(field.store != default_store_id() and field.has_producer,
                    Result() is not None and Result() == field.producer_id))
    Ensures(Implies(field.store != default_store_id() and not field.has_producer,
                    Result() is not None and Result() == field.store))
    # post-conditions-end
    # impl-start
    if field.store == default_store_id():
        return None
    if field.has_producer:
        return field.producer_id
    return field.store
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Project root here; adversary/harness run with the swebench-lean venv. Bundle ships no patch.diff (gold lives in dataset/meta.json); gold = add `self._storage_callable = self.storage` before evaluating the callable in FileField.__init__, and emit getattr(self,'_storage_callable',self.storage) in deconstruct. F2P = test_deconstruction (assertIs(storage, callable_storage)).

SPEC SHAPE: only the two impl regions are editable; same_spec confirmed byte-identical spec for all 9 files. configure's postconditions fully pin store/has_producer/producer_id on BOTH branches (incl. frame clause producer_id==Old(producer_id) on the non-producer branch); describe_store's postconditions pin Result() as a total function of state (None iff default; producer_id iff has_producer; store otherwise). This is an airtight functional spec, so any verifying impl is behaviourally gold at the model level.

### ATTACKS (all same-spec; adversary weakness nagini django__django-13343 <file>):
- atk_1 partial/prepatch-B: describe returns field.store unconditionally -> FAILS verify (fails Result()==producer_id). Reproduces model_prepatch.py site-B bug.
- atk_2 prepatch-A: configure never records producer (has_producer stays False) -> FAILS verify (fails has_producer==given_is_producer). Reproduces model_prepatch_2.py site-A bug.
- atk_3 boundary: producer_id=evaluated instead of given -> FAILS verify (fails producer_id==given).
- atk_4 swapped branches in describe -> FAILS verify.
- atk_5 control-flow-effect: scribble producer_id=given on the non-producer else branch -> FAILS verify (fails producer_id==Old(producer_id) frame clause; the dead-state hole the spec explicitly closes).
- atk_6 ungrounded-oracle: describe returns producer_id whenever non-default -> FAILS verify (breaks the not-has_producer case Result()==store).
- atk_7 boundary: describe returns None when has_producer (drops the key) -> FAILS verify (breaks store==default <=> Result() is None).
All 7 wrong impls REJECTED by the spec (exit 2, does-not-verify). 

CANDIDATE: atk_echo (behaviourally-gold rewrite of both impls, different text) -> adversary weakness = CANDIDATE (shares spec AND verifies, 10.6s). Materialized its faithful refined patch (patch_atk_echo.diff, = gold semantics) and ran it through the official harness: run_resolve('django__django-13343', ...) -> completed=True, resolved=True, flaky=False, note='resolved'. The one verifying candidate RESOLVES, so verify=>correct holds; no verifying wrong impl whose faithful patch fails to resolve was found.

Positive control pos_control.py (exact model.py) verifies (CANDIDATE, 11.0s). prepatch_reproduced=true (atk_1=site B, atk_2=site A each fail verify on the right postcondition).

REFINEMENT.MD A-LEG AUDIT: no consumed @ContractOnly axiom (meta axioms=[]). Two deep_model_references, both kind A-reference (no kind-3): (A-ref 1) producer evaluation yields a distinct real Storage -> configure precondition evaluated!=given & evaluated!=default; (A-ref 2) default-store identity -> describe guard store==default_store_id(). axiom_check.py validates BOTH against the REAL F2P callees (callable_storage, CallableStorage, temp_storage, default_storage): asserts producer() is not producer, isinstance(producer(),Storage), producer() is not default_storage, temp_storage is not default_storage, default_storage is default_storage, plus the real FileField round-trip at identity level (callable->callable, class->class, concrete->concrete, default->suppressed). Both A-references concern UNCHANGED Python semantics the new code relies on; the two genuinely-changed ops (record producer / emit producer) are modeled deeply as field-state logic. Every refinement.md leg is R / A-reference / I; correspondence to the real callees holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13343 nagini bundle. model.py verifies (nagini_verify.sh exit 0, 11s). The bundle models the two-site gold patch: configure (FileField.__init__ storage block, files.py:230-237) and describe_store (FileField.deconstruct, files.py:281-282), with storage objects/producers abstracted to int identities and default_storage=0.

Verified against the REAL repo at base_commit ece18207 by instantiating FileField on every representative input and comparing deconstruct() output to the model's postconditions:
  - func producer (callable_storage -> distinct temp_storage): _storage_callable recorded, deconstruct['storage'] IS callable_storage (the original producer, not evaluated store) == model producer_id. AGREE. This is exactly the F2P test_deconstruction input (storage_callable field, assertIs(storage, callable_storage)).
  - class producer (CallableStorage): deconstruct returns the class, model producer_id. AGREE (P2P storage_callable_class).
  - concrete store (temp_storage, non-callable): no _storage_callable, deconstruct returns the store == model store branch. AGREE.
  - default (unconfigured): storage is default_storage, key ABSENT == model None branch. AGREE.

The model's precondition domain (given != default; when producer, evaluated != given and evaluated != default) faithfully captures real producer semantics: real test producers return a distinct real Storage object. The two precondition-EXCLUDED real edge cases were checked for hidden drift and both still agree with the identity model: (a) a CallableStorage instance whose __call__ returns self (evaluated==given) -> real deconstruct returns the instance, identity model with store=producer_id=inst also returns inst; (b) a producer evaluating to default (evaluated==0) -> real suppresses the key, identity model store==0 => None. No input in or adjacent to the modeled domain makes the spec disagree with the real callee.

The spec is not too strong; the precondition restrictions are sound abstractions of real Python/Django semantics (validated additionally by axiom_check.py G-AX). No divergence found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures). Manual review of the spec view (model.py spec/pre/post/pure/axiom regions, verified via markers.spec_view) confirms no leakage of the gold edit beyond the public problem_statement:

1. No repo symbols leak. The gold patch touches FileField.__init__ / FileField.deconstruct and adds/uses `_storage_callable`, comparing against `default_storage`. The spec view abstracts all of these: class AttachmentField, fields store/has_producer/producer_id, functions configure/describe_store, default_store_id(). None of `_storage_callable`, `FileField`, `deconstruct`, `default_storage`, `storage`, `callable` appear in the spec view.

2. No file/module path leaks: `files.py` and `django.db.models.fields.files` do not appear in the spec view.

3. No gold-patch lines reproduced: neither `self._storage_callable = self.storage` nor `getattr(self, '_storage_callable', self.storage)` (nor any >=8-char normalized substring) appears in the spec view.

4. The behavior described in the spec view is already public via problem_statement, which states verbatim: 'The correct behavior should be to return a reference to the original callable during deconstruction' and explains that evaluating the callable during deconstruction inlines the concrete store and breaks runtime-varying storage. The spec's 'record the original producer at configuration, emit the originally-supplied producer (not the evaluation) at description' is the direct, necessary logical restatement of that public requirement, not a disclosure of the specific getattr-fallback implementation mechanism. Retaining the original in order to return it is entailed by the public requirement.

5. The narration screen finds no edit-narration in spec-view comments; comments describe behavior (identity logic, producer indirection) abstractly.

Note: mapping.md and refinement.md DO quote gold-patch hunks and repo symbols (`_storage_callable`, `files.py:230-237`, etc.), but those are AUDIT-only documents explicitly marked 'NOT referenced from the consumer spec view' — they are not part of the solver-visible spec view that G-PANEL-3 screens. The consumer spec view is clean.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
