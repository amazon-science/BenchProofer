#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-12973.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs.

THE MODEL HAS TWO OBSERVABLE BUFFERS, and this check observes both:

  data  the CALLER's buffer -- observed directly, by comparing the array the
        caller still holds after the run against its modeled value;
  work  the buffer the second routine is handed, as it stands after that routine
        returned. It is not the caller's object, so it is observed through the
        quantity the run REPORTS from it: `fit` reads that buffer at
        `R = y[:, np.newaxis] - np.dot(X, coef_path_)` to build the residuals
        that select the reported coefficient vector. So `coef_` is a function of
        `work`, and comparing `coef_` is how a run that lets the second routine
        rework that buffer is caught -- even on the leg where the caller's buffer
        is preserved and reveals nothing.

  * SHADOW  -- the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python via the mapping.md bijection. The single R op is the
              effective-copy resolution `effectiveCopy configured requested =
              requested.getD configured` (op #1). The two A-referenced routines
              are NOT transliterated: the shadow instead composes the REAL
              unchanged routines under ONE gate -- the resolved one -- exactly as
              `fit` composes them, and then transliterates `fit`'s UNCHANGED tail
              to obtain the coefficient vector the model's `work` buffer implies:

                  resolved is True   ->  data = the entry contents (dataOld)
                                         work = prepareInPlace dataOld
                  resolved is False  ->  data = work
                                         work = searchInPlace (prepareInPlace
                                                dataOld) target

  * ORACLE  -- `patch.diff`'s behaviour: the patched `LassoLarsIC.fit` applied at
              base_commit (the harness applies patch.diff before this runs).

Observable per input = `(resolved_choice, caller_buffer_matches_modeled,
coefficients_match_modeled)`. A run that resolves the choice for the first
routine but forwards the raw per-call value to the second one agrees on the first
two components and DISAGREES on the third, which is exactly the behaviour that
regresses `test_lars_precompute[LassoLarsIC]`.

The check also counts, per input, whether the two legs are actually
distinguishable (whether a truthy and a falsy gate give different coefficients),
so the agreement below cannot be vacuous.

Exit 0 iff zero disagreements. Any disagreement is a mechanical R/I-fidelity
counterexample.

THE MODELED REGION (mapping.md 3.3) is held and ASSERTED, not assumed: every
fuzzed buffer is a dense C-contiguous float matrix that `check_array(...,
dtype=FLOAT_DTYPES)` returns unchanged -- the layout is part of the region
because the first routine's reductions sum along the memory stride, so equal
contents in F order give a different float result in the last bits -- and the
estimator is built at the pinned configuration --
every setting at its constructor default except `precompute`, pinned falsy
because that is the only setting under which the second routine reaches the
buffer at all (and the setting both observable behaviours of this change are
stated in).

Runs in-container (the prebuilt SWE-Bench instance image), `sklearn` + `numpy` +
stdlib only. The fuzz seed is pinned (mapping.md 4) for a deterministic verdict.
"""
import random
import sys
import warnings

SEED = 12973
N_FUZZ = 100_000
ABSENT = object()  # argument omitted -> its default applies

# the pinned region (mapping.md 3.3): constructor defaults, except precompute
MAX_ITER = 500      # LassoLarsIC.__init__ default
NORMALIZE = True    # LassoLarsIC.__init__ default
POSITIVE = False    # LassoLarsIC.__init__ default
VERBOSE = False     # LassoLarsIC.__init__ default
CRITERION = 'aic'   # LassoLarsIC.__init__ default; selects K = 2 in the tail
PRECOMPUTE = False  # deliberate narrowing: a falsy Gram is what lets the second
#                     routine reach the buffer it is handed at all


def _eps():
    import numpy as np
    return np.finfo(float).eps


def reduction_stays_in_range(X):
    """mapping.md 3.3, the RANGE (domain) conjunct, computed the way the repo
    computes it.

    Routine 1 centers the buffer (`np.average(X, axis=0)`, base.py:149, then
    `X -= X_offset`, base.py:150) and immediately hands the result to
    `f_normalize(..., copy=False)` (base.py:152), whose `check_array` asserts
    every entry is finite (validation.py:51). When the mean's summation or the
    subtraction leaves the float64 range, that assertion fires: routine 1 raises,
    routine 2 never runs, and no buffer exists for the modeled terms to denote.
    Such runs are outside the modeled region."""
    import numpy as np
    with np.errstate(over='ignore', invalid='ignore'):
        offset = np.average(X, axis=0)
        if not np.isfinite(offset).all():
            return False
        centered = np.subtract(X, offset)
        return bool(np.isfinite(centered).all())


def both_routines_deliver(X, y):
    """`bothRoutinesDeliver` of Solution.lean — the DOMAIN of the two-routine
    sequence, decided by RUNNING it (mapping.md 3.5).

    `reduction_stays_in_range` covers only routine 1's own centering, which is a
    property of `X` alone. Routine 2 reads the TARGET, so a buffer whose
    centering is fine can still reach a descent that signals because `y`
    overflows — measured: a finite gaussian `X` accepted by `in_modeled_region`
    under `y = [1e308, 1e308, -1e308, 1e308]` raises from routine 2. The spec's
    precondition is therefore over the PAIR, and this decides it by the repo's own
    arithmetic rather than by any threshold. Gate-free: measured gate-independent
    in axiom_check.py GUARD 5."""
    try:
        modeled_run(X, y, False)
    except (ValueError, FloatingPointError):
        return False
    return True


def in_modeled_region(X):
    """mapping.md 3.3, the two buffer-shape guards.

    DTYPE: `check_array(..., dtype=FLOAT_DTYPES)` returns the SAME object only
    for a float dtype; when it does not, no in-place write can reach the
    caller's buffer.

    FORMAT: the buffer's dtype must be float64 -- routine 1's reduction runs in
    the buffer's own precision, so equal entries in another float format give a
    different result, and no signature argument carries the format.

    LAYOUT: the buffer must be C-contiguous. The first routine reduces along the
    memory stride (`np.average(X, axis=0)`, base.py:149), so equal contents in a
    different layout give a different float result in the last bits; outside this
    guard the modeled buffers are not functions of the modeled inputs and the
    model claims nothing.

    RANGE: the centering step must stay inside the float64 range, or routine 1
    raises before routine 2 runs at all and the modeled buffers have no referent
    (`reduction_stays_in_range` above, measured in `check_range_boundary`)."""
    import numpy as np
    from sklearn.utils import check_array
    from sklearn.utils.validation import FLOAT_DTYPES
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            same_object = check_array(X, copy=False, dtype=FLOAT_DTYPES) is X
    except ValueError:
        # the repo's own entry validation rejects the buffer up front, so the run
        # this model describes never happens.
        return False
    return bool(same_object and X.flags['C_CONTIGUOUS']
                and X.dtype == np.float64
                and reduction_stays_in_range(X))


# --- the R/I shadow: Solution.lean effectiveCopy, transliterated -------------
def resolve(configured, requested):
    """Op #1 (R): resolve the effective copy choice. `requested is ABSENT`
    models `requestedCopy = none` (the post-patch fit default None); a present
    value models `some b`. effectiveCopy = requested.getD configured."""
    eff_configured = True if configured is ABSENT else configured
    resolved = eff_configured if requested is ABSENT else requested
    return bool(resolved)


def modeled_run(X_entry, y, resolved):
    """The model, executed: the two REAL unchanged routines composed in `fit`'s
    order under ONE gate (the resolved choice), followed by `fit`'s UNCHANGED
    tail transliterated.

    Returns (modeled_caller_buffer, modeled_work_buffer, modeled_coefficients).
    `modeled_work_buffer` is `prepareInPlace dataOld` when the gate is truthy and
    `searchInPlace (prepareInPlace dataOld) target` when it is falsy; the
    coefficients are what the tail reports from it."""
    import numpy as np
    from sklearn.linear_model import lars_path
    from sklearn.linear_model.base import _preprocess_data
    from sklearn.utils import check_X_y

    X_caller = X_entry.copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        Xc, yc = check_X_y(X_caller, y, y_numeric=True)
        Xp, yp, _Xmean, _ymean, Xstd = _preprocess_data(
            Xc, yc, True, NORMALIZE, resolved)
        alphas, _active, coef_path, _n_iter = lars_path(
            Xp, yp, Gram=PRECOMPUTE, copy_X=resolved, copy_Gram=True,
            alpha_min=0.0, method='lasso', verbose=VERBOSE, max_iter=MAX_ITER,
            eps=_eps(), return_n_iter=True, positive=POSITIVE)
        # `Xp` is now the modeled `work` buffer. `fit`'s tail reads it:
        n_samples = Xp.shape[0]
        K = 2  # CRITERION == 'aic'
        R = yp[:, np.newaxis] - np.dot(Xp, coef_path)
        mean_squared_error = np.mean(R ** 2, axis=0)
        sigma2 = np.var(yp)
        df = np.zeros(coef_path.shape[1], dtype=int)
        for k, coef in enumerate(coef_path.T):
            mask = np.abs(coef) > np.finfo(coef.dtype).eps
            if not np.any(mask):
                continue
            df[k] = np.sum(mask)
        eps64 = np.finfo('float64').eps
        criterion = (n_samples * mean_squared_error / (sigma2 + eps64) + K * df)
        n_best = int(np.argmin(criterion))
        coef = coef_path[:, n_best] / Xstd  # base._set_intercept, fit_intercept
    return X_caller, Xp, coef


def shadow_observable(configured, requested, X, y):
    """The model's prediction for this input: the resolved choice, that the
    caller's buffer equals its modeled value, and the coefficient vector the
    modeled `work` buffer implies."""
    resolved = resolve(configured, requested)
    _caller, _work, coef = modeled_run(X, y, resolved)
    return (resolved, True, coef)


# --- the oracle: patch.diff's behaviour --------------------------------------
def oracle_observable(configured, requested, X, y):
    import numpy as np
    from sklearn.linear_model import LassoLarsIC

    init_kwargs = {"precompute": PRECOMPUTE}
    if configured is not ABSENT:
        init_kwargs["copy_X"] = configured
    model = LassoLarsIC(**init_kwargs)

    X_arg = X.copy()
    X_ref = X_arg.copy()

    fit_kwargs = {}
    if requested is not ABSENT:
        fit_kwargs["copy_X"] = requested

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(X_arg, y, **fit_kwargs)

    resolved = resolve(configured, requested)
    modeled_caller, _modeled_work, _coef = modeled_run(X_ref, y, resolved)
    return (resolved, bool(np.array_equal(X_arg, modeled_caller)),
            model.coef_.copy())


def fuzz_inputs(n, rng, nprng):
    import numpy as np
    choices = [True, False, ABSENT]
    # boundary product on a fixed matrix first
    X0 = nprng.normal(0, 1, (100, 5))
    y0 = X0[:, 2].copy()
    for configured in choices:
        for requested in choices:
            yield (configured, requested, X0, y0)
    # randomized matrices x full choice product
    for _ in range(n):
        rows = rng.randint(20, 120)
        cols = rng.randint(3, 8)
        scale = rng.choice([0.1, 1.0, 10.0, 100.0])
        # the modeled region pins the element format (mapping.md 3.3): the
        # reduction is carried out in the buffer's own precision, so a
        # float32 buffer is a DIFFERENT modeled input, not the same one.
        dtype = np.float64
        X = np.ascontiguousarray(nprng.normal(0, scale, (rows, cols)), dtype=dtype)
        y = np.ascontiguousarray(X[:, min(2, cols - 1)], dtype=dtype)
        configured = rng.choice(choices)
        requested = rng.choice(choices)
        yield (configured, requested, X, y)


def check_range_boundary():
    """The RANGE conjunct of the modeled region is where the repo puts it.

    Over a band of magnitudes straddling the float64 ceiling, the region
    predicate must agree with whether `fit` can run at all: a buffer the region
    ACCEPTS must not make `fit` raise (otherwise the shadow's terms would have no
    referent there), and the band must contain at least one buffer the region
    excludes together with a control it accepts, so the exclusion is measured
    against something. Returns (accepted, excluded)."""
    import numpy as np
    from sklearn.linear_model import LassoLarsIC

    bandrng = np.random.RandomState(SEED)
    accepted = excluded = 0
    for step in range(40):
        expo = 305.0 + 3.2 * step / 39.0
        with np.errstate(over='ignore'):
            mag = float(np.power(np.float64(10.0), np.float64(expo)))
        if not np.isfinite(mag) or mag == 0.0:
            continue
        n = 2 + (step % 4)
        X = np.ascontiguousarray(np.full((n, 2), mag, dtype=np.float64)
                                 * (1.0 - 0.25 * bandrng.rand(n, 2)))
        if not np.isfinite(X).all():
            continue
        y = np.ascontiguousarray(bandrng.rand(n))
        inside = in_modeled_region(X)
        raised = False
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                LassoLarsIC(precompute=PRECOMPUTE).fit(X.copy(), y)
        except ValueError:
            raised = True
        assert not (inside and raised), (
            "RANGE BOUNDARY VIOLATED: the region accepts a buffer (magnitude "
            "%.3e, %d rows) on which fit raises, so the shadow's buffers have "
            "no referent there" % (mag, n))
        if inside:
            accepted += 1
        elif raised:
            excluded += 1
    assert accepted and excluded, (
        "RANGE BOUNDARY: the band did not straddle the boundary (accepted=%d "
        "excluded=%d)" % (accepted, excluded))
    return accepted, excluded


def main():
    rng = random.Random(SEED)
    import numpy as np
    nprng = np.random.RandomState(SEED)
    disagreements = []
    count = 0
    legs = {True: 0, False: 0}
    buffer_discriminating = 0
    coef_discriminating = 0
    # N_FUZZ is the conceptual fuzz target; each iteration exercises one
    # (configured, requested, matrix) input and runs the estimator several times,
    # so matrix builds are capped for runtime while the full discriminating
    # choice product is exhausted on the boundary matrix.
    n_matrices = min(N_FUZZ, 20000)
    range_accepted, range_excluded = check_range_boundary()
    for (configured, requested, X, y) in fuzz_inputs(n_matrices, rng, nprng):
        count += 1
        assert in_modeled_region(X), (
            "REGION: fuzzed buffer is outside the modeled region (it must be a "
            "dense C-contiguous float matrix)")
        # The spec's precondition is over the PAIR (mapping.md 3.5): the clauses
        # that name a routine's output are asserted only where the sequence
        # delivers one. A pair on which it signals carries no obligation, so
        # comparing shadow against oracle there would be comparing two
        # non-answers.
        assert both_routines_deliver(X, y), (
            "REGION: the two-routine sequence signals on this (buffer, target) "
            "pair, so it is outside the spec's precondition and no clause "
            "applies to it")
        shadow = shadow_observable(configured, requested, X, y)
        oracle = oracle_observable(configured, requested, X, y)
        legs[shadow[0]] += 1
        # Is this input one on which the two legs are actually distinguishable?
        # Both components are checked: the caller's buffer, and the reported
        # coefficients (the observable consequence of the `work` buffer).
        preserve_caller, preserve_work, preserve_coef = modeled_run(X, y, True)
        _over_caller, over_work, over_coef = modeled_run(X, y, False)
        if not np.array_equal(preserve_work, over_work):
            buffer_discriminating += 1
        if not np.array_equal(preserve_coef, over_coef):
            coef_discriminating += 1
        agree = (shadow[0] == oracle[0] and shadow[1] == oracle[1]
                 and np.array_equal(shadow[2], oracle[2]))
        if not agree:
            disagreements.append((configured, requested, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cfg, req, sh, orc in disagreements:
            print("  configured=%r requested=%r resolved=%r/%r "
                  "buffer_ok=%r/%r coef_equal=%r"
                  % ("ABSENT" if cfg is ABSENT else cfg,
                     "ABSENT" if req is ABSENT else req, sh[0], orc[0],
                     sh[1], orc[1], bool(np.array_equal(sh[2], orc[2]))))
        return 1
    print("G-CONF OK: R/I shadow of applyWithCopyChoice agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements; preserve leg %d, "
          "overwrite leg %d. Inputs on which the two legs are distinguishable: "
          "%d by the buffer the second routine is handed, %d by the reported "
          "coefficients. Range boundary of the modeled region (mapping.md 3.3): "
          "%d buffer(s) accepted and run, %d excluded and observed to raise, 0 "
          "accepted-and-raising."
          % (count, SEED, legs[True], legs[False], buffer_discriminating,
             coef_discriminating, range_accepted, range_excluded))
    return 0


if __name__ == "__main__":
    sys.exit(main())
