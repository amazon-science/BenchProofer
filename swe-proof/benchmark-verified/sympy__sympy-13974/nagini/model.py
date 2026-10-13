"""Twin-artifact model for sympy__sympy-13974.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A tensor product is an ordered collection of factor expressions. Two related
  operations are specified:

  (1) Raising a tensor product to an exponent (``power_of_collection``). Given the
      ordered factors and a single exponent, the result is a tensor product with:
        * the same number of factors as the input, in the same order;
        * factor k equal to the power expression that raises input factor k to the
          given exponent (the value of the binary power map on that factor);
        * the same exponent used for every factor.

  (2) Simplifying ONE non-commutative factor of a product when that factor is such
      a power of a tensor product (``simp_pow_factor``). The simplifier replaces
      the power-of-a-tensor-product by its per-factor distribution (operation 1);
      a factor that is already a bare tensor product is returned unchanged; the
      decision is driven solely by whether the factor is a power whose base is a
      tensor product. This is the routing that lets the per-factor distribution be
      reached for a tensor-product power appearing as a factor of a product, not
      only as the whole expression.

A tensor product cannot be expressed in Nagini's fragment, so its content that the
operations touch — the ordered list of factor expressions — is the carrier
(``List[int]`` of opaque expression handles), and the exponent is one opaque
handle. The binary power map that takes one factor and one exponent to a power
expression is the single axiomatized callee (``pow_expr``), a deterministic map;
its soundness is checked out-of-band by axiom_check.py (G-AX). The specification of
a distributed result is the element-wise image of that map, carried by ``PSeq[int]``
via ``ToSeq`` (the front-recursive fold ``pointwise_pow``).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def pow_expr(base: int, exp: int) -> int:
    """The binary power map: the handle of the power expression that raises one
    factor handle ``base`` to the exponent handle ``exp`` (the symbolic
    ``base ** exp``), as a deterministic map over expression handles. Two
    properties are relied upon:

      * determinism / functionality — the result depends only on (base, exp), so
        every reader of the map sees the SAME power handle for the same
        (factor, exponent) pair;
      * non-triviality away from the identity exponent — when ``exp`` is not the
        identity exponent (the reserved handle ``1`` for the exponent one, which
        a power node never carries because ``base ** 1`` is the factor itself),
        the power expression is distinct from the factor: ``Result() != base``.

    The identity exponent is excluded by the precondition; on it the real power
    map returns the factor unchanged, so the axiom does not over-claim there.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(exp != 1)
    Ensures(Result() != base)
# axioms-end


# pure-start
@Pure
def pointwise_pow(s: PSeq[int], exp: int) -> PSeq[int]:
    """The factor list of a distributed result: the element-wise image of the
    power map on the factors of ``s`` at exponent ``exp``, in order.
    Front-recursive so a single unfold is available per loop step."""
    Requires(exp != 1)
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(pow_expr(s[0], exp)) + pointwise_pow(s.drop(1), exp)
# pure-end


def power_of_collection(args: List[int], exp: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(args), 1 / 2))
    # The identity exponent (handle 1) is excluded: a power node never carries it
    # (``base ** 1`` is the factor itself), so this operation is reached only for
    # a genuine, non-identity exponent.
    Requires(exp != 1)
    # The distribution must COMPLETE (total correctness): without this obligation
    # every Ensures below is claimed only of runs that reach the return, so an
    # implementation that never gets there satisfies the whole postcondition
    # vacuously. Level 2 leaves room for the list allocation it performs (at level
    # 1 the allocation's own obligation has nowhere below the caller to go); it
    # calls no other obligated method.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(args), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result has the same number of factors as the input, in the same order.
    Ensures(len(Result()) == len(args))
    # Factor k of the result is the value of the power map on input factor k at
    # the given exponent. Stated as the element-wise image over the actual input
    # factors, so the result is tied to a structural property of the input
    # carrier (its k-th factor), not to any constant or answer-key value.
    Ensures(ToSeq(Result()) == pointwise_pow(ToSeq(args), exp))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(args)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(args), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(args))
        Invariant(len(result) == len(args) - i)
        Invariant(ToSeq(result) == pointwise_pow(ToSeq(args).drop(i), exp))
        # At most i + 1 passes remain: the loop counts DOWN over the input
        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = args[i - 1]
        Assert(ToSeq(args).drop(i - 1)[0] == e)
        Assert(ToSeq(args).drop(i - 1).drop(1) == ToSeq(args).drop(i))
        result = [pow_expr(e, exp)] + result
        i = i - 1
    return result
    # impl-end


def simp_pow_factor(is_pow_of_tp: bool, factors: List[int], exp: int) -> List[int]:
    # pre-conditions-start
    # A single non-commutative factor of a product whose base is a tensor product:
    # `factors` are the tensor-product factors of that base (in order). The factor
    # is EITHER a power of that tensor product (`is_pow_of_tp` True), in which case
    # `exp` is the power's exponent, OR the bare tensor product itself
    # (`is_pow_of_tp` False). A power node never carries the identity exponent.
    Requires(Acc(list_pred(factors), 1 / 2))
    Requires(Implies(is_pow_of_tp, exp != 1))
    # The simplification must COMPLETE (total correctness): without this
    # obligation every Ensures below is claimed only of runs that reach the
    # return, so an implementation that never gets there satisfies the whole
    # postcondition vacuously. Level 3 is strictly above the callee it delegates
    # to (power_of_collection at 2).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(factors), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(factors))
    # Routing decision: a power-of-tensor-product factor is replaced by its
    # per-factor distribution (each base factor raised to the exponent); a bare
    # tensor-product factor passes through unchanged (factor k stays factor k).
    Ensures(Implies(is_pow_of_tp, ToSeq(Result()) == pointwise_pow(ToSeq(factors), exp)))
    Ensures(Implies(not is_pow_of_tp, ToSeq(Result()) == ToSeq(factors)))
    # post-conditions-end
    # impl-start
    if is_pow_of_tp:
        return power_of_collection(factors, exp)
    result = []  # type: List[int]
    i = len(factors)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(factors), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(factors))
        Invariant(len(result) == len(factors) - i)
        Invariant(ToSeq(result) == ToSeq(factors).drop(i))
        # At most i + 1 passes remain: the passthrough counts DOWN over the input
        # factors, i drops by exactly one per pass, and the guard i > 0 keeps the
        # bound >= 2 on entry to a pass (so it never reaches the unsatisfiable 0).
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = factors[i - 1]
        Assert(ToSeq(factors).drop(i - 1)[0] == e)
        Assert(ToSeq(factors).drop(i - 1).drop(1) == ToSeq(factors).drop(i))
        result = [e] + result
        i = i - 1
    return result
    # impl-end
