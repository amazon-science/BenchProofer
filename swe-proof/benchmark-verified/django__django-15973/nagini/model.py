"""Twin-artifact model for django__django-15973.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relational field contributes the migration dependencies that the field's
  references demand. Such a field always references a primary related object;
  some fields additionally route the relation through a SECOND, intermediary
  object. Each reference is an "app.Object" token that is resolved to an
  (app_label, object_name) pair by the shared reference resolver: the text
  before the first dot is the app label (verbatim), and the text after it is
  the object name, normalised to lower case.

  The contributed dependencies are:

    * one dependency derived from the PRIMARY reference, and
    * when an intermediary reference is supplied, a SECOND dependency derived
      from THAT intermediary reference -- NOT from the primary one.

  The two references are independent tokens that may name objects in different
  apps; the intermediary dependency must therefore resolve the intermediary
  reference's own app label and object name, so that a relation routed through
  an object in a different app records a dependency on that other app.

The "app.Object" reference tokens are modelled as `List[int]` of Unicode code
points (Nagini bans `str` indexing); resolution is carried by the pure sequence
theory `PSeq[int]`. The reference resolver is modelled DEEPLY as the dot-split
plus lower-casing fold (`ref_app` / `ref_name`), whose equality to the real
resolver is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def lower_cp(c: int) -> int:
    """Lower-case a single code point: ASCII 'A'..'Z' (65..90) map to
    'a'..'z' (97..122); every other code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def dot_index(ref: PSeq[int], i: int) -> int:
    """Index of the first '.' (code point 46) at or after position `i`, or
    `len(ref)` if none. Front-recursive so one unfold is available per step."""
    Requires(0 <= i and i <= len(ref))
    Ensures(i <= Result() and Result() <= len(ref))
    if i == len(ref):
        return i
    if ref[i] == 46:
        return i
    return dot_index(ref, i + 1)


@Pure
def ref_app(ref: PSeq[int]) -> PSeq[int]:
    """App label of a reference token: the prefix before the first dot,
    verbatim (no case change)."""
    return ref.take(dot_index(ref, 0))


@Pure
def lowered(s: PSeq[int]) -> PSeq[int]:
    """Lower-cased sequence: each code point through `lower_cp`. Front-recursive
    so a single unfold is available per fold/loop step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(lower_cp(s[0])) + lowered(s.drop(1))


@Pure
def ref_name(ref: PSeq[int]) -> PSeq[int]:
    """Object name of a reference token: the suffix after the first dot,
    lower-cased."""
    return lowered(ref.drop(dot_index(ref, 0) + 1))
# pure-end


def through_dependency(primary_ref: List[int], through_ref: List[int]
                       ) -> Tuple[List[int], List[int]]:
    """The (app_label, object_name) of the dependency contributed for a
    relation routed through an intermediary object.

    `primary_ref` is the field's primary related reference; `through_ref` is
    the intermediary reference. Both are read-only "app.Object" tokens.
    """
    # pre-conditions-start
    # Both references are read-only: this computation derives a dependency from
    # them but mutates neither (directive 5: fractional permission).
    Requires(Acc(list_pred(primary_ref), 1 / 2))
    Requires(Acc(list_pred(through_ref), 1 / 2))
    # An "app.Object" reference token carries a dot separating the two parts.
    Requires(dot_index(ToSeq(through_ref), 0) < len(through_ref))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(primary_ref), 1 / 2))
    Ensures(Acc(list_pred(through_ref), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The intermediary dependency resolves the INTERMEDIARY reference's own app
    # label and (lower-cased) object name -- never the primary reference's.
    # This is the discriminating clause: when the two references name objects
    # in different apps, the dependency must point at the intermediary's app.
    Ensures(ToSeq(Result()[0]) == ref_app(ToSeq(through_ref)))
    Ensures(ToSeq(Result()[1]) == ref_name(ToSeq(through_ref)))
    # post-conditions-end
    # impl-start
    app = []  # type: List[int]
    name = []  # type: List[int]
    # locate the first dot of the intermediary reference
    d = 0
    while d < len(through_ref) and through_ref[d] != 46:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(0 <= d and d <= len(through_ref))
        # the reference carries a dot (a stable fact about the unchanged input)
        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
        # scanning past non-dots does not change the first-dot index
        Invariant(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), 0))
        # Termination: the guard's FIRST conjunct `d < len(through_ref)` alone
        # bounds the scan -- `d` rises by exactly 1 per pass and
        # `len(through_ref)` is fixed (the input is only read), so
        # `len(through_ref) - d + 1` strictly decreases and is >= 2 at every
        # loop head. The second conjunct `through_ref[d] != 46` can only make
        # the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(through_ref) - d + 1))
        # invariants-end
        # ref[d] != 46, so the first dot from d equals the first dot from d+1
        Assert(dot_index(ToSeq(through_ref), d) == dot_index(ToSeq(through_ref), d + 1))
        d = d + 1
    # at exit either d == len(through_ref) or through_ref[d] == 46; both give
    # dot_index(.., d) == d, hence the first dot index is d
    Assert(dot_index(ToSeq(through_ref), d) == d)
    Assert(d == dot_index(ToSeq(through_ref), 0))
    # app label: prefix before the dot (verbatim)
    j = 0
    while j < d:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(app)))
        Invariant(d == dot_index(ToSeq(through_ref), 0))
        Invariant(dot_index(ToSeq(through_ref), 0) < len(through_ref))
        Invariant(0 <= j and j <= d)
        Invariant(ToSeq(app) == ToSeq(through_ref).take(d).take(j))
        # Termination: `j` rises by exactly 1 per pass and `d` is fixed inside
        # this loop, so `d - j + 1` strictly decreases; the guard `j < d` makes
        # it >= 2 at every loop head.
        Invariant(MustTerminate(d - j + 1))
        # invariants-end
        Assert(ToSeq(through_ref).take(d)[j] == through_ref[j])
        app = app + [through_ref[j]]
        Assert(ToSeq(app) == ToSeq(through_ref).take(d).take(j + 1))
        j = j + 1
    Assert(ToSeq(app) == ToSeq(through_ref).take(d))
    # the app label equals the deep-model resolver's app projection
    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
    # object name: lower-cased suffix after the dot
    Assert(dot_index(ToSeq(through_ref), 0) < len(through_ref))
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(d < len(through_ref))
    k = len(through_ref)
    while k > d + 1:
        # invariants-start
        Invariant(Acc(list_pred(through_ref), 1 / 2))
        Invariant(Acc(list_pred(name)))
        Invariant(Acc(list_pred(app)))
        Invariant(d == dot_index(ToSeq(through_ref), 0))
        # the app label, fully built, equals the resolver's app projection
        Invariant(ToSeq(app) == ref_app(ToSeq(through_ref)))
        Invariant(d + 1 <= k and k <= len(through_ref))
        Invariant(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1))))
        # Termination: `k` falls by exactly 1 per pass down towards the fixed
        # floor `d + 1`, so `k - d` strictly decreases; the guard `k > d + 1`
        # makes it >= 2 at every loop head.
        Invariant(MustTerminate(k - d))
        # invariants-end
        c = through_ref[k - 1]
        Assert(ToSeq(through_ref).drop(d + 1)[k - (d + 1) - 1] == c)
        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1)[0] == c)
        Assert(ToSeq(through_ref).drop(d + 1).drop(k - (d + 1) - 1).drop(1)
               == ToSeq(through_ref).drop(d + 1).drop(k - (d + 1)))
        name = [lower_cp(c)] + name
        k = k - 1
    Assert(ToSeq(name) == lowered(ToSeq(through_ref).drop(d + 1)))
    # connect the spelled-out parts to the deep-model reference resolver
    Assert(d == dot_index(ToSeq(through_ref), 0))
    Assert(ref_app(ToSeq(through_ref)) == ToSeq(through_ref).take(dot_index(ToSeq(through_ref), 0)))
    Assert(ref_name(ToSeq(through_ref)) == lowered(ToSeq(through_ref).drop(dot_index(ToSeq(through_ref), 0) + 1)))
    Assert(ToSeq(app) == ref_app(ToSeq(through_ref)))
    Assert(ToSeq(name) == ref_name(ToSeq(through_ref)))
    res = (app, name)  # type: Tuple[List[int], List[int]]
    Assert(ToSeq(res[0]) == ref_app(ToSeq(through_ref)))
    Assert(ToSeq(res[1]) == ref_name(ToSeq(through_ref)))
    return res
    # impl-end
