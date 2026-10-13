#!/usr/bin/env python3
"""G-CONF differential conformance for matplotlib__matplotlib-26113.

Refutes the R/I refinement leg of `accumulateBins` (the per-bin aggregate
selection modeled in Solution.lean). There are NO axioms in this bundle: the
bin reducer (`reduce_C_function`) and the per-bin populations (`bins`) are FREE
INPUTS, and the one changed operation (the population threshold) is modeled
concretely. So the whole impl region is R/I-tagged (conf_skip=false).

ORACLE CHOICE — why we transliterate the patched comprehension instead of
running the real `Axes.hexbin`:
  The patched line lives deep inside `Axes.hexbin`, after unit processing, log
  scaling, hexagon-index binning, and `Cs_at_i1/Cs_at_i2` construction, and its
  result `accum` feeds a `PolyCollection`. Exercising the REAL method to read
  back the aggregate selection requires a full Figure/Axes/Agg backend and then
  reverse-engineering which bins survived from a rendered collection. The code
  ABOVE the patched line (binning, the `[1:]` out-of-range drop, the two-group
  concatenation, the `if mincnt is None: mincnt = 0` normalization) is UNCHANGED
  by the patch — pre- and post-patch run it identically — and only determines
  WHICH per-bin populations exist, not the selection rule under change. It is
  folded into the free input `bins` (mapping.md §3.2). So, per the worker
  prompt, the ORACLE is the patched selection logic transliterated VERBATIM from
  the gold-patched lib/matplotlib/axes/_axes.py:5016-5020:

      accum = np.array(
          [reduce_C_function(acc) if len(acc) >= mincnt else np.nan
           for Cs_at_i in [Cs_at_i1, Cs_at_i2]
           for acc in Cs_at_i[1:]],
          float)

  flattened over the already-constructed bin list. NaN ↔ "bin not aggregated"
  (downstream matplotlib drops it via `good_idxs = ~np.isnan(accum)`).

  The SHADOW is the model from Solution.lean (binAggregate + aggregateSeq fold).
  We differential-test SHADOW vs ORACLE over fuzzed (reduceBin, minPop, bins)
  with heavy weight on the boundary `len(bin) == minPop` (the discriminating
  input). `None` (the NaN/empty marker) is compared structurally. Exit 0 iff
  zero disagreements. stdlib only (no numpy needed: float NaN models np.nan).
"""
import math
import random
import sys

SEED = 26113
N_FUZZ = 100_000

# Concrete reducers to instantiate the free function input reduce_C_function.
# (sum mirrors np.sum / the test's `lambda v: sum(v)`; the others mirror common
#  reduce_C_function choices. Their VALUE is irrelevant to the selection rule;
#  we vary them only to exercise the R-refinement of the free input.)
REDUCERS = {
    "sum": lambda v: float(sum(v)),
    "len": lambda v: float(len(v)),
    "max": lambda v: float(max(v)) if v else float("nan"),
    "mean": lambda v: float(sum(v) / len(v)) if v else float("nan"),
}


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def bin_aggregate(reduce_bin, min_pop, bin_):
    """`binAggregate` (Solution.lean pure region): aggregate the bin iff its
    population is AT LEAST min_pop, else leave it empty (None ↔ Option.none)."""
    if len(bin_) >= min_pop:
        return reduce_bin(bin_)
    return None


def aggregate_seq(reduce_bin, min_pop, bins):
    """`aggregateSeq` (front-recursive fold) transliterated: the per-bin
    aggregate of each bin, in order, empties left as None."""
    result = []
    for b in bins:
        result.append(bin_aggregate(reduce_bin, min_pop, b))
    return result


# ---- ORACLE: patched _axes.py comprehension transliterated ----------------

def oracle_accum(reduce_bin, min_pop, bins):
    """The gold-patched comprehension, verbatim, flattened over the
    already-built bin list `bins` (= [acc for Cs_at_i in [...] for acc in
    Cs_at_i[1:]]). np.nan ↔ None for structural comparison."""
    return [reduce_bin(acc) if len(acc) >= min_pop else None
            for acc in bins]


def same(a, b):
    """Structural equality with NaN-aware float compare (None == None; a real
    aggregate compared by value, NaN==NaN treated equal since both mark a
    produced-but-undefined reduce result, which is value-identical here)."""
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
        return a == b
    return a == b


def rand_bins(rng, min_pop):
    """A random bin list, weighted to hit the discriminating boundary
    len(bin) == min_pop often."""
    n = rng.randint(0, 8)
    bins = []
    for _ in range(n):
        r = rng.random()
        if r < 0.45:
            # boundary or near-boundary population
            k = max(0, min_pop + rng.randint(-1, 1))
        else:
            k = rng.randint(0, 6)
        bins.append([rng.uniform(-100.0, 100.0) for _ in range(k)])
    return bins


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    for _ in range(N_FUZZ):
        rname = rng.choice(list(REDUCERS))
        reduce_bin = REDUCERS[rname]
        min_pop = rng.randint(0, 5)
        bins = rand_bins(rng, min_pop)

        shadow = aggregate_seq(reduce_bin, min_pop, bins)
        oracle = oracle_accum(reduce_bin, min_pop, bins)
        count += 1

        ok = len(shadow) == len(oracle) and all(
            same(s, o) for s, o in zip(shadow, oracle))
        if not ok:
            disagreements.append((rname, min_pop, bins, shadow, oracle))
            if len(disagreements) >= 8:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements[:8]))
        return 1
    print("G-CONF OK: R/I shadow of accumulateBins (binAggregate + aggregateSeq) "
          "agrees with the patched hexbin selection comprehension on %d fuzzed "
          "inputs (seed=%d, boundary-weighted len(bin)==mincnt), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
