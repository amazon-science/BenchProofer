import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the changed operation is the selection of the
--  second argument's OWN attribute identity, modeled deeply. No outside callee
--  contract is consumed.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A conditional-selection routine is asked to preserve the attribute mapping of
   its SECOND positional argument. The mapping it preserves must be the mapping
   that BELONGS TO that second argument. If the second argument is a bare scalar
   (it carries no mapping of its own), the preserved mapping is the empty one.

   The routine is also handed the list of attribute mappings of exactly those
   arguments that actually carry one, in argument order. That list is NOT a
   reliable positional handle on the second argument: a scalar argument
   contributes no entry, so the second argument's mapping need not sit at any
   constant offset in the list (and may be absent from it entirely). The
   preserved mapping must therefore be the second argument's OWN mapping,
   regardless of its position in that list (or its absence from it).

   Attribute mappings are modeled as opaque integer identities (distinct
   mappings have distinct identities; the empty mapping, which is also what a
   scalar carries, is the identity 0). `present` is the list of identities of
   the arguments that carry a mapping, in order. `xAttrs` is the identity of the
   second argument's own mapping. `xPos` locates the second argument's mapping
   inside `present` (-1 when the second argument carries no mapping, i.e. it is a
   scalar). The carried structural fact — an entry actually present in `present`
   agrees with the owning argument's identity — pins the result to the second
   argument's mapping as PRODUCED from that argument, not merely a value read at
   a constant list offset.

   All three inputs are read-only (not `mut`); the routine mutates nothing
   (directive 5). `present` is modeled as `List Int`, the identities and the
   position as `Int`. -/
method attrsToKeep (present : List Int) (xAttrs : Int) (xPos : Int) return (out : Int)
  -- `xPos` locates the second argument's own mapping within `present`, or is
  -- -1 when the second argument carries no mapping (it is a scalar).
  require xPos = -1 ∨ (0 ≤ xPos ∧ xPos < present.length)
  -- When the second argument's mapping is present, the entry at that position is
  -- exactly the second argument's own mapping.
  require ∀ k : Nat, (xPos = (k : Int) ∧ k < present.length) → present[k]! = xAttrs
  -- A scalar second argument carries the empty mapping (identity 0).
  require xPos = -1 → xAttrs = 0
  -- The preserved mapping is the second argument's OWN mapping.
  ensures out = xAttrs
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: the preserved mapping is read at the CONSTANT
    -- offset 1 of the present-mappings list, rather than from the second
    -- argument itself. When the second argument's mapping does not sit at offset
    -- 1 (it is a scalar, or the leading arguments are not all carriers), this
    -- entry is the wrong mapping (or out of range entirely). The frozen spec
    -- requires `out = xAttrs`, so prove_correct MUST fail.
    return present[1]!
    -- impl-end

prove_correct attrsToKeep by
  loom_solve
