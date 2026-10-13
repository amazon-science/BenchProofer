"""Twin-artifact model for django__django-13512.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a textual value is serialised to its JSON-text rendering for display
  and editing, the resulting rendering must preserve every character of the
  text literally. Concretely, the rendering of a text scalar is an opening
  quotation mark, followed by the per-character JSON encoding of each code
  point of the text in order, followed by a closing quotation mark. The
  per-character encoding escapes only the two JSON-structural code points — the
  quotation mark (U+0022) becomes a backslash followed by a quotation mark, and
  the backslash (U+005C) becomes a doubled backslash — while EVERY other code
  point, INCLUDING every non-ASCII code point at or above U+0080 (e.g. CJK
  text, accented Latin letters, emoji), is emitted unchanged. Non-ASCII code
  points are therefore rendered as themselves, not transliterated into any
  ASCII-only surrogate form.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.
The modelled domain is the printable code points (>= U+0020), which is exactly
the domain of every tested input; the per-character encoding is spelled out
DEEPLY (`json_string_body`) and validated equal to the real serialiser by
axiom_check.py (G-AX), not consumed as an axiom — there is no consumed axiom in
this bundle.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def json_char(c: int) -> PSeq[int]:
    """JSON-text encoding of one printable code point (>= U+0020) when the
    serialiser is configured to keep non-ASCII text literal. The quotation
    mark and the backslash are the only escaped code points; everything else,
    including all non-ASCII code points, is emitted as itself."""
    if c == 34:        # '"'  -> '\"'
        return PSeq(92, 34)
    if c == 92:        # '\'  -> '\\'
        return PSeq(92, 92)
    return PSeq(c)


@Pure
def json_string_body(s: PSeq[int]) -> PSeq[int]:
    """Per-code-point JSON-text encoding of a whole sequence: concatenate the
    per-code-point encodings. Front-recursive so a single unfold is available
    to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return json_char(s[0]) + json_string_body(s.drop(1))
# pure-end


def json_render_text(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # every code point is printable (>= U+0020): the tested domain
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                             text[k] >= 32), [[text[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendering is a quotation mark, the per-code-point JSON encoding of
    # the text, then a closing quotation mark.
    Ensures(ToSeq(Result()) ==
            PSeq(34) + json_string_body(ToSeq(text)) + PSeq(34))
    # Discriminating clause: every non-ASCII code point (>= U+0080) is rendered
    # literally as itself (a single code point), never expanded into a longer
    # ASCII-only surrogate form.
    Ensures(Forall(int, lambda c: (Implies(c >= 128, json_char(c) == PSeq(c)),
                                    [[json_char(c)]])))
    # post-conditions-end
    # impl-start
    body = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(body)))
        Invariant(0 <= i and i <= len(text))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                                  text[k] >= 32), [[text[k]]])))
        Invariant(ToSeq(body) == json_string_body(ToSeq(text).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 34:
            body = [92, 34] + body
        elif c == 92:
            body = [92, 92] + body
        elif c >= 128:
            # pre-patch default: a non-ASCII code point is transliterated into
            # an ASCII-only escape (begins with backslash-u) rather than kept.
            body = [92, 117] + body
        else:
            body = [c] + body
        i = i - 1
    result = [34] + body + [34]
    return result
    # impl-end
