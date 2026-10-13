"""Twin-artifact model for matplotlib__matplotlib-14623.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an axis view interval is set from a requested pair of endpoints, the
  stored interval must keep the orientation the caller requested. If the caller
  asks for a descending interval (first endpoint greater than the second), the
  stored interval must remain descending; if the caller asks for an ascending
  interval, it must remain ascending. This must hold uniformly, independently
  of the range-conditioning step that an axis may apply to its endpoints to
  avoid singular transforms and to clamp the range to the domain admissible for
  its scale -- a step which, for some scales, normalises the endpoints into
  ascending order. The conditioning may only adjust endpoint magnitudes; it may
  never decide the final orientation. The endpoint values themselves are
  preserved whenever the requested endpoints are distinct and already admissible
  for the scale.

The endpoints are modelled as `int` (the tested behaviour -- which of two
distinct admissible endpoints ends up first -- depends only on their order, not
on floating-point magnitude; refinement.md states the carrier correspondence).
The range-conditioning step (locator non-singular expansion followed by the
scale's domain clamp) is an UNCHANGED callee, axiomatised as `conditioned_lo` /
`conditioned_hi`: a pair-valued operation that always returns its two endpoints
in ascending order -- preserving the values when the endpoints are distinct, and
expanding the degenerate range into a strictly-ascending surrounding interval
when they are equal (the observable behaviour of a logarithmic axis'
conditioning). Its soundness against the real callees is checked out-of-band by
axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def conditioned_lo(lo: int, hi: int) -> int:
    """First component of the unchanged range-conditioning callee
    (locator non-singular expansion then the scale's domain clamp), applied to
    a requested endpoint pair of admissible (positive) endpoints.

    The conditioning ALWAYS normalises its output to ascending order and never
    decides the final orientation. For two DISTINCT endpoints it returns the
    smaller value, preserving the endpoint magnitudes. For two EQUAL endpoints
    it expands the degenerate range into a strictly-larger ascending interval;
    the only guaranteed fact about the first component there is that it ends up
    strictly below the (paired) second component -- the concrete expanded
    magnitude is scale-dependent and is NOT claimed.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    # The endpoints are admissible (positive) and lie in the magnitude range
    # over which the carrier is order-faithful and the conditioning preserves
    # distinct endpoint values exactly. Above this bound the non-singular
    # expansion fires on too-narrow relative gaps and the int->float carrier
    # loses distinctness; the tested inputs all sit well inside it (mapping.md
    # 2 / 3.1).
    Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
    # Distinct endpoints: the smaller value is preserved exactly (min first).
    # Equal endpoints: no exact value is claimed -- the only consumed fact is
    # the cross-component ascending relation stated on conditioned_hi.
    Ensures(Implies(lo != hi, Result() == (lo if lo < hi else hi)))


@Pure
@ContractOnly
def conditioned_hi(lo: int, hi: int) -> int:
    """Second component of the unchanged range-conditioning callee. For two
    distinct admissible (positive) endpoints it returns the larger value; for
    two equal endpoints it returns the upper bound of the expanded ascending
    interval -- whose concrete magnitude is scale-dependent and NOT claimed.
    The only guaranteed (and only consumed) fact is the always-ascending
    relation: the second component is strictly greater than the first
    component for the same endpoint pair.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
    # Distinct endpoints: the larger value is preserved exactly (max second).
    Ensures(Implies(lo != hi, Result() == (hi if lo < hi else lo)))
    # Always-ascending: the conditioning returns its pair in ascending order
    # for EVERY admissible endpoint pair (distinct or equal). This is the
    # weakest fact the orientation proof consumes; no concrete equal-case
    # magnitude is asserted.
    Ensures(conditioned_lo(lo, hi) < Result())
# axioms-end


# pure-start
# (no pure helpers needed beyond the axiomatised conditioning callee)
# pure-end


def set_axis_interval(lo: int, hi: int) -> Tuple[int, int]:
    # pre-conditions-start
    # The endpoints reaching the conditioning step are admissible for the scale
    # (positive, as the log-domain validation upstream guarantees) and lie in
    # the order-faithful, value-preserving magnitude range (the tested inputs
    # are well inside it; mapping.md 2). They may be distinct (the
    # orientation-preserving case) or equal (the singular case that the
    # conditioning expands).
    Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # When the requested endpoints are distinct, the stored interval keeps the
    # requested orientation: a descending request stays descending, an ascending
    # request stays ascending -- regardless of how the conditioning step
    # reorders its output -- and the endpoint values are preserved exactly (the
    # conditioning does not expand an already-admissible non-degenerate range).
    Ensures(Implies(lo > hi, Result()[0] > Result()[1]))
    Ensures(Implies(lo < hi, Result()[0] < Result()[1]))
    Ensures(Implies(lo != hi, Result()[0] == lo and Result()[1] == hi))
    # When the requested endpoints are equal, the conditioning expands the
    # degenerate range, so the stored interval is strictly ascending.
    Ensures(Implies(lo == hi, Result()[0] < Result()[1]))
    # post-conditions-end
    # impl-start
    swapped = lo > hi
    a = conditioned_lo(lo, hi)
    b = conditioned_hi(lo, hi)
    # The conditioning normalises to strictly ascending order; the requested
    # orientation, captured before conditioning, is restored afterwards.
    if swapped:
        # caller requested descending: restore the requested orientation.
        tmp = a
        a = b
        b = tmp
    return (a, b)
    # impl-end
