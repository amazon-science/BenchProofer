#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for scikit-learn__scikit-learn-14496.

The bundle models the reduction of a neighborhood-size threshold given either as
an absolute count (`> 1`) or as a fraction (`<= 1`) of the sample count, to an
absolute whole-number count (mapping.md / refinement.md):

    normCount(scaled) = max(2, int(scaled))   # post-patch, integral

MODEL BOUNDARY. The scaling of a fractional threshold by the sample count
(`min_samples * n_samples`) lies OUTSIDE the modeled behavior: it is arithmetic
the routine already performed before the modeled reduction existed, and the patch
did not touch it. The shadow therefore does not recompute that product with its
own arithmetic — it receives the scaled amount the SAME way the model does, as an
input formed by the identical float multiply the repo performs, and models only
the reduction of that amount. This is not a convenience: recomputing the product
in exact rational arithmetic and flooring THAT is a different function, disagreeing
with the repo wherever the representable product lands on the far side of an
integer from the exact one (e.g. `0.6 * 5`, whose float value is exactly 3 while
the exact rational product is just below 3), so a shadow that did so would
mis-model the repo on a whole class of inputs while this fuzz — which draws
uniform reals, not boundary-straddling ones — stayed silent.

over two routines:

  resolveMinSamples(min_samples, scaled) : the count delivered to NearestNeighbors
      inside `compute_optics_graph`.
  resolveThresholds(min_samples, min_cluster_size, scaled_lead, scaled_trail) :
      the (min_samples, min_cluster_size) pair delivered to `_xi_cluster` inside
      `cluster_optics_xi`, with an unset `min_cluster_size` defaulting to the
      already-reduced `min_samples`.

ORACLE — the REAL patched functions. We monkeypatch the immediate downstream
consumer of each routine's output to CAPTURE the normalized value(s) and abort the
expensive remainder:
  * `compute_optics_graph`  -> patch `sklearn.cluster.optics_.NearestNeighbors` to
    record its `n_neighbors` kwarg and raise a sentinel.
  * `cluster_optics_xi`     -> patch `sklearn.cluster.optics_._xi_cluster` to
    record its `min_samples` / `min_cluster_size` positional args and raise.

SHADOW — transliteration of the Lean impls (post-patch / fixed form). We diff the
captured oracle value(s) against the shadow over fuzzed thresholds. Because the
oracle is the genuine repo code, this differential test is what pins the R/I legs.

The downstream consumer requires an integer, so the oracle's captured value is
compared for exact integer equality with the shadow.

PARTIALITY. Preparing a threshold is not total: each threshold faces a range
check first, and one the check refuses is not prepared at all — the routine
raises instead of delivering a value. Both outcome shapes are therefore modeled
and both are diffed here. The refusal outcome is compared as such (`None` on both
sides), NOT skipped: a lane that filtered out-of-range inputs before calling
would leave the whole refusal behavior unmeasured, and it is exactly the
behavior the modeled functions' `Option` result exists to state. The pair routine
gets special attention because its trailing threshold defaults to the value the
routine has just computed, so the reduction can move that default OUT of the
range the leading input was inside; the enumerated cases below include a
population of one, where that is what happens.

stdlib + numpy/sklearn only. Pinned seed: 14496 (also in mapping.md).
"""
import math
import random
import sys

import numpy as np

SEED = 14496
N_FUZZ_GRAPH = 60_000
N_FUZZ_XI = 60_000


class _Captured(Exception):
    def __init__(self, payload):
        self.payload = payload


def scale(x, n):
    """The population scaling, OUTSIDE the model boundary.

    Deliberately the repo's own float multiply, unchanged by the patch. Its
    result is what enters the modeled reduction as `scaled`; the shadow never
    re-derives it in different arithmetic.
    """
    return x * n


def norm_count(scaled):
    """Post-patch reduction of an already-scaled amount: max(2, int(scaled)).

    `int(.)` truncates toward zero, which on the non-negative scaled amount is
    the floor the Lean model takes.
    """
    return max(2, int(scaled))


# ---------------------------------------------------------------------------
# resolveMinSamples — drive the real compute_optics_graph
# ---------------------------------------------------------------------------
def _install_graph_capture(optics_mod):
    orig = optics_mod.NearestNeighbors

    class _CaptureNN:
        def __init__(self, *a, **k):
            raise _Captured(("n_neighbors", k.get("n_neighbors")))

    optics_mod.NearestNeighbors = _CaptureNN
    return lambda: setattr(optics_mod, "NearestNeighbors", orig)


REFUSED = "REFUSED"
"""The routine declined to prepare a threshold at all.

A distinct value rather than `None`, so a refusal can never be confused with the
"capture never fired" path, and so the shadow's refusal must MATCH the oracle's
rather than merely both being falsey.
"""


def admits(size, n):
    """The range check, transliterated: is this threshold prepared at all?

    Positive, either whole or at most one, and not exceeding the population. The
    three conditions are spelled out rather than delegated to the repo's helper,
    because the modeled specification spells them out too and the point of this
    lane is to diff the two.
    """
    if isinstance(size, bool):
        return False
    if not size > 0:
        return False
    if size != int(size) and size > 1:
        return False
    return not size > n


def oracle_resolve_min_samples(optics_mod, min_samples, n):
    X = np.zeros((n, 2), dtype=float)
    try:
        optics_mod.compute_optics_graph(
            X, min_samples=min_samples, max_eps=np.inf, metric="minkowski",
            p=2, metric_params=None, algorithm="auto", leaf_size=30, n_jobs=1)
    except _Captured as c:
        assert c.payload[0] == "n_neighbors"
        return c.payload[1]
    except ValueError:
        return REFUSED
    return None  # pragma: no cover


def shadow_resolve_min_samples(min_samples, n, scaled):
    if not admits(min_samples, n):
        return REFUSED
    ms = min_samples
    if ms <= 1:
        ms = norm_count(scaled)
    return ms


# ---------------------------------------------------------------------------
# resolveThresholds — drive the real cluster_optics_xi
# ---------------------------------------------------------------------------
def _install_xi_capture(optics_mod):
    orig = optics_mod._xi_cluster

    def _capture(reachability_plot, predecessor_plot, ordering, xi,
                 min_samples, min_cluster_size, predecessor_correction):
        raise _Captured(("xi", min_samples, min_cluster_size))

    optics_mod._xi_cluster = _capture
    return lambda: setattr(optics_mod, "_xi_cluster", orig)


def oracle_resolve_thresholds(optics_mod, min_samples, min_cluster_size, n):
    reachability = np.full(n, np.inf)
    predecessor = np.full(n, -1, dtype=int)
    ordering = np.arange(n)
    try:
        optics_mod.cluster_optics_xi(
            reachability, predecessor, ordering, min_samples,
            min_cluster_size=min_cluster_size, xi=0.05,
            predecessor_correction=True)
    except _Captured as c:
        assert c.payload[0] == "xi"
        return c.payload[1], c.payload[2]
    except ValueError:
        return REFUSED
    return None  # pragma: no cover


def shadow_resolve_thresholds(min_samples, min_cluster_size, n, scaled_lead,
                              scaled_trail):
    if not admits(min_samples, n):
        return REFUSED
    ms = min_samples
    if ms <= 1:
        ms = norm_count(scaled_lead)
    mcs0 = ms if min_cluster_size is None else min_cluster_size
    # The trailing check's subject is `mcs0` — the DEFAULTED-or-supplied value,
    # i.e. one this shadow has itself just computed on the default path — not the
    # incoming argument. That distinction is the whole content of this leg: with
    # an unset trailing threshold on a small population, the clamped-up leading
    # count can exceed the population the leading input was inside.
    if not admits(mcs0, n):
        return REFUSED
    mcs = mcs0
    if mcs <= 1:
        mcs = norm_count(scaled_trail)
    return ms, mcs


def _eq(a, b):
    """Equality of OUTCOMES: a refusal, or a prepared threshold in magnitude AND
    form.

    A refusal matches only a refusal. Comparing it structurally rather than
    treating it as an absent value is what makes the partiality leg measurable:
    "the routine declined" and "the routine delivered a count of two" are
    different observations, and on a population of one with an unset trailing
    threshold they are precisely the two candidates.

    Magnitude alone is not enough, and this is the crux of what the modeled
    behavior delivers. The consumer of the reduced threshold counts population
    members: it discriminates on the value's TYPE, admitting an integer count and
    rejecting a divisible amount even when that amount is whole (`3.0`). So an
    oracle capture of `3.0` where the shadow says `3` is a genuine disagreement,
    not a formatting difference — and it is EXACTLY the pre-patch behavior. A
    magnitude-only comparison (`float(a) == float(b)`) reports those two equal and
    would let the whole modeled distinction go unchecked here, on the very lane
    that pins the R/I legs.

    Correspondingly the Lean carrier is a two-form `Threshold` rather than a bare
    rational, and this predicate is the shadow-side counterpart of that carrier's
    derived equality.
    """
    if a is REFUSED or b is REFUSED:
        return a is REFUSED and b is REFUSED
    if isinstance(a, bool) or isinstance(b, bool):
        return False
    a_is_count = isinstance(a, (int, np.integer))
    b_is_count = isinstance(b, (int, np.integer))
    if a_is_count != b_is_count:
        return False
    return float(a) == float(b)


def _eq_pair(got, want):
    """Outcome equality for the pair routine.

    A refusal on one side matches only a refusal on the other; otherwise both
    components must agree in magnitude and form. Written as its own predicate
    because the pair lane's outcome is `REFUSED` OR a 2-tuple, and indexing a
    refusal to compare components would raise instead of reporting a
    disagreement.
    """
    if got is REFUSED or want is REFUSED:
        return got is REFUSED and want is REFUSED
    if got is None or want is None:
        return False
    return _eq(got[0], want[0]) and _eq(got[1], want[1])


def main() -> int:
    try:
        import sklearn.cluster.optics_ as optics_mod
    except Exception as e:  # pragma: no cover
        print(f"import error: {e}")
        print("status=error")
        return 2

    rng = random.Random(SEED)
    checked = 0

    # ---- resolveMinSamples ----
    restore = _install_graph_capture(optics_mod)
    try:
        # boundary thresholds: fractions near 0/1, integer counts, edge n.
        # A population of ONE is included deliberately. It is the smallest the
        # routine accepts, and it is where the clamp-to-two interacts with the
        # population bound: a fraction there reduces to two, which already
        # exceeds the population, so it is the only population size at which the
        # reduction's own output can fall outside the range its input was inside.
        ns = [1, 2, 3, 5, 10, 25, 30, 100]
        # Boundary-STRADDLING pairs: fractions whose representable scaled amount
        # falls on the opposite side of an integer from the exact rational
        # product. These are precisely the inputs a uniform fuzz almost never
        # draws, and precisely the inputs that discriminate the modeled reduction
        # of the repo's own scaled amount from a re-derivation of the product in
        # different arithmetic. Enumerated explicitly so the discrimination is
        # part of the recorded evidence, not left to chance.
        edges = [(0.6, 5), (0.3, 10), (0.7, 10), (0.9, 10), (8 / 9, 9),
                 (3 / 7, 7), (0.29, 100), (0.57, 100), (0.83, 100)]
        for n in ns:
            edges += [(0.001, n), (0.1, n), (0.08, n), (0.5, n), (1.0, n),
                      (1.0 / n, n), (2.0 / n, n)]
            for c in range(2, min(n, 12) + 1):
                edges.append((float(c), n))   # integer-count branch
                edges.append((c, n))          # ...as an int, not a whole float
            # REFUSAL inputs, one per condition of the range check plus each
            # boundary. These are NOT skipped: the modeled behavior states what
            # the routine does with them, so they have to be diffed like any
            # other input. Previously this lane filtered them out, which left the
            # whole refusal behavior unmeasured.
            edges += [(0.0, n), (-0.5, n), (-3, n),      # non-positive
                      (n + 1, n), (float(n + 1), n),     # beyond the population
                      (n + 0.5, n),                      # beyond, non-integral
                      (float(n), n), (n, n)]             # AT the population bound
            if n > 1:
                edges += [(1.5, n), (2.5, n), (7.5, n)]  # non-integral above one
        for ms, n in edges:
            got = oracle_resolve_min_samples(optics_mod, ms, n)
            want = shadow_resolve_min_samples(ms, n, scale(ms, n))
            if not _eq(got, want):
                print(f"DISAGREE graph-edge min_samples={ms} n={n}: "
                      f"oracle={got!r} shadow={want!r}")
                print("status=fail")
                return 1
            checked += 1

        for _ in range(N_FUZZ_GRAPH):
            n = rng.choice(ns)
            r = rng.random()
            if r < 0.45:
                ms = rng.uniform(1e-6, 1.0)             # fraction branch
            elif r < 0.85:
                ms = float(rng.randint(2, max(2, n)))   # count branch
            else:
                # REFUSAL draws: out of range in each of the three ways. Drawn
                # rather than only enumerated, so the fuzz measures the refusal
                # lane at the same volume as the delivery lane instead of leaving
                # it to a handful of hand-picked points.
                ms = rng.choice([rng.uniform(-5.0, 0.0),
                                 rng.uniform(1.0, 5.0) + 0.5,
                                 float(n) + rng.uniform(0.001, 10.0),
                                 n + rng.randint(1, 10)])
            got = oracle_resolve_min_samples(optics_mod, ms, n)
            want = shadow_resolve_min_samples(ms, n, scale(ms, n))
            if not _eq(got, want):
                print(f"DISAGREE graph-fuzz min_samples={ms} n={n}: "
                      f"oracle={got!r} shadow={want!r}")
                print("status=fail")
                return 1
            checked += 1
    finally:
        restore()

    # ---- resolveThresholds ----
    restore = _install_xi_capture(optics_mod)
    try:
        ns = [1, 2, 3, 5, 10, 25, 30, 100]
        # The DEFAULTED-TRAILING class at a population of one: the leading
        # threshold is in range, reduces to the clamped count of two, and that
        # two — the value the routine itself just computed — becomes the trailing
        # threshold and exceeds the population. So the trailing check refuses a
        # pair whose leading threshold the SAME check admitted, and no
        # leading-side reasoning predicts it. Enumerated explicitly, with the
        # explicit-trailing controls beside it: those are admitted at the same
        # population, which is what shows the refusal comes from the default and
        # not from the population size alone.
        defaulted = [(0.5, None, 1), (0.25, None, 1), (1.0, None, 1),
                     (1, None, 1), (1e-6, None, 1),
                     (0.5, 0.5, 1), (0.5, 1.0, 1), (1, 1, 1),
                     (0.5, None, 2), (0.5, None, 3), (0.9, None, 2),
                     (1.0, None, 2), (0.34, None, 3)]
        for ms, mcs, n in defaulted:
            got = oracle_resolve_thresholds(optics_mod, ms, mcs, n)
            want = shadow_resolve_thresholds(
                ms, mcs, n, scale(ms, n),
                scale(mcs, n) if mcs is not None else 0.0)
            if not _eq_pair(got, want):
                print(f"DISAGREE xi-defaulted ms={ms} mcs={mcs} n={n}: "
                      f"oracle={got!r} shadow={want!r}")
                print("status=fail")
                return 1
            checked += 1

        # REFUSAL inputs on each threshold independently, so a lane that checked
        # only one of them is caught: the leading threshold refused with the
        # trailing one fine, and the trailing threshold refused with the leading
        # one fine.
        refusals = []
        for n in ns:
            refusals += [(0.0, None, n), (-0.5, None, n), (n + 1, None, n),
                         (2.5, None, n) if n > 1 else (1.5, None, n),
                         (0.5, 0.0, n), (0.5, -1.0, n), (0.5, n + 1, n),
                         (2, n + 1, n) if n >= 2 else (1, n + 1, n),
                         (2, 2.5, n) if n >= 2 else (1, 2.5, n),
                         (float(n), float(n), n), (n, n, n)]
        for ms, mcs, n in refusals:
            got = oracle_resolve_thresholds(optics_mod, ms, mcs, n)
            want = shadow_resolve_thresholds(
                ms, mcs, n, scale(ms, n),
                scale(mcs, n) if mcs is not None else 0.0)
            if not _eq_pair(got, want):
                print(f"DISAGREE xi-refusal ms={ms} mcs={mcs} n={n}: "
                      f"oracle={got!r} shadow={want!r}")
                print("status=fail")
                return 1
            checked += 1

        # Boundary-straddling pairs on BOTH thresholds (see the graph lane above):
        # the leading amount, the trailing amount, and both at once.
        straddle = [(0.6, None, 5), (0.6, 0.3, 10), (0.3, 0.6, 5), (0.7, 0.9, 10),
                    (8 / 9, 3 / 7, 9), (5.0, 0.6, 5), (0.6, 5.0, 5),
                    (0.29, 0.57, 100), (0.83, 0.29, 100)]
        for ms, mcs, n in straddle:
            got = oracle_resolve_thresholds(optics_mod, ms, mcs, n)
            want = shadow_resolve_thresholds(
                ms, mcs, n, scale(ms, n),
                scale(mcs, n) if mcs is not None else 0.0)
            if not _eq_pair(got, want):
                print(f"DISAGREE xi-straddle ms={ms} mcs={mcs} n={n}: "
                      f"oracle={got!r} shadow={want!r}")
                print("status=fail")
                return 1
            checked += 1

        for n in ns:
            mcs_opts = [None, 0.001, 0.08, 0.1, 0.5, 1.0] + \
                       [float(c) for c in range(2, min(n, 8) + 1)]
            ms_opts = [1e-6, 0.05, 0.1, 0.5, 1.0] + \
                      [float(c) for c in range(2, min(n, 8) + 1)]
            for ms in ms_opts:
                for mcs in mcs_opts:
                    got = oracle_resolve_thresholds(optics_mod, ms, mcs, n)
                    want = shadow_resolve_thresholds(
                        ms, mcs, n, scale(ms, n),
                        scale(mcs, n) if mcs is not None else 0.0)
                    if not _eq_pair(got, want):
                        print(f"DISAGREE xi-edge ms={ms} mcs={mcs} n={n}: "
                              f"oracle={got!r} shadow={want!r}")
                        print("status=fail")
                        return 1
                    checked += 1

        for _ in range(N_FUZZ_XI):
            n = rng.choice(ns)
            r = rng.random()
            if r < 0.45:
                ms = rng.uniform(1e-6, 1.0)
            elif r < 0.85:
                ms = float(rng.randint(2, max(2, n)))
            else:
                ms = rng.choice([rng.uniform(-5.0, 0.0),
                                 rng.uniform(1.0, 5.0) + 0.5,
                                 float(n) + rng.uniform(0.001, 10.0)])
            r = rng.random()
            if r < 0.35:
                mcs = None          # the defaulting path, weighted up: it is the
                                    # one whose check subject the routine computes
            elif r < 0.6:
                mcs = rng.uniform(1e-6, 1.0)
            elif r < 0.85:
                mcs = float(rng.randint(2, max(2, n)))
            else:
                mcs = rng.choice([rng.uniform(-5.0, 0.0),
                                  rng.uniform(1.0, 5.0) + 0.5,
                                  float(n) + rng.uniform(0.001, 10.0)])
            got = oracle_resolve_thresholds(optics_mod, ms, mcs, n)
            want = shadow_resolve_thresholds(
                ms, mcs, n, scale(ms, n),
                scale(mcs, n) if mcs is not None else 0.0)
            if not _eq_pair(got, want):
                print(f"DISAGREE xi-fuzz ms={ms} mcs={mcs} n={n}: "
                      f"oracle={got!r} shadow={want!r}")
                print("status=fail")
                return 1
            checked += 1
    finally:
        restore()

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
