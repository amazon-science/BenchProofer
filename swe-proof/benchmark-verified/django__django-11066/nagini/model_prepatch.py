"""Twin-artifact model for django__django-11066.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A persistence step is given two things: an explicitly named target data
  store (an alias that is always present) and the alias that an external
  write-routing policy would otherwise select. The persisted-to data store
  must be the EXPLICITLY NAMED one, so that the write lands in the store the
  caller named rather than wherever an independent routing policy would send
  it. The routing policy is consulted only as a fallback, when no explicit
  store is named at all.

  Concretely: the resolved target is the explicit alias when one is present
  (which it always is here), and equals it regardless of which alias the
  routing policy would have chosen — even when the policy would pick a
  different store.

Connection aliases are modelled as `List[int]` of Unicode code points (Nagini
bans `str` indexing); equality of two aliases is `PSeq[int]` equality. The
routing policy's choice is modelled as a free input alias, because the policy
is wholly independent of the explicitly named store and may select any alias.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the resolution is modelled deeply; the routing policy's choice is a
# free input alias `routed`, an A-reference validated by axiom_check.py, not a
# consumed @ContractOnly. See refinement.md / mapping.md §3.)
# axioms-end


# pure-start
@Pure
def alias_eq(a: PSeq[int], b: PSeq[int]) -> bool:
    """Two connection aliases denote the same data store iff their code-point
    sequences are equal."""
    return a == b
# pure-end


def persisted_db(db: List[int], routed: List[int]) -> List[int]:
    # pre-conditions-start
    # `db` is the explicitly named target alias and is always present
    # (non-empty); `routed` is the alias the external routing policy would
    # otherwise pick — an arbitrary present alias, read-only here.
    Requires(Acc(list_pred(db), 1 / 2))
    Requires(Acc(list_pred(routed), 1 / 2))
    Requires(len(db) > 0)
    Requires(len(routed) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(db), 1 / 2))
    Ensures(Acc(list_pred(routed), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The write is committed to the EXPLICITLY NAMED store — its alias equals
    # `db` — no matter what the routing policy would have chosen.
    Ensures(alias_eq(ToSeq(Result()), ToSeq(db)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): no explicit alias is supplied, so `using` is absent
    # and the resolution `using or routing_policy_choice` ALWAYS falls through
    # to the routing policy. The write target is therefore `routed`, not `db`.
    src = routed  # type: List[int]
    # Copy the chosen alias into a fresh result carrier.
    target = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(db), 1 / 2))
        Invariant(Acc(list_pred(routed), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(len(db) > 0)
        Invariant(ToSeq(src) == ToSeq(routed))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(target) == ToSeq(src).take(i))
        # invariants-end
        target = target + [src[i]]
        Assert(ToSeq(src).take(i) + PSeq(src[i]) == ToSeq(src).take(i + 1))
        i = i + 1
    return target
    # impl-end
