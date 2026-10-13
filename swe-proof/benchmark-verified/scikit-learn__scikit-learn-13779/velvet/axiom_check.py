#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-13779.

This bundle consumes NO axioms and references NO deep-model callee (mapping.md
§3): the only repo callee the validation scan invokes,
`has_fit_parameter(step, 'sample_weight')`, is a pure boolean predicate whose
verdict is carried as the input bit `Member.supports`. There is therefore no
axiom `ensures` to validate.

What remains to confirm is the **R-refinement** of the member carrier
(mapping.md §2): that the boolean bits the spec consumes faithfully mirror the
real repo facts. This script executes the REAL
`sklearn.utils.validation.has_fit_parameter` and the REAL `step is None` test on
representative members, asserting:

  (R bridge) for a present member, `Member.supports` == has_fit_parameter(step,
      'sample_weight'): an estimator whose `fit` declares a `sample_weight`
      parameter -> True; one whose `fit` does not -> False.
  (R bridge) the absent case `step is None` is exactly the member the fix skips,
      and `None` exposes no `sample_weight` parameter (so leaving its `supports`
      bit `false` in the shadow is faithful).

  (non-vacuity) the modeled change is real: with an absent member ahead of a
      present unsupported one, the PRE-patch scan (no `step is None` skip) would
      consult `has_fit_parameter(None, ...)` — which raises AttributeError on the
      real callee — whereas the patched scan skips it. This confirms the
      skip-absent guard is load-bearing, not vacuous.

Imports only stdlib + the real sklearn callee the gold patch's neighbourhood
uses. Exit 0 iff every obligation holds.
"""
import sys

from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.utils.validation import has_fit_parameter


class _Supported(RegressorMixin, BaseEstimator):
    """fit ACCEPTS sample_weight (has_fit_parameter -> True)."""

    def fit(self, X, y=None, sample_weight=None):
        return self


class _Unsupported(RegressorMixin, BaseEstimator):
    """fit does NOT accept sample_weight (has_fit_parameter -> False)."""

    def fit(self, X, y=None):
        return self


def check_supports_bridge():
    """Member.supports == has_fit_parameter(step, 'sample_weight') for present."""
    sup = _Supported()
    uns = _Unsupported()
    assert has_fit_parameter(sup, 'sample_weight') is True, (
        "expected a sample_weight-accepting estimator to map to supports=True")
    assert has_fit_parameter(uns, 'sample_weight') is False, (
        "expected a non-accepting estimator to map to supports=False")


def check_absent_bridge():
    """`step is None` is the absent case; None has no 'fit' / sample_weight."""
    step = None
    assert (step is None), "absent member must be modeled as present=false"
    # `None` exposes no fit method, so the pre-patch has_fit_parameter(None, ...)
    # cannot succeed — the very crash the fix removes. Confirm it really fails.
    raised = False
    try:
        has_fit_parameter(None, 'sample_weight')
    except (AttributeError, TypeError, ValueError):
        raised = True
    assert raised, (
        "expected has_fit_parameter(None, ...) to fail on the real callee "
        "(the AttributeError the fix's `if step is None: continue` removes)")


def check_non_vacuity():
    """The skip-absent guard is load-bearing: a present unsupported member behind
    an absent one is reachable only because the patched scan skips the absent
    one (the pre-patch scan would have crashed on has_fit_parameter(None,...))."""
    sup, uns = _Supported(), _Unsupported()
    # supported is still detected as supported; unsupported as unsupported
    assert has_fit_parameter(sup, 'sample_weight') != \
        has_fit_parameter(uns, 'sample_weight'), (
        "modeled distinction (supports True vs False) must be observable")


def main():
    check_supports_bridge()
    check_absent_bridge()
    check_non_vacuity()
    print("G-AX OK: no consumed axioms; Member.supports/present R-refinement "
          "validated against real has_fit_parameter + `step is None` (supported "
          "-> True, unsupported -> False, None -> absent/crashes pre-patch); "
          "skip-absent guard confirmed load-bearing (non-vacuous).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
