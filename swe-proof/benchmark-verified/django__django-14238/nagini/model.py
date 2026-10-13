"""Twin-artifact model for django__django-14238.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A metaclass maintains a small, immutable family of registered "generated-key"
  base classes and answers the structural-subtype question for the type it is
  attached to.  Given a candidate class, the membership test must report TRUE
  exactly when the candidate stands in the subtype relation to AT LEAST ONE of
  the registered base classes, OR when the candidate is a subtype of the
  attached type itself by the ordinary class hierarchy.

  Crucially, this is a *subtype* relation, not an identity check: a candidate
  that derives (transitively) from one of the registered bases must be reported
  as a member even when the candidate is not itself one of those exact base
  classes.  Equivalently, the relation is reflexive and downward-closed under
  inheritance from the registered bases, so a user-defined class extending a
  registered base is recognised just as the base itself is.

A class is modelled abstractly by its identity together with the set of the
identities of all the classes it derives from (its ancestry, which by the
reflexivity of the subtype relation contains its own identity).  The subtype
relation `is_subtype(c, b)` holds iff `b`'s identity lies in `c`'s ancestry —
exactly the semantics of the ordinary `issubclass` query, which the membership
test consults against each registered base.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Cls:
    """A class abstracted by its identity `cid` and the set `anc` of identities
    of all classes it derives from (its ancestry).  The subtype relation is
    reflexive, so `cid in anc` always holds."""

    def __init__(self, cid: int, anc: PSet[int]) -> None:
        Requires(cid in anc)
        Ensures(Acc(self.cid) and Acc(self.anc))  # type: ignore
        Ensures(self.cid == cid and self.anc is anc)  # type: ignore
        Ensures(self.cid in self.anc)  # type: ignore
        self.cid = cid  # type: ignore
        self.anc = anc  # type: ignore


# axioms-start
# (No axiomatized callees: the structural-subtype query is modelled deeply.)
# axioms-end


# pure-start
@Pure
def is_subtype(sub: Cls, base: Cls) -> bool:
    """The ordinary structural-subtype query: `sub` is a subtype of `base` iff
    `base`'s identity lies in `sub`'s ancestry.  Reflexive (every class is its
    own subtype) and transitive by construction of the ancestry set."""
    Requires(Acc(sub.cid, 1 / 8) and Acc(sub.anc, 1 / 8))  # type: ignore
    Requires(Acc(base.cid, 1 / 8) and Acc(base.anc, 1 / 8))  # type: ignore
    return base.cid in sub.anc  # type: ignore
# pure-end


def subclass_check(owner: Cls, base_one: Cls, base_two: Cls, candidate: Cls) -> bool:
    # pre-conditions-start
    Requires(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
    Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
    Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
    Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
    Ensures(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
    Ensures(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
    Ensures(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
    # The decision is TRUE iff the candidate is a subtype of either registered
    # base or of the attached type itself.  Membership in the registered family
    # is by the subtype relation, NOT by identity with an exact base class.
    Ensures(Result() == (is_subtype(candidate, base_one)
                         or is_subtype(candidate, base_two)
                         or is_subtype(candidate, owner)))
    # post-conditions-end
    # impl-start
    if is_subtype(candidate, base_one):
        return True
    if is_subtype(candidate, base_two):
        return True
    return is_subtype(candidate, owner)
    # impl-end
