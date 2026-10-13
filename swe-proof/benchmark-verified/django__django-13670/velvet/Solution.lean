import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The calendar year is taken as a plain `Nat`; the
--  rendering is a pure character computation modeled in full below.)
-- axioms-end

-- pure-start
/- A single decimal digit (0..9) as its ASCII character. `48` is the code point
   of '0'; clamping by `% 10` keeps the map total. -/
def digitChar (d : Nat) : Char := Char.ofNat (48 + d % 10)

/- The two-character short rendering of a number: its value reduced to the last
   two decimal places, written as exactly two characters — tens digit then ones
   digit — so a value below ten still occupies two slots (a leading '0'). -/
def twoDigitString (n : Nat) : List Char :=
  [digitChar (n / 10 % 10), digitChar (n % 10)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The abbreviated form of a calendar year: the part of the year below one
   hundred, written as a fixed-width two-character decimal. The year is a
   non-negative count below ten thousand (the only values a calendar date
   carries). The output is always exactly two characters: when the sub-hundred
   part is a single digit it is filled on the left with a zero, so the width
   never collapses for small values. Nothing is mutated (directive 5); the year
   is read-only and the result is a fresh character sequence. -/
method twoDigitYear (year : Nat) return (out : List Char)
  require year ≤ 9999
  ensures out = twoDigitString (year % 100)
  do
    -- impl-start
    let n := year % 100
    return [digitChar (n / 10 % 10), digitChar (n % 10)]
    -- impl-end

prove_correct twoDigitYear by
  loom_solve
  simp [twoDigitString]
