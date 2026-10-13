import Mathlib
-- imports-end

/-!
Deciding, for a single item in a collection, whether an optional "remove me"
control should be attached to that item.

The collection has two configuration booleans:

  * whether removal is permitted at all, and
  * whether items beyond the pre-populated prefix may also be removed.

Each item is identified by an OPTIONAL position. Some items have a concrete
position (a natural-number offset); others are positionless (a standalone
template item that does not occupy a slot in the collection). The collection also
knows how many leading items are pre-populated.

The removal control is attached exactly when removal is permitted AND either
extra (non-pre-populated) items may be removed too, OR the item sits inside the
pre-populated prefix — i.e. it has a concrete position strictly below the
pre-populated count. A positionless item is, by definition, not inside that
prefix.

The decision is TOTAL: it is defined for every item, including a positionless
one, and never fails to produce an answer.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The decision is a pure
-- boolean computation over the two configuration booleans, the item's optional
-- position, and the pre-populated count; the downstream act of materializing the
-- control object is abstracted to the boolean "was the control attached". Hence
-- no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- An item is inside the pre-populated prefix iff it has a concrete position
strictly below the pre-populated count. A positionless item is never inside it. -/
def withinInitial (index : Option Nat) (ifc : Nat) : Bool :=
  match index with
  | some i => decide (i < ifc)
  | none   => false
-- pure-end

-- post-conditions-start
/-- The outcome is TOTAL and fully pinned to the inputs.

  * `result = some b` always (the decision never fails to produce an answer — in
    particular it is defined for a positionless item); there is no `none` outcome.
  * `b` is true exactly when removal is permitted AND either extra items may be
    removed, OR the item is inside the pre-populated prefix (`withinInitial`).

No output component is left free: the outcome is `some` of the exact boolean
combination of the inputs. -/
def problem_spec_addFields
    (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat)
    (result : Option Bool) : Prop :=
  result = some (canDelete && (canDeleteExtra || withinInitial index ifc))
-- post-conditions-end

-- impl-start
def implementation_addFields
    (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat) :
    Option Bool := Id.run do
  let mut addControl := false
  if canDelete then
    if canDeleteExtra then
      addControl := true
    else
      -- The within-prefix test only makes sense for an item that has a concrete
      -- position; a positionless item is treated as outside the prefix.
      match index with
      | some i => if i < ifc then addControl := true
      | none   => pure ()
  return some addControl
-- impl-end

-- proof-start
theorem correct_addFields :
    ∀ (canDelete canDeleteExtra : Bool) (index : Option Nat) (ifc : Nat),
      problem_spec_addFields canDelete canDeleteExtra index ifc
        (implementation_addFields canDelete canDeleteExtra index ifc) := by
  intro canDelete canDeleteExtra index ifc
  unfold problem_spec_addFields implementation_addFields withinInitial
  cases canDelete <;> cases canDeleteExtra <;> cases index <;>
    first
      | rfl
      | (rename_i val; by_cases h : val < ifc <;>
          simp only [Id.run, h, if_true, if_false, decide_true, decide_false,
            pure] <;> rfl)
-- proof-end
