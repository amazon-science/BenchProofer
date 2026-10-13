import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two pre-computed renderings the routine chooses
--  between are UNCHANGED sub-results of the surrounding code, modeled as plain
--  read-only inputs — tagged R in refinement.md, not axioms. Nothing is asserted
--  about their value, so G-AX has nothing to validate.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A number-display routine renders a numeric value for output. Two candidate
   renderings of the same value are available: an integer rendering (the value
   shown with no fractional component) and a fractional rendering (the value
   shown with a chosen count of fractional digits). The routine must choose
   between them.

   Desired behavior: when the value is a whole number AND the requested count of
   fractional digits is not positive, the integer rendering is the correct
   output; in every other case the fractional rendering is used. In particular,
   when a whole number is asked to be shown with zero fractional digits the
   integer rendering must be chosen — selecting the fractional rendering there is
   incorrect.

   `isWhole` is the read-only flag "the value has no fractional part"; `p` is the
   read-only requested fractional-digit count (which may be negative). The two
   renderings `intView`/`fracView` are read-only pre-computed results; the
   routine selects one and mutates nothing (directive 5). Strings are modeled as
   `List Char`. -/
method numericDisplay (isWhole : Bool) (p : Int)
    (intView : List Char) (fracView : List Char) return (out : List Char)
  ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)
  do
    -- impl-start
    -- Choose the integer rendering exactly when the value is whole and the
    -- requested fractional-digit count is not positive; otherwise the fractional
    -- rendering. The selection mutates nothing.
    if isWhole = true ∧ p ≤ 0 then
      return intView
    else
      return fracView
    -- impl-end

prove_correct numericDisplay by
  loom_solve
