"""Twin-artifact model for astropy__astropy-8872.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a numeric value is wrapped into a unit-carrying quantity and the caller
  supplies no explicit element type, the constructor must decide whether to
  coerce the stored elements to the default real type. The decision is a
  predicate on the *kind* of the value's element type alone:

    * integer and unsigned-integer element kinds are coerced to the default
      real type (an integer cannot stand in for a measured real value);
    * EVERY real (inexact / floating) element kind is preserved exactly,
      whatever its storage width -- the narrowest real kind is kept as
      faithfully as the widest;
    * the complex element kind, and composite (multi-field) element kinds, are
      preserved;
    * boolean elements are preserved.

  Two call paths make this decision. The first applies when the incoming value
  already carries a unit (the "homogeneous" path): there it coerces only the
  integer / unsigned-integer kinds. The second applies to a plain value with no
  unit (the "generic" path): there it coerces the integer / unsigned-integer
  kinds AND the opaque per-element-object kind (whose elements are arbitrary
  Python numbers and have no native real storage).

  In both paths the decision is a function of the element kind ONLY. An element
  type carries other observable properties (e.g. whether its storage can hold a
  given reference real value without loss, and whether it is composite); the
  decision must not be a function of those properties, only of the kind.

An element type is modelled abstractly by three observables: its `kind` (an
integer code identifying the storage category -- modelled as the code point of
the single-character category tag), whether a reference 32-bit real value fits
into its storage without loss (`fits_ref_real32`), and whether it is
composite/multi-field (`is_composite`). The relationships among these
observables that real element types obey are pinned as preconditions so the
spec ranges over realisable element types only. Nagini bans `str` indexing, so
kind tags are integer code points; the decision is pure boolean logic over
plain ints/bools (no heap permission needed).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatised callees: the changed operation is a pure predicate over the
#  element-type observables, modelled deeply below)
# axioms-end


# pure-start
@Pure
def KIND_BOOL() -> int:
    # numpy kind tag 'b'
    return 98


@Pure
def KIND_INT() -> int:
    # numpy kind tag 'i' (signed integer)
    return 105


@Pure
def KIND_UINT() -> int:
    # numpy kind tag 'u' (unsigned integer)
    return 117


@Pure
def KIND_REAL() -> int:
    # numpy kind tag 'f' (real / inexact floating)
    return 102


@Pure
def KIND_COMPLEX() -> int:
    # numpy kind tag 'c' (complex)
    return 99


@Pure
def KIND_OBJECT() -> int:
    # numpy kind tag 'O' (per-element Python object)
    return 79


@Pure
def KIND_COMPOSITE() -> int:
    # numpy kind tag 'V' (void / structured multi-field record)
    return 86


@Pure
def is_int_like(kind: int) -> bool:
    """The integer / unsigned-integer element kinds."""
    return kind == KIND_INT() or kind == KIND_UINT()


@Pure
def realizable(kind: int, fits_ref_real32: bool, is_composite: bool) -> bool:
    """The set of element types that can actually occur, pinning the real
    relationships among the three observables (so the spec ranges over genuine
    element types, not impossible combinations):

      * `fits_ref_real32` (a reference 32-bit real fits losslessly into the
        kind's storage) holds ONLY for the real kind (when wide enough), the
        complex kind, and the opaque per-element-object kind (which absorbs any
        value); a NARROW real kind, and the integer / unsigned / boolean /
        composite kinds, do NOT admit it;
      * `is_composite` holds exactly for the composite multi-field kind.
    """
    return (
        # only the real, complex, or opaque-object kinds can absorb a reference
        # 32-bit real value
        Implies(fits_ref_real32,
                kind == KIND_REAL() or kind == KIND_COMPLEX()
                or kind == KIND_OBJECT())
        # composite-ness is exactly the composite kind
        and (is_composite == (kind == KIND_COMPOSITE()))
        # the complex kind is never composite
        and Implies(kind == KIND_COMPLEX(), not is_composite)
        # integer / unsigned / boolean kinds never absorb the reference real and
        # are never composite
        and Implies(is_int_like(kind) or kind == KIND_BOOL(),
                    (not fits_ref_real32) and (not is_composite))
    )
# pure-end


def coerce_homogeneous_input(kind: int, fits_ref_real32: bool,
                             is_composite: bool) -> bool:
    # pre-conditions-start
    # plain ints/bools (no heap permission). The element type ranges over the
    # realisable combinations only.
    Requires(realizable(kind, fits_ref_real32, is_composite))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The homogeneous-path decision depends ONLY on the element kind: coerce
    # exactly the integer / unsigned-integer kinds. Every real kind (narrow or
    # wide), the complex kind, the boolean kind and composite kinds are
    # preserved. Grounded structurally in the input `kind`.
    Ensures(Result() == is_int_like(kind))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the decision keys on whether the element type
    # can absorb a reference 32-bit real (a width comparison) rather than on the
    # element kind. A narrow real kind cannot absorb it and is wrongly coerced.
    return not (fits_ref_real32 or is_composite)
    # impl-end


def coerce_generic_input(kind: int, fits_ref_real32: bool,
                         is_composite: bool) -> bool:
    # pre-conditions-start
    Requires(realizable(kind, fits_ref_real32, is_composite))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # The generic-path decision depends ONLY on the element kind: coerce the
    # integer / unsigned-integer kinds AND the opaque per-element-object kind.
    # Every real kind (narrow or wide), the complex kind, the boolean kind and
    # composite kinds are preserved. Grounded structurally in the input `kind`.
    Ensures(Result() == (is_int_like(kind) or kind == KIND_OBJECT()))
    # post-conditions-end
    # impl-start
    return is_int_like(kind) or kind == KIND_OBJECT()
    # impl-end
