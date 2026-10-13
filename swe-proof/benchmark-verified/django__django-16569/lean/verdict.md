# P2 adversarial audit — django__django-16569

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,6 +58,7 @@
   result = some (canDelete && (canDeleteExtra || withinInitial index ifc))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_addFields
     (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat) :
@@ -67,14 +68,11 @@
     if canDeleteExtra then
       addControl := true
     else
-      -- The within-prefix test only makes sense for an item that has a concrete
-      -- position; a positionless item is treated as outside the prefix.
       match index with
       | some i => if i < ifc then addControl := true
-      | none   => pure ()
+      | none   => return none
   return some addControl
 -- impl-end
-
 -- proof-start
 theorem correct_addFields :
     ∀ (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat),
@@ -88,4 +86,6 @@
       | (rename_i val; by_cases h : val < ifc <;>
           simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
             pure] <;> rfl)
+      | (simp_all [Id.run] <;> try omega)
+      | decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,23 +58,18 @@
   result = some (canDelete && (canDeleteExtra || withinInitial index ifc))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_addFields
     (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat) :
     Option Bool := Id.run do
   let mut addControl := false
   if canDelete then
-    if canDeleteExtra then
-      addControl := true
-    else
-      -- The within-prefix test only makes sense for an item that has a concrete
-      -- position; a positionless item is treated as outside the prefix.
-      match index with
-      | some i => if i < ifc then addControl := true
-      | none   => pure ()
+    match index with
+    | some i => if i < ifc then addControl := true
+    | none   => pure ()
   return some addControl
 -- impl-end
-
 -- proof-start
 theorem correct_addFields :
     ∀ (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat),
@@ -88,4 +83,6 @@
       | (rename_i val; by_cases h : val < ifc <;>
           simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
             pure] <;> rfl)
+      | (simp_all [Id.run] <;> try omega)
+      | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,6 +58,7 @@
   result = some (canDelete && (canDeleteExtra || withinInitial index ifc))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_addFields
     (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat) :
@@ -67,14 +68,11 @@
     if canDeleteExtra then
       addControl := true
     else
-      -- The within-prefix test only makes sense for an item that has a concrete
-      -- position; a positionless item is treated as outside the prefix.
       match index with
-      | some i => if i < ifc then addControl := true
+      | some i => if i <= ifc then addControl := true
       | none   => pure ()
   return some addControl
 -- impl-end
-
 -- proof-start
 theorem correct_addFields :
     ∀ (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat),
@@ -88,4 +86,6 @@
       | (rename_i val; by_cases h : val < ifc <;>
           simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
             pure] <;> rfl)
+      | (simp_all [Id.run] <;> try omega)
+      | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,6 +58,7 @@
   result = some (canDelete && (canDeleteExtra || withinInitial index ifc))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_addFields
     (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat) :
@@ -67,14 +68,11 @@
     if canDeleteExtra then
       addControl := true
     else
-      -- The within-prefix test only makes sense for an item that has a concrete
-      -- position; a positionless item is treated as outside the prefix.
       match index with
       | some i => if i < ifc then addControl := true
-      | none   => pure ()
+      | none   => addControl := true
   return some addControl
 -- impl-end
-
 -- proof-start
 theorem correct_addFields :
     ∀ (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat),
@@ -88,4 +86,6 @@
       | (rename_i val; by_cases h : val < ifc <;>
           simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
             pure] <;> rfl)
+      | (simp_all [Id.run] <;> try omega)
+      | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,23 +58,13 @@
   result = some (canDelete && (canDeleteExtra || withinInitial index ifc))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_addFields
     (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat) :
     Option Bool := Id.run do
-  let mut addControl := false
-  if canDelete then
-    if canDeleteExtra then
-      addControl := true
-    else
-      -- The within-prefix test only makes sense for an item that has a concrete
-      -- position; a positionless item is treated as outside the prefix.
-      match index with
-      | some i => if i < ifc then addControl := true
-      | none   => pure ()
-  return some addControl
+  return some canDelete
 -- impl-end
-
 -- proof-start
 theorem correct_addFields :
     ∀ (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat),
@@ -88,4 +78,6 @@
       | (rename_i val; by_cases h : val < ifc <;>
           simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
             pure] <;> rfl)
+      | (simp_all [Id.run] <;> try omega)
+      | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,23 +58,14 @@
   result = some (canDelete && (canDeleteExtra || withinInitial index ifc))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_addFields
     (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat) :
     Option Bool := Id.run do
-  let mut addControl := false
-  if canDelete then
-    if canDeleteExtra then
-      addControl := true
-    else
-      -- The within-prefix test only makes sense for an item that has a concrete
-      -- position; a positionless item is treated as outside the prefix.
-      match index with
-      | some i => if i < ifc then addControl := true
-      | none   => pure ()
-  return some addControl
+  let inPrefix := match index with | some i => decide (i < ifc) | none => false
+  return some (canDeleteExtra || inPrefix)
 -- impl-end
-
 -- proof-start
 theorem correct_addFields :
     ∀ (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat),
@@ -88,4 +79,6 @@
       | (rename_i val; by_cases h : val < ifc <;>
           simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
             pure] <;> rfl)
+      | (simp_all [Id.run] <;> try omega)
+      | decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,23 +58,13 @@
   result = some (canDelete && (canDeleteExtra || withinInitial index ifc))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_addFields
     (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat) :
     Option Bool := Id.run do
-  let mut addControl := false
-  if canDelete then
-    if canDeleteExtra then
-      addControl := true
-    else
-      -- The within-prefix test only makes sense for an item that has a concrete
-      -- position; a positionless item is treated as outside the prefix.
-      match index with
-      | some i => if i < ifc then addControl := true
-      | none   => pure ()
-  return some addControl
+  return some false
 -- impl-end
-
 -- proof-start
 theorem correct_addFields :
     ∀ (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat),
@@ -88,4 +78,6 @@
       | (rename_i val; by_cases h : val < ifc <;>
           simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
             pure] <;> rfl)
+      | (simp_all [Id.run] <;> try omega)
+      | decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding, for a single item in a collection, whether an optional "remove me"
control should be attached to that item.

The collection has two configuration booleans:

  * whether removal is permitted at all, and
  * whether items beyond the pre-populated prefix may also be removed.

Each item is identified by an OPTIONAL position. Some items have a concrete
position (a natural-number offset); others are positionless (a standalone
template item that does not occupy a slot in the collection). The collection also
knows how many leading items are pre-populated.

The removal control is attached exactly when removal is permitted AND either
extra (non-pre-populated) items may be removed too, OR the item sits inside the
pre-populated prefix — i.e. it has a concrete position strictly below the
pre-populated count. A positionless item is, by definition, not inside that
prefix.

The decision is TOTAL: it is defined for every item, including a positionless
one, and never fails to produce an answer.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The decision is a pure
-- boolean computation over the two configuration booleans, the item's optional
-- position, and the pre-populated count; the downstream act of materializing the
-- control object is abstracted to the boolean "was the control attached". Hence
-- no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- An item is inside the pre-populated prefix iff it has a concrete position
strictly below the pre-populated count. A positionless item is never inside it. -/
def withinInitial (index : Option Nat) (ifc : Nat) : Bool :=
  match index with
  | some i => decide (i < ifc)
  | none   => false
-- pure-end

-- post-conditions-start
/-- The outcome is TOTAL and fully pinned to the inputs.

  * `result = some b` always (the decision never fails to produce an answer — in
    particular it is defined for a positionless item); there is no `none` outcome.
  * `b` is true exactly when removal is permitted AND either extra items may be
    removed, OR the item is inside the pre-populated prefix (`withinInitial`).

No output component is left free: the outcome is `some` of the exact boolean
combination of the inputs. -/
def problem_spec_addFields
    (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat)
    (result : Option Bool) : Prop :=
  result = some (canDelete && (canDeleteExtra || withinInitial index ifc))
-- post-conditions-end

-- impl-start
def implementation_addFields
    (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat) :
    Option Bool := Id.run do
  let mut addControl := false
  if canDelete then
    if canDeleteExtra then
      addControl := true
    else
      -- The within-prefix test only makes sense for an item that has a concrete
      -- position; a positionless item is treated as outside the prefix.
      match index with
      | some i => if i < ifc then addControl := true
      | none   => pure ()
  return some addControl
-- impl-end

-- proof-start
theorem correct_addFields :
    ∀ (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat),
      problem_spec_addFields canDelete canDeleteExtra index ifc
        (implementation_addFields canDelete canDeleteExtra index ifc) := by
  intro canDelete canDeleteExtra index ifc
  unfold problem_spec_addFields implementation_addFields withinInitial
  cases canDelete <;> cases canDeleteExtra <;> cases index <;>
    first
      | rfl
      | (rename_i val; by_cases h : val < ifc <;>
          simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
            pure] <;> rfl)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_addFields is a TOTAL FUNCTIONAL EQUALITY: result = some (canDelete && (canDeleteExtra || withinInitial index ifc)), with withinInitial (some i) ifc = decide (i<ifc), withinInitial none _ = false. This pins result to exactly one value for every input, so ANY impl whose correct_addFields closes must be extensionally equal to gold = precisely the patched add_fields behavior. There is no closing-but-non-resolving alternative in principle. All 8 files confirmed same_spec=True vs Solution.lean via swebench_unified.markers.same_spec (spec regions byte-identical).

 Verify cmd: `bash scripts/lean_verify.sh <file>`. Attacks run concurrently as background jobs, <=4 at a time (two batches). 

POSITIVE CONTROL: pos.lean (gold Solution.lean verbatim) -> exit=0 (verifies, no sorry). pos_ax.lean (pos + `#print axioms correct_addFields`) -> exit=0, output: "'correct_addFields' depends on axioms: [propext]" — CLEAN (no sorryAx). 

PREPATCH BUG REPRODUCED: atk_1 encodes the prepatch semantics (returns none for the positionless can_delete=True,can_delete_extra=False,index=none case, modeling the None<int TypeError). same_spec=True, exit=1 (proof does NOT close): goal reduces to `False` on case true.false.none (spec demands some false, impl gives none). This is exactly the prepatch Solution_prepatch.lean behavior and the F2P-discriminating input.

7 DISTINCT WRONG IMPLS, each same_spec=True, each with a genuine gold-style closing-proof attempt (full case split + by_cases + simp/omega/decide fallbacks); ALL FAIL TO CLOSE (exit=1):
  atk_1 (prepatch/none-on-positionless): exit=1, error unsolved goal `False` on true.false.none.
  atk_2 (partial-domain: drops the canDeleteExtra disjunct): exit=1, unsolved goal on true.true.some.
  atk_3 (boundary: uses `i <= ifc` instead of `i < ifc`): exit=1.
  atk_4 (control-flow-effect: positionless treated as WITHIN prefix, addControl:=true on none): exit=1.
  atk_5 (ungrounded-oracle echo: `some canDelete`, drops both inner guards): exit=1.
  atk_6 (drops the canDelete outer guard: `some (canDeleteExtra || inPrefix)`): exit=1.
  atk_7 (constant `some false`): exit=1.

NON-PROVABILITY IS FUNDAMENTAL, NOT WEAK-TACTIC: diverge.lean (exit=0) discharges by native_decide the concrete spec values that each wrong impl contradicts: spec true false none 0 = some false (contradicts atk_1=none, atk_4=some true, atk_5=some true); spec true true none 0 = some true (contradicts atk_2=some false); spec true false (some 3) 3 = some false (contradicts atk_3=some true); spec false true none 0 = some false (contradicts atk_6=some true). Each wrong impl genuinely differs from the spec function at a witnessed input, so no tactic could close it.

MATERIALIZE+RESOLVE STEP: the set of wrong impls whose proof CLOSES with clean axioms is EMPTY, so there is no faithful patch to materialize/resolve. patches={} accordingly. verify=>correct holds vacuously via the functional-equality shape.

A-LEG / DEEP-MODEL AUDIT: meta.json has axioms=[] and deep_model_references=[]; refinement.md and mapping.md declare no unchanged callee consumed as an axiom (the deletion decision is pure boolean logic over (can_delete, can_delete_extra, index, initial_form_count); the BooleanField/get_deletion_widget side effect is abstracted to the boolean 'was the field attached', not axiomatized). axiom_check.py is a skip stub. There are NO A-consumed / A-reference legs to audit — the A-legs are vacuously sound. refinement.md legs are all R (op4, the fixed `index is not None` guard) or I (ops 1,2,3,5, the unchanged boolean framing); no kind-3 unmodeled legs. conf_skip=false; conformance_check.py differential-tests the boolean shadow vs the REAL patched BaseFormSet.add_fields on a live formset over 1e5 inputs (seed 16569), index in {None} U [0..12] exercising the positionless boundary.

VERDICT: SOUND. >=5 distinct same-spec wrong impls (7 run) + prepatch bug all fail to close under lean_verify; positive control verifies with clean [propext] axioms; the functional-equality spec uniquely pins the patched behavior so no closing-but-non-resolving impl exists; no A-legs to break.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding, for a single item in a collection, whether an optional "remove me"
control should be attached to that item.

The collection has two configuration booleans:

  * whether removal is permitted at all, and
  * whether items beyond the pre-populated prefix may also be removed.

Each item is identified by an OPTIONAL position. Some items have a concrete
position (a natural-number offset); others are positionless (a standalone
template item that does not occupy a slot in the collection). The collection also
knows how many leading items are pre-populated.

The removal control is attached exactly when removal is permitted AND either
extra (non-pre-populated) items may be removed too, OR the item sits inside the
pre-populated prefix — i.e. it has a concrete position strictly below the
pre-populated count. A positionless item is, by definition, not inside that
prefix.

The decision is TOTAL: it is defined for every item, including a positionless
one, and never fails to produce an answer.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The decision is a pure
-- boolean computation over the two configuration booleans, the item's optional
-- position, and the pre-populated count; the downstream act of materializing the
-- control object is abstracted to the boolean "was the control attached". Hence
-- no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- An item is inside the pre-populated prefix iff it has a concrete position
strictly below the pre-populated count. A positionless item is never inside it. -/
def withinInitial (index : Option Nat) (ifc : Nat) : Bool :=
  match index with
  | some i => decide (i < ifc)
  | none   => false
-- pure-end

-- post-conditions-start
/-- The outcome is TOTAL and fully pinned to the inputs.

  * `result = some b` always (the decision never fails to produce an answer — in
    particular it is defined for a positionless item); there is no `none` outcome.
  * `b` is true exactly when removal is permitted AND either extra items may be
    removed, OR the item is inside the pre-populated prefix (`withinInitial`).

No output component is left free: the outcome is `some` of the exact boolean
combination of the inputs. -/
def problem_spec_addFields
    (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat)
    (result : Option Bool) : Prop :=
  result = some (canDelete && (canDeleteExtra || withinInitial index ifc))
-- post-conditions-end

-- impl-start
def implementation_addFields
    (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat) :
    Option Bool := Id.run do
  let mut addControl := false
  if canDelete then
    if canDeleteExtra then
      addControl := true
    else
      -- The within-prefix test only makes sense for an item that has a concrete
      -- position; a positionless item is treated as outside the prefix.
      match index with
      | some i => if i < ifc then addControl := true
      | none   => pure ()
  return some addControl
-- impl-end

-- proof-start
theorem correct_addFields :
    ∀ (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat),
      problem_spec_addFields canDelete canDeleteExtra index ifc
        (implementation_addFields canDelete canDeleteExtra index ifc) := by
  intro canDelete canDeleteExtra index ifc
  unfold problem_spec_addFields implementation_addFields withinInitial
  cases canDelete <;> cases canDeleteExtra <;> cases index <;>
    first
      | rfl
      | (rename_i val; by_cases h : val < ifc <;>
          simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
            pure] <;> rfl)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_addFields is a TOTAL FUNCTIONAL EQUALITY: result = some (canDelete && (canDeleteExtra || withinInitial index ifc)), with withinInitial (some i) ifc = decide (i<ifc), withinInitial none _ = false. This pins result to exactly one value for every input, so ANY impl whose correct_addFields closes must be extensionally equal to gold = precisely the patched add_fields behavior. There is no closing-but-non-resolving alternative in principle. All 8 files confirmed same_spec=True vs Solution.lean via swebench_unified.markers.same_spec (spec regions byte-identical).

 Verify cmd: `bash scripts/lean_verify.sh <file>`. Attacks run concurrently as background jobs, <=4 at a time (two batches). 

POSITIVE CONTROL: pos.lean (gold Solution.lean verbatim) -> exit=0 (verifies, no sorry). pos_ax.lean (pos + `#print axioms correct_addFields`) -> exit=0, output: "'correct_addFields' depends on axioms: [propext]" — CLEAN (no sorryAx). 

PREPATCH BUG REPRODUCED: atk_1 encodes the prepatch semantics (returns none for the positionless can_delete=True,can_delete_extra=False,index=none case, modeling the None<int TypeError). same_spec=True, exit=1 (proof does NOT close): goal reduces to `False` on case true.false.none (spec demands some false, impl gives none). This is exactly the prepatch Solution_prepatch.lean behavior and the F2P-discriminating input.

7 DISTINCT WRONG IMPLS, each same_spec=True, each with a genuine gold-style closing-proof attempt (full case split + by_cases + simp/omega/decide fallbacks); ALL FAIL TO CLOSE (exit=1):
  atk_1 (prepatch/none-on-positionless): exit=1, error unsolved goal `False` on true.false.none.
  atk_2 (partial-domain: drops the canDeleteExtra disjunct): exit=1, unsolved goal on true.true.some.
  atk_3 (boundary: uses `i <= ifc` instead of `i < ifc`): exit=1.
  atk_4 (control-flow-effect: positionless treated as WITHIN prefix, addControl:=true on none): exit=1.
  atk_5 (ungrounded-oracle echo: `some canDelete`, drops both inner guards): exit=1.
  atk_6 (drops the canDelete outer guard: `some (canDeleteExtra || inPrefix)`): exit=1.
  atk_7 (constant `some false`): exit=1.

NON-PROVABILITY IS FUNDAMENTAL, NOT WEAK-TACTIC: diverge.lean (exit=0) discharges by native_decide the concrete spec values that each wrong impl contradicts: spec true false none 0 = some false (contradicts atk_1=none, atk_4=some true, atk_5=some true); spec true true none 0 = some true (contradicts atk_2=some false); spec true false (some 3) 3 = some false (contradicts atk_3=some true); spec false true none 0 = some false (contradicts atk_6=some true). Each wrong impl genuinely differs from the spec function at a witnessed input, so no tactic could close it.

MATERIALIZE+RESOLVE STEP: the set of wrong impls whose proof CLOSES with clean axioms is EMPTY, so there is no faithful patch to materialize/resolve. patches={} accordingly. verify=>correct holds vacuously via the functional-equality shape.

A-LEG / DEEP-MODEL AUDIT: meta.json has axioms=[] and deep_model_references=[]; refinement.md and mapping.md declare no unchanged callee consumed as an axiom (the deletion decision is pure boolean logic over (can_delete, can_delete_extra, index, initial_form_count); the BooleanField/get_deletion_widget side effect is abstracted to the boolean 'was the field attached', not axiomatized). axiom_check.py is a skip stub. There are NO A-consumed / A-reference legs to audit — the A-legs are vacuously sound. refinement.md legs are all R (op4, the fixed `index is not None` guard) or I (ops 1,2,3,5, the unchanged boolean framing); no kind-3 unmodeled legs. conf_skip=false; conformance_check.py differential-tests the boolean shadow vs the REAL patched BaseFormSet.add_fields on a live formset over 1e5 inputs (seed 16569), index in {None} U [0..12] exercising the positionless boundary.

VERDICT: SOUND. >=5 distinct same-spec wrong impls (7 run) + prepatch bug all fail to close under lean_verify; positive control verifies with clean [propext] axioms; the functional-equality spec uniquely pins the patched behavior so no closing-but-non-resolving impl exists; no A-legs to break.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-16569, modeled function addFields (BaseFormSet.add_fields deletion branch, django/forms/formsets.py:490). Findings: (1) same_spec(Solution, Solution_prepatch, lean)=True — spec region (problem_spec_addFields + withinInitial + non-impl framing) is byte-identical; only impl+proof differ (prepatch = sorry). (2) Solution.lean compiles via lean_verify.sh (exit 0); #print axioms correct_addFields => [propext] only, no sorryAx — proof is genuine. (3) The spec asserts result = some (canDelete && (canDeleteExtra || withinInitial index ifc)), withinInitial none _ = false, withinInitial (some i) ifc = decide (i<ifc). This exactly transcribes the patched guard `self.can_delete and (self.can_delete_extra or (index is not None and index < initial_form_count))`. (4) INDEPENDENT differential test: transcribed the post-patch add_fields verbatim from the gold patch, drove it on a live formset (formset_factory, initial of length ifc), and compared its observable outcome (TypeError->none, else DELETION_FIELD_NAME in form.fields) against the spec over the ENTIRE modeled domain: canDelete x canDeleteExtra x ifc in 0..13 x index in {None}∪0..13 = 840 inputs => 0 mismatches. The spec's TOTAL `some _` clause holds because index maps to Option Nat (None or non-negative), matching real formset index provenance (enumerate/None), so the patched callee never raises in-domain. Conclusion: the modeled function agrees with the real patched callee on every input in the type-bijected domain; the spec is neither too strong nor drifting. No diverging input exists. G-CONF also independently recorded 100000 inputs / 0 disagreements.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region byte-identity confirmed: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True; the patched/prepatch diff is confined to the elided impl/proof regions. The public spec_view exposes only the abstracted spec (docstring + `withinInitial` + `problem_spec_addFields`) with impl/proof elided.

Leakage assessment against the PUBLIC problem_statement (not hints — hints_text is empty): the problem_statement is maximally revealing already — it quotes the gold diff VERBATIM (`if self.can_delete and (self.can_delete_extra or (index is not None and index < initial_form_count)):`), names line 493, the exact `TypeError: '<' not supported between instances of 'NoneType' and 'int'`, the empty_form/can_delete=True/can_delete_extra=False trigger, and even prescribes the `index is not None` fix. The gold edit is fully public.

The spec view is strictly MORE abstract than the problem_statement: it is de-identified (no Django/add_fields/formsets/DELETION_FIELD_NAME/initial_form_count), phrased over a generic 'collection/item/optional position/removal control'. Its content (decision is TOTAL; a positionless item is treated as outside the prefix; control attached iff removal permitted AND (extra removable OR within prefix)) is a paraphrase of what the problem_statement states explicitly. Nothing in the spec view reveals the gold edit beyond the public problem_statement. No leaking line.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
