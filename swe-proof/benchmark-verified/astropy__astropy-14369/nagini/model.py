"""Twin-artifact model for astropy__astropy-14369.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A chain of operands separated by the division operator, written left to
  right as `u(0) / u(1) / ... / u(n-1)`, denotes repeated division grouped
  from the LEFT: `(((u(0) / u(1)) / u(2)) / ...) / u(n-1)`.  Each operand
  carries its own intrinsic exponent q(i) (an operand may be written with an
  explicit exponent of its own, e.g. a squared length).  Under left grouping
  the leading operand contributes with its intrinsic exponent unchanged and
  EVERY following operand is divided in exactly once, so it contributes with
  its intrinsic exponent NEGATED -- independent of how deep in the chain it
  sits.  A chain may also open with the division operator, in which case
  there is no leading operand and every operand of the chain, the first
  included, is divided in.  That is, with `leading` marking a chain that
  opens with the division operator, the resulting exponent of the operand at
  chain position i is

        +q(i)   if i == 0 and not leading
        -q(i)   otherwise.

This is the observable property the issue demands: the operands after the
first must NOT have their exponents re-flipped according to their depth in
the chain (which is what jumbles the order of the division), and an operand
written with its own exponent must keep that exponent's MAGNITUDE.

A chain is modelled as a `List[int]` of the operands' intrinsic exponents,
one per operand position, plus the `leading` flag; the result is modelled as
the `List[int]` of resulting integer exponents, one per operand position (the
exponent vector of the composite the chain denotes).  Operand identity is
irrelevant to the exponent the grouping assigns, so it is not carried; when
two positions name the same quantity the composite's exponent for that
quantity is the SUM of their positions' entries, which this vector
determines.  No rich object, scale, or dimensional algebra is needed.  The
specification is carried over `PSeq[int]` via `ToSeq` (Nagini bans `str`
indexing and rich library objects).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axiom: the behaviour is modelled deeply as the exponent rule
# below — there is no unchanged opaque callee the proof depends on.)
# axioms-end


# pure-start
@Pure
def chain_power(i: int, power: int, leading: bool) -> int:
    """Resulting exponent of the operand at position ``i`` of a left-grouped
    division chain, given that operand's own intrinsic exponent ``power``:
    the leading operand of a chain that does not open with the division
    operator keeps ``power``; every other operand is divided in exactly once
    and so receives ``-power``."""
    Requires(0 <= i)
    if i == 0 and not leading:
        return power
    return -power
# pure-end


def reduce_division_chain(powers: List[int], leading: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(powers), 1 / 2))
    Requires(len(powers) >= 1)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(powers), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # One exponent per operand position.
    Ensures(len(Result()) == len(powers))
    # Left-grouped division: the leading operand of a chain that does not open
    # with the division operator keeps its own exponent; every other operand
    # has its own exponent negated exactly once.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result()),
                                            Result()[k] == chain_power(k, powers[k], leading)),
                                    [[Result()[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    n = len(powers)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(powers) == n)
        Invariant(len(result) == n - i)
        # result currently holds the exponents of chain positions i .. n-1.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < n - i,
                                                  result[k] == chain_power(i + k, powers[i + k], leading)),
                                          [[result[k]]])))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        old = result
        q = powers[i - 1]
        if i - 1 == 0 and not leading:
            # combined_units seed: the leading unit_expression keeps its own
            # exponent.
            result = [q] + result
        else:
            # combined_units DIVISION unit_expression: the accumulated left
            # group divided by the next single operand -> that operand's own
            # exponent is negated exactly once.
            result = [-q] + result
        # The new head is the exponent of chain position i-1.
        Assert(result[0] == chain_power(i - 1, powers[i - 1], leading))
        Assert(ToSeq(result).drop(1) == ToSeq(old))
        Assert(Forall(int, lambda k: (Implies(1 <= k and k < len(result),
                                              result[k] == old[k - 1]),
                                       [[result[k]]])))
        i = i - 1
    Assert(i == 0)
    Assert(len(result) == n)
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < n,
                                          result[k] == chain_power(k, powers[k], leading)),
                                  [[result[k]]])))
    return result
    # impl-end
