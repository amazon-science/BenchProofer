# P2 adversarial audit — django__django-12858

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch.lean`, `atk2_alwaysfalse.lean`, `atk3_alwaystrue.lean`, `atk4_lookuponly.lean`, `atk5_partial.lean`, `atk6_nodescend.lean`, `atk8_boundary.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is exact functional equality (result = walkReported ... none (some start) parts) over UNIVERSALLY-QUANTIFIED machinery (getField/isRelation/descend/hasTransform/hasLookup). Any impl not extensionally equal to walkReported at some instantiation makes the forall-quantified correct_ theorem false and thus unprovable. No same-spec wrong impl closes.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,8 +108,6 @@
     (isRelation : Field → Bool) (descend : Field → Model)
     (hasTransform hasLookup : Field → String → Bool)
     (start : Model) (parts : List String) : Bool := Id.run do
-  -- Walk the entry segment by segment from the originating model, tracking the
-  -- last resolved field and the current (possibly exhausted) model context.
   let mut fld : Option Field := none
   let mut ctx : Option Model := some start
   let mut err : Bool := false
@@ -118,18 +116,19 @@
     | some m =>
       match getField m part with
       | some f =>
-        -- Resolved: descend into the related model if this field is a relation,
-        -- otherwise the context is exhausted.
         fld := some f
         ctx := if isRelation f then some (descend f) else none
       | none =>
-        -- Unresolved: report unless the segment is a transform or a registered
-        -- lookup of the preceding resolved field.
-        if reportSegment hasTransform hasLookup fld part then
+        let report : Bool := match fld with
+          | none => true
+          | some f => !hasTransform f part
+        if report then
           err := true
     | none =>
-      -- Context exhausted: same report decision against the preceding field.
-      if reportSegment hasTransform hasLookup fld part then
+      let report : Bool := match fld with
+        | none => true
+        | some f => !hasTransform f part
+      if report then
         err := true
   return err
 -- impl-end
```

Attack 2 — `atk2_alwaysfalse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,30 +108,7 @@
     (isRelation : Field → Bool) (descend : Field → Model)
     (hasTransform hasLookup : Field → String → Bool)
     (start : Model) (parts : List String) : Bool := Id.run do
-  -- Walk the entry segment by segment from the originating model, tracking the
-  -- last resolved field and the current (possibly exhausted) model context.
-  let mut fld : Option Field := none
-  let mut ctx : Option Model := some start
-  let mut err : Bool := false
-  for part in parts do
-    match ctx with
-    | some m =>
-      match getField m part with
-      | some f =>
-        -- Resolved: descend into the related model if this field is a relation,
-        -- otherwise the context is exhausted.
-        fld := some f
-        ctx := if isRelation f then some (descend f) else none
-      | none =>
-        -- Unresolved: report unless the segment is a transform or a registered
-        -- lookup of the preceding resolved field.
-        if reportSegment hasTransform hasLookup fld part then
-          err := true
-    | none =>
-      -- Context exhausted: same report decision against the preceding field.
-      if reportSegment hasTransform hasLookup fld part then
-        err := true
-  return err
+  return false
 -- impl-end
 
 
```

Attack 3 — `atk3_alwaystrue.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,30 +108,7 @@
     (isRelation : Field → Bool) (descend : Field → Model)
     (hasTransform hasLookup : Field → String → Bool)
     (start : Model) (parts : List String) : Bool := Id.run do
-  -- Walk the entry segment by segment from the originating model, tracking the
-  -- last resolved field and the current (possibly exhausted) model context.
-  let mut fld : Option Field := none
-  let mut ctx : Option Model := some start
-  let mut err : Bool := false
-  for part in parts do
-    match ctx with
-    | some m =>
-      match getField m part with
-      | some f =>
-        -- Resolved: descend into the related model if this field is a relation,
-        -- otherwise the context is exhausted.
-        fld := some f
-        ctx := if isRelation f then some (descend f) else none
-      | none =>
-        -- Unresolved: report unless the segment is a transform or a registered
-        -- lookup of the preceding resolved field.
-        if reportSegment hasTransform hasLookup fld part then
-          err := true
-    | none =>
-      -- Context exhausted: same report decision against the preceding field.
-      if reportSegment hasTransform hasLookup fld part then
-        err := true
-  return err
+  return true
 -- impl-end
 
 
```

Attack 4 — `atk4_lookuponly.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,8 +108,6 @@
     (isRelation : Field → Bool) (descend : Field → Model)
     (hasTransform hasLookup : Field → String → Bool)
     (start : Model) (parts : List String) : Bool := Id.run do
-  -- Walk the entry segment by segment from the originating model, tracking the
-  -- last resolved field and the current (possibly exhausted) model context.
   let mut fld : Option Field := none
   let mut ctx : Option Model := some start
   let mut err : Bool := false
@@ -118,18 +116,19 @@
     | some m =>
       match getField m part with
       | some f =>
-        -- Resolved: descend into the related model if this field is a relation,
-        -- otherwise the context is exhausted.
         fld := some f
         ctx := if isRelation f then some (descend f) else none
       | none =>
-        -- Unresolved: report unless the segment is a transform or a registered
-        -- lookup of the preceding resolved field.
-        if reportSegment hasTransform hasLookup fld part then
+        let report : Bool := match fld with
+          | none => true
+          | some f => !hasLookup f part
+        if report then
           err := true
     | none =>
-      -- Context exhausted: same report decision against the preceding field.
-      if reportSegment hasTransform hasLookup fld part then
+      let report : Bool := match fld with
+        | none => true
+        | some f => !hasLookup f part
+      if report then
         err := true
   return err
 -- impl-end
```

Attack 5 — `atk5_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,8 +108,6 @@
     (isRelation : Field → Bool) (descend : Field → Model)
     (hasTransform hasLookup : Field → String → Bool)
     (start : Model) (parts : List String) : Bool := Id.run do
-  -- Walk the entry segment by segment from the originating model, tracking the
-  -- last resolved field and the current (possibly exhausted) model context.
   let mut fld : Option Field := none
   let mut ctx : Option Model := some start
   let mut err : Bool := false
@@ -118,18 +116,19 @@
     | some m =>
       match getField m part with
       | some f =>
-        -- Resolved: descend into the related model if this field is a relation,
-        -- otherwise the context is exhausted.
         fld := some f
         ctx := if isRelation f then some (descend f) else none
       | none =>
-        -- Unresolved: report unless the segment is a transform or a registered
-        -- lookup of the preceding resolved field.
-        if reportSegment hasTransform hasLookup fld part then
+        let report : Bool := match fld with
+          | none => true
+          | some _ => false
+        if report then
           err := true
     | none =>
-      -- Context exhausted: same report decision against the preceding field.
-      if reportSegment hasTransform hasLookup fld part then
+      let report : Bool := match fld with
+        | none => true
+        | some _ => false
+      if report then
         err := true
   return err
 -- impl-end
```

Attack 6 — `atk6_nodescend.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,8 +108,6 @@
     (isRelation : Field → Bool) (descend : Field → Model)
     (hasTransform hasLookup : Field → String → Bool)
     (start : Model) (parts : List String) : Bool := Id.run do
-  -- Walk the entry segment by segment from the originating model, tracking the
-  -- last resolved field and the current (possibly exhausted) model context.
   let mut fld : Option Field := none
   let mut ctx : Option Model := some start
   let mut err : Bool := false
@@ -118,17 +116,12 @@
     | some m =>
       match getField m part with
       | some f =>
-        -- Resolved: descend into the related model if this field is a relation,
-        -- otherwise the context is exhausted.
         fld := some f
-        ctx := if isRelation f then some (descend f) else none
+        ctx := none
       | none =>
-        -- Unresolved: report unless the segment is a transform or a registered
-        -- lookup of the preceding resolved field.
         if reportSegment hasTransform hasLookup fld part then
           err := true
     | none =>
-      -- Context exhausted: same report decision against the preceding field.
       if reportSegment hasTransform hasLookup fld part then
         err := true
   return err
```

Attack 7 — `atk7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -108,216 +108,11 @@
     (isRelation : Field → Bool) (descend : Field → Model)
     (hasTransform hasLookup : Field → String → Bool)
     (start : Model) (parts : List String) : Bool := Id.run do
-  -- Walk the entry segment by segment from the originating model, tracking the
-  -- last resolved field and the current (possibly exhausted) model context.
-  let mut fld : Option Field := none
-  let mut ctx : Option Model := some start
-  let mut err : Bool := false
-  for part in parts do
-    match ctx with
-    | some m =>
-      match getField m part with
-      | some f =>
-        -- Resolved: descend into the related model if this field is a relation,
-        -- otherwise the context is exhausted.
-        fld := some f
-        ctx := if isRelation f then some (descend f) else none
-      | none =>
-        -- Unresolved: report unless the segment is a transform or a registered
-        -- lookup of the preceding resolved field.
-        if reportSegment hasTransform hasLookup fld part then
-          err := true
-    | none =>
-      -- Context exhausted: same report decision against the preceding field.
-      if reportSegment hasTransform hasLookup fld part then
-        err := true
-  return err
+  return walkReported getField isRelation descend hasTransform hasLookup none (some start) parts
 -- impl-end
 
 
 -- proof-start
-/-- Pure reification of one loop-body iteration on state `(fld, ctx, err)` for a
-given `part`, matching the imperative body of `implementation_orderingFieldCheck`.
-The unresolved / exhausted branches use `err || reportSegment …` so the step is
-provably equal to the imperative `if reportSegment then err := true`. -/
-def step {Model Field : Type}
-    (getField : Model → String → Option Field)
-    (isRelation : Field → Bool) (descend : Field → Model)
-    (hasTransform hasLookup : Field → String → Bool)
-    (s : Option Field × Option Model × Bool) (part : String) :
-    Option Field × Option Model × Bool :=
-  let (fld, ctx, err) := s
-  match ctx with
-  | some m =>
-    match getField m part with
-    | some f => (some f, (if isRelation f then some (descend f) else none), err)
-    | none => (fld, ctx, err || reportSegment hasTransform hasLookup fld part)
-  | none => (fld, none, err || reportSegment hasTransform hasLookup fld part)
-/-- The desugared body of one imperative loop iteration, operating on the loop's
-own packed state `(ctx, err, fld)` (the order of the `mut` variables). The
-unresolved / exhausted branches write `err || reportSegment …`, matching the
-imperative `if reportSegment then err := true`. Note the component order differs
-from `step`, which uses `(fld, ctx, err)`. -/
-def loopBodyOrderingFieldCheck {Model Field : Type}
-    (getField : Model → String → Option Field)
-    (isRelation : Field → Bool) (descend : Field → Model)
-    (hasTransform hasLookup : Field → String → Bool)
-    (s : Option Model × Bool × Option Field) (part : String) :
-    Option Model × Bool × Option Field :=
-  let (ctx, err, fld) := s
-  match ctx with
-  | some m =>
-    match getField m part with
-    | some f => (if isRelation f then some (descend f) else none, err, some f)
-    | none => (ctx, err || reportSegment hasTransform hasLookup fld part, fld)
-  | none => (none, err || reportSegment hasTransform hasLookup fld part, fld)
-
-/-- The boolean value written by `if reportSegment … then err := true` equals
-`err || reportSegment …`: for booleans, `(if b then true else err) = (err || b)`. -/
-theorem if_report_eq_or_orderingFieldCheck (err b : Bool) :
-    (if b = true then true else err) = (err || b) := by
-  cases b <;> cases err <;> rfl
-
-/-- Desugar the monadic `Id.run do` for-loop into a `List.foldl` of the explicit
-loop body over the packed state `(ctx, err, fld)`, reading off the `err`
-component (`.2.1`). -/
-theorem impl_eq_foldl_loopBody_orderingFieldCheck {Model Field : Type}
-    (getField : Model → String → Option Field)
-    (isRelation : Field → Bool) (descend : Field → Model)
-    (hasTransform hasLookup : Field → String → Bool)
-    (start : Model) (parts : List String) :
-    implementation_orderingFieldCheck getField isRelation descend hasTransform hasLookup
-        start parts
-      = (List.foldl (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup)
-          (some start, false, none) parts).2.1 := by
-  -- Generalized loop lemma matching the implementation's exact `let mut fld/ctx/err`
-  -- declaration order, so its desugared `Id.run do for` is defeq to the goal's `forIn`.
-  -- Proved by induction on `parts`; the concrete run uses `fld = none, ctx = some start`.
-  suffices key : ∀ (fld : Option Field) (ctx : Option Model) (err : Bool),
-      (Id.run do
-        let mut fld' := fld
-        let mut ctx' := ctx
-        let mut err' := err
-        for part in parts do
-          match ctx' with
-          | some m =>
-            match getField m part with
-            | some f =>
-              fld' := some f
-              ctx' := if isRelation f then some (descend f) else none
-            | none =>
-              if reportSegment hasTransform hasLookup fld' part then
-                err' := true
-          | none =>
-            if reportSegment hasTransform hasLookup fld' part then
-              err' := true
-        return err')
-        = (List.foldl (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup)
-            (ctx, err, fld) parts).2.1 by
-    simpa only [implementation_orderingFieldCheck] using key none (some start) false
-  intro fld ctx err
-  induction parts generalizing fld ctx err with
-  | nil => rfl
-  | cons part rest ih =>
-    simp only [List.foldl_cons, loopBodyOrderingFieldCheck, Id.run, bind, pure, List.forIn_cons]
-    cases ctx with
-    | none =>
-      by_cases hb : reportSegment hasTransform hasLookup fld part = true <;>
-        simp only [hb, if_true, Bool.or_true, Bool.or_false] <;>
-        exact ih _ _ _
-    | some m =>
-      cases hg : getField m part with
-      | none =>
-        by_cases hb : reportSegment hasTransform hasLookup fld part = true <;>
-          simp only [hg, hb, if_true, Bool.or_true, Bool.or_false] <;>
-          exact ih _ _ _
-      | some f =>
-        simp only [hg]
-        exact ih _ _ _
-
-/-- Fold-level correspondence between the loop body and `step` across the
-coordinate permutation `(ctx, err, fld) ↔ (fld, ctx, err)`: folding the loop body
-from `s` and reading `err` (`.2.1`) equals folding `step` from the permuted state
-`(s.2.2, s.1, s.2.1)` and reading `.2.2`. Proved by induction on `parts`,
-generalizing the accumulator `s`. -/
-theorem foldl_loopBody_eq_step_orderingFieldCheck {Model Field : Type}
-    (getField : Model → String → Option Field)
-    (isRelation : Field → Bool) (descend : Field → Model)
-    (hasTransform hasLookup : Field → String → Bool)
-    (parts : List String) (s : Option Model × Bool × Option Field) :
-    (List.foldl (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup)
-        s parts).2.1
-      = (List.foldl (step getField isRelation descend hasTransform hasLookup)
-          (s.2.2, s.1, s.2.1) parts).2.2 := by
-  induction parts generalizing s with
-  | nil => rfl
-  | cons part rest ih =>
-    rw [List.foldl_cons, List.foldl_cons, ih]
-    have hstep :
-        ((loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup s part).2.2,
-            (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup s part).1,
-            (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup s part).2.1)
-          = step getField isRelation descend hasTransform hasLookup (s.2.2, s.1, s.2.1) part := by
-      obtain ⟨ctx, err, fld⟩ := s
-      simp only [loopBodyOrderingFieldCheck, step]
-      split <;> (try split) <;> rfl
-    rw [hstep]
-
-/-- Desugar the monadic implementation into a pure left fold of `step`. -/
-theorem loop_is_foldl {Model Field : Type}
-    (getField : Model → String → Option Field)
-    (isRelation : Field → Bool) (descend : Field → Model)
-    (hasTransform hasLookup : Field → String → Bool)
-    (start : Model) (parts : List String) :
-    implementation_orderingFieldCheck getField isRelation descend hasTransform hasLookup
-        start parts
-      = (List.foldl (step getField isRelation descend hasTransform hasLookup)
-          (none, some start, false) parts).2.2 := by
-  rw [impl_eq_foldl_loopBody_orderingFieldCheck]
-  exact foldl_loopBody_eq_step_orderingFieldCheck getField isRelation descend
-    hasTransform hasLookup parts (some start, false, none)
-
-/-- Generalized loop invariant: folding `step` from an ARBITRARY state
-`(fld, ctx, err)` yields `err || walkReported … fld ctx parts`. -/
-theorem foldl_step_eq_walk {Model Field : Type}
-    (getField : Model → String → Option Field)
-    (isRelation : Field → Bool) (descend : Field → Model)
-    (hasTransform hasLookup : Field → String → Bool)
-    (parts : List String) (fld : Option Field) (ctx : Option Model) (err : Bool) :
-    (List.foldl (step getField isRelation descend hasTransform hasLookup)
-        (fld, ctx, err) parts).2.2
-      = (err ||
-          walkReported getField isRelation descend hasTransform hasLookup
-            fld ctx parts) := by
-  induction parts generalizing fld ctx err with
-  | nil => simp [walkReported]
-  | cons part rest ih =>
-    rw [List.foldl_cons]
-    cases ctx with
-    | none =>
-      show (List.foldl (step getField isRelation descend hasTransform hasLookup)
-          (fld, none, err || reportSegment hasTransform hasLookup fld part) rest).2.2 = _
-      rw [ih]
-      conv_rhs => rw [walkReported]
-      simp [Bool.or_assoc]
-    | some m =>
-      cases hf : getField m part with
-      | none =>
-        rw [show step getField isRelation descend hasTransform hasLookup (fld, some m, err) part
-            = (fld, some m, err || reportSegment hasTransform hasLookup fld part) by
-          simp only [step, hf]]
-        rw [ih]
-        conv_rhs => rw [walkReported]
-        rw [hf]
-        simp [Bool.or_assoc]
-      | some f =>
-        rw [show step getField isRelation descend hasTransform hasLookup (fld, some m, err) part
-            = (some f, (if isRelation f then some (descend f) else none), err) by
-          simp only [step, hf]]
-        rw [ih]
-        conv_rhs => rw [walkReported]
-        rw [hf]
-
 theorem correct_orderingFieldCheck :
     ∀ {Model Field : Type}
       (getField : Model → String → Option Field)
@@ -329,9 +124,6 @@
         (implementation_orderingFieldCheck getField isRelation descend hasTransform hasLookup
           start parts) := by
   intro Model Field getField isRelation descend hasTransform hasLookup start parts
-  unfold problem_spec_orderingFieldCheck
-  rw [loop_is_foldl getField isRelation descend hasTransform hasLookup start parts,
-      foldl_step_eq_walk getField isRelation descend hasTransform hasLookup parts
-        none (some start) false, Bool.false_or]
-
+  unfold problem_spec_orderingFieldCheck implementation_orderingFieldCheck
+  rfl
 -- proof-end
```

Attack 8 — `atk8_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -108,8 +108,6 @@
     (isRelation : Field → Bool) (descend : Field → Model)
     (hasTransform hasLookup : Field → String → Bool)
     (start : Model) (parts : List String) : Bool := Id.run do
-  -- Walk the entry segment by segment from the originating model, tracking the
-  -- last resolved field and the current (possibly exhausted) model context.
   let mut fld : Option Field := none
   let mut ctx : Option Model := some start
   let mut err : Bool := false
@@ -118,17 +116,11 @@
     | some m =>
       match getField m part with
       | some f =>
-        -- Resolved: descend into the related model if this field is a relation,
-        -- otherwise the context is exhausted.
         fld := some f
         ctx := if isRelation f then some (descend f) else none
       | none =>
-        -- Unresolved: report unless the segment is a transform or a registered
-        -- lookup of the preceding resolved field.
-        if reportSegment hasTransform hasLookup fld part then
-          err := true
+        pure ()
     | none =>
-      -- Context exhausted: same report decision against the preceding field.
       if reportSegment hasTransform hasLookup fld part then
         err := true
   return err
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Validating that every entry of a model's declared ordering refers to something
that actually exists.

An ordering entry that spans relations is written as a chain of name segments
separated by the relation separator (here a `List String` of segments). The
validator walks the chain segment by segment starting from the originating model:

  * each segment is looked up as a field of the current model context;
  * if that field is a relation, the walk descends into the related model and
    continues with the next segment;
  * if that field is not a relation, the context becomes exhausted (there is
    nothing further to descend into);
  * if a segment cannot be resolved as a field of the current context (either the
    context is already exhausted, or no such field exists), the validator decides
    whether to report this entry as referring to a nonexistent field, related
    field, or lookup.

The decision about an unresolved segment is the crux: an unresolved segment is
reported ONLY when there is no preceding resolved field to interpret it against,
OR the segment is neither a transform NOR a registered lookup of that preceding
field. A segment that names a transform or a registered lookup of the preceding
field is therefore accepted (it is a legitimate ordering directive, not a
nonexistent field). The whole entry is reported if ANY of its segments is
reported.

Here the model machinery (resolving a segment to a field, deciding whether a
field is a relation, descending into a related model, and asking whether a
segment is a transform or a registered lookup of a field) is taken as arbitrary
parameters, so the behavior pinned below holds for every such machinery; the
modeled behavior is solely the walk and the report decision.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a proof axiom. The model machinery
-- is taken as universally-quantified function parameters:
--   * `getField  : Model → String → Option Field` — resolve a segment to a field
--     of a model context (`none` = no such field / the lookup failed);
--   * `isRelation : Field → Bool` — whether a resolved field relates to another
--     model (so the walk may descend);
--   * `descend    : Field → Model` — the related model a relation field leads to;
--   * `hasTransform / hasLookup : Field → String → Bool` — whether a segment
--     names a transform / a registered lookup of a field.
-- Because the result is pinned for EVERY such machinery, the proof consumes no
-- property of any of them, so there is no `opaque`/`axiom` callee contract; the
-- binding of these parameters to the real model machinery is exercised by G-CONF.
-- axioms-end

-- pure-start
/-- Whether an UNRESOLVED segment is reported as referring to a nonexistent
field, related field, or lookup. It is reported exactly when there is no
preceding resolved field (`fld = none`), or the segment is neither a transform
nor a registered lookup of the preceding field. -/
def reportSegment {Field : Type}
    (hasTransform hasLookup : Field → String → Bool)
    (fld : Option Field) (part : String) : Bool :=
  match fld with
  | none => true
  | some f => (!hasTransform f part) && (!hasLookup f part)

/-- The reference outcome of the walk over an ordering entry's remaining
segments, given the last successfully resolved field `fld` and the current model
context `ctx` (`none` = exhausted). The entry is reported (`true`) iff some
remaining segment is reported. -/
def walkReported {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool) :
    Option Field → Option Model → List String → Bool
  | _, _, [] => false
  | fld, ctx, part :: rest =>
    match ctx with
    | some m =>
      match getField m part with
      | some f =>
        walkReported getField isRelation descend hasTransform hasLookup
          (some f) (if isRelation f then some (descend f) else none) rest
      | none =>
        reportSegment hasTransform hasLookup fld part ||
          walkReported getField isRelation descend hasTransform hasLookup fld ctx rest
    | none =>
      reportSegment hasTransform hasLookup fld part ||
        walkReported getField isRelation descend hasTransform hasLookup fld none rest
-- pure-end

-- post-conditions-start
/-- The reported-flag for a single relation-spanning ordering entry is fully
pinned to the inputs: it equals the reference walk over the entry's segments,
starting from the originating model with no field resolved yet. No output
component is left free — the flag is determined by the segments and the model
machinery. -/
def problem_spec_orderingFieldCheck {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (start : Model) (parts : List String) (result : Bool) : Prop :=
  result =
    walkReported getField isRelation descend hasTransform hasLookup
      none (some start) parts
-- post-conditions-end

-- impl-start
def implementation_orderingFieldCheck {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (start : Model) (parts : List String) : Bool := Id.run do
  -- Walk the entry segment by segment from the originating model, tracking the
  -- last resolved field and the current (possibly exhausted) model context.
  let mut fld : Option Field := none
  let mut ctx : Option Model := some start
  let mut err : Bool := false
  for part in parts do
    match ctx with
    | some m =>
      match getField m part with
      | some f =>
        -- Resolved: descend into the related model if this field is a relation,
        -- otherwise the context is exhausted.
        fld := some f
        ctx := if isRelation f then some (descend f) else none
      | none =>
        -- Unresolved: report unless the segment is a transform or a registered
        -- lookup of the preceding resolved field.
        if reportSegment hasTransform hasLookup fld part then
          err := true
    | none =>
      -- Context exhausted: same report decision against the preceding field.
      if reportSegment hasTransform hasLookup fld part then
        err := true
  return err
-- impl-end


-- proof-start
/-- Pure reification of one loop-body iteration on state `(fld, ctx, err)` for a
given `part`, matching the imperative body of `implementation_orderingFieldCheck`.
The unresolved / exhausted branches use `err || reportSegment …` so the step is
provably equal to the imperative `if reportSegment then err := true`. -/
def step {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (s : Option Field × Option Model × Bool) (part : String) :
    Option Field × Option Model × Bool :=
  let (fld, ctx, err) := s
  match ctx with
  | some m =>
    match getField m part with
    | some f => (some f, (if isRelation f then some (descend f) else none), err)
    | none => (fld, ctx, err || reportSegment hasTransform hasLookup fld part)
  | none => (fld, none, err || reportSegment hasTransform hasLookup fld part)
/-- The desugared body of one imperative loop iteration, operating on the loop's
own packed state `(ctx, err, fld)` (the order of the `mut` variables). The
unresolved / exhausted branches write `err || reportSegment …`, matching the
imperative `if reportSegment then err := true`. Note the component order differs
from `step`, which uses `(fld, ctx, err)`. -/
def loopBodyOrderingFieldCheck {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (s : Option Model × Bool × Option Field) (part : String) :
    Option Model × Bool × Option Field :=
  let (ctx, err, fld) := s
  match ctx with
  | some m =>
    match getField m part with
    | some f => (if isRelation f then some (descend f) else none, err, some f)
    | none => (ctx, err || reportSegment hasTransform hasLookup fld part, fld)
  | none => (none, err || reportSegment hasTransform hasLookup fld part, fld)

/-- The boolean value written by `if reportSegment … then err := true` equals
`err || reportSegment …`: for booleans, `(if b then true else err) = (err || b)`. -/
theorem if_report_eq_or_orderingFieldCheck (err b : Bool) :
    (if b = true then true else err) = (err || b) := by
  cases b <;> cases err <;> rfl

/-- Desugar the monadic `Id.run do` for-loop into a `List.foldl` of the explicit
loop body over the packed state `(ctx, err, fld)`, reading off the `err`
component (`.2.1`). -/
theorem impl_eq_foldl_loopBody_orderingFieldCheck {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (start : Model) (parts : List String) :
    implementation_orderingFieldCheck getField isRelation descend hasTransform hasLookup
        start parts
      = (List.foldl (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup)
          (some start, false, none) parts).2.1 := by
  -- Generalized loop lemma matching the implementation's exact `let mut fld/ctx/err`
  -- declaration order, so its desugared `Id.run do for` is defeq to the goal's `forIn`.
  -- Proved by induction on `parts`; the concrete run uses `fld = none, ctx = some start`.
  suffices key : ∀ (fld : Option Field) (ctx : Option Model) (err : Bool),
      (Id.run do
        let mut fld' := fld
        let mut ctx' := ctx
        let mut err' := err
        for part in parts do
          match ctx' with
          | some m =>
            match getField m part with
            | some f =>
              fld' := some f
              ctx' := if isRelation f then some (descend f) else none
            | none =>
              if reportSegment hasTransform hasLookup fld' part then
                err' := true
          | none =>
            if reportSegment hasTransform hasLookup fld' part then
              err' := true
        return err')
        = (List.foldl (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup)
            (ctx, err, fld) parts).2.1 by
    simpa only [implementation_orderingFieldCheck] using key none (some start) false
  intro fld ctx err
  induction parts generalizing fld ctx err with
  | nil => rfl
  | cons part rest ih =>
    simp only [List.foldl_cons, loopBodyOrderingFieldCheck, Id.run, bind, pure, List.forIn_cons]
    cases ctx with
    | none =>
      by_cases hb : reportSegment hasTransform hasLookup fld part = true <;>
        simp only [hb, if_true, Bool.or_true, Bool.or_false] <;>
        exact ih _ _ _
    | some m =>
      cases hg : getField m part with
      | none =>
        by_cases hb : reportSegment hasTransform hasLookup fld part = true <;>
          simp only [hg, hb, if_true, Bool.or_true, Bool.or_false] <;>
          exact ih _ _ _
      | some f =>
        simp only [hg]
        exact ih _ _ _

/-- Fold-level correspondence between the loop body and `step` across the
coordinate permutation `(ctx, err, fld) ↔ (fld, ctx, err)`: folding the loop body
from `s` and reading `err` (`.2.1`) equals folding `step` from the permuted state
`(s.2.2, s.1, s.2.1)` and reading `.2.2`. Proved by induction on `parts`,
generalizing the accumulator `s`. -/
theorem foldl_loopBody_eq_step_orderingFieldCheck {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (parts : List String) (s : Option Model × Bool × Option Field) :
    (List.foldl (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup)
        s parts).2.1
      = (List.foldl (step getField isRelation descend hasTransform hasLookup)
          (s.2.2, s.1, s.2.1) parts).2.2 := by
  induction parts generalizing s with
  | nil => rfl
  | cons part rest ih =>
    rw [List.foldl_cons, List.foldl_cons, ih]
    have hstep :
        ((loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup s part).2.2,
            (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup s part).1,
            (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup s part).2.1)
          = step getField isRelation descend hasTransform hasLookup (s.2.2, s.1, s.2.1) part := by
      obtain ⟨ctx, err, fld⟩ := s
      simp only [loopBodyOrderingFieldCheck, step]
      split <;> (try split) <;> rfl
    rw [hstep]

/-- Desugar the monadic implementation into a pure left fold of `step`. -/
theorem loop_is_foldl {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (start : Model) (parts : List String) :
    implementation_orderingFieldCheck getField isRelation descend hasTransform hasLookup
        start parts
      = (List.foldl (step getField isRelation descend hasTransform hasLookup)
          (none, some start, false) parts).2.2 := by
  rw [impl_eq_foldl_loopBody_orderingFieldCheck]
  exact foldl_loopBody_eq_step_orderingFieldCheck getField isRelation descend
    hasTransform hasLookup parts (some start, false, none)

/-- Generalized loop invariant: folding `step` from an ARBITRARY state
`(fld, ctx, err)` yields `err || walkReported … fld ctx parts`. -/
theorem foldl_step_eq_walk {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (parts : List String) (fld : Option Field) (ctx : Option Model) (err : Bool) :
    (List.foldl (step getField isRelation descend hasTransform hasLookup)
        (fld, ctx, err) parts).2.2
      = (err ||
          walkReported getField isRelation descend hasTransform hasLookup
            fld ctx parts) := by
  induction parts generalizing fld ctx err with
  | nil => simp [walkReported]
  | cons part rest ih =>
    rw [List.foldl_cons]
    cases ctx with
    | none =>
      show (List.foldl (step getField isRelation descend hasTransform hasLookup)
          (fld, none, err || reportSegment hasTransform hasLookup fld part) rest).2.2 = _
      rw [ih]
      conv_rhs => rw [walkReported]
      simp [Bool.or_assoc]
    | some m =>
      cases hf : getField m part with
      | none =>
        rw [show step getField isRelation descend hasTransform hasLookup (fld, some m, err) part
            = (fld, some m, err || reportSegment hasTransform hasLookup fld part) by
          simp only [step, hf]]
        rw [ih]
        conv_rhs => rw [walkReported]
        rw [hf]
        simp [Bool.or_assoc]
      | some f =>
        rw [show step getField isRelation descend hasTransform hasLookup (fld, some m, err) part
            = (some f, (if isRelation f then some (descend f) else none), err) by
          simp only [step, hf]]
        rw [ih]
        conv_rhs => rw [walkReported]
        rw [hf]

theorem correct_orderingFieldCheck :
    ∀ {Model Field : Type}
      (getField : Model → String → Option Field)
      (isRelation : Field → Bool) (descend : Field → Model)
      (hasTransform hasLookup : Field → String → Bool)
      (start : Model) (parts : List String),
      problem_spec_orderingFieldCheck getField isRelation descend hasTransform hasLookup
          start parts
        (implementation_orderingFieldCheck getField isRelation descend hasTransform hasLookup
          start parts) := by
  intro Model Field getField isRelation descend hasTransform hasLookup start parts
  unfold problem_spec_orderingFieldCheck
  rw [loop_is_foldl getField isRelation descend hasTransform hasLookup start parts,
      foldl_step_eq_walk getField isRelation descend hasTransform hasLookup parts
        none (some start) false, Bool.false_or]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

spec_view elides BOTH impl and proof regions, so same_spec only pins axioms/pure/post regions; all 8 attacks confirmed same_spec=True. The postcondition problem_spec_orderingFieldCheck is EXACT functional equality result = walkReported(...) over universally-quantified machinery params -- the strongest possible spec.

### ATTACKS (cmd: bash scripts/lean_verify.sh <file>; 0=verifies,1=error,3=sorry):
- pos_control (gold impl): exit 0. #print axioms => [propext, Quot.sound] (clean). POSITIVE CONTROL PASS.
- atk1_prepatch (prepatch bug, transform-only report; hasLookup dropped): exit 1. Does NOT close (gold proof fails on buggy impl). PREPATCH REPRODUCED.
- atk2_alwaysfalse (ungrounded const `return false`): exit 1. Does NOT close.
- atk3_alwaystrue (ungrounded const `return true`): exit 1. Does NOT close.
- atk4_lookuponly (symmetric bug, lookup-only report; hasTransform dropped): exit 1. Does NOT close.
- atk5_partial (partial-domain: spare ALL segments with a preceding resolved field): exit 1. Does NOT close.
- atk6_nodescend (control-flow-effect: never descend, ctx:=none after resolve): exit 1. Does NOT close.
- atk7_echo (ungrounded-oracle echo: `return walkReported getField isRelation descend hasTransform hasLookup none (some start) parts`, proof by rfl): exit 0, #print axioms => 'does not depend on any axioms' (clean). This is the ONLY closing attack -- but it is EXTENSIONALLY the post-patch behavior (literally the spec function), i.e. a correct impl, not a wrong one. Its faithful refined patch = the post-patch report condition = gold patch. run_resolve('django__django-12858', patch, retries=1) => ResolveResult(resolved=True, completed=True, attempts=1, flaky=False); FAIL_TO_PASS test_ordering_pointing_to_lookup_not_transform SUCCESS, all 73 PASS_TO_PASS success. RESOLVES => not a break.
- atk8_boundary (boundary: report only on ctx-exhausted branch, skip getField=none unresolved): exit 1. Does NOT close.

MANDATORY resolve step: the only clean-axiom-closing impl (atk7_echo) had its faithful patch materialized and run through the official harness (run_resolve) => RESOLVED. No closing wrong impl exists whose patch fails to resolve, so verify does NOT imply not-correct here.

refinement.md / mapping.md AUDIT: grep of Solution.lean shows NO opaque/axiom declarations; meta.json axioms=[]. Every leg is R / A-reference / I -- no kind-3. The five machinery ops (getField=get_field, isRelation=is_relation, descend=get_path_info()[-1].to_opts.model, hasTransform=get_transform is not None, hasLookup=get_lookup is not None) are universally-quantified A-reference parameters correctly bound to the REAL Python callees (validated by G-CONF binding); the postcondition consumes NO property of any of them, so the absence of an A-consumed leg is correct. Correspondence holds.

VERDICT: SOUND. >=5 distinct wrong-impl attacks (prepatch, always-false, always-true, symmetric-lookup, partial-domain, no-descend, boundary = 7 genuinely-wrong) all FAIL to close; the single closing impl is a correct echo whose materialized patch RESOLVES. Spec is exact-functional-equality and admits no verifying-but-nonresolving twin.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch.lean`, `atk2_alwaysfalse.lean`, `atk3_alwaystrue.lean`, `atk4_lookuponly.lean`, `atk5_partial.lean`, `atk6_nodescend.lean`, `atk8_boundary.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is exact functional equality (result = walkReported ... none (some start) parts) over UNIVERSALLY-QUANTIFIED machinery (getField/isRelation/descend/hasTransform/hasLookup). Any impl not extensionally equal to walkReported at some instantiation makes the forall-quantified correct_ theorem false and thus unprovable. No same-spec wrong impl closes.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_alwaysfalse.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_alwaystrue.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_lookuponly.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_partial.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_nodescend.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk8_boundary.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Validating that every entry of a model's declared ordering refers to something
that actually exists.

An ordering entry that spans relations is written as a chain of name segments
separated by the relation separator (here a `List String` of segments). The
validator walks the chain segment by segment starting from the originating model:

  * each segment is looked up as a field of the current model context;
  * if that field is a relation, the walk descends into the related model and
    continues with the next segment;
  * if that field is not a relation, the context becomes exhausted (there is
    nothing further to descend into);
  * if a segment cannot be resolved as a field of the current context (either the
    context is already exhausted, or no such field exists), the validator decides
    whether to report this entry as referring to a nonexistent field, related
    field, or lookup.

The decision about an unresolved segment is the crux: an unresolved segment is
reported ONLY when there is no preceding resolved field to interpret it against,
OR the segment is neither a transform NOR a registered lookup of that preceding
field. A segment that names a transform or a registered lookup of the preceding
field is therefore accepted (it is a legitimate ordering directive, not a
nonexistent field). The whole entry is reported if ANY of its segments is
reported.

Here the model machinery (resolving a segment to a field, deciding whether a
field is a relation, descending into a related model, and asking whether a
segment is a transform or a registered lookup of a field) is taken as arbitrary
parameters, so the behavior pinned below holds for every such machinery; the
modeled behavior is solely the walk and the report decision.
-/

-- axioms-start
-- No unchanged outside callee is consumed as a proof axiom. The model machinery
-- is taken as universally-quantified function parameters:
--   * `getField  : Model → String → Option Field` — resolve a segment to a field
--     of a model context (`none` = no such field / the lookup failed);
--   * `isRelation : Field → Bool` — whether a resolved field relates to another
--     model (so the walk may descend);
--   * `descend    : Field → Model` — the related model a relation field leads to;
--   * `hasTransform / hasLookup : Field → String → Bool` — whether a segment
--     names a transform / a registered lookup of a field.
-- Because the result is pinned for EVERY such machinery, the proof consumes no
-- property of any of them, so there is no `opaque`/`axiom` callee contract; the
-- binding of these parameters to the real model machinery is exercised by G-CONF.
-- axioms-end

-- pure-start
/-- Whether an UNRESOLVED segment is reported as referring to a nonexistent
field, related field, or lookup. It is reported exactly when there is no
preceding resolved field (`fld = none`), or the segment is neither a transform
nor a registered lookup of the preceding field. -/
def reportSegment {Field : Type}
    (hasTransform hasLookup : Field → String → Bool)
    (fld : Option Field) (part : String) : Bool :=
  match fld with
  | none => true
  | some f => (!hasTransform f part) && (!hasLookup f part)

/-- The reference outcome of the walk over an ordering entry's remaining
segments, given the last successfully resolved field `fld` and the current model
context `ctx` (`none` = exhausted). The entry is reported (`true`) iff some
remaining segment is reported. -/
def walkReported {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool) :
    Option Field → Option Model → List String → Bool
  | _, _, [] => false
  | fld, ctx, part :: rest =>
    match ctx with
    | some m =>
      match getField m part with
      | some f =>
        walkReported getField isRelation descend hasTransform hasLookup
          (some f) (if isRelation f then some (descend f) else none) rest
      | none =>
        reportSegment hasTransform hasLookup fld part ||
          walkReported getField isRelation descend hasTransform hasLookup fld ctx rest
    | none =>
      reportSegment hasTransform hasLookup fld part ||
        walkReported getField isRelation descend hasTransform hasLookup fld none rest
-- pure-end

-- post-conditions-start
/-- The reported-flag for a single relation-spanning ordering entry is fully
pinned to the inputs: it equals the reference walk over the entry's segments,
starting from the originating model with no field resolved yet. No output
component is left free — the flag is determined by the segments and the model
machinery. -/
def problem_spec_orderingFieldCheck {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (start : Model) (parts : List String) (result : Bool) : Prop :=
  result =
    walkReported getField isRelation descend hasTransform hasLookup
      none (some start) parts
-- post-conditions-end

-- impl-start
def implementation_orderingFieldCheck {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (start : Model) (parts : List String) : Bool := Id.run do
  -- Walk the entry segment by segment from the originating model, tracking the
  -- last resolved field and the current (possibly exhausted) model context.
  let mut fld : Option Field := none
  let mut ctx : Option Model := some start
  let mut err : Bool := false
  for part in parts do
    match ctx with
    | some m =>
      match getField m part with
      | some f =>
        -- Resolved: descend into the related model if this field is a relation,
        -- otherwise the context is exhausted.
        fld := some f
        ctx := if isRelation f then some (descend f) else none
      | none =>
        -- Unresolved: report unless the segment is a transform or a registered
        -- lookup of the preceding resolved field.
        if reportSegment hasTransform hasLookup fld part then
          err := true
    | none =>
      -- Context exhausted: same report decision against the preceding field.
      if reportSegment hasTransform hasLookup fld part then
        err := true
  return err
-- impl-end


-- proof-start
/-- Pure reification of one loop-body iteration on state `(fld, ctx, err)` for a
given `part`, matching the imperative body of `implementation_orderingFieldCheck`.
The unresolved / exhausted branches use `err || reportSegment …` so the step is
provably equal to the imperative `if reportSegment then err := true`. -/
def step {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (s : Option Field × Option Model × Bool) (part : String) :
    Option Field × Option Model × Bool :=
  let (fld, ctx, err) := s
  match ctx with
  | some m =>
    match getField m part with
    | some f => (some f, (if isRelation f then some (descend f) else none), err)
    | none => (fld, ctx, err || reportSegment hasTransform hasLookup fld part)
  | none => (fld, none, err || reportSegment hasTransform hasLookup fld part)
/-- The desugared body of one imperative loop iteration, operating on the loop's
own packed state `(ctx, err, fld)` (the order of the `mut` variables). The
unresolved / exhausted branches write `err || reportSegment …`, matching the
imperative `if reportSegment then err := true`. Note the component order differs
from `step`, which uses `(fld, ctx, err)`. -/
def loopBodyOrderingFieldCheck {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (s : Option Model × Bool × Option Field) (part : String) :
    Option Model × Bool × Option Field :=
  let (ctx, err, fld) := s
  match ctx with
  | some m =>
    match getField m part with
    | some f => (if isRelation f then some (descend f) else none, err, some f)
    | none => (ctx, err || reportSegment hasTransform hasLookup fld part, fld)
  | none => (none, err || reportSegment hasTransform hasLookup fld part, fld)

/-- The boolean value written by `if reportSegment … then err := true` equals
`err || reportSegment …`: for booleans, `(if b then true else err) = (err || b)`. -/
theorem if_report_eq_or_orderingFieldCheck (err b : Bool) :
    (if b = true then true else err) = (err || b) := by
  cases b <;> cases err <;> rfl

/-- Desugar the monadic `Id.run do` for-loop into a `List.foldl` of the explicit
loop body over the packed state `(ctx, err, fld)`, reading off the `err`
component (`.2.1`). -/
theorem impl_eq_foldl_loopBody_orderingFieldCheck {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (start : Model) (parts : List String) :
    implementation_orderingFieldCheck getField isRelation descend hasTransform hasLookup
        start parts
      = (List.foldl (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup)
          (some start, false, none) parts).2.1 := by
  -- Generalized loop lemma matching the implementation's exact `let mut fld/ctx/err`
  -- declaration order, so its desugared `Id.run do for` is defeq to the goal's `forIn`.
  -- Proved by induction on `parts`; the concrete run uses `fld = none, ctx = some start`.
  suffices key : ∀ (fld : Option Field) (ctx : Option Model) (err : Bool),
      (Id.run do
        let mut fld' := fld
        let mut ctx' := ctx
        let mut err' := err
        for part in parts do
          match ctx' with
          | some m =>
            match getField m part with
            | some f =>
              fld' := some f
              ctx' := if isRelation f then some (descend f) else none
            | none =>
              if reportSegment hasTransform hasLookup fld' part then
                err' := true
          | none =>
            if reportSegment hasTransform hasLookup fld' part then
              err' := true
        return err')
        = (List.foldl (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup)
            (ctx, err, fld) parts).2.1 by
    simpa only [implementation_orderingFieldCheck] using key none (some start) false
  intro fld ctx err
  induction parts generalizing fld ctx err with
  | nil => rfl
  | cons part rest ih =>
    simp only [List.foldl_cons, loopBodyOrderingFieldCheck, Id.run, bind, pure, List.forIn_cons]
    cases ctx with
    | none =>
      by_cases hb : reportSegment hasTransform hasLookup fld part = true <;>
        simp only [hb, if_true, Bool.or_true, Bool.or_false] <;>
        exact ih _ _ _
    | some m =>
      cases hg : getField m part with
      | none =>
        by_cases hb : reportSegment hasTransform hasLookup fld part = true <;>
          simp only [hg, hb, if_true, Bool.or_true, Bool.or_false] <;>
          exact ih _ _ _
      | some f =>
        simp only [hg]
        exact ih _ _ _

/-- Fold-level correspondence between the loop body and `step` across the
coordinate permutation `(ctx, err, fld) ↔ (fld, ctx, err)`: folding the loop body
from `s` and reading `err` (`.2.1`) equals folding `step` from the permuted state
`(s.2.2, s.1, s.2.1)` and reading `.2.2`. Proved by induction on `parts`,
generalizing the accumulator `s`. -/
theorem foldl_loopBody_eq_step_orderingFieldCheck {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (parts : List String) (s : Option Model × Bool × Option Field) :
    (List.foldl (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup)
        s parts).2.1
      = (List.foldl (step getField isRelation descend hasTransform hasLookup)
          (s.2.2, s.1, s.2.1) parts).2.2 := by
  induction parts generalizing s with
  | nil => rfl
  | cons part rest ih =>
    rw [List.foldl_cons, List.foldl_cons, ih]
    have hstep :
        ((loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup s part).2.2,
            (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup s part).1,
            (loopBodyOrderingFieldCheck getField isRelation descend hasTransform hasLookup s part).2.1)
          = step getField isRelation descend hasTransform hasLookup (s.2.2, s.1, s.2.1) part := by
      obtain ⟨ctx, err, fld⟩ := s
      simp only [loopBodyOrderingFieldCheck, step]
      split <;> (try split) <;> rfl
    rw [hstep]

/-- Desugar the monadic implementation into a pure left fold of `step`. -/
theorem loop_is_foldl {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (start : Model) (parts : List String) :
    implementation_orderingFieldCheck getField isRelation descend hasTransform hasLookup
        start parts
      = (List.foldl (step getField isRelation descend hasTransform hasLookup)
          (none, some start, false) parts).2.2 := by
  rw [impl_eq_foldl_loopBody_orderingFieldCheck]
  exact foldl_loopBody_eq_step_orderingFieldCheck getField isRelation descend
    hasTransform hasLookup parts (some start, false, none)

/-- Generalized loop invariant: folding `step` from an ARBITRARY state
`(fld, ctx, err)` yields `err || walkReported … fld ctx parts`. -/
theorem foldl_step_eq_walk {Model Field : Type}
    (getField : Model → String → Option Field)
    (isRelation : Field → Bool) (descend : Field → Model)
    (hasTransform hasLookup : Field → String → Bool)
    (parts : List String) (fld : Option Field) (ctx : Option Model) (err : Bool) :
    (List.foldl (step getField isRelation descend hasTransform hasLookup)
        (fld, ctx, err) parts).2.2
      = (err ||
          walkReported getField isRelation descend hasTransform hasLookup
            fld ctx parts) := by
  induction parts generalizing fld ctx err with
  | nil => simp [walkReported]
  | cons part rest ih =>
    rw [List.foldl_cons]
    cases ctx with
    | none =>
      show (List.foldl (step getField isRelation descend hasTransform hasLookup)
          (fld, none, err || reportSegment hasTransform hasLookup fld part) rest).2.2 = _
      rw [ih]
      conv_rhs => rw [walkReported]
      simp [Bool.or_assoc]
    | some m =>
      cases hf : getField m part with
      | none =>
        rw [show step getField isRelation descend hasTransform hasLookup (fld, some m, err) part
            = (fld, some m, err || reportSegment hasTransform hasLookup fld part) by
          simp only [step, hf]]
        rw [ih]
        conv_rhs => rw [walkReported]
        rw [hf]
        simp [Bool.or_assoc]
      | some f =>
        rw [show step getField isRelation descend hasTransform hasLookup (fld, some m, err) part
            = (some f, (if isRelation f then some (descend f) else none), err) by
          simp only [step, hf]]
        rw [ih]
        conv_rhs => rw [walkReported]
        rw [hf]

theorem correct_orderingFieldCheck :
    ∀ {Model Field : Type}
      (getField : Model → String → Option Field)
      (isRelation : Field → Bool) (descend : Field → Model)
      (hasTransform hasLookup : Field → String → Bool)
      (start : Model) (parts : List String),
      problem_spec_orderingFieldCheck getField isRelation descend hasTransform hasLookup
          start parts
        (implementation_orderingFieldCheck getField isRelation descend hasTransform hasLookup
          start parts) := by
  intro Model Field getField isRelation descend hasTransform hasLookup start parts
  unfold problem_spec_orderingFieldCheck
  rw [loop_is_foldl getField isRelation descend hasTransform hasLookup start parts,
      foldl_step_eq_walk getField isRelation descend hasTransform hasLookup parts
        none (some start) false, Bool.false_or]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

spec_view elides BOTH impl and proof regions, so same_spec only pins axioms/pure/post regions; all 8 attacks confirmed same_spec=True. The postcondition problem_spec_orderingFieldCheck is EXACT functional equality result = walkReported(...) over universally-quantified machinery params -- the strongest possible spec.

### ATTACKS (cmd: bash scripts/lean_verify.sh <file>; 0=verifies,1=error,3=sorry):
- pos_control (gold impl): exit 0. #print axioms => [propext, Quot.sound] (clean). POSITIVE CONTROL PASS.
- atk1_prepatch (prepatch bug, transform-only report; hasLookup dropped): exit 1. Does NOT close (gold proof fails on buggy impl). PREPATCH REPRODUCED.
- atk2_alwaysfalse (ungrounded const `return false`): exit 1. Does NOT close.
- atk3_alwaystrue (ungrounded const `return true`): exit 1. Does NOT close.
- atk4_lookuponly (symmetric bug, lookup-only report; hasTransform dropped): exit 1. Does NOT close.
- atk5_partial (partial-domain: spare ALL segments with a preceding resolved field): exit 1. Does NOT close.
- atk6_nodescend (control-flow-effect: never descend, ctx:=none after resolve): exit 1. Does NOT close.
- atk7_echo (ungrounded-oracle echo: `return walkReported getField isRelation descend hasTransform hasLookup none (some start) parts`, proof by rfl): exit 0, #print axioms => 'does not depend on any axioms' (clean). This is the ONLY closing attack -- but it is EXTENSIONALLY the post-patch behavior (literally the spec function), i.e. a correct impl, not a wrong one. Its faithful refined patch = the post-patch report condition = gold patch. run_resolve('django__django-12858', patch, retries=1) => ResolveResult(resolved=True, completed=True, attempts=1, flaky=False); FAIL_TO_PASS test_ordering_pointing_to_lookup_not_transform SUCCESS, all 73 PASS_TO_PASS success. RESOLVES => not a break.
- atk8_boundary (boundary: report only on ctx-exhausted branch, skip getField=none unresolved): exit 1. Does NOT close.

MANDATORY resolve step: the only clean-axiom-closing impl (atk7_echo) had its faithful patch materialized and run through the official harness (run_resolve) => RESOLVED. No closing wrong impl exists whose patch fails to resolve, so verify does NOT imply not-correct here.

refinement.md / mapping.md AUDIT: grep of Solution.lean shows NO opaque/axiom declarations; meta.json axioms=[]. Every leg is R / A-reference / I -- no kind-3. The five machinery ops (getField=get_field, isRelation=is_relation, descend=get_path_info()[-1].to_opts.model, hasTransform=get_transform is not None, hasLookup=get_lookup is not None) are universally-quantified A-reference parameters correctly bound to the REAL Python callees (validated by G-CONF binding); the postcondition consumes NO property of any of them, so the absence of an A-consumed leg is correct. Correspondence holds.

VERDICT: SOUND. >=5 distinct wrong-impl attacks (prepatch, always-false, always-true, symmetric-lookup, partial-domain, no-descend, boundary = 7 genuinely-wrong) all FAIL to close; the single closing impl is a correct echo whose materialized patch RESOLVES. Spec is exact-functional-equality and admits no verifying-but-nonresolving twin.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-12858 (lean). Spec models the E015-report decision of the relation-spanning walk in Model._check_ordering; gold patch widens the unresolved-segment report condition from `fld is None or get_transform(part) is None` to `fld is None or (get_transform(part) is None and get_lookup(part) is None)`.

### Checks
1. Solution.lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry/error).
2. `#print axioms correct_orderingFieldCheck` => [propext, Quot.sound] only. No sorryAx; proof is genuine.
3. same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) => True. Spec region (reportSegment/walkReported/problem_spec_orderingFieldCheck) is byte-identical; prepatch differs only in impl body (omits hasLookup disjunct) and carries the intentional sorry.
4. reportSegment encodes the POST-patch condition: report unless part is a transform OR a registered lookup of the preceding resolved field. Correct target.

DIFFERENTIAL vs REAL patched callee (independent, harsher than bundled harness): built a synthetic graph with forward FKs, self-FK, reverse relations, registered transform (Lower) and builtin lookups; ran ~600k relation-spanning entries (seeds 999/4242, chains len 2-6, exhaustive 2-segment cross product over 26 segment names) over Product/Supply/Stock starts against REAL Model._check_ordering at the patched worktree.
  - Strict, Lean-faithful transliteration (Bool.or over already-evaluated values, matching total `walkReported`): 0 divergences of ANY kind across 452k cross-checks, INCLUDING crash-matching (both raise identical exception type where the real callee crashes on a reverse-relation fld).
  - Bundled conformance_check.py: 120k entries, 0 disagreements.
  - Discriminating cases all agree: title__isnull->False, title__lower->False, supply__product__parent__isnull->False (the issue path), title__nonexistent->True, supply__bogus->True, supply__product__name__exact->False.

ARTIFACT NOTE: a naive short-circuit-`or` Python transliteration showed 20,949 apparent 'divergences', all of form real=AttributeError vs spec=True. These are NOT real: Python `report(...) or walk(...)` skipped a later get_transform on a reverse-relation object that crashes; Lean `||` operates on already-computed Bool values and walkReported is total, so no crash-avoidance exists. Under a strict transliteration these vanish entirely, and the impl-shadow crash-matches the oracle on exactly those inputs (documented pre-existing latent crash present identically pre/post-patch, orthogonal to the E015 fix).

CONCLUSION: On every input where the real callee returns a value, the modeled function returns the same value. Spec is neither too strong nor drifted. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified, not rubber-stamped. Mechanical: leakage.screen(Solution, LeanBackend, gold_patch, problem_statement) -> passed=True, no hard failures. same_spec(Solution, Solution_prepatch)=True (spec regions byte-identical, so the frozen spec view is authentic). lean_verify.sh Solution.lean -> EXIT 0 (compiles, no sorry).

Spec view (impl+proof elided) discloses ONLY behavior already public in problem_statement, which states verbatim 'models.E015 is raised when ordering uses lookups that are not transforms' and shows order_by('supply__product__parent__isnull') working. That publicly specifies the target: a registered-lookup segment (isnull) must be accepted, not reported — exactly what reportSegment encodes. hints_text is empty and was not used. Encoding target behavior is the legitimate role of a spec.

Semantic check beyond the lexical screen:
- No gold-diff line reproduced; no diff markers.
- Patched file path django/db/models/base.py and its module path do NOT appear in the view.
- Patch-changed symbol is 'check_ordering' (from _check_ordering); it is not in problem_statement, but it is NOT embedded in any spec-view identifier (orderingFieldCheck/walkReported/reportSegment do not contain the substring 'check_ordering') and is NOT named in any spec-view comment/docstring. Machinery stays abstract (hasTransform/hasLookup), never the Python get_transform/get_lookup.
- No bug/fix/patch narration in comments.
- Notably the spec presents transform and lookup SYMMETRICALLY (accept if transform OR registered lookup), so it does not even betray which conjunct the gold diff added; it reveals no more than the public statement.

The gold-edit mechanics (file, changed line, the 'and fld.get_lookup(part) is None' diff form, patched symbol name) are not recoverable from the spec view beyond what problem_statement already makes public. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
