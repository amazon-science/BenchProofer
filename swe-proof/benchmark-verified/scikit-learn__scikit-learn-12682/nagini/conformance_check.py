#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-12682
(nagini).

SHADOW: the impl region of model.py (encode_iteration_budget,
coder_solver_budget, estimator_encode_budget, the Estimator field store)
plus the @Pure helpers, copied verbatim below with the contract calls
(Requires/Ensures/Acc) stripped. All carriers are plain ints; no PSeq shim
is needed. There are no @ContractOnly callees (no consumed axioms).

ORACLE: the REAL patched repo functions the model models per mapping.md --
`sklearn.decomposition.dict_learning._sparse_encode` (generic single-block
coder), `sklearn.decomposition.dict_learning.sparse_encode` (public coder),
and `SparseCodingMixin.transform` reached through a `SparseCoder` carrying
the configured field. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable.

OBSERVATION BOUNDARY (mapping.md section 2): the modelled effect of the
solver constructor is exactly "the iteration budget it is handed" -- the
iterative optimisation itself is not modelled. The oracle therefore
intercepts the two solver constructors on the coder module, constructs the
real solver object, records the `max_iter` value the object holds after
construction (the constructors bind the argument verbatim), and -- in the
fast lane -- aborts before the numeric fit. A full-fit lane (no abort)
additionally confirms the recorded value is what the untouched code path
really binds when the solver goes on to fit.

Type bridge (mapping.md section 2):
  algorithm int selector <-> string selector: 0 = 'lasso_lars',
                             1 = 'lasso_cd' (the is_iterative_lasso domain)
  iteration budget (int) <-> the `max_iter` int at every layer: identity
  Estimator.configured_max_iter <-> the estimator's configured
                             transform-time iteration budget field

Per (algorithm, budget) round, three comparisons run -- one per modeled
function:
  L1: shadow encode_iteration_budget(alg, m)  vs the budget the solver
      built by the real _sparse_encode(..., max_iter=m) receives.
  L2: shadow coder_solver_budget(alg, m)      vs the budget the solver
      built by the real sparse_encode(..., max_iter=m) receives.
  L3: shadow estimator_encode_budget(Estimator(m), alg) vs the budget the
      solver built by SparseCoder(..., transform_max_iter=m).transform(X)
      receives (end-to-end through the estimator field).

Every generated input satisfies the model's Requires: algorithm in {0, 1}
(is_iterative_lasso) and max_iter >= 1; asserted per round.

>= 1e5 Requires-satisfying inputs: boundary budgets (including 1 and the
two library fallback constants +/- 1) x 2 algorithms x 3 layers, a small
full-fit lane, and 16_800 fuzz rounds x 2 algorithms x 3 layers
=> 100_800+ fast-lane comparisons plus boundary/full-fit. Pinned fuzz
seed: 12682. Exit 0 iff zero disagreements; on disagreement prints the
input and both outputs and exits 1. stdlib + numpy only.
"""
import importlib
import json
import random
import sys
import warnings

import numpy as np

SEED = 12682
N_FUZZ_ROUNDS = 16_800


# --- the impl region of model.py, verbatim, contract calls stripped ----------
# (@Pure helpers copied over as plain functions)

def is_iterative_lasso(algorithm):
    return algorithm == 0 or algorithm == 1


def lars_builtin_default():
    return 500


def coder_param_default():
    return 1000


def encode_iteration_budget(algorithm, max_iter):
    # Whichever iterative-lasso solver is built, it is constructed with the
    # supplied budget -- the budget reaches the solver unchanged.
    budget = max_iter
    return budget


def coder_solver_budget(algorithm, max_iter):
    return encode_iteration_budget(algorithm, max_iter)


class Estimator:
    # The minimal estimator: only the single touched field is modelled.
    def __init__(self, configured_max_iter):
        self.configured_max_iter = configured_max_iter


def estimator_encode_budget(self, algorithm):
    budget = coder_solver_budget(algorithm, self.configured_max_iter)
    return budget


# --- oracle plumbing over the real patched repo -------------------------------

ALG_NAMES = {0: "lasso_lars", 1: "lasso_cd"}   # int selector <-> string selector


class _StopAfterConstruction(Exception):
    """Fast lane: cut the call off at the modelled observation boundary
    (solver constructed, budget bound) before the numeric fit."""


def make_recorder(dl, record, abort):
    """Swap the two solver constructors on the coder module for factories
    that build the real object, record the iteration budget the object
    holds after construction, and (fast lane) abort before the fit."""
    real = {"lasso_lars": dl.LassoLars, "lasso_cd": dl.Lasso}

    def factory(cls):
        def build(*args, **kwargs):
            obj = cls(*args, **kwargs)
            record.append(obj.max_iter)
            if abort:
                raise _StopAfterConstruction()
            return obj
        return build

    dl.LassoLars = factory(real["lasso_lars"])
    dl.Lasso = factory(real["lasso_cd"])
    return real


def restore(dl, real):
    dl.LassoLars = real["lasso_lars"]
    dl.Lasso = real["lasso_cd"]


def observed_budget(record, call, inp):
    """The single budget recorded during `call()`; the fast lane's abort
    sentinel is expected and swallowed."""
    del record[:]
    try:
        call()
    except _StopAfterConstruction:
        pass
    assert len(record) == 1, (
        "oracle harness error: expected exactly 1 solver construction, "
        "saw %d for %s" % (len(record), inp))
    return record[0]


def check_round(dl, SparseCoder, fixtures, algorithm, m):
    """Run the three shadow-vs-real comparisons for one (algorithm, budget)
    input; return an error string on the first disagreement, else None."""
    X, D, gram, cov = fixtures
    alg = ALG_NAMES[algorithm]
    record = []
    real = make_recorder(dl, record, abort=True)
    try:
        inp = "algorithm=%d (%s) max_iter=%d" % (algorithm, alg, m)
        # Requires of the modeled functions.
        assert is_iterative_lasso(algorithm) and m >= 1, (
            "domain violation: %s" % inp)

        # L1: generic single-block coder.
        shadow = encode_iteration_budget(algorithm, m)
        got = observed_budget(record, lambda: dl._sparse_encode(
            X, D, gram, cov=(cov if alg == "lasso_lars" else None),
            algorithm=alg, regularization=1.0, max_iter=m,
            check_input=False), inp)
        if shadow != got:
            return ("DISAGREEMENT (L1 single-block coder)\n  input: %s\n"
                    "  shadow=%r\n  real solver budget=%r" % (inp, shadow, got))

        # L2: public coder layer.
        shadow = coder_solver_budget(algorithm, m)
        got = observed_budget(record, lambda: dl.sparse_encode(
            X, D, algorithm=alg, alpha=1.0, max_iter=m), inp)
        if shadow != got:
            return ("DISAGREEMENT (L2 public coder)\n  input: %s\n"
                    "  shadow=%r\n  real solver budget=%r" % (inp, shadow, got))

        # L3: end-to-end through the estimator's configured field.
        est = Estimator(m)
        shadow = estimator_encode_budget(est, algorithm)
        coder = SparseCoder(D, transform_algorithm=alg, transform_alpha=1.0,
                            transform_max_iter=m)
        got = observed_budget(record, lambda: coder.transform(X), inp)
        if shadow != got:
            return ("DISAGREEMENT (L3 estimator transform path)\n"
                    "  input: %s\n  shadow=%r\n  real solver budget=%r"
                    % (inp, shadow, got))
    finally:
        restore(dl, real)
    return None


def check_full_fit(dl, SparseCoder, fixtures, algorithm, m):
    """Full-fit lane: same three layers, no abort -- the solver really
    fits, confirming the recorded budget is bound on the live object the
    unmodified downstream code consumes."""
    X, D, gram, cov = fixtures
    alg = ALG_NAMES[algorithm]
    record = []
    real = make_recorder(dl, record, abort=False)
    try:
        inp = "full-fit algorithm=%d (%s) max_iter=%d" % (algorithm, alg, m)
        del record[:]
        dl._sparse_encode(X, D, gram,
                          cov=(cov if alg == "lasso_lars" else None),
                          algorithm=alg, regularization=1.0, max_iter=m,
                          check_input=False)
        dl.sparse_encode(X, D, algorithm=alg, alpha=1.0, max_iter=m)
        SparseCoder(D, transform_algorithm=alg, transform_alpha=1.0,
                    transform_max_iter=m).transform(X)
        shadows = [encode_iteration_budget(algorithm, m),
                   coder_solver_budget(algorithm, m),
                   estimator_encode_budget(Estimator(m), algorithm)]
        if record != shadows:
            return ("DISAGREEMENT (full-fit lane)\n  input: %s\n"
                    "  shadow=%r\n  real solver budgets=%r"
                    % (inp, shadows, record))
    finally:
        restore(dl, real)
    return None


# Boundary budgets: the domain edge, the two library fallback constants and
# their neighbours (where a budget-dropping impl diverges), and large values.
BOUNDARY_BUDGETS = [1, 2, 3, 7, 499, 500, 501, 999, 1000, 1001, 2000,
                    10 ** 6, 10 ** 9, 10 ** 12]
FULL_FIT_BUDGETS = [1, 2, 5, 100, 500, 1000, 2000]


def main():
    warnings.simplefilter("ignore")   # tiny budgets trip convergence warnings
    dl = importlib.import_module("sklearn.decomposition.dict_learning")
    SparseCoder = dl.SparseCoder

    # A small fixed problem: the budget propagation under test is
    # data-independent, so one well-formed dictionary/data pair suffices.
    rng_np = np.random.RandomState(SEED)
    D = rng_np.randn(5, 4)
    D /= np.sqrt(np.sum(D ** 2, axis=1))[:, np.newaxis]
    X = rng_np.randn(3, 4)
    gram = np.dot(D, D.T)
    cov = np.dot(D, X.T)
    fixtures = (X, D, gram, cov)

    checked = 0
    n_boundary = 0
    n_full_fit = 0

    # Boundary grid (fast lane).
    for algorithm in (0, 1):
        for m in BOUNDARY_BUDGETS:
            err = check_round(dl, SparseCoder, fixtures, algorithm, m)
            if err:
                print(err)
                return 1
            checked += 3
            n_boundary += 1

    # Full-fit lane (solvers really fit; budgets kept modest).
    for algorithm in (0, 1):
        for m in FULL_FIT_BUDGETS:
            err = check_full_fit(dl, SparseCoder, fixtures, algorithm, m)
            if err:
                print(err)
                return 1
            checked += 3
            n_full_fit += 1

    # Fuzz (fast lane), pinned seed.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ_ROUNDS):
        for algorithm in (0, 1):
            m = rng.choice([
                rng.randint(1, 10),
                rng.randint(1, 2000),
                rng.randint(400, 600),
                rng.randint(900, 1100),
                rng.randint(1, 10 ** 9),
            ])
            err = check_round(dl, SparseCoder, fixtures, algorithm, m)
            if err:
                print(err)
                return 1
            checked += 3

    print("G-CONF OK: shadow impl == real solver iteration budget at all "
          "three coder layers on %d comparisons (%d boundary + %d full-fit "
          "+ %d fuzz rounds x 2 algorithms, 3 layers each, seed %d)."
          % (checked, n_boundary, n_full_fit, 2 * N_FUZZ_ROUNDS, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "no @ContractOnly callees)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
