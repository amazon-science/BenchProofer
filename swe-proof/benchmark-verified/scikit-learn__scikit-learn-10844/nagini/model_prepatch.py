"""Twin-artifact model for scikit-learn__scikit-learn-10844.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A pair-counting similarity index between two clusterings is computed from
  three non-negative integer pair-counts derived from a contingency table:

    * `tk` — the number of concordant pairs (pairs grouped together in BOTH
      clusterings),
    * `pk` — the number of pairs grouped together in the first clustering,
    * `qk` — the number of pairs grouped together in the second clustering.

  Structurally a concordant pair is also counted by each marginal, so
  `0 <= tk <= pk` and `0 <= tk <= qk`; both marginals are positive whenever
  there is any concordant pair.

  The index is the geometric mean of the two conditional concordance ratios:
  it equals `sqrt(tk / pk) * sqrt(tk / qk)` when there is at least one
  concordant pair, and is `0` when there is none. Because each conditional
  ratio lies in the unit interval, the index is a similarity that always lies
  in `[0, 1]`; it must be a finite, well-defined number for EVERY admissible
  input, including the large-count regime where the two marginals are each
  enormous.

  The arithmetic that produces the index must stay within the representable
  range of the working numeric domain: every quantity formed while evaluating
  it — in particular every product, and every value handed to the square-root
  operation — must be representable (no greater than the domain's maximum
  magnitude `m`). Each marginal on its own is representable; the index must be
  obtained WITHOUT first forming the cross product of the two marginals, since
  that cross product can exceed the representable range even when each marginal
  does not. Forming the two unit-interval conditional ratios first keeps every
  intermediate representable and the result finite.

The pair-counts and the index are interpreted real numbers (verified with
`--float-encoding=real`) because the behaviour at stake is a real-valued
numeric computation that the tests probe to floating tolerance, and the
representability bound `m` models the finite numeric domain in which it runs.
The three numeric operations the computation uses — division, square root and
multiplication — are the unchanged numeric callees; they are axiomatized with
the weakest sufficient contracts (their true bounds plus the representability
precondition that gates an overflow value out of the domain), and validated
against the real operations out-of-band by axiom_check.py (G-AX). The
square-root's representability precondition is what forces an overflow-free
evaluation order.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def ratio(a: float, b: float, m: float) -> float:
    """Real division `a / b` of a non-negative numerator by a strictly positive
    representable denominator that dominates it (`0 <= a <= b <= m`). The
    quotient is then a real in the unit interval. The unchanged numeric division
    callee; provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(b > 0.0)
    Requires(a >= 0.0)
    Requires(a <= b)
    Requires(b <= m)
    Ensures(Result() == a / b)
    Ensures(Result() >= 0.0)
    Ensures(Result() <= 1.0)


@Pure
@ContractOnly
def root(x: float, m: float) -> float:
    """Non-negative square root of a representable non-negative real (the
    unchanged numeric square-root callee). Defined only on a value that is
    itself representable in the working domain (`0 <= x <= m`): a value that has
    already overflowed the domain cannot be fed to it. Returns a non-negative
    real, and a real in the unit interval when the argument is in the unit
    interval. Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(x >= 0.0)
    Requires(x <= m)
    Ensures(Result() >= 0.0)
    Ensures(Implies(x <= 1.0, Result() <= 1.0))


@Pure
@ContractOnly
def mul(x: float, y: float) -> float:
    """Real multiplication `x * y` of two unit-interval reals; the product is
    then itself in the unit interval. The unchanged numeric multiplication
    callee; provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(x >= 0.0 and x <= 1.0)
    Requires(y >= 0.0 and y <= 1.0)
    Ensures(Result() == x * y)
    Ensures(Result() >= 0.0)
    Ensures(Result() <= 1.0)
# axioms-end


# pure-start
# (no pure helpers needed — the index is the spelled-out arithmetic below)
# pure-end


def pair_similarity_index(tk: float, pk: float, qk: float, m: float) -> float:
    # pre-conditions-start
    # The representable bound is a genuine positive magnitude, large enough that
    # each marginal on its own is representable (the marginals are widened to a
    # domain that holds them) but NOT large enough to be assumed to hold their
    # cross product.
    Requires(m >= 1.0)
    # The pair-counts are non-negative reals and each marginal is representable.
    Requires(tk >= 0.0)
    Requires(pk >= 0.0 and pk <= m)
    Requires(qk >= 0.0 and qk <= m)
    # Structural facts of the contingency counting: a concordant pair is counted
    # by each marginal, so a concordant pair forces both marginals positive and
    # each conditional ratio into the unit interval.
    Requires(tk <= pk)
    Requires(tk <= qk)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # With at least one concordant pair the index is the geometric mean of the
    # two conditional concordance ratios.
    Ensures(Implies(tk > 0.0,
                    Result() == mul(root(ratio(tk, pk, m), m),
                                    root(ratio(tk, qk, m), m))))
    # With no concordant pair the index is exactly zero.
    Ensures(Implies(tk == 0.0, Result() == 0.0))
    # The index is a finite similarity in the unit interval for EVERY admissible
    # input — including the large-count regime — never an out-of-range or
    # ill-defined value.
    Ensures(Result() >= 0.0)
    Ensures(Result() <= 1.0)
    # post-conditions-end
    # impl-start
    if tk != 0.0:
        # Pre-patch evaluation order: form the cross product of the two
        # marginals FIRST and take the square root of that single combined
        # quantity, then divide. The combined cross product can exceed the
        # representable range of the working domain even when each marginal is
        # itself representable, so the value handed to the square root is not
        # known to be representable.
        prod = pk * qk
        denom = root(prod, m)
        result = ratio(tk, denom, m)
    else:
        result = 0.0
    return result
    # impl-end
