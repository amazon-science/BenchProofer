"""Twin-artifact model for django__django-11555.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the columns to order a query by are derived from a related model's
  default ordering, that default ordering is a sequence of items, and each
  item is of one of two kinds:

    * a column-reference item given as a name (a textual field path), which is
      expanded by the same name-resolution machinery used for every other
      column name into a sequence of zero or more concrete ordering targets;
      and

    * an item that is ALREADY a fully-formed ordering expression, supplied
      directly rather than as a name.

  The desired behaviour is that the expansion of the default ordering yields,
  in order, the concatenation of each item's contribution, where:

    * a name item contributes exactly the targets the name-resolution
      machinery produces for that name; and

    * an already-formed ordering-expression item contributes EXACTLY ITSELF,
      as a single target, passed through verbatim. It is NOT handed to the
      name-resolution machinery (which is defined only for textual names);
      its identity appears in the output unchanged and in its original
      position.

  The name-resolution machinery is a PARTIAL and STATE-CHANGING operation, not
  a free function of its argument: it is defined only for textual names, and
  each invocation advances the shared resolution state it threads through (the
  bookkeeping that detects cyclic ordering and accumulates the joins the query
  needs). Which items it is invoked ON is therefore part of the specified
  behaviour, not an implementation detail: expanding a default ordering
  invokes it EXACTLY ONCE PER NAME ITEM AND NEVER ON AN ALREADY-FORMED
  ORDERING EXPRESSION. Producing the right sequence of targets by a route that
  invokes the machinery on an already-formed expression, or more than once for
  a name, is NOT the desired behaviour even when the targets come out equal.

  There is only ONE resolution state, the shared one the expansion is handed;
  the machinery cannot be applied off to the side against a private one. So
  "invoked on" admits no loophole: every application of the machinery, whatever
  route reaches it, lands in the one account the behaviour above constrains.

The default ordering is modelled by two index-aligned ``List[int]``: a kind
tag per item (1 = already-formed ordering expression, 0 = name) and an identity
tag per item. The output is modelled as the ``List[int]`` of target identity
tags it produces. The unchanged name-resolution machinery (the recursive
resolution of one textual name into its targets) is axiomatized as a single
opaque callee, taking the shared resolution state it advances; the pass-through
of an already-formed expression is modelled deeply as the singleton of that
item's own identity. The shared resolution state is an OPAQUE RESOURCE with no
constructor — an expansion holds the one it was given and no other — and the
multiset of items the machinery has been applied to against it is observable,
so the spec constrains the invocations as well as the returned targets.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Predicate
@ContractOnly
def machinery_state(state: List[int]) -> bool:
    """The shared resolution state the name-resolution machinery threads
    through its recursion (the bookkeeping that detects cyclic ordering and the
    accumulated joins the query needs).

    Held as an OPAQUE RESOURCE: it has no body and there is no way to bring one
    into existence. An expansion therefore holds exactly the one shared state it
    is handed, and every invocation of the machinery it performs is an
    invocation on THAT state. There is no such thing as a private resolution
    state to resolve a name against on the side: the machinery always advances
    the one shared bookkeeping, so no invocation can be made off to the side and
    kept out of the account below. Provenance: mapping.md / axiom_check.py."""


@Pure
@ContractOnly
def invocations(state: List[int]) -> PMultiset[int]:
    """The items the name-resolution machinery has been invoked on so far,
    against this shared resolution state, as a MULTISET of item identities: it
    observes WHICH items were resolved and HOW MANY TIMES each, but not the
    order they were walked in. Reading it needs the state resource, and the only
    thing that changes it is an invocation of the machinery."""
    Requires(machinery_state(state))


@Pure
@ContractOnly
def resolve_name_seq(item_id: int) -> PSeq[int]:
    """The unchanged name-resolution machinery applied to one textual-name
    item, as a pure sequence of target identities (possibly empty, possibly
    several). Opaque; defined only for textual names. Pinned so that the
    impl-callable ``resolve_name`` produces exactly this sequence. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(True)


@ContractOnly
def resolve_name(state: List[int], item_id: int) -> List[int]:
    """The unchanged name-resolution machinery applied to one textual-name
    item, returning a freshly produced list of target identities. The same
    callee the resolution recurses through for every textual name.

    It is STATE-CHANGING: it consumes and returns the shared resolution state,
    and that state records this invocation against the item it was applied to.
    An invocation cannot be hidden, undone, or obtained on anything other than
    the shared state."""
    Requires(machinery_state(state))
    Requires(MustTerminate(2))
    Ensures(machinery_state(state))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == resolve_name_seq(item_id))
    # This invocation is recorded against the item it was applied to.
    Ensures(invocations(state) == Old(invocations(state)) + PMultiset(item_id))
# axioms-end


# pure-start
@Pure
def contribution(kind: int, item_id: int) -> PSeq[int]:
    """The targets one default-ordering item contributes to the output.

    A name item (kind 0) contributes the name-resolution of its identity; an
    already-formed ordering-expression item (kind 1) contributes exactly
    itself, as a single target carrying its own identity."""
    if kind == 1:
        return PSeq(item_id)
    return resolve_name_seq(item_id)


@Pure
def expanded(kinds: PSeq[int], ids: PSeq[int]) -> PSeq[int]:
    """Expansion of a whole default ordering: the front-to-back concatenation
    of each item's contribution. Front-recursive so a single unfold is
    available per loop step. Defensive on length so it carries no precondition
    (the two carriers are consumed in lock-step by the caller)."""
    if len(kinds) == 0 or len(ids) == 0:
        return PSeq(0).take(0)
    return contribution(kinds[0], ids[0]) + expanded(kinds.drop(1), ids.drop(1))


@Pure
def name_items(kinds: PSeq[int], ids: PSeq[int]) -> PMultiset[int]:
    """The items the name-resolution machinery is to be invoked on while
    expanding a default ordering, as a MULTISET of item identities: every name
    item exactly once, and no already-formed ordering expression. A multiset
    rather than a sequence, so the obligation pins WHICH items and HOW MANY
    TIMES each is resolved without constraining the order the items are walked
    in — an implementation may expand the ordering in either direction."""
    if len(kinds) == 0 or len(ids) == 0:
        return ToMS(PSeq(0).take(0))
    if kinds[0] == 1:
        return name_items(kinds.drop(1), ids.drop(1))
    return PMultiset(ids[0]) + name_items(kinds.drop(1), ids.drop(1))
# pure-end


def expand_default_ordering(kinds: List[int], ids: List[int],
                            state: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Acc(list_pred(ids), 1 / 2))
    Requires(machinery_state(state))
    Requires(len(kinds) == len(ids))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(ids), 1 / 2))
    Ensures(machinery_state(state))
    Ensures(Acc(list_pred(Result())))
    # The output is exactly the concatenation of each item's contribution.
    Ensures(ToSeq(Result()) == expanded(ToSeq(kinds), ToSeq(ids)))
    # The name-resolution machinery is invoked exactly once per name item and
    # never on an already-formed ordering expression: the invocations the
    # shared resolution state has accumulated are precisely the name items.
    Ensures(invocations(state)
            == Old(invocations(state)) + name_items(ToSeq(kinds), ToSeq(ids)))
    # post-conditions-end
    # impl-start
    inv0 = invocations(state)  # type: PMultiset[int]
    result = []  # type: List[int]
    i = len(kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(Acc(list_pred(ids), 1 / 2))
        Invariant(machinery_state(state))
        Invariant(len(kinds) == len(ids))
        Invariant(0 <= i and i <= len(kinds))
        Invariant(Acc(list_pred(result)))
        Invariant(ToSeq(result) == expanded(ToSeq(kinds).drop(i), ToSeq(ids).drop(i)))
        Invariant(invocations(state)
                  == inv0 + name_items(ToSeq(kinds).drop(i), ToSeq(ids).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        k = kinds[i - 1]
        d = ids[i - 1]
        Assert(ToSeq(kinds).drop(i - 1)[0] == k)
        Assert(ToSeq(ids).drop(i - 1)[0] == d)
        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
        Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))
        if k == 1:
            # An already-formed ordering expression: pass it through verbatim
            # as a single target carrying its own identity. The name-resolution
            # machinery is not invoked for it.
            piece = [d]  # type: List[int]
        else:
            # A textual name: expand it through the name-resolution machinery,
            # advancing the shared resolution state exactly once.
            piece = resolve_name(state, d)
        Assert(ToSeq(piece) == contribution(k, d))
        result = piece + result
        i = i - 1
    return result
    # impl-end
