import Mathlib
-- imports-end

-- axioms-start
-- No callee needs an opaque signature here. The system check that validates a
-- user model accumulates a list of diagnostics from several independent
-- sub-checks; the outcomes of the structural sub-checks (the
-- required-fields-shape check, the required-fields-membership check, the chosen
-- authentication backend, and the two anonymous/authenticated attribute checks)
-- are taken as boolean inputs (a type-only refinement, refinement.md). The
-- decision of whether the login field is guaranteed unique is modeled DEEPLY
-- below over the declared model constraints, so no callee property is consumed.
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The information about one declared model constraint that the login-field
uniqueness decision inspects: whether it is a uniqueness constraint, whether it
is conditional (applies only to a subset of rows), and the ordered tuple of
field names it ranges over. -/
structure ConstraintInfo where
  isUnique : Bool
  isConditional : Bool
  fields : List String
deriving DecidableEq

/-- The login field counts as guaranteed unique by a declared constraint when
some unconditional uniqueness constraint ranges over exactly that one field. A
conditional (partial) constraint, a non-uniqueness constraint, or a constraint
spanning a different set of fields does not count. -/
def coveredByUnconditionalUniqueConstraint
    (constraints : List ConstraintInfo) (field : String) : Bool :=
  constraints.any (fun c => c.isUnique && !c.isConditional && c.fields == [field])
-- pure-end

-- post-conditions-start
/-- The diagnostics produced when validating a user model, each represented by
its stable identifier code. The list is the in-order accumulation of the
independent sub-checks: a required-fields-shape diagnostic, a
required-fields-membership diagnostic, then — only when the login field is
neither directly unique nor guaranteed unique by a declared unconditional
uniqueness constraint over exactly that field — a uniqueness diagnostic whose
severity depends on whether the default authentication backend is in use (an
error there, otherwise a warning), and finally the two
anonymous/authenticated-attribute diagnostics. Each unchanged sub-check pins its
contribution to its input, and the login-field branch is grounded in the
declared constraints. -/
def problem_spec_checkUserModel
    (usernameField : String)
    (reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
      isAnonymousMethod isAuthenticatedMethod : Bool)
    (constraints : List ConstraintInfo)
    (result : List String) : Prop :=
  result =
    (if reqFieldsBadShape then ["auth.E001"] else []) ++
    (if usernameInRequired then ["auth.E002"] else []) ++
    (if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
      (if usesDefaultBackend then ["auth.E003"] else ["auth.W004"]) else []) ++
    (if isAnonymousMethod then ["auth.C009"] else []) ++
    (if isAuthenticatedMethod then ["auth.C010"] else [])
-- post-conditions-end

-- impl-start
def implementation_checkUserModel
    (usernameField : String)
    (reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
      isAnonymousMethod isAuthenticatedMethod : Bool)
    (constraints : List ConstraintInfo) : List String :=
  Id.run do
    let mut errors : List String := []
    if reqFieldsBadShape then
      errors := errors ++ ["auth.E001"]
    if usernameInRequired then
      errors := errors ++ ["auth.E002"]
    -- Pre-patch (buggy): the uniqueness diagnostic fires whenever the field is
    -- not directly unique, IGNORING any declared unconditional uniqueness
    -- constraint that already guarantees uniqueness over that field.
    if !fieldUnique then
      if usesDefaultBackend then
        errors := errors ++ ["auth.E003"]
      else
        errors := errors ++ ["auth.W004"]
    if isAnonymousMethod then
      errors := errors ++ ["auth.C009"]
    if isAuthenticatedMethod then
      errors := errors ++ ["auth.C010"]
    return errors
-- impl-end

-- proof-start
theorem correct_checkUserModel :
    ∀ (usernameField : String)
      (reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
        isAnonymousMethod isAuthenticatedMethod : Bool)
      (constraints : List ConstraintInfo),
    problem_spec_checkUserModel usernameField reqFieldsBadShape usernameInRequired
      fieldUnique usesDefaultBackend isAnonymousMethod isAuthenticatedMethod constraints
      (implementation_checkUserModel usernameField reqFieldsBadShape usernameInRequired
        fieldUnique usesDefaultBackend isAnonymousMethod isAuthenticatedMethod constraints) := by
  intro usernameField reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
    isAnonymousMethod isAuthenticatedMethod constraints
  unfold problem_spec_checkUserModel implementation_checkUserModel
  simp only [Id.run]
  -- carries the gold proof shape; UNCLOSABLE against the buggy impl because the
  -- uniqueness branch drops the `coveredByUnconditionalUniqueConstraint` guard
  -- (G-DIFF). A model with an unconditional unique constraint over the login
  -- field discriminates: spec says no diagnostic, buggy impl emits one.
  rfl
-- proof-end
