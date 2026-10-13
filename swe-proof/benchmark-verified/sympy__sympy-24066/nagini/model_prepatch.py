"""Twin-artifact model for sympy__sympy-24066.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the scale factor and the dimension of an expression are collected for a
  unit-bearing applied function (a function symbol applied to a list of
  argument expressions), the dimension reported for each argument must be in
  canonical form: an argument whose dimension is dimensionless must be reported
  with the canonical dimensionless dimension, the one whose name is the unit 1,
  rather than with whatever (possibly non-canonical) dimension expression the
  argument happened to carry. Any argument whose dimension is genuinely NOT
  dimensionless is reported with its own dimension, unchanged.

  This matters because a dimensionless dimension may be carried in a
  non-canonical form (a product/quotient of base dimensions whose net powers all
  cancel) that is structurally unequal to the canonical dimensionless dimension.
  Downstream, two dimensions are compared for structural equality (e.g. when a
  sum requires all addends to share one dimension); a dimensionless argument
  dimension that is not first reduced to the canonical form would compare
  unequal to the canonical dimensionless dimension and be rejected, even though
  it IS dimensionless. Canonicalising each dimensionless argument dimension to
  the canonical form makes that comparison succeed.

Dimensions are abstracted by integer "dimension codes": the canonical
dimensionless dimension (the one whose name is the unit 1) is the distinguished
code ``CANON_ONE``; every other code denotes some other dimension expression. A
code may denote a dimension that is dimensionless yet non-canonical (a code
different from ``CANON_ONE`` for which the dimension system nonetheless reports
dimensionless). Whether a code denotes a dimensionless dimension is decided by
the dimension system, modelled by the unchanged ``is_dimensionless`` callee.

The argument dimensions are a ``List[int]`` of codes; the result is the parallel
``List[int]`` of canonicalised codes (the scale-factor component, which is
unchanged, is not modelled). The structural correspondence to a sum's
all-addends-equal comparison is pinned by the canonical-equality clause.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def resolvable(code: int) -> bool:
    """Whether the dimension system can compute the dimensional dependencies of
    the dimension denoted by this code WITHOUT signalling an error — i.e. the
    sub-domain on which the dimensionless test below produces a verdict at all.
    The dimensionless test is only a partial predicate: a code that denotes a
    dimension whose dependencies cannot be resolved (a dimension built from
    incompatible or non-resolvable components) has no dimensionless verdict, and
    consulting it for one is a domain error. This opaque predicate carves out the
    domain on which the verdict exists; only codes for which it holds are fed to
    the test. Provenance + executable soundness check: mapping.md / axiom_check.py."""


@Pure
@ContractOnly
def is_dimensionless(code: int) -> bool:
    """The dimension system's dimensionless test on a dimension, here on the
    dimension's integer code (the unchanged community callee
    ``get_dimension_system().is_dimensionless``). It is a PARTIAL opaque
    predicate, defined only where the dimension's dependencies are resolvable
    (``resolvable(code)``); outside that domain the dimension system signals a
    domain error rather than returning a verdict, so the test is not invoked
    there. Within its domain the verdict is whatever the dimension system
    decides — a code may denote a dimensionless dimension yet differ from the
    canonical code ``CANON_ONE`` (a non-canonical dimensionless dimension). The
    proof relies on no particular verdict, only that the SAME code yields the
    SAME verdict at every site (function purity). Provenance + executable
    soundness check: mapping.md / axiom_check.py."""
    Requires(resolvable(code))
# axioms-end


# pure-start
@Pure
def CANON_ONE() -> int:
    """The code of the canonical dimensionless dimension — the dimension whose
    name is the unit 1. Distinguished so that the result can be compared for
    structural equality against it."""
    return 1


@Pure
def all_resolvable(s: PSeq[int]) -> bool:
    """Whether every code in the sequence has a dimensionless verdict (each is
    ``resolvable``) — the domain on which the whole-sequence canonicalisation is
    defined. Front-recursive so a single unfold exposes the head's resolvability
    and the tail's, matching the canonicalisation fold step-for-step."""
    if len(s) == 0:
        return True
    return resolvable(s[0]) and all_resolvable(s.drop(1))


@Pure
def canon_dim(code: int) -> int:
    """The canonicalised dimension code for one argument: the canonical
    dimensionless code when the argument's dimension is dimensionless, otherwise
    the argument's own code unchanged. Defined only on the domain where the
    dimensionless verdict exists (``resolvable(code)``)."""
    Requires(resolvable(code))
    if is_dimensionless(code):
        return CANON_ONE()
    return code


@Pure
def canon_seq(s: PSeq[int]) -> PSeq[int]:
    """The canonicalisation of a whole sequence of argument dimension codes:
    canonicalise each code. Front-recursive so a single unfold is available to
    callers per loop step. Defined only when every code has a dimensionless
    verdict (``all_resolvable``)."""
    Requires(all_resolvable(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(canon_dim(s[0])) + canon_seq(s.drop(1))
# pure-end


def collect_argument_dimensions(arg_dims: List[int]) -> List[int]:
    # pre-conditions-start
    # Read-only input: the argument dimension codes are not mutated, so they are
    # held at fractional permission, required AND ensured (directive 5).
    Requires(Acc(list_pred(arg_dims), 1 / 2))
    # The dimensionless test is partial: it has a verdict only for codes whose
    # dimensional dependencies resolve. Within the modeled domain every argument
    # dimension is such a code, so the per-element test is always well-defined;
    # codes outside this domain are not handled here (the test would signal a
    # domain error, not a verdict). Stated both element-wise (for the per-element
    # test) and as the fold-shaped ``all_resolvable`` (the domain of the
    # whole-sequence canonicalisation) — two views of the same total domain.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                             resolvable(arg_dims[k])))))
    Requires(all_resolvable(ToSeq(arg_dims)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(arg_dims), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The read-only input is unchanged, so its codes still all have a
    # dimensionless verdict — the domain on which the canonicalisation below is
    # defined (carries the precondition's well-definedness to the post-state).
    Ensures(all_resolvable(ToSeq(arg_dims)))
    # The result is the parallel list of per-argument canonicalised codes,
    # the per-element canonicalisation of the input.
    Ensures(len(Result()) == len(arg_dims))
    Ensures(ToSeq(Result()) == canon_seq(ToSeq(arg_dims)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(arg_dims)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(arg_dims), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(arg_dims))
        # Every argument dimension code has a dimensionless verdict (the modeled
        # domain), so each per-element test and the canonicalisation fold below
        # are well-defined. Kept in both views: element-wise (per-element test)
        # and fold-shaped over the not-yet-processed suffix (canon_seq's domain).
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(arg_dims),
                                                  resolvable(arg_dims[k])))))
        Invariant(all_resolvable(ToSeq(arg_dims)))
        Invariant(all_resolvable(ToSeq(arg_dims).drop(i)))
        Invariant(len(result) == len(arg_dims) - i)
        Invariant(ToSeq(result) == canon_seq(ToSeq(arg_dims).drop(i)))
        # invariants-end
        c = arg_dims[i - 1]
        Assert(ToSeq(arg_dims).drop(i - 1)[0] == c)
        Assert(ToSeq(arg_dims).drop(i - 1).drop(1) == ToSeq(arg_dims).drop(i))
        Assert(resolvable(c))
        Assert(all_resolvable(ToSeq(arg_dims).drop(i - 1)))
        # Pre-patch: the argument dimension is reported verbatim, with no
        # canonicalisation of a dimensionless-but-non-canonical dimension.
        result = [c] + result
        i = i - 1
    Assert(ToSeq(arg_dims).drop(0) == ToSeq(arg_dims))
    Assert(all_resolvable(ToSeq(arg_dims)))
    return result
    # impl-end
