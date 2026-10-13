"""Twin-artifact model for scikit-learn__scikit-learn-14053.

Behaviour under specification (an abstract behavioural contract):

  A textual report of a fitted decision tree resolves a display name for every
  node of the tree from a caller-supplied table of feature names. Each node
  carries a feature selector: a node that selects a feature gives that
  feature's position in the name table; a node that selects no feature carries
  the reserved out-of-band selector value -2 instead of a table position.

  The per-node name resolution is a total function from the node selectors and
  the name table to a sequence of resolved entries, one per node, such that:

    (1) it is total over every node for a name table of any size;

    (2) a node whose selector is a position in the table resolves to exactly
        the table entry at that position; and

    (3) a node whose selector is -2 resolves to a dedicated placeholder
        distinct from any table entry (modelled as ``None``).

Feature names are abstracted to integer identifiers; the report observes only
*which* table entry is chosen at each node that selects a feature (and that the
remaining nodes carry the placeholder), not the spelling of the names.
Strings/arrays are therefore modelled as ``List[int]`` of identifiers (Nagini
bans ``str`` indexing); the specification is carried by ``PSeq`` pure sequences
via ``ToSeq``.

The resolved-name sequence is modelled deeply as a verified per-node fold
(``built_seq``); there are no axiomatized callees. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No callee is axiomatized: the resolution is modelled deeply as built_seq.)
# axioms-end


# pure-start
@Pure
def in_domain(names: PSeq[int], feat: PSeq[int]) -> bool:
    """The per-node selector array is well-formed: every node's selector is
    either the reserved out-of-band value -2 or a valid position in the name
    table. This is the genuine domain of the selector array (see mapping.md)."""
    return Forall(int, lambda j: (Implies(0 <= j and j < len(feat),
                feat[j] == -2 or (0 <= feat[j] and feat[j] < len(names)))))


@Pure
def built_seq(names: PSeq[int], feat: PSeq[int]) -> PSeq[Optional[int]]:
    """Resolved-name sequence, one entry per node, front-recursive so a single
    unfold is available per loop step. A node whose selector is a valid table
    position resolves to that table entry; every other node (in particular one
    carrying the reserved out-of-band value -2) resolves to the placeholder
    None."""
    none_val = None  # type: Optional[int]
    if len(feat) == 0:
        return PSeq(none_val).take(0)
    head = feat[0]  # type: int
    rest = built_seq(names, feat.drop(1))  # type: PSeq[Optional[int]]
    if head != -2 and 0 <= head and head < len(names):
        nm = names[head]  # type: Optional[int]
        return PSeq(nm) + rest
    return PSeq(none_val) + rest
# pure-end


def resolve_node_names(names: List[int], feat: List[int]) -> List[Optional[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(feat), 1 / 2))
    Requires(in_domain(ToSeq(names), ToSeq(feat)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(feat), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # One resolved name per node.
    Ensures(len(Result()) == len(feat))
    # The resolved sequence is the per-node fold: a node selecting a table
    # position resolves to that table entry, and a node carrying the reserved
    # out-of-band value -2 (or any non-position selector) resolves to None.
    Ensures(ToSeq(Result()) == built_seq(ToSeq(names), ToSeq(feat)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[Optional[int]]
    i = len(feat)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(feat), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(feat))
        Invariant(in_domain(ToSeq(names), ToSeq(feat)))
        Invariant(len(result) == len(feat) - i)
        Invariant(ToSeq(result) == built_seq(ToSeq(names), ToSeq(feat).drop(i)))
        # invariants-end
        fi = feat[i - 1]
        Assert(ToSeq(feat).drop(i - 1)[0] == fi)
        Assert(ToSeq(feat).drop(i - 1).drop(1) == ToSeq(feat).drop(i))
        if fi != -2:
            nm = names[fi]  # type: Optional[int]
            result = [nm] + result
        else:
            none_val = None  # type: Optional[int]
            result = [none_val] + result
        i = i - 1
    return result
    # impl-end
