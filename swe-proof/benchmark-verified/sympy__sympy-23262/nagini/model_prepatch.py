"""Twin-artifact model for sympy__sympy-23262.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A finite ordered container of already-rendered element source-fragments is
  serialised into the surface source text of a container literal that, when
  re-parsed, reconstructs a container of the SAME KIND (a parenthesis-delimited
  container vs. a square-bracket-delimited container) and the SAME ARITY as the
  input.

  The body is the element fragments concatenated left-to-right with exactly one
  ", " (comma, single space) between each adjacent pair, with no separator
  before the first or after the last element. The body is wrapped in the
  delimiters of the requested kind:

    * the square-bracket kind opens with "[" and closes with "]";
    * the parenthesis kind opens with "(" and closes with ",)" -- a comma
      immediately before the closing parenthesis.

  The trailing comma of the parenthesis kind is REQUIRED: it is what makes the
  emitted text re-parse as a one-element grouping rather than as the bare
  parenthesised value of its single element. A parenthesis container holding
  exactly one element therefore serialises as "(" element ",)", which re-parses
  to that same one-element container; without the trailing comma it would
  re-parse to the element itself, collapsing the arity from one to zero.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); the element list is `PSeq[PSeq[int]]`, the sequence of the elements'
already-rendered surface fragments. Pure sequences carry no heap permission, so
the specification quantifies over them directly. No library callee is
axiomatized: the element-fragment production is unchanged upstream machinery,
taken as given; the assembly modelled here -- delimiter selection plus the
", "-join -- is modelled deeply and pinned exactly by the spec.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The per-element surface fragments are taken as given
# `PSeq[int]` values -- producing them is unchanged recursive machinery, not
# part of the modelled assembly. The assembly itself -- delimiter selection and
# the ", "-join -- is modelled deeply.)
# axioms-end


# pure-start
@Pure
def lparen() -> int:
    # '(' : opening delimiter of the parenthesis-kind container.
    return 40


@Pure
def rparen() -> int:
    # ')' : closing delimiter of the parenthesis-kind container.
    return 41


@Pure
def lbracket() -> int:
    # '[' : opening delimiter of the square-bracket-kind container.
    return 91


@Pure
def rbracket() -> int:
    # ']' : closing delimiter of the square-bracket-kind container.
    return 93


@Pure
def comma() -> int:
    # ',' : the separator/terminator code point.
    return 44


@Pure
def sep() -> PSeq[int]:
    # ', ' : a comma followed by a single space, the element separator.
    return PSeq(44, 32)


@Pure
def left_delim(is_paren: bool) -> PSeq[int]:
    """Opening delimiter for the requested container kind."""
    if is_paren:
        return PSeq(lparen())
    return PSeq(lbracket())


@Pure
def right_delim(is_paren: bool) -> PSeq[int]:
    """Closing delimiter for the requested container kind. The parenthesis kind
    closes with a comma immediately before the closing parenthesis so that a
    one-element container re-parses to a one-element container; the square-
    bracket kind closes with the bare closing bracket."""
    if is_paren:
        return PSeq(comma(), rparen())
    return PSeq(rbracket())


@Pure
def joined(elems: PSeq[PSeq[int]]) -> PSeq[int]:
    """The element fragments rendered as the separator-joined body that sits
    between the delimiters: the fragments concatenated left-to-right with
    exactly one `sep()` between each adjacent pair and no trailing separator.
    Front-recursive so a single unfold is available per loop step."""
    if len(elems) == 0:
        return PSeq(0).take(0)
    if len(elems) == 1:
        return elems[0]
    return elems[0] + sep() + joined(elems.drop(1))


@Pure
def rendered(elems: PSeq[PSeq[int]], is_paren: bool) -> PSeq[int]:
    """The full container literal: opening delimiter, the ", "-joined element
    body, closing delimiter."""
    return left_delim(is_paren) + joined(elems) + right_delim(is_paren)
# pure-end


def render_container(elems: PSeq[PSeq[int]], is_paren: bool) -> PSeq[int]:
    # pre-conditions-start
    # (no heap input; pure sequences carry no permission)
    # TERMINATION: the serialiser must actually ANSWER — assembling a finite
    # container literal from finitely many fragments is a bounded computation.
    # Nagini is a partial-correctness verifier by default, so without this
    # obligation a non-terminating implementation (e.g. bare self-recursion or
    # an endless loop) satisfies every Ensures vacuously; the real assembly
    # always returns its rendered text.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The rendered text is exactly left-delim + (", "-joined elements) + right-delim.
    Ensures(Result() == rendered(elems, is_paren))
    # Kind fidelity: the first code point is the opening delimiter of the
    # requested kind -- '(' (40) for the parenthesis kind, '[' (91) otherwise.
    Ensures(len(Result()) >= 2)
    Ensures(Implies(is_paren, Result()[0] == lparen()))
    Ensures(Implies(not is_paren, Result()[0] == lbracket()))
    # Closing fidelity: the parenthesis kind ends with ',' immediately followed
    # by ')' (the REQUIRED trailing comma -- the last two code points are 44
    # then 41); the square-bracket kind ends with ']' (93).
    Ensures(Implies(is_paren, Result()[len(Result()) - 1] == rparen()))
    Ensures(Implies(is_paren, Result()[len(Result()) - 2] == comma()))
    Ensures(Implies(not is_paren, Result()[len(Result()) - 1] == rbracket()))
    # Arity-preserving single-element case: a parenthesis container of exactly
    # one element serialises as '(' + element + ',)' -- the trailing comma keeps
    # it a one-element grouping rather than collapsing to the bare element.
    Ensures(Implies(is_paren and len(elems) == 1,
                    Result() == PSeq(lparen()) + elems[0] + PSeq(comma(), rparen())))
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: the parenthesis kind's delimiter pair is taken as the
    # two characters of the bare parenthesis pair, so the closing delimiter is
    # the lone closing parenthesis with NO trailing comma. A one-element
    # parenthesis container then serialises as '(' element ')', which re-parses
    # to the bare element -- collapsing the arity.
    if is_paren:
        left = PSeq(lparen())  # type: PSeq[int]
        right = PSeq(rparen())  # type: PSeq[int]
    else:
        left = PSeq(lbracket())
        right = PSeq(rbracket())
    # body := the ", "-joined element list (front-recursive fold, built back to
    # front so each step unfolds `joined` once).
    body = PSeq(0).take(0)  # type: PSeq[int]
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(elems))
        Invariant(body == joined(elems.drop(i)))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        # Bridge the front-recursive unfold of `joined` over `elems.drop(i-1)`:
        # its head is elems[i-1] and its tail is elems.drop(i).
        Assert(elems.drop(i - 1)[0] == elems[i - 1])
        Assert(elems.drop(i - 1).drop(1) == elems.drop(i))
        if i == len(elems):
            # last element: a single-element tail, no trailing separator.
            Assert(len(elems.drop(i - 1)) == 1)
            body = elems[i - 1]
        else:
            # at least two elements remain, so `joined` unfolds once.
            Assert(len(elems.drop(i - 1)) >= 2)
            body = elems[i - 1] + sep() + body
        i = i - 1
    result = left + body + right  # type: PSeq[int]
    return result
    # impl-end
