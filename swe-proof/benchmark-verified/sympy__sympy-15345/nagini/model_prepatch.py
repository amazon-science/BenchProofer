"""Twin-artifact model for sympy__sympy-15345.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A recognised n-ary lattice operator (an associative/commutative reduction
  over its operands, e.g. the running maximum or minimum of a list of terms)
  is rendered into the Wolfram-language surface syntax. In that syntax a
  function application is written with the function's recognised name, then a
  SQUARE-bracket-delimited operand list whose operands are separated by a
  comma followed by a single space:

        name "[" operand_0 ", " operand_1 ", " ... ", " operand_{n-1} "]"

  Concretely the rendered text is the recognised name, then the opening
  square bracket, then the operands joined by ", " in their given left-to-right
  order, then the closing square bracket. Round parentheses are NOT used as the
  application delimiter, operands are neither dropped nor reordered, and the
  ", " separator appears once between each adjacent pair of operands (never a
  trailing separator after the last operand).

Rendering is a bounded, straight-line computation: the operation MUST
terminate and return its rendered text (a total-correctness obligation,
carried as MustTerminate in the precondition). Nagini is a partial-correctness
verifier by default, so without the obligation a non-terminating
implementation would satisfy every value postcondition only vacuously and
would never deliver the rendered text to the printer.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); the operand list is `PSeq[PSeq[int]]`, the sequence of operands'
already-rendered surface forms. Pure sequences carry no heap permission, so the
specification quantifies over them directly. No library callee is axiomatized:
the rendering is a pure name+bracket+separator-join assembly, modelled deeply
via a front-recursive separator-join fold and pinned exactly by the spec.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The per-operand surface forms are taken as given
# `PSeq[int]` values -- the recursive rendering of each operand is unchanged
# machinery, not part of the modelled assembly. The assembly itself -- name,
# square brackets, ", "-join -- is modelled deeply.)
# axioms-end


# pure-start
@Pure
def lbracket() -> int:
    # '[' : the opening application delimiter of the surface syntax.
    return 91


@Pure
def rbracket() -> int:
    # ']' : the closing application delimiter of the surface syntax.
    return 93


@Pure
def sep() -> PSeq[int]:
    # ', ' : a comma followed by a single space, the operand separator.
    return PSeq(44, 32)


@Pure
def joined(operands: PSeq[PSeq[int]]) -> PSeq[int]:
    """The operand list rendered as the separator-joined body that sits between
    the brackets: the operands concatenated left-to-right with exactly one
    `sep()` between each adjacent pair and no trailing separator. Front-
    recursive so a single unfold is available per loop step."""
    if len(operands) == 0:
        return PSeq(0).take(0)
    if len(operands) == 1:
        return operands[0]
    return operands[0] + sep() + joined(operands.drop(1))


@Pure
def rendered(name: PSeq[int], operands: PSeq[PSeq[int]]) -> PSeq[int]:
    """The full surface form: name, opening square bracket, the ", "-joined
    operand body, closing square bracket."""
    return name + PSeq(lbracket()) + joined(operands) + PSeq(rbracket())
# pure-end


def print_lattice_call(name: PSeq[int], operands: PSeq[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    # A function application always carries at least one operand.
    Requires(len(operands) > 0)
    # TERMINATION: the renderer must actually ANSWER — assembling a function
    # application's surface text from finitely many operand fragments is a
    # bounded computation. Nagini is a partial-correctness verifier by
    # default, so without this obligation a non-terminating implementation
    # (e.g. an endless loop) satisfies every Ensures vacuously; the real
    # printer always returns its rendered text.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The rendered text is exactly name + '[' + (", "-joined operands) + ']'.
    Ensures(Result() == rendered(name, operands))
    # The application delimiters are the SQUARE brackets, not round parens:
    # the character immediately after the name is '[' (91, never '(' = 40), and
    # the final character is ']' (93, never ')' = 41).
    Ensures(len(Result()) > len(name))
    Ensures(Result()[len(name)] == lbracket())
    Ensures(Result()[len(Result()) - 1] == rbracket())
    # The rendered text begins with the recognised name verbatim.
    Ensures(Result().take(len(name)) == name)
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: the operator is not a recognised application, so it
    # falls through to the generic reduction-printer, which wraps the ", "-joined
    # operands in ROUND parentheses ('(' = 40, ')' = 41) rather than the
    # square-bracket application delimiters the surface syntax requires.
    body = PSeq(0).take(0)  # type: PSeq[int]
    i = len(operands)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(operands))
        Invariant(body == joined(operands.drop(i)))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        Assert(operands.drop(i - 1)[0] == operands[i - 1])
        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))
        if i == len(operands):
            Assert(len(operands.drop(i - 1)) == 1)
            body = operands[i - 1]
        else:
            Assert(len(operands.drop(i - 1)) >= 2)
            body = operands[i - 1] + sep() + body
        i = i - 1
    result = name + PSeq(40) + body + PSeq(41)  # type: PSeq[int]
    return result
    # impl-end
