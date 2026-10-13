#!/usr/bin/env python3
"""G-CONF differential conformance for scikit-learn__scikit-learn-12682.

Refutes the R/I refinement leg of the data-flow property modeled in
Solution.lean: the iteration budget the user configures at construction
(`transform_max_iter`) is recorded on the estimator and then forwarded UNCHANGED
to the underlying iterative solver as its `max_iter`. There are NO axioms and NO
deep-model references in this bundle: every op is a pure read/store of one value
over a free input, so the whole impl region is R/I-tagged (conf_skip=false).

SHADOW (Solution.lean transliterated)
-------------------------------------
  recordIterationBudget(b)              -> cfg.iterationBudget = b
  encodeWithConfig(cfg)                 -> cfg.iterationBudget
  configuredBudgetReachesSolver(b)      -> b           (the composition)
i.e. the budget reaches the solver verbatim: shadow(b) == b.

ORACLE (patched sklearn/decomposition/dict_learning.py, run in-container)
-------------------------------------------------------------------------
We do NOT re-implement the threading; we OBSERVE the real patched code. We build
the patched `SparseCoder(dictionary, transform_algorithm='lasso_cd',
transform_max_iter=b)` and run `.transform(X)`. The patched `transform` reads
`self.transform_max_iter` and calls `sparse_encode(..., max_iter=...)`; that
argument is handed straight to the `lasso_cd` solver (`Lasso(max_iter=...)`) by
`_sparse_encode` (verbatim forwarding, unchanged by the patch). We intercept the
module-global `sparse_encode` that `transform` looks up, capture the `max_iter`
kwarg it is called with — the real end-to-end budget the gold patch delivers to
the solver — and short-circuit (raise a sentinel) so no numerical fitting runs.

oracle(b) := the `max_iter` value the patched `transform` forwards for a
`SparseCoder` configured with `transform_max_iter=b`.

We differential-test SHADOW vs ORACLE over a boundary set plus seeded fuzz of
>=10^5 budgets (seed=12682). Exit 0 iff zero disagreements. stdlib + sklearn
(already in the testbed image) only.
"""
import random
import sys

SEED = 12682
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def shadow_record(user_budget):
    """recordIterationBudget: store the budget verbatim -> cfg.iterationBudget."""
    return {"iterationBudget": user_budget}


def shadow_encode(cfg):
    """encodeWithConfig: read the recorded budget and forward it."""
    return cfg["iterationBudget"]


def shadow_reaches_solver(user_budget):
    """configuredBudgetReachesSolver: the composition (identity threading)."""
    cfg = shadow_record(user_budget)
    return shadow_encode(cfg)


# ---- ORACLE: observe the real patched threading ---------------------------

class _Captured(Exception):
    """Sentinel raised after we have observed the forwarded budget, so the
    heavy numerical fit never runs."""
    def __init__(self, max_iter):
        super().__init__()
        self.max_iter = max_iter


def _build_oracle():
    """Return (oracle_fn, dictionary, X) using the patched in-tree sklearn.

    Raises SystemExit with a skip diagnostic if the patched surface is absent
    (would indicate the patch was not applied — the orchestrator applies gold
    before running this)."""
    import importlib
    import numpy as np
    # NB: `import sklearn.decomposition.dict_learning as dl` would bind `dl` to
    # the *function* `dict_learning` (re-exported into the package namespace,
    # shadowing the submodule). Resolve the submodule object explicitly so we can
    # monkeypatch the module-global `sparse_encode` that `transform` looks up.
    dl = importlib.import_module("sklearn.decomposition.dict_learning")
    from sklearn.decomposition import SparseCoder

    # The patch must have introduced the construction-time budget argument.
    import inspect
    sig = inspect.signature(SparseCoder.__init__)
    if "transform_max_iter" not in sig.parameters:
        print("G-CONF ERROR: patched SparseCoder lacks transform_max_iter "
              "(gold patch not applied?)")
        sys.exit(2)

    # Tiny, valid inputs: a 2-atom dictionary over 4 features, one sample.
    rng = np.random.RandomState(0)
    dictionary = rng.randn(2, 4)
    X = rng.randn(1, 4)

    real_sparse_encode = dl.sparse_encode

    def capturing_sparse_encode(*args, **kwargs):
        # `transform` calls sparse_encode(..., max_iter=self.transform_max_iter, ...)
        # Capture the forwarded budget and stop before any fitting.
        raise _Captured(kwargs.get("max_iter", "<<absent>>"))

    def oracle(b):
        dl.sparse_encode = capturing_sparse_encode
        try:
            model = SparseCoder(dictionary,
                                transform_algorithm="lasso_cd",
                                transform_max_iter=b)
            model.transform(X)
        except _Captured as c:
            return c.max_iter
        finally:
            dl.sparse_encode = real_sparse_encode
        # transform returned without calling sparse_encode -> unexpected.
        return "<<no-call>>"

    return oracle


def main():
    try:
        oracle = _build_oracle()
    except ImportError as e:
        print("G-CONF ERROR: cannot import patched sklearn: %r" % (e,))
        return 2

    rng = random.Random(SEED)
    # Boundary budgets (incl. the two values the F2P test_max_iter uses: 1, 2000)
    # and a fuzz cloud of positive ints; transform_max_iter is a Python int >= 1.
    boundary = [1, 2, 3, 5, 10, 100, 999, 1000, 1001, 2000, 5000, 100000]
    fuzz = [rng.randint(1, 10_000_000) for _ in range(N_FUZZ)]

    disagreements = []
    count = 0
    for b in boundary + fuzz:
        count += 1
        s = shadow_reaches_solver(b)
        o = oracle(b)
        if s != o:
            disagreements.append((b, s, o))
            if len(disagreements) >= 8:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) (budget, shadow, oracle): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of recordIterationBudget/encodeWithConfig/"
          "configuredBudgetReachesSolver (identity budget threading) agrees with "
          "the patched SparseCoder->transform->sparse_encode forwarded max_iter on "
          "%d budgets (12 boundary + %d fuzz, seed=%d), 0 disagreements."
          % (count, N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
