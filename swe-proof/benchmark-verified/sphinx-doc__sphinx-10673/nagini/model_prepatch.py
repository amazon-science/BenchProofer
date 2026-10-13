"""Twin-artifact model for sphinx-doc__sphinx-10673.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A document-tree directive lists, in order, a sequence of target document
  names. Each target is classified against the set of names the project knows
  about. The project knows two disjoint families of names:

    * the names of the ordinary source documents that were discovered, and
    * the names of the auto-built reference pages (a general index, a module
      index and a full-text search page) that the standard domain always
      provides even though no source file with that name exists.

  A listed target is RETAINED (kept in the resulting ordered entry list) when
  its name belongs to EITHER family; a target whose name belongs to neither is
  rejected (it names no document at all). The auto-built reference pages must be
  retainable exactly like ordinary documents: a target naming one of them is
  kept even though it is absent from the discovered-source family.

Names are modelled as integer identifiers (each distinct document name is a
distinct int); the two families and the listed targets are `List[int]`, and the
specification is carried by the pure sequence theory `PSeq[int]`. Membership and
the order-preserving retention filter are spelled out deeply as front-recursive
folds (a single unfold per loop step), so no membership oracle is consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the classification is modelled deeply over PSeq[int]; there is no
#  consumed @ContractOnly callee.)
# axioms-end


# pure-start
@Pure
def mem(x: int, s: PSeq[int]) -> bool:
    """Whether `x` occurs in `s`. Front-recursive so a single unfold is
    available per loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or mem(x, s.drop(1))


@Pure
def known(x: int, found: PSeq[int], gen: PSeq[int]) -> bool:
    """A target name is known when it belongs to either family — the discovered
    documents OR the always-provided reference pages."""
    return mem(x, found) or mem(x, gen)


@Pure
def kept(entries: PSeq[int], found: PSeq[int], gen: PSeq[int]) -> PSeq[int]:
    """The order-preserving sublist of `entries` whose names are known.
    Front-recursive: the head is emitted iff it is known, then recurse."""
    if len(entries) == 0:
        return PSeq(0).take(0)
    if known(entries[0], found, gen):
        return PSeq(entries[0]) + kept(entries.drop(1), found, gen)
    return kept(entries.drop(1), found, gen)
# pure-end


def select_toctree_entries(entries: List[int], found: List[int],
                           generated: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(entries), 1 / 2))
    Requires(Acc(list_pred(found), 1 / 2))
    Requires(Acc(list_pred(generated), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Acc(list_pred(found), 1 / 2))
    Ensures(Acc(list_pred(generated), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The retained entries are exactly those listed targets whose name belongs
    # to the discovered documents OR the always-provided reference pages,
    # in their original order.
    Ensures(ToSeq(Result()) ==
            kept(ToSeq(entries), ToSeq(found), ToSeq(generated)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(entries)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(entries), 1 / 2))
        Invariant(Acc(list_pred(found), 1 / 2))
        Invariant(Acc(list_pred(generated), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(entries))
        Invariant(ToSeq(result) ==
                  kept(ToSeq(entries).drop(i), ToSeq(found), ToSeq(generated)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # PRE-PATCH BUG: classify the head target against the discovered-source
        # family ALONE (the always-provided reference pages are not consulted),
        # so a target naming a reference page is dropped.
        x = entries[i - 1]
        Assert(ToSeq(entries).drop(i - 1)[0] == x)
        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
        # cons-decomposition of the non-empty sequence entries.drop(i-1):
        Assert(PSeq(x) == PSeq(ToSeq(entries).drop(i - 1)[0]))
        Assert(ToSeq(entries).drop(i - 1) ==
               PSeq(ToSeq(entries).drop(i - 1)[0]) +
               ToSeq(entries).drop(i - 1).drop(1))
        cons = PSeq(x) + ToSeq(entries).drop(i)
        Assert(cons[0] == x)
        Assert(cons.drop(1) == ToSeq(entries).drop(i))
        Assert(ToSeq(entries).drop(i - 1) == cons)
        if mem(x, ToSeq(found)):
            # head is known: kept unfolds to PSeq(x) + kept(tail)
            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
                   PSeq(x) + kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
            Assert(kept(ToSeq(entries).drop(i - 1),
                        ToSeq(found), ToSeq(generated)) ==
                   PSeq(x) + kept(ToSeq(entries).drop(i),
                                  ToSeq(found), ToSeq(generated)))
            old_seq = ToSeq(result)
            result = [x] + result
            Assert(ToSeq(result) == PSeq(x) + old_seq)
        else:
            # head is unknown: kept unfolds to just kept(tail)
            Assert(kept(cons, ToSeq(found), ToSeq(generated)) ==
                   kept(cons.drop(1), ToSeq(found), ToSeq(generated)))
            Assert(kept(ToSeq(entries).drop(i - 1),
                        ToSeq(found), ToSeq(generated)) ==
                   kept(ToSeq(entries).drop(i),
                        ToSeq(found), ToSeq(generated)))
        Assert(ToSeq(result) ==
               kept(ToSeq(entries).drop(i - 1), ToSeq(found), ToSeq(generated)))
        i = i - 1
    return result
    # impl-end
