"""Twin-artifact model for pydata__xarray-3095.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A labelled-index wrapper preserves the element type (dtype) it was created
  with. When such a wrapper is duplicated — whether the duplication makes an
  independent copy of the underlying buffer or merely shares it — the duplicate
  must report the SAME element type as the original.

  This matters because re-deriving the element type from a freshly materialised
  buffer is lossy for some types: a buffer holding fixed-width text, once it has
  round-tripped through the general-purpose index machinery, can no longer be
  distinguished from a buffer of arbitrary Python objects, so a re-derivation
  would report the generic "object" type instead of the original text type.
  The contract therefore requires the duplicate to carry over the element type
  the original was constructed with, rather than recomputing it from the
  duplicated buffer.

The wrapper is modelled as a minimal class carrying only the facts that decide
the reported element type:

  * ``stored_dtype``  — the element-type code the wrapper was created with;
  * ``array_kind``    — the type code that WOULD be re-derived from the wrapper's
                        underlying buffer if no element type were supplied.

These two can disagree precisely for the fixed-width-text case, where
``stored_dtype`` is the text code while a re-derivation of ``array_kind`` yields
the generic object code. Element-type codes and re-derivation are modelled
deeply (``derive_dtype``); there is no consumed axiom. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# A distinguished code for "no explicit element type supplied" (re-derive it).
NO_DTYPE = -1            # type: int
# The generic object element-type code (the lossy fallback).
OBJECT_DTYPE = 0         # type: int


class IndexWrapper:
    """A wrapper around a labelled index. ``stored_dtype`` is the element-type
    code the wrapper reports; ``array_kind`` is the type code that would be
    re-derived from the underlying buffer with no element type supplied."""

    def __init__(self, array_kind: int, stored_dtype: int) -> None:
        Requires(stored_dtype != NO_DTYPE)
        # Level 1: the constructor is a leaf (two field writes, no obligated
        # callee), and it must sit strictly BELOW every caller's level so the
        # caller can hand its obligation down without an obligation leak.
        Requires(MustTerminate(1))
        Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
        Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
        Ensures(self.array_kind == array_kind)    # type: ignore
        Ensures(self.stored_dtype == stored_dtype)  # type: ignore
        self.array_kind = array_kind
        self.stored_dtype = stored_dtype


# axioms-start
# (no @ContractOnly callees: the element-type re-derivation is modelled deeply
# below as derive_dtype, validated against the real wrapper construction by
# axiom_check.py / G-AX, not consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def derive_dtype(array_kind: int, given_dtype: int) -> int:
    """The element-type code a freshly constructed wrapper reports, given the
    re-derivable type code of its buffer (``array_kind``) and an optionally
    supplied element-type code (``given_dtype``).

    When an element type IS supplied (``given_dtype != NO_DTYPE``) it is used
    verbatim. When none is supplied the type is re-derived from the buffer —
    which is the lossy step: a fixed-width-text buffer that has round-tripped
    through the general index machinery re-derives to OBJECT_DTYPE, so any
    ``array_kind`` may legitimately re-derive to the generic object code.
    """
    if given_dtype != NO_DTYPE:
        return given_dtype
    return array_kind
# pure-end


def adapter_copy(self: IndexWrapper, deep: bool) -> int:
    # pre-conditions-start
    Requires(Acc(self.array_kind, 1 / 2))
    Requires(Acc(self.stored_dtype, 1 / 2))
    Requires(self.stored_dtype != NO_DTYPE)
    # a buffer always has some re-derivable element type (never the sentinel).
    Requires(self.array_kind != NO_DTYPE)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.array_kind, 1 / 2))
    Ensures(Acc(self.stored_dtype, 1 / 2))
    # the read-only original is unchanged.
    Ensures(self.array_kind == Old(self.array_kind))
    Ensures(self.stored_dtype == Old(self.stored_dtype))
    # The duplicate reports the SAME element type the original carried, never a
    # type re-derived from the duplicated buffer. This is the discriminating
    # guarantee: it must hold even when a re-derivation would differ (the
    # fixed-width-text case, where re-derivation collapses to the object code).
    Ensures(Result() == Old(self.stored_dtype))
    # post-conditions-end
    # impl-start
    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
    # so its reported type is carried over rather than re-derived.
    array_kind = self.array_kind
    dtype = self.stored_dtype
    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
    return duplicate.stored_dtype
    # impl-end
