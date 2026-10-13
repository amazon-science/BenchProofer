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
        -- Unresolved: report unless the segment is a transform of the preceding
        -- resolved field. (A registered lookup of that field is NOT taken into
        -- account, so a lookup-only segment is reported here.)
        let report : Bool := match fld with
          | none => true
          | some f => !hasTransform f part
        if report then
          err := true
    | none =>
      -- Context exhausted: same report decision against the preceding field.
      let report : Bool := match fld with
        | none => true
        | some f => !hasTransform f part
      if report then
        err := true
  return err
-- impl-end

-- proof-start
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
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
