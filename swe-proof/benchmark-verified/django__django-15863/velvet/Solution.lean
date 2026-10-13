import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The fixed-point rendering of a non-negative decimal numeral to a requested
   number of fractional places, when that request keeps or exceeds the numeral's
   own fractional length (so no value is rounded away). The integer-digit run and
   the fractional-digit run are reproduced verbatim — every significant digit the
   numeral carries survives — and the fractional run is right-extended with as
   many trailing '0' as are needed to reach the requested width. -/
def renderFixed (intDigits fracDigits : List Char) (p : Nat) : List Char :=
  intDigits ++ ['.'] ++ fracDigits ++ List.replicate (p - fracDigits.length) '0'

/- One zero-pad step at the tail: extending the replicate run by one and tacking
   on a single '0' coincide. The single algebraic fact the backward pad loop
   needs (the front/back-recursive fold pattern, SPEC_GUIDE §3). -/
lemma pad_tail_step (frac : List Char) (P k : Nat) (hk : 0 < k) (hkP : k ≤ P) :
    frac ++ List.replicate (P - k) '0' ++ ['0']
      = frac ++ List.replicate (P - (k - 1)) '0' := by
  have hpk : P - (k - 1) = (P - k) + 1 := by omega
  rw [hpk, List.replicate_succ', ← List.append_assoc]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a non-negative decimal numeral, given as its integer-digit run
   `intDigits` and fractional-digit run `fracDigits`, to exactly `p` fractional
   places, in the regime where `p` is at least the numeral's own fractional
   length (no digit is rounded off). The result must carry every fractional digit
   the numeral has, in order, padded on the right with trailing zeros to width
   `p`. The integer run is emitted unchanged ahead of the decimal point. -/
method floatFormat (intDigits : List Char) (fracDigits : List Char) (p : Nat) return (out : List Char)
  require 1 ≤ p
  require fracDigits.length ≤ p
  require intDigits ≠ []
  require ∀ c ∈ intDigits, c.isDigit
  require ∀ c ∈ fracDigits, c.isDigit
  ensures out = renderFixed intDigits fracDigits p
  do
    -- impl-start
    let mut digits : List Char := fracDigits
    let mut k : Nat := p - fracDigits.length
    while k > 0
      invariant k ≤ p - fracDigits.length
      invariant digits = fracDigits ++ List.replicate (p - fracDigits.length - k) '0'
      done_with k = 0
      decreasing k
    do
      digits := digits ++ ['0']
      k := k - 1
    return intDigits ++ ['.'] ++ digits
    -- impl-end

prove_correct floatFormat by
  loom_solve
  · rw [invariant_2]
    rw [pad_tail_step fracDigits (p - fracDigits.length) k (by omega) (by omega)]
  · simp_all [renderFixed]
