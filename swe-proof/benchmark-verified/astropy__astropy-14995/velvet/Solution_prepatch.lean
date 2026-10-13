import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The mask-combining routine treats each operand's
--  mask as opaque presence-or-absence and, when both are present, hands the two
--  mask values to the caller-supplied combiner. That combiner is a parameter of
--  the routine, modeled directly as the function `combine`; there is no
--  unchanged library callee whose contract the proof must assume.)
-- axioms-end

-- pure-start
-- (No pure helpers required: the result is a direct case split over which
--  operands carry a mask and whether a combiner was supplied.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine the masks of two operands of an elementwise operation.

   Each operand may or may not carry a mask (`some` values vs. `none`). A
   caller-supplied combiner `combine` merges two present masks elementwise; the
   caller may also decline mask handling entirely (`handleMaskNone = true`).
   The second operand is a real operand value, never absent (`operandPresent`).

   The resulting mask is determined entirely by which masks are present:

   - if the caller declines mask handling, or NEITHER operand carries a mask,
     there is no resulting mask (`none`);
   - if ONLY the second operand carries a mask, that mask is the result (it is
     carried over unchanged);
   - if ONLY the first operand carries a mask, that mask is the result (it is
     carried over unchanged);
   - if BOTH operands carry a mask, the result is the combiner applied to the
     two present mask values.

   The two single-mask cases must each yield the one mask that is present — they
   must never attempt to combine a present mask with an absent one. The mask
   values themselves are read-only carriers (not `mut`); the routine builds a
   fresh result and mutates neither operand's mask (directive 5). -/
method resolveMask
    (selfMask : Option (List Int))
    (operandMask : Option (List Int))
    (handleMaskNone : Bool)
    (operandPresent : Bool)
    (combine : List Int → List Int → List Int)
    return (out : Option (List Int))
  require operandPresent = true
  ensures handleMaskNone = true → out = none
  ensures (handleMaskNone = false ∧ selfMask = none ∧ operandMask = none) →
    out = none
  ensures (handleMaskNone = false ∧ selfMask = none ∧ operandMask ≠ none) →
    out = operandMask
  ensures (handleMaskNone = false ∧ selfMask ≠ none ∧ operandMask = none) →
    out = selfMask
  ensures (handleMaskNone = false ∧ selfMask ≠ none ∧ operandMask ≠ none) →
    out = some (combine (selfMask.getD []) (operandMask.getD []))
  do
    -- impl-start
    -- Pre-image skeleton: the single-mask carry-over branch guards on whether
    -- the SECOND OPERAND ITSELF is absent, rather than on whether that operand's
    -- MASK is absent. For a real second operand (`operandPresent = true`) this
    -- guard is never taken, so a present first mask paired with an absent second
    -- mask falls through to the combiner instead of being carried over. The
    -- frozen spec requires `out = selfMask` in that case, so prove_correct MUST
    -- fail.
    let out : Option (List Int) :=
      if ((selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true) then
        none
      else
        if selfMask = none then
          operandMask
        else
          if operandPresent = false then
            selfMask
          else
            some (combine (selfMask.getD []) (operandMask.getD []))
    return out
    -- impl-end

prove_correct resolveMask by
  loom_solve
