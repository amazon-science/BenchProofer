import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A single declared option, abstracted to only the observations that decide
   whether its supplied value must be forwarded to argument re-parsing.

   * `supplied`        — a value for this option was provided by the caller (its
                         destination name is present among the supplied keyword
                         arguments).
   * `individuallyRequired` — the option is required on its own.
   * `inRequiredGroup` — the option belongs to a mutually exclusive group that is
                         itself required (at least one of the group's members
                         must be provided). -/
structure OptionView where
  supplied : Bool
  individuallyRequired : Bool
  inRequiredGroup : Bool
  deriving Inhabited

/- A supplied option's value must be forwarded for re-parsing exactly when the
   caller provided it AND it is mandatory — either required on its own, or a
   member of a required mutually exclusive group. An option whose value was not
   provided is never forwarded; a non-mandatory provided option is not forwarded
   here either (its value is merged separately). -/
@[grind] def forwarded (a : OptionView) : Bool :=
  a.supplied && (a.individuallyRequired || a.inRequiredGroup)

/- Whether each declared option, in declaration order, has its value forwarded.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def forwardedAll : List OptionView → List Bool
  | []      => []
  | a :: rest => forwarded a :: forwardedAll rest

@[grind] lemma forwardedAll_nil : forwardedAll [] = [] := rfl
@[grind] lemma forwardedAll_cons (a : OptionView) (rest : List OptionView) :
    forwardedAll (a :: rest) = forwarded a :: forwardedAll rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method selectForwarded (options : List OptionView) return (out : List Bool)
  ensures out = forwardedAll options
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := options.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ options.length
      invariant result = forwardedAll (options.drop i)
      done_with i = 0
      decreasing i
    do
      let a := options[i - 1]!
      -- Pre-image skeleton: an option's value is forwarded only when it was
      -- supplied AND it is required on its own; membership of a required
      -- mutually exclusive group is NOT consulted. The frozen spec forwards a
      -- supplied option that is mandatory by EITHER route, so a supplied
      -- group-only-required option diverges and prove_correct MUST fail.
      let c : Bool := a.supplied && a.individuallyRequired
      result := c :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `forwardedAll` peels one `forwarded`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma forwardedAll_drop_step (options : List OptionView) (i : Nat)
    (hi : 0 < i) (hle : i ≤ options.length) :
    forwardedAll (options.drop (i - 1))
      = forwarded options[i - 1]! :: forwardedAll (options.drop i) := by
  have hlt : i - 1 < options.length := by omega
  have hcons : options.drop (i - 1) = options[i - 1]! :: options.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, forwardedAll_cons]

prove_correct selectForwarded by
  loom_solve
  rw [forwardedAll_drop_step options i (by omega) (by omega)]
  simp_all
