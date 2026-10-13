"""Twin-artifact model for pytest-dev__pytest-7982.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A directory walk inspects the ordered entries of one directory level. For
  each entry it must decide whether to descend into that entry's own contents.
  The walk descends into an entry exactly when BOTH hold:

    * the entry resolves to a directory -- this is true not only for a plain
      directory but also for a link whose target is a directory (the link is
      followed when classifying it), and false for a non-directory entry or a
      link whose target is not a directory; and
    * a caller-supplied recursion predicate selects that entry.

  In particular, a link that points at a directory is treated as a directory
  for the purpose of descending: when such a link is selected by the predicate
  the walk descends into it, just as it would for a plain directory. A link to
  a non-directory, and any non-directory entry, is never descended into.

Each directory level is modelled as two parallel pure sequences: `kinds[i]`
classifies entry `i` and `selected[i]` is the caller predicate's verdict for
entry `i`. The classification carrier uses four codes:

    0 = a non-directory entry (e.g. a regular file)
    1 = a plain directory
    2 = a link whose target is a directory
    3 = a link whose target is not a directory (or that resolves to none)

The decision "this entry resolves to a directory" is modelled DEEPLY as the
pure predicate `resolves_to_dir` (codes 1 and 2); its equality to the real
filesystem classification callee is checked out-of-band by axiom_check.py
(G-AX), NOT consumed as an axiom. Pure sequences carry no heap permission, so
the inputs are read-only by construction and the specification quantifies over
their elements directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axiom: the "resolves to a directory" classification
#  is modelled deeply below as `resolves_to_dir` and validated == the real
#  filesystem classification callee out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def resolves_to_dir(kind: int) -> bool:
    """Whether an entry of the given classification code resolves to a
    directory. A plain directory (1) does; a link whose target is a directory
    (2) also does, because the link is followed when classifying it; a
    non-directory entry (0) and a link to a non-directory (3) do not."""
    return kind == 1 or kind == 2


@Pure
def should_descend(kind: int, selected: bool) -> bool:
    """The per-entry descent decision: descend exactly when the entry resolves
    to a directory AND the caller predicate selected it."""
    return resolves_to_dir(kind) and selected
# pure-end


def descend_decisions(kinds: PSeq[int], selected: PSeq[bool]) -> PSeq[bool]:
    # pre-conditions-start
    # The two parallel views describe the same entries, one verdict each.
    Requires(len(kinds) == len(selected))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # One decision per entry, in order.
    Ensures(len(Result()) == len(kinds))
    # Each decision is exactly "resolves to a directory AND selected": a
    # link-to-directory (code 2) that is selected IS descended into, exactly as
    # a plain directory (code 1) is; a non-directory (0) or link-to-non-dir (3)
    # is never descended into.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
        Result()[i] == should_descend(kinds[i], selected[i])),
        [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    result = PSeq(True).take(0)  # type: PSeq[bool]
    i = 0
    n = len(kinds)
    while i < n:
        # invariants-start
        Invariant(len(kinds) == len(selected))
        Invariant(n == len(kinds))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == should_descend(kinds[k], selected[k])),
            [[result[k]]])))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        # Classify the entry by following any link to its target, then require
        # the caller predicate to have selected it.
        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
        Assert(decision == should_descend(kinds[i], selected[i]))
        old_result = result  # type: PSeq[bool]
        result = result + PSeq(decision)
        Assert(len(result) == i + 1)
        Assert(result[i] == decision)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == old_result[k]), [[result[k]]])))
        i = i + 1
    return result
    # impl-end
