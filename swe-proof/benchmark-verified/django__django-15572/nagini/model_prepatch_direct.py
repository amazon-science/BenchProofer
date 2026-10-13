"""Twin-artifact model for django__django-15572.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A development-server watcher assembles the collection of on-disk locations it
  must observe for template changes. Each configured location is supplied as a
  raw entry that is first turned into a concrete watched location by joining it,
  relative, onto a constant base location (the current working directory). The base
  location itself is a perfectly ordinary location that may legitimately be
  observed for other reasons.

  An entry that carries NO location at all — the absent / empty entry — denotes
  no directory. Joining such an empty entry relative to the base collapses onto
  the base location itself, so an empty entry that is allowed through would make
  the watcher observe the entire base location indiscriminately. The desired
  behaviour is therefore: an entry contributes its joined watched location to
  the collection exactly when the entry is present (non-empty); an empty entry
  contributes nothing. The collection is precisely the joined locations of the
  present entries, in order.

  Two configured sources feed this collection:

    (1) the source list of entries declared directly on the watcher; an entry
        contributes exactly when it is present (non-empty);

    (2) the source list of entries declared by an auxiliary provider; an entry
        contributes exactly when it is present (non-empty) AND it does not lie
        beneath the framework's own installation tree (a deterministic
        provider-supplied predicate that this code does not change). The
        present-entry condition and the framework-tree condition are both
        required.

Raw entries are modelled as integer tokens: the reserved token ``0`` is the
empty entry, every other token is a present entry. Joining onto the base is the
pure map ``join_base`` (the empty entry collapses to the reserved base token
``0``; a present entry maps to a watched-location token, ``0`` reserved for the
base). The emitted collection is the ``List[int]`` filtered-then-mapped
subsequence of the present entries. ``beneath_framework`` is the unchanged
provider predicate.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def beneath_framework(entry: int) -> bool:
    """Unchanged auxiliary-provider predicate: whether a present entry lies
    beneath the framework's own installation tree. Deterministic function of the
    entry; the proof relies only on its being a deterministic Boolean of the
    entry (no value constraint is consumed). Provenance + executable soundness
    check: mapping.md / axiom_check.py.
    """
    pass
# axioms-end


# pure-start
@Pure
def is_present(entry: int) -> bool:
    """A raw entry carries a location exactly when it is not the reserved empty
    entry (token 0)."""
    return entry != 0


@Pure
def join_base(entry: int) -> int:
    """The watched location obtained by joining a raw entry, relative, onto the
    constant base location. The empty entry (token 0) collapses onto the base
    location itself (reserved location token 0). On the configured directory
    entries this code receives, a present entry carries its own watched-location
    token; the base token 0 stays reserved for the empty/base-collapsing case."""
    return entry


@Pure
def selected_direct(entries: PSeq[int]) -> PSeq[int]:
    """The watched locations contributed by the directly-declared source: the
    joined location of every present entry, in order; empty entries contribute
    nothing. Front-recursive so a single unfold is available to the loop."""
    if len(entries) == 0:
        return PSeq(0).take(0)
    if is_present(entries[0]):
        return PSeq(join_base(entries[0])) + selected_direct(entries.drop(1))
    return selected_direct(entries.drop(1))


@Pure
def selected_provider(entries: PSeq[int]) -> PSeq[int]:
    """The watched locations contributed by the auxiliary-provider source: the
    joined location of every entry that is present AND not beneath the
    framework tree, in order. Front-recursive so a single unfold is available to
    the loop."""
    if len(entries) == 0:
        return PSeq(0).take(0)
    if is_present(entries[0]) and not beneath_framework(entries[0]):
        return PSeq(join_base(entries[0])) + selected_provider(entries.drop(1))
    return selected_provider(entries.drop(1))
# pure-end


def collect_direct_locations(entries: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(entries), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The collection is exactly the joined locations of the present entries, in
    # order: an empty entry contributes nothing.
    Ensures(ToSeq(Result()) == selected_direct(ToSeq(entries)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(entries)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(entries), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(entries))
        Invariant(ToSeq(result) == selected_direct(ToSeq(entries).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        d = entries[i - 1]
        Assert(ToSeq(entries).drop(i - 1)[0] == d)
        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
        result = [d] + result
        i = i - 1
    return result
    # impl-end


def collect_provider_locations(entries: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(entries), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The collection is exactly the joined locations of the entries that are
    # present AND not beneath the framework tree, in order.
    Ensures(ToSeq(Result()) == selected_provider(ToSeq(entries)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(entries)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(entries), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(entries))
        Invariant(ToSeq(result) == selected_provider(ToSeq(entries).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        d = entries[i - 1]
        Assert(ToSeq(entries).drop(i - 1)[0] == d)
        Assert(ToSeq(entries).drop(i - 1).drop(1) == ToSeq(entries).drop(i))
        if d != 0 and not beneath_framework(d):
            result = [d] + result
        i = i - 1
    return result
    # impl-end
