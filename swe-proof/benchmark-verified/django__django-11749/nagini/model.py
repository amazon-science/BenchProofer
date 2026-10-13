"""Twin-artifact model for django__django-11749.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Before a command's option defaults are computed, the caller-supplied keyword
  options must be threaded through the option parser for every option whose
  presence the parser would otherwise INSIST on. An option's value, when the
  caller supplied it, is forwarded to the parser exactly when that option is
  one the parser obliges the caller to provide. An option is obliged when it
  is individually mandatory OR when it belongs to a set of alternatives of
  which the parser mandates that at least one be supplied. Forwarding preserves
  the parser's declaration order, and an option whose value the caller did not
  supply is never forwarded.

  Concretely: the forwarded sequence is the order-preserving sub-list of the
  declared options for which (the caller supplied this option) AND (the option
  is itself mandatory OR it is a member of a mandated set of alternatives).
  An option that is a member of a mandated alternative set but is not itself
  individually mandatory is still forwarded; the previous omission of such
  options is exactly the gap this contract closes.

Each declared option is modelled by an integer carrying three independent
boolean facts as separate low bits (Nagini bans richer object graphs in a
sequence): whether the caller supplied this option (`supplied`), whether the
option is individually mandatory (`mandatory`), and whether the option belongs
to a mandated set of alternatives (`in_mandated_set`). The forwarded result is
the order-preserving filter of the declared options under the forwarding
predicate, carried as `PSeq[int]` (the per-option formatted argument string is
the same on both sides of the change, so each forwarded option corresponds to
exactly one forwarded argument; only membership of the forwarded set changed).

No callee is axiomatized: the change is pure selection logic over the declared
options, modelled deeply. Markers (machine-parsed) delimit the spec / proof /
impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def supplied(a: int) -> bool:
    """The caller supplied a value for this option (its destination is present
    among the caller-supplied keyword options)."""
    return a % 2 == 1


@Pure
def mandatory(a: int) -> bool:
    """The option is individually mandatory."""
    return (a // 2) % 2 == 1


@Pure
def in_mandated_set(a: int) -> bool:
    """The option belongs to a set of alternatives of which at least one is
    mandated to be supplied."""
    return (a // 4) % 2 == 1


@Pure
def forward(a: int) -> bool:
    """An option's caller-supplied value is forwarded to the parser exactly when
    the caller supplied it AND it is obliged: either individually mandatory, or
    a member of a mandated set of alternatives."""
    return supplied(a) and (mandatory(a) or in_mandated_set(a))


@Pure
def forwarded_seq(s: PSeq[int]) -> PSeq[int]:
    """The forwarded options: the order-preserving sub-list of the declared
    options that satisfy `forward`. Front-recursive so a single unfold is
    available per declared option."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if forward(s[0]):
        return PSeq(s[0]) + forwarded_seq(s.drop(1))
    return forwarded_seq(s.drop(1))
# pure-end


def select_forwarded(actions: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(actions), 1 / 2))
    Requires(MustTerminate(len(actions) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(actions), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The forwarded options are exactly the order-preserving filter of the
    # declared options under the forwarding predicate.
    Ensures(ToSeq(Result()) == forwarded_seq(ToSeq(actions)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
            result = [a] + result
        i = i - 1
    return result
    # impl-end
