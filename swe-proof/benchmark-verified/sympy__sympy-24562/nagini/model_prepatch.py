"""Twin-artifact model for sympy__sympy-24562.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A ratio is formed by dividing one operand (the dividend) by another (the
  divisor). Each operand is an exact rational: the dividend has numerator
  `p_num` and positive denominator `p_den`; the divisor has numerator `q_num`
  -- supplied in textual form as a sequence of decimal-digit characters whose
  value is the integer it spells -- and positive denominator `q_den`.

  The constructed ratio is the quotient of the two operands,
  `(p_num / p_den) / (q_num / q_den)`, expressed as an integer
  numerator/denominator pair before any common-factor reduction:

      numerator   == p_num * q_den
      denominator == p_den * q_num

  where `q_num` is the integer value of the divisor's textual numerator. Both
  component integers are ordinary products of the operands' integer parts.

The divisor's textual numerator is modelled as `List[int]` of decimal-digit
code points (Nagini bans `str` indexing); the sequence theory `PSeq[int]`
carries the specification. The integer value of a digit sequence is named by
the function `read_int`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def read_int(digits: PSeq[int]) -> int:
    """The integer value of a non-empty all-digit sequence of decimal code
    points (the value the digit characters spell, e.g. the sequence `1 0 0`
    has value one hundred). Weakest contract the proof needs: a non-empty
    all-digit sequence has a non-negative integer value.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(digits) >= 1)
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(digits),
                 48 <= digits[k] and digits[k] <= 57), [[digits[k]]])))
    Ensures(Result() >= 0)


@Pure
@ContractOnly
def aux_value(digits: PSeq[int], n: int) -> int:
    """An auxiliary integer-valued function of a non-empty all-digit sequence
    and a positive multiplicity `n`. Its value is deliberately left
    unspecified -- the contract asserts only that it is a non-negative integer
    and, in particular, does NOT relate it to `read_int(digits)` in any way.
    A correct result therefore cannot depend on this quantity.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(digits) >= 1)
    Requires(n >= 1)
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(digits),
                 48 <= digits[k] and digits[k] <= 57), [[digits[k]]])))
    Ensures(Result() >= 0)
# axioms-end


# pure-start
# (no pure helpers required)
# pure-end


def combine_ratio(p_num: int, p_den: int,
                  q_digits: List[int], q_den: int) -> Tuple[int, int]:
    # pre-conditions-start
    Requires(Acc(list_pred(q_digits), 1 / 2))
    # The dividend is an exact ratio with a positive denominator.
    Requires(p_den >= 1)
    # The divisor's numerator is a non-empty digit sequence; its denominator
    # is positive.
    Requires(len(q_digits) >= 1)
    Requires(len(ToSeq(q_digits)) >= 1)
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(ToSeq(q_digits)),
                 48 <= ToSeq(q_digits)[k] and ToSeq(q_digits)[k] <= 57),
         [[ToSeq(q_digits)[k]]])))
    Requires(q_den >= 1)
    # The combination must terminate: the caller grants a finite obligation,
    # so a diverging implementation (frozen loop / unbounded self-call)
    # cannot satisfy this contract.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(q_digits), 1 / 2))
    Ensures(len(ToSeq(q_digits)) >= 1)
    Ensures(Forall(int, lambda k:
        (Implies(0 <= k and k < len(ToSeq(q_digits)),
                 48 <= ToSeq(q_digits)[k] and ToSeq(q_digits)[k] <= 57),
         [[ToSeq(q_digits)[k]]])))
    # The quotient's numerator is the dividend's numerator scaled by the
    # divisor's denominator.
    Ensures(Result()[0] == p_num * q_den)
    # The quotient's denominator is the dividend's denominator scaled by the
    # integer value of the divisor's textual numerator.
    Ensures(Result()[1] == p_den * read_int(ToSeq(q_digits)))
    # post-conditions-end
    # impl-start
    # Pre-patch (buggy) skeleton: the denominator accumulator is the same
    # variable that carries the divisor's textual numerator, so that numerator
    # is combined with the dividend's denominator -- repeating its characters
    # `p_den` times -- and only the resulting longer character sequence is then
    # read as a number (the auxiliary value aux_value(q_digits, p_den), which
    # the spec does not relate to read_int). The numerator branch is unchanged.
    out_num = p_num * q_den  # type: int
    out_den = aux_value(ToSeq(q_digits), p_den)  # type: int
    return (out_num, out_den)
    # impl-end
