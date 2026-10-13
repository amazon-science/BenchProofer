# P2 adversarial audit — django__django-14500

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_3.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # for); the result is a freshly-built list of the keys recorded as
     # no-longer-applied. No object is mutated, so nothing needs full permission.
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -70,22 +68,17 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # For replacement migrations, record each replaced key as no-longer-applied,
-    # in listed order.
-    i = 0
-    while i < len(replaced_keys):
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(replaced_keys))
-        # The recorded keys so far are exactly the first `i` replaced keys.
-        Invariant(ToSeq(result) == replaced_keys.take(i))
-        Invariant(MustTerminate(len(replaced_keys) - i + 1))
-        # invariants-end
-        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
-        result = result + [replaced_keys[i]]
-        i = i + 1
-    Assert(replaced_keys.take(i) == replaced_keys)
-    # Then record the migration's own key as no-longer-applied -- always.
-    result = result + [own_key]
+    if len(replaced_keys) > 0:
+        i = 0
+        while i < len(replaced_keys):
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= i and i <= len(replaced_keys))
+            Invariant(ToSeq(result) == replaced_keys.take(i))
+            Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
+            result = result + [replaced_keys[i]]
+            i = i + 1
+        Assert(replaced_keys.take(i) == replaced_keys)
+    else:
+        result = result + [own_key]
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # for); the result is a freshly-built list of the keys recorded as
     # no-longer-applied. No object is mutated, so nothing needs full permission.
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -70,22 +68,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # For replacement migrations, record each replaced key as no-longer-applied,
-    # in listed order.
-    i = 0
-    while i < len(replaced_keys):
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(replaced_keys))
-        # The recorded keys so far are exactly the first `i` replaced keys.
-        Invariant(ToSeq(result) == replaced_keys.take(i))
-        Invariant(MustTerminate(len(replaced_keys) - i + 1))
-        # invariants-end
-        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
-        result = result + [replaced_keys[i]]
-        i = i + 1
-    Assert(replaced_keys.take(i) == replaced_keys)
-    # Then record the migration's own key as no-longer-applied -- always.
     result = result + [own_key]
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # for); the result is a freshly-built list of the keys recorded as
     # no-longer-applied. No object is mutated, so nothing needs full permission.
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -70,22 +68,7 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # For replacement migrations, record each replaced key as no-longer-applied,
-    # in listed order.
-    i = 0
-    while i < len(replaced_keys):
-        # invariants-start
+    while True:
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(replaced_keys))
-        # The recorded keys so far are exactly the first `i` replaced keys.
-        Invariant(ToSeq(result) == replaced_keys.take(i))
-        Invariant(MustTerminate(len(replaced_keys) - i + 1))
-        # invariants-end
-        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
-        result = result + [replaced_keys[i]]
-        i = i + 1
-    Assert(replaced_keys.take(i) == replaced_keys)
-    # Then record the migration's own key as no-longer-applied -- always.
-    result = result + [own_key]
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # for); the result is a freshly-built list of the keys recorded as
     # no-longer-applied. No object is mutated, so nothing needs full permission.
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -70,22 +68,14 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # For replacement migrations, record each replaced key as no-longer-applied,
-    # in listed order.
+    result = result + [own_key]
     i = 0
     while i < len(replaced_keys):
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(replaced_keys))
-        # The recorded keys so far are exactly the first `i` replaced keys.
-        Invariant(ToSeq(result) == replaced_keys.take(i))
-        Invariant(MustTerminate(len(replaced_keys) - i + 1))
-        # invariants-end
-        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
+        Invariant(ToSeq(result) == PSeq(own_key) + replaced_keys.take(i))
+        Assert(PSeq(own_key) + replaced_keys.take(i) + PSeq(replaced_keys[i]) == PSeq(own_key) + replaced_keys.take(i + 1))
         result = result + [replaced_keys[i]]
         i = i + 1
-    Assert(replaced_keys.take(i) == replaced_keys)
-    # Then record the migration's own key as no-longer-applied -- always.
-    result = result + [own_key]
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # for); the result is a freshly-built list of the keys recorded as
     # no-longer-applied. No object is mutated, so nothing needs full permission.
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -70,22 +68,13 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # For replacement migrations, record each replaced key as no-longer-applied,
-    # in listed order.
     i = 0
-    while i < len(replaced_keys):
-        # invariants-start
+    while i < len(replaced_keys) - 1:
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(replaced_keys))
-        # The recorded keys so far are exactly the first `i` replaced keys.
         Invariant(ToSeq(result) == replaced_keys.take(i))
-        Invariant(MustTerminate(len(replaced_keys) - i + 1))
-        # invariants-end
-        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
         result = result + [replaced_keys[i]]
         i = i + 1
-    Assert(replaced_keys.take(i) == replaced_keys)
-    # Then record the migration's own key as no-longer-applied -- always.
     result = result + [own_key]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # for); the result is a freshly-built list of the keys recorded as
     # no-longer-applied. No object is mutated, so nothing needs full permission.
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -70,22 +68,14 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # For replacement migrations, record each replaced key as no-longer-applied,
-    # in listed order.
     i = 0
     while i < len(replaced_keys):
-        # invariants-start
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(replaced_keys))
-        # The recorded keys so far are exactly the first `i` replaced keys.
         Invariant(ToSeq(result) == replaced_keys.take(i))
-        Invariant(MustTerminate(len(replaced_keys) - i + 1))
-        # invariants-end
-        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
         result = result + [replaced_keys[i]]
         i = i + 1
-    Assert(replaced_keys.take(i) == replaced_keys)
-    # Then record the migration's own key as no-longer-applied -- always.
+    result = result + [own_key]
     result = result + [own_key]
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -56,7 +55,6 @@
     # for); the result is a freshly-built list of the keys recorded as
     # no-longer-applied. No object is mutated, so nothing needs full permission.
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -70,22 +68,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    # For replacement migrations, record each replaced key as no-longer-applied,
-    # in listed order.
-    i = 0
-    while i < len(replaced_keys):
-        # invariants-start
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(replaced_keys))
-        # The recorded keys so far are exactly the first `i` replaced keys.
-        Invariant(ToSeq(result) == replaced_keys.take(i))
-        Invariant(MustTerminate(len(replaced_keys) - i + 1))
-        # invariants-end
-        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
-        result = result + [replaced_keys[i]]
-        i = i + 1
-    Assert(replaced_keys.take(i) == replaced_keys)
-    # Then record the migration's own key as no-longer-applied -- always.
-    result = result + [own_key]
-    return result
+    raise Exception("boom")
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14500.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a stored migration is rolled back, the migration-state bookkeeper must
  record every bookkeeping key that should leave the "applied" set as a result
  of that roll-back. A migration is identified by its own key. Some migrations
  are *replacement* migrations: they stand in for a set of other (replaced)
  migrations whose individual keys are listed.

  Rolling a migration back records the following keys as no-longer-applied:

    * the keys of all migrations it stands in for (when it is a replacement;
      the run visits them in their listed order), AND
    * the migration's OWN key.

  The own key is recorded UNCONDITIONALLY -- a replacement migration that is
  rolled back leaves the applied set exactly like any other migration would,
  i.e. its own key is no longer applied, in addition to the keys it stands in
  for.
  A non-replacement migration (empty replaced-key list) records only its own
  key. So the recorded keys are precisely the replaced keys, in listed order,
  followed by the migration's own key.

Each migration bookkeeping key (a migration's identity key) is modelled as an
integer code; the list of keys recorded as no-longer-applied is a `List[int]`.
The replaced-key list is a `PSeq[int]`. The recorded-key sequence is the only
observable behaviour; it is modelled deeply as a front-recursive build, so no
callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (no axiomatized callees: recording a key as no-longer-applied is a pure
# append against the bookkeeper, modelled deeply below as the sequence of keys
# recorded. The schema-existence check and the underlying row deletion the
# bookkeeper performs are unchanged by, and independent of, which keys this
# operation chooses to record, and are unobserved by the behaviour pinned here.)
# axioms-end

# pure-start
# (no pure helpers needed: the recorded-key sequence is pinned exactly by
# sequence equality, which needs no recursive predicate.)
# pure-end

def keys_leaving_applied_set(own_key: int, replaced_keys: PSeq[int]) -> List[int]:
    # pre-conditions-start
    # `replaced_keys` is a pure sequence value (the keys this migration stands in
    # for); the result is a freshly-built list of the keys recorded as
    # no-longer-applied. No object is mutated, so nothing needs full permission.
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The recorded keys are exactly: each replaced key (in listed order),
    # followed by the migration's OWN key. The own key is appended
    # UNCONDITIONALLY -- whether or not the migration is a replacement. This is
    # the discriminating behaviour: a replacement migration's own key must leave
    # the applied set when it is rolled back, not only the keys it stands in for;
    # and it is recorded last, after the replaced ones.
    Ensures(ToSeq(Result()) == replaced_keys + PSeq(own_key))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # For replacement migrations, record each replaced key as no-longer-applied,
    # in listed order.
    i = 0
    while i < len(replaced_keys):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(replaced_keys))
        # The recorded keys so far are exactly the first `i` replaced keys.
        Invariant(ToSeq(result) == replaced_keys.take(i))
        # invariants-end
        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
        result = result + [replaced_keys[i]]
        i = i + 1
    Assert(replaced_keys.take(i) == replaced_keys)
    # Then record the migration's own key as no-longer-applied -- always.
    result = result + [own_key]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: keys_leaving_applied_set(own_key:int, replaced_keys:PSeq[int]) -> List[int] with Requires(True) and postcondition Ensures(ToSeq(Result()) == replaced_keys + PSeq(own_key)) plus Acc(list_pred(Result())). This pins the OUTPUT SEQUENCE EXACTLY (replaced keys in order, then own key, unconditionally). A fully-pinned functional postcondition leaves no room for a terminating verifying-but-wrong impl: any terminating verifying impl must return exactly replaced_keys++[own_key], which is the gold-equivalent (echo -> resolves). So the only realistic weakness vectors are partial-correctness vacuity (non-termination) and exceptional-exit vacuity. Nagini closes the exceptional-exit one (atk_7, rejected by the verifier); the non-termination one was probed only by a program Nagini's front end refused to translate, so it is left untested here.

PROTOCOL: copied model.py; edited ONLY the impl region (axioms/@Pure/Requires/Ensures/signature byte-identical). All 7 attacks + positive control confirmed SAME-SPEC (adversary same-spec exit 0). weakness verifications run concurrently in 3 background batches (<=3 JVM each).

### ATTACKS (all NOT-A-COUNTEREXAMPLE, exit 2 = spec rejected the wrong impl, except where noted below):
- atk_1 PREPATCH BUG (own_key recorded only inside else: for non-replacement): FAILED with 'Postcondition of keys_leaving_applied_set might not hold. Assertion (ToSeq(Result()) == (replaced_keys + PSeq(own_key))) might not hold' at Ensures line -> prepatch_reproduced=true, spec senses the discriminating A4 change.
- atk_2 PARTIAL-DOMAIN (drop replaced loop, return [own_key] only): FAILED postcondition for non-empty replaced_keys.
- atk_3 CONTROL-FLOW / NON-TERMINATION (while True with only Acc invariant, unreachable return): NOT JUDGED -- Nagini's front end refused the program at translation as 'dead.code' on the unreachable return, so it never reached the verifier and the spec never ruled on it (counts in neither tally); the attack SHAPE is unexpressible in Nagini's fragment, so this file did not exercise the spec's method-level MustTerminate(2), and whether that clause rejects a TRANSLATABLE diverging rival is a separate question this attack does not settle.
- atk_4 UNGROUNDED-ORACLE ECHO / REORDER (own_key FIRST then replaced, invariant ToSeq==PSeq(own_key)+take(i)): FAILED postcondition (sequence order pinned; PSeq(own)+replaced != replaced+PSeq(own)).
- atk_5 BOUNDARY off-by-one (loop to len-1, drops last replaced key): FAILED (invariant/postcondition).
- atk_6 duplicate own key appended twice: FAILED postcondition (result would be replaced++[own,own]).
- atk_7 EXCEPTIONAL-EXIT vacuity (raise before return): FAILED with 'Exhale might fail. Assertion "method raises no exceptions" might not hold' -- Nagini enforces no-exception, closing the exception-vacuity vector.

POSITIVE CONTROL: pos_control.py (exact gold impl) VERIFIES (Verification successful, 15.7s).

No attack came back CANDIDATE (same-spec AND verifies), so there is NO verifying-wrong-impl requiring a materialized faithful patch + run_resolve. The patches map is therefore empty by construction.

REFINEMENT.MD AUDIT (A-legs + correspondence): axioms-start/end region is EMPTY (no @ContractOnly callee) -> there is NO A-consumed leg and no axiom-soundness trust point. Legs: A1 (own_key:int <- (app_label,name)) = R; A2 (replaced_keys:PSeq[int] <- migration.replaces) = R; A3 (index loop <- for-loop over migration.replaces + subsumed truthiness guard) = R+I; A4 (unconditional final result+[own_key] <- record_unapplied(own) moved out of else:) = R+I -- the discriminating changed op, modeled DEEPLY as an A-reference (not hidden behind an axiom); A5 (return List[int] <- record_unapplied side-effect observed via applied_migrations()) = R. Section B confirms no kind-3 (unexpressible-changed-op) leg.

The A-reference correspondence is validated out-of-band by axiom_check.py, which I RAN: exit 0, 'abstract keys_leaving_applied_set build == real fixed unapply_migration recording ... on 8 boundary + exhaustive small enumeration + 40000 fuzz inputs; pre-patch differential confirmed'. The transcribed real-fixed branch in axiom_check.py (record each replaced key in order, then own key unconditionally) faithfully matches mapping.md's post-patch executor.py:253-257 hunk. conformance_check.py independently diffs the contract-stripped shadow against the REAL patched MigrationExecutor.unapply_migration (G-CONF lane).

VERDICT: SOUND. >=5 distinct wrong impls (7 built: prepatch, partial-domain, non-termination control-flow, echo/reorder ungrounded-oracle, boundary off-by-one, duplicate-append, exception-vacuity) all fail to verify; positive control verifies; every refinement.md leg is R/A-reference/I with no kind-3 and no consumed axiom; the A-reference deep-model correspondence holds under axiom_check.py. The exactly-pinned sequence postcondition admits no verifying incorrect implementation.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_3.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14500.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a stored migration is rolled back, the migration-state bookkeeper must
  record every bookkeeping key that should leave the "applied" set as a result
  of that roll-back. A migration is identified by its own key. Some migrations
  are *replacement* migrations: they stand in for a set of other (replaced)
  migrations whose individual keys are listed.

  Rolling a migration back records the following keys as no-longer-applied:

    * the keys of all migrations it stands in for (when it is a replacement;
      the run visits them in their listed order), AND
    * the migration's OWN key.

  The own key is recorded UNCONDITIONALLY -- a replacement migration that is
  rolled back leaves the applied set exactly like any other migration would,
  i.e. its own key is no longer applied, in addition to the keys it stands in
  for.
  A non-replacement migration (empty replaced-key list) records only its own
  key. So the recorded keys are precisely the replaced keys, in listed order,
  followed by the migration's own key.

Each migration bookkeeping key (a migration's identity key) is modelled as an
integer code; the list of keys recorded as no-longer-applied is a `List[int]`.
The replaced-key list is a `PSeq[int]`. The recorded-key sequence is the only
observable behaviour; it is modelled deeply as a front-recursive build, so no
callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (no axiomatized callees: recording a key as no-longer-applied is a pure
# append against the bookkeeper, modelled deeply below as the sequence of keys
# recorded. The schema-existence check and the underlying row deletion the
# bookkeeper performs are unchanged by, and independent of, which keys this
# operation chooses to record, and are unobserved by the behaviour pinned here.)
# axioms-end

# pure-start
# (no pure helpers needed: the recorded-key sequence is pinned exactly by
# sequence equality, which needs no recursive predicate.)
# pure-end

def keys_leaving_applied_set(own_key: int, replaced_keys: PSeq[int]) -> List[int]:
    # pre-conditions-start
    # `replaced_keys` is a pure sequence value (the keys this migration stands in
    # for); the result is a freshly-built list of the keys recorded as
    # no-longer-applied. No object is mutated, so nothing needs full permission.
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The recorded keys are exactly: each replaced key (in listed order),
    # followed by the migration's OWN key. The own key is appended
    # UNCONDITIONALLY -- whether or not the migration is a replacement. This is
    # the discriminating behaviour: a replacement migration's own key must leave
    # the applied set when it is rolled back, not only the keys it stands in for;
    # and it is recorded last, after the replaced ones.
    Ensures(ToSeq(Result()) == replaced_keys + PSeq(own_key))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    # For replacement migrations, record each replaced key as no-longer-applied,
    # in listed order.
    i = 0
    while i < len(replaced_keys):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(replaced_keys))
        # The recorded keys so far are exactly the first `i` replaced keys.
        Invariant(ToSeq(result) == replaced_keys.take(i))
        # invariants-end
        Assert(replaced_keys.take(i) + PSeq(replaced_keys[i]) == replaced_keys.take(i + 1))
        result = result + [replaced_keys[i]]
        i = i + 1
    Assert(replaced_keys.take(i) == replaced_keys)
    # Then record the migration's own key as no-longer-applied -- always.
    result = result + [own_key]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: keys_leaving_applied_set(own_key:int, replaced_keys:PSeq[int]) -> List[int] with Requires(True) and postcondition Ensures(ToSeq(Result()) == replaced_keys + PSeq(own_key)) plus Acc(list_pred(Result())). This pins the OUTPUT SEQUENCE EXACTLY (replaced keys in order, then own key, unconditionally). A fully-pinned functional postcondition leaves no room for a terminating verifying-but-wrong impl: any terminating verifying impl must return exactly replaced_keys++[own_key], which is the gold-equivalent (echo -> resolves). So the only realistic weakness vectors are partial-correctness vacuity (non-termination) and exceptional-exit vacuity. Nagini closes the exceptional-exit one (atk_7, rejected by the verifier); the non-termination one was probed only by a program Nagini's front end refused to translate, so it is left untested here.

PROTOCOL: copied model.py; edited ONLY the impl region (axioms/@Pure/Requires/Ensures/signature byte-identical). All 7 attacks + positive control confirmed SAME-SPEC (adversary same-spec exit 0). weakness verifications run concurrently in 3 background batches (<=3 JVM each).

### ATTACKS (all NOT-A-COUNTEREXAMPLE, exit 2 = spec rejected the wrong impl, except where noted below):
- atk_1 PREPATCH BUG (own_key recorded only inside else: for non-replacement): FAILED with 'Postcondition of keys_leaving_applied_set might not hold. Assertion (ToSeq(Result()) == (replaced_keys + PSeq(own_key))) might not hold' at Ensures line -> prepatch_reproduced=true, spec senses the discriminating A4 change.
- atk_2 PARTIAL-DOMAIN (drop replaced loop, return [own_key] only): FAILED postcondition for non-empty replaced_keys.
- atk_3 CONTROL-FLOW / NON-TERMINATION (while True with only Acc invariant, unreachable return): NOT JUDGED -- Nagini's front end refused the program at translation as 'dead.code' on the unreachable return, so it never reached the verifier and the spec never ruled on it (counts in neither tally); the attack SHAPE is unexpressible in Nagini's fragment, so this file did not exercise the spec's method-level MustTerminate(2), and whether that clause rejects a TRANSLATABLE diverging rival is a separate question this attack does not settle.
- atk_4 UNGROUNDED-ORACLE ECHO / REORDER (own_key FIRST then replaced, invariant ToSeq==PSeq(own_key)+take(i)): FAILED postcondition (sequence order pinned; PSeq(own)+replaced != replaced+PSeq(own)).
- atk_5 BOUNDARY off-by-one (loop to len-1, drops last replaced key): FAILED (invariant/postcondition).
- atk_6 duplicate own key appended twice: FAILED postcondition (result would be replaced++[own,own]).
- atk_7 EXCEPTIONAL-EXIT vacuity (raise before return): FAILED with 'Exhale might fail. Assertion "method raises no exceptions" might not hold' -- Nagini enforces no-exception, closing the exception-vacuity vector.

POSITIVE CONTROL: pos_control.py (exact gold impl) VERIFIES (Verification successful, 15.7s).

No attack came back CANDIDATE (same-spec AND verifies), so there is NO verifying-wrong-impl requiring a materialized faithful patch + run_resolve. The patches map is therefore empty by construction.

REFINEMENT.MD AUDIT (A-legs + correspondence): axioms-start/end region is EMPTY (no @ContractOnly callee) -> there is NO A-consumed leg and no axiom-soundness trust point. Legs: A1 (own_key:int <- (app_label,name)) = R; A2 (replaced_keys:PSeq[int] <- migration.replaces) = R; A3 (index loop <- for-loop over migration.replaces + subsumed truthiness guard) = R+I; A4 (unconditional final result+[own_key] <- record_unapplied(own) moved out of else:) = R+I -- the discriminating changed op, modeled DEEPLY as an A-reference (not hidden behind an axiom); A5 (return List[int] <- record_unapplied side-effect observed via applied_migrations()) = R. Section B confirms no kind-3 (unexpressible-changed-op) leg.

The A-reference correspondence is validated out-of-band by axiom_check.py, which I RAN: exit 0, 'abstract keys_leaving_applied_set build == real fixed unapply_migration recording ... on 8 boundary + exhaustive small enumeration + 40000 fuzz inputs; pre-patch differential confirmed'. The transcribed real-fixed branch in axiom_check.py (record each replaced key in order, then own key unconditionally) faithfully matches mapping.md's post-patch executor.py:253-257 hunk. conformance_check.py independently diffs the contract-stripped shadow against the REAL patched MigrationExecutor.unapply_migration (G-CONF lane).

VERDICT: SOUND. >=5 distinct wrong impls (7 built: prepatch, partial-domain, non-termination control-flow, echo/reorder ungrounded-oracle, boundary off-by-one, duplicate-append, exception-vacuity) all fail to verify; positive control verifies; every refinement.md leg is R/A-reference/I with no kind-3 and no consumed axiom; the A-reference deep-model correspondence holds under axiom_check.py. The exactly-pinned sequence postcondition admits no verifying incorrect implementation.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo drift) check for django__django-14500 (nagini). No divergence found; spec pins exactly the post-patch behavior.

SPEC (byte-identical, same-spec exit 0): keys_leaving_applied_set(own_key:int, replaced_keys:PSeq[int]) with Requires(True) and postcondition ToSeq(Result()) == replaced_keys + PSeq(own_key) — recorded keys = each replaced key in listed order, then the migration's own key UNCONDITIONALLY.

REAL CALLEE (post-patch MigrationExecutor.unapply_migration, executor.py:246, verified in a patched checkout at base_commit 8c3bd0b): `if migration.replaces: for app_label,name in migration.replaces: record_unapplied(app_label,name)` then `record_unapplied(migration.app_label, migration.name)` unconditionally. Observable = ordered record_unapplied call sequence = [replaced...] + [own]. Structurally identical to the spec.

### Machine facts
- same-spec nagini django__django-14500 <bundle model.py> => exit 0 (spec region confirmed byte-identical).
- nagini_verify.sh model.py => Verification successful (14.6s): spec non-vacuous; the impl builds exactly replaced_keys + [own_key].
- axiom_check.py (deep-model A-reference) => G-AX OK on 8 boundary + exhaustive(0..4 over 5-key universe) + 40000 fuzz; pre-patch differential confirmed.
- conformance_check.py run against the REAL gold-patched repo (PYTHONPATH to patched /tmp checkout) => G-CONF OK, 103915 inputs (10 boundary + 3905 exhaustive + 100000 fuzz seed 14500), ZERO disagreements. Inputs include duplicates ([10,10]), own-key-among-replaced ([5],own=5), negatives, empty replaced list.

ABSTRACTION FIDELITY: type bridge code_to_pair(k)=("app_%d"%k,"mig_%d"%k) is injective, so int-code equality == real key equality; the branch never inspects key content (only records), so the int abstraction loses nothing on the full Requires(True) domain. record_unapplied is a content-independent set-removal faithfully modeled as sequence append; fake=True only skips schema-editor work outside the modeled observable (state passes through unchanged, asserted). The empty-replaced (non-replacement) case records only own_key on both sides — matches. 

No input exists where the modeled function disagrees with the real repo callee. Spec is neither too strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over spec_view) passes with zero hard failures: no diff markers, no reproduced gold-patch line, no patched file path (executor.py) or module path, no spec-view identifier/comment embedding a patched repo symbol (record_unapplied, unapply_migration, replaces), and no bug/fix narration. Spec region confirmed elided at impl-start (impl body replaced by placeholder).

Semantic panel-3 judgment: the spec view discloses no more than the PUBLIC problem_statement. The problem_statement already states the corrected behavior verbatim: 'the MigrationExecutor mark[s] the squash migration as unapplied, too, not only the replaced migrations' — i.e. the migration's own/squash key must be recorded as unapplied IN ADDITION to the replaced keys. The spec view (docstring + Ensures ToSeq(Result()) == replaced_keys + PSeq(own_key)) is an abstracted restatement of exactly that public behavior: own key recorded unconditionally, in addition to replaced keys. The gold edit's discriminating content (moving record_unapplied of the own key out of the `else:` so it always runs) is fully abstracted — no repo symbols, no file path, no if/else control-flow structure, no diff. The only formalization detail beyond the prose (replaced keys in listed order, own key appended last) is a natural modeling choice, not gold-edit-specific leakage, and does not localize the edit beyond what a solver already knows from the public task. The spec legitimately encodes the target behavior the solver is asked to achieve — that is the intended spec, not a leak of the edit.

Nothing in the spec view leaks the gold edit beyond the public problem_statement (hints_text not consulted, per policy).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).