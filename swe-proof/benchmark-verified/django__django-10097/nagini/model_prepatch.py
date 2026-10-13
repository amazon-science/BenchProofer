"""Twin-artifact model for django__django-10097.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A URL may optionally carry a leading authentication segment (the text that
  appears before the host and is terminated by a literal ``@``). RFC 1738
  section 3.1 requires that within that segment any ``":"``, ``"@"`` or ``"/"``
  be percent-encoded; whitespace is likewise not permitted. The acceptance
  predicate for a candidate authentication segment is therefore:

    * the segment is non-empty;
    * it may be split at most once by a single ``":"`` separator into a
      *user* run followed by an optional *password* run;
    * the user run (the text before that separator, or the whole segment when
      there is no separator) is non-empty;
    * every code point other than that one permitted separator colon is an
      "authentication character": it is none of whitespace, ``":"``,
      ``"@"`` or ``"/"``.

A segment is accepted iff all four hold. The discriminating cases are segments
that smuggle an unencoded ``"/"``, ``"@"`` or a second ``":"`` into the user or
password: those must be rejected.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``.
The acceptance predicate is modelled DEEPLY as front-recursive ``@Pure``
sequence predicates (no consumed axiom); its equality to the real compiled
matcher is checked out-of-band by axiom_check.py (G-AX), not consumed here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the changed operation is modelled deeply; the real compiled matcher
#  is an A-reference validated by axiom_check.py / G-AX, not a consumed axiom.)
# axioms-end


# pure-start
@Pure
def is_whitespace(c: int) -> bool:
    """The full set of whitespace code points (the Unicode whitespace class):
    the ASCII run ``{9..13, 32}`` together with the C1/separator code points
    ``{0x1c..0x1f, 0x85, 0xa0, 0x1680, 0x2000..0x200a, 0x2028, 0x2029,
    0x202f, 0x205f, 0x3000}``. A character is whitespace iff it lies in this
    set."""
    return ((9 <= c and c <= 13) or c == 32
            or (0x1c <= c and c <= 0x1f) or c == 0x85 or c == 0xa0
            or c == 0x1680 or (0x2000 <= c and c <= 0x200a)
            or c == 0x2028 or c == 0x2029 or c == 0x202f
            or c == 0x205f or c == 0x3000)


@Pure
def is_uchar(c: int) -> bool:
    """A single authentication character: every code point EXCEPT whitespace
    and the three RFC-1738 separators that must be encoded — ``":"`` (58),
    ``"@"`` (64) and ``"/"`` (47)."""
    return not is_whitespace(c) and c != 58 and c != 64 and c != 47


@Pure
def body_ok(s: PSeq[int]) -> bool:
    """Every code point is either an authentication character or the single
    permitted separator colon (58). Front-recursive: one unfold per step."""
    if len(s) == 0:
        return True
    return (is_uchar(s[0]) or s[0] == 58) and body_ok(s.drop(1))


@Pure
def colons(s: PSeq[int]) -> int:
    """Number of separator colons (code point 58) in the segment.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return 0
    return (1 if s[0] == 58 else 0) + colons(s.drop(1))


@Pure
def accepts(s: PSeq[int]) -> bool:
    """The authentication segment ``s`` (the text before the terminating
    ``@``) is accepted iff it is non-empty, contains only authentication
    characters apart from at most one separator colon, and does not begin with
    that colon (the user run is non-empty)."""
    return len(s) > 0 and body_ok(s) and colons(s) <= 1 and s[0] != 58
# pure-end


def validate_authsegment(seg: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(seg), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(seg), 1 / 2))
    # The decision is exactly the structural acceptance predicate on the input.
    Ensures(Result() == accepts(ToSeq(seg)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: the authentication run is a maximal non-whitespace
    # run, optionally split by a colon — i.e. the only excluded code points are
    # whitespace. ":", "@" and "/" are NOT excluded, so any number of them may
    # appear anywhere. A segment is accepted whenever it is non-empty and free
    # of whitespace.
    n = len(seg)
    if n == 0:
        return False
    nonws = True
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(seg), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(seg))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = seg[i - 1]
        if is_whitespace(c):
            nonws = False
        i = i - 1
    return nonws
    # impl-end
