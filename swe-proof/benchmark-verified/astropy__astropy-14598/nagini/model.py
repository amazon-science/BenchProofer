"""Twin-artifact model for astropy__astropy-14598.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A long keyword value is serialised by *escaping* every embedded single quote
  U+0027 as a pair of single quotes (the convention for a literal quote inside a
  quoted string), then carrying the escaped text across one or more continuation
  segments. Re-deriving the value from that serialised form must be its exact
  inverse, so that serialise-then-parse is the identity on EVERY value. Two
  independently observable obligations:

  (A) Full payload recovery. The escaped text carried by a continuation segment
      must be recovered IN FULL. Characters that follow an interior space (the
      payload of a quoted string may legitimately contain spaces) are part of
      the payload and must not be dropped: recovery may not stop early at the
      first interior space-adjacent quote. The recovered payload equals the
      segment's escaped text exactly.

  (B) Single un-escape. The recovered escaped text is un-escaped EXACTLY ONCE:
      each leading pair of single quotes collapses to one single quote, every
      other code point is copied. The un-escape is applied a single time, so a
      genuine embedded quote pair is preserved as a quote pair.

  (A) and (B) compose to the round-trip identity: for every value, un-escaping
      the full recovery of its escape returns the original value, in particular
      for a value that contains or ends with an embedded quote pair, with or
      without trailing text and with or without an interior space.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the single quote is the code point 39, the space is 32. The
specification is carried by the pure sequence theory `PSeq[int]`.

There are no axioms. The escaping, the full-payload recovery, and the
un-escaping are all *changed* / supporting operations modelled DEEPLY as
verified folds (`escape_quotes`, `unescape_quotes`). Their agreement with the
real library operations is checked out-of-band by axiom_check.py (G-AX), not
consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions; the
per-function regions repeat, one set per modelled obligation.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def escape_quotes(s: PSeq[int]) -> PSeq[int]:
    """Serialisation escape: every single quote (39) becomes a pair of single
    quotes; every other code point is copied. Front-recursive so a single
    unfold is available per loop / proof step."""
    if len(s) == 0:
        return s
    if s[0] == 39:
        return PSeq(39, 39) + escape_quotes(s.drop(1))
    return PSeq(s[0]) + escape_quotes(s.drop(1))


@Pure
def unescape_quotes(s: PSeq[int]) -> PSeq[int]:
    """Parse un-escape applied exactly once: a leading pair of single quotes
    (39,39) collapses to one single quote and parsing continues after the pair;
    any other leading code point is copied and parsing continues after it. The
    single non-overlapping left-to-right collapse of `''` -> `'`."""
    if len(s) < 2:
        return s
    if s[0] == 39 and s[1] == 39:
        return PSeq(39) + unescape_quotes(s.drop(2))
    return PSeq(s[0]) + unescape_quotes(s.drop(1))
# pure-end


def recover_payload(segment: List[int]) -> List[int]:
    """Obligation (A): recover the FULL escaped payload carried by a
    continuation segment. The recovered payload is every code point of the
    segment's carried text -- nothing is dropped at an interior space.

    The carried text does not contain the value/comment separator (code point
    47, '/'): segments whose payload introduces a separator are handled by the
    comment-separation logic and are out of this obligation's scope.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(segment), 1 / 2))
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(segment), segment[k] != 47))))
    Requires(MustTerminate(len(segment) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(segment), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The complete carried payload is recovered, in order, in full.
    Ensures(ToSeq(Result()) == ToSeq(segment))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    n = len(segment)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(segment), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(segment))
        Invariant(ToSeq(result) == ToSeq(segment).take(j))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
        result = result + [segment[j]]
        j = j + 1
    Assert(ToSeq(segment).take(n) == ToSeq(segment))
    return result
    # impl-end


def unescape_value(captured: List[int], witness: List[int]) -> List[int]:
    """Obligation (B): un-escape the recovered escaped text EXACTLY ONCE. Each
    leading pair of single quotes collapses to one; every other code point is
    copied. Composing with the full recovery (A) is the round-trip identity:
    `witness` is the read-only original value whose escape this recovers, and
    the un-escape returns it exactly (the round-trip clause).
    """
    # pre-conditions-start
    Requires(Acc(list_pred(captured), 1 / 2))
    Requires(Acc(list_pred(witness), 1 / 2))
    Requires(MustTerminate(len(witness) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(captured), 1 / 2))
    Ensures(Acc(list_pred(witness), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Exactly one un-escape pass over the recovered text.
    Ensures(ToSeq(Result()) == unescape_quotes(ToSeq(captured)))
    # Round-trip witness: if the recovered text is the escape of `witness`, this
    # un-escape returns `witness` -- single application is the exact inverse.
    Ensures(Implies(ToSeq(captured) == escape_quotes(ToSeq(witness)),
                    ToSeq(Result()) == ToSeq(witness)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    n = len(captured)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(captured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(captured))
        Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
                  == unescape_quotes(ToSeq(captured)))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
            Assert(ToSeq(captured).drop(j)[0] == 39)
            Assert(ToSeq(captured).drop(j)[1] == 39)
            Assert(len(ToSeq(captured).drop(j)) >= 2)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(39) + unescape_quotes(ToSeq(captured).drop(j).drop(2)))
            Assert(ToSeq(captured).drop(j).drop(2) == ToSeq(captured).drop(j + 2))
            result = result + [39]
            j = j + 2
        else:
            c = captured[j]
            Assert(ToSeq(captured).drop(j)[0] == c)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(c) + unescape_quotes(ToSeq(captured).drop(j).drop(1)))
            Assert(ToSeq(captured).drop(j).drop(1) == ToSeq(captured).drop(j + 1))
            result = result + [c]
            j = j + 1
    rt_lemma(ToSeq(witness))
    return result
    # impl-end


# The round-trip identity, proved once and quantified, supports the rt witness
# clause of `unescape_value`.
def rt_lemma(v: PSeq[int]) -> None:
    Requires(MustTerminate(len(v) + 1))
    Ensures(unescape_quotes(escape_quotes(v)) == v)
    if len(v) == 0:
        return
    rt_lemma(v.drop(1))
    if v[0] == 39:
        Assert(escape_quotes(v) == PSeq(39, 39) + escape_quotes(v.drop(1)))
        Assert(escape_quotes(v)[0] == 39)
        Assert(escape_quotes(v)[1] == 39)
        Assert(len(escape_quotes(v)) >= 2)
        Assert(escape_quotes(v).drop(2) == escape_quotes(v.drop(1)))
        Assert(unescape_quotes(escape_quotes(v))
               == PSeq(39) + unescape_quotes(escape_quotes(v.drop(1))))
    else:
        Assert(escape_quotes(v) == PSeq(v[0]) + escape_quotes(v.drop(1)))
        Assert(escape_quotes(v)[0] == v[0])
        Assert(v[0] != 39)
        Assert(unescape_quotes(escape_quotes(v))
               == PSeq(v[0]) + unescape_quotes(escape_quotes(v).drop(1)))
        Assert(escape_quotes(v).drop(1) == escape_quotes(v.drop(1)))
