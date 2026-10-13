#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-14496
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant) stripped. The model IS Python:
`neighborhood_size` runs directly (a plain while-loop over floats). The @Pure
helper `clamp_low` copies over as a plain function; the other @Pure helper
`is_whole` is spec-only (it appears only inside Ensures, via a quantifier) and
carries no executable impl content, so it does not appear in the shadow. There
are no @ContractOnly callees (the axioms region is empty) and no PSeq usage.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
fractional-parameter-to-neighbourhood-size conversion inside
`sklearn.cluster.optics_`, at its three identical sites:
  (1) `compute_optics_graph` converting `min_samples`,
  (2) `cluster_optics_xi` converting `min_samples`,
  (3) `cluster_optics_xi` converting `min_cluster_size`.
The gate applies the gold patch to /testbed before this script runs and sets
PYTHONPATH so the patched package is what imports here; this script does NOT
apply any patch itself.

The converted value is an inline local of those functions, so it is observed
exactly where the real code consumes it: this script temporarily rebinds
module attributes of `sklearn.cluster.optics_` —
  * `NearestNeighbors` -> a spy whose constructor records the `n_neighbors`
    it was handed (that argument IS the converted `min_samples` of site 1)
    and raises a private capture exception, stopping the function right
    after the behaviour under test;
  * `_xi_cluster` -> a spy that records the `min_samples` and
    `min_cluster_size` arguments it was handed (the converted values of
    sites 2 and 3) and raises the same capture exception.
Everything upstream of the capture point (input validation, the conversion
itself) is the real patched repo code, executed unmodified.

Type bridge (mapping.md sections 0 and 2): the model's input `scaled` is the
float64 product of the fractional parameter with the sample count, exactly as
the repository computes it (the multiplication is upstream of the model
boundary and unchanged). The oracle is driven with a `(fraction, n_samples)`
pair; the bridge recomputes `fraction * n_samples` in this script — the
identical IEEE-754 float64 operation on the identical operands, hence
bit-identical to the product the repo forms internally — and feeds that
double to the shadow. The repo's converted value is a Python int; the
shadow's result is an integral float; they are compared by value, and the
oracle value's integrality (a genuine int) is asserted directly.

Input domain (the Requires: `scaled > 0.0`): fractions in (0, 1] with sample
counts >= 2, which the repo's own validation admits and which make the
fractional branch execute; every such product is strictly positive. Boundary
cases include the F2P pair (0.1 and 0.08 over 31 samples), the float64
round-up fixture 0.11165523996082272 * 1021 == 114.0 (the product crosses a
whole number under float64 rounding — model boundary fidelity), products
straddling the floor of two, near-whole products, and large-sample spot
checks up to 100000 samples.

>= 1e5 Requires-satisfying observations:
  * site 1: boundary battery + 40000 fuzzed (fraction, n) pairs;
  * sites 2+3: boundary battery + 31000 fuzzed calls, each observing BOTH
    converted parameters (an explicit fraction for the second one in most
    cases; ~20% of cases omit it, checking the real defaulting path hands
    the already-converted first value through unchanged).
Total observations: 20*1 + 18*2 + 40000 + 2*31000 > 100000.

Pinned fuzz seed: 14496 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' values and exits 1. stdlib + numpy only (plus the repo under test).
"""
import random
import sys

import numpy as np

SEED = 14496
N_GRAPH_FUZZ = 40000
N_XI_FUZZ = 31000


# --- SHADOW: model.py pure helper (executable), verbatim ----------------------

def clamp_low(scaled):
    """The scaled value raised to a floor of two: it is at least two, it is
    no less than the scaled value, and it equals one of the two."""
    if scaled >= 2.0:
        return scaled
    return 2.0


# (`is_whole` is spec-only: it appears exclusively inside Ensures as an
#  existential over ints and has no executable role in the impl region.)


# --- SHADOW: model.py impl region, verbatim, contract calls stripped ----------

def neighborhood_size(scaled):
    clamped = clamp_low(scaled)     # type: float
    # Reduce the value to the largest whole number not exceeding it.
    count = 0       # type: int
    acc = 0.0       # type: float
    while acc + 1.0 <= clamped:
        count = count + 1
        acc = acc + 1.0
    return acc


# --- oracle plumbing -----------------------------------------------------------

class _Captured(Exception):
    """Private capture signal: carries the converted value(s) the real code
    handed to its consumer."""

    def __init__(self, payload):
        Exception.__init__(self)
        self.payload = payload


def _fail(site, scenario, shadow_out, real_out, msg):
    print("DISAGREEMENT at %s: %s" % (site, msg))
    print("  scenario       = %r" % (scenario,))
    print("  shadow output  = %r" % (shadow_out,))
    print("  real (bridged) = %r" % (real_out,))
    sys.exit(1)


def _observe_graph(mod, frac, n):
    """Run the real `compute_optics_graph` on `n` samples with the fractional
    parameter, capturing the converted neighbourhood size at the point the
    function consumes it (the neighbour-search constructor)."""
    saved = mod.NearestNeighbors

    class _SpyNN(object):
        def __init__(self, **kwargs):
            raise _Captured(kwargs["n_neighbors"])

    mod.NearestNeighbors = _SpyNN
    try:
        X = np.empty((n, 1))
        try:
            mod.compute_optics_graph(
                X=X, min_samples=frac, max_eps=np.inf, metric="minkowski",
                p=2, metric_params=None, algorithm="auto", leaf_size=30,
                n_jobs=None)
        except _Captured as cap:
            return cap.payload
        raise AssertionError(
            "capture point never reached for (frac=%r, n=%r)" % (frac, n))
    finally:
        mod.NearestNeighbors = saved


def _observe_xi(mod, frac_ms, frac_mcs, n):
    """Run the real `cluster_optics_xi` over `n` samples, capturing BOTH
    converted parameters at the point the function consumes them (the
    cluster-extraction callee). `frac_mcs=None` exercises the real
    defaulting path."""
    saved = mod._xi_cluster

    def _spy_xi(reachability_plot, predecessor_plot, ordering, xi,
                min_samples, min_cluster_size, predecessor_correction):
        raise _Captured((min_samples, min_cluster_size))

    mod._xi_cluster = _spy_xi
    try:
        reach = np.zeros(n)
        pred = np.full(n, -1)
        ordering = np.arange(n)
        try:
            mod.cluster_optics_xi(reach, pred, ordering,
                                  min_samples=frac_ms,
                                  min_cluster_size=frac_mcs)
        except _Captured as cap:
            return cap.payload
        raise AssertionError(
            "capture point never reached for (ms=%r, mcs=%r, n=%r)"
            % (frac_ms, frac_mcs, n))
    finally:
        mod._xi_cluster = saved


def _diff_one(site, frac, n, real, scenario):
    """Bridge and diff one observation: the shadow gets the float64 product
    (recomputed here, bit-identical to the repo's own), the oracle value is
    the captured converted size."""
    scaled = frac * n            # the shared float64 product (mapping.md 0)
    if not (scaled > 0.0):       # Requires guard (never trips on this domain)
        raise AssertionError("generated input violates Requires: %r" % scaled)
    shadow = neighborhood_size(scaled)
    if not isinstance(real, int):
        _fail(site, scenario, shadow, real,
              "real converted size is not a genuine int (type %s)"
              % type(real).__name__)
    if float(real) != shadow:
        _fail(site, scenario, shadow, real,
              "converted neighbourhood size differs")


def main():
    try:
        import sklearn.cluster.optics_ as mod
    except Exception as exc:
        print("ERROR: cannot import the module under test: %r" % (exc,))
        return 2

    # boundary (fraction, n_samples) pairs: F2P inputs, the float64 round-up
    # fixture, products straddling/at the floor of two, near-whole products,
    # large-sample spot checks.
    boundary = [
        (0.1, 31), (0.08, 31),               # the F2P scenario's pairs
        (0.11165523996082272, 1021),         # float64 rounds the product UP
                                             # to exactly 114.0
        (1.0, 2), (1.0, 3), (1.0, 100),
        (0.5, 2), (0.5, 3), (0.5, 4), (0.5, 5),
        (0.1, 20), (0.1, 21), (0.1, 25),
        (0.01, 2), (0.001, 1000),
        (0.999999, 2),
        (2.0 / 3.0, 3),                      # product 2.0000000000000004
        (0.7, 100000), (1.0, 100000), (0.99999, 50000),
    ]

    n_obs = 0

    # ---- site 1: compute_optics_graph / min_samples ----
    for frac, n in boundary:
        real = _observe_graph(mod, frac, n)
        _diff_one("compute_optics_graph.min_samples", frac, n, real,
                  {"fraction": frac, "n_samples": n})
        n_obs += 1
    rng = random.Random(SEED)
    for i in range(N_GRAPH_FUZZ):
        frac = rng.uniform(1e-9, 1.0)
        n = rng.randint(2, 1000)
        real = _observe_graph(mod, frac, n)
        _diff_one("compute_optics_graph.min_samples", frac, n, real,
                  {"case": i, "fraction": frac, "n_samples": n})
        n_obs += 1

    # ---- sites 2+3: cluster_optics_xi / min_samples + min_cluster_size ----
    xi_boundary = [(ms, mcs, n)
                   for (ms, n) in boundary[:9]
                   for mcs in (0.08, None)]
    for ms, mcs, n in xi_boundary:
        real_ms, real_mcs = _observe_xi(mod, ms, mcs, n)
        scen = {"min_samples_frac": ms, "min_cluster_size_frac": mcs,
                "n_samples": n}
        _diff_one("cluster_optics_xi.min_samples", ms, n, real_ms, scen)
        n_obs += 1
        if mcs is None:
            # defaulting path: the second parameter must be handed the
            # already-converted first value, unchanged.
            if real_mcs != real_ms:
                _fail("cluster_optics_xi.min_cluster_size(default)", scen,
                      real_ms, real_mcs,
                      "defaulted second parameter differs from the "
                      "converted first")
        else:
            _diff_one("cluster_optics_xi.min_cluster_size", mcs, n,
                      real_mcs, scen)
        n_obs += 1
    for i in range(N_XI_FUZZ):
        ms = rng.uniform(1e-9, 1.0)
        n = rng.randint(2, 1000)
        mcs = None if rng.random() < 0.2 else rng.uniform(1e-9, 1.0)
        real_ms, real_mcs = _observe_xi(mod, ms, mcs, n)
        scen = {"case": i, "min_samples_frac": ms,
                "min_cluster_size_frac": mcs, "n_samples": n}
        _diff_one("cluster_optics_xi.min_samples", ms, n, real_ms, scen)
        n_obs += 1
        if mcs is None:
            if real_mcs != real_ms:
                _fail("cluster_optics_xi.min_cluster_size(default)", scen,
                      real_ms, real_mcs,
                      "defaulted second parameter differs from the "
                      "converted first")
        else:
            _diff_one("cluster_optics_xi.min_cluster_size", mcs, n,
                      real_mcs, scen)
        n_obs += 1

    print("G-CONF OK: shadow of the model impl agrees with the real patched "
          "conversion at all three sites over %d observations (boundary incl. "
          "F2P pairs and the float64 round-up fixture, + %d + %d fuzz cases); "
          "every real converted size a genuine int equal to the shadow's "
          "whole-number result; seed=%d"
          % (n_obs, N_GRAPH_FUZZ, N_XI_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
