import Velvet.Std
-- imports-end

/- Total correctness: the real attribute-assembly step is a bounded loop over
   the zipped (sub-field, sub-widget) pairs and always terminates, so a
   diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating loop discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee needs an axiom here. Whether a sub-widget renders the
   required marker is decided entirely by two booleans observable at the
   sub-widget — whether it opts into the marker on its own, and whether its
   sub-field is itself required — together with the two field-level flags. All
   of that is modeled directly in the `pure` region below; nothing is
   axiomatized. -/
-- axioms-end

-- pure-start
/- One sub-field of a MultiValueField, as the rendering step observes it.
   * `required`      — whether this sub-field is itself a required field.
   * `marksRequired` — whether this sub-field's own sub-widget opts into the
                       required marker (a visible text-style widget does; a
                       hidden one does not). -/
structure SubField where
  required      : Bool
  marksRequired : Bool
deriving Inhabited, DecidableEq

/- Whether a single sub-widget should carry the required marker.

   `outerRequired` is the overall gate: the MultiValueField as a whole is
   required and the form asks for the required marker. When that gate is open,
   two regimes apply:
     * all sub-fields jointly required (`requireAll`): every sub-widget carries
       the marker;
     * otherwise (`require_all_fields` is false): a sub-widget carries the
       marker exactly when it opts in on its own AND its sub-field is required.
   When the gate is closed, no sub-widget carries the marker. -/
def subRequired (outerRequired requireAll : Bool) (s : SubField) : Bool :=
  outerRequired && (requireAll || (s.marksRequired && s.required))

/- The per-sub-widget required markers across the whole sub-field list.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def requiredPlan (outerRequired requireAll : Bool) : List SubField → List Bool
  | []      => []
  | s :: ss => subRequired outerRequired requireAll s :: requiredPlan outerRequired requireAll ss

@[grind] lemma requiredPlan_nil (oR rA : Bool) : requiredPlan oR rA [] = [] := rfl
@[grind] lemma requiredPlan_cons (oR rA : Bool) (s : SubField) (ss : List SubField) :
    requiredPlan oR rA (s :: ss) = subRequired oR rA s :: requiredPlan oR rA ss := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method requiredFlags (outerRequired : Bool) (requireAll : Bool) (subs : List SubField) return (out : List Bool)
  ensures out = requiredPlan outerRequired requireAll subs
  do
    -- impl-start
    -- Pre-image skeleton: when the overall gate is open, the marker is applied
    -- UNIFORMLY to every sub-widget, regardless of the per-sub-field
    -- distinction the frozen spec (`subRequired` ⇒ when not requiring all
    -- sub-fields, a sub-widget is marked only if it opts in AND its sub-field
    -- is required) demands. On a sub-field that does not itself require its
    -- value (in a not-require-all field) this over-marks it, so prove_correct
    -- MUST fail against `out = requiredPlan ...`.
    let mut result : List Bool := []
    let mut i := subs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ subs.length
      invariant result = requiredPlan outerRequired requireAll (subs.drop i)
      done_with i = 0
      decreasing i
    do
      let v : Bool := outerRequired
      result := v :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the sub-field at
   `i-1` on the front, so `requiredPlan` peels one `subRequired`. The single goal
   `loom_solve` leaves for the loop body. -/
lemma requiredPlan_drop_step (oR rA : Bool) (subs : List SubField) (i : Nat)
    (hi : 0 < i) (hle : i ≤ subs.length) :
    requiredPlan oR rA (subs.drop (i - 1)) = subRequired oR rA subs[i - 1]! :: requiredPlan oR rA (subs.drop i) := by
  have hlt : i - 1 < subs.length := by omega
  have hcons : subs.drop (i - 1) = subs[i - 1]! :: subs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, requiredPlan_cons]

prove_correct requiredFlags by
  loom_solve
  rw [requiredPlan_drop_step outerRequired requireAll subs i (by omega) (by omega)]
  simp_all
