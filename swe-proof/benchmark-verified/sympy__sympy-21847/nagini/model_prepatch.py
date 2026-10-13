"""Twin-artifact model for sympy__sympy-21847.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A candidate term over a set of variables is described by its exponent vector
  `powers` (one non-negative integer per variable: how many times that variable
  occurs in the term). The TOTAL DEGREE of the term is the arithmetic sum of the
  exponents across all variables.

  When enumerating terms subject to a single lower bound `min_degree` on the
  total degree, a candidate is RETAINED exactly when its total degree is at
  least `min_degree`. The documented contract is
  `min_degree <= total_degree(term)`: the threshold is compared against the
  whole term's total degree, i.e. the arithmetic sum of the per-variable
  exponents. So a multi-variable term such as one with exponent vector `[2, 1]`
  (total degree 3) must be retained at `min_degree = 3`.

  The same retention rule governs both the case where the variables commute and
  the case where they do not — the lower-bound test is on the total degree of
  the enumerated term in either case.

Modelling: the exponent vector is `powers: List[int]` of non-negative integers;
the total degree is spelled out deeply as the front-recursive fold `deg_sum`
(the arithmetic sum over the vector), the canonical sequence-fold pattern (one
unfold per loop step). The specification is carried by `PSeq[int]` via `ToSeq`.
No callee is axiomatized: the modelled reduction is spelled out deeply, not
hidden behind an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the reduction is modelled deeply as the fold deg_sum below; no
# unchanged opaque callee is consumed by the proof.)
# axioms-end


# pure-start
@Pure
def deg_sum(p: PSeq[int]) -> int:
    """Total degree: the arithmetic sum of the per-variable exponents.
    Front-recursive (one unfold per loop step — the canonical fold pattern)."""
    if len(p) == 0:
        return 0
    return p[0] + deg_sum(p.drop(1))
# pure-end


def keep_comm(powers: List[int], min_degree: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(powers), 1 / 2))
    Requires(min_degree >= 0)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(powers),
                                            powers[i] >= 0),
                                    [[powers[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(powers), 1 / 2))
    # The candidate is retained exactly when its TOTAL degree (the sum of the
    # per-variable exponents) meets the lower bound.
    Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the lower bound is tested against the largest single
    # per-variable exponent instead of the total degree.
    running = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(running >= 0)
        Invariant(Forall(int, lambda j: (Implies(i <= j and j < len(powers),
                                                 powers[j] <= running),
                                         [[powers[j]]])))
        # invariants-end
        if powers[i - 1] >= running:
            running = powers[i - 1]
        i = i - 1
    return running >= min_degree
    # impl-end


def keep_noncomm(powers: List[int], min_degree: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(powers), 1 / 2))
    Requires(min_degree >= 0)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(powers),
                                            powers[i] >= 0),
                                    [[powers[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(powers), 1 / 2))
    # The candidate is retained exactly when its TOTAL degree (the sum of the
    # per-variable exponents) meets the lower bound.
    Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the lower bound is tested against the largest single
    # per-variable exponent instead of the total degree.
    running = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(running >= 0)
        Invariant(Forall(int, lambda j: (Implies(i <= j and j < len(powers),
                                                 powers[j] <= running),
                                         [[powers[j]]])))
        # invariants-end
        if powers[i - 1] >= running:
            running = powers[i - 1]
        i = i - 1
    return running >= min_degree
    # impl-end
