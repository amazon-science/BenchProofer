"""Twin-artifact model for django__django-13315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A form field that offers a choice of related rows narrows its offered options
  by a restriction. When that restriction spans a relational join, a single
  offered row can be matched by the restriction along SEVERAL distinct join
  paths, so the raw matching pass yields the same row more than once. The
  options a user is offered must NOT contain such repeats: a row that satisfies
  the restriction is offered EXACTLY ONCE.

  The behaviour pinned here is the relationship between the raw stream of
  restriction matches (a row identifier appears once per join path that
  satisfies the restriction, hence possibly several times) and the options the
  field exposes. The offered options are the DUPLICATE-FREE image of the raw
  matching stream:

    * membership is preserved -- a row is offered if and only if the raw
      matching pass produced it at least once (no genuinely-matching row is
      dropped, and no row that never matched is invented); and
    * no row identifier is offered more than once, however many join paths
      matched it.

  This duplicate-free image is captured exactly by `dedup` below: it keeps one
  representative of every value occurring in the stream and discards every
  repeat, so by construction the result has no duplicate and preserves
  membership.

A queryset is modelled as a `List[int]` of row identifiers (primary keys). The
raw matching pass -- applying the restriction across the join -- is the input
`matches`, in which a row identifier may repeat once per satisfying join path.
The offered options are the returned `List[int]`. `List[int]`/`PSeq` sequence
reasoning carries the specification; Nagini bans richer object graphs, and the
only property the result is observed through is its multiset of row identifiers
collapsed to a set (which row identifiers are offered, each at most once).

No callee is axiomatized: the change is pure collection logic (duplicate
elimination over the matching stream), modelled deeply over `List[int]` as the
front-recursive fold `dedup`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly callees: the behaviour is the duplicate-free image of the
# raw matching stream, modelled deeply over List[int] as the front-recursive
# fold `dedup`; there is no unchanged library callee whose Ensures the proof
# must consume.)
# axioms-end


# pure-start
@Pure
def occurs(v: int, s: PSeq[int]) -> bool:
    """Whether the row identifier `v` appears somewhere in `s`. Front-recursive
    over the sequence so a single membership unfold is available per step."""
    if len(s) == 0:
        return False
    return s[0] == v or occurs(v, s.drop(1))


@Pure
def dedup(s: PSeq[int]) -> PSeq[int]:
    """The duplicate-free image of `s`: keep exactly one representative of each
    distinct value and discard every repeat. Front-recursive (one unfold per
    element): a head that recurs later in the sequence is dropped here and kept
    at its later occurrence, so the result carries no value twice while every
    value present in `s` remains present."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if occurs(s[0], s.drop(1)):
        return dedup(s.drop(1))
    return PSeq(s[0]) + dedup(s.drop(1))
# pure-end


def offered_options(matches: List[int]) -> List[int]:
    # pre-conditions-start
    # The raw matching stream is read-only here (the narrowing reads it to build
    # a fresh options list; it does not mutate it). Fractional permission,
    # required AND ensured, so no caller can satisfy a postcondition vacuously by
    # overwriting the input.
    Requires(Acc(list_pred(matches), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(matches), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The offered options are exactly the duplicate-free image of the raw
    # matching stream: every value present in `matches` is offered (membership
    # preserved) and none is offered twice (`dedup` is duplicate-free by
    # construction). Returning the matching stream unchanged -- repeats and all
    # -- violates this whenever a row matched along more than one join path.
    Ensures(ToSeq(Result()) == dedup(ToSeq(matches)))
    # post-conditions-end
    # impl-start
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `dedup` (one unfold per step).
    result = []  # type: List[int]
    i = len(matches)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(matches), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(matches))
        Invariant(ToSeq(result) == dedup(ToSeq(matches).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(matches).drop(i - 1)[0] == matches[i - 1])
        Assert(ToSeq(matches).drop(i - 1).drop(1) == ToSeq(matches).drop(i))
        v = matches[i - 1]
        # Keep this row only if it does not recur later in the stream, so a row
        # matched along several join paths is offered exactly once.
        if occurs(v, ToSeq(matches).drop(i)):
            pass
        else:
            result = [v] + result
        i = i - 1
    return result
    # impl-end
