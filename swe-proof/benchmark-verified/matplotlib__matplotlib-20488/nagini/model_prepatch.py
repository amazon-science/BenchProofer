"""Twin-artifact model for matplotlib__matplotlib-20488.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Before a real-valued lower bound is handed to a logarithmic normalization, it
  must be sanitised. A logarithmic normalization is only defined on strictly
  positive numbers, so whenever it is the active normalization the lower bound
  that reaches it MUST be strictly positive. Concretely, given

    * a flag saying whether the active normalization is logarithmic,
    * a candidate lower bound (an arbitrary finite real number that, after the
      resampling round trip, may have landed at zero or below), and
    * a strictly positive floor value (the smallest positive magnitude the
      working numeric type can represent),

  the sanitised lower bound is:

    * the floor value, when the normalization is logarithmic AND the candidate
      lower bound is zero or negative (the candidate is unusable for a log scale
      and is replaced by the smallest positive magnitude); and
    * the candidate lower bound unchanged, in every other case (a non-log
      normalization, or a candidate that is already strictly positive — these
      pass through untouched).

  The guarantee the issue demands: when the normalization is logarithmic the
  sanitised lower bound is always strictly positive, including at the boundary
  where the candidate is exactly zero.

The candidate bound and the floor are interpreted real numbers (verified with
`--float-encoding=real`); the flag is a bool. The behaviour is a sign/zero
conditional on real numbers, so it is modelled directly over floats.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the behaviour is a direct real-number conditional)
# axioms-end


# pure-start
# (no pure helpers needed)
# pure-end


def sanitized_lower_bound(is_log: bool, lower_bound: float, eps: float) -> float:
    # pre-conditions-start
    # The floor value is the smallest positive magnitude of the working numeric
    # type, hence strictly positive.
    Requires(eps > 0.0)
    # The candidate lower bound is a genuine ordered real number (it arises from
    # finite arithmetic on the data range), so it compares against zero — i.e.
    # it is either zero-or-below or strictly positive.
    Requires(lower_bound <= 0.0 or lower_bound > 0.0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # When the active normalization is logarithmic the sanitised lower bound is
    # ALWAYS strictly positive (a log scale is undefined at and below zero) —
    # this is the property the failing case demands, and it must hold even when
    # the candidate is exactly zero.
    Ensures(Implies(is_log, Result() > 0.0))
    # When a sanitisation is actually required (logarithmic AND the candidate is
    # zero or negative) the result is exactly the positive floor value.
    Ensures(Implies(is_log and lower_bound <= 0.0, Result() == eps))
    # Otherwise the candidate lower bound passes through completely unchanged.
    Ensures(Implies(not (is_log and lower_bound <= 0.0), Result() == lower_bound))
    # post-conditions-end
    # impl-start
    result = lower_bound
    if is_log:
        if lower_bound < 0.0:
            # max(lower_bound, eps): since lower_bound < 0.0 < eps this is eps
            if lower_bound > eps:
                result = lower_bound
            else:
                result = eps
    return result
    # impl-end
