#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-25747.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `wrapContainer` impl region
              transliterated to Python over the *real* repo type (a
              `pandas.DataFrame` restricted to its two label axes), via the
              mapping.md bijection (`Frame ↔ ⟨list(df.columns), list(df.index)⟩`,
              `Option (List Lbl) ↔ None|list`,
              `Except WrapErr Frame ↔ ('ok', cols, index) | ('error',)`).
              The branch is pure R/I; there is no consumed axiom in the computed
              state, so the shadow is exact.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sklearn.utils._set_output._wrap_in_pandas_container` applied at
              base_commit (the real correctness oracle, G-RESOLVE), restricted to
              the already-a-DataFrame branch, observed via the resulting
              `(list(columns), list(index))` on success, or the escaping
              size-mismatch `ValueError` when the offered column-label set does
              not hold one label per existing column. On failure the container's
              own labels must be untouched (`frameAfter` = identity).

An "input" is `(df, new_columns, new_index)`: an existing DataFrame plus an
optional replacement column-label set and an optional row-label set offered by
the caller. Column-label sets of NON-matching length are deliberately fuzzed:
they must make the request fail with the size-mismatch error while leaving the
frame untouched (`wrapResult .error`, `frameAfter` identity). Row-label sets of
any length must be ignored on the already-a-DataFrame branch. The observable
compared is the outcome tag plus, on success, the resulting `(columns, index)`
pair, and on failure the container's unchanged label axes. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + pandas only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 25747
N_FUZZ = 100_000


def shadow_outcome(orig_cols, orig_index, new_columns, new_index):
    """The R/I shadow of `wrapContainer` on an already-a-container input:
       * when a column-label set is supplied it must hold exactly one label per
         existing column (`sizeFits`); an ill-fitting set makes the request fail
         with the size-mismatch error, the frame untouched
         (`wrapResult .error`, `frameAfter` = identity);
       * a fitting (or absent) set settles the column axis per
         `resolvedCols = supplied.getD current`;
       * row axis: ALWAYS the frame's own labels — `new_index` has no effect
         (the directive-5 frame clause `frame.rowLabels = frameOld.rowLabels`).
    Returns ('ok', cols, index) or ('error', orig_cols, orig_index)."""
    if new_columns is not None and len(new_columns) != len(orig_cols):
        return ("error", list(orig_cols), list(orig_index))
    out_cols = list(new_columns) if new_columns is not None else list(orig_cols)
    out_index = list(orig_index)  # row axis pinned to the frame's own labels
    return ("ok", out_cols, out_index)


def oracle_outcome(make_df, new_columns, new_index):
    """patch.diff's behaviour: the patched _wrap_in_pandas_container on a fresh
    copy of the same DataFrame (the harness applies patch.diff before this runs).
    Observed via the outcome tag and the resulting (columns, index); when the
    size-mismatch ValueError escapes, the frame's own labels must be untouched."""
    from sklearn.utils._set_output import _wrap_in_pandas_container
    df = make_df()
    try:
        res = _wrap_in_pandas_container(df, columns=new_columns, index=new_index)
    except ValueError:
        # size-mismatch escape: the container must be left exactly as it was
        return ("error", list(df.columns), list(df.index))
    return ("ok", list(res.columns), list(res.index))


def fuzz_inputs(n, rng):
    import pandas as pd

    def gen():
        nrows = rng.randint(0, 6)
        ncols = rng.randint(0, 5)
        # the frame's own labels (sometimes default RangeIndex-like, sometimes
        # custom strings/ints) -- the values whose preservation is the fix
        if rng.random() < 0.5:
            orig_cols = list(range(ncols))
        else:
            orig_cols = [f"c{rng.randint(0, 99)}_{j}" for j in range(ncols)]
        if rng.random() < 0.5:
            orig_index = list(range(nrows))
        else:
            orig_index = [f"r{rng.randint(0, 99)}_{i}" for i in range(nrows)]

        def make_df():
            data = [[rng.random() for _ in range(ncols)] for _ in range(nrows)]
            return pd.DataFrame(data, columns=list(orig_cols), index=list(orig_index))

        # optional replacement column labels: 60% supplied; of those, a quarter
        # deliberately DON'T fit (the size-mismatch surface)
        if rng.random() < 0.6:
            if rng.random() < 0.25:
                k = rng.choice([d for d in (-2, -1, 1, 2, 3)
                                if ncols + d >= 0 and ncols + d != ncols])
                new_columns = [f"X{j}" for j in range(ncols + k)]
            else:
                new_columns = [f"X{j}" for j in range(ncols)]
        else:
            new_columns = None
        # optional row-label set offered by the caller: 70% supplied; a quarter
        # of those deliberately of the WRONG length -- all must be ignored
        if rng.random() < 0.7:
            if rng.random() < 0.25:
                k = rng.choice([d for d in (-2, -1, 1, 2, 3)
                                if nrows + d >= 0 and nrows + d != nrows])
                new_index = [f"s{i}" for i in range(nrows + k)]
            else:
                new_index = [f"s{i}" for i in range(nrows)]
        else:
            new_index = None
        return make_df, orig_cols, orig_index, new_columns, new_index

    # boundary cases first (plan §4.1 step 4)
    def boundary(nrows, ncols, oc, oi, nc, ni):
        def make_df():
            data = [[float(i * ncols + j) for j in range(ncols)] for i in range(nrows)]
            return pd.DataFrame(data, columns=list(oc), index=list(oi))
        return make_df, oc, oi, nc, ni

    # the F2P scenario: 2x3 frame, custom string index supplied, columns supplied
    yield boundary(2, 3, [0, 1, 2], [0, 1],
                   ["X0", "X1", "X2"], ["s0", "s1"])
    # supplied index differs from own index -> must keep own (the bug surface)
    yield boundary(2, 3, [0, 1, 2], [10, 20],
                   None, ["s0", "s1"])
    # no new columns, no new index
    yield boundary(3, 2, ["a", "b"], ["i", "j", "k"], None, None)
    # new columns only
    yield boundary(1, 1, [0], [0], ["only"], None)
    # empty frame
    yield boundary(0, 0, [], [], None, None)
    # zero rows, some columns
    yield boundary(0, 3, [0, 1, 2], [], ["p", "q", "r"], [])
    # some rows, zero columns
    yield boundary(4, 0, [], [0, 1, 2, 3], None, ["w", "x", "y", "z"])
    # the P2-audit divergence input: TOO MANY column labels for a 2x2 frame
    # -> size-mismatch error, frame untouched
    yield boundary(2, 2, ["a", "b"], [10, 20], ["x", "y", "z"], None)
    # too FEW column labels -> size-mismatch error
    yield boundary(2, 2, ["a", "b"], [10, 20], ["only"], None)
    # ill-fitting ROW labels with fitting columns -> ignored, still ok
    yield boundary(2, 2, ["a", "b"], [10, 20], ["x", "y"], ["s0", "s1", "s2"])
    # ill-fitting row labels alone -> ignored, still ok
    yield boundary(2, 2, ["a", "b"], [10, 20], None, ["s0"])
    # empty replacement column set on a non-empty axis -> size-mismatch error
    yield boundary(1, 2, ["a", "b"], [0], [], None)

    for _ in range(n):
        yield gen()


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for make_df, orig_cols, orig_index, new_columns, new_index in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_outcome(orig_cols, orig_index, new_columns, new_index)
        oracle = oracle_outcome(make_df, new_columns, new_index)
        if shadow != oracle:
            disagreements.append((orig_cols, orig_index, new_columns, new_index,
                                  shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for oc, oi, nc, ni, sh, orc in disagreements:
            print("  orig_cols=%r orig_index=%r new_columns=%r new_index=%r "
                  "shadow=%r oracle=%r" % (oc, oi, nc, ni, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of wrapContainer agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
