import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behavior under specification is the construction
--  of a string field type's validator list during initialization. The decision
--  it makes — whether to register a length-bound check — depends only on whether
--  a length bound is configured, an input carried directly in the model. The
--  validators already present are carried opaquely and never inspected, so no
--  unchanged callee's contract is consumed; there is nothing to validate against
--  a real callee.)
-- axioms-end

-- pure-start
/- A validator entry of a field. `lengthBound lim` is a length-bound check whose
   configured bound is `lim` (an optional integer: `none` when the field carries
   no length bound). `existing j` is an opaque pre-existing validator, tagged by
   an index so distinct entries stay distinct; its internal nature is irrelevant
   to the behavior modeled here. -/
inductive Validator where
  | existing : Nat → Validator
  | lengthBound : Option Int → Validator
  deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Initializing a string field type assembles its list of validators. A
   length-bound check is registered among them ONLY when the field actually
   carries a length bound; when no length bound is configured the validator list
   is left exactly as it was, with no length-bound check added.

   `priorValidators` is the read-only list of validators already established for
   the field (not `mut`): initialization appends to a fresh result and never
   rewrites the prior list (directive 5). `lengthBound` is the field's optional
   length bound, read-only (`none` = no bound configured). The post-state pins
   the result exactly in both configurations: with no bound the result equals the
   prior list verbatim; with a bound `b` the result is the prior list followed by
   a single length-bound check whose configured bound is `b`. -/
method configureValidators (priorValidators : List Validator) (lengthBound : Option Int)
    return (out : List Validator)
  ensures lengthBound = none → out = priorValidators
  ensures lengthBound.isSome = true →
            out = priorValidators ++ [Validator.lengthBound lengthBound]
  do
    -- impl-start
    -- Register a length-bound check only when a length bound is configured;
    -- otherwise leave the established validator list untouched.
    let result : List Validator :=
      if lengthBound.isSome then
        priorValidators ++ [Validator.lengthBound lengthBound]
      else
        priorValidators
    return result
    -- impl-end

prove_correct configureValidators by
  loom_solve
