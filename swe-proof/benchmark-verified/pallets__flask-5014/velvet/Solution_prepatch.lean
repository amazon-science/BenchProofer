import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the acceptance decision is a pure property of the
--  candidate name's code points — its emptiness and whether any code point is
--  the dot — modeled deeply in the `pure` region. The unchanged base
--  initialisation performed before the decision touches none of the state this
--  specification observes and cannot alter the accept/reject outcome, so it is
--  abstracted away rather than axiomatised.)
-- axioms-end

-- pure-start
/- Whether a sequence of code points contains the dot code point U+002E ('.').
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern). -/
def containsDot : List Char → Bool
  | []      => false
  | c :: cs => c == '.' || containsDot cs

@[grind] lemma containsDot_nil : containsDot [] = false := rfl
@[grind] lemma containsDot_cons (c : Char) (cs : List Char) :
    containsDot (c :: cs) = (c == '.' || containsDot cs) := rfl

/- A candidate name is acceptable for construction exactly when it is non-empty
   AND carries no dot code point. A name with zero code points (the empty name)
   is rejected, as is any name carrying a dot. -/
def validName (s : List Char) : Bool :=
  !s.isEmpty && !containsDot s
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The acceptance decision for a candidate construction name, modeled over its
   code point sequence: accept (return `true`) iff the name is non-empty and
   contains no dot code point; otherwise reject (return `false`). The empty name
   must be rejected. -/
method validateBlueprintName (s : List Char) return (out : Bool)
  ensures out = validName s
  do
    -- impl-start
    -- Pre-image skeleton: the decision checks ONLY for a dot code point and has
    -- no emptiness guard, so a name with zero code points (the empty name) is
    -- wrongly ACCEPTED (`!hasDot` is `true` for the empty input). The frozen
    -- spec rejects the empty name (`validName [] = false`), so on `s = []` the
    -- exit goal reduces to `true = false`: `prove_correct` MUST fail (G-DIFF).
    let mut hasDot : Bool := false
    let mut i := s.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ s.length
      invariant hasDot = containsDot (s.drop i)
      done_with i = 0
      decreasing i
    do
      let c := s[i - 1]!
      hasDot := c == '.' || hasDot
      i := i - 1
    return !hasDot
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `containsDot` peels one membership test. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma containsDot_drop_step (s : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ s.length) :
    containsDot (s.drop (i - 1)) = (s[i - 1]! == '.' || containsDot (s.drop i)) := by
  have hlt : i - 1 < s.length := by omega
  have hcons : s.drop (i - 1) = s[i - 1]! :: s.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, containsDot_cons]

prove_correct validateBlueprintName by
  loom_solve
  -- The loop-body leg discharges via the same drop-step lemma.
  · rw [containsDot_drop_step s i (by omega) (by omega)]
    simp_all [Bool.or_comm]
  -- The exit leg is the discriminating obligation: this skeleton omits the
  -- emptiness conjunct, so on `s = []` (empty, dot-free) the goal reduces to
  -- `true = false`, which is unprovable. The prepatch fails here (G-DIFF).
  · simp_all [validName, List.drop_zero]
