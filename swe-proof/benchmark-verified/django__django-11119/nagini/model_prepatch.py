"""Twin-artifact model for django__django-11119.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configured renderer carries an auto-escaping policy flag. When it renders a
  context value into a template, that policy MUST govern whether the value is
  HTML-escaped:

    * policy ON  -> the value is HTML-escaped: each of the five HTML-significant
      code points is replaced by its constant entity sequence, every other code
      point passing through unchanged (the per-code-point substitution);
    * policy OFF -> the value is emitted verbatim, with NO escaping applied.

  The rendering context inherits the renderer's policy flag; it is NOT forced to
  the escaping default. So a renderer whose policy is OFF emits an angle-bracket
  value such as ``<...>`` unchanged, while a renderer whose policy is ON emits
  it escaped (``&lt;...&gt;``).

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

The HTML-escape of a value is modelled deeply as a verified per-code-point
substitution (`escaped_seq`); its equality to the real escaping callee is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom. The
operation under specification is the *policy-conditioned choice* between the
escaped form and the verbatim form, not the escaping itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def seq_amp() -> PSeq[int]:
    # '&amp;'
    return PSeq(38, 97, 109, 112, 59)


@Pure
def seq_lt() -> PSeq[int]:
    # '&lt;'
    return PSeq(38, 108, 116, 59)


@Pure
def seq_gt() -> PSeq[int]:
    # '&gt;'
    return PSeq(38, 103, 116, 59)


@Pure
def seq_quot() -> PSeq[int]:
    # '&quot;'
    return PSeq(38, 113, 117, 111, 116, 59)


@Pure
def seq_apos_dec() -> PSeq[int]:
    # '&#39;'  (the apostrophe entity emitted at this code base)
    return PSeq(38, 35, 51, 57, 59)


@Pure
def entity(c: int) -> PSeq[int]:
    """Entity sequence emitted for a single code point under escaping: the five
    significant ones expand, every other code point maps to itself."""
    if c == 38:        # '&'
        return seq_amp()
    if c == 60:        # '<'
        return seq_lt()
    if c == 62:        # '>'
        return seq_gt()
    if c == 34:        # '"'
        return seq_quot()
    if c == 39:        # "'"
        return seq_apos_dec()
    return PSeq(c)


@Pure
def escaped_seq(s: PSeq[int]) -> PSeq[int]:
    """The escape of a whole sequence: concatenate the per-code-point entity
    sequences. Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return entity(s[0]) + escaped_seq(s.drop(1))
# pure-end


def render_value(value: List[int], engine_autoescape: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendering context inherits the renderer's policy flag, and that flag
    # decides escaping: ON => escaped per-code-point substitution; OFF =>
    # verbatim. The OFF clause is the discriminating one (escaping must NOT be
    # forced when the policy is OFF).
    Ensures(Implies(engine_autoescape == True,
                    ToSeq(Result()) == escaped_seq(ToSeq(value))))
    Ensures(Implies(engine_autoescape == False,
                    ToSeq(Result()) == ToSeq(value)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH BUG: the context is built without inheriting the renderer's
    # policy flag, so it takes the escaping default regardless of the renderer.
    ctx_autoescape = True
    result = []  # type: List[int]
    if ctx_autoescape:
        i = len(value)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(value))
            Invariant(ToSeq(result) == escaped_seq(ToSeq(value).drop(i)))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            c = value[i - 1]
            Assert(ToSeq(value).drop(i - 1)[0] == c)
            Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
            if c == 38:
                result = [38, 97, 109, 112, 59] + result
            elif c == 60:
                result = [38, 108, 116, 59] + result
            elif c == 62:
                result = [38, 103, 116, 59] + result
            elif c == 34:
                result = [38, 113, 117, 111, 116, 59] + result
            elif c == 39:
                result = [38, 35, 51, 57, 59] + result
            else:
                result = [c] + result
            i = i - 1
    else:
        i = 0
        while i < len(value):
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(value))
            Invariant(ToSeq(result) == ToSeq(value).take(i))
            Invariant(MustTerminate(len(value) - i + 1))
            # invariants-end
            result = result + [value[i]]
            i = i + 1
    return result
    # impl-end
