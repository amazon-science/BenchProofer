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
