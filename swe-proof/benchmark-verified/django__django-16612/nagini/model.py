"""Twin-artifact model for django__django-16612.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a known administrative endpoint is requested without its mandatory
  trailing slash and trailing-slash appension is enabled, the permanent
  redirect must point at the *full* requested location with the slash added:
  the original location, then a single trailing "/" (added only when the
  location does not already end in one), then the request's query component
  reproduced verbatim and introduced by "?" whenever a query component is
  present. A request that carries no query component redirects to the
  slash-completed location alone.

  The essential property is that the query component is NOT discarded: the
  redirect target ends with "?" followed by the original query characters
  exactly when the request had a non-empty query, and the slash separating
  location from query is placed before the "?".

Locations and query components are modelled as `List[int]` of Unicode code
points (Nagini bans `str` indexing); the specification is carried by the pure
sequence theory `PSeq[int]` via `ToSeq`. For the locations and query
components exercised here the percent-encoding/IRI-to-URI normalisation of the
location and query characters is the identity on character content (see
mapping.md), so the redirect target is exactly this concatenation.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def ends_with_slash(s: PSeq[int]) -> bool:
    """True iff the sequence is non-empty and its last code point is '/'."""
    return len(s) > 0 and s[len(s) - 1] == 47


@Pure
def slash_part(path: PSeq[int]) -> PSeq[int]:
    """The single "/" separator, present unless the location already ends in
    one (an empty location also receives the slash)."""
    if ends_with_slash(path):
        return PSeq(47).take(0)
    return PSeq(47)


@Pure
def query_part(query: PSeq[int]) -> PSeq[int]:
    """The query component of the target: empty when there is no query, else
    "?" followed by the query characters verbatim."""
    if len(query) == 0:
        return PSeq(63).take(0)
    return PSeq(63) + query


@Pure
def redirect_target(path: PSeq[int], query: PSeq[int]) -> PSeq[int]:
    """The full slash-completed redirect target: location, then the trailing
    slash separator, then the (possibly empty) query component."""
    return path + slash_part(path) + query_part(query)
# pure-end


def build_append_slash_redirect(path: List[int], query: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(Acc(list_pred(query), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(path), 1 / 2))
    Ensures(Acc(list_pred(query), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The target is location ++ slash ++ query, all reproduced verbatim.
    Ensures(ToSeq(Result()) == redirect_target(ToSeq(path), ToSeq(query)))
    # The query characters are carried through unchanged and never dropped:
    # a non-empty query appears verbatim at the tail, introduced by "?".
    Ensures(Implies(len(query) > 0,
                    ToSeq(Result()) == ToSeq(path) + slash_part(ToSeq(path))
                    + PSeq(63) + ToSeq(query)))
    # An absent query produces only the slash-completed location.
    Ensures(Implies(len(query) == 0,
                    ToSeq(Result()) == ToSeq(path) + slash_part(ToSeq(path))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    m = len(path)
    n = len(query)
    Assert(len(ToSeq(query)) == n)
    Assert(len(ToSeq(path)) == m)
    i = 0
    while i < m:
        # invariants-start
        Invariant(Acc(list_pred(path), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(m == len(path))
        Invariant(0 <= i and i <= m)
        Invariant(ToSeq(result) == ToSeq(path).take(i))
        Invariant(MustTerminate(m - i + 1))
        # invariants-end
        result = result + [path[i]]
        i = i + 1
    Assert(ToSeq(path).take(m) == ToSeq(path))
    if not (m > 0 and path[m - 1] == 47):
        result = result + [47]
        Assert(slash_part(ToSeq(path)) == PSeq(47))
    else:
        Assert(slash_part(ToSeq(path)) == PSeq(47).take(0))
    Assert(ToSeq(result) == ToSeq(path) + slash_part(ToSeq(path)))
    if n > 0:
        result = result + [63]
        j = 0
        while j < n:
            # invariants-start
            Invariant(Acc(list_pred(path), 1 / 2))
            Invariant(Acc(list_pred(query), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(n == len(query))
            Invariant(0 <= j and j <= n)
            Invariant(len(ToSeq(query)) == n)
            Invariant(ToSeq(result) == ToSeq(path) + slash_part(ToSeq(path))
                      + PSeq(63) + ToSeq(query).take(j))
            Invariant(MustTerminate(n - j + 1))
            # invariants-end
            result = result + [query[j]]
            j = j + 1
        Assert(ToSeq(query).take(n) == ToSeq(query))
        Assert(query_part(ToSeq(query)) == PSeq(63) + ToSeq(query))
    else:
        Assert(query_part(ToSeq(query)) == PSeq(63).take(0))
    return result
    # impl-end
