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
  -- mirror `old_children, self._children = self._children, []`
  let oldChildren := artists
  let mut newChildren : List Artist := []
  -- mirror `for chld in old_children: chld.axes = chld.figure = None`
  let mut formerChildren : List Artist := []
  for chld in oldChildren do
    let chld := { chld with axes := none, figure := none }
    formerChildren := formerChildren ++ [chld]
  return (newChildren, formerChildren)
-- impl-end

-- proof-start
/-- The loop accumulates a `++ [deparented child]` per element; generalized over
the accumulator it equals `init ++ (map deparent xs)`. -/
theorem loop_helper_clearAxes (xs : List Artist) (init : List Artist) :
    Id.run (forIn xs init (fun chld r =>
      (pure (ForInStep.yield (r ++ [{ chld with axes := none, figure := none }])) : Id _)))
      = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.map_cons]

/-- Closed form of the implementation. -/
theorem impl_eq_clearAxes (artists : List Artist) :
    implementation_clearAxes artists
      = ([], artists.map (fun c => { c with axes := none, figure := none })) := by
  unfold implementation_clearAxes
  simp only [Id.run, bind]
  have := loop_helper_clearAxes artists []
  simp only [Id.run] at this
  rw [this]
  rfl

theorem correct_clearAxes : ∀ artists,
    problem_spec_clearAxes artists (implementation_clearAxes artists) := by
  intro artists
  rw [impl_eq_clearAxes]
  refine ⟨rfl, ?_, ?_⟩
  · simp
  · intro i hi
    refine ⟨{ artists[i] with axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
    · rw [List.getElem?_eq_getElem (by simpa using hi)]
      simp [List.getElem_map]
    · rw [List.getElem?_eq_getElem hi]
-- proof-end
