import Mathlib
-- imports-end

/-!
Adding a value to a vector.

A vector is carried by its list of basis-weighted components (its *argument
list*). The sum of a vector with some other value is defined by cases on that
value:

* adding another vector appends the two component lists (the combined list is
  what is handed to the vector constructor downstream);
* adding the additive identity — the scalar zero — leaves the vector unchanged,
  yielding the vector's own component list;
* adding anything else is rejected as a type error.

In particular, the additive identity is a valid right operand: summing a vector
with zero must SUCCEED and return the original vector unchanged — it must not be
treated as an invalid operand and rejected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The operand
-- classification (another vector / the additive identity / anything else) and
-- the resulting component list are modeled structurally over the observable
-- shape of the operand, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The right-hand operand of a vector addition, classified by its shape.

* `vector args` — another vector, carried by its component (argument) list;
* `scalarZero`  — the scalar zero (the additive identity);
* `nonVector`   — any other value, which is not a valid addend. -/
inductive AddOperand where
  | vector (args : List Int)
  | scalarZero
  | nonVector
deriving DecidableEq, Repr

/-- Whether an operand is equal to the additive identity. The scalar zero is the
identity; so is a vector carrying no components (an empty component list), since
it represents the zero vector. -/
def isAdditiveZero : AddOperand → Bool
  | .scalarZero => true
  | .vector []  => true
  | _           => false
-- pure-end

-- post-conditions-start
/-- The result of adding `other` to a vector with component list `selfArgs`.

The result is the component list handed to the vector constructor, or a type
error (`Except.error`) when the operand is not a valid addend:

* another vector contributes its components, appended after `selfArgs`;
* the additive identity (the scalar zero) leaves the vector unchanged, so the
  result is exactly `selfArgs`;
* any other value is rejected as a type error. -/
def problem_spec_vectorAdd
    (selfArgs : List Int) (other : AddOperand)
    (result : Except Unit (List Int)) : Prop :=
  match other with
  | .vector otherArgs => result = Except.ok (selfArgs ++ otherArgs)
  | .scalarZero       => result = Except.ok selfArgs
  | .nonVector        => result = Except.error ()
-- post-conditions-end

-- impl-start
def implementation_vectorAdd
    (selfArgs : List Int) (other : AddOperand) : Except Unit (List Int) :=
  Id.run do
    if isAdditiveZero other then
      return Except.ok selfArgs
    match other with
    | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
    | _                 => return Except.error ()
-- impl-end

-- proof-start
theorem correct_vectorAdd :
    ∀ (selfArgs : List Int) (other : AddOperand),
      problem_spec_vectorAdd selfArgs other
        (implementation_vectorAdd selfArgs other) := by
  intro selfArgs other
  unfold problem_spec_vectorAdd implementation_vectorAdd
  cases other with
  | vector otherArgs =>
    cases otherArgs with
    | nil =>
      simp only [isAdditiveZero, Id.run, if_true, List.append_nil, pure]
    | cons a as => rfl
  | scalarZero => rfl
  | nonVector => rfl
-- proof-end
