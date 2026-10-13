# P2 adversarial audit — django__django-13741

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,20 +64,13 @@
   result.changed = (if result.disabled then false else !(valEq initial data))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_passwordHashField
     (disabledArg : Option Bool) (initial data : Option String) : FieldOutcome :=
   Id.run do
-  -- The effective disabled setting: the caller's value, or the default when
-  -- the caller supplied none.
-  let disabled := disabledArg.getD true
+  let disabled := disabledArg.getD false
   let mut changed := false
-  -- A disabled field is never editable, so it never reports a change.
-  if disabled then
-    return { disabled := disabled, changed := false }
-  -- Otherwise compare the initial value against the submission (missing ↦ "").
-  if !(valEq initial data) then
-    changed := true
   return { disabled := disabled, changed := changed }
 -- impl-end
 
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,18 +64,13 @@
   result.changed = (if result.disabled then false else !(valEq initial data))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_passwordHashField
     (disabledArg : Option Bool) (initial data : Option String) : FieldOutcome :=
   Id.run do
-  -- The effective disabled setting: the caller's value, or the default when
-  -- the caller supplied none.
   let disabled := disabledArg.getD true
   let mut changed := false
-  -- A disabled field is never editable, so it never reports a change.
-  if disabled then
-    return { disabled := disabled, changed := false }
-  -- Otherwise compare the initial value against the submission (missing ↦ "").
   if !(valEq initial data) then
     changed := true
   return { disabled := disabled, changed := changed }
@@ -90,7 +85,8 @@
   unfold problem_spec_passwordHashField implementation_passwordHashField
   simp only [Id.run]
   by_cases h : disabledArg.getD true
-  · simp only [h, if_true]; exact ⟨rfl, rfl⟩
+  · simp only [h, if_true]
+    by_cases hv : valEq initial data <;> simp only [hv] <;> exact ⟨rfl, rfl⟩
   · simp only [h, Bool.false_eq_true, if_false]
     by_cases hv : valEq initial data <;> simp only [hv] <;> exact ⟨rfl, rfl⟩
 -- proof-end
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,18 +64,15 @@
   result.changed = (if result.disabled then false else !(valEq initial data))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_passwordHashField
     (disabledArg : Option Bool) (initial data : Option String) : FieldOutcome :=
   Id.run do
-  -- The effective disabled setting: the caller's value, or the default when
-  -- the caller supplied none.
   let disabled := disabledArg.getD true
   let mut changed := false
-  -- A disabled field is never editable, so it never reports a change.
   if disabled then
-    return { disabled := disabled, changed := false }
-  -- Otherwise compare the initial value against the submission (missing ↦ "").
+    return { disabled := disabled, changed := true }
   if !(valEq initial data) then
     changed := true
   return { disabled := disabled, changed := changed }
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,19 +64,16 @@
   result.changed = (if result.disabled then false else !(valEq initial data))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_passwordHashField
     (disabledArg : Option Bool) (initial data : Option String) : FieldOutcome :=
   Id.run do
-  -- The effective disabled setting: the caller's value, or the default when
-  -- the caller supplied none.
   let disabled := disabledArg.getD true
   let mut changed := false
-  -- A disabled field is never editable, so it never reports a change.
   if disabled then
     return { disabled := disabled, changed := false }
-  -- Otherwise compare the initial value against the submission (missing ↦ "").
-  if !(valEq initial data) then
+  if valEq initial data then
     changed := true
   return { disabled := disabled, changed := changed }
 -- impl-end
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,20 +64,18 @@
   result.changed = (if result.disabled then false else !(valEq initial data))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_passwordHashField
     (disabledArg : Option Bool) (initial data : Option String) : FieldOutcome :=
   Id.run do
-  -- The effective disabled setting: the caller's value, or the default when
-  -- the caller supplied none.
   let disabled := disabledArg.getD true
   let mut changed := false
-  -- A disabled field is never editable, so it never reports a change.
   if disabled then
     return { disabled := disabled, changed := false }
-  -- Otherwise compare the initial value against the submission (missing ↦ "").
-  if !(valEq initial data) then
-    changed := true
+  match initial, data with
+  | none, none => changed := true
+  | _, _ => if !(valEq initial data) then changed := true
   return { disabled := disabled, changed := changed }
 -- impl-end
 
@@ -92,5 +90,9 @@
   by_cases h : disabledArg.getD true
   · simp only [h, if_true]; exact ⟨rfl, rfl⟩
   · simp only [h, Bool.false_eq_true, if_false]
-    by_cases hv : valEq initial data <;> simp only [hv] <;> exact ⟨rfl, rfl⟩
+    cases initial <;> cases data <;>
+      simp only [valEq] <;>
+      first
+        | exact ⟨rfl, rfl⟩
+        | (by_cases hv : valEq initial data <;> simp only [hv] <;> exact ⟨rfl, rfl⟩)
 -- proof-end
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,19 +64,16 @@
   result.changed = (if result.disabled then false else !(valEq initial data))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_passwordHashField
     (disabledArg : Option Bool) (initial data : Option String) : FieldOutcome :=
   Id.run do
-  -- The effective disabled setting: the caller's value, or the default when
-  -- the caller supplied none.
   let disabled := disabledArg.getD true
   let mut changed := false
-  -- A disabled field is never editable, so it never reports a change.
   if disabled then
     return { disabled := disabled, changed := false }
-  -- Otherwise compare the initial value against the submission (missing ↦ "").
-  if !(valEq initial data) then
+  if initial != data then
     changed := true
   return { disabled := disabled, changed := changed }
 -- impl-end
@@ -92,5 +89,5 @@
   by_cases h : disabledArg.getD true
   · simp only [h, if_true]; exact ⟨rfl, rfl⟩
   · simp only [h, Bool.false_eq_true, if_false]
-    by_cases hv : valEq initial data <;> simp only [hv] <;> exact ⟨rfl, rfl⟩
+    by_cases hv : initial != data <;> simp only [hv] <;> exact ⟨rfl, rfl⟩
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing a read-only form field that displays a stored secret summary and
must never be treated as editable, then deciding whether such a field reports a
change between its initial value and a submitted value.

The field is built from an optional caller-supplied "disabled" setting. When the
caller does not supply that setting, the field defaults to being disabled; when
the caller does supply it, the caller's choice is used verbatim. A disabled
field is shown but cannot be edited: any value the client submits is ignored in
favour of the field's initial value.

The change decision follows from that configuration:

  * a disabled field never reports a change (its effective value is always the
    initial value, so there is nothing to differ);
  * a field that is not disabled reports a change exactly when its initial value
    differs from the submitted value, where a missing value on either side is
    treated as the empty string.

The behavior is stated abstractly as an input→output relation over the optional
disabled setting and the (optional) initial and submitted values; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a contract. Recording the
-- effective disabled setting (the caller's value, or the default when none was
-- supplied) and the resulting change decision are modeled directly below, so
-- the spec needs no `opaque`/`axiom` callee property.
-- axioms-end

-- pure-start
/-- The observable outcome of constructing the field and asking it whether a
submission constitutes a change: the field's effective disabled setting, and the
change decision. -/
structure FieldOutcome where
  disabled : Bool
  changed : Bool
deriving DecidableEq, Repr

/-- Value-level equality of two optional values, treating a missing value as the
empty string. -/
def valEq (a b : Option String) : Bool := (a.getD "") == (b.getD "")
-- pure-end

-- post-conditions-start
/-- The outcome is fully pinned to the inputs:

  * `disabled` is the caller's supplied setting when present, and the default
    `true` when no setting was supplied (`disabledArg.getD true`);
  * `changed` is `false` whenever the field is disabled, and otherwise is `true`
    exactly when the initial and submitted values differ (missing ↦ empty
    string).

No output component is left free: both fields of the outcome are determined by
the inputs. -/
def problem_spec_passwordHashField
    (disabledArg : Option Bool) (initial data : Option String)
    (result : FieldOutcome) : Prop :=
  result.disabled = disabledArg.getD true ∧
  result.changed = (if result.disabled then false else !(valEq initial data))
-- post-conditions-end

-- impl-start
def implementation_passwordHashField
    (disabledArg : Option Bool) (initial data : Option String) : FieldOutcome :=
  Id.run do
  -- The effective disabled setting: the caller's value, or the default when
  -- the caller supplied none.
  let disabled := disabledArg.getD true
  let mut changed := false
  -- A disabled field is never editable, so it never reports a change.
  if disabled then
    return { disabled := disabled, changed := false }
  -- Otherwise compare the initial value against the submission (missing ↦ "").
  if !(valEq initial data) then
    changed := true
  return { disabled := disabled, changed := changed }
-- impl-end

-- proof-start
theorem correct_passwordHashField :
    ∀ (disabledArg : Option Bool) (initial data : Option String),
      problem_spec_passwordHashField disabledArg initial data
        (implementation_passwordHashField disabledArg initial data) := by
  intro disabledArg initial data
  unfold problem_spec_passwordHashField implementation_passwordHashField
  simp only [Id.run]
  by_cases h : disabledArg.getD true
  · simp only [h, if_true]; exact ⟨rfl, rfl⟩
  · simp only [h, Bool.false_eq_true, if_false]
    by_cases hv : valEq initial data <;> simp only [hv] <;> exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The postcondition problem_spec_passwordHashField fully pins BOTH output fields to a deterministic function of the inputs (result.disabled = disabledArg.getD true; result.changed = if result.disabled then false else !(valEq initial data)). This is a single-valued functional relation: for every (disabledArg, initial, data) there is exactly one satisfying FieldOutcome, so any impl differing behaviorally from gold on any input cannot close the proof. No wrong impl produced a closing clean-axiom proof, so protocol step 2 (materialize+resolve the faithful patch) has no qualifying attack — every attack failed to verify.

same_spec: all 7 files (atk_pos + atk1..atk6) return True (axioms/pure/pre/post byte-identical; only impl region edited). Verified against get_backend('lean').language with python from repo root.

Commands: bash scripts/lean_verify.sh <file>. Run concurrently in two batches of <=4.

Results:
- atk_pos (gold copy, positive control): exit 0 (verifies, no sorry). #print axioms correct_passwordHashField => [propext, Quot.sound] (clean std axioms; no sorryAx, no custom axiom). Confirms no axiom/opaque declared in Solution.lean (axioms region is comments only).
- atk1 (prepatch bug: disabled defaults to false, changed hardwired false — partial/default-boundary wrong): exit 1. Genuine proof error at proof lines (Application type mismatch on rfl). PREPATCH REPRODUCED: matches Solution_prepatch.lean behavior; gold proof does not close.
- atk2 (control-flow: drops disabled branch, changed=!valEq always): exit 1, genuine type-mismatch error.
- atk3 (control-flow-effect: changed=true when disabled): exit 1, genuine error.
- atk4 (ungrounded-oracle inversion: changed=valEq i.e. equality instead of inequality in non-disabled branch): exit 1, genuine error.
- atk5 (partial-domain: correct except forces changed=true when both initial/data are none): exit 1, genuine error.
- atk6 (ungrounded-oracle echo: uses Option beq initial!=data instead of valEq, so none vs some "" wrongly differ): exit 1, genuine error.

All 6 attacks fail with real proof-obligation errors (Application type mismatch / unsolved rfl), not spurious syntax; positive control verifies cleanly. A-leg audit (refinement.md/mapping.md): no axioms declared or consumed (axiom_check.py is a genuine skip stub — no opaque/axiom in Solution.lean). Three A-reference legs — (1) `let disabled := disabledArg.getD true` <-> kwargs.setdefault('disabled', True) + self.disabled (fields.py:87); (2) disabled->changed:=false <-> base Field.has_changed `if self.disabled: return False` (fields.py:179); (3) `!(valEq initial data)` <-> base Field.has_changed None->'' compare (fields.py:190-192) — each faithfully corresponds to the real patched ReadOnlyPasswordHashField / base Field callees per mapping.md, and are differentially validated by G-CONF (conformance_check.py, pinned seed 13741, 1e5 cases, oracle constructs REAL patched field). All refinement legs are R / A-reference / I; no kind-3 (unvalidated deep-model) leg. verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing a read-only form field that displays a stored secret summary and
must never be treated as editable, then deciding whether such a field reports a
change between its initial value and a submitted value.

The field is built from an optional caller-supplied "disabled" setting. When the
caller does not supply that setting, the field defaults to being disabled; when
the caller does supply it, the caller's choice is used verbatim. A disabled
field is shown but cannot be edited: any value the client submits is ignored in
favour of the field's initial value.

The change decision follows from that configuration:

  * a disabled field never reports a change (its effective value is always the
    initial value, so there is nothing to differ);
  * a field that is not disabled reports a change exactly when its initial value
    differs from the submitted value, where a missing value on either side is
    treated as the empty string.

The behavior is stated abstractly as an input→output relation over the optional
disabled setting and the (optional) initial and submitted values; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a contract. Recording the
-- effective disabled setting (the caller's value, or the default when none was
-- supplied) and the resulting change decision are modeled directly below, so
-- the spec needs no `opaque`/`axiom` callee property.
-- axioms-end

-- pure-start
/-- The observable outcome of constructing the field and asking it whether a
submission constitutes a change: the field's effective disabled setting, and the
change decision. -/
structure FieldOutcome where
  disabled : Bool
  changed : Bool
deriving DecidableEq, Repr

/-- Value-level equality of two optional values, treating a missing value as the
empty string. -/
def valEq (a b : Option String) : Bool := (a.getD "") == (b.getD "")
-- pure-end

-- post-conditions-start
/-- The outcome is fully pinned to the inputs:

  * `disabled` is the caller's supplied setting when present, and the default
    `true` when no setting was supplied (`disabledArg.getD true`);
  * `changed` is `false` whenever the field is disabled, and otherwise is `true`
    exactly when the initial and submitted values differ (missing ↦ empty
    string).

No output component is left free: both fields of the outcome are determined by
the inputs. -/
def problem_spec_passwordHashField
    (disabledArg : Option Bool) (initial data : Option String)
    (result : FieldOutcome) : Prop :=
  result.disabled = disabledArg.getD true ∧
  result.changed = (if result.disabled then false else !(valEq initial data))
-- post-conditions-end

-- impl-start
def implementation_passwordHashField
    (disabledArg : Option Bool) (initial data : Option String) : FieldOutcome :=
  Id.run do
  -- The effective disabled setting: the caller's value, or the default when
  -- the caller supplied none.
  let disabled := disabledArg.getD true
  let mut changed := false
  -- A disabled field is never editable, so it never reports a change.
  if disabled then
    return { disabled := disabled, changed := false }
  -- Otherwise compare the initial value against the submission (missing ↦ "").
  if !(valEq initial data) then
    changed := true
  return { disabled := disabled, changed := changed }
-- impl-end

-- proof-start
theorem correct_passwordHashField :
    ∀ (disabledArg : Option Bool) (initial data : Option String),
      problem_spec_passwordHashField disabledArg initial data
        (implementation_passwordHashField disabledArg initial data) := by
  intro disabledArg initial data
  unfold problem_spec_passwordHashField implementation_passwordHashField
  simp only [Id.run]
  by_cases h : disabledArg.getD true
  · simp only [h, if_true]; exact ⟨rfl, rfl⟩
  · simp only [h, Bool.false_eq_true, if_false]
    by_cases hv : valEq initial data <;> simp only [hv] <;> exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The postcondition problem_spec_passwordHashField fully pins BOTH output fields to a deterministic function of the inputs (result.disabled = disabledArg.getD true; result.changed = if result.disabled then false else !(valEq initial data)). This is a single-valued functional relation: for every (disabledArg, initial, data) there is exactly one satisfying FieldOutcome, so any impl differing behaviorally from gold on any input cannot close the proof. No wrong impl produced a closing clean-axiom proof, so protocol step 2 (materialize+resolve the faithful patch) has no qualifying attack — every attack failed to verify.

same_spec: all 7 files (atk_pos + atk1..atk6) return True (axioms/pure/pre/post byte-identical; only impl region edited). Verified against get_backend('lean').language with python from repo root.

Commands: bash scripts/lean_verify.sh <file>. Run concurrently in two batches of <=4.

Results:
- atk_pos (gold copy, positive control): exit 0 (verifies, no sorry). #print axioms correct_passwordHashField => [propext, Quot.sound] (clean std axioms; no sorryAx, no custom axiom). Confirms no axiom/opaque declared in Solution.lean (axioms region is comments only).
- atk1 (prepatch bug: disabled defaults to false, changed hardwired false — partial/default-boundary wrong): exit 1. Genuine proof error at proof lines (Application type mismatch on rfl). PREPATCH REPRODUCED: matches Solution_prepatch.lean behavior; gold proof does not close.
- atk2 (control-flow: drops disabled branch, changed=!valEq always): exit 1, genuine type-mismatch error.
- atk3 (control-flow-effect: changed=true when disabled): exit 1, genuine error.
- atk4 (ungrounded-oracle inversion: changed=valEq i.e. equality instead of inequality in non-disabled branch): exit 1, genuine error.
- atk5 (partial-domain: correct except forces changed=true when both initial/data are none): exit 1, genuine error.
- atk6 (ungrounded-oracle echo: uses Option beq initial!=data instead of valEq, so none vs some "" wrongly differ): exit 1, genuine error.

All 6 attacks fail with real proof-obligation errors (Application type mismatch / unsolved rfl), not spurious syntax; positive control verifies cleanly. A-leg audit (refinement.md/mapping.md): no axioms declared or consumed (axiom_check.py is a genuine skip stub — no opaque/axiom in Solution.lean). Three A-reference legs — (1) `let disabled := disabledArg.getD true` <-> kwargs.setdefault('disabled', True) + self.disabled (fields.py:87); (2) disabled->changed:=false <-> base Field.has_changed `if self.disabled: return False` (fields.py:179); (3) `!(valEq initial data)` <-> base Field.has_changed None->'' compare (fields.py:190-192) — each faithfully corresponds to the real patched ReadOnlyPasswordHashField / base Field callees per mapping.md, and are differentially validated by G-CONF (conformance_check.py, pinned seed 13741, 1e5 cases, oracle constructs REAL patched field). All refinement legs are R / A-reference / I; no kind-3 (unvalidated deep-model) leg. verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. Setup: Solution.lean compiles under lean_verify.sh (exit 0); #print axioms correct_passwordHashField = [propext, Quot.sound] — no sorryAx, real proof. Spec view byte-identical to Solution_prepatch (same_spec=True). Differential test against the REAL gold-patched ReadOnlyPasswordHashField (base_commit d746f28949, gold patch: kwargs.setdefault('disabled', True) + removal of bound_data/has_changed overrides, inheriting base Field.has_changed): spec (disabled=disabledArg.getD true; changed = if disabled then false else initial/None->'' != data/None->'') matched the real field.disabled and field.has_changed(initial,data) on 147 structured cases (disabled kwarg ∈ {absent,True,False} × initial/data ∈ {None,'','a','b','abc','ABC',unicode}) AND 200,000 randomized fuzz cases (seed 13741, incl. NUL bytes/unicode) — 0 disagreements. Field has no to_python/_coerce override, so base has_changed reduces exactly to None-normalized value equality, matching valEq. Only out-of-model edge: explicit disabled=None yields field.disabled=None, but that lies outside the declared Option Bool↔{absent,True,False} bijection and is not a valid modeled input. Spec is neither too strong nor drifted; no diverging input exists within the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view judged is the recorded one: spec_view sha256 = 06252d16db4fe3d19f172988bcbaa19ddbeabaa2bc8cfca6d4eabb40a1d1ad0d (matches meta.json region_hashes.spec_view exactly); same_spec(Solution, Solution_prepatch, lean) = True, so the shared spec region is byte-identical.

The gold edit is `kwargs.setdefault('disabled', True)` on ReadOnlyPasswordHashField plus removal of the bound_data/has_changed overrides and UserChangeForm.clean_password. The spec view discloses NONE of these mechanics: no setdefault, no `disabled=True` kwarg code, no method names (bound_data/has_changed/clean_password), no Django identifiers. Impl and proof regions are correctly elided to placeholders.

Every load-bearing fact in the spec view is already disclosed in the PUBLIC problem_statement (not hints_text):
  * the default-to-disabled fact pinned by `result.disabled = disabledArg.getD true` <- problem_statement: 'this property could be set to True be default on the ReadOnlyPasswordHashField'.
  * the disabled-field-never-changes semantics <- problem_statement: '[disabled] so that it won't be editable... Even if a user tampers with the field's value submitted to the server, it will be ignored in favor of the value from the form's initial data'.
  * the non-disabled initial!=data (None->'') comparison is generic base Field.has_changed behavior, not gold-specific, and is not the discriminating observable (FAIL_TO_PASS test asserts field.disabled is True).

The spec is abstract (FieldOutcome{disabled,changed} + valEq over Option String) and carries nothing beyond the problem_statement's own restatement of intended behavior. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
