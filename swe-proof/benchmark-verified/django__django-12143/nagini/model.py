"""Twin-artifact model for django__django-12143.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When selecting, from a body of submitted form keys, those keys that carry an
  edited row's primary key, a key is RECOGNISED exactly when it decomposes,
  reading it as a sequence of Unicode code points, as

      <group label>  '-'  <one or more decimal digits>  '-'  <pk field name>

  and NOTHING ELSE — the whole key, from its first code point to its last, is
  consumed by that decomposition. The group label is matched LITERALLY: every
  code point of the candidate key's leading region must equal the corresponding
  code point of the label, with no code point of the label given any special
  interpretation. In particular a label that happens to contain code points
  such as U+0024 ('$'), U+002E ('.') or U+002B ('+') is still matched
  character-for-character, so a key whose leading region is exactly that label
  followed by the '-<digits>-<field name>' tail IS recognised, and a key that
  merely shares a proper textual fragment of the label is NOT.

  The digit run between the two hyphens must be non-empty and consist solely of
  the decimal-digit code points U+0030..U+0039; the trailing region after the
  second hyphen must equal the primary-key field name exactly, ending the key.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification. The
recognition decision for one candidate key is modelled deeply as a verified
structural decomposition; the literal recognition it pins is validated == the
real compiled-pattern match out-of-band by axiom_check.py (G-AX), not consumed
as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms: the recognition decision is the changed behaviour and is
#  modelled DEEPLY below. The real compiled-pattern match is an A-reference,
#  validated == the deep model by axiom_check.py / G-AX, never consumed.)
# axioms-end


# pure-start
@Pure
def is_digit(c: int) -> bool:
    """A single code point is a decimal digit U+0030..U+0039."""
    return 48 <= c and c <= 57


@Pure
def prefix_eq(s: PSeq[int], lit: PSeq[int]) -> bool:
    """The first `len(lit)` code points of `s` equal `lit` code point for code
    point — a LITERAL match of `lit` against the head of `s`. Total: if `s` is
    shorter than `lit` there can be no such match, so the result is False.
    Front-recursive (over both sequences) so a single unfold is available per
    loop step."""
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s.drop(1), lit.drop(1))


@Pure
def all_digits(s: PSeq[int]) -> bool:
    """Every code point of `s` is a decimal digit. Front-recursive so a single
    unfold is available per loop step."""
    if len(s) == 0:
        return True
    return is_digit(s[0]) and all_digits(s.drop(1))


@Pure
def recognises(prefix: PSeq[int], pkname: PSeq[int], key: PSeq[int]) -> bool:
    """True iff `key` decomposes EXACTLY as

        prefix ++ '-' ++ <one or more decimal digits> ++ '-' ++ pkname

    consuming the whole key, with `prefix` matched literally (code point for
    code point). The digit-run length is forced by the three fixed-length
    regions, so the decomposition is unique when it exists.

    The label region is `key[:np]`, the digit run `key[np+1 : np+1+d]`, and the
    field-name region `key[np+2+d:]`; the two hyphens sit at `np` and `np+1+d`."""
    np = len(prefix)
    nk = len(pkname)
    n = len(key)
    d = n - np - nk - 2          # length of the digit run if a match exists
    return (
        d >= 1
        and prefix_eq(key, prefix)                            # literal label
        and key[np] == 45                                     # first '-'
        and all_digits(key.take(np + 1 + d).drop(np + 1))     # the digit run
        and key[np + 1 + d] == 45                             # second '-'
        and prefix_eq(key.drop(np + 2 + d), pkname)           # field name, to end
    )
# pure-end

def match_literal(key: List[int], off: int, lit: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(key), 1 / 4))
    Requires(Acc(list_pred(lit), 1 / 4))
    Requires(0 <= off and off + len(lit) <= len(key))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 4))
    Ensures(Acc(list_pred(lit), 1 / 4))
    # Result is the LITERAL match of `lit` against `key[off:]`.
    Ensures(Result() == prefix_eq(ToSeq(key).drop(off), ToSeq(lit)))
    # post-conditions-end
    # impl-start
    m = len(lit)
    ok = True
    i = m
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 4))
        Invariant(Acc(list_pred(lit), 1 / 4))
        Invariant(0 <= i and i <= m and m == len(lit))
        Invariant(0 <= off and off + m <= len(key))
        Invariant(len(ToSeq(lit).drop(i)) <= len(ToSeq(key).drop(off + i)))
        Invariant(ok == prefix_eq(ToSeq(key).drop(off + i), ToSeq(lit).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(key).drop(off + i - 1)[0] == ToSeq(key)[off + i - 1])
        Assert(ToSeq(lit).drop(i - 1)[0] == ToSeq(lit)[i - 1])
        Assert(ToSeq(key).drop(off + i - 1).drop(1) == ToSeq(key).drop(off + i))
        Assert(ToSeq(lit).drop(i - 1).drop(1) == ToSeq(lit).drop(i))
        if key[off + i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    Assert(ToSeq(key).drop(off + 0) == ToSeq(key).drop(off))
    Assert(ToSeq(lit).drop(0) == ToSeq(lit))
    return ok
    # impl-end


def run_is_digits(key: List[int], lo: int, hi: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(key), 1 / 4))
    Requires(0 <= lo and lo <= hi and hi <= len(key))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key), 1 / 4))
    # Result is "every code point of key[lo:hi] is a decimal digit".
    Ensures(Result() == all_digits(ToSeq(key).take(hi).drop(lo)))
    # post-conditions-end
    # impl-start
    ok = True
    i = hi
    while i > lo:
        # invariants-start
        Invariant(Acc(list_pred(key), 1 / 4))
        Invariant(lo <= i and i <= hi and hi <= len(key) and 0 <= lo)
        Invariant(ok == all_digits(ToSeq(key).take(hi).drop(i)))
        Invariant(MustTerminate(i - lo + 1))
        # invariants-end
        c = key[i - 1]
        Assert(ToSeq(key).take(hi).drop(i - 1)[0] == ToSeq(key).take(hi)[i - 1])
        Assert(ToSeq(key).take(hi)[i - 1] == ToSeq(key)[i - 1])
        Assert(ToSeq(key).take(hi).drop(i - 1).drop(1) == ToSeq(key).take(hi).drop(i))
        if not (48 <= c and c <= 57):
            ok = False
        i = i - 1
    Assert(ToSeq(key).take(hi).drop(lo) == ToSeq(key).take(hi).drop(lo))
    return ok
    # impl-end


def is_edited_pk_key(prefix: List[int], pkname: List[int], key: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(prefix), 1 / 2))
    Requires(Acc(list_pred(pkname), 1 / 2))
    Requires(Acc(list_pred(key), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prefix), 1 / 2))
    Ensures(Acc(list_pred(pkname), 1 / 2))
    Ensures(Acc(list_pred(key), 1 / 2))
    # Recognised iff the key decomposes exactly as label-'-'-digits-'-'-name,
    # the label matched LITERALLY.
    Ensures(Result() == recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
    # post-conditions-end
    # impl-start
    np = len(prefix)
    nk = len(pkname)
    n = len(key)
    d = n - np - nk - 2
    if d < 1:
        Assert(not recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key)))
        return False
    # d >= 1, and n == np + 2 + d + nk, so every index/slice below is in bounds.
    Assert(n == np + 2 + d + nk)
    Assert(0 <= np and np < n)
    Assert(np + 1 + d <= n and np + 1 + d < n)
    Assert(np + 2 + d + nk == n)
    ok_label = match_literal(key, 0, prefix)
    Assert(len(key) == n)
    Assert(ToSeq(key).drop(0) == ToSeq(key))
    Assert(ok_label == prefix_eq(ToSeq(key), ToSeq(prefix)))
    Assert(0 <= np and np < len(key))
    hyphen1 = (key[np] == 45)
    ok_digits = run_is_digits(key, np + 1, np + 1 + d)
    Assert(len(key) == n)
    Assert(0 <= np + 1 + d and np + 1 + d < len(key))
    hyphen2 = (key[np + 1 + d] == 45)
    ok_name = match_literal(key, np + 2 + d, pkname)
    Assert(recognises(ToSeq(prefix), ToSeq(pkname), ToSeq(key))
           == (ok_label and hyphen1 and ok_digits and hyphen2 and ok_name))
    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name
    # impl-end
