import Mathlib
-- imports-end

/-!
Combining the masks of two operands during array arithmetic.

When an arithmetic operation is performed between two array-like operands, the
result's mask is derived from the operands' masks. Each operand may or may not
carry a mask, and the caller may optionally supply a function that merges two
masks together (e.g. an element-wise bitwise/logical combination).

The desired behaviour:

  * if no combining function is supplied, or NEITHER operand carries a mask, the
    result carries no mask;
  * if exactly one operand carries a mask, that mask is copied over to the
    result unchanged — the combining function is not consulted;
  * if BOTH operands carry a mask, the result is the combining function applied
    to the two masks.

In particular, when one operand lacks a mask the mask that does exist is simply
propagated to the result; the combining function is never asked to merge an
existing mask with a missing one. (This is the behaviour the issue's
"Expected behavior" section asks for.)
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The combining
-- function is an explicit input (a parameter of the modeled routine), and the
-- mask-propagation decision is modeled structurally over the observable inputs
-- (whether each operand carries a mask, whether a combining function was
-- supplied). No `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A mask is modeled as the (flattened) integer bitmask grid of an operand;
`none` denotes an operand that carries no mask. The combining function is the
optional mask-merging callback the caller may supply (e.g. an element-wise
bitwise-or); `none` denotes that no combining was requested. The result is
either the produced mask (`some`/`none`) or an error, modeling the situation in
which the merge cannot be carried out. -/
abbrev Mask := List Int
abbrev Combine := Mask → Mask → Mask
-- pure-end

-- post-conditions-start
/-- The mask carried by the result of the operation, as a function of the two
operands' masks and the optional combining function. An error result models a
failed merge (the combining callback cannot run on a missing operand mask); a
correct propagation never errors in this domain. -/
def problem_spec_maskPropagation
    (selfMask operandMask : Option Mask) (handleMask : Option Combine)
    (result : Except Unit (Option Mask)) : Prop :=
  result =
    (match handleMask with
     | none => .ok none
     | some hm =>
       match selfMask, operandMask with
       | none,    none    => .ok none
       | none,    some om => .ok (some om)
       | some sm, none    => .ok (some sm)
       | some sm, some om => .ok (some (hm sm om)))
-- post-conditions-end

-- impl-start
def implementation_maskPropagation
    (selfMask operandMask : Option Mask) (handleMask : Option Combine) :
    Except Unit (Option Mask) := Id.run do
  -- Pre-patch bug: the "only one mask present" case keys on whether the SECOND
  -- operand object itself is absent rather than on whether it carries a mask.
  -- In the two-operand domain the operand is always present, so a self-only
  -- mask never takes the copy-over branch; instead it falls through to the
  -- merge, which is asked to combine an existing mask with a missing one.
  match handleMask with
  | none => return .ok none
  | some hm =>
    match selfMask, operandMask with
    | none,    none    => return .ok none
    | none,    some om => return .ok (some om)
    -- self has a mask, operand has none: should copy `sm` over, but the buggy
    -- branch condition is never met, so the merge runs on a missing mask.
    | some _,  none    => return .error ()
    | some sm, some om => return .ok (some (hm sm om))
-- impl-end

-- proof-start
theorem correct_maskPropagation :
    ∀ (selfMask operandMask : Option Mask) (handleMask : Option Combine),
      problem_spec_maskPropagation selfMask operandMask handleMask
        (implementation_maskPropagation selfMask operandMask handleMask) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
