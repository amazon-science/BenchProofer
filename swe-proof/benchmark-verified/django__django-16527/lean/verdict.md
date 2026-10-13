# P2 adversarial audit — django__django-16527

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_buttonFlags pins all 7 ButtonFlags fields with '=' to exact boolean formulas under ∀ i (maximal frame discipline). Any verifying impl is provably extensionally equal to the gold on all 2^13 inputs, so no verify⇏correct witness can exist.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,7 +80,7 @@
   return {
     canChange := canChange,
     showDeleteLink := !i.isPopup && i.hasDeletePermission && i.change && i.showDelete,
-    showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && i.saveAs,
+    showSaveAsNew := !i.isPopup && i.hasChangePermission && i.change && i.saveAs,
     showSaveAndAddAnother := canSaveAndAddAnother,
     showSaveAndContinue := canSaveAndContinue,
     showSave := i.showSave && canSaveV,
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,7 +80,7 @@
   return {
     canChange := canChange,
     showDeleteLink := !i.isPopup && i.hasDeletePermission && i.change && i.showDelete,
-    showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && i.saveAs,
+    showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && i.saveAs && !i.add,
     showSaveAndAddAnother := canSaveAndAddAnother,
     showSaveAndContinue := canSaveAndContinue,
     showSave := i.showSave && canSaveV,
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,7 @@
       && i.showSaveAndAddAnother
   let canSaveAndContinue : Bool :=
     !i.isPopup && canSaveV && i.hasViewPermission && i.showSaveAndContinue
-  let canChange : Bool := i.hasChangePermission || i.hasEditableInlineAdminFormsets
+  let canChange : Bool := i.hasChangePermission && i.hasEditableInlineAdminFormsets
   return {
     canChange := canChange,
     showDeleteLink := !i.isPopup && i.hasDeletePermission && i.change && i.showDelete,
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
     showSaveAndAddAnother := canSaveAndAddAnother,
     showSaveAndContinue := canSaveAndContinue,
     showSave := i.showSave && canSaveV,
-    showClose := !(i.showSave && canSaveV)
+    showClose := !(i.showSave || canSaveV)
   }
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
     showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && i.saveAs,
     showSaveAndAddAnother := canSaveAndAddAnother,
     showSaveAndContinue := canSaveAndContinue,
-    showSave := i.showSave && canSaveV,
+    showSave := i.showSave,
     showClose := !(i.showSave && canSaveV)
   }
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
   let canChange : Bool := i.hasChangePermission || i.hasEditableInlineAdminFormsets
   return {
     canChange := canChange,
-    showDeleteLink := !i.isPopup && i.hasDeletePermission && i.change && i.showDelete,
+    showDeleteLink := !i.isPopup && i.hasDeletePermission && i.change,
     showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && i.saveAs,
     showSaveAndAddAnother := canSaveAndAddAnother,
     showSaveAndContinue := canSaveAndContinue,
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -68,23 +68,23 @@
 
 -- impl-start
 def implementation_buttonFlags (i : ButtonInput) : ButtonFlags := Id.run do
-  let canSaveV : Bool :=
+  let cc : Bool := i.hasChangePermission || i.hasEditableInlineAdminFormsets
+  let cs : Bool :=
     (i.hasChangePermission && i.change) || (i.hasAddPermission && i.add)
       || i.hasEditableInlineAdminFormsets
-  let canSaveAndAddAnother : Bool :=
-    i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && canSaveV
+  let ssac : Bool :=
+    !i.isPopup && cs && i.hasViewPermission && i.showSaveAndContinue
+  let saan : Bool :=
+    i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && cs
       && i.showSaveAndAddAnother
-  let canSaveAndContinue : Bool :=
-    !i.isPopup && canSaveV && i.hasViewPermission && i.showSaveAndContinue
-  let canChange : Bool := i.hasChangePermission || i.hasEditableInlineAdminFormsets
   return {
-    canChange := canChange,
+    canChange := cc,
     showDeleteLink := !i.isPopup && i.hasDeletePermission && i.change && i.showDelete,
     showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && i.saveAs,
-    showSaveAndAddAnother := canSaveAndAddAnother,
-    showSaveAndContinue := canSaveAndContinue,
-    showSave := i.showSave && canSaveV,
-    showClose := !(i.showSave && canSaveV)
+    showSaveAndAddAnother := saan,
+    showSaveAndContinue := ssac,
+    showSave := i.showSave && cs,
+    showClose := !(i.showSave && cs)
   }
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee carries semantics the proof must assume: the button-flag
-- computation is concrete boolean algebra over the input flags, reproduced
-- directly. The container plumbing (copying the context and updating it with the
-- derived keys) is orthogonal to the boolean logic and is not modeled. The proof
-- agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The bundle of boolean inputs that drive the button-visibility computation on
an admin change/add form. -/
structure ButtonInput where
  add : Bool
  change : Bool
  isPopup : Bool
  saveAs : Bool
  showSave : Bool
  showSaveAndAddAnother : Bool
  showSaveAndContinue : Bool
  hasAddPermission : Bool
  hasChangePermission : Bool
  hasViewPermission : Bool
  hasEditableInlineAdminFormsets : Bool
  hasDeletePermission : Bool
  showDelete : Bool
  deriving Repr, DecidableEq

/-- The bundle of derived button-visibility flags. -/
structure ButtonFlags where
  canChange : Bool
  showDeleteLink : Bool
  showSaveAsNew : Bool
  showSaveAndAddAnother : Bool
  showSaveAndContinue : Bool
  showSave : Bool
  showClose : Bool
  deriving Repr, DecidableEq

/-- Whether the form can be saved at all: editable with the relevant permission,
or it has editable inline formsets. -/
def canSave (i : ButtonInput) : Bool :=
  (i.hasChangePermission && i.change) || (i.hasAddPermission && i.add)
    || i.hasEditableInlineAdminFormsets
-- pure-end

-- post-conditions-start
/-- The derived flags are exactly the boolean formulas over the inputs. Every
output component is pinned to its input formula (frame discipline). The "save as
new" flag requires the add permission, since it creates a new object. -/
def problem_spec_buttonFlags (i : ButtonInput) (result : ButtonFlags) : Prop :=
  let cs := canSave i
  result.canChange = (i.hasChangePermission || i.hasEditableInlineAdminFormsets) ∧
  result.showDeleteLink =
    (!i.isPopup && i.hasDeletePermission && i.change && i.showDelete) ∧
  result.showSaveAsNew =
    (!i.isPopup && i.hasAddPermission && i.change && i.saveAs) ∧
  result.showSaveAndAddAnother =
    (i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && cs
      && i.showSaveAndAddAnother) ∧
  result.showSaveAndContinue =
    (!i.isPopup && cs && i.hasViewPermission && i.showSaveAndContinue) ∧
  result.showSave = (i.showSave && cs) ∧
  result.showClose = (!(i.showSave && cs))
-- post-conditions-end

-- impl-start
def implementation_buttonFlags (i : ButtonInput) : ButtonFlags := Id.run do
  let canSaveV : Bool :=
    (i.hasChangePermission && i.change) || (i.hasAddPermission && i.add)
      || i.hasEditableInlineAdminFormsets
  let canSaveAndAddAnother : Bool :=
    i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && canSaveV
      && i.showSaveAndAddAnother
  let canSaveAndContinue : Bool :=
    !i.isPopup && canSaveV && i.hasViewPermission && i.showSaveAndContinue
  let canChange : Bool := i.hasChangePermission || i.hasEditableInlineAdminFormsets
  return {
    canChange := canChange,
    showDeleteLink := !i.isPopup && i.hasDeletePermission && i.change && i.showDelete,
    showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && i.saveAs,
    showSaveAndAddAnother := canSaveAndAddAnother,
    showSaveAndContinue := canSaveAndContinue,
    showSave := i.showSave && canSaveV,
    showClose := !(i.showSave && canSaveV)
  }
-- impl-end

-- proof-start
theorem correct_buttonFlags :
    ∀ (i : ButtonInput),
    problem_spec_buttonFlags i (implementation_buttonFlags i) := by
  intro i
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

COMMANDS: same_spec via swebench_unified.markers.same_spec — all 8 files (pos_control, atk_1..7) => True. Verify: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4/batch.

### Results
- pos_control (gold): rc=0. #print axioms correct_buttonFlags => 'does not depend on any axioms' (clean).
- atk_1 PREPATCH BUG (showSaveAsNew gated on hasChangePermission): rc=1 (does NOT close). prepatch_reproduced=true.
- atk_2 partial-domain (showSaveAsNew && !i.add): rc=1.
- atk_3 boundary (canChange uses && instead of ||): rc=1.
- atk_4 control-flow-effect (showClose uses || instead of &&): rc=1.
- atk_5 dropped-conjunct (showSave := i.showSave, drops && canSaveV): rc=1.
- atk_6 ungrounded/dropped (showDeleteLink drops && i.showDelete): rc=1.
- atk_7 GENUINE ECHO (reordered lets/fields, extensionally identical to gold): rc=0. #print axioms => 'does not depend on any axioms' (clean).

6 DISTINCT wrong impls all FAIL to close against the fully-pinned spec — proof `refine ⟨rfl,...,rfl⟩` cannot discharge any field that diverges from its formula. The ONLY closing impls (pos_control, atk_7) are provably extensionally equal to the gold on all inputs. atk_7's faithful refined patch is therefore behaviorally identical to the gold patch — it is byte-identical to patch.diff (same has_change_permission→has_add_permission gate) and resolves by construction; there is no wrong-but-closing impl whose patch could fail to resolve.

A-LEG AUDIT (refinement.md/mapping.md): axioms region is comments-only; #print axioms confirms zero axiom dependence. Only callees are dict.get / Context.update (container plumbing, reproduced concretely or out of scope). All 12 refinement legs are R (rows 1,12 input reads/output struct) or I (rows 2-11 boolean algebra). NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible) legs. G-AX skip stub justified. Model↔patch correspondence holds: the single behavioral change (show_save_as_new gate) is reproduced concretely in impl-start (line 83) and pinned in the postcondition (line 58-59).

VERDICT SOUND: ≥6 distinct same-spec wrong impls attacked; none with a closing clean-axiom proof; the frame-disciplined spec forces extensional equality for every verifying impl.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_buttonFlags pins all 7 ButtonFlags fields with '=' to exact boolean formulas under ∀ i (maximal frame discipline). Any verifying impl is provably extensionally equal to the gold on all 2^13 inputs, so no verify⇏correct witness can exist.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee carries semantics the proof must assume: the button-flag
-- computation is concrete boolean algebra over the input flags, reproduced
-- directly. The container plumbing (copying the context and updating it with the
-- derived keys) is orthogonal to the boolean logic and is not modeled. The proof
-- agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The bundle of boolean inputs that drive the button-visibility computation on
an admin change/add form. -/
structure ButtonInput where
  add : Bool
  change : Bool
  isPopup : Bool
  saveAs : Bool
  showSave : Bool
  showSaveAndAddAnother : Bool
  showSaveAndContinue : Bool
  hasAddPermission : Bool
  hasChangePermission : Bool
  hasViewPermission : Bool
  hasEditableInlineAdminFormsets : Bool
  hasDeletePermission : Bool
  showDelete : Bool
  deriving Repr, DecidableEq

/-- The bundle of derived button-visibility flags. -/
structure ButtonFlags where
  canChange : Bool
  showDeleteLink : Bool
  showSaveAsNew : Bool
  showSaveAndAddAnother : Bool
  showSaveAndContinue : Bool
  showSave : Bool
  showClose : Bool
  deriving Repr, DecidableEq

/-- Whether the form can be saved at all: editable with the relevant permission,
or it has editable inline formsets. -/
def canSave (i : ButtonInput) : Bool :=
  (i.hasChangePermission && i.change) || (i.hasAddPermission && i.add)
    || i.hasEditableInlineAdminFormsets
-- pure-end

-- post-conditions-start
/-- The derived flags are exactly the boolean formulas over the inputs. Every
output component is pinned to its input formula (frame discipline). The "save as
new" flag requires the add permission, since it creates a new object. -/
def problem_spec_buttonFlags (i : ButtonInput) (result : ButtonFlags) : Prop :=
  let cs := canSave i
  result.canChange = (i.hasChangePermission || i.hasEditableInlineAdminFormsets) ∧
  result.showDeleteLink =
    (!i.isPopup && i.hasDeletePermission && i.change && i.showDelete) ∧
  result.showSaveAsNew =
    (!i.isPopup && i.hasAddPermission && i.change && i.saveAs) ∧
  result.showSaveAndAddAnother =
    (i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && cs
      && i.showSaveAndAddAnother) ∧
  result.showSaveAndContinue =
    (!i.isPopup && cs && i.hasViewPermission && i.showSaveAndContinue) ∧
  result.showSave = (i.showSave && cs) ∧
  result.showClose = (!(i.showSave && cs))
-- post-conditions-end

-- impl-start
def implementation_buttonFlags (i : ButtonInput) : ButtonFlags := Id.run do
  let canSaveV : Bool :=
    (i.hasChangePermission && i.change) || (i.hasAddPermission && i.add)
      || i.hasEditableInlineAdminFormsets
  let canSaveAndAddAnother : Bool :=
    i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && canSaveV
      && i.showSaveAndAddAnother
  let canSaveAndContinue : Bool :=
    !i.isPopup && canSaveV && i.hasViewPermission && i.showSaveAndContinue
  let canChange : Bool := i.hasChangePermission || i.hasEditableInlineAdminFormsets
  return {
    canChange := canChange,
    showDeleteLink := !i.isPopup && i.hasDeletePermission && i.change && i.showDelete,
    showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && i.saveAs,
    showSaveAndAddAnother := canSaveAndAddAnother,
    showSaveAndContinue := canSaveAndContinue,
    showSave := i.showSave && canSaveV,
    showClose := !(i.showSave && canSaveV)
  }
-- impl-end

-- proof-start
theorem correct_buttonFlags :
    ∀ (i : ButtonInput),
    problem_spec_buttonFlags i (implementation_buttonFlags i) := by
  intro i
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

COMMANDS: same_spec via swebench_unified.markers.same_spec — all 8 files (pos_control, atk_1..7) => True. Verify: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4/batch.

### Results
- pos_control (gold): rc=0. #print axioms correct_buttonFlags => 'does not depend on any axioms' (clean).
- atk_1 PREPATCH BUG (showSaveAsNew gated on hasChangePermission): rc=1 (does NOT close). prepatch_reproduced=true.
- atk_2 partial-domain (showSaveAsNew && !i.add): rc=1.
- atk_3 boundary (canChange uses && instead of ||): rc=1.
- atk_4 control-flow-effect (showClose uses || instead of &&): rc=1.
- atk_5 dropped-conjunct (showSave := i.showSave, drops && canSaveV): rc=1.
- atk_6 ungrounded/dropped (showDeleteLink drops && i.showDelete): rc=1.
- atk_7 GENUINE ECHO (reordered lets/fields, extensionally identical to gold): rc=0. #print axioms => 'does not depend on any axioms' (clean).

6 DISTINCT wrong impls all FAIL to close against the fully-pinned spec — proof `refine ⟨rfl,...,rfl⟩` cannot discharge any field that diverges from its formula. The ONLY closing impls (pos_control, atk_7) are provably extensionally equal to the gold on all inputs. atk_7's faithful refined patch is therefore behaviorally identical to the gold patch — it is byte-identical to patch.diff (same has_change_permission→has_add_permission gate) and resolves by construction; there is no wrong-but-closing impl whose patch could fail to resolve.

A-LEG AUDIT (refinement.md/mapping.md): axioms region is comments-only; #print axioms confirms zero axiom dependence. Only callees are dict.get / Context.update (container plumbing, reproduced concretely or out of scope). All 12 refinement legs are R (rows 1,12 input reads/output struct) or I (rows 2-11 boolean algebra). NO A-consumed, NO A-reference, NO kind-3 (changed-inexpressible) legs. G-AX skip stub justified. Model↔patch correspondence holds: the single behavioral change (show_save_as_new gate) is reproduced concretely in impl-start (line 83) and pinned in the postcondition (line 58-59).

VERDICT SOUND: ≥6 distinct same-spec wrong impls attacked; none with a closing clean-axiom proof; the frame-disciplined spec forces extensional equality for every verifying impl.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-16527, lean bundle.

Mechanical checks:
- same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) = True: the spec region (imports/axioms/pure/post-conditions) is byte-identical between the post- and pre-patch files; the diff lives only in impl+proof, as required.
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry/error).
- `#print axioms correct_buttonFlags` -> "does not depend on any axioms": the proof is genuine (no sorryAx), discharged by refl over the seven conjuncts.

Faithfulness vs the real callee. Modeled function = submit_row(context) at django/contrib/admin/templatetags/admin_modify.py:61-112 @ base_commit bd366ca2, plus the gold patch. Verified the base-commit source via `git show` and the gold patch (has_change_permission -> has_add_permission in show_save_as_new). Every clause of problem_spec_buttonFlags matches the real post-patch boolean formula exactly:
  canChange = has_change_permission or has_editable_inline_admin_formsets ✓
  showDeleteLink = not is_popup and has_delete_permission and change and show_delete ✓
  showSaveAsNew = not is_popup and has_add_permission and change and save_as ✓ (post-patch gate — the single behavioral change; matches gold)
  showSaveAndAddAnother = has_add_permission and not is_popup and (not save_as or add) and can_save and show_save_and_add_another ✓
  showSaveAndContinue = not is_popup and can_save and has_view_permission and show_save_and_continue ✓
  showSave = show_save and can_save ✓
  showClose = not (show_save and can_save) ✓
  with can_save = (has_change_permission and change) or (has_add_permission and add) or has_editable_inline_admin_formsets ✓.

No divergence exists on the modeled outputs: the spec pins each derived flag to precisely the formula the real function computes; a full 2^13 enumeration of the boolean inputs would find no disagreement (implementation_buttonFlags = the same formulas, and correct_buttonFlags proves equality). The only modeling gap is UNDER-modeling: the passthrough Context entries (the copied context, dict.get defaults as pure container plumbing) are dropped, which projects the output rather than over-constraining it — it cannot make the spec too strong. The context.get(k, True) defaults are input-sourcing details; the modeled field carries the boolean actually consumed, so no input drives a divergence.

Conclusion: the spec is not too strong and does not drift from the real post-patch behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, lean flavor) PASSES with zero hard_failures. Spec region is frozen: same_spec(Solution.lean, Solution_prepatch.lean)=True, so the edit lives entirely in the elided impl/proof regions, not the consumer spec view. Bundle is NOT relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md), meta G-LEAK=pass.

Semantic review beyond the lexical screen — no leak beyond the PUBLIC problem_statement:
- The gold edit is has_change_permission -> has_add_permission on the show_save_as_new line (admin_modify.py:102). The problem_statement ITSELF discloses this fix verbatim: it states 'you must put one more verification for this tag: and has_add_permission' and shows the rewrite. So the requirement that show_save_as_new be gated on has_add_permission is already solver-visible via the task, not just the spec.
- The post-condition `result.showSaveAsNew = (!i.isPopup && i.hasAddPermission && i.change && i.saveAs)` encodes the correct target behavior (a post-condition's legitimate job). The hasAddPermission gate matches the publicly-stated requirement; the decision to DROP hasChangePermission entirely ('checking only has_add_permission is enough') originates in hints_text, but the spec merely states the desired behavior and does not narrate the edit or reference the removed predicate as a change.
- Docstring comment ('the "save as new" flag requires the add permission, since it creates a new object') describes behavior, not the diff/pre-patch state; narration regex correctly does not fire. No diff markers, no patched file path admin_modify.py, no patched dotted module path, no gold-patch changed line reproduced verbatim in the spec view. `submit_row` appears only in auditor docs (mapping.md/refinement.md), which are not part of the consumer spec view.

The spec view reveals nothing about the gold edit that the public problem_statement does not already reveal.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
