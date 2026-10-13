"""Twin-artifact model for sympy__sympy-15599.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A modulo-by-an-integer of a product is simplified factor by factor. The
  product is given as a list of factors; some factors are concrete integer
  constants, the rest are opaque (symbolic) factors that the operation must
  leave untouched. The divisor is a given integer modulus m with m >= 2.

  Reducing the product modulo m rewrites each factor independently:

    - a concrete-integer factor whose value is NOT a multiple of m is replaced
      by its least non-negative residue modulo m (the value r with 0 <= r < m
      and value - r a multiple of m);
    - every other factor -- an opaque factor, or an integer factor that already
      is a multiple of m -- is kept exactly as it stands.

  Thus the factor list shrinks each integer coefficient into the residue range
  [0, m): a coefficient of 3 against modulus 2 becomes 1, a coefficient of 8
  against modulus 4 becomes 0, while a coefficient already inside [0, m) and an
  opaque symbolic factor are unchanged.

The product's factors are modelled by two parallel `List[int]`: a 0/1 tag
saying whether each factor is a concrete integer, and the integer value carried
by such a factor (irrelevant for opaque factors). Whether a factor is integral
is never altered by the rewrite, so the operation returns the new list of factor
values; the specification is carried by `PSeq[int]` via `ToSeq`.

The least-non-negative-residue primitive of the unchanged numeric layer is the
single axiomatized callee (`residue`), value-preserving and total for m >= 2;
its soundness is checked out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def residue(value: int, m: int) -> int:
    """The unchanged numeric remainder primitive: the least non-negative residue
    of `value` modulo `m` for m >= 2. Total, deterministic and value-preserving
    in the sense that it lands in [0, m) and differs from `value` by a multiple
    of `m`.  Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(m >= 2)
    Ensures(0 <= Result() and Result() < m)
    Ensures((value - Result()) % m == 0)
    # being a residue is idempotent on values already in range
    Ensures(Implies(0 <= value and value < m, Result() == value))
# axioms-end


# pure-start
@Pure
def reduced_factor(is_int: int, value: int, m: int) -> int:
    """Value carried by one factor after reduction modulo m (m >= 2):
      integer factor not divisible by m -> its residue in [0, m)
      otherwise (opaque factor, or integer multiple of m) -> unchanged value.
    The integer-ness of a factor is never changed; only its carried value is."""
    Requires(m >= 2)
    if is_int == 1 and residue(value, m) != 0:
        return residue(value, m)
    return value
# pure-end


def reduce_coefficients(is_int: List[int], value: List[int],
                        m: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(is_int), 1 / 2))
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(m >= 2)
    Requires(len(is_int) == len(value))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(is_int), 1 / 2))
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(len(is_int) == len(value))
    Ensures(Acc(list_pred(Result())))
    # The reduced product keeps one value per original factor.
    Ensures(len(Result()) == len(value))
    # Every factor value is rewritten exactly by the per-factor reduction.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(value),
                Result()[k] == reduced_factor(is_int[k], value[k], m)),
        [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    n = len(value)
    result = []  # type: List[int]
    k = 0
    while k < n:
        # invariants-start
        Invariant(Acc(list_pred(is_int), 1 / 2))
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(m >= 2)
        Invariant(len(is_int) == len(value))
        Invariant(n == len(value))
        Invariant(0 <= k and k <= n)
        Invariant(len(result) == k)
        Invariant(Forall(int, lambda b: (
            Implies(0 <= b and b < k,
                    result[b] == reduced_factor(is_int[b], value[b], m)),
            [[result[b]]])))
        Invariant(MustTerminate(n - k + 1))
        # invariants-end
        if is_int[k] == 1 and residue(value[k], m) != 0:
            v = residue(value[k], m)
        else:
            v = value[k]
        # v is exactly the per-factor reduction for factor k.
        Assert(v == reduced_factor(is_int[k], value[k], m))
        old_result = result
        result = result + [v]
        Assert(len(result) == k + 1)
        Assert(Forall(int, lambda b: (
            Implies(0 <= b and b < k, result[b] == old_result[b]),
            [[result[b]]])))
        Assert(result[k] == v)
        Assert(result[k] == reduced_factor(is_int[k], value[k], m))
        k = k + 1
    return result
    # impl-end
