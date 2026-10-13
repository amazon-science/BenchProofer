# P2 adversarial audit — django__django-12209

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1.py`, `atk2.py`, `atk5.py`, `atk6.py`, `atk7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk3.py`, `atk4.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
                        adding: bool, pk_has_default: bool) -> bool:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The routine reports an update exactly when an identifier is present, the
@@ -101,6 +99,6 @@
         force_insert_eff = True
     updated = False
     if pk_set and not force_insert_eff:
-        updated = update_matched_row()
+        updated = True
     return updated
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
                        adding: bool, pk_has_default: bool) -> bool:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The routine reports an update exactly when an identifier is present, the
@@ -97,7 +95,7 @@
     # post-conditions-end
     # impl-start
     force_insert_eff = force_insert
-    if (not pk_explicit) and (not force_insert) and adding and pk_has_default:
+    if pk_explicit and (not force_insert) and adding and pk_has_default:
         force_insert_eff = True
     updated = False
     if pk_set and not force_insert_eff:
```

Attack 3 — `atk3.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
                        adding: bool, pk_has_default: bool) -> bool:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The routine reports an update exactly when an identifier is present, the
@@ -99,8 +97,7 @@
     force_insert_eff = force_insert
     if (not pk_explicit) and (not force_insert) and adding and pk_has_default:
         force_insert_eff = True
-    updated = False
-    if pk_set and not force_insert_eff:
-        updated = update_matched_row()
+    matched = update_matched_row()
+    updated = pk_set and (not force_insert_eff) and matched
     return updated
     # impl-end
```

Attack 4 — `atk4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
                        adding: bool, pk_has_default: bool) -> bool:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The routine reports an update exactly when an identifier is present, the
@@ -99,8 +97,10 @@
     force_insert_eff = force_insert
     if (not pk_explicit) and (not force_insert) and adding and pk_has_default:
         force_insert_eff = True
-    updated = False
     if pk_set and not force_insert_eff:
         updated = update_matched_row()
+    else:
+        extra = update_matched_row()
+        updated = False
     return updated
     # impl-end
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
                        adding: bool, pk_has_default: bool) -> bool:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The routine reports an update exactly when an identifier is present, the
@@ -96,11 +94,5 @@
                     Result() == update_matched_row()))
     # post-conditions-end
     # impl-start
-    force_insert_eff = force_insert
-    if (not pk_explicit) and (not force_insert) and adding and pk_has_default:
-        force_insert_eff = True
-    updated = False
-    if pk_set and not force_insert_eff:
-        updated = update_matched_row()
-    return updated
+    return False
     # impl-end
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
                        adding: bool, pk_has_default: bool) -> bool:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The routine reports an update exactly when an identifier is present, the
@@ -97,7 +95,7 @@
     # post-conditions-end
     # impl-start
     force_insert_eff = force_insert
-    if (not pk_explicit) and (not force_insert) and adding and pk_has_default:
+    if (not pk_explicit) and (not force_insert) and pk_has_default:
         force_insert_eff = True
     updated = False
     if pk_set and not force_insert_eff:
```

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -74,7 +73,6 @@
                        adding: bool, pk_has_default: bool) -> bool:
     # pre-conditions-start
     Requires(True)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The routine reports an update exactly when an identifier is present, the
@@ -100,7 +98,7 @@
     if (not pk_explicit) and (not force_insert) and adding and pk_has_default:
         force_insert_eff = True
     updated = False
-    if pk_set and not force_insert_eff:
+    if not force_insert_eff:
         updated = update_matched_row()
     return updated
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12209.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single-table persistence routine decides how to store an instance that
  carries an identifier value. It may take a short-cut that *skips the
  existence check and goes straight to an insertion*. That short-cut is sound
  only when the instance is known to be genuinely new — when its identifier was
  produced by the field's own generating default rather than supplied by the
  caller.

  When instead the caller has explicitly supplied the identifier, the same
  identifier may already correspond to a stored row, so the short-cut MUST NOT
  be taken: the routine must first attempt to update the matching row, and
  insert only if none matched.

  Concretely the routine reports whether it updated an existing row. It reports
  an update exactly when an identifier is present, the insertion short-cut was
  not engaged, and the underlying update primitive matched a stored row. The
  short-cut engages only when ALL of the following hold together: the
  identifier was not caller-supplied, the caller did not already force an
  insertion, the instance is being added, and the identifier field carries a
  generating default.

The numerous data objects of the real routine are not touched by this change
and are abstracted away; the contract is entirely about the boolean decision of
whether the insertion short-cut engages. The unchanged update primitive (which
reports whether a stored row matched the identifier) is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def update_matched_row() -> bool:
    """Outcome reported by the unchanged update primitive for this instance's
    identifier: True iff it matched and updated a stored row. A single,
    instance-fixed observation (the primitive is only consulted along the
    update path). Provenance + executable soundness: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def shortcut_engaged(pk_explicit: bool, force_insert: bool, adding: bool,
                     pk_has_default: bool) -> bool:
    """Whether the straight-to-insertion short-cut engages. It engages exactly
    when ALL of the following hold: the identifier was not caller-supplied, the
    caller did not already force an insertion, the object is being added, and
    its identifier field carries a generating default. When the caller supplied
    the identifier explicitly the short-cut is suppressed, so a possibly
    pre-existing identifier is offered for update rather than blindly
    inserted."""
    return (not pk_explicit) and (not force_insert) and adding and pk_has_default


@Pure
def forces_insert(pk_explicit: bool, force_insert: bool, adding: bool,
                  pk_has_default: bool) -> bool:
    """The effective decision to go straight to insertion: either the caller
    forced it or the short-cut engaged. When this is False (and an identifier
    is present) the routine first attempts to update an existing row."""
    return force_insert or shortcut_engaged(pk_explicit, force_insert, adding,
                                            pk_has_default)
# pure-end


def store_single_table(pk_explicit: bool, force_insert: bool, pk_set: bool,
                       adding: bool, pk_has_default: bool) -> bool:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # The routine reports an update exactly when an identifier is present, the
    # effective straight-to-insertion decision is NOT taken, and the update
    # primitive matched a stored row. In particular, when the identifier was
    # caller-supplied, an identifier is present, and the caller did not force an
    # insertion, the short-cut is suppressed, so an existing row IS updated
    # rather than re-inserted.
    Ensures(Result() == (
        pk_set
        and not forces_insert(pk_explicit, force_insert, adding, pk_has_default)
        and update_matched_row()))
    # When the identifier was caller-supplied, an identifier-bearing instance
    # that the caller did not force to insert MUST be offered to the update
    # primitive: the short-cut is suppressed, so the reported outcome is exactly
    # that primitive's result (an existing row is updated, not blindly
    # re-inserted).
    Ensures(Implies(pk_explicit and pk_set and not force_insert,
                    Result() == update_matched_row()))
    # post-conditions-end
    # impl-start
    force_insert_eff = force_insert
    if (not pk_explicit) and (not force_insert) and adding and pk_has_default:
        force_insert_eff = True
    updated = False
    if pk_set and not force_insert_eff:
        updated = update_matched_row()
    return updated
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-12209 (nagini). SPEC SHAPE: complete total functional spec — Requires(True); post-1 pins Result() == (pk_set and not forces_insert(pk_explicit,force_insert,adding,pk_has_default) and update_matched_row()) as a boolean function of all 5 bool inputs plus the nullary @Pure axiom update_matched_row(); post-2 is a positive restatement.

### ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini django__django-12209 <path>):
- atk_prepatch.py (bundle model_prepatch.py; drops the not-pk_explicit conjunct): NOT-A-COUNTEREXAMPLE, verification failed (exit 2) — PREPATCH BUG REPRODUCED, spec senses it.
- atk1.py (partial-domain: return True on update path, drop update_matched_row() conjunct): does-not-verify (exit 2), rejected.
- atk2.py (boundary/inversion: pk_explicit instead of not pk_explicit in guard): does-not-verify (exit 2), rejected.
- atk5.py (constant: return False): does-not-verify (exit 2), rejected.
- atk6.py (dropped-conjunct: remove `adding` from shortcut guard): does-not-verify (exit 2), rejected.
- atk7.py (ungrounded-oracle echo: drop pk_set from update-path guard): does-not-verify (exit 2), rejected.
- atk3.py (CONTROL-FLOW-EFFECT: call update_matched_row() UNCONDITIONALLY, mask return by guards; same boolean): CANDIDATE (shares spec AND verifies, 9.1s).
- atk4.py (CONTROL-FLOW-EFFECT: also call update_matched_row() in the else/insert branch; same boolean): CANDIDATE (shares spec AND verifies, 8.9s).

MANDATED RESOLVE OF EVERY VERIFYING CANDIDATE (cmd: run_resolve via resolve_one.py; patches materialized against real /testbed/django/db/models/base.py extracted from swebench image, both `git apply --check` clean):
- GOLD patch.diff: completed=True resolved=True (baseline).
- atk3 faithful patch (patch_atk3.diff — unconditional `_do_update` call, return masked): completed=True RESOLVED=True → correct echo, NOT a weakness.
- atk4 faithful patch (patch_atk4.diff — extra `_do_update` in else branch): completed=True RESOLVED=True → correct echo, NOT a weakness.
The @Pure/nullary axiom makes relocating/duplicating the update_matched_row() call free in the model; faithfully refined that means the side-effecting real `_do_update` runs an extra (idempotent / zero-match) UPDATE query in states the gold never touches, but the returned `updated` bool and observable DB state stay gold-equivalent on the tested inputs, so both resolve. This is the sound outcome, not verify⇏correct.

REFINEMENT.MD LEG AUDIT (A-leg focus): A1=R (5 bools refine self-fields + raw param); A2=I (the fix — identical 4-conjunct guard, model not-pk_explicit ↔ repo not raw); A3=A-consumed (update_matched_row() ↔ unchanged Model.`_do_update`, base.py:892-917); A4=I (identical return updated). §C confirms NO kind-3 step and NO A-reference (no deep model; the only consumed axiom covers an UNCHANGED callee). A-consumed correspondence: axiom_check.py (G-AX) drives the REAL `_do_update` over a uuid4-defaulted structural twin of UUIDDefaultData, asserting True-for-present / False-for-absent — exactly the instance-fixed value the proof consumes along the update path. Correspondence holds and is executably grounded; the abstraction's only latent freedom (call-count/site of the side-effecting callee) is precisely what atk3/atk4 exercised, and both resolved.

**VERDICT:** SOUND. Prepatch bug + 5 wrong-boolean families all rejected by the verifier (spec discriminates); 2 control-flow-effect verifying candidates both had their materialized faithful patches RESOLVE under the official harness; positive control verifies (9.2s); gold resolves. No verifying wrong-impl patch failed to resolve → verify does not contradict correct here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1.py`, `atk2.py`, `atk5.py`, `atk6.py`, `atk7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk3.py`, `atk4.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12209.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single-table persistence routine decides how to store an instance that
  carries an identifier value. It may take a short-cut that *skips the
  existence check and goes straight to an insertion*. That short-cut is sound
  only when the instance is known to be genuinely new — when its identifier was
  produced by the field's own generating default rather than supplied by the
  caller.

  When instead the caller has explicitly supplied the identifier, the same
  identifier may already correspond to a stored row, so the short-cut MUST NOT
  be taken: the routine must first attempt to update the matching row, and
  insert only if none matched.

  Concretely the routine reports whether it updated an existing row. It reports
  an update exactly when an identifier is present, the insertion short-cut was
  not engaged, and the underlying update primitive matched a stored row. The
  short-cut engages only when ALL of the following hold together: the
  identifier was not caller-supplied, the caller did not already force an
  insertion, the instance is being added, and the identifier field carries a
  generating default.

The numerous data objects of the real routine are not touched by this change
and are abstracted away; the contract is entirely about the boolean decision of
whether the insertion short-cut engages. The unchanged update primitive (which
reports whether a stored row matched the identifier) is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def update_matched_row() -> bool:
    """Outcome reported by the unchanged update primitive for this instance's
    identifier: True iff it matched and updated a stored row. A single,
    instance-fixed observation (the primitive is only consulted along the
    update path). Provenance + executable soundness: mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def shortcut_engaged(pk_explicit: bool, force_insert: bool, adding: bool,
                     pk_has_default: bool) -> bool:
    """Whether the straight-to-insertion short-cut engages. It engages exactly
    when ALL of the following hold: the identifier was not caller-supplied, the
    caller did not already force an insertion, the object is being added, and
    its identifier field carries a generating default. When the caller supplied
    the identifier explicitly the short-cut is suppressed, so a possibly
    pre-existing identifier is offered for update rather than blindly
    inserted."""
    return (not pk_explicit) and (not force_insert) and adding and pk_has_default


@Pure
def forces_insert(pk_explicit: bool, force_insert: bool, adding: bool,
                  pk_has_default: bool) -> bool:
    """The effective decision to go straight to insertion: either the caller
    forced it or the short-cut engaged. When this is False (and an identifier
    is present) the routine first attempts to update an existing row."""
    return force_insert or shortcut_engaged(pk_explicit, force_insert, adding,
                                            pk_has_default)
# pure-end


def store_single_table(pk_explicit: bool, force_insert: bool, pk_set: bool,
                       adding: bool, pk_has_default: bool) -> bool:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # The routine reports an update exactly when an identifier is present, the
    # effective straight-to-insertion decision is NOT taken, and the update
    # primitive matched a stored row. In particular, when the identifier was
    # caller-supplied, an identifier is present, and the caller did not force an
    # insertion, the short-cut is suppressed, so an existing row IS updated
    # rather than re-inserted.
    Ensures(Result() == (
        pk_set
        and not forces_insert(pk_explicit, force_insert, adding, pk_has_default)
        and update_matched_row()))
    # When the identifier was caller-supplied, an identifier-bearing instance
    # that the caller did not force to insert MUST be offered to the update
    # primitive: the short-cut is suppressed, so the reported outcome is exactly
    # that primitive's result (an existing row is updated, not blindly
    # re-inserted).
    Ensures(Implies(pk_explicit and pk_set and not force_insert,
                    Result() == update_matched_row()))
    # post-conditions-end
    # impl-start
    force_insert_eff = force_insert
    if (not pk_explicit) and (not force_insert) and adding and pk_has_default:
        force_insert_eff = True
    updated = False
    if pk_set and not force_insert_eff:
        updated = update_matched_row()
    return updated
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-12209 (nagini). SPEC SHAPE: complete total functional spec — Requires(True); post-1 pins Result() == (pk_set and not forces_insert(pk_explicit,force_insert,adding,pk_has_default) and update_matched_row()) as a boolean function of all 5 bool inputs plus the nullary @Pure axiom update_matched_row(); post-2 is a positive restatement.

### ATTACKS (cmd: python -m swebench_unified.adversary weakness nagini django__django-12209 <path>):
- atk_prepatch.py (bundle model_prepatch.py; drops the not-pk_explicit conjunct): NOT-A-COUNTEREXAMPLE, verification failed (exit 2) — PREPATCH BUG REPRODUCED, spec senses it.
- atk1.py (partial-domain: return True on update path, drop update_matched_row() conjunct): does-not-verify (exit 2), rejected.
- atk2.py (boundary/inversion: pk_explicit instead of not pk_explicit in guard): does-not-verify (exit 2), rejected.
- atk5.py (constant: return False): does-not-verify (exit 2), rejected.
- atk6.py (dropped-conjunct: remove `adding` from shortcut guard): does-not-verify (exit 2), rejected.
- atk7.py (ungrounded-oracle echo: drop pk_set from update-path guard): does-not-verify (exit 2), rejected.
- atk3.py (CONTROL-FLOW-EFFECT: call update_matched_row() UNCONDITIONALLY, mask return by guards; same boolean): CANDIDATE (shares spec AND verifies, 9.1s).
- atk4.py (CONTROL-FLOW-EFFECT: also call update_matched_row() in the else/insert branch; same boolean): CANDIDATE (shares spec AND verifies, 8.9s).

MANDATED RESOLVE OF EVERY VERIFYING CANDIDATE (cmd: run_resolve via resolve_one.py; patches materialized against real /testbed/django/db/models/base.py extracted from swebench image, both `git apply --check` clean):
- GOLD patch.diff: completed=True resolved=True (baseline).
- atk3 faithful patch (patch_atk3.diff — unconditional `_do_update` call, return masked): completed=True RESOLVED=True → correct echo, NOT a weakness.
- atk4 faithful patch (patch_atk4.diff — extra `_do_update` in else branch): completed=True RESOLVED=True → correct echo, NOT a weakness.
The @Pure/nullary axiom makes relocating/duplicating the update_matched_row() call free in the model; faithfully refined that means the side-effecting real `_do_update` runs an extra (idempotent / zero-match) UPDATE query in states the gold never touches, but the returned `updated` bool and observable DB state stay gold-equivalent on the tested inputs, so both resolve. This is the sound outcome, not verify⇏correct.

REFINEMENT.MD LEG AUDIT (A-leg focus): A1=R (5 bools refine self-fields + raw param); A2=I (the fix — identical 4-conjunct guard, model not-pk_explicit ↔ repo not raw); A3=A-consumed (update_matched_row() ↔ unchanged Model.`_do_update`, base.py:892-917); A4=I (identical return updated). §C confirms NO kind-3 step and NO A-reference (no deep model; the only consumed axiom covers an UNCHANGED callee). A-consumed correspondence: axiom_check.py (G-AX) drives the REAL `_do_update` over a uuid4-defaulted structural twin of UUIDDefaultData, asserting True-for-present / False-for-absent — exactly the instance-fixed value the proof consumes along the update path. Correspondence holds and is executably grounded; the abstraction's only latent freedom (call-count/site of the side-effecting callee) is precisely what atk3/atk4 exercised, and both resolved.

**VERDICT:** SOUND. Prepatch bug + 5 wrong-boolean families all rejected by the verifier (spec discriminates); 2 control-flow-effect verifying candidates both had their materialized faithful patches RESOLVE under the official harness; positive control verifies (9.2s); gold resolves. No verifying wrong-impl patch failed to resolve → verify does not contradict correct here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. (1) Spec region byte-identical (same-spec exit 0) and model verifies (nagini_verify.sh, 6.89s). (2) The modeled store_single_table is a mechanical mirror of the real patched Model.`_save_table` decision at base_commit 5a68f024 + gold patch (added conjunct 'not raw and'): model pk_explicit<->repo raw, update_matched_row()<->`_do_update`, force_insert_eff<->re-assigned force_insert, Result()<->returned `updated`. (3) INDEPENDENT differential test (not the bundle's own conformance_check.py): I applied the gold patch to a base worktree, drove the REAL `_save_table` end-to-end over in-memory sqlite (two model classes: UUID-defaulted pk = pk_has_default True, CharField pk = pk_has_default False; stored/absent identifiers; INSERT fallback stubbed as abstracted), and compared its `updated` return against the modeled function over all 40 realizable boundary combos + 20,000 seed=12209 fuzzed inputs => 0 disagreements ('OK checked 20000 combos 40'). (4) Requires(True) admits unrealizable tuples (e.g. pk_has_default=True & pk_set=False, impossible when a defaulted pk always resolves a value), but the real routine cannot reach those states, so the extra spec claims produce no observable divergence — the spec is not too strong on any reachable input. The axiom over `_do_update` is A-consumed on an unchanged callee; both the empty-values probe (filtered.exists()) and the real non-empty-values path (filtered.`_update`(values)>0) agree for present/absent rows. Spec is a faithful, exact translation.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: adds the `not raw and` conjunct to the `_save_table` short-cut guard in django/db/models/base.py (suppress the straight-to-insert short-cut when the identifier was caller-supplied).

Mechanical screen (leakage.screen) over the computed spec_view returns passed=True, hard_failures=[]: no diff markers, no reproduced gold-patch line (>=8 chars), no patched file/module path, no patched-symbol identifier collision, no bug/fix narration words.

Semantic review confirms no leakage beyond the PUBLIC problem_statement:
- The problem_statement already states the observable behaviour and the fix's discriminator: saving an instance with an EXPLICIT pk value when the pk field has a default should UPDATE not blind-INSERT, and explicitly asks whether the behaviour should only change 'if an explicit pk value was not set on the model instance'. So the behavioural discriminator (caller-supplied identifier => suppress short-cut) is public.
- The spec view uses the ABSTRACT behavioural name `pk_explicit` ('identifier was caller-supplied rather than field-generated'), matching the public 'explicit pk value' framing — NOT the hints_text-only repo binding `raw`.
- Confirmed ABSENT from the spec view: `raw`, `_save_table`, `_do_update`, `loaddata`, `serial`, `base.py`, `pk_val`. The repo `raw` binding and file:line provenance appear ONLY in mapping.md/refinement.md (auditor docs, not part of the leakage-screened spec view).

The spec view reveals nothing about the gold edit beyond what the solver-visible problem_statement already discloses.

**Gold edit:** adds the `not raw and` conjunct to the `_save_table` short-cut guard in django/db/models/base.py (suppress the straight-to-insert short-cut when the identifier was caller-supplied).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
