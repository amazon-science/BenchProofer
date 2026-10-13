"""Twin-artifact model for django__django-13933.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a single-object choice field rejects a submitted value that is not an
  available choice, the human-readable error it produces is derived from a
  configurable message template by interpolating the offending value into the
  template's named placeholder. The placeholder is the literal token
  ``%(value)s``. Interpolation replaces EVERY occurrence of that token by the
  string form of the rejected value; all other characters of the template pass
  through unchanged. A template that contains no placeholder is therefore
  rendered verbatim, while a template that contains the placeholder renders
  with the rejected value visible in its place (rather than the literal
  placeholder text surviving into the message shown to the user).

Strings (the message template, the rejected value, and the rendered message)
are modelled as ``List[int]`` of Unicode code points (Nagini bans ``str``
indexing). The pure sequence theory ``PSeq[int]`` carries the specification.

The named-mapping ``%``-interpolation performed by the message machinery is
modelled DEEPLY as a verified front-recursive substitution fold
(``interpolated``); its equality to the real ``str.__mod__`` named mapping is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom. There
are no consumed axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms: the interpolation is modelled deeply in the pure region
#  and validated against the real str %-mapping by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def placeholder() -> PSeq[int]:
    """The named placeholder token, ``%(value)s``, as code points."""
    # '%' '(' 'v' 'a' 'l' 'u' 'e' ')' 's'
    return PSeq(37, 40, 118, 97, 108, 117, 101, 41, 115)


@Pure
def starts_with_placeholder(s: PSeq[int]) -> bool:
    """True iff ``s`` begins with the ``%(value)s`` token."""
    return len(s) >= 9 and s.take(9) == placeholder()


@Pure
def interpolated(template: PSeq[int], value: PSeq[int]) -> PSeq[int]:
    """Named-mapping interpolation of ``value`` into ``template``: every
    occurrence of the ``%(value)s`` token is replaced by ``value``; every other
    code point passes through. Front-recursive so a single unfold is available
    to callers per processed token/character."""
    if len(template) == 0:
        return template
    if starts_with_placeholder(template):
        return value + interpolated(template.drop(9), value)
    return template.take(1) + interpolated(template.drop(1), value)
# pure-end


def render_invalid_choice(template: List[int], value: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(template), 1 / 2))
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(template), 1 / 2))
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered message is the named-mapping interpolation of the rejected
    # value into the template: every %(value)s token becomes the value, all
    # other code points pass through unchanged.
    Ensures(ToSeq(Result()) == interpolated(ToSeq(template), ToSeq(value)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: no value is supplied to the message machinery, so the
    # named placeholder is never interpolated and the template is emitted
    # verbatim (a faithful copy of the configured message, placeholder intact).
    result = []  # type: List[int]
    k = len(template)
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(template), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(template))
        Invariant(ToSeq(result) == ToSeq(template).drop(k))
        # invariants-end
        c = template[k - 1]
        Assert(ToSeq(template).drop(k - 1) == PSeq(c) + ToSeq(template).drop(k))
        result = [c] + result
        k = k - 1
    return result
    # impl-end


def _render(ts: PSeq[int], value: List[int], i: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 4))
    Requires(0 <= i and i <= len(ts))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == interpolated(ts.drop(i), ToSeq(value)))
    # post-conditions-end
    # impl-start
    n = len(ts)
    result = []  # type: List[int]
    if i == n:
        Assert(len(ts.drop(i)) == 0)
        return result
    if i + 9 <= n and ts.drop(i).take(9) == placeholder():
        Assert(starts_with_placeholder(ts.drop(i)))
        Assert(ts.drop(i).drop(9) == ts.drop(i + 9))
        result = _render(ts, value, i + 9)
        Assert(ToSeq(result) == interpolated(ts.drop(i + 9), ToSeq(value)))
        # Prepend the rejected value, element by element from its end.
        j = len(value)
        while j > 0:
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 8))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(value))
            Invariant(ToSeq(result) == ToSeq(value).drop(j)
                      + interpolated(ts.drop(i + 9), ToSeq(value)))
            # invariants-end
            vj = value[j - 1]
            result = [vj] + result
            Assert(ToSeq(value).drop(j - 1) == PSeq(vj) + ToSeq(value).drop(j))
            j = j - 1
        Assert(ToSeq(value).drop(0) == ToSeq(value))
        Assert(starts_with_placeholder(ts.drop(i)))
        Assert(ts.drop(i).drop(9) == ts.drop(i + 9))
        Assert(interpolated(ts.drop(i), ToSeq(value))
               == ToSeq(value) + interpolated(ts.drop(i + 9), ToSeq(value)))
        return result
    Assert(not starts_with_placeholder(ts.drop(i)))
    Assert(len(ts.drop(i)) >= 1)
    head = ts[i]
    Assert(ts.drop(i).take(1) == PSeq(head))
    Assert(ts.drop(i).drop(1) == ts.drop(i + 1))
    result = _render(ts, value, i + 1)
    result = [head] + result
    return result
    # impl-end
