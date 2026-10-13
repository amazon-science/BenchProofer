"""Twin-artifact model for sympy__sympy-14248.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Rendering a matrix-valued sum of terms as a flat infix string.
      A subtraction is carried internally as the addition of a term whose
      rendered form already begins with a leading minus.  The rendered sum
      must therefore use a binary minus for such a term -- the separator
      before a leading-minus term is " - " and that leading minus is removed
      from the term -- rather than blindly joining every term with " + "
      (which would yield "+ -<term>").  The very first term carries no infix
      separator: a leading-minus first term keeps its minus, a non-negative
      first term is rendered bare.

  (2) Rendering a matrix-valued product of factors as a flat string joined by
      "*".  When the product carries a negative numeric leading coefficient
      the whole product is rendered with a single leading minus in front of
      the factor list (the coefficient having been folded back, positive, into
      the factors); otherwise no sign is emitted.

  (3) A second flavour of matrix-sum rendering that joins with a single space
      rather than a spaced binary minus.  Here the decision is NOT made on the
      rendered text: each term carries a separate boolean fact -- "this term's
      leading coefficient is structurally negative" (the truthiness of a
      structural test on the expression tree, supplied as an input alongside
      the rendered term; a term may be structurally negative yet render with
      no leading minus, e.g. a negative-assumption symbol coefficient).  The
      separator before a structurally-negative term is a single space and the
      term is emitted in full (any minus stays attached to the term); a
      non-negative non-leading term is preceded by " + ".  As in (1) the very
      first term carries no infix separator and is emitted in full.  This must
      not blindly join every term with " + " (which would yield "+ -<term>"),
      and must NOT substitute a rendered-text leading-minus test for the
      structural fact.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the per-element specification is carried by `PSeq[int]`, and the
list of already-rendered terms / factors by `PSeq[PSeq[int]]`.  All three
behaviours are modelled DEEPLY (the assembly of the output sequence is spelled
out as a front-recursive fold) -- there are no axiomatized callees: the
rendering of an individual term / factor is an INPUT to each function (a type
refinement of the per-argument sub-render), so nothing opaque is consumed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: both behaviours are modelled deeply; the per-argument rendering
# of each term/factor is an input, not an opaque callee under contract.)
# axioms-end


# pure-start
@Pure
def empty() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(45).take(0)


@Pure
def is_neg(t: PSeq[int]) -> bool:
    """A rendered term that already begins with a leading minus (U+002D)."""
    return len(t) > 0 and t[0] == 45


@Pure
def body(t: PSeq[int]) -> PSeq[int]:
    """The rendered term with a single leading minus stripped, if present."""
    if is_neg(t):
        return t.drop(1)
    return t


@Pure
def sep_plus() -> PSeq[int]:
    # ' + '
    return PSeq(32, 43, 32)


@Pure
def sep_minus() -> PSeq[int]:
    # ' - '
    return PSeq(32, 45, 32)


@Pure
def star() -> PSeq[int]:
    # '*'
    return PSeq(42)


@Pure
def contrib(t: PSeq[int]) -> PSeq[int]:
    """The infix contribution of one non-leading sum term: a leading-minus
    term becomes ' - '<body>; any other term becomes ' + '<term>."""
    if is_neg(t):
        return sep_minus() + body(t)
    return sep_plus() + body(t)


@Pure
def add_tail(terms: PSeq[PSeq[int]], i: int) -> PSeq[int]:
    """Front-recursive fold of the non-leading sum terms terms[i:]."""
    Requires(0 <= i and i <= len(terms))
    if i == len(terms):
        return empty()
    return contrib(terms[i]) + add_tail(terms, i + 1)


@Pure
def lead(t: PSeq[int]) -> PSeq[int]:
    """The leading sum term: a leading-minus term keeps its minus; otherwise
    rendered bare (no infix separator)."""
    if is_neg(t):
        return PSeq(45) + body(t)
    return body(t)


@Pure
def matadd(terms: PSeq[PSeq[int]]) -> PSeq[int]:
    """The whole rendered sum: leading term then the folded non-leading tail."""
    if len(terms) == 0:
        return empty()
    return lead(terms[0]) + add_tail(terms, 1)


@Pure
def mul_tail(factors: PSeq[PSeq[int]], i: int) -> PSeq[int]:
    """Front-recursive fold of the non-leading product factors factors[i:],
    each prefixed by the '*' separator."""
    Requires(0 <= i and i <= len(factors))
    if i == len(factors):
        return empty()
    return star() + factors[i] + mul_tail(factors, i + 1)


@Pure
def joinstar(factors: PSeq[PSeq[int]]) -> PSeq[int]:
    """The factor list joined by '*' (leading factor bare)."""
    if len(factors) == 0:
        return empty()
    return factors[0] + mul_tail(factors, 1)


@Pure
def matmul(factors: PSeq[PSeq[int]], neg: bool) -> PSeq[int]:
    """The whole rendered product: a single leading minus iff the product
    carries a negative numeric leading coefficient, then the '*'-joined
    (coefficient-normalised) factors."""
    if neg:
        return PSeq(45) + joinstar(factors)
    return joinstar(factors)


@Pure
def sep_space() -> PSeq[int]:
    # ' '
    return PSeq(32)


@Pure
def contrib_space(t: PSeq[int], n: bool) -> PSeq[int]:
    """The infix contribution of one non-leading sum term under the
    single-space join discipline: a STRUCTURALLY-negative term (the boolean
    fact n, an input alongside the rendered term) becomes ' '<term> (the term
    emitted in full, any minus kept); any other term becomes ' + '<term>.
    The decision is n, NOT a test on the rendered text."""
    if n:
        return sep_space() + t
    return sep_plus() + t


@Pure
def add_tail_space(terms: PSeq[PSeq[int]], negs: PSeq[bool], i: int) -> PSeq[int]:
    """Front-recursive fold of the non-leading sum terms terms[i:] under the
    single-space join discipline, negs[k] carrying the structural negativity
    fact of terms[k]."""
    Requires(len(negs) == len(terms))
    Requires(0 <= i and i <= len(terms))
    if i == len(terms):
        return empty()
    return contrib_space(terms[i], negs[i]) + add_tail_space(terms, negs, i + 1)


@Pure
def matadd_space(terms: PSeq[PSeq[int]], negs: PSeq[bool]) -> PSeq[int]:
    """The whole rendered sum under the single-space join discipline: the
    leading term emitted in full, then the folded non-leading tail."""
    Requires(len(negs) == len(terms))
    if len(terms) == 0:
        return empty()
    return terms[0] + add_tail_space(terms, negs, 1)
# pure-end


def render_sum(terms: List[PSeq[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(terms), 1 / 2))
    Requires(len(terms) >= 1)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(terms)) == len(terms))
    Ensures(ToSeq(Result()) == matadd(ToSeq(terms)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(terms)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(terms), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(terms))
        Invariant(ToSeq(result) == add_tail(ToSeq(terms), i))
        Invariant(MustTerminate(i))
        # invariants-end
        t = terms[i - 1]
        Assert(ToSeq(terms)[i - 1] == t)
        piece = list(contrib(t))  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = terms[0]
    head = list(lead(t0))  # type: List[int]
    result = head + result
    return result
    # impl-end


def render_sum_space(terms: List[PSeq[int]], negs: List[bool]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(terms), 1 / 2))
    Requires(Acc(list_pred(negs), 1 / 2))
    Requires(len(terms) >= 1)
    Requires(len(negs) == len(terms))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(terms), 1 / 2))
    Ensures(Acc(list_pred(negs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(terms)) == len(terms))
    Ensures(len(ToSeq(negs)) == len(ToSeq(terms)))
    Ensures(ToSeq(Result()) == matadd_space(ToSeq(terms), ToSeq(negs)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(terms)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(terms), 1 / 2))
        Invariant(Acc(list_pred(negs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(terms))
        Invariant(len(ToSeq(negs)) == len(ToSeq(terms)))
        Invariant(ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i))
        Invariant(MustTerminate(i))
        # invariants-end
        t = terms[i - 1]
        n = negs[i - 1]
        Assert(ToSeq(terms)[i - 1] == t)
        Assert(ToSeq(negs)[i - 1] == n)
        piece = list(contrib_space(t, n))  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = terms[0]
    head = list(t0)  # type: List[int]
    result = head + result
    return result
    # impl-end


def render_product(factors: List[PSeq[int]], neg: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(len(factors) >= 1)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(ToSeq(factors)) == len(factors))
    Ensures(ToSeq(Result()) == matmul(ToSeq(factors), neg))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(factors)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(factors))
        Invariant(ToSeq(result) == mul_tail(ToSeq(factors), i))
        Invariant(MustTerminate(i))
        # invariants-end
        t = factors[i - 1]
        Assert(ToSeq(factors)[i - 1] == t)
        piece = list(star() + t)  # type: List[int]
        result = piece + result
        i = i - 1
    t0 = factors[0]
    head = list(t0)  # type: List[int]
    result = head + result
    return result
    # impl-end
