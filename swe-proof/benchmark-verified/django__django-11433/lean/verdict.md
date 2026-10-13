# P2 adversarial audit — django__django-11433

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
None found. The spec problem_spec_bindFields pins result = assignmentsFor nf sk fields (exact functional equality), so any impl that closes correct_bindFields must be extensionally equal to the gold model on all inputs. The only same-spec impl that verified is the oracle echo (atk_7: implementation := assignmentsFor), whose faithful refined patch is exactly the gold patch and RESOLVES under the official harness. No verify-but-incorrect impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -127,7 +127,7 @@
     -- Leave a defaulted field at its default only when no meaningful value was
     -- supplied: the value was omitted from the payload and the resolved value is
     -- itself an empty sentinel.
-    if f.hasDefault && f.omitted && f.resolvedEmpty then
+    if f.hasDefault && f.omitted then
       continue
     -- Defer file fields to a second pass; assign everything else now.
     if f.isFile then
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -134,7 +134,7 @@
       fileFields := fileFields ++ [(f.name, f.resolvedValue)]
     else
       assigned := assigned ++ [(f.name, f.resolvedValue)]
-  return assigned ++ fileFields
+  return fileFields ++ assigned
 -- impl-end
 
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -117,10 +117,7 @@
     -- Skip fields that cannot or need not receive a resolved value.
     if !f.editable || f.isAuto || !f.inResolved then
       continue
-    -- Honor an explicit field-name restriction.
-    if let some names := nameFilter then
-      if !names.contains f.name then
-        continue
+    -- (bug) name filter ignored
     -- Honor a non-empty set of names to skip.
     if !skipNames.isEmpty && skipNames.contains f.name then
       continue
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -129,11 +129,8 @@
     -- itself an empty sentinel.
     if f.hasDefault && f.omitted && f.resolvedEmpty then
       continue
-    -- Defer file fields to a second pass; assign everything else now.
-    if f.isFile then
-      fileFields := fileFields ++ [(f.name, f.resolvedValue)]
-    else
-      assigned := assigned ++ [(f.name, f.resolvedValue)]
+    -- (bug) no deferral: assign every kept field in one pass
+    assigned := assigned ++ [(f.name, f.resolvedValue)]
   return assigned ++ fileFields
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -115,7 +115,7 @@
   let mut fileFields : List (String × String) := []
   for f in fields do
     -- Skip fields that cannot or need not receive a resolved value.
-    if !f.editable || f.isAuto || !f.inResolved then
+    if !f.editable || !f.inResolved then
       continue
     -- Honor an explicit field-name restriction.
     if let some names := nameFilter then
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,9 +131,9 @@
       continue
     -- Defer file fields to a second pass; assign everything else now.
     if f.isFile then
-      fileFields := fileFields ++ [(f.name, f.resolvedValue)]
+      fileFields := fileFields ++ [(f.name, f.name)]
     else
-      assigned := assigned ++ [(f.name, f.resolvedValue)]
+      assigned := assigned ++ [(f.name, f.name)]
   return assigned ++ fileFields
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -110,145 +110,17 @@
 -- impl-start
 def implementation_bindFields (nameFilter : Option (List String))
     (skipNames : List String) (fields : List FieldInput) :
-    List (String × String) := Id.run do
-  let mut assigned : List (String × String) := []
-  let mut fileFields : List (String × String) := []
-  for f in fields do
-    -- Skip fields that cannot or need not receive a resolved value.
-    if !f.editable || f.isAuto || !f.inResolved then
-      continue
-    -- Honor an explicit field-name restriction.
-    if let some names := nameFilter then
-      if !names.contains f.name then
-        continue
-    -- Honor a non-empty set of names to skip.
-    if !skipNames.isEmpty && skipNames.contains f.name then
-      continue
-    -- Leave a defaulted field at its default only when no meaningful value was
-    -- supplied: the value was omitted from the payload and the resolved value is
-    -- itself an empty sentinel.
-    if f.hasDefault && f.omitted && f.resolvedEmpty then
-      continue
-    -- Defer file fields to a second pass; assign everything else now.
-    if f.isFile then
-      fileFields := fileFields ++ [(f.name, f.resolvedValue)]
-    else
-      assigned := assigned ++ [(f.name, f.resolvedValue)]
-  return assigned ++ fileFields
+    List (String × String) :=
+  assignmentsFor nameFilter skipNames fields
 -- impl-end
 
 
 -- proof-start
-/-- The per-field state transition of the desugared loop: given the current
-`(assigned, fileFields)` pair and a field, leave the state unchanged if the
-field fails `assignField`, else append its emitted assignment to the file
-accumulator (if it is a file field) or to the non-file accumulator. -/
-def step (nf : Option (List String)) (sk : List String)
-    (st : List (String × String) × List (String × String)) (f : FieldInput) :
-    List (String × String) × List (String × String) :=
-  if assignField nf sk f then
-    (if f.isFile then (st.1, st.2 ++ [emit f]) else (st.1 ++ [emit f], st.2))
-  else st
-
-/-- Invariant relating the two accumulators after processing a prefix `p` to the
-filtered-mapped sublists of the kept fields of `p`. -/
-def FoldInv (nf : Option (List String)) (sk : List String)
-    (p : List FieldInput) (assigned fileFields : List (String × String)) : Prop :=
-  assigned = ((p.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit
-    ∧ fileFields = ((p.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit
-
-/-- Generalized-accumulator form of the desugared implementation loop: running the
-`for` loop from an arbitrary initial `(assigned, fileFields)` pair yields exactly the
-left fold of `step` over the fields from that pair. This isolates the fragile
-`Id.run`/`forIn`→`foldl` bridge behind a clean statement that inducts on `fields`
-generalizing the accumulators, so `impl_as_foldl` follows by instantiating at `([],[])`. -/
-theorem impl_loop_eq_foldl (nameFilter : Option (List String)) (skipNames : List String)
-    (fields : List FieldInput) (a0 ff0 : List (String × String)) :
-    (Id.run do
-      let mut assigned := a0
-      let mut fileFields := ff0
-      for f in fields do
-        if !f.editable || f.isAuto || !f.inResolved then
-          continue
-        if let some names := nameFilter then
-          if !names.contains f.name then
-            continue
-        if !skipNames.isEmpty && skipNames.contains f.name then
-          continue
-        if f.hasDefault && f.omitted && f.resolvedEmpty then
-          continue
-        if f.isFile then
-          fileFields := fileFields ++ [(f.name, f.resolvedValue)]
-        else
-          assigned := assigned ++ [(f.name, f.resolvedValue)]
-      return (assigned, fileFields))
-    = fields.foldl (step nameFilter skipNames) (a0, ff0) := by
-  simp only [Id.run, bind, pure, ← apply_ite ForInStep.yield]
-  rcases nameFilter with _ | names <;>
-    simp only [← apply_ite ForInStep.yield, List.forIn_yield_eq_foldl] <;>
-    · induction fields generalizing a0 ff0 with
-      | nil => rfl
-      | cons f fs ih =>
-        simp only [List.foldl_cons, step, assignField]
-        rw [ih]
-        clear ih
-        congr 1 <;>
-          simp only [emit] <;>
-          split_ifs <;>
-          grind
-
-theorem impl_as_foldl (nameFilter : Option (List String)) (skipNames : List String)
-    (fields : List FieldInput) :
-    implementation_bindFields nameFilter skipNames fields
-      = (fun st => st.1 ++ st.2) (fields.foldl (step nameFilter skipNames) ([], [])) := by
-  rw [← impl_loop_eq_foldl nameFilter skipNames fields [] []]
-  rfl
-
-theorem guards_iff_assignField (nameFilter : Option (List String))
-    (skipNames : List String) (f : FieldInput) :
-    (¬(!f.editable || f.isAuto || !f.inResolved) ∧
-      (match nameFilter with | some names => names.contains f.name | none => True) ∧
-      ¬(!skipNames.isEmpty && skipNames.contains f.name) ∧
-      ¬(f.hasDefault && f.omitted && f.resolvedEmpty))
-    ↔ assignField nameFilter skipNames f = true := by
-  cases nameFilter <;>
-    simp only [assignField, Bool.and_eq_true, Bool.or_eq_true, Bool.not_eq_true,
-      Bool.not_eq_true', not_or, not_and] <;>
-    (cases f.editable <;> cases f.isAuto <;> cases f.inResolved <;>
-      cases f.hasDefault <;> cases f.omitted <;> cases f.resolvedEmpty <;>
-      cases skipNames.isEmpty <;> cases skipNames.contains f.name <;> simp_all)
-
-theorem foldl_step_general (nf : Option (List String)) (sk : List String)
-    (p : List FieldInput) (a0 ff0 : List (String × String)) :
-    p.foldl (step nf sk) (a0, ff0)
-      = (a0 ++ ((p.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit,
-         ff0 ++ ((p.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit) := by
-  induction p generalizing a0 ff0 with
-  | nil => simp
-  | cons f rest ih =>
-    simp only [List.foldl_cons, List.filter_cons, step]
-    by_cases h : assignField nf sk f = true
-    · by_cases hf : f.isFile = true
-      · simp [h, hf, ih, List.append_assoc]
-      · simp only [Bool.not_eq_true] at hf
-        simp [h, hf, ih, List.append_assoc]
-    · simp only [Bool.not_eq_true] at h
-      simp [h, ih]
-
-theorem FoldInv_final (nf : Option (List String)) (sk : List String)
-    (fields : List FieldInput) :
-    fields.foldl (step nf sk) ([], [])
-      = (((fields.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit,
-         ((fields.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit) := by
-  simpa using foldl_step_general nf sk fields [] []
-
 theorem correct_bindFields :
     ∀ (nameFilter : Option (List String)) (skipNames : List String)
       (fields : List FieldInput),
       problem_spec_bindFields nameFilter skipNames fields
         (implementation_bindFields nameFilter skipNames fields) := by
   intro nameFilter skipNames fields
-  unfold problem_spec_bindFields assignmentsFor
-  rw [impl_as_foldl, FoldInv_final]
-
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a model object's field assignments from the resolved data of a bound
form.

The routine walks the model's fields in order and, for each one, decides whether
to assign the form's resolved value to that field or to leave the field holding
the value it already carries (its model-level default). A field is assigned its
resolved value exactly when all of the following hold:

* the field is editable and is not an auto-generated key field;
* the field has a resolved value available (it appears in the resolved data);
* if the caller restricted the work to an explicit set of field names, the
  field's name is in that set;
* if the caller supplied a non-empty set of names to skip, the field's name is
  not among them;
* it is NOT the case that the field both carries a model-level default AND had
  its value omitted from the submitted payload AND its resolved value is itself
  one of the field's "empty" sentinels. In other words, a field that has a
  default is left at that default only when no meaningful value was supplied for
  it; a non-empty resolved value always takes precedence over the default.

Assignments are emitted in two passes: first every eligible non-file field in
field order, then every eligible file field in field order (file fields are
deferred so that a later field's value is available when their value is
computed). Each emitted assignment records the field's name together with the
resolved value assigned to it; a field left at its default emits nothing.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Every per-field predicate
-- the routine consults (editability, auto-key test, availability of a resolved
-- value, presence of a default, whether the value was omitted from the payload,
-- whether the resolved value is an empty sentinel, file-field test) is supplied
-- as a boolean field of the per-field input record; the assignment-selection
-- logic is spelled out concretely below.
-- axioms-end

-- pure-start
/-- The observable per-field state the routine reads on one loop iteration,
together with the resolved value that would be assigned. -/
structure FieldInput where
  /-- the field's name -/
  name : String
  /-- the field may be written by a form -/
  editable : Bool
  /-- the field is an auto-generated key field -/
  isAuto : Bool
  /-- a resolved value for this field is available -/
  inResolved : Bool
  /-- the field carries a model-level default -/
  hasDefault : Bool
  /-- the field's value was omitted from the submitted payload -/
  omitted : Bool
  /-- the resolved value is one of the field's "empty" sentinels -/
  resolvedEmpty : Bool
  /-- the field stores a file and is therefore deferred to the second pass -/
  isFile : Bool
  /-- the resolved value that would be assigned to the field -/
  resolvedValue : String
deriving Repr, DecidableEq

/-- Whether a field is assigned its resolved value (rather than left at its
default). Encodes the full chain of skip-conditions as a single conjunction. -/
def assignField (nameFilter : Option (List String)) (skipNames : List String)
    (f : FieldInput) : Bool :=
  f.editable && !f.isAuto && f.inResolved
    && (match nameFilter with
        | some names => names.contains f.name
        | none => true)
    && !(!skipNames.isEmpty && skipNames.contains f.name)
    && !(f.hasDefault && f.omitted && f.resolvedEmpty)

/-- One emitted assignment: the field's name paired with the value assigned. -/
def emit (f : FieldInput) : String × String := (f.name, f.resolvedValue)

/-- The assignments the routine performs, in execution order: eligible non-file
fields first (field order), then eligible file fields (field order). -/
def assignmentsFor (nameFilter : Option (List String)) (skipNames : List String)
    (fields : List FieldInput) : List (String × String) :=
  let kept := fields.filter (assignField nameFilter skipNames)
  (kept.filter (fun f => !f.isFile)).map emit
    ++ (kept.filter (fun f => f.isFile)).map emit
-- pure-end

-- post-conditions-start
/-- Input→output relation for building the field assignments.

Inputs:
* `nameFilter` — `none` if the caller imposed no field-name restriction, else
  `some names` to restrict work to those names;
* `skipNames`  — names to skip (effective only when non-empty);
* `fields`     — the model's fields, in order, each with its observable state.

The result is the exact sequence of `(name, value)` assignments performed, with
the file-field deferral reflected in the ordering. It is fully pinned: every
field that qualifies contributes its emitted assignment, every field that does
not contributes nothing, and the order is the two-pass order. -/
def problem_spec_bindFields (nameFilter : Option (List String))
    (skipNames : List String) (fields : List FieldInput)
    (result : List (String × String)) : Prop :=
  result = assignmentsFor nameFilter skipNames fields
-- post-conditions-end

-- impl-start
def implementation_bindFields (nameFilter : Option (List String))
    (skipNames : List String) (fields : List FieldInput) :
    List (String × String) := Id.run do
  let mut assigned : List (String × String) := []
  let mut fileFields : List (String × String) := []
  for f in fields do
    -- Skip fields that cannot or need not receive a resolved value.
    if !f.editable || f.isAuto || !f.inResolved then
      continue
    -- Honor an explicit field-name restriction.
    if let some names := nameFilter then
      if !names.contains f.name then
        continue
    -- Honor a non-empty set of names to skip.
    if !skipNames.isEmpty && skipNames.contains f.name then
      continue
    -- Leave a defaulted field at its default only when no meaningful value was
    -- supplied: the value was omitted from the payload and the resolved value is
    -- itself an empty sentinel.
    if f.hasDefault && f.omitted && f.resolvedEmpty then
      continue
    -- Defer file fields to a second pass; assign everything else now.
    if f.isFile then
      fileFields := fileFields ++ [(f.name, f.resolvedValue)]
    else
      assigned := assigned ++ [(f.name, f.resolvedValue)]
  return assigned ++ fileFields
-- impl-end


-- proof-start
/-- The per-field state transition of the desugared loop: given the current
`(assigned, fileFields)` pair and a field, leave the state unchanged if the
field fails `assignField`, else append its emitted assignment to the file
accumulator (if it is a file field) or to the non-file accumulator. -/
def step (nf : Option (List String)) (sk : List String)
    (st : List (String × String) × List (String × String)) (f : FieldInput) :
    List (String × String) × List (String × String) :=
  if assignField nf sk f then
    (if f.isFile then (st.1, st.2 ++ [emit f]) else (st.1 ++ [emit f], st.2))
  else st

/-- Invariant relating the two accumulators after processing a prefix `p` to the
filtered-mapped sublists of the kept fields of `p`. -/
def FoldInv (nf : Option (List String)) (sk : List String)
    (p : List FieldInput) (assigned fileFields : List (String × String)) : Prop :=
  assigned = ((p.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit
    ∧ fileFields = ((p.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit

/-- Generalized-accumulator form of the desugared implementation loop: running the
`for` loop from an arbitrary initial `(assigned, fileFields)` pair yields exactly the
left fold of `step` over the fields from that pair. This isolates the fragile
`Id.run`/`forIn`→`foldl` bridge behind a clean statement that inducts on `fields`
generalizing the accumulators, so `impl_as_foldl` follows by instantiating at `([],[])`. -/
theorem impl_loop_eq_foldl (nameFilter : Option (List String)) (skipNames : List String)
    (fields : List FieldInput) (a0 ff0 : List (String × String)) :
    (Id.run do
      let mut assigned := a0
      let mut fileFields := ff0
      for f in fields do
        if !f.editable || f.isAuto || !f.inResolved then
          continue
        if let some names := nameFilter then
          if !names.contains f.name then
            continue
        if !skipNames.isEmpty && skipNames.contains f.name then
          continue
        if f.hasDefault && f.omitted && f.resolvedEmpty then
          continue
        if f.isFile then
          fileFields := fileFields ++ [(f.name, f.resolvedValue)]
        else
          assigned := assigned ++ [(f.name, f.resolvedValue)]
      return (assigned, fileFields))
    = fields.foldl (step nameFilter skipNames) (a0, ff0) := by
  simp only [Id.run, bind, pure, ← apply_ite ForInStep.yield]
  rcases nameFilter with _ | names <;>
    simp only [← apply_ite ForInStep.yield, List.forIn_yield_eq_foldl] <;>
    · induction fields generalizing a0 ff0 with
      | nil => rfl
      | cons f fs ih =>
        simp only [List.foldl_cons, step, assignField]
        rw [ih]
        clear ih
        congr 1 <;>
          simp only [emit] <;>
          split_ifs <;>
          grind

theorem impl_as_foldl (nameFilter : Option (List String)) (skipNames : List String)
    (fields : List FieldInput) :
    implementation_bindFields nameFilter skipNames fields
      = (fun st => st.1 ++ st.2) (fields.foldl (step nameFilter skipNames) ([], [])) := by
  rw [← impl_loop_eq_foldl nameFilter skipNames fields [] []]
  rfl

theorem guards_iff_assignField (nameFilter : Option (List String))
    (skipNames : List String) (f : FieldInput) :
    (¬(!f.editable || f.isAuto || !f.inResolved) ∧
      (match nameFilter with | some names => names.contains f.name | none => True) ∧
      ¬(!skipNames.isEmpty && skipNames.contains f.name) ∧
      ¬(f.hasDefault && f.omitted && f.resolvedEmpty))
    ↔ assignField nameFilter skipNames f = true := by
  cases nameFilter <;>
    simp only [assignField, Bool.and_eq_true, Bool.or_eq_true, Bool.not_eq_true,
      Bool.not_eq_true', not_or, not_and] <;>
    (cases f.editable <;> cases f.isAuto <;> cases f.inResolved <;>
      cases f.hasDefault <;> cases f.omitted <;> cases f.resolvedEmpty <;>
      cases skipNames.isEmpty <;> cases skipNames.contains f.name <;> simp_all)

theorem foldl_step_general (nf : Option (List String)) (sk : List String)
    (p : List FieldInput) (a0 ff0 : List (String × String)) :
    p.foldl (step nf sk) (a0, ff0)
      = (a0 ++ ((p.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit,
         ff0 ++ ((p.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit) := by
  induction p generalizing a0 ff0 with
  | nil => simp
  | cons f rest ih =>
    simp only [List.foldl_cons, List.filter_cons, step]
    by_cases h : assignField nf sk f = true
    · by_cases hf : f.isFile = true
      · simp [h, hf, ih, List.append_assoc]
      · simp only [Bool.not_eq_true] at hf
        simp [h, hf, ih, List.append_assoc]
    · simp only [Bool.not_eq_true] at h
      simp [h, ih]

theorem FoldInv_final (nf : Option (List String)) (sk : List String)
    (fields : List FieldInput) :
    fields.foldl (step nf sk) ([], [])
      = (((fields.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit,
         ((fields.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit) := by
  simpa using foldl_step_general nf sk fields [] []

theorem correct_bindFields :
    ∀ (nameFilter : Option (List String)) (skipNames : List String)
      (fields : List FieldInput),
      problem_spec_bindFields nameFilter skipNames fields
        (implementation_bindFields nameFilter skipNames fields) := by
  intro nameFilter skipNames fields
  unfold problem_spec_bindFields assignmentsFor
  rw [impl_as_foldl, FoldInv_final]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier: python for same_spec; scripts/lean_verify.sh <file> for verification.

All 7 attacks confirmed same_spec=True (spec/axioms/pure/pre/post byte-identical).

### ATTACK RESULTS (cmd: bash scripts/lean_verify.sh <file>):
- atk_1 (PREPATCH BUG: leave-default guard drops the resolvedEmpty conjunct -> `if f.hasDefault && f.omitted then continue`): exit=1. Real proof fails at impl_as_foldl `rfl` bridge. Reproduces the FAIL_TO_PASS behavior; PREPATCH reproduced.
- atk_2 (control-flow: file/non-file order swapped, `return fileFields ++ assigned`): exit=1 (rfl failed).
- atk_3 (partial-domain: nameFilter restriction ignored): exit=1 (rfl failed).
- atk_4 (control-flow-effect: no file deferral, single pass): exit=1 (rfl failed).
- atk_5 (boundary: isAuto skip check dropped): exit=1 (rfl failed).
- atk_6 (wrong emitted value: (name,name) instead of (name,resolvedValue)): exit=1 (rfl failed).
- atk_7 (UNGROUNDED-ORACLE ECHO: implementation_bindFields := assignmentsFor, proof `unfold; rfl`): exit=0 VERIFIES. #print axioms correct_bindFields => 'does not depend on any axioms' (clean).

POSITIVE CONTROL (pos_control.lean = original Solution.lean): exit=0 verifies; #print axioms => [propext, Classical.choice, Quot.sound] (standard Mathlib, clean).

### RESOLVE RUN (mandatory for the one verifying impl atk_7):
- Materialized atk_7's faithful patch = the gold patch (impl reproduces the patched three-way-guard behavior exactly; meta patch_equals_gold=True).
- run_resolve('django__django-11433', <gold patch>, timeout=1800) => RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1, FLAKY=False.
- Therefore verify => correct holds for the only same-spec verifying impl.

REFINEMENT.MD AUDIT: axioms=[] and opaque_callees=[] in meta.json -> NO A-consumed legs. Two A-reference deep-model legs (assignField = the per-field continue-guard chain incl. the patched three-way leave-default guard; assignmentsFor = two-pass ordering) validated by G-CONF. conformance_check.py reviewed: ORACLE is a faithful in-process replica of the patched construct_instance guards (uses f.has_default() and omitted and resolved_empty), SHADOW is op-for-op transliteration of assignField/assignmentsFor; edge cases cover F2P (defaulted+omitted+non-empty resolved -> assign) and P2P (defaulted+omitted+empty -> keep default) plus editable/auto/membership/exclude skips and file deferral, 120k fuzz at pinned SEED=20240629. Correspondence of every A-reference/I predicate to its real UNCHANGED callee holds; the patch only ADDS the resolvedEmpty conjunct, correctly modeled as assignField's third conjunct. Every refinement.md row is R / A-reference / I; no kind-3 legs.

CONCLUSION: The exact-equality spec admits no verify-but-incorrect impl; the sole verifying same-spec impl (echo) resolves under the harness. SOUND.

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
None found. The spec problem_spec_bindFields pins result = assignmentsFor nf sk fields (exact functional equality), so any impl that closes correct_bindFields must be extensionally equal to the gold model on all inputs. The only same-spec impl that verified is the oracle echo (atk_7: implementation := assignmentsFor), whose faithful refined patch is exactly the gold patch and RESOLVES under the official harness. No verify-but-incorrect impl exists.
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

/-!
Building a model object's field assignments from the resolved data of a bound
form.

The routine walks the model's fields in order and, for each one, decides whether
to assign the form's resolved value to that field or to leave the field holding
the value it already carries (its model-level default). A field is assigned its
resolved value exactly when all of the following hold:

* the field is editable and is not an auto-generated key field;
* the field has a resolved value available (it appears in the resolved data);
* if the caller restricted the work to an explicit set of field names, the
  field's name is in that set;
* if the caller supplied a non-empty set of names to skip, the field's name is
  not among them;
* it is NOT the case that the field both carries a model-level default AND had
  its value omitted from the submitted payload AND its resolved value is itself
  one of the field's "empty" sentinels. In other words, a field that has a
  default is left at that default only when no meaningful value was supplied for
  it; a non-empty resolved value always takes precedence over the default.

Assignments are emitted in two passes: first every eligible non-file field in
field order, then every eligible file field in field order (file fields are
deferred so that a later field's value is available when their value is
computed). Each emitted assignment records the field's name together with the
resolved value assigned to it; a field left at its default emits nothing.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Every per-field predicate
-- the routine consults (editability, auto-key test, availability of a resolved
-- value, presence of a default, whether the value was omitted from the payload,
-- whether the resolved value is an empty sentinel, file-field test) is supplied
-- as a boolean field of the per-field input record; the assignment-selection
-- logic is spelled out concretely below.
-- axioms-end

-- pure-start
/-- The observable per-field state the routine reads on one loop iteration,
together with the resolved value that would be assigned. -/
structure FieldInput where
  /-- the field's name -/
  name : String
  /-- the field may be written by a form -/
  editable : Bool
  /-- the field is an auto-generated key field -/
  isAuto : Bool
  /-- a resolved value for this field is available -/
  inResolved : Bool
  /-- the field carries a model-level default -/
  hasDefault : Bool
  /-- the field's value was omitted from the submitted payload -/
  omitted : Bool
  /-- the resolved value is one of the field's "empty" sentinels -/
  resolvedEmpty : Bool
  /-- the field stores a file and is therefore deferred to the second pass -/
  isFile : Bool
  /-- the resolved value that would be assigned to the field -/
  resolvedValue : String
deriving Repr, DecidableEq

/-- Whether a field is assigned its resolved value (rather than left at its
default). Encodes the full chain of skip-conditions as a single conjunction. -/
def assignField (nameFilter : Option (List String)) (skipNames : List String)
    (f : FieldInput) : Bool :=
  f.editable && !f.isAuto && f.inResolved
    && (match nameFilter with
        | some names => names.contains f.name
        | none => true)
    && !(!skipNames.isEmpty && skipNames.contains f.name)
    && !(f.hasDefault && f.omitted && f.resolvedEmpty)

/-- One emitted assignment: the field's name paired with the value assigned. -/
def emit (f : FieldInput) : String × String := (f.name, f.resolvedValue)

/-- The assignments the routine performs, in execution order: eligible non-file
fields first (field order), then eligible file fields (field order). -/
def assignmentsFor (nameFilter : Option (List String)) (skipNames : List String)
    (fields : List FieldInput) : List (String × String) :=
  let kept := fields.filter (assignField nameFilter skipNames)
  (kept.filter (fun f => !f.isFile)).map emit
    ++ (kept.filter (fun f => f.isFile)).map emit
-- pure-end

-- post-conditions-start
/-- Input→output relation for building the field assignments.

Inputs:
* `nameFilter` — `none` if the caller imposed no field-name restriction, else
  `some names` to restrict work to those names;
* `skipNames`  — names to skip (effective only when non-empty);
* `fields`     — the model's fields, in order, each with its observable state.

The result is the exact sequence of `(name, value)` assignments performed, with
the file-field deferral reflected in the ordering. It is fully pinned: every
field that qualifies contributes its emitted assignment, every field that does
not contributes nothing, and the order is the two-pass order. -/
def problem_spec_bindFields (nameFilter : Option (List String))
    (skipNames : List String) (fields : List FieldInput)
    (result : List (String × String)) : Prop :=
  result = assignmentsFor nameFilter skipNames fields
-- post-conditions-end

-- impl-start
def implementation_bindFields (nameFilter : Option (List String))
    (skipNames : List String) (fields : List FieldInput) :
    List (String × String) := Id.run do
  let mut assigned : List (String × String) := []
  let mut fileFields : List (String × String) := []
  for f in fields do
    -- Skip fields that cannot or need not receive a resolved value.
    if !f.editable || f.isAuto || !f.inResolved then
      continue
    -- Honor an explicit field-name restriction.
    if let some names := nameFilter then
      if !names.contains f.name then
        continue
    -- Honor a non-empty set of names to skip.
    if !skipNames.isEmpty && skipNames.contains f.name then
      continue
    -- Leave a defaulted field at its default only when no meaningful value was
    -- supplied: the value was omitted from the payload and the resolved value is
    -- itself an empty sentinel.
    if f.hasDefault && f.omitted && f.resolvedEmpty then
      continue
    -- Defer file fields to a second pass; assign everything else now.
    if f.isFile then
      fileFields := fileFields ++ [(f.name, f.resolvedValue)]
    else
      assigned := assigned ++ [(f.name, f.resolvedValue)]
  return assigned ++ fileFields
-- impl-end


-- proof-start
/-- The per-field state transition of the desugared loop: given the current
`(assigned, fileFields)` pair and a field, leave the state unchanged if the
field fails `assignField`, else append its emitted assignment to the file
accumulator (if it is a file field) or to the non-file accumulator. -/
def step (nf : Option (List String)) (sk : List String)
    (st : List (String × String) × List (String × String)) (f : FieldInput) :
    List (String × String) × List (String × String) :=
  if assignField nf sk f then
    (if f.isFile then (st.1, st.2 ++ [emit f]) else (st.1 ++ [emit f], st.2))
  else st

/-- Invariant relating the two accumulators after processing a prefix `p` to the
filtered-mapped sublists of the kept fields of `p`. -/
def FoldInv (nf : Option (List String)) (sk : List String)
    (p : List FieldInput) (assigned fileFields : List (String × String)) : Prop :=
  assigned = ((p.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit
    ∧ fileFields = ((p.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit

/-- Generalized-accumulator form of the desugared implementation loop: running the
`for` loop from an arbitrary initial `(assigned, fileFields)` pair yields exactly the
left fold of `step` over the fields from that pair. This isolates the fragile
`Id.run`/`forIn`→`foldl` bridge behind a clean statement that inducts on `fields`
generalizing the accumulators, so `impl_as_foldl` follows by instantiating at `([],[])`. -/
theorem impl_loop_eq_foldl (nameFilter : Option (List String)) (skipNames : List String)
    (fields : List FieldInput) (a0 ff0 : List (String × String)) :
    (Id.run do
      let mut assigned := a0
      let mut fileFields := ff0
      for f in fields do
        if !f.editable || f.isAuto || !f.inResolved then
          continue
        if let some names := nameFilter then
          if !names.contains f.name then
            continue
        if !skipNames.isEmpty && skipNames.contains f.name then
          continue
        if f.hasDefault && f.omitted && f.resolvedEmpty then
          continue
        if f.isFile then
          fileFields := fileFields ++ [(f.name, f.resolvedValue)]
        else
          assigned := assigned ++ [(f.name, f.resolvedValue)]
      return (assigned, fileFields))
    = fields.foldl (step nameFilter skipNames) (a0, ff0) := by
  simp only [Id.run, bind, pure, ← apply_ite ForInStep.yield]
  rcases nameFilter with _ | names <;>
    simp only [← apply_ite ForInStep.yield, List.forIn_yield_eq_foldl] <;>
    · induction fields generalizing a0 ff0 with
      | nil => rfl
      | cons f fs ih =>
        simp only [List.foldl_cons, step, assignField]
        rw [ih]
        clear ih
        congr 1 <;>
          simp only [emit] <;>
          split_ifs <;>
          grind

theorem impl_as_foldl (nameFilter : Option (List String)) (skipNames : List String)
    (fields : List FieldInput) :
    implementation_bindFields nameFilter skipNames fields
      = (fun st => st.1 ++ st.2) (fields.foldl (step nameFilter skipNames) ([], [])) := by
  rw [← impl_loop_eq_foldl nameFilter skipNames fields [] []]
  rfl

theorem guards_iff_assignField (nameFilter : Option (List String))
    (skipNames : List String) (f : FieldInput) :
    (¬(!f.editable || f.isAuto || !f.inResolved) ∧
      (match nameFilter with | some names => names.contains f.name | none => True) ∧
      ¬(!skipNames.isEmpty && skipNames.contains f.name) ∧
      ¬(f.hasDefault && f.omitted && f.resolvedEmpty))
    ↔ assignField nameFilter skipNames f = true := by
  cases nameFilter <;>
    simp only [assignField, Bool.and_eq_true, Bool.or_eq_true, Bool.not_eq_true,
      Bool.not_eq_true', not_or, not_and] <;>
    (cases f.editable <;> cases f.isAuto <;> cases f.inResolved <;>
      cases f.hasDefault <;> cases f.omitted <;> cases f.resolvedEmpty <;>
      cases skipNames.isEmpty <;> cases skipNames.contains f.name <;> simp_all)

theorem foldl_step_general (nf : Option (List String)) (sk : List String)
    (p : List FieldInput) (a0 ff0 : List (String × String)) :
    p.foldl (step nf sk) (a0, ff0)
      = (a0 ++ ((p.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit,
         ff0 ++ ((p.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit) := by
  induction p generalizing a0 ff0 with
  | nil => simp
  | cons f rest ih =>
    simp only [List.foldl_cons, List.filter_cons, step]
    by_cases h : assignField nf sk f = true
    · by_cases hf : f.isFile = true
      · simp [h, hf, ih, List.append_assoc]
      · simp only [Bool.not_eq_true] at hf
        simp [h, hf, ih, List.append_assoc]
    · simp only [Bool.not_eq_true] at h
      simp [h, ih]

theorem FoldInv_final (nf : Option (List String)) (sk : List String)
    (fields : List FieldInput) :
    fields.foldl (step nf sk) ([], [])
      = (((fields.filter (assignField nf sk)).filter (fun f => !f.isFile)).map emit,
         ((fields.filter (assignField nf sk)).filter (fun f => f.isFile)).map emit) := by
  simpa using foldl_step_general nf sk fields [] []

theorem correct_bindFields :
    ∀ (nameFilter : Option (List String)) (skipNames : List String)
      (fields : List FieldInput),
      problem_spec_bindFields nameFilter skipNames fields
        (implementation_bindFields nameFilter skipNames fields) := by
  intro nameFilter skipNames fields
  unfold problem_spec_bindFields assignmentsFor
  rw [impl_as_foldl, FoldInv_final]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier: python for same_spec; scripts/lean_verify.sh <file> for verification.

All 7 attacks confirmed same_spec=True (spec/axioms/pure/pre/post byte-identical).

### ATTACK RESULTS (cmd: bash scripts/lean_verify.sh <file>):
- atk_1 (PREPATCH BUG: leave-default guard drops the resolvedEmpty conjunct -> `if f.hasDefault && f.omitted then continue`): exit=1. Real proof fails at impl_as_foldl `rfl` bridge. Reproduces the FAIL_TO_PASS behavior; PREPATCH reproduced.
- atk_2 (control-flow: file/non-file order swapped, `return fileFields ++ assigned`): exit=1 (rfl failed).
- atk_3 (partial-domain: nameFilter restriction ignored): exit=1 (rfl failed).
- atk_4 (control-flow-effect: no file deferral, single pass): exit=1 (rfl failed).
- atk_5 (boundary: isAuto skip check dropped): exit=1 (rfl failed).
- atk_6 (wrong emitted value: (name,name) instead of (name,resolvedValue)): exit=1 (rfl failed).
- atk_7 (UNGROUNDED-ORACLE ECHO: implementation_bindFields := assignmentsFor, proof `unfold; rfl`): exit=0 VERIFIES. #print axioms correct_bindFields => 'does not depend on any axioms' (clean).

POSITIVE CONTROL (pos_control.lean = original Solution.lean): exit=0 verifies; #print axioms => [propext, Classical.choice, Quot.sound] (standard Mathlib, clean).

### RESOLVE RUN (mandatory for the one verifying impl atk_7):
- Materialized atk_7's faithful patch = the gold patch (impl reproduces the patched three-way-guard behavior exactly; meta patch_equals_gold=True).
- run_resolve('django__django-11433', <gold patch>, timeout=1800) => RESOLVED=True, COMPLETED=True, NOTE='resolved', ATTEMPTS=1, FLAKY=False.
- Therefore verify => correct holds for the only same-spec verifying impl.

REFINEMENT.MD AUDIT: axioms=[] and opaque_callees=[] in meta.json -> NO A-consumed legs. Two A-reference deep-model legs (assignField = the per-field continue-guard chain incl. the patched three-way leave-default guard; assignmentsFor = two-pass ordering) validated by G-CONF. conformance_check.py reviewed: ORACLE is a faithful in-process replica of the patched construct_instance guards (uses f.has_default() and omitted and resolved_empty), SHADOW is op-for-op transliteration of assignField/assignmentsFor; edge cases cover F2P (defaulted+omitted+non-empty resolved -> assign) and P2P (defaulted+omitted+empty -> keep default) plus editable/auto/membership/exclude skips and file deferral, 120k fuzz at pinned SEED=20240629. Correspondence of every A-reference/I predicate to its real UNCHANGED callee holds; the patch only ADDS the resolvedEmpty conjunct, correctly modeled as assignField's third conjunct. Every refinement.md row is R / A-reference / I; no kind-3 legs.

CONCLUSION: The exact-equality spec admits no verify-but-incorrect impl; the sole verifying same-spec impl (echo) resolves under the harness. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No divergence found between the modeled function and the real repo behavior. Verification performed:

1. COMPILES: scripts/lean_verify.sh on Solution.lean exits 0 (only deprecation/lint warnings, no errors, no sorry).
2. AXIOMS CLEAN: `#print axioms correct_bindFields` => [propext, Classical.choice, Quot.sound] only; no sorryAx, proof is genuine.
3. SAME_SPEC: swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean-backend) = True; spec region (pure/post-conditions) byte-identical. Prepatch differs only in the impl guard (drops the `resolvedEmpty` conjunct), so the spec genuinely discriminates the F2P behavior.
4. CONFORMANCE: conformance_check.py passes 120,010 cases (oracle = faithful replica of patched construct_instance; shadow = transliteration of assignField/assignmentsFor) with 0 disagreements.

FAITHFULNESS vs real repo (django/forms/models.py:construct_instance @ base 21b1d239125f, confirmed worktree):
- `not f.editable or isinstance(f,AutoField) or f.name not in cleaned_data` <-> `!editable || isAuto || !inResolved` (I)
- `fields is not None and f.name not in fields` <-> `some names => names.contains f.name` (I); `fields=[]` -> `some []` skips all, matches
- `exclude and f.name in exclude` <-> `!skipNames.isEmpty && contains`; exclude=None -> [] matches
- patched guard `has_default() and value_omitted_from_data(...) and cleaned_data.get(name) in empty_values` <-> `hasDefault && omitted && resolvedEmpty` (the edited three-way conjunction, modeled deeply)
- FileField deferral / two-pass ordering preserved; file fields appended after non-file, both in field order.

All per-field predicates are UNCHANGED callees supplied as FieldInput booleans; the patch alters only the conjunction, which is modeled exactly. The spec is neither too strong nor drifting: it exactly pins the patched relation. No input on which assignmentsFor disagrees with the real construct_instance assignment sequence.

Spec is also non-trivial (not spec-too-weak either): prepatch impl (guard missing resolvedEmpty) fails correct_bindFields on hasDefault=true, omitted=true, resolvedEmpty=false, otherwise-eligible fields, which is exactly the F2P test.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view is fully abstract (Lean FieldInput model with boolean observables); no Python identifiers (empty_values, value_omitted_from_data, construct_instance, has_default), no patch phrasing, no file/line locations. same_spec(Solution, Solution_prepatch)==True, so the prepatch reveals nothing. The post-condition describes the correct post-patch behavior ('a defaulted field is left at its default only when no meaningful value was supplied; a non-empty resolved value takes precedence'), which is exactly the natural formalization of the public problem_statement's stated goal ('Allow cleaned_data to overwrite fields' default values'), not information beyond it. The third conjunct is modeled as an abstract boolean input (resolvedEmpty), giving no mechanical route to the gold edit past what the problem statement already discloses. The lexical scan's only hit ('conjunct') is a substring of 'conjunction' in the abstract docstring, not a gold token. G-LEAK recorded pass with empty failures, consistent.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
