# Requirements: mask propagation in NDData arithmetic when one operand has no mask

## Introduction

`astropy.nddata` supports element-wise arithmetic (`add`, `subtract`,
`multiply`, `divide`) between `NDData`-like objects (e.g. `NDDataRef`) through
the `NDArithmeticMixin`. Each operand may optionally carry a `mask`. The caller
controls how the two operands' masks are combined into the result's mask via the
`handle_mask` keyword (for example `handle_mask=np.bitwise_or` for integer
bit-masks, or the string `"first_found"`/`"ff"`).

The mask-combination logic lives in
`astropy.nddata.mixins.ndarithmetic.NDArithmeticMixin._arithmetic_mask`, which is
invoked from the mixin's private `_arithmetic` driver behind the public
arithmetic methods.

A regression was introduced (present in v5.3, absent in v5.2): when exactly one
of the two operands carries a mask and the other does not, the combining
function is nonetheless invoked with a missing mask. With a `handle_mask` such
as `np.bitwise_or`, this raises `TypeError: unsupported operand type(s) for |:
'int' and 'NoneType'`. Cases that trigger the failure include an operand that
carries a mask combined with a plain scalar/constant, or with another operand
that carries no mask.

The goal is to restore the intended behavior: when only one operand has a mask,
that mask is propagated (copied) to the result unchanged, and the combining
function is only ever applied when **both** operands carry a mask.

## Requirement 1: Propagate the single existing mask when one operand lacks a mask

**User story:** As a user performing arithmetic between an `NDData` object that
has a mask and an operand that has none (including a plain scalar/constant), I
want the existing mask to be carried through to the result, so that mask
information is preserved and no error is raised.

**Acceptance criteria**

1. WHEN `_arithmetic_mask` is called with a combining function supplied, the
   calling object (`self`) carrying a mask, and the operand carrying no mask
   (its `mask` attribute is `None`), THEN the result mask SHALL be a copy of the
   calling object's mask and the combining function SHALL NOT be invoked.
2. WHEN `_arithmetic_mask` is called with a combining function supplied, the
   calling object (`self`) carrying no mask, and the operand carrying a mask,
   THEN the result mask SHALL be a copy of the operand's mask and the combining
   function SHALL NOT be invoked.
3. WHEN a public arithmetic method (`add`, `subtract`, `multiply`, `divide`) is
   invoked with `handle_mask=np.bitwise_or` (or any similar element-wise
   combiner) on an operand pair where exactly one side carries an integer
   bit-mask and the other carries no mask, THEN the operation SHALL complete
   without raising, and the resulting object's `mask` SHALL be element-wise
   equal to the one mask that was present.
4. WHEN one operand carries a mask and the other operand is a plain scalar or
   constant (which carries no mask), THEN the operation SHALL complete without
   raising `TypeError`, and the result's `mask` SHALL equal the mask that was
   present.
5. The system SHALL return the propagated single mask as an independent copy, so
   that mutating the result's mask does not alter the source operand's mask.

## Requirement 2: Combine both masks only when both operands carry a mask

**User story:** As a user combining two masked `NDData` objects, I want the
supplied combining function to merge the two masks, so that both operands'
masking information is reflected in the result.

**Acceptance criteria**

1. WHEN `_arithmetic_mask` is called with a combining function supplied and
   BOTH the calling object and the operand carry a mask, THEN the result mask
   SHALL be the value produced by applying that combining function to the
   calling object's mask and the operand's mask (with any additional keyword
   arguments forwarded to it).
2. WHEN two masked operands are combined with `handle_mask=np.bitwise_or`, THEN
   the resulting object's `mask` SHALL equal the element-wise bitwise-or of the
   two input masks.

## Requirement 3: No result mask when neither operand has a mask or no combiner is given

**User story:** As a user, I want the result to have no mask when there is no
masking information to propagate, so that unmasked arithmetic stays unmasked.

**Acceptance criteria**

1. WHEN a combining function is supplied but neither the calling object nor the
   operand carries a mask, THEN the result mask SHALL be `None`.
2. IF no combining function is supplied (`handle_mask` is `None`), THEN the
   result mask SHALL be `None` regardless of the operands' masks.
3. WHEN both operands lack a mask and an element-wise combiner such as
   `np.bitwise_or` is supplied, THEN the operation SHALL complete without
   raising and the resulting object's `mask` SHALL be `None`.

## Requirement 4: Preserve existing arithmetic and mask-handling behavior

**User story:** As a maintainer, I want the fix to preserve all previously
correct arithmetic behavior, so that no existing functionality regresses.

**Acceptance criteria**

1. The system SHALL keep the `handle_mask` string options `"first_found"` and
   `"ff"` behaving as before: when at least one operand has a mask, the result
   mask SHALL be a copy of the first operand's mask if it exists, otherwise a
   copy of the other operand's mask.
2. The system SHALL keep data-value computation for `add`, `subtract`,
   `multiply`, and `divide` unchanged, independent of masking.
3. The system SHALL keep uncertainty propagation (standard-deviation, variance,
   and inverse-variance uncertainties, including correlation handling and unit
   handling) unchanged.
4. The system SHALL keep WCS comparison and `meta` merging behavior unchanged.
5. WHEN both operands lack any mask attribute value and no masking is requested,
   THEN existing behavior of returning an unmasked result SHALL be preserved.
6. The system SHALL keep raising the existing errors/warnings for unsupported
   configurations (e.g. incompatible units, unsupported uncertainty
   correlation, and the PSF-not-propagated warning) unchanged.
