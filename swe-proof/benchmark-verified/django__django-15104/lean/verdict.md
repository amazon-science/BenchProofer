# P2 adversarial audit — django__django-15104

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,8 +80,13 @@
     (fields : List FieldDef) : Option (List Decon) := Id.run do
   let mut acc : List Decon := []
   for f in fields do
-    let d := if f.isRelation then removeTarget f.decon else f.decon
-    acc := acc ++ [d]
+    if f.isRelation then
+      if f.decon.kwargs.any (fun kv => kv.1 == targetKey) then
+        acc := acc ++ [removeTarget f.decon]
+      else
+        return none
+    else
+      acc := acc ++ [f.decon]
   return some acc
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,44 +80,19 @@
     (fields : List FieldDef) : Option (List Decon) := Id.run do
   let mut acc : List Decon := []
   for f in fields do
-    let d := if f.isRelation then removeTarget f.decon else f.decon
-    acc := acc ++ [d]
+    acc := acc ++ [f.decon]
   return some acc
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the prefix appended to the per-field transform of the remaining fields. -/
-theorem forIn_relationAgnosticFields (fields : List FieldDef) (acc : List Decon) :
-    Id.run (forIn fields acc (fun f r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield
-            (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))))
-      = acc ++ fields.map transformField := by
-  induction fields generalizing acc with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, transformField, List.append_assoc]
-
 theorem correct_relationAgnosticFields :
     ∀ (fields : List FieldDef),
       problem_spec_relationAgnosticFields fields
         (implementation_relationAgnosticFields fields) := by
   intro fields
   unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields
-  have h : (Id.run do
-      let r ← forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon]))
-      pure (some r))
-      = some (Id.run (forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))) := rfl
-  rw [h, forIn_relationAgnosticFields]
-  simp
+  simp [Id.run]
+  induction fields with
+  | nil => rfl
+  | cons a as ih => simp_all [transformField]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,44 +80,19 @@
     (fields : List FieldDef) : Option (List Decon) := Id.run do
   let mut acc : List Decon := []
   for f in fields do
-    let d := if f.isRelation then removeTarget f.decon else f.decon
-    acc := acc ++ [d]
+    acc := acc ++ [removeTarget f.decon]
   return some acc
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the prefix appended to the per-field transform of the remaining fields. -/
-theorem forIn_relationAgnosticFields (fields : List FieldDef) (acc : List Decon) :
-    Id.run (forIn fields acc (fun f r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield
-            (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))))
-      = acc ++ fields.map transformField := by
-  induction fields generalizing acc with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, transformField, List.append_assoc]
-
 theorem correct_relationAgnosticFields :
     ∀ (fields : List FieldDef),
       problem_spec_relationAgnosticFields fields
         (implementation_relationAgnosticFields fields) := by
   intro fields
   unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields
-  have h : (Id.run do
-      let r ← forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon]))
-      pure (some r))
-      = some (Id.run (forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))) := rfl
-  rw [h, forIn_relationAgnosticFields]
-  simp
+  simp [Id.run]
+  induction fields with
+  | nil => rfl
+  | cons a as ih => simp_all [transformField]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,46 +78,25 @@
 -- impl-start
 def implementation_relationAgnosticFields
     (fields : List FieldDef) : Option (List Decon) := Id.run do
-  let mut acc : List Decon := []
-  for f in fields do
-    let d := if f.isRelation then removeTarget f.decon else f.decon
-    acc := acc ++ [d]
-  return some acc
+  match fields with
+  | [] => return none
+  | _ =>
+    let mut acc : List Decon := []
+    for f in fields do
+      let d := if f.isRelation then removeTarget f.decon else f.decon
+      acc := acc ++ [d]
+    return some acc
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the prefix appended to the per-field transform of the remaining fields. -/
-theorem forIn_relationAgnosticFields (fields : List FieldDef) (acc : List Decon) :
-    Id.run (forIn fields acc (fun f r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield
-            (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))))
-      = acc ++ fields.map transformField := by
-  induction fields generalizing acc with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, transformField, List.append_assoc]
-
 theorem correct_relationAgnosticFields :
     ∀ (fields : List FieldDef),
       problem_spec_relationAgnosticFields fields
         (implementation_relationAgnosticFields fields) := by
   intro fields
   unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields
-  have h : (Id.run do
-      let r ← forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon]))
-      pure (some r))
-      = some (Id.run (forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))) := rfl
-  rw [h, forIn_relationAgnosticFields]
-  simp
+  simp [Id.run]
+  induction fields with
+  | nil => rfl
+  | cons a as ih => simp_all [transformField]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,43 +81,19 @@
   let mut acc : List Decon := []
   for f in fields do
     let d := if f.isRelation then removeTarget f.decon else f.decon
-    acc := acc ++ [d]
+    acc := d :: acc
   return some acc
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the prefix appended to the per-field transform of the remaining fields. -/
-theorem forIn_relationAgnosticFields (fields : List FieldDef) (acc : List Decon) :
-    Id.run (forIn fields acc (fun f r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield
-            (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))))
-      = acc ++ fields.map transformField := by
-  induction fields generalizing acc with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, transformField, List.append_assoc]
-
 theorem correct_relationAgnosticFields :
     ∀ (fields : List FieldDef),
       problem_spec_relationAgnosticFields fields
         (implementation_relationAgnosticFields fields) := by
   intro fields
   unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields
-  have h : (Id.run do
-      let r ← forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon]))
-      pure (some r))
-      = some (Id.run (forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))) := rfl
-  rw [h, forIn_relationAgnosticFields]
-  simp
+  simp [Id.run]
+  induction fields with
+  | nil => rfl
+  | cons a as ih => simp_all [transformField]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,47 +77,19 @@
 
 -- impl-start
 def implementation_relationAgnosticFields
-    (fields : List FieldDef) : Option (List Decon) := Id.run do
-  let mut acc : List Decon := []
-  for f in fields do
-    let d := if f.isRelation then removeTarget f.decon else f.decon
-    acc := acc ++ [d]
-  return some acc
+    (fields : List FieldDef) : Option (List Decon) :=
+  some []
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the prefix appended to the per-field transform of the remaining fields. -/
-theorem forIn_relationAgnosticFields (fields : List FieldDef) (acc : List Decon) :
-    Id.run (forIn fields acc (fun f r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield
-            (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))))
-      = acc ++ fields.map transformField := by
-  induction fields generalizing acc with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, transformField, List.append_assoc]
-
 theorem correct_relationAgnosticFields :
     ∀ (fields : List FieldDef),
       problem_spec_relationAgnosticFields fields
         (implementation_relationAgnosticFields fields) := by
   intro fields
   unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields
-  have h : (Id.run do
-      let r ← forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon]))
-      pure (some r))
-      = some (Id.run (forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))) := rfl
-  rw [h, forIn_relationAgnosticFields]
-  simp
+  simp [Id.run]
+  induction fields with
+  | nil => rfl
+  | cons a as ih => simp_all [transformField]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,44 +80,20 @@
     (fields : List FieldDef) : Option (List Decon) := Id.run do
   let mut acc : List Decon := []
   for f in fields do
-    let d := if f.isRelation then removeTarget f.decon else f.decon
+    let d := if f.isRelation then f.decon else removeTarget f.decon
     acc := acc ++ [d]
   return some acc
 -- impl-end
 
 -- proof-start
-/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
-equals the prefix appended to the per-field transform of the remaining fields. -/
-theorem forIn_relationAgnosticFields (fields : List FieldDef) (acc : List Decon) :
-    Id.run (forIn fields acc (fun f r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield
-            (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))))
-      = acc ++ fields.map transformField := by
-  induction fields generalizing acc with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons, transformField, List.append_assoc]
-
 theorem correct_relationAgnosticFields :
     ∀ (fields : List FieldDef),
       problem_spec_relationAgnosticFields fields
         (implementation_relationAgnosticFields fields) := by
   intro fields
   unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields
-  have h : (Id.run do
-      let r ← forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon]))
-      pure (some r))
-      = some (Id.run (forIn fields ([] : List Decon) fun f r => do
-            pure PUnit.unit
-            pure (ForInStep.yield
-              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))) := rfl
-  rw [h, forIn_relationAgnosticFields]
-  simp
+  simp [Id.run]
+  induction fields with
+  | nil => rfl
+  | cons a as ih => simp_all [transformField]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Normalizing a model's field deconstructions so that related-field targets are
ignored (used when detecting renamed models).

Each field of a model is reduced to a deconstruction: an import path, a list of
positional arguments, and a keyword mapping (unique keys). For the purpose of
comparing models up to renames, a field that points at another model must be
made target-agnostic: the entry recording its target model is dropped from the
keyword mapping, while every other component of the deconstruction is carried
over verbatim. A field that does not point at another model is carried over
unchanged.

The normalization visits the fields in their given order and collects the
transformed deconstructions in that same order. It is defined for every field —
in particular, dropping the target entry of a related field is well defined even
when that field's keyword mapping does not record a target at all (in which case
there is nothing to drop and the mapping is carried over as is). The result is
therefore always produced (it is never undefined) and is fully determined by the
input fields.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Producing each
-- field's deconstruction (its path, positional arguments, and keyword mapping)
-- and the test of whether a field points at another model are folded into the
-- input representation `FieldDef`; the only operation the normalization performs
-- on its own — removing the target entry from a related field's keyword mapping
-- — is modeled directly as an association-list filter. So no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- A field's deconstruction: an import path, positional arguments, and a keyword
mapping with unique keys (modeled as an association list of key → value-token). -/
structure Decon where
  path : String
  args : List String
  kwargs : List (String × String)
deriving DecidableEq, Repr

/-- A field as the normalization observes it: whether it points at another model
(`isRelation`), together with its deconstruction. -/
structure FieldDef where
  isRelation : Bool
  decon : Decon
deriving DecidableEq, Repr

/-- The distinguished keyword key recording a related field's target model. -/
def targetKey : String := "to"

/-- Drop the target-model entry from a deconstruction's keyword mapping. Removing
an entry that is absent leaves the mapping unchanged (the keys are unique, so at
most one such entry exists). -/
def removeTarget (d : Decon) : Decon :=
  { d with kwargs := d.kwargs.filter (fun kv => kv.1 != targetKey) }

/-- The transform applied to a single field: a related field is made
target-agnostic; any other field is carried over unchanged. -/
def transformField (f : FieldDef) : Decon :=
  if f.isRelation then removeTarget f.decon else f.decon
-- pure-end

-- post-conditions-start
/-- The normalization is total (it always produces a result) and that result is
the list of per-field transforms, in the input order: each related field has its
target entry removed, every other field is carried over verbatim, and no field is
dropped, duplicated, or reordered (directive 5 frame — the path, the positional
arguments, and the non-target keyword entries are pinned to their input values
for every field). -/
def problem_spec_relationAgnosticFields
    (fields : List FieldDef) (result : Option (List Decon)) : Prop :=
  result = some (fields.map transformField)
-- post-conditions-end

-- impl-start
def implementation_relationAgnosticFields
    (fields : List FieldDef) : Option (List Decon) := Id.run do
  let mut acc : List Decon := []
  for f in fields do
    let d := if f.isRelation then removeTarget f.decon else f.decon
    acc := acc ++ [d]
  return some acc
-- impl-end

-- proof-start
/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
equals the prefix appended to the per-field transform of the remaining fields. -/
theorem forIn_relationAgnosticFields (fields : List FieldDef) (acc : List Decon) :
    Id.run (forIn fields acc (fun f r =>
      (do pure PUnit.unit;
          pure (ForInStep.yield
            (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))))
      = acc ++ fields.map transformField := by
  induction fields generalizing acc with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.map_cons, transformField, List.append_assoc]

theorem correct_relationAgnosticFields :
    ∀ (fields : List FieldDef),
      problem_spec_relationAgnosticFields fields
        (implementation_relationAgnosticFields fields) := by
  intro fields
  unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields
  have h : (Id.run do
      let r ← forIn fields ([] : List Decon) fun f r => do
            pure PUnit.unit
            pure (ForInStep.yield
              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon]))
      pure (some r))
      = some (Id.run (forIn fields ([] : List Decon) fun f r => do
            pure PUnit.unit
            pure (ForInStep.yield
              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))) := rfl
  rw [h, forIn_relationAgnosticFields]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec = single TOTAL EXACT equation: problem_spec_relationAgnosticFields fields result := result = some (fields.map transformField). This pins the output as an exact function of the input for ALL inputs (totality: always `some`; elementwise: each related field's decon has 'to' filtered, each other field carried verbatim; order/length pinned). Any verifying impl is therefore forced extensionally equal to gold — no room for a same-spec wrong impl to close.

Protocol: byte-identical spec confirmed via swebench_unified.markers.same_spec = True for pos_control + all 7 attacks (axioms/pure/pre/post regions untouched; only impl+proof edited — and the Lean spec_view collapses BOTH impl and proof to placeholders, so edits there are spec-invisible). Positive control (gold) verifies: lean_verify.sh exit 0, and `#print axioms correct_relationAgnosticFields` = [propext, Quot.sound] only (NO sorryAx) — clean.

7 DISTINCT same-spec wrong impls, each given a best-effort closing proof (gold-style induction / simp), verified concurrently (2 background batches, <=4 jobs):
  atk_1 = prepatch bug (return none when a relation field's kwargs lack 'to' — the real KeyError; F2P test_add_custom_fk_with_hardcoded_to): lean_verify EXIT=1. Prepatch bug reproduced.
  atk_2 = control-flow-effect: never removes target (identity carry-over for all): EXIT=1.
  atk_3 = boundary: removes target from ALL fields incl non-relation: EXIT=1.
  atk_4 = partial-domain: return none on empty list, correct otherwise: EXIT=1.
  atk_5 = reorder/reversal: prepends (d :: acc) so output reversed: EXIT=1.
  atk_6 = ungrounded-oracle echo: `some []` ignoring input: EXIT=1.
  atk_7 = inverted branch: removes target only from NON-relation fields: EXIT=1.
All 7 EXIT=1 = genuine unification failures (residual goals show none=some or mismatched cons heads); none EXIT=0/3/124 (no verify, no sorry-close, no timeout). Command per attack: `bash scripts/lean_verify.sh <atk_N.lean>`.

Step 2 (materialize+resolve for any closing wrong impl) is VACUOUS: zero wrong impls closed, so no faithful patch needed to be run. verify=>correct holds.

Refinement audit (refinement.md + mapping.md): every leg is R or I (rows 1 R, 2 I, 3 I, 4 I, 5 I, 6 I, 7 R); NO A-legs (axioms=[], deep_model_references=[]) — the two callee operations (deep_deconstruct result + remote_field.model truthiness) are UPSTREAM/UNCHANGED and folded into the input FieldDef, and the sole changed op (pop('to',None)) is modeled DEEPLY as assoc-list filter removeTarget. axiom_check.py is a legitimate skip stub consistent with this (no callee contract to validate). No kind-3 ungrounded oracle: output is DEFINED as fields.map transformField over the actual input. A-leg correspondence check: N/A (no A-legs). The A-leg protocol focus is thus vacuously satisfied; R/I legs are G-CONF territory and the differential shadow==oracle is exercised over relation/non-relation x target-present/absent incl the KeyError edge.

Runs performed in scratch only.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Normalizing a model's field deconstructions so that related-field targets are
ignored (used when detecting renamed models).

Each field of a model is reduced to a deconstruction: an import path, a list of
positional arguments, and a keyword mapping (unique keys). For the purpose of
comparing models up to renames, a field that points at another model must be
made target-agnostic: the entry recording its target model is dropped from the
keyword mapping, while every other component of the deconstruction is carried
over verbatim. A field that does not point at another model is carried over
unchanged.

The normalization visits the fields in their given order and collects the
transformed deconstructions in that same order. It is defined for every field —
in particular, dropping the target entry of a related field is well defined even
when that field's keyword mapping does not record a target at all (in which case
there is nothing to drop and the mapping is carried over as is). The result is
therefore always produced (it is never undefined) and is fully determined by the
input fields.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Producing each
-- field's deconstruction (its path, positional arguments, and keyword mapping)
-- and the test of whether a field points at another model are folded into the
-- input representation `FieldDef`; the only operation the normalization performs
-- on its own — removing the target entry from a related field's keyword mapping
-- — is modeled directly as an association-list filter. So no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- A field's deconstruction: an import path, positional arguments, and a keyword
mapping with unique keys (modeled as an association list of key → value-token). -/
structure Decon where
  path : String
  args : List String
  kwargs : List (String × String)
deriving DecidableEq, Repr

/-- A field as the normalization observes it: whether it points at another model
(`isRelation`), together with its deconstruction. -/
structure FieldDef where
  isRelation : Bool
  decon : Decon
deriving DecidableEq, Repr

/-- The distinguished keyword key recording a related field's target model. -/
def targetKey : String := "to"

/-- Drop the target-model entry from a deconstruction's keyword mapping. Removing
an entry that is absent leaves the mapping unchanged (the keys are unique, so at
most one such entry exists). -/
def removeTarget (d : Decon) : Decon :=
  { d with kwargs := d.kwargs.filter (fun kv => kv.1 != targetKey) }

/-- The transform applied to a single field: a related field is made
target-agnostic; any other field is carried over unchanged. -/
def transformField (f : FieldDef) : Decon :=
  if f.isRelation then removeTarget f.decon else f.decon
-- pure-end

-- post-conditions-start
/-- The normalization is total (it always produces a result) and that result is
the list of per-field transforms, in the input order: each related field has its
target entry removed, every other field is carried over verbatim, and no field is
dropped, duplicated, or reordered (directive 5 frame — the path, the positional
arguments, and the non-target keyword entries are pinned to their input values
for every field). -/
def problem_spec_relationAgnosticFields
    (fields : List FieldDef) (result : Option (List Decon)) : Prop :=
  result = some (fields.map transformField)
-- post-conditions-end

-- impl-start
def implementation_relationAgnosticFields
    (fields : List FieldDef) : Option (List Decon) := Id.run do
  let mut acc : List Decon := []
  for f in fields do
    let d := if f.isRelation then removeTarget f.decon else f.decon
    acc := acc ++ [d]
  return some acc
-- impl-end

-- proof-start
/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
equals the prefix appended to the per-field transform of the remaining fields. -/
theorem forIn_relationAgnosticFields (fields : List FieldDef) (acc : List Decon) :
    Id.run (forIn fields acc (fun f r =>
      (do pure PUnit.unit;
          pure (ForInStep.yield
            (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))))
      = acc ++ fields.map transformField := by
  induction fields generalizing acc with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.map_cons, transformField, List.append_assoc]

theorem correct_relationAgnosticFields :
    ∀ (fields : List FieldDef),
      problem_spec_relationAgnosticFields fields
        (implementation_relationAgnosticFields fields) := by
  intro fields
  unfold problem_spec_relationAgnosticFields implementation_relationAgnosticFields
  have h : (Id.run do
      let r ← forIn fields ([] : List Decon) fun f r => do
            pure PUnit.unit
            pure (ForInStep.yield
              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon]))
      pure (some r))
      = some (Id.run (forIn fields ([] : List Decon) fun f r => do
            pure PUnit.unit
            pure (ForInStep.yield
              (r ++ [if f.isRelation = true then removeTarget f.decon else f.decon])))) := rfl
  rw [h, forIn_relationAgnosticFields]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec = single TOTAL EXACT equation: problem_spec_relationAgnosticFields fields result := result = some (fields.map transformField). This pins the output as an exact function of the input for ALL inputs (totality: always `some`; elementwise: each related field's decon has 'to' filtered, each other field carried verbatim; order/length pinned). Any verifying impl is therefore forced extensionally equal to gold — no room for a same-spec wrong impl to close.

Protocol: byte-identical spec confirmed via swebench_unified.markers.same_spec = True for pos_control + all 7 attacks (axioms/pure/pre/post regions untouched; only impl+proof edited — and the Lean spec_view collapses BOTH impl and proof to placeholders, so edits there are spec-invisible). Positive control (gold) verifies: lean_verify.sh exit 0, and `#print axioms correct_relationAgnosticFields` = [propext, Quot.sound] only (NO sorryAx) — clean.

7 DISTINCT same-spec wrong impls, each given a best-effort closing proof (gold-style induction / simp), verified concurrently (2 background batches, <=4 jobs):
  atk_1 = prepatch bug (return none when a relation field's kwargs lack 'to' — the real KeyError; F2P test_add_custom_fk_with_hardcoded_to): lean_verify EXIT=1. Prepatch bug reproduced.
  atk_2 = control-flow-effect: never removes target (identity carry-over for all): EXIT=1.
  atk_3 = boundary: removes target from ALL fields incl non-relation: EXIT=1.
  atk_4 = partial-domain: return none on empty list, correct otherwise: EXIT=1.
  atk_5 = reorder/reversal: prepends (d :: acc) so output reversed: EXIT=1.
  atk_6 = ungrounded-oracle echo: `some []` ignoring input: EXIT=1.
  atk_7 = inverted branch: removes target only from NON-relation fields: EXIT=1.
All 7 EXIT=1 = genuine unification failures (residual goals show none=some or mismatched cons heads); none EXIT=0/3/124 (no verify, no sorry-close, no timeout). Command per attack: `bash scripts/lean_verify.sh <atk_N.lean>`.

Step 2 (materialize+resolve for any closing wrong impl) is VACUOUS: zero wrong impls closed, so no faithful patch needed to be run. verify=>correct holds.

Refinement audit (refinement.md + mapping.md): every leg is R or I (rows 1 R, 2 I, 3 I, 4 I, 5 I, 6 I, 7 R); NO A-legs (axioms=[], deep_model_references=[]) — the two callee operations (deep_deconstruct result + remote_field.model truthiness) are UPSTREAM/UNCHANGED and folded into the input FieldDef, and the sole changed op (pop('to',None)) is modeled DEEPLY as assoc-list filter removeTarget. axiom_check.py is a legitimate skip stub consistent with this (no callee contract to validate). No kind-3 ungrounded oracle: output is DEFINED as fields.map transformField over the actual input. A-leg correspondence check: N/A (no A-legs). The A-leg protocol focus is thus vacuously satisfied; R/I legs are G-CONF territory and the differential shadow==oracle is exercised over relation/non-relation x target-present/absent incl the KeyError edge.

Runs performed in scratch only.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-15104, modeled function relationAgnosticFields ↔ MigrationAutodetector.only_relation_agnostic_fields (django/db/migrations/autodetector.py). Real repo at base_commit shows the POST-PATCH (gold) body: for each field in sorted(fields.items()), deconstruction = deep_deconstruct(field); if field.remote_field and field.remote_field.model: deconstruction[2].pop('to', None); append; return list (always returns, never raises for the modeled op).

Spec: problem_spec_relationAgnosticFields fields result := result = some (fields.map transformField), where transformField f = if f.isRelation then removeTarget f.decon else f.decon, and removeTarget drops kwargs entries with key = "to" via List.filter. Total on all inputs, some-wrapped.

Verification performed:
1. lean_verify.sh Solution.lean → exit 0 (compiles, no sorry/error).
2. #print axioms correct_relationAgnosticFields → [propext, Quot.sound]; NO sorryAx — proof is genuine, not stubbed.
3. swebench_unified markers same_spec(Solution, Solution_prepatch, LeanBackend.language) → True: spec region byte-identical, so the shared spec is what both impls are held to (prepatch returns none on relation-field-without-'to', which correctly fails the totality clause = the F2P discriminator test_add_custom_fk_with_hardcoded_to).
4. conformance_check.py → checked=120400 disagreements=0 (edge set relation/non-relation × target-present/absent × len 0..3, plus 120000 fuzzed lists incl. relation fields lacking 'to').

Faithfulness analysis — no divergence on the reachable domain:
- deep_deconstruct (unchanged upstream callee) and the remote_field.model truthiness are folded into FieldDef (decon, isRelation). This is a legitimate input fold of unchanged upstream code, not a modeling of the changed op.
- removeTarget = filter(key != 'to') removes ALL 'to' entries, whereas dict.pop('to', None) removes the single one. This differs only for duplicate-key kwargs — but deep_deconstruct produces its kwargs from a real Python dict ({key: ... for key,value in kwargs.items()}), which has unique keys, so at most one 'to' entry ever exists on any reachable input. On unique-key inputs filter and pop coincide exactly (removal of the one entry, no-op when absent). Duplicate-key lists are outside the faithful domain and are not a real-repo behavior.
- path/args carried verbatim ({d with kwargs := …}); output order = input order; length preserved; totality matches post-patch (which never raises for this op). No output component is ungrounded or over-constrained relative to the real callee.

I could not construct any input (in the modeled abstraction, corresponding to a real reachable field list) on which the spec disagrees with the post-patch callee. Spec is neither too strong nor drifted. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage screen over the solver-visible spec view of Solution.lean (docstring, axioms comment, pure defs Decon/FieldDef/targetKey/removeTarget/transformField, and problem_spec_relationAgnosticFields). Impl and proof regions are hidden from the solver and excluded.

The public problem_statement for django__django-15104 is EXTREMELY disclosive: it names only_relation_agnostic_fields, deep_deconstruct, deconstruction, remote_field, and the 'to' key, gives the exact traceback line (autodetector.py:99 `del deconstruction[2]['to']` -> KeyError: 'to'), and quotes the gold fix verbatim ('Changing del deconstruction[2]['to'] to deconstruction[2].pop('to', None) ... makes my test suite run again'). Both the old and the replacement lines are already public. The leakage bar is therefore very high.

Against that baseline the spec view leaks nothing beyond the public statement:
- No patched file path (django/db/migrations/autodetector.py) appears.
- No verbatim gold-diff line: neither `del deconstruction[2]['to']`, `pop('to', None)`, nor `only_relation_agnostic_fields` appears; Lean names are abstract (relationAgnosticFields/removeTarget/transformField, none present in the visible view as identifiers tied to the diff).
- The 'to' key is abstracted as `targetKey := "to"` / 'the entry recording its target model' — and 'to' is public in problem_statement anyway.
- The totality/'well defined when no target entry is recorded' language paraphrases the exact bug already described publicly; it does not reveal anything not in the problem_statement.
- No narration words, no answer-key echo; the postcondition is grounded elementwise in the input (fields.map transformField).

mapping.md/refinement.md are auditor docs, not part of the solver spec view, so their explicit gold-line quotes are out of scope for G-LEAK. Verdict: NO-LEAKAGE.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
