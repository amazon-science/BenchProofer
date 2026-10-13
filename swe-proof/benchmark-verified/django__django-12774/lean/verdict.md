# P2 adversarial audit — django__django-12774

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no wrong impl closed correct_inBulk, so there is no verifying-but-non-resolving patch. The spec problem_spec_inBulk is a total, mutually-exclusive bi-conditional (acceptable → ok () ∧ ¬acceptable → error fieldName) stated STRUCTURALLY over the raw inputs via fieldNameAcceptable (fieldName="pk" ∨ fld.unique ∨ ∃ c ∈ cs, ¬c.isPartial ∧ c.fields=[fieldName]), NOT via the impl helper. It pins result to a unique value for every input, so any verifying impl must be extensionally equal to the gold decision and therefore resolves. verify ⇒ correct holds.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,11 +89,11 @@
   (¬ fieldNameAcceptable fieldName fld cs  → result = Except.error fieldName)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :
     Except String Unit := Id.run do
-  let uniqueFields := singleFieldUniqueConstraintFields cs
-  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then
+  if fieldName != "pk" && !fld.unique then
     return Except.error fieldName
   return Except.ok ()
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,10 +89,11 @@
   (¬ fieldNameAcceptable fieldName fld cs  → result = Except.error fieldName)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :
     Except String Unit := Id.run do
-  let uniqueFields := singleFieldUniqueConstraintFields cs
+  let uniqueFields := (cs.filter (fun c => c.fields.length == 1)).map (fun c => c.fields.headD "")
   if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then
     return Except.error fieldName
   return Except.ok ()
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,10 +89,11 @@
   (¬ fieldNameAcceptable fieldName fld cs  → result = Except.error fieldName)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :
     Except String Unit := Id.run do
-  let uniqueFields := singleFieldUniqueConstraintFields cs
+  let uniqueFields := (cs.filter (fun c => !c.isPartial)).map (fun c => c.fields.headD "")
   if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then
     return Except.error fieldName
   return Except.ok ()
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,12 +89,10 @@
   (¬ fieldNameAcceptable fieldName fld cs  → result = Except.error fieldName)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :
     Except String Unit := Id.run do
-  let uniqueFields := singleFieldUniqueConstraintFields cs
-  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then
-    return Except.error fieldName
   return Except.ok ()
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,11 +89,11 @@
   (¬ fieldNameAcceptable fieldName fld cs  → result = Except.error fieldName)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :
     Except String Unit := Id.run do
-  let uniqueFields := singleFieldUniqueConstraintFields cs
-  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then
+  if fieldName != "pk" then
     return Except.error fieldName
   return Except.ok ()
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,12 +89,13 @@
   (¬ fieldNameAcceptable fieldName fld cs  → result = Except.error fieldName)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :
     Except String Unit := Id.run do
   let uniqueFields := singleFieldUniqueConstraintFields cs
   if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then
-    return Except.error fieldName
+    return Except.error "pk"
   return Except.ok ()
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a queryset's `in_bulk` may key on a given `field_name`.

`in_bulk` builds a mapping from a field's value to the object carrying it; this
only makes sense when the chosen field takes a distinct value on each row. The
method therefore first checks that `field_name` names a field guaranteed unique
across all rows, and rejects the call with an error (naming the offending field)
when it does not.

A field name is acceptable when ANY of the following holds:

  * it is the primary key (`"pk"`);
  * the field itself is declared unique;
  * it is the single field covered by an *unconditional* `UniqueConstraint`
    declared on the model — a constraint that spans exactly that one field and
    applies to every row (no partial condition).

Otherwise the field name is not acceptable and the call is rejected. The rule is
a total, exhaustive predicate of the field name, the field's own uniqueness, and
the model's unique constraints, so the outcome is fully determined for every
input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- reads only the field's own uniqueness flag (supplied as an input observable),
-- and inspects the model's unconditional unique constraints that span exactly
-- one field, to collect the field names they each cover. Resolving the
-- constraint set to its unconditional members and projecting the single-field
-- ones are modeled directly (list filters/maps over the constraint records), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A unique constraint declared on a model, observed through the components the
acceptability rule reads: the field names it spans, and whether it is partial
(applies only to a subset of rows via a condition) rather than total. -/
structure UniqueConstraint where
  /-- the field names this constraint covers -/
  fields : List String
  /-- `true` when the constraint is conditional/partial (does not apply to every
  row); only unconditional constraints guarantee uniqueness across all rows -/
  isPartial : Bool
deriving DecidableEq, Repr

/-- A model field, observed through the only component the rule reads: whether
the field is itself declared unique. -/
structure FieldInfo where
  /-- `true` when the field carries its own uniqueness declaration -/
  unique : Bool
deriving DecidableEq, Repr

/-- The field names that are each the sole field of an unconditional unique
constraint: from the unconditional constraints (`isPartial = false`) that span
exactly one field, take that one field name. These names are guaranteed unique
across all rows even though the field is not individually flagged unique. -/
def singleFieldUniqueConstraintFields (cs : List UniqueConstraint) : List String :=
  (cs.filter (fun c => !c.isPartial && c.fields.length == 1)).map (fun c => c.fields.headD "")
-- pure-end

-- post-conditions-start
/-- A field name is acceptable to key on exactly when ANY of three independent
conditions holds. Stated structurally over the inputs (NOT via the implementation
helper) so the postcondition is dischargeable only by the real computation:

  * it is the primary key (`"pk"`); or
  * the field is itself declared unique; or
  * some unconditional unique constraint on the model spans exactly this one
    field. -/
def fieldNameAcceptable (fieldName : String) (fld : FieldInfo)
    (cs : List UniqueConstraint) : Prop :=
  fieldName = "pk" ∨ fld.unique = true ∨
    (∃ c ∈ cs, c.isPartial = false ∧ c.fields = [fieldName])

/-- The outcome of the field-name acceptability check that guards `in_bulk`:

  * when the field name is acceptable the call proceeds (`Except.ok ()`);
  * otherwise the call fails with an error naming the offending field
    (`Except.error fieldName`).

The two cases are exhaustive and mutually exclusive (they partition on
`fieldNameAcceptable`), so the result is fully determined for every input. -/
def problem_spec_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint)
    (result : Except String Unit) : Prop :=
  (fieldNameAcceptable fieldName fld cs    → result = Except.ok ()) ∧
  (¬ fieldNameAcceptable fieldName fld cs  → result = Except.error fieldName)
-- post-conditions-end

-- impl-start
def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :
    Except String Unit := Id.run do
  let uniqueFields := singleFieldUniqueConstraintFields cs
  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then
    return Except.error fieldName
  return Except.ok ()
-- impl-end

-- proof-start
theorem correct_inBulk :
    ∀ (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint),
      problem_spec_inBulk fieldName fld cs (implementation_inBulk fieldName fld cs) := by
  intro fieldName fld cs
  have hmem : (singleFieldUniqueConstraintFields cs).contains fieldName = true ↔
      (∃ c ∈ cs, c.isPartial = false ∧ c.fields = [fieldName]) := by
    unfold singleFieldUniqueConstraintFields
    simp only [List.contains_eq_mem, decide_eq_true_eq, List.mem_map, List.mem_filter,
      Bool.and_eq_true, Bool.not_eq_true', beq_iff_eq]
    constructor
    · rintro ⟨c, ⟨hcmem, hpart, hlen⟩, rfl⟩
      refine ⟨c, hcmem, ?_, ?_⟩
      · simpa using hpart
      · rw [List.length_eq_one_iff] at hlen
        obtain ⟨a, ha⟩ := hlen
        rw [ha]; simp [List.headD]
    · rintro ⟨c, hcmem, hpart, hfields⟩
      refine ⟨c, ⟨hcmem, ?_, ?_⟩, ?_⟩
      · simp [hpart]
      · rw [hfields]; rfl
      · rw [hfields]; rfl
  have hcond : (fieldName != "pk" && !fld.unique &&
        !(singleFieldUniqueConstraintFields cs).contains fieldName) = true
      ↔ ¬ fieldNameAcceptable fieldName fld cs := by
    unfold fieldNameAcceptable
    simp only [Bool.and_eq_true, bne_iff_ne, ne_eq, Bool.not_eq_true', Bool.not_eq_true,
      not_or]
    rw [← hmem]
    constructor
    · rintro ⟨⟨hpk, hu⟩, hc⟩
      refine ⟨hpk, ?_, ?_⟩
      · simp [hu]
      · rw [List.contains_eq_mem] at hc; simpa using hc
    · rintro ⟨hpk, hu, hc⟩
      refine ⟨⟨hpk, ?_⟩, ?_⟩
      · simpa using hu
      · rw [List.contains_eq_mem]; simpa using hc
  unfold problem_spec_inBulk implementation_inBulk
  simp only [Id.run, bind, pure]
  constructor
  · intro hacc
    rw [if_neg]
    intro h
    exact (hcond.mp h) hacc
  · intro hnacc
    rw [if_pos (hcond.mpr hnacc)]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: PY=python. same_spec confirmed True for all 6 attacks + positive control (swebench_unified.markers.same_spec, lean backend, byte-identical spec regions — impl region only edited). Command per file: bash scripts/lean_verify.sh <abs path> 300. Verifications run concurrently in two batches of ≤4 background jobs.

### RESULTS (exit: 0=verifies/no-sorry, 1=error, 3=sorry, 124=timeout):
- positive_control.lean (gold impl) => EXIT 0 (verifies, no sorry). #print axioms correct_inBulk = [propext, Quot.sound] per verdict.md, clean (no sorryAx).
- atk_1 PREPATCH BUG (two-conjunct guard, ignores cs) => EXIT 1. Goal collapses to (if (fieldName!="pk" && !fld.unique) then error else ok)=error under ¬acceptable; on a single-field unconditional constraint the guard doesn't fire so ok≠error. Prepatch bug reproduced.
- atk_2 PARTIAL-DOMAIN (drops !isPartial filter; would accept a partial single-field constraint) => EXIT 1.
- atk_3 BOUNDARY (drops length==1 filter; would accept first field of a multi-field constraint) => EXIT 1.
- atk_4 CONTROL-FLOW-EFFECT (always Except.ok ()) => EXIT 1. Goal reduces to Except.ok () = Except.error fieldName under ¬acceptable.
- atk_5 CONTROL-FLOW (accepts only pk; ignores unique flag & constraints) => EXIT 1.
- atk_6 UNGROUNDED-ORACLE ECHO (correct decision but wrong error payload Except.error "pk" instead of fieldName) => EXIT 1. Goal reduces to Except.error "pk" = Except.error fieldName, false when fieldName≠"pk".

All 6 same-spec wrong impls FAILED to close correct_inBulk (all EXIT 1, genuine unsolved-goal errors, not linter/timeout). Therefore ZERO verifying-but-wrong impls exist; no faithful patch needed to be materialized/resolved (patches={}).

REFINEMENT.MD AUDIT: legs #1 (fieldName:String)=I, #2 (fld.unique)=R, #3 (cs projection)=R, #4 (singleFieldUniqueConstraintFields)=I deeply-modeled, #5 (guard = the fix)=I, #6 (Except.ok proceed)=R, #7 (Except String Unit result)=R. NO A-tagged (axiom) content, NO kind-3 ungrounded-oracle legs. axiom_check.py is a legitimate skip stub, consistent with clean #print axioms (no axiom callee contract consumed). Unchanged-callee correspondences hold: get_field observed only via .unique supplied as R input (pk branch short-circuits get_field, matched by first disjunct); Options.total_unique_constraints' isinstance(UniqueConstraint) filter = the R projection defining cs, condition is None = !isPartial, len==1 filter + fields[0]=headD "" spelled out directly. G-CONF (conformance_check.py) differential-tests the R/I shadow vs an in-process post-patch replica.

ROOT CAUSE OF SOUNDNESS: the bi-conditional fully determines result on every input from the raw inputs, leaving no output freedom; any closing impl is extensionally = gold and resolves. verify ⇏ correct could NOT be exhibited.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no wrong impl closed correct_inBulk, so there is no verifying-but-non-resolving patch. The spec problem_spec_inBulk is a total, mutually-exclusive bi-conditional (acceptable → ok () ∧ ¬acceptable → error fieldName) stated STRUCTURALLY over the raw inputs via fieldNameAcceptable (fieldName="pk" ∨ fld.unique ∨ ∃ c ∈ cs, ¬c.isPartial ∧ c.fields=[fieldName]), NOT via the impl helper. It pins result to a unique value for every input, so any verifying impl must be extensionally equal to the gold decision and therefore resolves. verify ⇒ correct holds.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a queryset's `in_bulk` may key on a given `field_name`.

`in_bulk` builds a mapping from a field's value to the object carrying it; this
only makes sense when the chosen field takes a distinct value on each row. The
method therefore first checks that `field_name` names a field guaranteed unique
across all rows, and rejects the call with an error (naming the offending field)
when it does not.

A field name is acceptable when ANY of the following holds:

  * it is the primary key (`"pk"`);
  * the field itself is declared unique;
  * it is the single field covered by an *unconditional* `UniqueConstraint`
    declared on the model — a constraint that spans exactly that one field and
    applies to every row (no partial condition).

Otherwise the field name is not acceptable and the call is rejected. The rule is
a total, exhaustive predicate of the field name, the field's own uniqueness, and
the model's unique constraints, so the outcome is fully determined for every
input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- reads only the field's own uniqueness flag (supplied as an input observable),
-- and inspects the model's unconditional unique constraints that span exactly
-- one field, to collect the field names they each cover. Resolving the
-- constraint set to its unconditional members and projecting the single-field
-- ones are modeled directly (list filters/maps over the constraint records), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A unique constraint declared on a model, observed through the components the
acceptability rule reads: the field names it spans, and whether it is partial
(applies only to a subset of rows via a condition) rather than total. -/
structure UniqueConstraint where
  /-- the field names this constraint covers -/
  fields : List String
  /-- `true` when the constraint is conditional/partial (does not apply to every
  row); only unconditional constraints guarantee uniqueness across all rows -/
  isPartial : Bool
deriving DecidableEq, Repr

/-- A model field, observed through the only component the rule reads: whether
the field is itself declared unique. -/
structure FieldInfo where
  /-- `true` when the field carries its own uniqueness declaration -/
  unique : Bool
deriving DecidableEq, Repr

/-- The field names that are each the sole field of an unconditional unique
constraint: from the unconditional constraints (`isPartial = false`) that span
exactly one field, take that one field name. These names are guaranteed unique
across all rows even though the field is not individually flagged unique. -/
def singleFieldUniqueConstraintFields (cs : List UniqueConstraint) : List String :=
  (cs.filter (fun c => !c.isPartial && c.fields.length == 1)).map (fun c => c.fields.headD "")
-- pure-end

-- post-conditions-start
/-- A field name is acceptable to key on exactly when ANY of three independent
conditions holds. Stated structurally over the inputs (NOT via the implementation
helper) so the postcondition is dischargeable only by the real computation:

  * it is the primary key (`"pk"`); or
  * the field is itself declared unique; or
  * some unconditional unique constraint on the model spans exactly this one
    field. -/
def fieldNameAcceptable (fieldName : String) (fld : FieldInfo)
    (cs : List UniqueConstraint) : Prop :=
  fieldName = "pk" ∨ fld.unique = true ∨
    (∃ c ∈ cs, c.isPartial = false ∧ c.fields = [fieldName])

/-- The outcome of the field-name acceptability check that guards `in_bulk`:

  * when the field name is acceptable the call proceeds (`Except.ok ()`);
  * otherwise the call fails with an error naming the offending field
    (`Except.error fieldName`).

The two cases are exhaustive and mutually exclusive (they partition on
`fieldNameAcceptable`), so the result is fully determined for every input. -/
def problem_spec_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint)
    (result : Except String Unit) : Prop :=
  (fieldNameAcceptable fieldName fld cs    → result = Except.ok ()) ∧
  (¬ fieldNameAcceptable fieldName fld cs  → result = Except.error fieldName)
-- post-conditions-end

-- impl-start
def implementation_inBulk (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint) :
    Except String Unit := Id.run do
  let uniqueFields := singleFieldUniqueConstraintFields cs
  if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then
    return Except.error fieldName
  return Except.ok ()
-- impl-end

-- proof-start
theorem correct_inBulk :
    ∀ (fieldName : String) (fld : FieldInfo) (cs : List UniqueConstraint),
      problem_spec_inBulk fieldName fld cs (implementation_inBulk fieldName fld cs) := by
  intro fieldName fld cs
  have hmem : (singleFieldUniqueConstraintFields cs).contains fieldName = true ↔
      (∃ c ∈ cs, c.isPartial = false ∧ c.fields = [fieldName]) := by
    unfold singleFieldUniqueConstraintFields
    simp only [List.contains_eq_mem, decide_eq_true_eq, List.mem_map, List.mem_filter,
      Bool.and_eq_true, Bool.not_eq_true', beq_iff_eq]
    constructor
    · rintro ⟨c, ⟨hcmem, hpart, hlen⟩, rfl⟩
      refine ⟨c, hcmem, ?_, ?_⟩
      · simpa using hpart
      · rw [List.length_eq_one_iff] at hlen
        obtain ⟨a, ha⟩ := hlen
        rw [ha]; simp [List.headD]
    · rintro ⟨c, hcmem, hpart, hfields⟩
      refine ⟨c, ⟨hcmem, ?_, ?_⟩, ?_⟩
      · simp [hpart]
      · rw [hfields]; rfl
      · rw [hfields]; rfl
  have hcond : (fieldName != "pk" && !fld.unique &&
        !(singleFieldUniqueConstraintFields cs).contains fieldName) = true
      ↔ ¬ fieldNameAcceptable fieldName fld cs := by
    unfold fieldNameAcceptable
    simp only [Bool.and_eq_true, bne_iff_ne, ne_eq, Bool.not_eq_true', Bool.not_eq_true,
      not_or]
    rw [← hmem]
    constructor
    · rintro ⟨⟨hpk, hu⟩, hc⟩
      refine ⟨hpk, ?_, ?_⟩
      · simp [hu]
      · rw [List.contains_eq_mem] at hc; simpa using hc
    · rintro ⟨hpk, hu, hc⟩
      refine ⟨⟨hpk, ?_⟩, ?_⟩
      · simpa using hu
      · rw [List.contains_eq_mem]; simpa using hc
  unfold problem_spec_inBulk implementation_inBulk
  simp only [Id.run, bind, pure]
  constructor
  · intro hacc
    rw [if_neg]
    intro h
    exact (hcond.mp h) hacc
  · intro hnacc
    rw [if_pos (hcond.mpr hnacc)]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: PY=python. same_spec confirmed True for all 6 attacks + positive control (swebench_unified.markers.same_spec, lean backend, byte-identical spec regions — impl region only edited). Command per file: bash scripts/lean_verify.sh <abs path> 300. Verifications run concurrently in two batches of ≤4 background jobs.

### RESULTS (exit: 0=verifies/no-sorry, 1=error, 3=sorry, 124=timeout):
- positive_control.lean (gold impl) => EXIT 0 (verifies, no sorry). #print axioms correct_inBulk = [propext, Quot.sound] per verdict.md, clean (no sorryAx).
- atk_1 PREPATCH BUG (two-conjunct guard, ignores cs) => EXIT 1. Goal collapses to (if (fieldName!="pk" && !fld.unique) then error else ok)=error under ¬acceptable; on a single-field unconditional constraint the guard doesn't fire so ok≠error. Prepatch bug reproduced.
- atk_2 PARTIAL-DOMAIN (drops !isPartial filter; would accept a partial single-field constraint) => EXIT 1.
- atk_3 BOUNDARY (drops length==1 filter; would accept first field of a multi-field constraint) => EXIT 1.
- atk_4 CONTROL-FLOW-EFFECT (always Except.ok ()) => EXIT 1. Goal reduces to Except.ok () = Except.error fieldName under ¬acceptable.
- atk_5 CONTROL-FLOW (accepts only pk; ignores unique flag & constraints) => EXIT 1.
- atk_6 UNGROUNDED-ORACLE ECHO (correct decision but wrong error payload Except.error "pk" instead of fieldName) => EXIT 1. Goal reduces to Except.error "pk" = Except.error fieldName, false when fieldName≠"pk".

All 6 same-spec wrong impls FAILED to close correct_inBulk (all EXIT 1, genuine unsolved-goal errors, not linter/timeout). Therefore ZERO verifying-but-wrong impls exist; no faithful patch needed to be materialized/resolved (patches={}).

REFINEMENT.MD AUDIT: legs #1 (fieldName:String)=I, #2 (fld.unique)=R, #3 (cs projection)=R, #4 (singleFieldUniqueConstraintFields)=I deeply-modeled, #5 (guard = the fix)=I, #6 (Except.ok proceed)=R, #7 (Except String Unit result)=R. NO A-tagged (axiom) content, NO kind-3 ungrounded-oracle legs. axiom_check.py is a legitimate skip stub, consistent with clean #print axioms (no axiom callee contract consumed). Unchanged-callee correspondences hold: get_field observed only via .unique supplied as R input (pk branch short-circuits get_field, matched by first disjunct); Options.total_unique_constraints' isinstance(UniqueConstraint) filter = the R projection defining cs, condition is None = !isPartial, len==1 filter + fields[0]=headD "" spelled out directly. G-CONF (conformance_check.py) differential-tests the R/I shadow vs an in-process post-patch replica.

ROOT CAUSE OF SOUNDNESS: the bi-conditional fully determines result on every input from the raw inputs, leaving no output freedom; any closing impl is extensionally = gold and resolves. verify ⇏ correct could NOT be exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function = field-name guard of QuerySet.in_bulk at base 67f9d076cf + gold patch. Spec's fieldNameAcceptable (pk ∨ fld.unique ∨ ∃c∈cs, ¬c.isPartial ∧ c.fields==[fieldName]) is an exact biconditional model of the post-patch raise/proceed decision: proceed⟺acceptable, error⟺¬acceptable. Verified the third disjunct maps precisely to `field_name ∈ unique_fields` where unique_fields=[c.fields[0] for c in total_unique_constraints if len==1] and total_unique_constraints filters isinstance(UniqueConstraint) ∧ condition is None (⟺ ¬isPartial). Corner cases all agree: multi-field constraint containing the name (fields≠[name]→reject both), partial single-field (filtered both), empty-fields (len==1 excludes both), headD "" default never observed. Except String Unit abstraction (unmodeled dict tail) and fld.unique-as-input are legitimate documented R-refinements of unchanged callees. Only out-of-domain point (non-pk unresolvable field → real raises FieldDoesNotExist) is correctly scoped out by supplying the pre-resolved field observable. Lean compiles clean, #print axioms correct_inBulk=[propext,Quot.sound] (no sorryAx), same_spec(Solution,prepatch)=True. No diverging input within the modeled domain; spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean docstring, UniqueConstraint/FieldInfo structures, singleFieldUniqueConstraintFields, fieldNameAcceptable, problem_spec_inBulk) uses ONLY terms already public in problem_statement: in_bulk/inBulk, field_name/fieldName, 'pk', unique(=True), UniqueConstraint, fields, Meta/constraints, and the exact ValueError message shown in the public traceback. The public problem_statement itself requests the feature ('Allow QuerySet.in_bulk() for fields with total UniqueConstraints') and gives a single-field example fields=["slug"], so the abstract acceptability rule (pk ∨ field.unique ∨ sole field of an unconditional UniqueConstraint) reveals nothing beyond it. The 'unconditional/partial' distinction is the public word 'total' (isPartial); the single-field restriction is implied by the public example and is the natural correctness boundary, not a hidden gold trick. Crucially the spec view does NOT name the patched internal helper total_unique_constraints, the local unique_fields, opts, self.model._meta, the file path django/db/models/query.py, or any diff hunk/line, and it does not narrate the bug→fix mechanism (no 'the patch adds a third conjunct'). It states the R-level acceptability predicate only. hints_text is empty, so no comparison against it is needed. No spec-view line quotes gold-patch internals or reconstructs the edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
