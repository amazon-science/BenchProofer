# P2 adversarial audit — django__django-16256

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -201,10 +201,8 @@
     Ensures(mgr.payload == requested)
     # post-conditions-end
     # impl-start
-    # Run the SAME-named immediate form on this accessor (its result is then
-    # delivered to the awaiting caller). Because it is the related-set accessor's
-    # OWN immediate form, the produced object is attached to the related set.
-    return create(mgr, obj, requested)
+    mgr.payload = requested
+    return obj
     # impl-end
 
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -365,5 +365,5 @@
     Ensures(Result().payload == requested)
     # post-conditions-end
     # impl-start
-    return update_or_create(mgr, obj, exists, requested)
-    # impl-end
+    return get_or_create(mgr, obj, exists, requested)
+    # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -289,7 +289,7 @@
     Ensures(Implies(not exists, Result().payload == requested))
     # post-conditions-end
     # impl-start
-    return get_or_create(mgr, obj, exists, requested)
+    return update_or_create(mgr, obj, exists, requested)
     # impl-end
 
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -289,7 +289,12 @@
     Ensures(Implies(not exists, Result().payload == requested))
     # post-conditions-end
     # impl-start
-    return get_or_create(mgr, obj, exists, requested)
+    if exists:
+        return Outcome(obj, False, mgr.payload)
+    if requested >= 0:
+        mgr.members.append(obj)
+    mgr.payload = requested
+    return Outcome(obj, True, requested)
     # impl-end
 
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -365,5 +365,9 @@
     Ensures(Result().payload == requested)
     # post-conditions-end
     # impl-start
+    b = True
+    while b:
+        Invariant(b)
+        b = True
     return update_or_create(mgr, obj, exists, requested)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -289,7 +289,12 @@
     Ensures(Implies(not exists, Result().payload == requested))
     # post-conditions-end
     # impl-start
-    return get_or_create(mgr, obj, exists, requested)
+    if exists:
+        mgr.members.append(obj)
+        return Outcome(obj, False, mgr.payload)
+    mgr.members.append(obj)
+    mgr.payload = requested
+    return Outcome(obj, True, requested)
     # impl-end
 
 
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -365,5 +365,9 @@
     Ensures(Result().payload == requested)
     # post-conditions-end
     # impl-start
-    return update_or_create(mgr, obj, exists, requested)
-    # impl-end
+    if exists:
+        return Outcome(obj, False, requested)
+    mgr.members.append(obj)
+    mgr.payload = requested
+    return Outcome(obj, True, requested)
+    # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -201,10 +201,10 @@
     Ensures(mgr.payload == requested)
     # post-conditions-end
     # impl-start
-    # Run the SAME-named immediate form on this accessor (its result is then
-    # delivered to the awaiting caller). Because it is the related-set accessor's
-    # OWN immediate form, the produced object is attached to the related set.
-    return create(mgr, obj, requested)
+    if len(mgr.members) == 0:
+        mgr.members.append(obj)
+    mgr.payload = requested
+    return obj
     # impl-end
 
 
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -201,10 +201,9 @@
     Ensures(mgr.payload == requested)
     # post-conditions-end
     # impl-start
-    # Run the SAME-named immediate form on this accessor (its result is then
-    # delivered to the awaiting caller). Because it is the related-set accessor's
-    # OWN immediate form, the produced object is attached to the related set.
-    return create(mgr, obj, requested)
+    mgr.members.append(mgr.payload)
+    mgr.payload = requested
+    return obj
     # impl-end
 
 
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -289,7 +289,12 @@
     Ensures(Implies(not exists, Result().payload == requested))
     # post-conditions-end
     # impl-start
-    return get_or_create(mgr, obj, exists, requested)
+    if exists:
+        return Outcome(obj, False, mgr.payload)
+    if len(mgr.members) == 0:
+        mgr.members.append(obj)
+    mgr.payload = requested
+    return Outcome(obj, True, requested)
     # impl-end
 
 
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -201,10 +201,10 @@
     Ensures(mgr.payload == requested)
     # post-conditions-end
     # impl-start
-    # Run the SAME-named immediate form on this accessor (its result is then
-    # delivered to the awaiting caller). Because it is the related-set accessor's
-    # OWN immediate form, the produced object is attached to the related set.
-    return create(mgr, obj, requested)
+    mgr.members.append(obj)
+    mgr.members.append(obj)
+    mgr.payload = requested
+    return obj
     # impl-end
 
 
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -289,7 +289,10 @@
     Ensures(Implies(not exists, Result().payload == requested))
     # post-conditions-end
     # impl-start
-    return get_or_create(mgr, obj, exists, requested)
+    if exists:
+        return Outcome(obj, False, mgr.payload)
+    mgr.members.append(obj)
+    return Outcome(obj, True, mgr.payload)
     # impl-end
 
 
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -365,5 +365,5 @@
     Ensures(Result().payload == requested)
     # post-conditions-end
     # impl-start
-    return update_or_create(mgr, obj, exists, requested)
-    # impl-end
+    return aget_or_create(mgr, obj, exists, requested)
+    # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16256.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A related-set accessor exposes both an immediate and a deferred form of three
  object-producing operations. The immediate forms perform relation-specific
  work: producing (or locating) an object AND, when a NEW object is produced,
  attaching it to the owning instance's related set (so the object becomes a
  member of that set). The three operations are distinguished by what they do
  to an object that is ALREADY present and by the payload the delivered object
  ends up carrying:

    * "produce" always produces a new object, attaches it to the related set,
      and the object carries the payload the caller asked for;
    * "locate-or-produce" hands an already-present object back EXACTLY as it
      stands — the caller's payload is used only when a new object has to be
      produced — and attaches only a newly-produced object;
    * "refresh-or-produce" leaves the object carrying the caller's payload in
      BOTH cases: an already-present object is refreshed with it (that payload
      is what persists and what the caller receives), a new object is produced
      with it and attached.

  The deferred forms exist so a caller may obtain the result without blocking;
  the contract pinned here is that each deferred form delivers EXACTLY the
  result its SAME-named immediate counterpart would, with EXACTLY the same
  effect on the owning instance's related set and on the delivered object's
  payload. Concretely:

    (1) the deferred "produce" form delivers the object the immediate "produce"
        form would, leaves the owning instance's related set extended by that
        produced object (membership), and leaves the object carrying the
        requested payload, just as the immediate form does;

    (2) the deferred "locate-or-produce" form delivers the same object, the
        same produced/located flag and the same payload as its immediate
        counterpart, and reproduces its effects: a produced object is attached
        to the related set and carries the requested payload; an already-present
        object leaves the set unchanged and is delivered with the payload it
        already had, which is also left unchanged;

    (3) the deferred "refresh-or-produce" form behaves like (2) on membership —
        attach a produced object, leave the set unchanged for an already-present
        one — but on payload it differs: in BOTH cases the object ends up
        carrying the requested payload, and that is the payload delivered.

  The two discriminating requirements. (a) MEMBERSHIP: each deferred form must
  reproduce the membership effect of the same-named immediate form; a deferred
  form that delivers the object but does NOT attach a newly-produced object to
  the owning instance's related set violates the contract. (b) PAYLOAD: each
  deferred form must reproduce the payload behaviour of the same-named
  immediate form; a "refresh-or-produce" form that hands an already-present
  object back untouched, and a "locate-or-produce" form that overwrites an
  already-present object's payload with the caller's, both violate the
  contract — even though the two agree on the delivered identity, on the
  produced/located flag and on membership.

The related set is modelled as a `List[int]` of member object identities held
by a minimal accessor object; an object identity is an `int`. The payload of
the object an operation keys on is modelled by one `int` slot on that accessor
(`payload`) — the value currently persisted for that object — and the payload
the caller asks the object to carry is the `int` parameter `requested`. The
immediate forms are modelled deeply (a produced object is attached via a list
append, and the payload slot is written exactly when the operation is defined
to write it), and each deferred form is specified to reproduce its immediate
counterpart's post-state exactly. The produced/located flag, the delivered
object and its delivered payload are carried by a minimal result object.

Termination (total correctness): every modelled operation is bounded,
loop-free straight-line work that must actually ANSWER — deliver the produced
(or located) object to the awaiting caller. Nagini is a partial-correctness
verifier by default, so without an explicit obligation a non-terminating
implementation (e.g. an endless loop before the return) satisfies every
`Ensures` vacuously while a real deferred form that never resolves would hang
every awaiting F2P test. The obligation is carried as `MustTerminate` in each
precondition, with strictly decreasing measures (deferred form 3 -> immediate
form 2 -> result/accessor construction 1) so each routine may invoke its
callees but may NOT re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class RelatedAccessor:
    """Accessor for an owning instance's related set. Carries only the touched
    fields: ``members``, the identities of the objects currently attached to the
    owning instance (the related set), and ``payload``, the value currently
    persisted for the object the operation keys on."""

    def __init__(self, members: List[int], payload: int) -> None:
        Requires(list_pred(members))
        # Constructing the accessor is bounded straight-line work (measure 1,
        # strictly below every modelled operation, so any of them may build one).
        Requires(MustTerminate(1))
        Ensures(Acc(self.members))  # type: ignore
        Ensures(Acc(self.payload))  # type: ignore
        Ensures(self.members is members)  # type: ignore
        Ensures(self.payload == payload)  # type: ignore
        self.members = members  # type: List[int]
        self.payload = payload  # type: int

class Outcome:
    """Result of a locate-or-produce / refresh-or-produce operation: the object
    identity delivered, whether it was newly produced (``created``), and the
    payload the delivered object carries."""

    def __init__(self, obj: int, created: bool, payload: int) -> None:
        # Building the result carrier is bounded straight-line work (measure 1).
        Requires(MustTerminate(1))
        Ensures(Acc(self.obj))  # type: ignore
        Ensures(Acc(self.created))  # type: ignore
        Ensures(Acc(self.payload))  # type: ignore
        Ensures(self.obj == obj)  # type: ignore
        Ensures(self.created == created)  # type: ignore
        Ensures(self.payload == payload)  # type: ignore
        self.obj = obj  # type: int
        self.created = created  # type: bool
        self.payload = payload  # type: int

# axioms-start
# (no unchanged-callee axioms are consumed: the relation-specific attachment
# and payload work of the immediate forms is modelled DEEPLY below as a list
# append and a payload write, and each deferred form's contract is tied to its
# immediate counterpart's pinned post-state. The thread-offloading machinery
# the deferred forms use to run the immediate form is unobservable at this
# granularity — the only observable fact is that the SAME immediate form runs,
# so the related set and the payload end in the SAME state — and is therefore
# not axiomatised.)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required: the membership effect is pinned
# exactly by sequence equality on the related set and the payload effect by
# equality on the payload slot.)
# pure-end

def create(mgr: RelatedAccessor, obj: int, requested: int) -> int:
    # pre-conditions-start
    # The immediate "produce" form genuinely mutates the related set (it
    # attaches the produced object) and the payload slot (the produced object
    # carries the requested payload), so both are held at full permission with
    # their exact post-state pinned below.
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: producing-and-attaching is bounded work that must COMPLETE
    # and deliver the produced object. Under partial-correctness semantics a
    # diverging body satisfies every Ensures vacuously yet never answers; the
    # real immediate form always returns. Measure 2 (> 1) lets it construct
    # the result/accessor carriers; measure 2 (< 3) lets the deferred form
    # invoke it without leaking its own obligation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    # The produced object is delivered.
    Ensures(Result() == obj)
    # ATTACH: the produced object is appended to the owning instance's related
    # set (it becomes a member); nothing else changes.
    Ensures(ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj))
    # PAYLOAD: the produced object carries the payload the caller asked for.
    Ensures(mgr.payload == requested)
    # post-conditions-end
    # impl-start
    mgr.members.append(obj)
    mgr.payload = requested
    return obj
    # impl-end

def acreate(mgr: RelatedAccessor, obj: int, requested: int) -> int:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: the deferred form must actually RESOLVE — run the immediate
    # form to completion and deliver its result to the awaiting caller. Nagini
    # checks partial correctness by default, so without this obligation a
    # same-spec impl that spins forever before returning satisfies every
    # Ensures vacuously while its real counterpart would hang every awaiting
    # F2P test. Measure 3 (> 2) admits the delegation to the immediate form.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    # (1) The deferred form delivers EXACTLY what the immediate "produce" form
    # delivers, and reproduces its effects: the produced object is attached to
    # the owning instance's related set and carries the requested payload.
    Ensures(Result() == obj)
    Ensures(ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj))
    Ensures(mgr.payload == requested)
    # post-conditions-end
    # impl-start
    # Run the SAME-named immediate form on this accessor (its result is then
    # delivered to the awaiting caller). Because it is the related-set accessor's
    # OWN immediate form, the produced object is attached to the related set.
    return create(mgr, obj, requested)
    # impl-end

def get_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                  requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: locate-or-produce is bounded work that must COMPLETE and
    # deliver its (object, produced-flag, payload) outcome; the real immediate
    # form always returns. Measure 2: may build the Outcome carrier (1), may be
    # invoked by the deferred form (3).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    # `exists` records whether a matching object is already present (located),
    # in which case the related set is left unchanged and the object is handed
    # back exactly as it stands; otherwise a new object is produced, attached,
    # and given the requested payload.
    Ensures(Result().obj == obj)
    # produced flag mirrors whether the object had to be produced.
    Ensures(Result().created == (not exists))
    # LOCATE: an already-present object leaves the related set unchanged.
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    # PRODUCE: a newly-produced object is attached to the related set.
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    # LOCATE / PAYLOAD: the caller's payload is NOT applied to an object that is
    # already present — it keeps, and is delivered with, the payload it has.
    Ensures(Implies(exists, mgr.payload == Old(mgr.payload)))
    Ensures(Implies(exists, Result().payload == Old(mgr.payload)))
    # PRODUCE / PAYLOAD: a newly-produced object carries the requested payload.
    Ensures(Implies(not exists, mgr.payload == requested))
    Ensures(Implies(not exists, Result().payload == requested))
    # post-conditions-end
    # impl-start
    if exists:
        return Outcome(obj, False, mgr.payload)
    mgr.members.append(obj)
    mgr.payload = requested
    return Outcome(obj, True, requested)
    # impl-end

def aget_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                   requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: the deferred form must RESOLVE (run the immediate form to
    # completion and deliver its outcome to the awaiting caller); a diverging
    # body would satisfy every Ensures vacuously. Measure 3 (> 2) admits the
    # delegation to the immediate form.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    # (2) The deferred form delivers EXACTLY the object, produced flag and
    # payload the immediate "locate-or-produce" form would, and reproduces its
    # membership and payload effects.
    Ensures(Result().obj == obj)
    Ensures(Result().created == (not exists))
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    Ensures(Implies(exists, mgr.payload == Old(mgr.payload)))
    Ensures(Implies(exists, Result().payload == Old(mgr.payload)))
    Ensures(Implies(not exists, mgr.payload == requested))
    Ensures(Implies(not exists, Result().payload == requested))
    # post-conditions-end
    # impl-start
    return get_or_create(mgr, obj, exists, requested)
    # impl-end

def update_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                     requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: refresh-or-produce is bounded work that must COMPLETE and
    # deliver its (object, produced-flag, payload) outcome; the real immediate
    # form always returns. Measure 2: may build the Outcome carrier (1), may be
    # invoked by the deferred form (3).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    Ensures(Result().obj == obj)
    Ensures(Result().created == (not exists))
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    # REFRESH / PAYLOAD: whether the object was already present or had to be
    # produced, it ends up carrying the payload the caller asked for, and that
    # is the payload delivered. This is what separates refresh-or-produce from
    # locate-or-produce: an already-present object is NOT handed back untouched.
    Ensures(mgr.payload == requested)
    Ensures(Result().payload == requested)
    # post-conditions-end
    # impl-start
    if exists:
        mgr.payload = requested
        return Outcome(obj, False, requested)
    mgr.members.append(obj)
    mgr.payload = requested
    return Outcome(obj, True, requested)
    # impl-end

def aupdate_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                      requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: the deferred form must RESOLVE (run the immediate form to
    # completion and deliver its outcome to the awaiting caller); a diverging
    # body would satisfy every Ensures vacuously. Measure 3 (> 2) admits the
    # delegation to the immediate form.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    # (3) The deferred form delivers EXACTLY the object, produced flag and
    # payload the immediate "refresh-or-produce" form would, and reproduces its
    # membership and payload effects.
    Ensures(Result().obj == obj)
    Ensures(Result().created == (not exists))
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    Ensures(mgr.payload == requested)
    Ensures(Result().payload == requested)
    # post-conditions-end
    # impl-start
    return update_or_create(mgr, obj, exists, requested)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-16256 (nagini). 13 same-spec wrong impls encoded; ALL 13 same-spec-byte-identical (adversary same-spec exit 0) and ALL 13 REJECTED by the verifier (adversary weakness exit 2, summary 'attack does not verify (verification failed)'). ZERO CANDIDATEs, so no faithful refined patch had to be materialized through run_resolve -- step 2 of the protocol is vacuous by measurement, not by omission. Positive control = byte-identical copy of bundle model.py: 'Verification successful' in 24.93s via scripts/nagini_verify.sh (exit 0).

### COMMANDS (from repo root swe-proof, D=):
  python -m swebench_unified.adversary same-spec nagini django__django-16256 $D/atk_N.py   -> exit 0 (all N=1..13)
  python -m swebench_unified.adversary weakness  nagini django__django-16256 $D/atk_N.py   -> exit 2 (all N=1..13)
  bash scripts/nagini_verify.sh $D/positive_control.py                                     -> exit 0
Attack builders: $D/build_attacks.py, $D/build_attacks2.py. Raw verifier output retained per attack at $D/res_atk_N.txt and $D/res_poscontrol.txt.

### ATTACK BATTERY (path -> class -> result; every one exit 2 = spec rejected):
atk_1  PREPATCH BUG. acreate delivers the produced object carrying the requested payload but never attaches it (pre-patch a<op> fell through to QuerySet's async method, which creates but does not run the related manager's attaching create). Behaviourally identical to the bundle's own model_prepatch.py acreate impl (diffed: same two statements, prose aside). Fails the membership clause. REJECTED. atk_2  WRONG CALLEE, payload downgraded. aupdate_or_create delegates to get_or_create -- agrees on identity, created flag and membership in EVERY branch, differs only by handing an already-present object back untouched. This is exactly the collapse refinement.md C2b and axiom_check.check_discriminates_payload claim the spec rejects.

REJECTED. atk_3  WRONG CALLEE, payload upgraded (opposite direction). aget_or_create delegates to update_or_create, overwriting an already-present object's payload. refinement.md B2b leg; would break F2P test_generic_async_aget_or_create (located tag must still read 'fatty') and P2P test_generic_get_or_create_when_exists. REJECTED. atk_4  PARTIAL DOMAIN. aget_or_create attaches a produced object only when requested >= 0. Correct on every F2P input (field=2/3, tags), wrong elsewhere; spec bounds `requested` nowhere. REJECTED. atk_5  DIVERGENCE / partial-correctness vacuity. aupdate_or_create spins in `while b: Invariant(b)` before delegating. The G-PANEL-1 witness class MustTerminate(3) is supposed to close; confirms the obligation is load-bearing, not decorative.

REJECTED. atk_6  CONTROL-FLOW EFFECT (double attach). aget_or_create attaches on BOTH paths -- re-attaching an already-present object (the real `self.add()` outside `if created` bug shape). Only the locate-path clause Implies(exists, ToSeq == Old(ToSeq)) separates it. REJECTED. atk_7  UNSAVED WRITE. aupdate_or_create's refresh path applies the payload to the DELIVERED object but never persists it (setattr with no obj.save()). Probes mapping.md §2's claim that Outcome.payload and mgr.payload are genuinely distinct observables.

REJECTED. atk_8  BOUNDARY ON PRE-STATE (highest-value probe). acreate attaches only when the related set is currently EMPTY -- satisfies the two async F2P tests that start empty, but F2P test_generic_async_acreate starts from bacon.tags with TWO tags and asserts acount()==3, so a patch refining this would NOT resolve. REJECTED (had it verified, this was the break). atk_9  WRONG IDENTITY ATTACHED. acreate appends the stale payload instead of obj -- satisfies a count-only observation, fails ...+PSeq(obj). REJECTED. atk_10 PARTIAL DOMAIN on the other op. aget_or_create attaches only into an empty related set (atk_8's shape moved to locate-or-produce).

REJECTED. atk_11 OFF-BY-ONE. acreate attaches the produced object twice (two through-rows); shows the exact ToSeq sequence equality bites where a set-style membership predicate would not. REJECTED. atk_12 PAYLOAD DROPPED ON PRODUCE. aget_or_create's produce path attaches and reports created=True but the object keeps the stale payload (kwargs dropped); breaks test_aget_or_create's new_simple.field==2. REJECTED. atk_13 MEASURE-LADDER PROBE. aupdate_or_create delegates to the sibling DEFERRED form aget_or_create -- wrong operation AND same MustTerminate measure (3->3). REJECTED, so the 3>2>1 ladder advertised in refinement.md A5 genuinely constrains the call graph.

A-LEG AUDIT (the assignment's focus). The axioms region is genuinely EMPTY -- grep for ContractOnly/Assume/Refute/sorry/admit in model.py returns only prose hits inside MustTerminate comments, so there is no A-consumed leg and no assumed postcondition to launder a proof. All 12 refinement.md legs tag as R (A1,A2,A3b,A4,A5), R+A-reference (A3,B1,C1) or R+I (B2,B2b,C2,C2b): no kind-3, consistent with §C's claim.
I checked every A-leg citation against the REAL source at base_commit 76e37513 in the upstream repository rather than trusting the prose:
  - ManyRelatedManager.create calls self.add(new_obj, through_defaults=...) after super().create -> A4's 'attach' ↔ members.append is faithful.
  - ManyRelatedManager.get_or_create and update_or_create both guard the attach with `if created: self.add(obj, ...)` -> B2/C2's 'attach only when produced' is faithful, and the two ARE identical on membership, which is why the payload legs must carry the discrimination.
  - QuerySet.get_or_create: the located path is `return self.get(**kwargs), False` with defaults consumed only on the create path -> B2b's Old-preserving payload clause is faithful.
  - QuerySet.update_or_create: located path runs `for k,v in resolve_callables(defaults): setattr(obj,k,v)` then obj.save(...) -> C2b's UNCONDITIONAL payload==requested is faithful, and the locate/refresh asymmetry is real in the repo, not an artifact.
  - RelatedManager (reverse FK) and GenericRelatedObjectManager delegate to the same QuerySet methods with the relation fields injected into kwargs -> the nine per-site wrappers really do collapse onto the three modelled contracts.
  - The one A-reference library fact (`await sync_to_async(f)(**kwargs) == f(**kwargs)`, result AND both effects) is executed against the REAL asgiref: `python axiom_check.py` -> exit 0, 200 randomized cases, and it self-checks that it DISCRIMINATES in both dimensions (no-attach prepatch shape rejected on membership; refresh-runs-locate collapse rejected on payload). atk_1/atk_2/atk_3 are the model-side duals of those two discrimination checks and both were rejected by the verifier, so the A-reference correspondence holds on both sides.
  - Omissions audited as genuinely unobservable: `through_defaults` addresses the through-ROW's fields (a different object from the one payload tracks) and no F2P/P2P assertion reads it; `.alters_data` is a template-safety marker with no test in either the 9 F2P or 53 P2P observing it (grepped). Both omissions are sound.

MODEL<->PATCH CORRESPONDENCE. The spec pins all five modelled observables (mgr.members as an ordered sequence, mgr.payload, Result().obj, Result().created, Result().payload) in EVERY branch of all six functions, plus termination. The battery is my attempt to find a free observable a same-spec rival could still move: I probed membership (atk_1,8,9,10,11), delivered-vs-persisted payload split (atk_7,12), both cross-delegation directions (atk_2,3,13), locate-path set stability (atk_6), an unconstrained-input partial domain (atk_4) and divergence (atk_5). Every one was rejected, which is what a functionally-total spec on its modelled state looks like. The residual trust points are the two PLAN §1.1 ones and are unchanged by this audit: the sync_to_async library fact (G-AX, executed above) and the R-abstraction itself (one int scalar for the defaults-writable field, int identity for the object) -- an infidelity there is out of G-EQ's reach and is what G-CONF's 100k live-DB probes cover.

**Verdict SOUND:** >= 5 (13) admissible same-spec attacks run to a real verdict, prepatch reproduced and rejected, positive control verifies, no CANDIDATE and therefore no non-resolving faithful patch. No evidence of verify => correct failing here. Nothing was capped, timed out or left unrun -- no attack summary contains 'inconclusive'.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-16256.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A related-set accessor exposes both an immediate and a deferred form of three
  object-producing operations. The immediate forms perform relation-specific
  work: producing (or locating) an object AND, when a NEW object is produced,
  attaching it to the owning instance's related set (so the object becomes a
  member of that set). The three operations are distinguished by what they do
  to an object that is ALREADY present and by the payload the delivered object
  ends up carrying:

    * "produce" always produces a new object, attaches it to the related set,
      and the object carries the payload the caller asked for;
    * "locate-or-produce" hands an already-present object back EXACTLY as it
      stands — the caller's payload is used only when a new object has to be
      produced — and attaches only a newly-produced object;
    * "refresh-or-produce" leaves the object carrying the caller's payload in
      BOTH cases: an already-present object is refreshed with it (that payload
      is what persists and what the caller receives), a new object is produced
      with it and attached.

  The deferred forms exist so a caller may obtain the result without blocking;
  the contract pinned here is that each deferred form delivers EXACTLY the
  result its SAME-named immediate counterpart would, with EXACTLY the same
  effect on the owning instance's related set and on the delivered object's
  payload. Concretely:

    (1) the deferred "produce" form delivers the object the immediate "produce"
        form would, leaves the owning instance's related set extended by that
        produced object (membership), and leaves the object carrying the
        requested payload, just as the immediate form does;

    (2) the deferred "locate-or-produce" form delivers the same object, the
        same produced/located flag and the same payload as its immediate
        counterpart, and reproduces its effects: a produced object is attached
        to the related set and carries the requested payload; an already-present
        object leaves the set unchanged and is delivered with the payload it
        already had, which is also left unchanged;

    (3) the deferred "refresh-or-produce" form behaves like (2) on membership —
        attach a produced object, leave the set unchanged for an already-present
        one — but on payload it differs: in BOTH cases the object ends up
        carrying the requested payload, and that is the payload delivered.

  The two discriminating requirements. (a) MEMBERSHIP: each deferred form must
  reproduce the membership effect of the same-named immediate form; a deferred
  form that delivers the object but does NOT attach a newly-produced object to
  the owning instance's related set violates the contract. (b) PAYLOAD: each
  deferred form must reproduce the payload behaviour of the same-named
  immediate form; a "refresh-or-produce" form that hands an already-present
  object back untouched, and a "locate-or-produce" form that overwrites an
  already-present object's payload with the caller's, both violate the
  contract — even though the two agree on the delivered identity, on the
  produced/located flag and on membership.

The related set is modelled as a `List[int]` of member object identities held
by a minimal accessor object; an object identity is an `int`. The payload of
the object an operation keys on is modelled by one `int` slot on that accessor
(`payload`) — the value currently persisted for that object — and the payload
the caller asks the object to carry is the `int` parameter `requested`. The
immediate forms are modelled deeply (a produced object is attached via a list
append, and the payload slot is written exactly when the operation is defined
to write it), and each deferred form is specified to reproduce its immediate
counterpart's post-state exactly. The produced/located flag, the delivered
object and its delivered payload are carried by a minimal result object.

Termination (total correctness): every modelled operation is bounded,
loop-free straight-line work that must actually ANSWER — deliver the produced
(or located) object to the awaiting caller. Nagini is a partial-correctness
verifier by default, so without an explicit obligation a non-terminating
implementation (e.g. an endless loop before the return) satisfies every
`Ensures` vacuously while a real deferred form that never resolves would hang
every awaiting F2P test. The obligation is carried as `MustTerminate` in each
precondition, with strictly decreasing measures (deferred form 3 -> immediate
form 2 -> result/accessor construction 1) so each routine may invoke its
callees but may NOT re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class RelatedAccessor:
    """Accessor for an owning instance's related set. Carries only the touched
    fields: ``members``, the identities of the objects currently attached to the
    owning instance (the related set), and ``payload``, the value currently
    persisted for the object the operation keys on."""

    def __init__(self, members: List[int], payload: int) -> None:
        Requires(list_pred(members))
        # Constructing the accessor is bounded straight-line work (measure 1,
        # strictly below every modelled operation, so any of them may build one).
        Requires(MustTerminate(1))
        Ensures(Acc(self.members))  # type: ignore
        Ensures(Acc(self.payload))  # type: ignore
        Ensures(self.members is members)  # type: ignore
        Ensures(self.payload == payload)  # type: ignore
        self.members = members  # type: List[int]
        self.payload = payload  # type: int

class Outcome:
    """Result of a locate-or-produce / refresh-or-produce operation: the object
    identity delivered, whether it was newly produced (``created``), and the
    payload the delivered object carries."""

    def __init__(self, obj: int, created: bool, payload: int) -> None:
        # Building the result carrier is bounded straight-line work (measure 1).
        Requires(MustTerminate(1))
        Ensures(Acc(self.obj))  # type: ignore
        Ensures(Acc(self.created))  # type: ignore
        Ensures(Acc(self.payload))  # type: ignore
        Ensures(self.obj == obj)  # type: ignore
        Ensures(self.created == created)  # type: ignore
        Ensures(self.payload == payload)  # type: ignore
        self.obj = obj  # type: int
        self.created = created  # type: bool
        self.payload = payload  # type: int

# axioms-start
# (no unchanged-callee axioms are consumed: the relation-specific attachment
# and payload work of the immediate forms is modelled DEEPLY below as a list
# append and a payload write, and each deferred form's contract is tied to its
# immediate counterpart's pinned post-state. The thread-offloading machinery
# the deferred forms use to run the immediate form is unobservable at this
# granularity — the only observable fact is that the SAME immediate form runs,
# so the related set and the payload end in the SAME state — and is therefore
# not axiomatised.)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required: the membership effect is pinned
# exactly by sequence equality on the related set and the payload effect by
# equality on the payload slot.)
# pure-end

def create(mgr: RelatedAccessor, obj: int, requested: int) -> int:
    # pre-conditions-start
    # The immediate "produce" form genuinely mutates the related set (it
    # attaches the produced object) and the payload slot (the produced object
    # carries the requested payload), so both are held at full permission with
    # their exact post-state pinned below.
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: producing-and-attaching is bounded work that must COMPLETE
    # and deliver the produced object. Under partial-correctness semantics a
    # diverging body satisfies every Ensures vacuously yet never answers; the
    # real immediate form always returns. Measure 2 (> 1) lets it construct
    # the result/accessor carriers; measure 2 (< 3) lets the deferred form
    # invoke it without leaking its own obligation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    # The produced object is delivered.
    Ensures(Result() == obj)
    # ATTACH: the produced object is appended to the owning instance's related
    # set (it becomes a member); nothing else changes.
    Ensures(ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj))
    # PAYLOAD: the produced object carries the payload the caller asked for.
    Ensures(mgr.payload == requested)
    # post-conditions-end
    # impl-start
    mgr.members.append(obj)
    mgr.payload = requested
    return obj
    # impl-end

def acreate(mgr: RelatedAccessor, obj: int, requested: int) -> int:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: the deferred form must actually RESOLVE — run the immediate
    # form to completion and deliver its result to the awaiting caller. Nagini
    # checks partial correctness by default, so without this obligation a
    # same-spec impl that spins forever before returning satisfies every
    # Ensures vacuously while its real counterpart would hang every awaiting
    # F2P test. Measure 3 (> 2) admits the delegation to the immediate form.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    # (1) The deferred form delivers EXACTLY what the immediate "produce" form
    # delivers, and reproduces its effects: the produced object is attached to
    # the owning instance's related set and carries the requested payload.
    Ensures(Result() == obj)
    Ensures(ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj))
    Ensures(mgr.payload == requested)
    # post-conditions-end
    # impl-start
    # Run the SAME-named immediate form on this accessor (its result is then
    # delivered to the awaiting caller). Because it is the related-set accessor's
    # OWN immediate form, the produced object is attached to the related set.
    return create(mgr, obj, requested)
    # impl-end

def get_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                  requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: locate-or-produce is bounded work that must COMPLETE and
    # deliver its (object, produced-flag, payload) outcome; the real immediate
    # form always returns. Measure 2: may build the Outcome carrier (1), may be
    # invoked by the deferred form (3).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    # `exists` records whether a matching object is already present (located),
    # in which case the related set is left unchanged and the object is handed
    # back exactly as it stands; otherwise a new object is produced, attached,
    # and given the requested payload.
    Ensures(Result().obj == obj)
    # produced flag mirrors whether the object had to be produced.
    Ensures(Result().created == (not exists))
    # LOCATE: an already-present object leaves the related set unchanged.
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    # PRODUCE: a newly-produced object is attached to the related set.
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    # LOCATE / PAYLOAD: the caller's payload is NOT applied to an object that is
    # already present — it keeps, and is delivered with, the payload it has.
    Ensures(Implies(exists, mgr.payload == Old(mgr.payload)))
    Ensures(Implies(exists, Result().payload == Old(mgr.payload)))
    # PRODUCE / PAYLOAD: a newly-produced object carries the requested payload.
    Ensures(Implies(not exists, mgr.payload == requested))
    Ensures(Implies(not exists, Result().payload == requested))
    # post-conditions-end
    # impl-start
    if exists:
        return Outcome(obj, False, mgr.payload)
    mgr.members.append(obj)
    mgr.payload = requested
    return Outcome(obj, True, requested)
    # impl-end

def aget_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                   requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: the deferred form must RESOLVE (run the immediate form to
    # completion and deliver its outcome to the awaiting caller); a diverging
    # body would satisfy every Ensures vacuously. Measure 3 (> 2) admits the
    # delegation to the immediate form.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    # (2) The deferred form delivers EXACTLY the object, produced flag and
    # payload the immediate "locate-or-produce" form would, and reproduces its
    # membership and payload effects.
    Ensures(Result().obj == obj)
    Ensures(Result().created == (not exists))
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    Ensures(Implies(exists, mgr.payload == Old(mgr.payload)))
    Ensures(Implies(exists, Result().payload == Old(mgr.payload)))
    Ensures(Implies(not exists, mgr.payload == requested))
    Ensures(Implies(not exists, Result().payload == requested))
    # post-conditions-end
    # impl-start
    return get_or_create(mgr, obj, exists, requested)
    # impl-end

def update_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                     requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: refresh-or-produce is bounded work that must COMPLETE and
    # deliver its (object, produced-flag, payload) outcome; the real immediate
    # form always returns. Measure 2: may build the Outcome carrier (1), may be
    # invoked by the deferred form (3).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    Ensures(Result().obj == obj)
    Ensures(Result().created == (not exists))
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    # REFRESH / PAYLOAD: whether the object was already present or had to be
    # produced, it ends up carrying the payload the caller asked for, and that
    # is the payload delivered. This is what separates refresh-or-produce from
    # locate-or-produce: an already-present object is NOT handed back untouched.
    Ensures(mgr.payload == requested)
    Ensures(Result().payload == requested)
    # post-conditions-end
    # impl-start
    if exists:
        mgr.payload = requested
        return Outcome(obj, False, requested)
    mgr.members.append(obj)
    mgr.payload = requested
    return Outcome(obj, True, requested)
    # impl-end

def aupdate_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                      requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: the deferred form must RESOLVE (run the immediate form to
    # completion and deliver its outcome to the awaiting caller); a diverging
    # body would satisfy every Ensures vacuously. Measure 3 (> 2) admits the
    # delegation to the immediate form.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    # (3) The deferred form delivers EXACTLY the object, produced flag and
    # payload the immediate "refresh-or-produce" form would, and reproduces its
    # membership and payload effects.
    Ensures(Result().obj == obj)
    Ensures(Result().created == (not exists))
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    Ensures(mgr.payload == requested)
    Ensures(Result().payload == requested)
    # post-conditions-end
    # impl-start
    return update_or_create(mgr, obj, exists, requested)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-16256 (nagini). 13 same-spec wrong impls encoded; ALL 13 same-spec-byte-identical (adversary same-spec exit 0) and ALL 13 REJECTED by the verifier (adversary weakness exit 2, summary 'attack does not verify (verification failed)'). ZERO CANDIDATEs, so no faithful refined patch had to be materialized through run_resolve -- step 2 of the protocol is vacuous by measurement, not by omission. Positive control = byte-identical copy of bundle model.py: 'Verification successful' in 24.93s via scripts/nagini_verify.sh (exit 0).

### COMMANDS (from repo root swe-proof, D=):
  python -m swebench_unified.adversary same-spec nagini django__django-16256 $D/atk_N.py   -> exit 0 (all N=1..13)
  python -m swebench_unified.adversary weakness  nagini django__django-16256 $D/atk_N.py   -> exit 2 (all N=1..13)
  bash scripts/nagini_verify.sh $D/positive_control.py                                     -> exit 0
Attack builders: $D/build_attacks.py, $D/build_attacks2.py. Raw verifier output retained per attack at $D/res_atk_N.txt and $D/res_poscontrol.txt.

### ATTACK BATTERY (path -> class -> result; every one exit 2 = spec rejected):
atk_1  PREPATCH BUG. acreate delivers the produced object carrying the requested payload but never attaches it (pre-patch a<op> fell through to QuerySet's async method, which creates but does not run the related manager's attaching create). Behaviourally identical to the bundle's own model_prepatch.py acreate impl (diffed: same two statements, prose aside). Fails the membership clause. REJECTED. atk_2  WRONG CALLEE, payload downgraded. aupdate_or_create delegates to get_or_create -- agrees on identity, created flag and membership in EVERY branch, differs only by handing an already-present object back untouched. This is exactly the collapse refinement.md C2b and axiom_check.check_discriminates_payload claim the spec rejects.

REJECTED. atk_3  WRONG CALLEE, payload upgraded (opposite direction). aget_or_create delegates to update_or_create, overwriting an already-present object's payload. refinement.md B2b leg; would break F2P test_generic_async_aget_or_create (located tag must still read 'fatty') and P2P test_generic_get_or_create_when_exists. REJECTED. atk_4  PARTIAL DOMAIN. aget_or_create attaches a produced object only when requested >= 0. Correct on every F2P input (field=2/3, tags), wrong elsewhere; spec bounds `requested` nowhere. REJECTED. atk_5  DIVERGENCE / partial-correctness vacuity. aupdate_or_create spins in `while b: Invariant(b)` before delegating. The G-PANEL-1 witness class MustTerminate(3) is supposed to close; confirms the obligation is load-bearing, not decorative.

REJECTED. atk_6  CONTROL-FLOW EFFECT (double attach). aget_or_create attaches on BOTH paths -- re-attaching an already-present object (the real `self.add()` outside `if created` bug shape). Only the locate-path clause Implies(exists, ToSeq == Old(ToSeq)) separates it. REJECTED. atk_7  UNSAVED WRITE. aupdate_or_create's refresh path applies the payload to the DELIVERED object but never persists it (setattr with no obj.save()). Probes mapping.md §2's claim that Outcome.payload and mgr.payload are genuinely distinct observables.

REJECTED. atk_8  BOUNDARY ON PRE-STATE (highest-value probe). acreate attaches only when the related set is currently EMPTY -- satisfies the two async F2P tests that start empty, but F2P test_generic_async_acreate starts from bacon.tags with TWO tags and asserts acount()==3, so a patch refining this would NOT resolve. REJECTED (had it verified, this was the break). atk_9  WRONG IDENTITY ATTACHED. acreate appends the stale payload instead of obj -- satisfies a count-only observation, fails ...+PSeq(obj). REJECTED. atk_10 PARTIAL DOMAIN on the other op. aget_or_create attaches only into an empty related set (atk_8's shape moved to locate-or-produce).

REJECTED. atk_11 OFF-BY-ONE. acreate attaches the produced object twice (two through-rows); shows the exact ToSeq sequence equality bites where a set-style membership predicate would not. REJECTED. atk_12 PAYLOAD DROPPED ON PRODUCE. aget_or_create's produce path attaches and reports created=True but the object keeps the stale payload (kwargs dropped); breaks test_aget_or_create's new_simple.field==2. REJECTED. atk_13 MEASURE-LADDER PROBE. aupdate_or_create delegates to the sibling DEFERRED form aget_or_create -- wrong operation AND same MustTerminate measure (3->3). REJECTED, so the 3>2>1 ladder advertised in refinement.md A5 genuinely constrains the call graph.

A-LEG AUDIT (the assignment's focus). The axioms region is genuinely EMPTY -- grep for ContractOnly/Assume/Refute/sorry/admit in model.py returns only prose hits inside MustTerminate comments, so there is no A-consumed leg and no assumed postcondition to launder a proof. All 12 refinement.md legs tag as R (A1,A2,A3b,A4,A5), R+A-reference (A3,B1,C1) or R+I (B2,B2b,C2,C2b): no kind-3, consistent with §C's claim.
I checked every A-leg citation against the REAL source at base_commit 76e37513 in the upstream repository rather than trusting the prose:
  - ManyRelatedManager.create calls self.add(new_obj, through_defaults=...) after super().create -> A4's 'attach' ↔ members.append is faithful.
  - ManyRelatedManager.get_or_create and update_or_create both guard the attach with `if created: self.add(obj, ...)` -> B2/C2's 'attach only when produced' is faithful, and the two ARE identical on membership, which is why the payload legs must carry the discrimination.
  - QuerySet.get_or_create: the located path is `return self.get(**kwargs), False` with defaults consumed only on the create path -> B2b's Old-preserving payload clause is faithful.
  - QuerySet.update_or_create: located path runs `for k,v in resolve_callables(defaults): setattr(obj,k,v)` then obj.save(...) -> C2b's UNCONDITIONAL payload==requested is faithful, and the locate/refresh asymmetry is real in the repo, not an artifact.
  - RelatedManager (reverse FK) and GenericRelatedObjectManager delegate to the same QuerySet methods with the relation fields injected into kwargs -> the nine per-site wrappers really do collapse onto the three modelled contracts.
  - The one A-reference library fact (`await sync_to_async(f)(**kwargs) == f(**kwargs)`, result AND both effects) is executed against the REAL asgiref: `python axiom_check.py` -> exit 0, 200 randomized cases, and it self-checks that it DISCRIMINATES in both dimensions (no-attach prepatch shape rejected on membership; refresh-runs-locate collapse rejected on payload). atk_1/atk_2/atk_3 are the model-side duals of those two discrimination checks and both were rejected by the verifier, so the A-reference correspondence holds on both sides.
  - Omissions audited as genuinely unobservable: `through_defaults` addresses the through-ROW's fields (a different object from the one payload tracks) and no F2P/P2P assertion reads it; `.alters_data` is a template-safety marker with no test in either the 9 F2P or 53 P2P observing it (grepped). Both omissions are sound.

MODEL<->PATCH CORRESPONDENCE. The spec pins all five modelled observables (mgr.members as an ordered sequence, mgr.payload, Result().obj, Result().created, Result().payload) in EVERY branch of all six functions, plus termination. The battery is my attempt to find a free observable a same-spec rival could still move: I probed membership (atk_1,8,9,10,11), delivered-vs-persisted payload split (atk_7,12), both cross-delegation directions (atk_2,3,13), locate-path set stability (atk_6), an unconstrained-input partial domain (atk_4) and divergence (atk_5). Every one was rejected, which is what a functionally-total spec on its modelled state looks like. The residual trust points are the two PLAN §1.1 ones and are unchanged by this audit: the sync_to_async library fact (G-AX, executed above) and the R-abstraction itself (one int scalar for the defaults-writable field, int identity for the object) -- an infidelity there is out of G-EQ's reach and is what G-CONF's 100k live-DB probes cover.

**Verdict SOUND:** >= 5 (13) admissible same-spec attacks run to a real verdict, prepatch reproduced and rejected, positive control verifies, no CANDIDATE and therefore no non-resolving faithful patch. No evidence of verify => correct failing here. Nothing was capped, timed out or left unrun -- no attack summary contains 'inconclusive'.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: show the spec is too strong / drifts from real repo behavior (modeled function disagrees with the real callee on some input). Reference = base_commit 76e37513e2 worktree with patch.diff APPLIED (per instructions); base used only as a control.

SETUP: git worktree at base + `git apply patch.diff` (clean); second worktree left UNPATCHED as a control. Stood up an INDEPENDENT harness (not the bundle's conformance_check.py): settings.configure over sqlite, ContentType + 5 probe models mirroring the F2P models (SimpleModel/RelatedModel/ManyToManyModel + Tag/GenOwner GenericRelation, Tag.Meta.ordering mirroring TaggedItem's), real asyncio loop so the real sync_to_async hand-off actually executes. Shadow = model.py's six impl regions copied verbatim.

**RESULT:** NO DIVERGENCE FOUND. 312 boundary probes (3 relation kinds x 3 ops x deferred/immediate x both `exists` branches x pre-state sizes 0/1/2 x requested==/!=persisted x supply/no-supply) + 4000 seeded fuzz probes (seed 20260814, independent of the bundle's pinned 16256): 4312 compared, 0 disagreements on all five observables (delivered identity, created flag, delivered payload, FULL ordered post-state of the related set, persisted payload re-read from the DB). Coverage: 30/30 (kind,op,deferred,branch) cells reached, 30/30 also reached with a payload DIFFERING from the pre-state (so the payload columns are not vacuously equal; min 21 per cell).

EXACT F2P SHAPES reproduced against real patched code, each matching the spec clause: m2m aget_or_create create-leg (created=True, count=1, field=2) then locate-leg with through_defaults={'field':3} -> created=False, count=1, field STAYS 2, persisted 2 (matches B2b Old-preserving clause); m2m aupdate_or_create refresh-leg with defaults={'field':3} -> field=3, persisted=3 (matches C2b unconditional clause); generic aget_or_create locate delivers the OLD payload and leaves it persisted while aupdate_or_create on the SAME keyed row delivers/persists 777 -- the locate-vs-refresh asymmetry holds in both directions on real code; reverse-FK acreate() with no field -> field = declared default 0, and the object IS a member (matches the mapping.md degenerate-shape bridge).

OVER-STRENGTH PROBES (the places a too-strong spec would break) all HOLD on real code, across all 3 relation kinds: (a) no-op refresh where requested==persisted -> real still delivers/persists requested, so the unconditional `mgr.payload == requested` is not too strong; (b) update_or_create with NO defaults on an existing row -> delivers/persists the pre-existing value, matching the clause instantiated at requested=Old(payload) exactly as mapping.md scopes it; (c) get_or_create locate with defaults differing by 1000 -> real does NOT apply them, so the `Implies(exists, payload == Old(payload))` clause is not too strong; (d) through_defaults=None passed for real on the m2m create leg -> membership/payload unaffected, so omitting it from the model is sound; (e) a matching object existing GLOBALLY but NOT a member of this owner's set -> real related manager's scoped lookup creates a NEW object and attaches it, which is exactly the model's exists=False branch (the `exists` parameter correctly models set-scoped lookup, not global existence).

HARNESS FALSIFICATION CONTROLS (proving the probe can detect drift, so the clean result is not a vacuous pass): mutating the shadow's refresh form to hand a located object back untouched -> DIFF (shadow payload=9 vs real=46); mutating the shadow's acreate to deliver-without-attaching -> DIFF (shadow members=[1002] vs real=[1002,1003]). Both membership and payload dimensions are live. Reverse control against the UNPATCHED base worktree: all 9 deferred-form probes DIFF/ERR (m2m/fk report real members=[1002] where the model says [1002,1003]; generic errors) -- i.e. the divergence sits exactly on the patch delta and vanishes once patch.diff is applied, which is the correct sign and is NOT reportable as UNFAITHFUL per the instructions.

BUNDLE GATES re-run independently: axiom_check.py exit 0 (real asgiref sync_to_async, 200 cases, discriminates on both membership and payload); scripts/nagini_verify.sh model.py -> 'Verification successful' (21.1s, exit 0); adversary same-spec exit 0 for model.py and all three model_prepatch*.py, so the three G-DIFF twins do share the byte-identical spec region.

ONE SCOPED OBSERVATION (not a defect, disclosed for the record): if I force a produced FK/generic object to take a pk SMALLER than existing members' pks, the real set read back via order_by('pk') puts it FIRST while the model's append puts it LAST ([502,1002,1003] vs [1002,1003,502]). This is an artifact of the type bridge, not of the spec: mapping.md explicitly scopes the FK/generic members bridge to pks 'allocated from a strictly increasing counter, so pk order IS attachment order', and real Django AutoField pks are monotonic, so the shape is unreachable through the real API without hand-forcing a decreasing pk. The m2m bridge (through-row pk order = true attachment order) matches even under the forced pk. I therefore do not count it as a diverging input.

**CONCLUSION:** I could not construct any Requires-satisfying input on which the modelled functions disagree with the real patched callees. The spec's asymmetric payload clauses, its membership clauses, and its MustTerminate obligations are each true of the real code, and the MustTerminate obligation adds nothing the real wrappers do not already have (they always resolve), so it cannot exclude a correct implementation. FAITHFUL.

**ATTACK GOAL:** show the spec is too strong / drifts from real repo behavior (modeled function disagrees with the real callee on some input). Reference = base_commit 76e37513e2 worktree with patch.diff APPLIED (per instructions); base used only as a control.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Instance django__django-16256 (nagini). Spec view derived mechanically with markers.spec_view(model.py, nagini) into a per-instance output; a first pass wrote a generically named spec_view.py that was overwritten before it was read, so that output was discarded and every finding below comes from the re-run.

PROVENANCE / SAME-SPEC
- `python -m swebench_unified.adversary same-spec nagini django__django-16256 <copy of bundle model.py>` -> exit 0, "SAME - attack shares the bundle's exact specification". The spec region I screened is byte-identical to the bundle's.
- spec_view is idempotent (spec_view(spec_view(src))==spec_view(src)); ELISION_IMPL present; all 6 impl bodies elided (no `mgr.members.append`, no `return create(mgr...`, no `Outcome(obj...` survive).
- Critically, the mechanism-narrating impl comment in acreate ("Run the SAME-named immediate form on this accessor ... Because it is the related-set accessor's OWN immediate form, the produced object is attached") IS inside impl-start/impl-end and is confirmed ABSENT from the spec view. Had it been in the spec region it would have been a mechanism leak; the marker placement is correct.

### MECHANICAL SCREEN (leakage.screen, judged vs problem_statement only, hints_text excluded)
- passed=True, hard_failures=[], warnings=[].
- L1 diff markers: 0 of ('@@','diff --git','+++ ','--- ','\nindex ') in view.
- L1 gold-line reproduction: re-ran `_patch_changed_lines` with the length threshold lowered from 8 to 4 (stricter than the gate). ZERO normalized gold changed lines occur in the view. The only sub-8 fragments in the gold are three bare ')'.
- L2 paths: neither `django/db/models/fields/related_descriptors.py` nor `django/contrib/contenttypes/fields.py` nor their dotted module forms appear. Targeted vocabulary sweep all zero: sync_to_async, asgiref, alters_data, `async def`, `await `, through_defaults, kwargs, related_descriptors, contenttypes, ManyRelatedManager, RelatedManager, GenericRelatedObjectManager, QuerySet, content_type, object_id, router, db_manager, superclass, reverse, forward, m2m, generic. (grep -c "self.create"=3 is a substring artifact of `self.created` in Outcome.`__init__`, not the repo symbol.)
- L2/L5 symbol collision: patched distinctive symbols are {Child, create, get_or_create, update_or_create, acreate, aget_or_create, aupdate_or_create}. All six operation names occur in the view as identifiers, but every one appears VERBATIM in the public problem_statement (its title names acreate()/aget_or_create()/aupdate_or_create(); its body names create()/get_or_create()/update_or_create()), so they are already public via the task. `Child` (from a docstring hunk context) does not appear in the view at all.
- L3 narration: zero hits for bug/buggy/fix(ed|es)/patch(ed)/pre-patch/post-patch/regression/previously/incorrect(ly)/wrong/broken/unintended/unintentionally/mistake/instead of/rather than across all spec-view comments and docstrings.
- Hints-only vocabulary echo: hints_text minus problem_statement leaves only generic English (back, immediate, just, like, that, this, would) - no hints-only diagnosis or symbol is echoed.

SUBSTANTIVE (beyond-the-mechanical) RECONSTRUCTION TEST
The decisive fact is the direction of the information gradient. The public problem_statement is unusually generous here: it contains the patched file path `django/db/models/fields/related_descriptors.py`, the literal added import `from asgiref.sync import sync_to_async`, the literal added bodies `async def acreate(self, **kwargs): return await sync_to_async(self.create)(**kwargs)` and `acreate.alters_data = True` at two manager sites, and the diagnosis "they don't call create(), get_or_create(), and update_or_create() ... from a related manager but from the QuerySet ... We should add a proper versions to related managers." The spec view is strictly LESS informative than that:
- It never names the library primitive; the nearest phrase is "thread-offloading machinery" (line 128, axioms comment), which is weaker than the PS's verbatim `sync_to_async`.
- It never names a file, manager class, relation kind, or direction. Words generic/forward/reverse/m2m appear zero times.
- Multi-site structure is UNDER-stated, not leaked: the gold touches nine wrappers across three managers in TWO files, and the second file (contrib/contenttypes/fields.py) is NOT in the problem statement. The spec view models one abstract accessor with three operations x two forms and says nothing about relation-kind multiplicity or a second file, so it cannot be used to recover the contenttypes site.
- The discriminating content the spec does add - the membership requirement (a deferred form must attach a newly-produced object) and the locate-vs-refresh payload asymmetry (get_or_create hands an already-present object back untouched; update_or_create refreshes it) - is abstract DESIRED BEHAVIOUR, not the edit. The membership requirement is the same failure mode the PS already states publicly ("call ... from the QuerySet" rather than the related manager). The payload asymmetry is the documented semantics of the two same-named sync operations and appears nowhere in the gold diff (which only delegates), so it localizes no edit; it is spec strength that G-PANEL-1 requires, obtained without naming the mechanism.
A solver handed only the spec view would know it must make six operations behave as described; it would NOT learn the file, the import, the delegation code, or the contenttypes site. Nothing is recoverable that the problem_statement does not already hand over verbatim.

### OUT-OF-SCOPE OBSERVATIONS (not leakage; flagged for the owning gates, not as findings against this one)
1. Benchmark-meta vocabulary in spec-view comments: "F2P test" (docstring line 74 and acreate line 187) and "Nagini is a partial-correctness verifier". These reference the harness, not the gold edit - no test name or test content - so they are not leakage. Mildly unhygienic; 18 of 500 nagini bundles mention F2P, so it is a house-wide style point, not instance-specific.
2. meta.json region_hashes do NOT match a fresh markers.region_hashes() of the current model.py (all six entries differ, incl. spec_view faa8738 vs recomputed 13d672d). This is code-version drift, not bundle tampering: 14 of the first 15 verified nagini bundles mismatch identically, and the G-AX record's model.py sha 641a6595c77a still matches the on-disk model.py byte-for-byte. Belongs to G-HYGIENE/G-INTEGRITY, and it does not affect this gate because I screened the spec view recomputed from the actual model.py rather than trusting a stored hash.
3. In spec modes 1/2 the consumer view also carries meta.json modeled_functions, whose repo_location strings do name both patched files including contrib/contenttypes/fields.py. That is the mode's designed edit-localization layer (modes 0/1/2 grant localization by construction), not the spec view, so it is outside this gate's scope - noting it only so it is not mistaken for spec-view leakage later.

**CONCLUSION:** NO-LEAKAGE. Mechanical screen clean under a stricter-than-gate threshold, impl-region mechanism narration correctly elided, and no gold-edit fact (file, import, delegation code, second site, or site count) is recoverable from the spec view beyond what the public problem_statement already discloses verbatim.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
