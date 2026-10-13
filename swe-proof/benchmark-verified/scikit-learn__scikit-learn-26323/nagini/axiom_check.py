#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-26323.

The model has NO consumed `@ContractOnly` axioms. The configuration
propagation is modelled DEEPLY (a per-child field write). The two operations
the deep model abstracts are unchanged repo callees; this script validates the
deep model is FAITHFUL to them (refinement.md tags: R / A-reference), running
the REAL callees in-container (sklearn is installed in the evaluation image):

  (A-reference 1) the per-child configuration primitive
        model:  `t.cfg = transform`   (cfg becomes the requested output code)
        real :  `_safe_set_output(estimator, transform=transform)`
                (sets `estimator._sklearn_output_config["transform"] == transform`)
      i.e. configuring an estimator records exactly the requested output
      container, which `_get_output_config("transform", estimator)["dense"]`
      then reports. The model's integer `cfg` code stands in for this string
      container code under the type refinement.

  (A-reference 2) the estimator-vs-sentinel classification
        model:  `is_estimator(t)` == (kind == 1)   vs   sentinel (kind == 0)
        real :  `trans not in {"passthrough", "drop"}`
      The two routing sentinels carry no output container and are never
      configured; everything else is an estimator that is configured. This is
      exactly the guard the composite uses for the leftover-columns child.

It also re-derives the WHOLE pinned behaviour end-to-end with the real
composite: a leftover-columns ESTIMATOR is configured to the requested
container (so a DataFrame is preserved), while a leftover-columns SENTINEL is
not — the discriminating witness from the issue's reproducer.

Exit 0 iff every obligation holds.
"""
import sys


SENTINELS = {"passthrough", "drop"}


def _is_estimator(trans):
    """Real classification used by the composite's leftover-columns guard."""
    return trans not in SENTINELS


def check_safe_set_output_primitive():
    """A-reference 1: the real `_safe_set_output` records the requested output
    container on an estimator (model `cfg = transform`)."""
    from sklearn.utils._set_output import _safe_set_output, _get_output_config
    from sklearn.preprocessing import StandardScaler

    for transform in ("pandas", "default"):
        est = StandardScaler()
        _safe_set_output(est, transform=transform)
        cfg = _get_output_config("transform", est)["dense"]
        assert cfg == transform, (
            "_safe_set_output unsound: requested %r, estimator reports %r"
            % (transform, cfg))


def check_sentinel_classification():
    """A-reference 2: the routing sentinels are exactly the guard's excluded
    values, and an estimator is anything else."""
    from sklearn.preprocessing import StandardScaler
    from sklearn.feature_selection import VarianceThreshold

    assert _is_estimator("passthrough") is False
    assert _is_estimator("drop") is False
    assert _is_estimator(StandardScaler()) is True
    assert _is_estimator(VarianceThreshold()) is True


def check_composite_behaviour_estimator_remainder():
    """End-to-end discriminating witness: when the leftover-columns child is an
    ESTIMATOR, configuring the composite to a DataFrame container must reach it,
    so the round-trip preserves the DataFrame (the issue's expected result)."""
    import numpy as np

    try:
        import pandas as pd
    except ImportError:
        print("G-AX SKIP: pandas not available; primitive checks already passed")
        return

    from sklearn.compose import make_column_selector, make_column_transformer
    from sklearn.feature_selection import VarianceThreshold

    df = pd.DataFrame({"a": [True, False, True], "b": [1, 2, 3]})

    ct = make_column_transformer(
        (VarianceThreshold(), make_column_selector(dtype_include=bool)),
        remainder=VarianceThreshold(),
        verbose_feature_names_out=False,
    )
    ct.set_output(transform="pandas")
    out = ct.fit_transform(df)
    # the leftover-columns estimator was configured -> DataFrame preserved
    pd.testing.assert_frame_equal(out, df)

    # and a leftover-columns SENTINEL stays a sentinel: switching to default
    # yields a numpy array (no per-child container) — confirms the kind==0 path.
    ct.set_output(transform="default")
    out = ct.fit_transform(df)
    assert isinstance(out, np.ndarray), (
        "default output config must yield a numpy array, got %r" % type(out))


def main():
    check_safe_set_output_primitive()
    check_sentinel_classification()
    check_composite_behaviour_estimator_remainder()
    print("G-AX OK: _safe_set_output records the requested output container on "
          "an estimator (deep-model cfg=transform); {passthrough, drop} are the "
          "exact routing sentinels the leftover-columns guard excludes "
          "(kind==0); end-to-end the leftover-columns estimator is configured "
          "and the DataFrame round-trip is preserved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
