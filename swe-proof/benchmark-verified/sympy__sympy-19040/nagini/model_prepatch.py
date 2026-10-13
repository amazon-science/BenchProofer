"""Twin-artifact model for sympy__sympy-19040.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Factoring a (multivariate) polynomial with an extension must return its
  COMPLETE factor list: the returned list must contain EVERY factor of the
  input — none dropped — AND an input that splits into several factors must be
  returned as all of those separate factors, never collapsed to a single
  element. The leading coefficient is returned unchanged.

A polynomial is identified by an opaque identity (`int`), a value DISTINCT from
the factor list it must produce. The complete factor list OF THE INPUT is the
result of the (unchanged) factoring operation `factor_list` applied TO THAT
INPUT. The contract pins the result to that input-driven factoring: the returned
list equals `factor_list(poly)` whenever it has two or more elements, and equals
the single-element result `lone(poly)` otherwise (the legitimate case of an
input that does not split). Returning the input unchanged, returning it as a
length-one list, or applying the factoring to any polynomial OTHER than the
input itself does NOT satisfy the contract.

`factor_list`, the single-element result `lone`, and the auxiliary helper
`other_poly` are operations the function invokes but does not change; they are
axiomatised (`@Pure @ContractOnly`) by the weakest behaviour the proof needs
(each returns SOME determinate value as a function of its argument), and their
soundness is checked against the real callees out of band (axiom_check.py /
G-AX). The contract is expressed purely STRUCTURALLY over `factor_list(poly)`
(sequence equality and length only — no hidden answer-key lookup, no unbounded
value quantifiers), so the proof obligation stays inside Nagini's decidable
fragment.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def other_poly(poly: int) -> int:
    """An unchanged helper that maps a polynomial to some related polynomial
    identity. The weakest behaviour the proof needs: it returns SOME identity,
    about which nothing is promised — in particular it is NOT promised to denote
    the same polynomial as its argument. Provenance / soundness: mapping.md /
    axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def factor_list(poly: int) -> PSeq[int]:
    """The unchanged factoring operation: applied to a polynomial it returns
    that polynomial's complete factor list, a determinate sequence that depends
    ONLY on its argument. The weakest behaviour the proof needs: it returns SOME
    determinate sequence as a function of `poly` (nothing is promised relating
    the lists of two DIFFERENT arguments). Because the result depends only on the
    argument, applying it to a polynomial other than the input yields, in
    general, a different list. Provenance / soundness: mapping.md /
    axiom_check.py."""


@Pure
@ContractOnly
def lone(poly: int) -> PSeq[int]:
    """The single-element result the function returns when the factoring yields
    only one element: the input as ONE element. A determinate one-element
    sequence depending only on its argument; nothing further is promised.
    Provenance / soundness: mapping.md / axiom_check.py."""
    Ensures(len(Result()) == 1)
# axioms-end


# pure-start
# pure-end


def ext_factor(lc: int, poly: int) -> List[int]:
    # pre-conditions-start
    # `poly` is the opaque polynomial identity; the modeled domain is the input
    # shapes the F2P / PASS_TO_PASS extension-factorisation tests exercise.
    Requires(0 <= poly and poly <= 4)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # COMPLETE: the returned list is EXACTLY the factor list the factoring
    # operation reads off the INPUT itself -- every factor present, none
    # dropped, an input that splits returned as all of its separate factors.
    # When the factoring yields two or more elements the result is precisely
    # that list; when it yields a single element the result is that
    # single-element list (the legitimate non-splitting case). The result is
    # therefore pinned to the factoring APPLIED TO THE INPUT (`factor_list(poly)`),
    # not to any other polynomial.
    Ensures(Implies(len(factor_list(poly)) >= 2, ToSeq(Result()) == factor_list(poly)))
    Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH BUG: the factoring is applied to the related polynomial `other`
    # instead of the input. `other` may carry fewer factors, so the factoring
    # reads back fewer (or collapses to a single element and the single-element
    # branch returns that one un-split element), dropping factors of the input.
    other = other_poly(poly)
    images = factor_list(other)
    result = []  # type: List[int]
    if len(images) <= 1:
        blob = lone(poly)
        i = 0
        while i < len(blob):
            # invariants-start
            Invariant(Acc(list_pred(result)))
            Invariant(images == factor_list(other))
            Invariant(blob == lone(poly))
            Invariant(0 <= i and i <= len(blob))
            Invariant(ToSeq(result) == blob.take(i))
            # invariants-end
            result = result + [blob[i]]
            i = i + 1
    else:
        i = 0
        while i < len(images):
            # invariants-start
            Invariant(Acc(list_pred(result)))
            Invariant(images == factor_list(other))
            Invariant(0 <= i and i <= len(images))
            Invariant(ToSeq(result) == images.take(i))
            # invariants-end
            result = result + [images[i]]
            i = i + 1
    return result
    # impl-end
