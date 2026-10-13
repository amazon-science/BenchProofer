import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Producing the elements of an
-- ordered collection in reverse of their existing order is the changed operation;
-- it is modeled deeply as an order-reversal over the element sequence (an
-- accumulator fold), not abstracted behind a callee. The proof agent may add
-- `_prop` axioms only if it gets genuinely stuck.
-- axioms-end

-- pure-start
-- (no auxiliary pure helpers needed; the spec is a direct order relation)
-- pure-end

-- post-conditions-start
/-- The reverse enumeration of an ordered collection. Given the collection's
elements in their existing order (`xs`), the produced sequence lists exactly the
same elements in the opposite order: the last element first and the first element
last. The result is fully determined by the input order — it is its reversal. -/
def problem_spec_reversed (xs : List Int) (result : List Int) : Prop :=
  result = xs.reverse
-- post-conditions-end

-- impl-start
/-- Pre-patch (buggy): the collection does not expose a reverse enumeration, so
iterating it yields the elements in their existing forward order — the requested
reversal never happens. We walk the elements and append each to the end of an
accumulator, so the produced sequence keeps the original order. -/
def implementation_reversed (xs : List Int) : List Int := Id.run do
  let mut acc : List Int := []
  for x in xs do
    acc := acc ++ [x]
  return acc
-- impl-end

-- proof-start
theorem correct_reversed :
    ∀ (xs : List Int),
    problem_spec_reversed xs (implementation_reversed xs) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
