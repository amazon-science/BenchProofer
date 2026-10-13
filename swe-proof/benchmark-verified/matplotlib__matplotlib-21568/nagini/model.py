"""Twin-artifact model for matplotlib__matplotlib-21568.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a tick label is rendered in math mode, the literal characters that a
  math renderer would otherwise typeset as spaced binary operators or as
  inter-token gaps must be neutralised so the label keeps the same visual
  spacing as a plain-text label. Three code points need this protection:

    * the hyphen-minus U+002D is wrapped in braces  ->  `{-}`
    * the colon       U+003A is wrapped in braces    ->  `{:}`
    * the space       U+0020 is replaced by a thin    ->  `\\;`
      non-breaking math space so adjacent numbers do not run together.

  Every other code point passes through unchanged. The protection is a
  per-code-point substitution: element i of the result is the constant
  expansion of element i of the input (a length-3 token for the hyphen-minus
  and the colon, a length-2 token for the space, the singleton for any other
  code point), concatenated in order.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

The substitution is the operation under specification; it is modelled DEEPLY as
a verified per-code-point fold (`protected_seq`), whose equality to the real
math-mode neutralisation is checked out-of-band by axiom_check.py (G-AX), not
consumed as an axiom. There is no consumed `@ContractOnly` callee: the proof is
self-contained.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the modeled operation is a self-contained per-code-point substitution;
#  no unchanged opaque callee is consumed in the proof.)
# axioms-end


# pure-start
@Pure
def tok_dash() -> PSeq[int]:
    # '{-}'  = '{' '-' '}'
    return PSeq(123, 45, 125)


@Pure
def tok_colon() -> PSeq[int]:
    # '{:}'  = '{' ':' '}'
    return PSeq(123, 58, 125)


@Pure
def tok_space() -> PSeq[int]:
    # '\;'   = '\\' ';'
    return PSeq(92, 59)


@Pure
def protect(c: int) -> PSeq[int]:
    """Protected expansion of a single code point: the three math-significant
    code points expand to a constant token, every other code point maps to the
    singleton containing itself."""
    if c == 45:        # '-'
        return tok_dash()
    if c == 58:        # ':'
        return tok_colon()
    if c == 32:        # ' '
        return tok_space()
    return PSeq(c)


@Pure
def protected_seq(s: PSeq[int]) -> PSeq[int]:
    """The protection of a whole sequence: concatenate the per-code-point
    expansions. Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return protect(s[0]) + protected_seq(s.drop(1))
# pure-end


def protect_codepoints(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The protected output is the per-code-point math-space substitution.
    Ensures(ToSeq(Result()) == protected_seq(ToSeq(text)))
    # The three protected code points expand to their constant brace/space
    # tokens; in particular the colon and the space are protected (the
    # discriminating cases) alongside the hyphen-minus.
    Ensures(protect(45) == tok_dash())
    Ensures(protect(58) == tok_colon())
    Ensures(protect(32) == tok_space())
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 45:
            result = [123, 45, 125] + result
        elif c == 58:
            result = [123, 58, 125] + result
        elif c == 32:
            result = [92, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end
