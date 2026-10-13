"""Twin-artifact model for django__django-11099.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A candidate identifier string is accepted as VALID only when, reading it as a
  sequence of Unicode code points, it is NON-EMPTY and EVERY one of its code
  points belongs to the permitted character class (word characters together
  with the symbols '.', '@', '+', '-'). The acceptance test is anchored to the
  TRUE boundaries of the whole string: the very first code point and the very
  last code point are both inside the run that must consist only of permitted
  characters. In particular a line-feed code point (U+000A) is NOT a permitted
  character, so a string whose final code point is a line feed is REJECTED even
  when every earlier code point is permitted — there is no end-of-string
  tolerance that would let a terminal line feed slip through.

  Two permitted-character regimes are specified: an ASCII regime in which the
  word characters are exactly the ASCII letters, digits, and the low-line; and
  a wider regime in which the word characters additionally include the relevant
  non-ASCII letters and digits. The anchoring behaviour above is identical in
  both regimes.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification. The
permitted-character membership test for each regime is an unchanged callee and
is axiomatized; the whole-string acceptance decision is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def permitted_ascii(c: int) -> bool:
    """Membership of one code point in the ASCII permitted class
    (ASCII letters, digits, low-line, and the symbols '.', '@', '+', '-').
    Unchanged community callee; provenance + executable soundness check:
    mapping.md / axiom_check.py. The line feed U+000A is NOT a member."""
    Ensures(Implies(c == 10, not Result()))          # line feed excluded
    Ensures(Implies(c == 32, not Result()))           # space excluded
    Ensures(Implies(c == 97, Result()))               # 'a' included
    Ensures(Implies(c == 65, Result()))               # 'A' included
    Ensures(Implies(c == 48, Result()))               # '0' included
    Ensures(Implies(c == 45, Result()))               # '-' included
    Ensures(Implies(c == 46, Result()))               # '.' included


@Pure
@ContractOnly
def permitted_unicode(c: int) -> bool:
    """Membership of one code point in the wider permitted class (the word
    characters of the wider regime plus the symbols '.', '@', '+', '-').
    Unchanged community callee; provenance + executable soundness check:
    mapping.md / axiom_check.py. The line feed U+000A is NOT a member."""
    Ensures(Implies(c == 10, not Result()))          # line feed excluded
    Ensures(Implies(c == 32, not Result()))           # space excluded
    Ensures(Implies(c == 97, Result()))               # 'a' included
    Ensures(Implies(c == 233, Result()))              # 'é' included (wider)
    Ensures(Implies(c == 48, Result()))               # '0' included
    Ensures(Implies(c == 45, Result()))               # '-' included
    Ensures(Implies(c == 46, Result()))               # '.' included
# axioms-end


# pure-start
@Pure
def all_ascii_permitted(s: PSeq[int]) -> bool:
    """Every code point of the sequence is in the ASCII permitted class.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return permitted_ascii(s[0]) and all_ascii_permitted(s.drop(1))


@Pure
def all_unicode_permitted(s: PSeq[int]) -> bool:
    """Every code point of the sequence is in the wider permitted class.
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return permitted_unicode(s[0]) and all_unicode_permitted(s.drop(1))
# pure-end


def accepts_ascii(value: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    # Accepted iff the WHOLE string is a non-empty run of permitted code points,
    # anchored to both true ends — a terminal line feed is therefore rejected.
    Ensures(Result() == (len(value) >= 1 and all_ascii_permitted(ToSeq(value))))
    # post-conditions-end
    # impl-start
    n = len(value)
    if n == 0:
        return False
    # Pre-patch skeleton: the end anchor tolerates a single terminal line feed,
    # so the run that must be permitted ends one position early when the final
    # code point is a line feed (U+000A).
    m = n
    if value[n - 1] == 10:
        m = n - 1
    if m == 0:
        return False
    i = m
    ok = True
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= m and m <= n and n == len(value))
        Invariant(ok == all_ascii_permitted(ToSeq(value).take(m).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = value[i - 1]
        Assert(ToSeq(value).take(m).drop(i - 1)[0] == c)
        Assert(ToSeq(value).take(m).drop(i - 1).drop(1) == ToSeq(value).take(m).drop(i))
        if not permitted_ascii(c):
            ok = False
        i = i - 1
    Assert(ToSeq(value).take(m).drop(0) == ToSeq(value).take(m))
    return ok
    # impl-end


def accepts_unicode(value: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    # Accepted iff the WHOLE string is a non-empty run of permitted code points,
    # anchored to both true ends — a terminal line feed is therefore rejected.
    Ensures(Result() == (len(value) >= 1 and all_unicode_permitted(ToSeq(value))))
    # post-conditions-end
    # impl-start
    n = len(value)
    if n == 0:
        return False
    # Pre-patch skeleton: the end anchor tolerates a single terminal line feed,
    # so the run that must be permitted ends one position early when the final
    # code point is a line feed (U+000A).
    m = n
    if value[n - 1] == 10:
        m = n - 1
    if m == 0:
        return False
    i = m
    ok = True
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(0 <= i and i <= m and m <= n and n == len(value))
        Invariant(ok == all_unicode_permitted(ToSeq(value).take(m).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = value[i - 1]
        Assert(ToSeq(value).take(m).drop(i - 1)[0] == c)
        Assert(ToSeq(value).take(m).drop(i - 1).drop(1) == ToSeq(value).take(m).drop(i))
        if not permitted_unicode(c):
            ok = False
        i = i - 1
    Assert(ToSeq(value).take(m).drop(0) == ToSeq(value).take(m))
    return ok
    # impl-end
