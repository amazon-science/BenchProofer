import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The two affected
-- procedures branch on (a) a looked-up documentation comment for the object and
-- (b) the rendered description of an alias target; both are supplied to the
-- modeled decision logic as abstract inputs (their values come from the
-- caller/environment), while the decision logic itself is modeled DEEPLY below.
-- The proof agent may add `_prop` axioms only if a proof obligation needs one.
-- axioms-end

-- pure-start
/-- A looked-up documentation comment for a name is "present" exactly when the
lookup succeeded and produced at least one line. A failed lookup (`none`) and a
successful-but-empty lookup (`some []`) both count as absent — this mirrors the
truthiness test applied to such a value in the reference language. -/
def commentPresent (comment : Option (List String)) : Bool :=
  match comment with
  | some (_ :: _) => true
  | _             => false
-- pure-end

-- post-conditions-start
/-- Specification of the documentation-block selection for a documented object.

`docAsAttr` indicates the object is being documented as an alias rather than in
its own right. `comment` is the looked-up documentation comment for the object
(a failed lookup is `none`). `normalDoc` is the documentation block produced by
the ordinary path taken when the object is documented in its own right.

When the object is documented as an alias, the result is an empty block
(`some []`) when a documentation comment is present, and "no documentation"
(`none`) when it is absent. When the object is documented in its own right, the
result is exactly the ordinary block. -/
def problem_spec_getDoc (docAsAttr : Bool) (comment : Option (List String))
    (normalDoc : Option (List (List String)))
    (result : Option (List (List String))) : Prop :=
  (docAsAttr = true →
      (commentPresent comment = true  → result = some []) ∧
      (commentPresent comment = false → result = none)) ∧
  (docAsAttr = false → result = normalDoc)
-- post-conditions-end

-- impl-start
def implementation_getDoc (docAsAttr : Bool) (comment : Option (List String))
    (normalDoc : Option (List (List String))) :
    Option (List (List String)) := Id.run do
  if docAsAttr then
    if commentPresent comment then
      return some []
    else
      return none
  return normalDoc
-- impl-end

-- proof-start
theorem correct_getDoc : ∀ (docAsAttr : Bool) (comment : Option (List String))
    (normalDoc : Option (List (List String))),
    problem_spec_getDoc docAsAttr comment normalDoc
      (implementation_getDoc docAsAttr comment normalDoc) := by
  intro docAsAttr comment normalDoc
  unfold problem_spec_getDoc implementation_getDoc
  refine ⟨fun hattr => ⟨fun hc => ?_, fun hc => ?_⟩, fun hattr => ?_⟩
  · simp only [Id.run, hattr, hc, if_true]; rfl
  · simp only [Id.run, hattr, hc, if_true, Bool.false_eq_true, if_false]; rfl
  · simp only [Id.run, hattr, Bool.false_eq_true, if_false]; rfl
-- proof-end

-- post-conditions-start
/-- Specification of the supplementary content forwarded for a documented object.

`docAsAttr` indicates the object is being documented as an alias. `comment` is
the looked-up documentation comment for the object. `aliasText` is the rendered
description of the alias target. `incoming` is the supplementary content already
supplied by the caller.

When the object is documented as an alias AND no documentation comment is
present, the forwarded content is a single line describing the alias target.
Otherwise the forwarded content is exactly the caller-supplied content,
unchanged. -/
def problem_spec_addContent (docAsAttr : Bool) (comment : Option (List String))
    (aliasText : String) (incoming : Option (List String))
    (result : Option (List String)) : Prop :=
  (docAsAttr = true ∧ commentPresent comment = false →
      result = some ["alias of " ++ aliasText]) ∧
  ((docAsAttr = false ∨ commentPresent comment = true) →
      result = incoming)
-- post-conditions-end

-- impl-start
def implementation_addContent (docAsAttr : Bool) (comment : Option (List String))
    (aliasText : String) (incoming : Option (List String)) :
    Option (List String) := Id.run do
  if docAsAttr && (! commentPresent comment) then
    return some ["alias of " ++ aliasText]
  return incoming
-- impl-end

-- proof-start
theorem correct_addContent : ∀ (docAsAttr : Bool) (comment : Option (List String))
    (aliasText : String) (incoming : Option (List String)),
    problem_spec_addContent docAsAttr comment aliasText incoming
      (implementation_addContent docAsAttr comment aliasText incoming) := by
  intro docAsAttr comment aliasText incoming
  unfold problem_spec_addContent implementation_addContent
  refine ⟨fun h => ?_, fun h => ?_⟩
  · obtain ⟨h1, h2⟩ := h
    simp only [Id.run, h1, h2, Bool.not_false, Bool.and_true, if_true]; rfl
  · rcases h with h | h
    · simp only [Id.run, h, Bool.false_and, Bool.false_eq_true, if_false]; rfl
    · simp only [Id.run, h, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]; rfl
-- proof-end
