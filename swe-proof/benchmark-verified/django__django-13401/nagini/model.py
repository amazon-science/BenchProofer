"""Twin-artifact model for django__django-13401.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A schema attribute carries an integer creation rank and, optionally, an
  owning-container identity (a label/name pair). Three relational operations are
  specified over two such attributes:

  (1) EQUALITY. Two attributes are equal exactly when they share the same
      creation rank AND have the same owning-container identity. "Same identity"
      means: both lack an owner, or both have an owner with an identical
      (label, name) pair. Consequently two attributes that share a creation rank
      but belong to DIFFERENT owning containers are NOT equal — and one that has
      an owner is never equal to one that lacks an owner.

  (2) STRICT ORDER (a total order refining equality, used so the attributes may
      be kept sorted). The order is taken first by creation rank, for backward
      compatibility: whenever the two ranks differ, OR neither attribute has an
      owner, the smaller-ranked one precedes. Only when the ranks are equal and
      ownership is involved does the owner break the tie: an attribute that
      lacks an owner precedes one that has an owner; and when both have an owner
      with the same rank, they are ordered by the lexicographic order of their
      (label, name) identity pair.

  (3) HASH KEY. The value an attribute contributes to a hash is determined by
      its FULL identity — its creation rank together with its owning-container
      identity (the (label, name) pair, or their absence) — not by the creation
      rank alone. Hence two attributes that differ in owning container (even at
      the same creation rank) contribute distinct hash keys, so a hashed
      collection keeps them distinct rather than collapsing them.

Strings (the label and name of an owner) are modelled as `List[int]` of code
points (Nagini bans `str` indexing); the (label, name) identity pair is carried
as a single `PSeq[int]` key (label, a separator below every identifier code
point, then name), and identity-pair comparison is the lexicographic order on
that key. The hash KEY is modelled deeply (the operation under specification is
which identity flows into the hash, not the hashing itself).

Markers (machine-parsed) delimit the spec / proof / impl regions; provenance
binding to the repository is in mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Attr:
    """A schema attribute abstracted by its integer creation rank `rank`, a flag
    `owned` recording whether it has an owning container, and `okey`, the owner
    identity (label, name) flattened into one code-point sequence. `okey` is
    meaningful only when `owned` is true."""

    def __init__(self, rank: int, owned: bool, okey: PSeq[int]) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.rank) and Acc(self.owned) and Acc(self.okey))  # type: ignore
        Ensures(self.rank == rank and self.owned == owned)  # type: ignore
        Ensures(self.okey is okey)  # type: ignore
        self.rank = rank  # type: ignore
        self.owned = owned  # type: ignore
        self.okey = okey  # type: ignore


# axioms-start
# (No axiomatized callees: equality, the order, and the hash KEY are modelled
# deeply over the attributes' own fields. The unchanged hashing of a key is an
# A-reference validated out-of-band by axiom_check.py / G-AX, not a consumed
# axiom of this proof.)
# axioms-end


# pure-start
@Pure
def lex_lt(x: PSeq[int], y: PSeq[int]) -> bool:
    """Lexicographic strict less-than on two code-point sequences (the order
    Python uses to compare the (label, name) identity pairs). Front-recursive so
    one unfold is available per element."""
    if len(x) == 0:
        return len(y) > 0
    if len(y) == 0:
        return False
    if x[0] != y[0]:
        return x[0] < y[0]
    return lex_lt(x.drop(1), y.drop(1))


@Pure
def same_owner(a: 'Attr', b: 'Attr') -> bool:
    """Two attributes have the same owning-container identity iff both lack an
    owner, or both have an owner with an identical (label, name) key."""
    Requires(Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    Requires(Acc(b.owned, 1 / 8) and Acc(b.okey, 1 / 8))  # type: ignore
    return a.owned == b.owned and (not a.owned or a.okey == b.okey)  # type: ignore


@Pure
def eq_ref(a: 'Attr', b: 'Attr') -> bool:
    """Reference equality: same creation rank AND same owning-container identity."""
    Requires(Acc(a.rank, 1 / 8) and Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    Requires(Acc(b.rank, 1 / 8) and Acc(b.owned, 1 / 8) and Acc(b.okey, 1 / 8))  # type: ignore
    return a.rank == b.rank and same_owner(a, b)  # type: ignore


@Pure
def lt_ref(a: 'Attr', b: 'Attr') -> bool:
    """Reference strict order: by creation rank first; only equal-rank owned
    attributes are tie-broken (no-owner before owner, then by identity key)."""
    Requires(Acc(a.rank, 1 / 8) and Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    Requires(Acc(b.rank, 1 / 8) and Acc(b.owned, 1 / 8) and Acc(b.okey, 1 / 8))  # type: ignore
    if a.rank != b.rank or (not a.owned and not b.owned):  # type: ignore
        return a.rank < b.rank  # type: ignore
    if a.owned != b.owned:  # type: ignore
        return not a.owned  # type: ignore
    return lex_lt(a.okey, b.okey)  # type: ignore


@Pure
def hash_ref(a: 'Attr') -> PSeq[int]:
    """Reference hash KEY: the full identity that flows into the hash — the
    creation rank, an ownership flag, then (when owned) the identity key. Two
    attributes contribute the same hash key iff this whole sequence agrees, so
    attributes differing in owner contribute distinct keys."""
    Requires(Acc(a.rank, 1 / 8) and Acc(a.owned, 1 / 8) and Acc(a.okey, 1 / 8))  # type: ignore
    if a.owned:  # type: ignore
        return PSeq(a.rank, 1) + a.okey  # type: ignore
    return PSeq(a.rank, 0)  # type: ignore
# pure-end


def attr_eq(self_: Attr, other: Attr) -> bool:
    # pre-conditions-start
    Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Ensures(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    # Equal iff same creation rank AND same owning-container identity.
    Ensures(Result() == eq_ref(self_, other))
    # post-conditions-end
    # impl-start
    return (
        self_.rank == other.rank and
        same_owner(self_, other)
    )
    # impl-end


def attr_lt(self_: Attr, other: Attr) -> bool:
    # pre-conditions-start
    Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Requires(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Ensures(Acc(other.rank, 1 / 4) and Acc(other.owned, 1 / 4) and Acc(other.okey, 1 / 4))  # type: ignore
    # Order by creation rank first; equal-rank owned attributes tie-break by
    # ownership then by lexicographic identity key.
    Ensures(Result() == lt_ref(self_, other))
    # post-conditions-end
    # impl-start
    if (
        self_.rank != other.rank or
        not self_.owned and not other.owned
    ):
        return self_.rank < other.rank
    elif self_.owned != other.owned:
        return not self_.owned  # the owner-less attribute precedes
    else:
        return lex_lt(self_.okey, other.okey)
    # impl-end


def attr_hash_key(self_: Attr) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self_.rank, 1 / 4) and Acc(self_.owned, 1 / 4) and Acc(self_.okey, 1 / 4))  # type: ignore
    # The hash key is the full identity: creation rank, ownership, and (when
    # owned) the identity key. So it depends on the owner, not the rank alone.
    Ensures(Result() == hash_ref(self_))
    # post-conditions-end
    # impl-start
    if self_.owned:
        return PSeq(self_.rank, 1) + self_.okey
    return PSeq(self_.rank, 0)
    # impl-end
