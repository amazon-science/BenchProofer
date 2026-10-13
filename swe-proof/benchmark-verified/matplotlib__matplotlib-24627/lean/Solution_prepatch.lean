import Mathlib
-- imports-end

/-!
Model of the behavior of clearing a plotting axes.

Public behavior (from the issue): when an axes is cleared, its list of child
artists is emptied, AND every former child artist is *deparented* — its owning
`axes` and owning `figure` references are unset (set to "none"). Removing an
artist individually already deparents it; clearing must do the same for every
child it drops. Any other state carried by an artist is left untouched.

We model an artist as a record carrying opaque payload `data` (all state the
clear operation must NOT touch), plus its owning-`axes` and owning-`figure`
references as `Option` identities (`none` ⇒ deparented).
-/

-- axioms-start
-- No unchanged outside callee is consumed: the modeled behavior is a pure
-- list/record transformation, so there is no `opaque` callee and no `_prop`
-- axiom. (G-AX is a skip stub for this instance.)
-- axioms-end

-- pure-start
/-- An artist owned by an axes/figure. `data` stands for every other field the
clear operation must preserve; `axes`/`figure` are the owning references that
clearing unsets (`none` ⇒ deparented). -/
structure Artist where
  data : Nat
  axes : Option Nat
  figure : Option Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Clearing returns the pair `(newChildren, formerChildren)`:
* `newChildren` (`result.1`) is the axes' fresh child list — empty;
* `formerChildren` (`result.2`) are the artists that were children, each now
  deparented.

The contract pins, in order: the new child list is empty; the former-children
list has the same length (and positional correspondence) as the input; and for
each position the former child has its owning `axes` and `figure` unset to
`none` while every other field (`data`) is preserved (frame discipline). -/
def problem_spec_clearAxes (artists : List Artist)
    (result : List Artist × List Artist) : Prop :=
  result.1 = [] ∧
  result.2.length = artists.length ∧
  ∀ i, i < artists.length →
    ∃ a c, result.2[i]? = some a ∧ artists[i]? = some c ∧
      a.axes = none ∧ a.figure = none ∧ a.data = c.data
-- post-conditions-end

-- impl-start
def implementation_clearAxes (artists : List Artist)
    : List Artist × List Artist := Id.run do
  -- Pre-patch bug: clearing only resets the child list to empty; the former
  -- children are returned untouched, so their owning `axes`/`figure` references
  -- are NOT unset (they remain parented to a cleared axes).
  let oldChildren := artists
  let newChildren : List Artist := []
  return (newChildren, oldChildren)
-- impl-end

-- proof-start
theorem correct_clearAxes : ∀ artists,
    problem_spec_clearAxes artists (implementation_clearAxes artists) := by
  sorry
-- proof-end
