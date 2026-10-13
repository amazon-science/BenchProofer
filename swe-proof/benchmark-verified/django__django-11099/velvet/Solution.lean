import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-code-point character-class membership is
--  taken as a FREE INPUT `isAllowed : Char → Bool`: the spec holds for every
--  value of it, and mapping.md binds it to the real class `[\w.@+-]` under
--  each validator's regex flags. Nothing here needs validation against a
--  real callee, hence no G-AX axioms.)
-- axioms-end

-- pure-start
/- Every code point of a sequence lies in the allowed class `isAllowed`.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern). -/
def allowedAll (isAllowed : Char → Bool) : List Char → Bool
  | []      => true
  | c :: cs => isAllowed c && allowedAll isAllowed cs

@[grind] lemma allowedAll_nil (p : Char → Bool) : allowedAll p [] = true := rfl
@[grind] lemma allowedAll_cons (p : Char → Bool) (c : Char) (cs : List Char) :
    allowedAll p (c :: cs) = (p c && allowedAll p cs) := rfl

/- A sequence names a valid identifier exactly when it is non-empty AND every
   one of its code points — from the first through the very LAST — lies in the
   allowed class. There is NO end-of-input tolerance: no code point is dropped
   or exempted before the check, so a sequence whose final code point falls
   outside the class (such as a trailing line terminator, which the real class
   excludes) is rejected, and so is the empty sequence. -/
def validName (isAllowed : Char → Bool) (s : List Char) : Bool :=
  !s.isEmpty && allowedAll isAllowed s
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The acceptance decision for a candidate identifier, modeled over its code
   point sequence and parametric in the (unchanged) per-code-point class
   membership `isAllowed`: accept iff the candidate is non-empty and every
   code point — including the very last one — is in the allowed class.
   `isAllowed` and `s` are read-only inputs. -/
method validateName (isAllowed : Char → Bool) (s : List Char) return (out : Bool)
  ensures out = validName isAllowed s
  do
    -- impl-start
    let mut acc : Bool := true
    let mut i := s.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ s.length
      invariant acc = allowedAll isAllowed (s.drop i)
      done_with i = 0
      decreasing i
    do
      let c := s[i - 1]!
      acc := isAllowed c && acc
      i := i - 1
    return !s.isEmpty && acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `allowedAll` peels one membership test. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma allowedAll_drop_step (p : Char → Bool) (s : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ s.length) :
    allowedAll p (s.drop (i - 1)) = (p s[i - 1]! && allowedAll p (s.drop i)) := by
  have hlt : i - 1 < s.length := by omega
  have hcons : s.drop (i - 1) = s[i - 1]! :: s.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, allowedAll_cons]

prove_correct validateName by
  loom_solve
  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
    simp_all [Bool.and_comm]
  · simp_all [validName, List.drop_zero]
