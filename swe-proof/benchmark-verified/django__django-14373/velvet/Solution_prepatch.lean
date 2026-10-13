import Velvet.Std
-- imports-end

/- Total correctness: the real rendering is a straight-line pure computation
   (four digit extractions and a fixed-width write) that always terminates, so
   a diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the postcondition vacuously. -/
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

/- The four-character rendering of a number below ten thousand: its thousands,
   hundreds, tens and ones digits, written as exactly four characters — most
   significant first — so a value below one thousand still occupies four slots
   (filled on the left with zeros). -/
def fourDigitString (n : Nat) : List Char :=
  [digitChar (n / 1000 % 10), digitChar (n / 100 % 10),
   digitChar (n / 10 % 10), digitChar (n % 10)]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The full form of a calendar year: the year written as a fixed-width
   four-character decimal. The year is a non-negative count below ten thousand
   (the only values a calendar date carries). The output is always exactly four
   characters: when the year is below one thousand the high-order slots are
   filled on the left with zeros, so the width never collapses for small years.
   Nothing is mutated (directive 5); the year is read-only and the result is a
   fresh character sequence. -/
method fourDigitYear (year : Nat) return (out : List Char)
  require year ≤ 9999
  ensures out = fourDigitString year
  do
    -- impl-start
    -- Pre-image skeleton: the year was emitted as its bare decimal value rather
    -- than as a fixed-width field, so a year below one thousand keeps only as
    -- many characters as its magnitude needs — the high-order slots are NOT
    -- filled with zeros. This drops the leading slots and MUST fail the spec
    -- whenever the year is below one thousand (fewer than four characters).
    let out : List Char :=
      if year < 10 then [digitChar (year % 10)]
      else
        if year < 100 then
          [digitChar (year / 10 % 10), digitChar (year % 10)]
        else
          if year < 1000 then
            [digitChar (year / 100 % 10), digitChar (year / 10 % 10),
             digitChar (year % 10)]
          else
            [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
             digitChar (year / 10 % 10), digitChar (year % 10)]
    return out
    -- impl-end

prove_correct fourDigitYear by
  loom_solve
  simp [fourDigitString]
