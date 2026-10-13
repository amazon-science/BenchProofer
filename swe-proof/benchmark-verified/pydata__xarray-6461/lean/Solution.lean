import Mathlib
-- imports-end

/-!
Resolving the attribute dictionary of a three-argument conditional selection.

Each of the three arguments is either a *labelled array* that carries its own
attribute dictionary, or a bare *scalar* that carries no attributes. When the
caller asks for attribute preservation, the selection's resulting attributes are
defined to be those of the **second** argument (the value chosen where the
condition holds) — its attribute dictionary if it is a labelled array, or the
empty dictionary if it is a scalar.

There is one subtlety inherited from the underlying attribute-merging routine:
if *none* of the three arguments is a labelled array there is nothing to merge,
and the routine yields "no attributes" (modeled as `none`) without consulting
the preservation rule at all.

An attribute dictionary is modeled as an association list `List (String ×
String)` (key/value pairs). The overall result is modeled as `Except Unit
(Option Attrs)`: `Except.ok none` for the no-arrays case, `Except.ok (some d)`
for a resolved dictionary `d`, and `Except.error ()` reserved for an
out-of-range lookup failure.
-/

-- axioms-start
-- No unchanged callee is consumed: the attribute-selection rule and the
-- "nothing to merge" short-circuit are both modeled deeply (spelled out).
-- axioms-end

-- pure-start
/-- An attribute dictionary: an ordered list of key/value pairs. -/
abbrev Attrs := List (String × String)

/-- A positional argument to the conditional selection: either a labelled array
carrying its own attribute dictionary, or a bare scalar (no attributes). -/
inductive Arg where
  | darray (attrs : Attrs)
  | scalar
  deriving DecidableEq, Repr

/-- Whether an argument is a labelled array (carries attributes). -/
def Arg.isDarray : Arg → Bool
  | .darray _ => true
  | .scalar   => false

/-- The attribute dictionary of an argument: its own dictionary if it is a
labelled array, otherwise the empty dictionary. -/
def attrsOf : Arg → Attrs
  | .darray a => a
  | .scalar   => []
-- pure-end

-- post-conditions-start
/-- Specification of the resolved attributes of `select cond x y` under
attribute preservation.

Let `objs` be the labelled-array arguments, in positional order. Then:
* if there are no labelled-array arguments, the result is `ok none`
  (nothing to merge);
* otherwise the result is `ok (some (attrsOf x))` — the attributes of the
  second positional argument `x`. -/
def problem_spec_whereAttrs
    (cond x y : Arg) (result : Except Unit (Option Attrs)) : Prop :=
  let objs := [cond, x, y].filter (fun a => a.isDarray)
  (objs = [] → result = Except.ok none) ∧
  (objs ≠ [] → result = Except.ok (some (attrsOf x)))
-- post-conditions-end

-- impl-start
def implementation_whereAttrs
    (cond x y : Arg) : Except Unit (Option Attrs) := Id.run do
  let objs := [cond, x, y].filter (fun a => a.isDarray)
  if objs = [] then
    return Except.ok none
  return Except.ok (some (attrsOf x))
-- impl-end

-- proof-start
theorem correct_whereAttrs :
    ∀ (cond x y : Arg),
      problem_spec_whereAttrs cond x y
        (implementation_whereAttrs cond x y) := by
  intro cond x y
  unfold problem_spec_whereAttrs implementation_whereAttrs
  simp only [Id.run]
  by_cases h : [cond, x, y].filter (fun a => a.isDarray) = []
  · refine ⟨fun _ => ?_, fun hne => absurd h hne⟩
    simp only [h, if_true]
    rfl
  · refine ⟨fun he => absurd he h, fun _ => ?_⟩
    simp only [h, if_false]
    rfl
-- proof-end
