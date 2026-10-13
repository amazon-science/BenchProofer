import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the
   input-validation routine that resolves the element type of the training
   matrix — is modeled DEEPLY in the `pure` region (`resolveElemType`) and
   validated == the real callee by G-AX (an A-reference, mapping.md §3). It
   carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The element type of a dense numeric matrix, abstracted to the categories the
   validation step distinguishes. `f64`/`f32` are the two floating element types
   that may be carried through unchanged; `f16` is a floating type that is NOT
   carried through; `boolean`, `integer`, `object` are non-floating element
   types (mapping.md §2 gives the bijection to the repository's element-type
   tags). -/
inductive DType where
  | f64
  | f32
  | f16
  | boolean
  | integer
  | object
  deriving DecidableEq

/- Whether an element type is a floating type. This is the property the desired
   behaviour must guarantee for the validated matrix: downstream numeric code
   (signed arithmetic on the matrix) is well-defined only on floating element
   types, so a non-floating input must not survive validation unconverted. -/
@[grind] def DType.isFloating : DType → Bool
  | .f64 => true
  | .f32 => true
  | .f16 => true
  | _    => false

/- The set of floating element types accepted *as-is* by the validation step:
   the two that are carried through unchanged when the input already has one of
   them. -/
@[grind] def DType.isAccepted : DType → Bool
  | .f64 => true
  | .f32 => true
  | _    => false

/- Deep model (A-reference, mapping.md §3.1) of the element-type resolution the
   validation routine performs when the requested element type is the floating
   accept-list {f64, f32}: an input element type that is already one of the
   accepted floating types is preserved; ANY other element type — floating or
   not — is converted to the first accepted floating type (`f64`). Validated
   == the real routine by axiom_check.py (G-AX). -/
@[grind] def resolveElemType (orig : DType) : DType :=
  if orig.isAccepted then orig else .f64

/- The resolved element type is always a floating type: an accepted input is
   already floating, and every other input is converted to `f64`. This is the
   guarantee the desired behaviour pins. -/
@[grind] lemma resolveElemType_isFloating (orig : DType) :
    (resolveElemType orig).isFloating = true := by
  cases orig <;> rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The element type of the training matrix after the model's input-validation
   step. Desired behaviour: validation must hand downstream numeric code a
   matrix whose element type is a floating type, so that signed arithmetic on
   the matrix is well-defined for every supported input — in particular a
   non-floating input (e.g. a matrix of truth values) must be converted, not
   passed through. Concretely, an input whose element type is already one of the
   accepted floating types is kept; any other element type is converted to the
   default floating type.

   `orig` is read-only (not `mut`): the routine inspects the incoming element
   type and decides the validated element type; it does not mutate the input
   tag (directive 5). The result is pinned exactly by `resolveElemType` and is
   guaranteed floating by `resolveElemType_isFloating`. -/
method validatedElementType (orig : DType) return (out : DType)
  ensures out = resolveElemType orig
  ensures out.isFloating = true
  do
    -- impl-start
    -- Pre-image skeleton: the requested element type is the generic "numeric"
    -- policy, which preserves the input element type unless it is the opaque
    -- `object` type (only then converting to the default floating type). A
    -- non-floating input such as a matrix of truth values is therefore passed
    -- through UNCONVERTED — the bug. The frozen spec requires `resolveElemType`
    -- (every non-accepted type converts to f64), so prove_correct MUST fail.
    let isObject : Bool := orig = DType.object
    let out : DType := if isObject then DType.f64 else orig
    return out
    -- impl-end

prove_correct validatedElementType by
  loom_solve
  cases orig <;> rfl
