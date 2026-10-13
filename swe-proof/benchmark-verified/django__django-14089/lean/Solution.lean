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
/-- Enumerate the ordered collection's elements in reverse of their existing
order. We walk the elements in their current order and prepend each onto an
accumulator, so the element seen last ends up at the front. -/
def implementation_reversed (xs : List Int) : List Int := Id.run do
  let mut acc : List Int := []
  for x in xs do
    acc := x :: acc
  return acc
-- impl-end

-- proof-start
theorem correct_reversed :
    ∀ (xs : List Int),
    problem_spec_reversed xs (implementation_reversed xs) := by
  intro xs
  unfold problem_spec_reversed implementation_reversed
  have helper : ∀ (ys : List Int) (init : List Int),
      Id.run (forIn ys init
        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))
        = ys.reverse ++ init := by
    intro ys
    induction ys with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
      simp [List.reverse_cons]
  show Id.run (forIn xs [] _) = xs.reverse
  rw [helper xs []]
  simp
-- proof-end
