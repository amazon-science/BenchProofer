# P2 adversarial audit — django__django-16527

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -53,7 +52,6 @@
 ) -> bool:
     # pre-conditions-start
     # All inputs are plain booleans; nothing is mutated.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The control is offered exactly when the page is not a popup, the viewer
@@ -66,7 +64,7 @@
     # post-conditions-end
     # impl-start
     show_save_as_new = (
-        not is_popup and may_add and editing_existing and save_as_enabled
+        not is_popup and may_change and editing_existing and save_as_enabled
     )
     return show_save_as_new
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -53,7 +52,6 @@
 ) -> bool:
     # pre-conditions-start
     # All inputs are plain booleans; nothing is mutated.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The control is offered exactly when the page is not a popup, the viewer
@@ -66,7 +64,7 @@
     # post-conditions-end
     # impl-start
     show_save_as_new = (
-        not is_popup and may_add and editing_existing and save_as_enabled
+        not is_popup and may_add and editing_existing
     )
     return show_save_as_new
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -53,7 +52,6 @@
 ) -> bool:
     # pre-conditions-start
     # All inputs are plain booleans; nothing is mutated.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The control is offered exactly when the page is not a popup, the viewer
@@ -66,7 +64,7 @@
     # post-conditions-end
     # impl-start
     show_save_as_new = (
-        not is_popup and may_add and editing_existing and save_as_enabled
+        not is_popup and may_add and editing_existing or save_as_enabled
     )
     return show_save_as_new
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -53,7 +52,6 @@
 ) -> bool:
     # pre-conditions-start
     # All inputs are plain booleans; nothing is mutated.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The control is offered exactly when the page is not a popup, the viewer
@@ -65,8 +63,5 @@
     )
     # post-conditions-end
     # impl-start
-    show_save_as_new = (
-        not is_popup and may_add and editing_existing and save_as_enabled
-    )
-    return show_save_as_new
+    return False
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -53,7 +52,6 @@
 ) -> bool:
     # pre-conditions-start
     # All inputs are plain booleans; nothing is mutated.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The control is offered exactly when the page is not a popup, the viewer
@@ -65,8 +63,8 @@
     )
     # post-conditions-end
     # impl-start
-    show_save_as_new = (
-        not is_popup and may_add and editing_existing and save_as_enabled
-    )
-    return show_save_as_new
+    if may_add:
+        return not is_popup and editing_existing and save_as_enabled
+    else:
+        return True
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -53,7 +52,6 @@
 ) -> bool:
     # pre-conditions-start
     # All inputs are plain booleans; nothing is mutated.
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The control is offered exactly when the page is not a popup, the viewer
@@ -66,7 +64,7 @@
     # post-conditions-end
     # impl-start
     show_save_as_new = (
-        not is_popup and may_add and editing_existing and save_as_enabled
+        is_popup and may_add and editing_existing and save_as_enabled
     )
     return show_save_as_new
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for django__django-16527.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the row of save/delete controls for an editable object is assembled, one
  of the controls offers to persist the current object as a brand-new object
  (a "save as new" action). Because that action creates a NEW stored object, it
  must be offered ONLY to a viewer who is permitted to add objects of this kind
  — possessing permission merely to alter the existing object is insufficient.

  Concretely, the "save as new" control is offered exactly when ALL of the
  following hold:

    * the page is not being shown in a stripped-down popup presentation,
    * the viewer holds the permission to ADD objects of this kind,
    * the page is editing an already-existing object (not creating one), and
    * the surrounding configuration enables the save-as-new affordance.

  In every other case the control is withheld. In particular, a viewer who may
  only change the existing object — but may not add — is NOT offered the
  control.

All of the inputs are independent booleans drawn from the rendering context
(the permission flags, the popup flag, the object-exists flag, and the
configuration flag). The control's visibility is itself a boolean. No callee is
axiomatized: the visibility is pure boolean logic over the context, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the control's visibility is pure boolean logic over the
# rendering context. Every input is a context boolean read directly; nothing is
# an unchanged opaque callee whose contract the proof would need.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def save_as_new_visible(
    is_popup: bool,
    may_add: bool,
    may_change: bool,
    editing_existing: bool,
    save_as_enabled: bool,
) -> bool:
    # pre-conditions-start
    # All inputs are plain booleans; nothing is mutated.
    # pre-conditions-end
    # post-conditions-start
    # The control is offered exactly when the page is not a popup, the viewer
    # may ADD, the page edits an existing object, and the affordance is enabled.
    # The permission to merely change is NOT part of the gating condition.
    Ensures(
        Result()
        == (not is_popup and may_add and editing_existing and save_as_enabled)
    )
    # post-conditions-end
    # impl-start
    show_save_as_new = (
        not is_popup and may_add and editing_existing and save_as_enabled
    )
    return show_save_as_new
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-16527 (nagini): the spec models save_as_new_visible over 5 boolean context flags. The postcondition is a TOTAL bare equality with NO Requires narrowing the domain: Ensures(Result() == (not is_popup and may_add and editing_existing and save_as_enabled)). This pins the output as an exact boolean function over the entire 2^5 input cube — leaving zero slack for any behaviorally-wrong impl to verify.

ATTACKS (all same-spec byte-identical, only impl region edited; all run via `python -m swebench_unified.adversary weakness nagini django__django-16527 <path>` with SBU_BENCHMARK_DIR=benchmark-verified; verify checks run concurrently ≤3 at a time):
- atk_1.py — prepatch bug, gates on may_change (byte-identical to model_prepatch.py impl region): same-spec EXIT=0; weakness EXIT=2 (NOT-A-COUNTEREXAMPLE, does not verify).
- atk_2.py — guard omission (drops save_as_enabled): same-spec EXIT=0; weakness EXIT=2.
- atk_3.py — operator swap (`... and editing_existing or save_as_enabled`): same-spec EXIT=0; weakness EXIT=2.
- atk_4.py — degenerate constant `return False`: same-spec EXIT=0; weakness EXIT=2.
- atk_5.py — partial-domain control-flow branch (correct on may_add branch, returns True otherwise): same-spec EXIT=0; weakness EXIT=2.
- atk_6.py — sign flip on is_popup (`is_popup and ...`): same-spec EXIT=0; weakness EXIT=2.

RESULT: 0 CANDIDATEs. No wrong impl both shares-spec AND verifies, so there is NO faithful patch to materialize/run through run_resolve — the resolve step is vacuous by protocol (patches={} accordingly). The one impl that DID come back CANDIDATE is atk_pos.py (byte-identical correct impl): weakness EXIT=0 (shares spec AND verifies, 7.2s); its refined patch IS the gold patch.diff (`has_change_permission`->`has_add_permission` at admin_modify.py:102-105), which resolves (G-RESOLVE). Positive control confirmed.

PREPATCH: reproduced — atk_1.py impl region is byte-identical to model_prepatch.py (may_change gating) and is rejected by the spec, confirming G-DIFF (the spec senses the bug on inputs where may_add != may_change, e.g. the F2P change-but-not-add viewer).

REFINEMENT.MD / A-LEG AUDIT: All legs A1–A6 are R or R+I; NO kind-3 (unexpressible-changed-op). This bundle genuinely has NO A-consumed axioms and NO A-reference deep-model callee — mapping.md §3 and refinement.md §B are correct: the modeled expression calls no library/utility callee; every operand is a context boolean read directly (identity R-refinement per mapping.md §2), operators are primitive and/not. The single nontrivial soundness obligation (modeled formula == gold expression) is discharged EXHAUSTIVELY by axiom_check.py over all 32 assignments: `SOUND: model formula == gold expression on all 32 boolean assignments; pre-patch differs from gold on 2 of them` (EXIT=0). Model↔patch correspondence holds: may_add↔has_add_permission, editing_existing↔change, save_as_enabled↔save_as, return↔ctx['show_save_as_new'].

VERDICT: SOUND. ≥5 distinct wrong impls (6) attempted and none verifies; no verify⇏correct gap exhibited. verify(model) constrains the impl to exactly the gold boolean function, and the gold patch resolves.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for django__django-16527.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the row of save/delete controls for an editable object is assembled, one
  of the controls offers to persist the current object as a brand-new object
  (a "save as new" action). Because that action creates a NEW stored object, it
  must be offered ONLY to a viewer who is permitted to add objects of this kind
  — possessing permission merely to alter the existing object is insufficient.

  Concretely, the "save as new" control is offered exactly when ALL of the
  following hold:

    * the page is not being shown in a stripped-down popup presentation,
    * the viewer holds the permission to ADD objects of this kind,
    * the page is editing an already-existing object (not creating one), and
    * the surrounding configuration enables the save-as-new affordance.

  In every other case the control is withheld. In particular, a viewer who may
  only change the existing object — but may not add — is NOT offered the
  control.

All of the inputs are independent booleans drawn from the rendering context
(the permission flags, the popup flag, the object-exists flag, and the
configuration flag). The control's visibility is itself a boolean. No callee is
axiomatized: the visibility is pure boolean logic over the context, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the control's visibility is pure boolean logic over the
# rendering context. Every input is a context boolean read directly; nothing is
# an unchanged opaque callee whose contract the proof would need.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def save_as_new_visible(
    is_popup: bool,
    may_add: bool,
    may_change: bool,
    editing_existing: bool,
    save_as_enabled: bool,
) -> bool:
    # pre-conditions-start
    # All inputs are plain booleans; nothing is mutated.
    # pre-conditions-end
    # post-conditions-start
    # The control is offered exactly when the page is not a popup, the viewer
    # may ADD, the page edits an existing object, and the affordance is enabled.
    # The permission to merely change is NOT part of the gating condition.
    Ensures(
        Result()
        == (not is_popup and may_add and editing_existing and save_as_enabled)
    )
    # post-conditions-end
    # impl-start
    show_save_as_new = (
        not is_popup and may_add and editing_existing and save_as_enabled
    )
    return show_save_as_new
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-16527 (nagini): the spec models save_as_new_visible over 5 boolean context flags. The postcondition is a TOTAL bare equality with NO Requires narrowing the domain: Ensures(Result() == (not is_popup and may_add and editing_existing and save_as_enabled)). This pins the output as an exact boolean function over the entire 2^5 input cube — leaving zero slack for any behaviorally-wrong impl to verify.

ATTACKS (all same-spec byte-identical, only impl region edited; all run via `python -m swebench_unified.adversary weakness nagini django__django-16527 <path>` with SBU_BENCHMARK_DIR=benchmark-verified; verify checks run concurrently ≤3 at a time):
- atk_1.py — prepatch bug, gates on may_change (byte-identical to model_prepatch.py impl region): same-spec EXIT=0; weakness EXIT=2 (NOT-A-COUNTEREXAMPLE, does not verify).
- atk_2.py — guard omission (drops save_as_enabled): same-spec EXIT=0; weakness EXIT=2.
- atk_3.py — operator swap (`... and editing_existing or save_as_enabled`): same-spec EXIT=0; weakness EXIT=2.
- atk_4.py — degenerate constant `return False`: same-spec EXIT=0; weakness EXIT=2.
- atk_5.py — partial-domain control-flow branch (correct on may_add branch, returns True otherwise): same-spec EXIT=0; weakness EXIT=2.
- atk_6.py — sign flip on is_popup (`is_popup and ...`): same-spec EXIT=0; weakness EXIT=2.

RESULT: 0 CANDIDATEs. No wrong impl both shares-spec AND verifies, so there is NO faithful patch to materialize/run through run_resolve — the resolve step is vacuous by protocol (patches={} accordingly). The one impl that DID come back CANDIDATE is atk_pos.py (byte-identical correct impl): weakness EXIT=0 (shares spec AND verifies, 7.2s); its refined patch IS the gold patch.diff (`has_change_permission`->`has_add_permission` at admin_modify.py:102-105), which resolves (G-RESOLVE). Positive control confirmed.

PREPATCH: reproduced — atk_1.py impl region is byte-identical to model_prepatch.py (may_change gating) and is rejected by the spec, confirming G-DIFF (the spec senses the bug on inputs where may_add != may_change, e.g. the F2P change-but-not-add viewer).

REFINEMENT.MD / A-LEG AUDIT: All legs A1–A6 are R or R+I; NO kind-3 (unexpressible-changed-op). This bundle genuinely has NO A-consumed axioms and NO A-reference deep-model callee — mapping.md §3 and refinement.md §B are correct: the modeled expression calls no library/utility callee; every operand is a context boolean read directly (identity R-refinement per mapping.md §2), operators are primitive and/not. The single nontrivial soundness obligation (modeled formula == gold expression) is discharged EXHAUSTIVELY by axiom_check.py over all 32 assignments: `SOUND: model formula == gold expression on all 32 boolean assignments; pre-patch differs from gold on 2 of them` (EXIT=0). Model↔patch correspondence holds: may_add↔has_add_permission, editing_existing↔change, save_as_enabled↔save_as, return↔ctx['show_save_as_new'].

VERDICT: SOUND. ≥5 distinct wrong impls (6) attempted and none verifies; no verify⇏correct gap exhibited. verify(model) constrains the impl to exactly the gold boolean function, and the gold patch resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is a pure boolean postcondition: Result() == (not is_popup and may_add and editing_existing and save_as_enabled). Per mapping.md the model parameters bind identity to context flags: may_add<->has_add_permission, editing_existing<->change, save_as_enabled<->save_as, is_popup<->is_popup (may_change carried only for byte-identical prepatch spec, unused). The gold patch changes submit_row's 'show_save_as_new' entry to exactly 'not is_popup and has_add_permission and change and save_as' — verbatim the modeled formula. I applied patch.diff to a base_commit worktree and ran a differential of the model postcondition against the REAL patched submit_row()['show_save_as_new'] over the FULL input space: the 2^5 modeled flags crossed with all 2^8 surrounding context flags (add/view/delete perms, inline-formset, show_* options) = 8192 assignments. Zero mismatches. The surrounding flags provably do not affect the observed entry (the gold expression only conjoins the four modeled operands). No callee is axiomatized; there is no over-approximation surface. The spec is neither too strong nor drifted — it is exactly the real behavior. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The spec view (model.py Ensures clause, refinement.md A3, mapping.md §1) frames the modeled behavior as gating the 'save as new' control on ADD permission (may_add) rather than change permission. This IS the discriminating content of the gold patch (admin_modify.py:102, `+ and has_add_permission`). However, the PUBLIC problem_statement already discloses this edit in full: it names the file 'django/contrib/admin/templatetags/admin_modify.py' line 102, states verbatim 'you must put one more verification for this tag: "and has_add_permission", because "save_as_new" is a add modification', and shows the rewritten code block with `and has_add_permission` added. The gold fix is therefore fully public independent of the spec. Nothing in the spec view (model.py/refinement.md/mapping.md) exposes the gold edit BEYOND the public problem_statement. The spec is a legitimate restatement of publicly-known desired behavior. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
