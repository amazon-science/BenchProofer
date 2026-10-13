#!/usr/bin/env python
"""G-CONF: differential conformance for scikit-learn__scikit-learn-25232.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The bundle models ONE behavior: the first-round
`initial_strategy="constant"` initialization of `IterativeImputer`, which the
patch makes user-controllable. The soundness-critical change is one line — the
inner imputer that produces the round-zero fill is now built WITH the user's
`fill_value` instead of always defaulting it.

ORACLE = the genuine post-patch behavior, reconstructed from the REAL unchanged
callee: a `SimpleImputer(strategy="constant", missing_values=..., fill_value=...)`
fit+transform on the matrix. Its `statistics_` is the per-feature fill and its
`transform(X)` is the sentinel-replaced matrix — exactly what
`IterativeImputer._initial_imputation` builds and returns on the constant path.

SHADOW_FIX = the op-for-op transliteration of `implementation_initial_fill`
(Solution.lean impl region): fill = (fill_value if fill_value is not None else 0);
statistics = full(n_features, fill); xFilled[i][j] = fill if X[i][j]==mv else X[i][j].
Must EQUAL the oracle on every input.

SHADOW_BUG = the transliteration of `Solution_prepatch.lean` (fill hard-coded to
0, ignoring fill_value). Negative control: the differential test must be powerful
enough to tell the bug apart from the fix on at least one configuration.

Exit 0 iff (a) zero fix-vs-oracle disagreements AND (b) the bug shadow disagrees
on >= 1 configuration, over a discrete edge matrix + >= 1e5 fuzzed draws.
stdlib-driven fuzzing (pinned seed 25232).
"""
import random
import sys
from fractions import Fraction

import numpy as np

try:
    from sklearn.impute import SimpleImputer  # REAL unchanged callee
except Exception as e:  # pragma: no cover
    print("status=error could not import sklearn.impute.SimpleImputer:", e)
    sys.exit(2)

SEED = 25232
N_RANDOM = 120_000  # >= 1e5


def _eff_fill(fill_value):
    return 0 if fill_value is None else fill_value


# ---- ORACLE: genuine post-patch path via the REAL SimpleImputer callee -------
def oracle(X, missing_values, fill_value):
    Xa = np.asarray(X, dtype=float)
    imp = SimpleImputer(
        missing_values=float(missing_values),
        strategy="constant",
        fill_value=fill_value,
    )
    xfilled = imp.fit_transform(Xa)
    return [float(s) for s in imp.statistics_], xfilled.tolist()


# ---- SHADOW_FIX: transliteration of implementation_initial_fill --------------
def shadow_fix(X, missing_values, fill_value):
    fill = _eff_fill(fill_value)
    n_features = 0 if len(X) == 0 else len(X[0])
    statistics = [float(fill)] * n_features
    xfilled = []
    for row in X:
        new_row = []
        for v in row:
            new_row.append(float(fill) if v == missing_values else float(v))
        xfilled.append(new_row)
    return statistics, xfilled


# ---- SHADOW_BUG: transliteration of Solution_prepatch.lean -------------------
def shadow_bug(X, missing_values, fill_value):
    fill = 0  # bug: fill_value ignored, always default 0
    n_features = 0 if len(X) == 0 else len(X[0])
    statistics = [float(fill)] * n_features
    xfilled = []
    for row in X:
        new_row = []
        for v in row:
            new_row.append(float(fill) if v == missing_values else float(v))
        xfilled.append(new_row)
    return statistics, xfilled


def _eq(a, b, tol=1e-9):
    sa, xa = a
    sb, xb = b
    if len(sa) != len(sb):
        return False
    if any(abs(x - y) > tol for x, y in zip(sa, sb)):
        return False
    if len(xa) != len(xb):
        return False
    for ra, rb in zip(xa, xb):
        if len(ra) != len(rb):
            return False
        if any(abs(x - y) > tol for x, y in zip(ra, rb)):
            return False
    return True


def edge_matrix():
    cases = []
    # the FAIL_TO_PASS reproducer shape (missing_values=-1, fill_value=100)
    cases.append(([[-1, 2, 3, -1], [4, -1, 5, -1], [6, 7, -1, -1], [8, 9, 0, -1]], -1, 100))
    # default fill (None -> 0)
    cases.append(([[-1, 2], [3, -1]], -1, None))
    # explicit fill 0 (same as default)
    cases.append(([[-1, 2], [3, -1]], -1, 0))
    # missing_values = 0
    cases.append(([[0, 5], [7, 0]], 0, 9))
    # negative / fractional fill
    cases.append(([[7, 7], [7, 1]], 7, -3))
    # single column, single row
    cases.append(([[5]], 5, 42))
    cases.append(([[1, 2, 3]], 9, 9))
    return cases


def main():
    fix_disagree = 0
    bug_disagree = 0
    checked = 0

    def check(X, mv, fv):
        nonlocal fix_disagree, bug_disagree, checked
        # SimpleImputer drops all-missing columns from transform output unless
        # keep_empty_features; on the constant path statistics_ are never NaN so
        # no column is dropped, but guard against degenerate empty matrices.
        if len(X) == 0 or len(X[0]) == 0:
            return
        checked += 1
        o = oracle(X, mv, fv)
        f = shadow_fix(X, mv, fv)
        if not _eq(f, o):
            fix_disagree += 1
            if fix_disagree <= 5:
                print("FIX!=ORACLE mv=%r fv=%r X=%r\n  oracle=%r\n  fix   =%r"
                      % (mv, fv, X, o, f))
        b = shadow_bug(X, mv, fv)
        if not _eq(b, o):
            bug_disagree += 1

    for c in edge_matrix():
        check(*c)

    rnd = random.Random(SEED)
    for _ in range(N_RANDOM):
        n_features = rnd.randint(1, 6)
        n_samples = rnd.randint(1, 10)
        mv = rnd.choice([-1, 0, 7])
        # values drawn so the sentinel actually appears with decent frequency
        pool = [mv, mv] + list(range(-2, 9))
        X = [[rnd.choice(pool) for _ in range(n_features)] for _ in range(n_samples)]
        fv = rnd.choice([None, 0, 1, -3, 100, 5])
        check(X, mv, fv)

    print("checked=%d fix_disagreements=%d bug_disagreements=%d"
          % (checked, fix_disagree, bug_disagree))
    if fix_disagree != 0:
        print("status=fail impl shadow disagrees with genuine post-patch behavior")
        sys.exit(1)
    if bug_disagree == 0:
        print("status=fail differential test has NO power: prepatch (default-0) "
              "never distinguished from the fix (forwarded constant)")
        sys.exit(1)
    print("status=ok impl shadow == genuine post-patch behavior on all %d configs; "
          "prepatch distinguished on %d" % (checked, bug_disagree))
    sys.exit(0)


if __name__ == "__main__":
    main()
