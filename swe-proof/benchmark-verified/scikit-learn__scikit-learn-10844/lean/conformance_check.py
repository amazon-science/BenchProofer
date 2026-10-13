#!/usr/bin/env python
"""G-CONF: differential conformance for scikit-learn__scikit-learn-10844.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_fmIndex` skeleton and diffs it against the REAL patched
`sklearn.metrics.cluster.supervised.fowlkes_mallows_score` over a discrete
catalogue plus >=1e5 randomized label-array draws.

  observable: whether the call named a real number, and if so which one.

The modeled result carrier is `Option R`, because float division and `np.sqrt`
are PARTIAL: they can return a value (`nan`, `+-inf`) that names no real number.
The observable is therefore two-part and the shadow returns `None` for the Lean
`none` and a `float` for `some v`. The bridge on the real side is:

  real result names a real number  <=>  math.isfinite(result)
  real result is nan / +-inf       <=>  shadow returns None

so a disagreement is counted BOTH when the two disagree on definedness and when
they agree on definedness but differ in value. This is what makes G-CONF check
the partiality modeling rather than assuming it.

I/O bridge (mapping.md): the modeled function's input carrier `M` is the integer
contingency matrix produced by the UNCHANGED `contingency_matrix` callee. The
shadow therefore obtains `M` by calling the real `contingency_matrix` on the
fuzzed label arrays (dense, integer), then transliterates the Lean impl,
including its `fdiv`/`fsqrt` partiality:

  tk = sum(e*e for e in M) - n
  pk = sum(cs*cs for cs in colsums(M)) - n      # column totals
  qk = sum(rs*rs for rs in rowsums(M)) - n      # row totals
  result = 0.0                       if tk == 0                  # the guard
           None                      if a divisor is 0           # fdiv -> none
           None                      if a radicand is negative   # fsqrt -> none
           sqrt(tk/pk)*sqrt(tk/qk)   otherwise   # the patched reassociation

computed in Python's arbitrary-precision ints (no fixed-width overflow), then
compared to the real patched fowlkes_mallows_score over the same labels. Floats
compared with a relative+absolute tolerance. Exit 0 iff zero disagreements.
stdlib-only fuzzing (pinned seed). Catalogue includes the F2P overflow workload
and the zero-agreement matrices where the guard is the only thing standing
between the real code and a 0/0.
"""
import math
import random
import sys

SEED = 10844
N_RANDOM = 120_000  # >= 1e5
RTOL = 1e-9
ATOL = 1e-12


# ---- Python shadow of implementation_fmIndex -------------------------------

def fdiv(x, y):
    """The library's division as the PARTIAL operation it is: a quotient names a
    real number only when the divisor is nonzero. Lean `fdiv`."""
    if y == 0:
        return None
    return x / y


def fsqrt(x):
    """The library's square root as the PARTIAL operation it is: the root of a
    negative quantity names no real number. Lean `fsqrt`."""
    if x is None or x < 0:
        return None
    return math.sqrt(x)


def shadow_fmi(M):
    """Transliteration of implementation_fmIndex from the integer contingency
    matrix M (list of list of int).

    Returns None for the Lean `none` (the assembly named no real number) and a
    float for `some v`."""
    flat = [e for row in M for e in row]
    n = sum(flat)
    tk = sum(e * e for e in flat) - n
    colsums = [sum(M[i][j] for i in range(len(M))) for j in range(len(M[0]))] if M and M[0] else []
    rowsums = [sum(row) for row in M]
    pk = sum(cs * cs for cs in colsums) - n
    qk = sum(rs * rs for rs in rowsums) - n
    if tk == 0:
        return 0.0
    a = fdiv(float(tk), float(pk))
    if a is None:
        return None
    b = fdiv(float(tk), float(qk))
    if b is None:
        return None
    ra = fsqrt(a)
    if ra is None:
        return None
    rb = fsqrt(b)
    if rb is None:
        return None
    return ra * rb


# ---- real callee observation ------------------------------------------------

def build_matrix(labels_true, labels_pred):
    """Dense integer contingency matrix via the UNCHANGED real callee."""
    import numpy as np
    from sklearn.metrics.cluster.supervised import contingency_matrix
    c = contingency_matrix(labels_true, labels_pred, sparse=False)
    return np.asarray(c).astype("int64").tolist()


def real_fmi(labels_true, labels_pred):
    """Observe the real patched function on the two-part observable: returns None
    when the call named no real number (nan / +-inf), else the float it named."""
    from sklearn.metrics.cluster.supervised import fowlkes_mallows_score
    v = float(fowlkes_mallows_score(labels_true, labels_pred))
    if not math.isfinite(v):
        return None
    return v


def close(a, b):
    """Compare two `Option R` observations: agreement on definedness first, then
    on value."""
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= ATOL + RTOL * max(abs(a), abs(b))


def main():
    import numpy as np

    disagreements = 0
    checked = 0

    def check(lt, lp):
        nonlocal disagreements, checked
        lt = np.asarray(lt)
        lp = np.asarray(lp)
        M = build_matrix(lt, lp)
        exp = shadow_fmi(M)
        got = real_fmi(lt, lp)
        checked += 1
        if not close(got, exp):
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH lt={lt.tolist()[:8]}... lp={lp.tolist()[:8]}... "
                      f"real={got!r} shadow={exp!r}")

    # discrete catalogue
    catalogue = [
        ([0, 0, 1, 1], [0, 0, 1, 1]),          # perfect
        ([0, 0, 1, 1], [1, 1, 0, 0]),          # perfect (permuted)
        ([0, 0, 0, 0], [0, 1, 2, 3]),          # fully split -> tk == 0, pk == 0
        ([0, 1, 2, 3], [0, 0, 0, 0]),          # tk == 0 other side, qk == 0
        # the test suite's own worst case: tk == 0 AND pk == 0 (one true class,
        # every sample its own cluster). Guard erasure divides 0 by 0 here.
        ([0, 0, 0, 0, 0, 0], [0, 1, 2, 3, 4, 5]),
        ([0, 1, 2, 3, 4, 5], [0, 0, 0, 0, 0, 0]),
        ([0, 1], [0, 1]),                      # tk == 0, pk == 0, qk == 0
        ([0], [0]),                            # singleton: all three counts 0
        ([0, 0, 1, 2], [0, 1, 1, 2]),
        ([0, 1, 0, 1, 2, 2], [1, 1, 0, 0, 2, 2]),
        ([5, 5, 5, 6, 6, 7], [1, 1, 2, 2, 2, 3]),
    ]
    for lt, lp in catalogue:
        check(lt, lp)

    # F2P-style overflow workload (the int64 product overflow regime):
    x = ([1] * (52632 + 2529) + [2] * (14660 + 793) + [3] * (3271 + 204)
         + [4] * (814 + 39) + [5] * (316 + 20))
    y = ([0] * 52632 + [1] * 2529 + [0] * 14660 + [1] * 793 + [0] * 3271
         + [1] * 204 + [0] * 814 + [1] * 39 + [0] * 316 + [1] * 20)
    check(x, y)

    # randomized fuzz: small label arrays over a few classes/clusters
    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        n = rng.randint(2, 30)
        k_true = rng.randint(1, 6)
        k_pred = rng.randint(1, 6)
        lt = [rng.randint(0, k_true - 1) for _ in range(n)]
        lp = [rng.randint(0, k_pred - 1) for _ in range(n)]
        check(lt, lp)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
