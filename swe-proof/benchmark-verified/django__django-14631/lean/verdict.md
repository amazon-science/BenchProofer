# P2 adversarial audit — django__django-14631

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean`, `atk8.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition is a tight equality `problem_spec_cleanFields fields result := result = fields.map cleanedValue` (no existential, no weakening), so every verifying impl must be extensionally equal to the oracle `fields.map cleanedValue` on ALL inputs. No same-spec wrong impl could close its correctness proof. Concrete distinguishing input for the prepatch bug (atk1): fields = [⟨disabled:=true, supportsMicro:=false, rawInitial:=ts 100 123456, data:=other 0⟩] — spec requires cleanedValue = boundInitial = ts 100 0 (sub-second dropped), but prepatch impl yields ts 100 123456; the proof goal reduces to `rawInitial = boundInitial` which is false, giving unsolved goals.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
 def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do
   let mut cleaned : List FieldValue := []
   for f in fields do
-    let value := if f.disabled then boundInitial f else f.data
+    let value := if f.disabled then f.rawInitial else f.data
     cleaned := cleaned ++ [value]
   return cleaned
 -- impl-end
@@ -90,7 +90,7 @@
 theorem helper_cleanFields (fields : List FieldModel) :
     ∀ (init : List FieldValue),
       Id.run (forIn fields init (fun f r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then boundInitial f else f.data]))))) =
+        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then f.rawInitial else f.data]))))) =
       init ++ fields.map cleanedValue := by
   induction fields with
   | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,34 +81,22 @@
 def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do
   let mut cleaned : List FieldValue := []
   for f in fields do
-    let value := if f.disabled then boundInitial f else f.data
+    let value := f.data
     cleaned := cleaned ++ [value]
   return cleaned
 -- impl-end
 
 -- proof-start
-theorem helper_cleanFields (fields : List FieldModel) :
-    ∀ (init : List FieldValue),
-      Id.run (forIn fields init (fun f r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then boundInitial f else f.data]))))) =
-      init ++ fields.map cleanedValue := by
-  induction fields with
-  | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp only [List.map_cons, cleanedValue, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_cleanFields :
     ∀ (fields : List FieldModel),
       problem_spec_cleanFields fields (implementation_cleanFields fields) := by
   intro fields
   unfold problem_spec_cleanFields implementation_cleanFields
   simp only [Id.run, bind, pure]
-  have h := helper_cleanFields fields []
-  simp only [Id.run, bind, pure] at h
-  rw [h]
-  simp
+  induction fields with
+  | nil => rfl
+  | cons a as ih =>
+    rw [List.forIn_cons]
+    simp only [Id.run, bind, pure, List.map_cons, cleanedValue] at *
+    sorry
 -- proof-end
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,34 +81,22 @@
 def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do
   let mut cleaned : List FieldValue := []
   for f in fields do
-    let value := if f.disabled then boundInitial f else f.data
+    let value := if f.disabled then f.data else boundInitial f
     cleaned := cleaned ++ [value]
   return cleaned
 -- impl-end
 
 -- proof-start
-theorem helper_cleanFields (fields : List FieldModel) :
-    ∀ (init : List FieldValue),
-      Id.run (forIn fields init (fun f r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then boundInitial f else f.data]))))) =
-      init ++ fields.map cleanedValue := by
-  induction fields with
-  | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp only [List.map_cons, cleanedValue, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_cleanFields :
     ∀ (fields : List FieldModel),
       problem_spec_cleanFields fields (implementation_cleanFields fields) := by
   intro fields
   unfold problem_spec_cleanFields implementation_cleanFields
   simp only [Id.run, bind, pure]
-  have h := helper_cleanFields fields []
-  simp only [Id.run, bind, pure] at h
-  rw [h]
-  simp
+  induction fields with
+  | nil => rfl
+  | cons a as ih =>
+    rw [List.forIn_cons]
+    simp only [Id.run, bind, pure, List.map_cons, cleanedValue] at *
+    sorry
 -- proof-end
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,33 +82,21 @@
   let mut cleaned : List FieldValue := []
   for f in fields do
     let value := if f.disabled then boundInitial f else f.data
-    cleaned := cleaned ++ [value]
+    cleaned := [value] ++ cleaned
   return cleaned
 -- impl-end
 
 -- proof-start
-theorem helper_cleanFields (fields : List FieldModel) :
-    ∀ (init : List FieldValue),
-      Id.run (forIn fields init (fun f r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then boundInitial f else f.data]))))) =
-      init ++ fields.map cleanedValue := by
-  induction fields with
-  | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp only [List.map_cons, cleanedValue, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_cleanFields :
     ∀ (fields : List FieldModel),
       problem_spec_cleanFields fields (implementation_cleanFields fields) := by
   intro fields
   unfold problem_spec_cleanFields implementation_cleanFields
   simp only [Id.run, bind, pure]
-  have h := helper_cleanFields fields []
-  simp only [Id.run, bind, pure] at h
-  rw [h]
-  simp
+  induction fields with
+  | nil => rfl
+  | cons a as ih =>
+    rw [List.forIn_cons]
+    simp only [Id.run, bind, pure, List.map_cons, cleanedValue] at *
+    sorry
 -- proof-end
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,37 +78,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do
-  let mut cleaned : List FieldValue := []
-  for f in fields do
-    let value := if f.disabled then boundInitial f else f.data
-    cleaned := cleaned ++ [value]
-  return cleaned
+def implementation_cleanFields (fields : List FieldModel) : List FieldValue :=
+  []
 -- impl-end
 
 -- proof-start
-theorem helper_cleanFields (fields : List FieldModel) :
-    ∀ (init : List FieldValue),
-      Id.run (forIn fields init (fun f r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then boundInitial f else f.data]))))) =
-      init ++ fields.map cleanedValue := by
-  induction fields with
-  | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp only [List.map_cons, cleanedValue, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_cleanFields :
     ∀ (fields : List FieldModel),
       problem_spec_cleanFields fields (implementation_cleanFields fields) := by
   intro fields
   unfold problem_spec_cleanFields implementation_cleanFields
-  simp only [Id.run, bind, pure]
-  have h := helper_cleanFields fields []
-  simp only [Id.run, bind, pure] at h
-  rw [h]
-  simp
+  cases fields with
+  | nil => rfl
+  | cons a as => sorry
 -- proof-end
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,12 @@
 def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do
   let mut cleaned : List FieldValue := []
   for f in fields do
-    let value := if f.disabled then boundInitial f else f.data
+    let value :=
+      if f.disabled then
+        (match f.rawInitial with
+         | FieldValue.ts whole _ => FieldValue.ts whole 0
+         | FieldValue.other n => FieldValue.other n)
+      else f.data
     cleaned := cleaned ++ [value]
   return cleaned
 -- impl-end
@@ -90,7 +95,11 @@
 theorem helper_cleanFields (fields : List FieldModel) :
     ∀ (init : List FieldValue),
       Id.run (forIn fields init (fun f r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then boundInitial f else f.data]))))) =
+        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then
+          (match f.rawInitial with
+           | FieldValue.ts whole _ => FieldValue.ts whole 0
+           | FieldValue.other n => FieldValue.other n)
+          else f.data]))))) =
       init ++ fields.map cleanedValue := by
   induction fields with
   | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl
@@ -99,7 +108,7 @@
     rw [List.forIn_cons]
     simp only [Id.run, bind, pure] at ih ⊢
     rw [ih]
-    simp only [List.map_cons, cleanedValue, List.append_assoc, List.cons_append, List.nil_append]
+    simp only [List.map_cons, cleanedValue, boundInitial, List.append_assoc, List.cons_append, List.nil_append]
 
 theorem correct_cleanFields :
     ∀ (fields : List FieldModel),
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,35 +80,24 @@
 -- impl-start
 def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do
   let mut cleaned : List FieldValue := []
+  let mut first := true
   for f in fields do
-    let value := if f.disabled then boundInitial f else f.data
-    cleaned := cleaned ++ [value]
+    if first then
+      first := false
+    else
+      let value := if f.disabled then boundInitial f else f.data
+      cleaned := cleaned ++ [value]
   return cleaned
 -- impl-end
 
 -- proof-start
-theorem helper_cleanFields (fields : List FieldModel) :
-    ∀ (init : List FieldValue),
-      Id.run (forIn fields init (fun f r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then boundInitial f else f.data]))))) =
-      init ++ fields.map cleanedValue := by
-  induction fields with
-  | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp only [List.map_cons, cleanedValue, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_cleanFields :
     ∀ (fields : List FieldModel),
       problem_spec_cleanFields fields (implementation_cleanFields fields) := by
   intro fields
   unfold problem_spec_cleanFields implementation_cleanFields
   simp only [Id.run, bind, pure]
-  have h := helper_cleanFields fields []
-  simp only [Id.run, bind, pure] at h
-  rw [h]
-  simp
+  cases fields with
+  | nil => rfl
+  | cons a as => sorry
 -- proof-end
```

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,37 +78,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do
-  let mut cleaned : List FieldValue := []
-  for f in fields do
-    let value := if f.disabled then boundInitial f else f.data
-    cleaned := cleaned ++ [value]
-  return cleaned
+def implementation_cleanFields (fields : List FieldModel) : List FieldValue :=
+  fields.map (fun _ => FieldValue.other 0)
 -- impl-end
 
 -- proof-start
-theorem helper_cleanFields (fields : List FieldModel) :
-    ∀ (init : List FieldValue),
-      Id.run (forIn fields init (fun f r =>
-        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then boundInitial f else f.data]))))) =
-      init ++ fields.map cleanedValue := by
-  induction fields with
-  | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp only [List.map_cons, cleanedValue, List.append_assoc, List.cons_append, List.nil_append]
-
 theorem correct_cleanFields :
     ∀ (fields : List FieldModel),
       problem_spec_cleanFields fields (implementation_cleanFields fields) := by
   intro fields
   unfold problem_spec_cleanFields implementation_cleanFields
-  simp only [Id.run, bind, pure]
-  have h := helper_cleanFields fields []
-  simp only [Id.run, bind, pure] at h
-  rw [h]
-  simp
+  cases fields with
+  | nil => rfl
+  | cons a as => sorry
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting and cleaning the submitted value of each field on a bound form.

A form has an ordered collection of fields. Cleaning the form produces, for each
field and in field order, the value that field contributes to the form's cleaned
data. For each field the value is chosen as follows:

* an *editable* field takes the value submitted for it (the data extracted from
  the form's payload for that field);
* a *disabled* field ignores any submitted payload and instead takes its own
  preset initial value — specifically the initial value exactly as the field
  itself would present it. A field presents a temporal initial value (a date or
  time) only at the precision its display can represent: if the field's display
  cannot represent sub-second precision, any sub-second component of the initial
  value is dropped before it is used. Non-temporal initial values, and temporal
  values on fields whose display does support sub-second precision, are presented
  unchanged.

The selected value is then cleaned. In the success case modeled here cleaning
preserves the selected value, so the cleaned value for each field equals the
value selected by the rule above. The cleaned data therefore has one entry per
field, in field order, with no field's entry left unconstrained.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The two outside
-- operations used per field — obtaining the field's preset initial value and
-- obtaining the value submitted for the field — have their results supplied as
-- inputs (`rawInitial`, `data`). The presentation-normalization of a temporal
-- value and the field-order traversal are spelled out concretely below.
-- axioms-end

-- pure-start
/-- A field value. `ts whole sub` is a temporal value split into its
whole-second-and-coarser component (`whole`) and its sub-second component
(`sub`, a microsecond count `0..999999`). `other n` stands in for any
non-temporal value. -/
inductive FieldValue where
  | ts (whole : Int) (sub : Nat)
  | other (n : Int)
deriving DecidableEq

/-- One field of the form together with its bound state.
* `disabled`      — whether the field is disabled;
* `supportsMicro` — whether the field's display can represent sub-second precision;
* `rawInitial`    — the field's preset initial value (already evaluated);
* `data`          — the value submitted for the field. -/
structure FieldModel where
  disabled : Bool
  supportsMicro : Bool
  rawInitial : FieldValue
  data : FieldValue
deriving DecidableEq

/-- The initial value of a field exactly as the field presents it: a temporal
value loses its sub-second component when the field's display cannot represent
sub-second precision; every other value is presented unchanged. -/
def boundInitial (f : FieldModel) : FieldValue :=
  match f.rawInitial with
  | FieldValue.ts whole sub => if f.supportsMicro then FieldValue.ts whole sub else FieldValue.ts whole 0
  | FieldValue.other n => FieldValue.other n

/-- The cleaned value contributed by one field: a disabled field uses its
presented initial value; an editable field uses its submitted value. -/
def cleanedValue (f : FieldModel) : FieldValue :=
  if f.disabled then boundInitial f else f.data
-- pure-end

-- post-conditions-start
def problem_spec_cleanFields (fields : List FieldModel) (result : List FieldValue) : Prop :=
  result = fields.map cleanedValue
-- post-conditions-end

-- impl-start
def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do
  let mut cleaned : List FieldValue := []
  for f in fields do
    let value := if f.disabled then boundInitial f else f.data
    cleaned := cleaned ++ [value]
  return cleaned
-- impl-end

-- proof-start
theorem helper_cleanFields (fields : List FieldModel) :
    ∀ (init : List FieldValue),
      Id.run (forIn fields init (fun f r =>
        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then boundInitial f else f.data]))))) =
      init ++ fields.map cleanedValue := by
  induction fields with
  | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp only [List.map_cons, cleanedValue, List.append_assoc, List.cons_append, List.nil_append]

theorem correct_cleanFields :
    ∀ (fields : List FieldModel),
      problem_spec_cleanFields fields (implementation_cleanFields fields) := by
  intro fields
  unfold problem_spec_cleanFields implementation_cleanFields
  simp only [Id.run, bind, pure]
  have h := helper_cleanFields fields []
  simp only [Id.run, bind, pure] at h
  rw [h]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL COMPLETE.** Bundle: django__django-14631 lean. same_spec=True verified for all 8 attacks + positive control against Solution.lean (impl-region-only edits; axioms/pure/pre/post byte-identical).

**POSITIVE CONTROL:** atk_pos.lean (gold impl) — `bash scripts/lean_verify.sh atk_pos.lean` exit 0 (verifies, no sorry). `#print axioms correct_cleanFields` => [propext, Quot.sound] only — CLEAN (no sorryAx, no custom axioms; axioms region is empty).

### ATTACKS (all same-spec True; command `bash scripts/lean_verify.sh atk_N.lean`):
- atk1 (prepatch bug: disabled uses raw rawInitial, no micro-strip): exit 1 UNSOLVED GOALS at proof (goal `rawInitial = boundInitial`, false when supportsMicro=false & sub>0). Prepatch reproduced.
- atk2 (ignore disabled, always f.data): exit 3 sorry (goal false on disabled fields).
- atk3 (branches swapped: disabled->data, editable->boundInitial): exit 3 sorry.
- atk4 (order reversed: prepend [value]++cleaned): exit 3 sorry.
- atk5 (partial-domain/boundary: always []): exit 3 sorry (correct only on nil).
- atk6 (over-strip: always drop sub-second even when supportsMicro=true): exit 1 UNSOLVED GOALS (goal `ts whole 0 = if supportsMicro then ts whole sub else ts whole 0`).
- atk7 (control-flow-effect / off-by-one: skip first field): exit 3 sorry.
- atk8 (ungrounded oracle echo: constant other 0): exit 3 sorry.

No wrong impl closes with clean axioms => there is NO verifying attack requiring a materialized faithful patch + resolve run (protocol step 2 vacuous — nothing to run). verify=>correct holds: every behaviorally-wrong impl is non-verifiable.

**REFINEMENT.MD AUDIT:** legs #1,#2 = R (List FieldModel <-> ordered form fields; List FieldValue <-> cleaned_data dict-in-field-order bijection, mapping.md); #3 = I (identical `if disabled` split, matches `bf.initial if field.disabled else bf.data`); #4 = A-reference (bf.data supplied as input FieldModel.data, identity, G-CONF-validated); #5 = A-reference (boundInitial deeply models BoundField.initial micro-strip, boundfield.py:212-220, G-AX-validated — this IS the patch's behavioral discriminator, baked into cleanedValue in the postcondition, which is precisely why atk1 prepatch cannot verify); #6 = A-reference (success-path field.clean/to_python identity, form.errors=={}). NO kind-3 (no A-consumed / shipped `axiom _prop`); axioms region empty, confirmed by clean #print axioms (no sorryAx). A-reference correspondences hold: the micro-strip discriminator (#5) is the only expressible F2P behavior and it is faithfully modeled; the inexpressible re-evaluation-timing aspect is documented and is not a separate observable input->output discriminator. R/I legs mechanically covered by G-CONF.

**VERDICT:** SOUND. 8 distinct same-spec wrong impls attacked (>=5 required), positive control verifies with clean axioms, none of the wrong impls could close a clean-axiom proof, so none required a resolve run and none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean`, `atk8.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition is a tight equality `problem_spec_cleanFields fields result := result = fields.map cleanedValue` (no existential, no weakening), so every verifying impl must be extensionally equal to the oracle `fields.map cleanedValue` on ALL inputs. No same-spec wrong impl could close its correctness proof. Concrete distinguishing input for the prepatch bug (atk1): fields = [⟨disabled:=true, supportsMicro:=false, rawInitial:=ts 100 123456, data:=other 0⟩] — spec requires cleanedValue = boundInitial = ts 100 0 (sub-second dropped), but prepatch impl yields ts 100 123456; the proof goal reduces to `rawInitial = boundInitial` which is false, giving unsolved goals.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting and cleaning the submitted value of each field on a bound form.

A form has an ordered collection of fields. Cleaning the form produces, for each
field and in field order, the value that field contributes to the form's cleaned
data. For each field the value is chosen as follows:

* an *editable* field takes the value submitted for it (the data extracted from
  the form's payload for that field);
* a *disabled* field ignores any submitted payload and instead takes its own
  preset initial value — specifically the initial value exactly as the field
  itself would present it. A field presents a temporal initial value (a date or
  time) only at the precision its display can represent: if the field's display
  cannot represent sub-second precision, any sub-second component of the initial
  value is dropped before it is used. Non-temporal initial values, and temporal
  values on fields whose display does support sub-second precision, are presented
  unchanged.

The selected value is then cleaned. In the success case modeled here cleaning
preserves the selected value, so the cleaned value for each field equals the
value selected by the rule above. The cleaned data therefore has one entry per
field, in field order, with no field's entry left unconstrained.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The two outside
-- operations used per field — obtaining the field's preset initial value and
-- obtaining the value submitted for the field — have their results supplied as
-- inputs (`rawInitial`, `data`). The presentation-normalization of a temporal
-- value and the field-order traversal are spelled out concretely below.
-- axioms-end

-- pure-start
/-- A field value. `ts whole sub` is a temporal value split into its
whole-second-and-coarser component (`whole`) and its sub-second component
(`sub`, a microsecond count `0..999999`). `other n` stands in for any
non-temporal value. -/
inductive FieldValue where
  | ts (whole : Int) (sub : Nat)
  | other (n : Int)
deriving DecidableEq

/-- One field of the form together with its bound state.
* `disabled`      — whether the field is disabled;
* `supportsMicro` — whether the field's display can represent sub-second precision;
* `rawInitial`    — the field's preset initial value (already evaluated);
* `data`          — the value submitted for the field. -/
structure FieldModel where
  disabled : Bool
  supportsMicro : Bool
  rawInitial : FieldValue
  data : FieldValue
deriving DecidableEq

/-- The initial value of a field exactly as the field presents it: a temporal
value loses its sub-second component when the field's display cannot represent
sub-second precision; every other value is presented unchanged. -/
def boundInitial (f : FieldModel) : FieldValue :=
  match f.rawInitial with
  | FieldValue.ts whole sub => if f.supportsMicro then FieldValue.ts whole sub else FieldValue.ts whole 0
  | FieldValue.other n => FieldValue.other n

/-- The cleaned value contributed by one field: a disabled field uses its
presented initial value; an editable field uses its submitted value. -/
def cleanedValue (f : FieldModel) : FieldValue :=
  if f.disabled then boundInitial f else f.data
-- pure-end

-- post-conditions-start
def problem_spec_cleanFields (fields : List FieldModel) (result : List FieldValue) : Prop :=
  result = fields.map cleanedValue
-- post-conditions-end

-- impl-start
def implementation_cleanFields (fields : List FieldModel) : List FieldValue := Id.run do
  let mut cleaned : List FieldValue := []
  for f in fields do
    let value := if f.disabled then boundInitial f else f.data
    cleaned := cleaned ++ [value]
  return cleaned
-- impl-end

-- proof-start
theorem helper_cleanFields (fields : List FieldModel) :
    ∀ (init : List FieldValue),
      Id.run (forIn fields init (fun f r =>
        (do pure PUnit.unit; pure (ForInStep.yield (r ++ [if f.disabled = true then boundInitial f else f.data]))))) =
      init ++ fields.map cleanedValue := by
  induction fields with
  | nil => intro init; simp only [List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp only [List.map_cons, cleanedValue, List.append_assoc, List.cons_append, List.nil_append]

theorem correct_cleanFields :
    ∀ (fields : List FieldModel),
      problem_spec_cleanFields fields (implementation_cleanFields fields) := by
  intro fields
  unfold problem_spec_cleanFields implementation_cleanFields
  simp only [Id.run, bind, pure]
  have h := helper_cleanFields fields []
  simp only [Id.run, bind, pure] at h
  rw [h]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL COMPLETE.** Bundle: django__django-14631 lean. same_spec=True verified for all 8 attacks + positive control against Solution.lean (impl-region-only edits; axioms/pure/pre/post byte-identical).

**POSITIVE CONTROL:** atk_pos.lean (gold impl) — `bash scripts/lean_verify.sh atk_pos.lean` exit 0 (verifies, no sorry). `#print axioms correct_cleanFields` => [propext, Quot.sound] only — CLEAN (no sorryAx, no custom axioms; axioms region is empty).

### ATTACKS (all same-spec True; command `bash scripts/lean_verify.sh atk_N.lean`):
- atk1 (prepatch bug: disabled uses raw rawInitial, no micro-strip): exit 1 UNSOLVED GOALS at proof (goal `rawInitial = boundInitial`, false when supportsMicro=false & sub>0). Prepatch reproduced.
- atk2 (ignore disabled, always f.data): exit 3 sorry (goal false on disabled fields).
- atk3 (branches swapped: disabled->data, editable->boundInitial): exit 3 sorry.
- atk4 (order reversed: prepend [value]++cleaned): exit 3 sorry.
- atk5 (partial-domain/boundary: always []): exit 3 sorry (correct only on nil).
- atk6 (over-strip: always drop sub-second even when supportsMicro=true): exit 1 UNSOLVED GOALS (goal `ts whole 0 = if supportsMicro then ts whole sub else ts whole 0`).
- atk7 (control-flow-effect / off-by-one: skip first field): exit 3 sorry.
- atk8 (ungrounded oracle echo: constant other 0): exit 3 sorry.

No wrong impl closes with clean axioms => there is NO verifying attack requiring a materialized faithful patch + resolve run (protocol step 2 vacuous — nothing to run). verify=>correct holds: every behaviorally-wrong impl is non-verifiable.

**REFINEMENT.MD AUDIT:** legs #1,#2 = R (List FieldModel <-> ordered form fields; List FieldValue <-> cleaned_data dict-in-field-order bijection, mapping.md); #3 = I (identical `if disabled` split, matches `bf.initial if field.disabled else bf.data`); #4 = A-reference (bf.data supplied as input FieldModel.data, identity, G-CONF-validated); #5 = A-reference (boundInitial deeply models BoundField.initial micro-strip, boundfield.py:212-220, G-AX-validated — this IS the patch's behavioral discriminator, baked into cleanedValue in the postcondition, which is precisely why atk1 prepatch cannot verify); #6 = A-reference (success-path field.clean/to_python identity, form.errors=={}). NO kind-3 (no A-consumed / shipped `axiom _prop`); axioms region empty, confirmed by clean #print axioms (no sorryAx). A-reference correspondences hold: the micro-strip discriminator (#5) is the only expressible F2P behavior and it is faithfully modeled; the inexpressible re-evaluation-timing aspect is documented and is not a separate observable input->output discriminator. R/I legs mechanically covered by G-CONF.

**VERDICT:** SOUND. 8 distinct same-spec wrong impls attacked (>=5 required), positive control verifies with clean axioms, none of the wrong impls could close a clean-axiom proof, so none required a resolve run and none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-14631 lean bundle. Verified mechanics first: Solution.lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry); #print axioms correct_cleanFields => [propext, Quot.sound] only (no sorryAx, proof is real); same_spec(Solution, Solution_prepatch) = True under lean LanguageTables (spec region byte-identical); conformance_check.py passes (120008 cases).

Spec faithfulness vs real repo @ base 84400d2: the patch's observable change in BaseForm.`_clean_fields` is that a disabled field now takes value = bf.initial (post-patch) instead of raw get_initial_for_field (pre-patch). Real BoundField.initial (boundfield.py:212-220) does data.replace(microsecond=0) iff isinstance(data,(datetime.datetime,datetime.time)) and not widget.supports_microseconds. The model's boundInitial reproduces this EXACTLY: FieldValue.ts whole sub -> ts whole 0 when not supportsMicro, else ts whole sub; other n unchanged. cleanedValue = if disabled then boundInitial else data matches the patched 'value = bf.initial if field.disabled else bf.data'. Field-order traversal and one-entry-per-field (cleaned_data dict modeled as ordered list) also match `_bound_items` iterating self.fields in declared order.

**Searched for divergence:** (a) editable branch = f.data (identity on submitted value) — matches bf.data; (b) disabled temporal, no micro support, sub>0 -> stripped — matches; (c) disabled temporal with micro support -> kept — matches; (d) disabled non-temporal -> passthrough — matches; (e) success-path clean identity: for an already-typed datetime field.clean/to_python IS the identity, which is precisely the disabled-datetime path the F2P tests exercise (form.errors=={}). No temporal or non-temporal input yields disagreement between boundInitial/cleanedValue and the real callee. The documented inexpressible aspect (re-evaluation count of a callable initial via cached_property) is a temporal/side-effect property, not an input->output relation, and is not a separate observable discriminator beyond the modeled microsecond-strip — the spec is scoped, not over-strong. No diverging input found. Spec is FAITHFUL to the real repo behavior on the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures/warnings) and same_spec is True (spec region byte-identical between Solution.lean and Solution_prepatch.lean). Substantive review of the projected spec view: (1) no gold-diff line reproduced, no diff markers, no patched file paths (forms.py/boundfield.py); (2) no spec-view identifier echoes any distinctive patched repo symbol — FieldModel/boundInitial/cleanedValue/problem_spec_cleanFields are invented abstractions, and none of `_bound_items`/`_clean_fields`/changed_data/`_has_changed`/`_widget_data_value`/`_field_data_value` appear; (3) no bug/fix narration. The docstring abstractly specifies correct behavior (disabled field -> presented initial; sub-second component dropped when display lacks microsecond support). This discriminator is already foreshadowed in the PUBLIC problem_statement, which explicitly notes `_clean_fields`() 'can return a different value from form[name].initial' and cites test_datetime_clean_initial_callable_disabled(). The spec states correct behavior, not the gold edit, and does not reveal edit-localization beyond problem_statement. No LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
