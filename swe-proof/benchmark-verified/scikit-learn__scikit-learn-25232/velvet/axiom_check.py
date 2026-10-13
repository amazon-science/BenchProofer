#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-25232.

Executes the REAL unchanged callee the modeled `initialFillStatistics` relies on
and asserts every observation meets the `constantFill` stub's `ensures`
(Solution.lean), as bound in mapping.md §3.

The A-consumed contract:

  (A-consumed) `constantFill (fillValue) (nFeatures)` ↔
      `SimpleImputer(strategy="constant", fill_value=<v>).fit(X).statistics_`
      (sklearn/impute/_base.py, UNCHANGED by the patch). For numerical dense X
      with `n_features` columns, the fitted `statistics_` is the constant vector

          np.full(n_features, fill_value if fill_value is not None else 0)

      i.e. `constantFill fillValue nFeatures
            = List.replicate nFeatures (resolveFill fillValue)`
      where `resolveFill none = 0`, `resolveFill (some v) = v`.

This is the weakest contract the caller `_initial_imputation` consumes: the
patch's whole behavioural content is forwarding the configured `fill_value`
into this constructor (`fill_value=self.fill_value`), so the constant vector is
built from the configured value rather than the default. We fix
`strategy="constant"` (mapping.md §3.2: the constant vector only arises in that
configuration) and the numerical dense case (the modeled domain, mapping.md §2).

Imports only `sklearn.impute` + `numpy` — the same code the gold patch calls,
in-container. Exit 0 iff every obligation holds. Seed pinned for determinism.
"""
import sys
import random

import numpy as np
from sklearn.impute import SimpleImputer

SEED = 25232


def resolve_fill(fill_value):
    """resolveFill: None -> 0 (numerical default), else the value (mapping §2)."""
    return 0 if fill_value is None else fill_value


def real_constant_fill(fill_value, X, missing_values):
    """The REAL unchanged callee: SimpleImputer constant-strategy fit, then
    statistics_. This is exactly what _initial_imputation constructs (with
    fill_value forwarded post-patch)."""
    imp = SimpleImputer(
        missing_values=missing_values,
        strategy="constant",
        fill_value=fill_value,
    )
    imp.fit(X)
    return imp.statistics_


def check_once(fill_value, n_features, n_samples, missing_values, rng):
    """Run the real callee and assert it meets the constantFill ensures."""
    # Build a numerical dense matrix with some missing entries (so the constant
    # strategy is meaningfully exercised); content is irrelevant to statistics_.
    X = rng.standard_normal((n_samples, n_features))
    # plant the sentinel in a few cells so missing values genuinely occur
    if n_samples and n_features:
        # numpy RandomState has no randrange; randint(0, hi) draws from [0, hi)
        for _ in range(int(rng.randint(0, n_samples + 1))):
            i = int(rng.randint(0, n_samples))
            j = int(rng.randint(0, n_features))
            X[i, j] = missing_values if not np.isnan(missing_values) else np.nan

    stats = real_constant_fill(fill_value, X, missing_values)
    expected = np.full(n_features, resolve_fill(fill_value), dtype=stats.dtype)

    if stats.shape != (n_features,):
        return (fill_value, n_features, "shape", stats.shape)
    if not np.array_equal(stats, expected):
        return (fill_value, n_features, list(stats), list(expected))
    return None


def main():
    rng = np.random.RandomState(SEED)
    pyrng = random.Random(SEED)
    failures = []
    count = 0

    # --- boundary cases (plan §4.1 step 4) -----------------------------------
    boundary_fills = [None, 0, 1, -1, 100, -100, 3.5, 1e6, -1e6, 0.0]
    boundary_shapes = [(1, 1), (4, 1), (4, 4), (10, 3), (2, 7)]
    for fv in boundary_fills:
        for (ns, nf) in boundary_shapes:
            count += 1
            r = check_once(fv, nf, ns, np.nan, rng)
            if r:
                failures.append(r)
            # also exercise a non-nan sentinel (the F2P test uses missing=-1)
            count += 1
            r = check_once(fv, nf, ns, -1, rng)
            if r:
                failures.append(r)

    # exact F2P configuration: missing=-1, fill_value=100
    count += 1
    Xf = np.array([[-1, 2, 3, -1], [4, -1, 5, -1], [6, 7, -1, -1], [8, 9, 0, -1]],
                  dtype=float)
    stats = real_constant_fill(100, Xf, -1)
    if not np.array_equal(stats, np.full(4, 100, dtype=stats.dtype)):
        failures.append((100, 4, "F2P", list(stats)))

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(3000):
        count += 1
        fv = pyrng.choice([None, 0, 1, -1, 7, 100, -100,
                           pyrng.uniform(-1e3, 1e3),
                           pyrng.randint(-10**6, 10**6)])
        nf = pyrng.randint(1, 12)
        ns = pyrng.randint(1, 30)
        missing = pyrng.choice([np.nan, -1, 0.0, 999])
        r = check_once(fv, nf, ns, missing, rng)
        if r:
            failures.append(r)
            if len(failures) >= 5:
                break

    if failures:
        print("G-AX FAIL: %d constantFill (SimpleImputer constant fit) "
              "violation(s) over %d cases:" % (len(failures), count))
        for f in failures[:5]:
            print("  fill_value=%r n_features=%r got=%r expected=%r"
                  % (f[0], f[1], f[2], f[3]))
        return 1

    print("G-AX OK: constantFill (real SimpleImputer constant-strategy fit) "
          "statistics_ == replicate(n_features, resolveFill(fill_value)) on %d "
          "numerical cases incl. the F2P config (seed=%d)." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
