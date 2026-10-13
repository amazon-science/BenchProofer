import Mathlib
-- imports-end

/-!
The two-digit representation of a calendar year.

The abstract behaviour: given a year (a non-negative whole number), produce the
two-digit short form of that year — that is, the value of the year reduced
modulo one hundred, rendered as exactly two decimal digits with a leading zero
when the reduced value is below ten. So a year of 476 yields `76`, a year of 42
yields `42`, a year of 4 yields `04`, and a year of 1999 yields `99`. The output
is always exactly two characters, each an ASCII decimal digit.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed. The two-digit short form is a pure
-- arithmetic function of the year (reduction modulo one hundred, then rendering
-- the tens and units digits); it is modeled DEEPLY below, so no `opaque`/`axiom`
-- callee contract is required. The proof agent may add `_prop` axioms only if
-- genuinely stuck.
-- axioms-end

-- pure-start
/-- Render a single decimal digit (`0`–`9`) as its ASCII character. -/
def digitChar (d : Nat) : Char := Char.ofNat (48 + d)

/-- The two-digit short form of a year: reduce modulo one hundred, then emit the
tens digit followed by the units digit. The tens digit is `0` when the reduced
value is below ten, giving the leading-zero behaviour. The result is always
exactly two ASCII decimal digits. -/
def twoDigitYear (year : Nat) : List Char :=
  let r := year % 100
  [digitChar (r / 10), digitChar (r % 10)]
-- pure-end

-- post-conditions-start
/-- The result is exactly the two-digit short form of the year: the two ASCII
decimal digits of the year taken modulo one hundred, with a leading zero when
the reduced value is below ten. -/
def problem_spec_twoDigitYear (year : Nat) (result : List Char) : Prop :=
  result = twoDigitYear year
-- post-conditions-end

-- impl-start
def implementation_twoDigitYear (year : Nat) : List Char := Id.run do
  let r := year % 100
  let tens := r / 10
  let ones := r % 10
  return [digitChar tens, digitChar ones]
-- impl-end

-- proof-start
theorem correct_twoDigitYear : ∀ year : Nat,
    problem_spec_twoDigitYear year (implementation_twoDigitYear year) := by
  intro year
  unfold problem_spec_twoDigitYear implementation_twoDigitYear twoDigitYear
  rfl
-- proof-end
