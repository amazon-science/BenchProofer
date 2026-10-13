#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-26113.

This bundle consumes NO `@ContractOnly` axiom: the changed per-bin decision is
modeled DEEPLY in model.py (`decision_agg`, applied element-wise and pinned by
the index-wise postcondition).  G-AX validates that deep model against the REAL
`hexbin` accumulation decision, exactly as the library computes it.

Modeled domain (model.py precondition `threshold >= 1`): the documented
positive-threshold regime — the library documents `mincnt : int > 0`, and the
F2P test observes `mincnt=1`.  The unset default (mincnt resolved to 0) is
OUTSIDE the modeled boundary: there an empty bin passes `len(acc) >= 0`, so
whether it is observably populated additionally depends on the aggregator's
value on an EMPTY list — the default `reduce_C_function=np.mean` yields NaN on
`[]` (bin cleared) while e.g. `sum` yields a real 0.0 (bin populated).  That
payload-dependent effect is not pinned by the changed comparison and cannot be
carried by the occupancy-only abstraction; on `mincnt >= 1` every kept bin is
nonempty, its aggregate of finite payloads is a real value, and the populated
decision is EXACTLY the occupancy comparison in both regimes.

Three checks:

  (A-reference, value-aggregation regime, threshold >= 1) the deep model
      `decision_agg(occ, t)` (model.py pure region: `occ >= t`) == the real
      per-bin decision in the `C is not None` branch of `Axes.hexbin`:
          reduce_C_function(acc) if len(acc) >= mincnt else np.nan
      followed by `good_idxs = ~np.isnan(accum)`.  We build `accum` exactly as
      the source does, with the DEFAULT aggregator `np.mean` (and, to pin
      payload-independence on the modeled domain, with `sum` as well), and
      read back which bins survive `~np.isnan(accum)`.

  (consistency, threshold >= 1) the value-aggregation decision == the
      bare-count regime's decision for every (occupancy, threshold).  The
      bare-count regime (`C is None` branch) clears a bin iff `count < mincnt`
      — reproduced via the same `accum[accum < mincnt] = np.nan` mask the
      source uses.  This is the `Forall` postcondition `decision_agg(occ, t)
      == decision_count(occ, t)` in model.py, and the property the F2P test
      observes.

  (boundary witness) at threshold 0 — outside the modeled domain — the
      occupancy-only abstraction genuinely breaks with the default aggregator
      (empty bin: value-aggregation clears it, bare-count keeps it), which is
      exactly why model.py restricts the domain to `threshold >= 1`.  This
      check documents that the restriction is load-bearing, not cosmetic.

Imports only `numpy` (the library `hexbin` itself depends on) and the standard
library; nothing repo-specific.  Exit 0 iff every obligation holds.
"""
import random
import sys
import warnings

import numpy as np


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def decision_agg(occ, t):
    """model.py pure `decision_agg`: value-aggregation regime, populated iff
    occ >= t."""
    return occ >= t


def decision_count(occ, t):
    """model.py pure `decision_count`: bare-count regime, populated unless the
    occupancy falls below the threshold (not (occ < t))."""
    return not (occ < t)


# --- the REAL hexbin decisions, computed exactly as lib/matplotlib/axes/_axes.py

def real_agg_populated(occ, mincnt, reduce_C_function=np.mean):
    """Reproduce the value-aggregation (`C is not None`) accum decision for a
    single bin with `occ` accumulated C-values, exactly as the post-patch
    source:  reduce_C_function(acc) if len(acc) >= mincnt else np.nan, then
    `good_idxs = ~np.isnan(accum)` decides which bins survive.  The default
    aggregator is the library's default, np.mean."""
    acc = [1.0] * occ  # a concrete C-value list of the given occupancy
    if mincnt is None:
        mincnt = 0
    with warnings.catch_warnings():
        # np.mean([]) emits "Mean of empty slice" and yields NaN — exactly the
        # real library behaviour at the out-of-domain threshold 0.
        warnings.simplefilter("ignore")
        accum = np.array(
            [reduce_C_function(acc) if len(acc) >= mincnt else np.nan],
            float)
    good = ~np.isnan(accum)
    return bool(good[0])


def real_count_populated(occ, mincnt):
    """Reproduce the bare-count (`C is None`) accum decision for a single bin
    with `occ` data points, exactly as the source:  the bin count is placed in
    `accum`, then `if mincnt is not None: accum[accum < mincnt] = np.nan`; the
    bin survives iff it is not NaN."""
    accum = np.array([occ], float)
    if mincnt is not None:
        accum[accum < mincnt] = np.nan
    good = ~np.isnan(accum)
    return bool(good[0])


# --- the checks --------------------------------------------------------------

def check_agg_reference(occ, t):
    """Deep model `decision_agg(occ, t)` == REAL value-aggregation decision,
    with the default aggregator (np.mean) AND a structurally different finite
    aggregator (sum) — on the modeled domain the decision must be
    payload/aggregator independent."""
    model = bool(decision_agg(occ, t))
    real_mean = real_agg_populated(occ, t, np.mean)
    assert model == real_mean, (
        "decision_agg deep model unsound at occ=%r, mincnt=%r "
        "(reduce_C_function=np.mean): model says populated=%r, real hexbin "
        "says %r" % (occ, t, model, real_mean))
    real_sum = real_agg_populated(occ, t, sum)
    assert model == real_sum, (
        "decision_agg deep model unsound at occ=%r, mincnt=%r "
        "(reduce_C_function=sum): model says populated=%r, real hexbin "
        "says %r" % (occ, t, model, real_sum))


def check_consistency(occ, t):
    """value-aggregation decision == bare-count decision (the Forall the
    postcondition encodes and the F2P test observes), on the REAL code."""
    agg = real_agg_populated(occ, t)
    cnt = real_count_populated(occ, t)
    assert agg == cnt, (
        "regime inconsistency at occ=%r, mincnt=%r: value-aggregation "
        "populated=%r but bare-count populated=%r" % (occ, t, agg, cnt))
    # and both match the model's two pure predicates
    assert bool(decision_agg(occ, t)) == agg, "decision_agg != real agg"
    assert bool(decision_count(occ, t)) == cnt, "decision_count != real count"


def main():
    # --- boundary cases: occupancies and thresholds around the comparison ----
    # The MODELED domain is threshold >= 1 (model.py Requires; the library
    # documents mincnt as `int > 0`). mincnt=1 is the headline case from the
    # issue: count==1 must be populated.
    boundary_occ = [0, 1, 2, 3, 5, 10]
    boundary_t = [1, 2, 3, 5, 10]
    for t in boundary_t:
        for occ in boundary_occ:
            check_agg_reference(occ, t)
            check_consistency(occ, t)

    # explicit headline witness: mincnt=1 keeps count>=1 in BOTH regimes
    assert real_agg_populated(1, 1) is True, "mincnt=1 must keep an occ=1 bin"
    assert real_count_populated(1, 1) is True, "mincnt=1 must keep an occ=1 bin"
    assert real_agg_populated(0, 1) is False, "mincnt=1 must clear an occ=0 bin"
    assert real_count_populated(0, 1) is False, "mincnt=1 must clear an occ=0 bin"

    # --- randomized fuzz over the modeled domain (threshold >= 1) ------------
    rng = random.Random(26113)
    for _ in range(20000):
        occ = rng.randint(0, 50)
        t = rng.randint(1, 50)
        check_agg_reference(occ, t)
        check_consistency(occ, t)

    # --- out-of-domain boundary witness (threshold 0 / unset default) --------
    # At mincnt=0 an EMPTY bin passes len(acc) >= 0, and the real populated
    # decision then depends on the aggregator's value on []: the DEFAULT
    # np.mean yields NaN (cleared) while sum yields 0.0 (populated); the
    # bare-count regime keeps the bin either way.  The occupancy-only
    # abstraction cannot carry that payload dependence — which is exactly why
    # model.py's precondition restricts the modeled domain to threshold >= 1.
    assert real_agg_populated(0, 0, np.mean) is False, (
        "expected: default-aggregator empty bin at mincnt=0 is CLEARED (NaN)")
    assert real_agg_populated(0, 0, sum) is True, (
        "expected: sum-aggregator empty bin at mincnt=0 is POPULATED (0.0)")
    assert real_count_populated(0, 0) is True, (
        "expected: bare-count keeps an empty bin at mincnt=0")
    assert real_count_populated(0, None) is True, (
        "expected: bare-count clears nothing when mincnt is None")
    # nonempty bins agree with the model even at mincnt=0 (finite aggregate):
    for occ in [1, 2, 5]:
        assert real_agg_populated(occ, 0) is True
        assert real_count_populated(occ, 0) is True

    print("G-AX OK: decision_agg deep model == real hexbin value-aggregation "
          "decision (default np.mean and sum aggregators), and the "
          "value-aggregation and bare-count regimes coincide, over %d "
          "boundary + 20000 fuzz (occupancy, mincnt) pairs on the modeled "
          "domain mincnt >= 1; the mincnt=0 empty-bin aggregator dependence "
          "(np.mean NaN vs sum 0.0) confirmed OUTSIDE the modeled domain, "
          "justifying model.py's threshold >= 1 precondition."
          % (len(boundary_occ) * len(boundary_t)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
