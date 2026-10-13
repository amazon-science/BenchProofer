"""Twin-artifact model for scikit-learn__scikit-learn-12682.

Behaviour under specification (the desired behaviour, stated abstractly):

  A sparse-coding estimator exposes a user-controlled iteration budget. When
  the estimator encodes data with an iterative least-squares solver (either of
  the two coordinate-descent / least-angle lasso solvers), the solver is
  constructed with EXACTLY the iteration budget the user configured on the
  estimator. The budget the user supplies must propagate, unchanged, through
  the layered coding routines all the way to the solver that is built; it is
  never replaced by a constant library default at any layer.

  Concretely:
    (1) The generic single-block coder, when it builds either iterative lasso
        solver, gives that solver the iteration budget it was handed (never the
        solver class's own built-in default).
    (2) The estimator's encoding path hands the generic coder the iteration
        budget stored on the estimator (the value the user configured), rather
        than the coder routine's own parameter default.

  The end-to-end guarantee: for the iterative-lasso algorithms, the iteration
  budget the constructed solver receives equals the budget configured on the
  estimator, for ANY configured value.

This behaviour is pure parameter propagation: integer-valued and
precision-independent, so iteration budgets and the algorithm selector are
modelled as plain `int` (no floating-point semantics are involved). The
estimator is modelled as a minimal object carrying only the single relevant
field.

The two independently-specified behaviours each have their own contracted
function so each is differentially observable on its own.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none) The changed operation is integer parameter propagation, fully
# expressible; no library callee's behaviour is relied upon, so there is no
# @ContractOnly axiom. The solver constructor's only modelled effect is to
# record the iteration budget it is given, which is the identity on that int.
# axioms-end


# pure-start
@Pure
def is_iterative_lasso(algorithm: int) -> bool:
    """Whether the chosen coding algorithm builds an iterative least-squares
    lasso solver (the two algorithms whose iteration budget is meaningful).
    Selector encoding: 0 = least-angle lasso, 1 = coordinate-descent lasso,
    2 = least-angle, 3 = orthogonal matching pursuit, 4 = thresholding."""
    return algorithm == 0 or algorithm == 1


@Pure
def lars_builtin_default() -> int:
    """The least-angle solver class's own built-in iteration default (the value
    silently used when the budget is not threaded into its constructor)."""
    return 500


@Pure
def coder_param_default() -> int:
    """The generic coder routine's own iteration-budget parameter default (the
    value silently used when the encoding path does not forward the budget)."""
    return 1000
# pure-end


def encode_iteration_budget(algorithm: int, max_iter: int) -> int:
    # pre-conditions-start
    Requires(is_iterative_lasso(algorithm))
    Requires(max_iter >= 1)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The constructed iterative-lasso solver receives EXACTLY the budget handed
    # to this routine -- never the solver class's built-in default.
    Ensures(Result() == max_iter)
    # post-conditions-end
    # impl-start
    if algorithm == 0:
        # PRE-PATCH BUG (B2): the least-angle lasso solver is constructed
        # without the supplied budget, so it silently falls back to the solver
        # class's own built-in iteration default.
        budget = lars_builtin_default()
    else:
        # Build the coordinate-descent lasso solver WITH the supplied budget.
        budget = max_iter
    return budget
    # impl-end


def coder_solver_budget(algorithm: int, max_iter: int) -> int:
    # pre-conditions-start
    Requires(is_iterative_lasso(algorithm))
    Requires(max_iter >= 1)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The generic coder forwards its budget, unchanged, to the solver builder.
    Ensures(Result() == max_iter)
    # post-conditions-end
    # impl-start
    return encode_iteration_budget(algorithm, max_iter)
    # impl-end


class Estimator:
    # The minimal estimator: only the single touched field is modelled.
    def __init__(self, configured_max_iter: int) -> None:
        Requires(configured_max_iter >= 1)
        Ensures(Acc(self.configured_max_iter))
        Ensures(self.configured_max_iter == configured_max_iter)
        self.configured_max_iter = configured_max_iter  # type: int


def estimator_encode_budget(self: Estimator, algorithm: int) -> int:
    # pre-conditions-start
    Requires(Acc(self.configured_max_iter, 1 / 2))
    Requires(self.configured_max_iter >= 1)
    Requires(is_iterative_lasso(algorithm))
    Requires(MustTerminate(4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.configured_max_iter, 1 / 2))
    # End-to-end: the solver built by the encoding path receives the budget
    # configured on the estimator, for ANY configured value -- not a default.
    Ensures(Result() == self.configured_max_iter)
    # post-conditions-end
    # impl-start
    budget = coder_solver_budget(algorithm, self.configured_max_iter)
    return budget
    # impl-end
