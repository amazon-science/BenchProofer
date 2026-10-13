"""Twin-artifact model for sympy__sympy-17318.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A symbolic additive expression is matched against the shape ``a + b*sqrt(r)``.
  The matcher first decides whether to use the FAST path, a helper that splits a
  sum of square-root terms by the greatest common divisor of their radicands.

  Each addend has two abstract facets that decide the branch: whether it is
  ELIGIBLE for the fast splitting path (facet E), and whether it CARRIES A
  NESTED RADICAL (facet N). The splitting helper is only well-defined for a sum
  every addend of which has facet E, and only when the sum actually contains at
  least one square-root term; handed a sum with no square-root term it has
  nothing to split and cannot produce a result.

  The behaviour pinned here:

    (1) The fast path is taken EXACTLY when every addend has facet E. When that
        holds for a genuine multi-term sum, at least one addend is a square-root
        term, so the helper's precondition (at least one square-root term
        present) is met and the fast path yields a match.

    (2) If some addend lacks facet E, the fast path is NOT taken — calling the
        helper there would violate its precondition. Instead the matcher falls
        back to a depth-based analysis. When every addend is shallow (lacks
        facet N, maximal nesting depth zero), that analysis finds nothing to
        denest and the result is NO MATCH (an empty match), with no error.

    (3) Otherwise (some addend lacks facet E while another carries facet N) the
        depth-based analysis proceeds and yields a match around the deepest
        addend.

Each addend is abstracted by an integer category code over the two facets
(E = fast-path eligible, N = carries a nested radical):

    0  facet E, no N           (a fast-eligible non-nested addend)
    1  facet E, with N         (a fast-eligible square-root term)
    2  not E, no N             (a non-eligible non-nested addend)
    3  not E, with N           (a non-eligible nested addend)

The sum of addend codes is carried as ``PSeq[int]`` (Nagini bans ``str``/object
indexing in specs); the per-element predicates are folded front-recursively so a
single unfold is available per loop step. The empty match is signalled by a
user-defined exception (a builtin exception in an ``Exsures`` crashes the Nagini
translator; mapping.md §2). The unchanged splitting helper is axiomatized with
its at-least-one-square-root-term precondition (A-consumed; mapping.md §3).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NoMatch(Exception):
    """Signals the sum does not match ``a + b*sqrt(r)`` — the depth-based
    analysis found nothing to denest (maximal depth zero). Stands in for the
    empty list the real matcher returns; a builtin exception in an ``Exsures``
    crashes the Nagini translator (mapping.md §2)."""


# axioms-start
@Pure
@ContractOnly
def split_by_radicand_gcd(codes: PSeq[int], k: int) -> int:
    """The unchanged splitting helper (radicand-gcd split of a sum of
    square-root terms). It is meaningful only for a sum every addend of which
    has facet E (fast-path eligible) AND that contains at least one square-root
    term (``k`` of them, ``k >= 1``); handed a sum with no square-root term it
    cannot produce a result. Returns the SPLIT outcome for the match it
    produces — an opaque value distinct from the depth analysis' match marker,
    so the result records that the split helper, not the depth analysis,
    produced this match.
    Weakest contract the proof needs; provenance + soundness check in
    mapping.md / axiom_check.py.
    """
    Requires(all_fast_facet(codes))
    Requires(k == num_surds(codes))
    Requires(k >= 1)
    # A match is produced by the split helper. Its result is the SPLIT outcome,
    # an opaque value distinct from the depth analysis' match marker (1): the
    # exact value is NOT pinned, only that it differs from 1, so a caller's
    # result observably records WHICH mechanism produced the match while the
    # value itself can be obtained ONLY by invoking this helper (a literal
    # cannot be proved equal to it).
    Ensures(Result() != 1)
# axioms-end


# pure-start
@Pure
def code_fast_facet(c: int) -> bool:
    """An addend with facet E (fast-path eligible): codes 0 and 1."""
    return c == 0 or c == 1


@Pure
def code_is_surd(c: int) -> bool:
    """An addend that is a square-root term contributing to the split (code 1:
    fast-path eligible WITH a nested radical)."""
    return c == 1


@Pure
def code_has_depth(c: int) -> bool:
    """An addend carrying facet N (a nested radical, maximal depth at least
    one): codes 1 and 3."""
    return c == 1 or c == 3


@Pure
def all_fast_facet(s: PSeq[int]) -> bool:
    """Every addend of the sum has facet E (fast-path eligible). Front-recursive
    so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return code_fast_facet(s[0]) and all_fast_facet(s.drop(1))


@Pure
def num_surds(s: PSeq[int]) -> int:
    """How many addends are square-root terms (code 1)."""
    Ensures(Result() >= 0)
    Ensures(Result() <= len(s))
    if len(s) == 0:
        return 0
    return (1 if code_is_surd(s[0]) else 0) + num_surds(s.drop(1))


@Pure
def any_has_depth(s: PSeq[int]) -> bool:
    """Some addend carries facet N (a nested radical, maximal depth at least
    one)."""
    if len(s) == 0:
        return False
    return code_has_depth(s[0]) or any_has_depth(s.drop(1))
# pure-end


def match_additive(codes: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(codes), 1 / 2))
    # The argument is a genuine multi-term sum of valid addend codes.
    Requires(len(codes) >= 2)
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(codes),
                             0 <= codes[k] and codes[k] <= 3),
                     [[codes[k]]])))
    # A genuine multi-term sum every addend of which has facet E always contains
    # at least one square-root term (a sum of only non-radical addends would
    # collapse to a single number and not be a multi-term sum). This frame fact
    # ties the guard to the helper's precondition.
    Requires(Implies(all_fast_facet(ToSeq(codes)),
                     num_surds(ToSeq(codes)) >= 1))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(codes), 1 / 2))
    # A match was produced ONLY along a path that is sound: either every addend
    # has facet E (the SPLIT path) or some addend carries facet N so the depth
    # analysis matches (the DEPTH path).
    Ensures(all_fast_facet(ToSeq(codes)) or any_has_depth(ToSeq(codes)))
    # The result records WHICH mechanism produced the match, so the two paths are
    # observably distinct. On the SPLIT path the result is exactly the value the
    # splitting helper returns for this sum -- pinning the OUTPUT of the modeled
    # computation, not a literal: the helper's value is opaque, so the only way
    # to satisfy this clause is to actually invoke the helper. On the DEPTH path
    # the result is the depth-analysis match marker 1.
    Ensures(Implies(all_fast_facet(ToSeq(codes)) and num_surds(ToSeq(codes)) >= 1,
                    Result() == split_by_radicand_gcd(ToSeq(codes),
                                                       num_surds(ToSeq(codes)))))
    Ensures(Implies(not all_fast_facet(ToSeq(codes)), Result() == 1))
    # post-conditions-end
    # The empty match: no addend carries facet N (no nesting) AND not every
    # addend has facet E — a shallow sum with a non-eligible addend. The fast
    # path is provably NOT taken here (its precondition would be violated).
    Exsures(NoMatch,
            Acc(list_pred(codes), 1 / 2)
            and not all_fast_facet(ToSeq(codes))
            and not any_has_depth(ToSeq(codes)))
    # impl-start
    # Pre-patch guard: take the fast path when every addend is non-nested-or-
    # eligible (codes 0, 1, 2) — admitting addends that lack facet E (the
    # non-eligible non-nested code 2) as long as they are not nested. A shallow
    # sum with such a non-eligible addend is therefore admitted to the fast path
    # even though the helper's facet-E precondition is not met.
    all_admit = True
    i = 0
    while i < len(codes):
        # invariants-start
        Invariant(Acc(list_pred(codes), 1 / 2))
        Invariant(0 <= i and i <= len(codes))
        Invariant(MustTerminate(len(codes) - i + 1))
        # invariants-end
        if codes[i] == 3:
            all_admit = False
        i = i + 1
    if all_admit:
        k = num_surds(ToSeq(codes))
        return split_by_radicand_gcd(ToSeq(codes), k)
    if not any_has_depth(ToSeq(codes)):
        raise NoMatch()
    return 1
    # impl-end
