#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-20826.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type (`dict[str, bool]`), via the
              mapping.md bijection (`String → Bool` ↔ dict). The impl is two
              `Function.update`s, one per settings map, at the distinguished key
              'gridOn': post[k] = val if k == 'gridOn' else pre[k], and no key
              is added or dropped. There are no A-tagged callees in the impl.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Axis.clear` applied at
              base_commit. We pre-populate an axis's `_major_tick_kw` /
              `_minor_tick_kw` with the fuzzed settings maps, call
              `xaxis.clear()`, and read the resulting dicts. The patched clear
              sets 'gridOn' in place and preserves every other entry; the
              pre-patch clear (via `_reset_*_tick_kw`) would `dict.clear()` them.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch.diff applied),
matplotlib + stdlib only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict. The oracle is memoised over the finite input domain so
that >=1e5 fuzzed inputs are processed without 1e5 figure mutations.
"""
import random
import sys

SEED = 20826
N_FUZZ = 100_000
KEY = "gridOn"

# The boolean tick-keyword flags this bug concerns (the per-side tick/label
# visibility flags shared axes toggle off, plus the recomputed gridOn) and a
# couple of arbitrary extra names to exercise frame preservation generally.
FLAG_KEYS = ["gridOn", "tick1On", "tick2On", "label1On", "label2On",
             "_customFlagA", "_customFlagB"]
WHICH_CHOICES = ["both", "major", "minor"]  # the validated rcParam domain


def expected_grid_on(grid, which, side):
    """Transliteration (I-tag) of the recomputed rcParams expression for the
    'gridOn' entry: rcParams['axes.grid'] and rcParams['axes.grid.which'] in
    ('both', side). Mirrors the gold patch hunk exactly."""
    return bool(grid and which in ("both", side))


def shadow_clear(pre_major, pre_minor, grid, which):
    """The R/I shadow: Function.update on KEY for each settings map. Every other
    entry is preserved; no entry is added or dropped (besides KEY, which the
    reset always writes)."""
    major = dict(pre_major)
    minor = dict(pre_minor)
    major[KEY] = expected_grid_on(grid, which, "major")
    minor[KEY] = expected_grid_on(grid, which, "minor")
    return major, minor


def make_oracle():
    """Return an oracle(pre_major, pre_minor, grid, which) that runs the patched
    Axis.clear on a fresh axis and returns the resulting (_major_tick_kw,
    _minor_tick_kw). Memoised on the (frozen maps, grid, which) domain."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    cache = {}

    def key_of(pre_major, pre_minor, grid, which):
        return (tuple(sorted(pre_major.items())),
                tuple(sorted(pre_minor.items())), grid, which)

    def oracle(pre_major, pre_minor, grid, which):
        ck = key_of(pre_major, pre_minor, grid, which)
        if ck in cache:
            return cache[ck]
        mpl.rcParams["axes.grid"] = grid
        mpl.rcParams["axes.grid.which"] = which
        fig, ax = plt.subplots()
        try:
            axis = ax.xaxis
            axis._major_tick_kw = dict(pre_major)
            axis._minor_tick_kw = dict(pre_minor)
            axis.clear()  # the patched behaviour
            out = (dict(axis._major_tick_kw), dict(axis._minor_tick_kw))
        finally:
            plt.close(fig)
        cache[ck] = out
        return out

    return oracle


def fuzz_inputs(n, rng):
    # boundary cases first
    yield ({}, {}, True, "both")
    yield ({}, {}, False, "major")
    yield ({KEY: True}, {KEY: True}, False, "minor")
    yield ({"tick1On": False, "label1On": False},
           {"tick2On": False, "label2On": False}, True, "major")
    yield ({k: True for k in FLAG_KEYS}, {k: False for k in FLAG_KEYS},
           True, "minor")
    yield ({"tick1On": False, "tick2On": False, "label1On": False,
            "label2On": False, KEY: True},
           {"tick1On": False, "tick2On": False, "label1On": False,
            "label2On": False, KEY: True}, False, "both")
    for _ in range(n):
        pre_major = {k: rng.choice([True, False])
                     for k in FLAG_KEYS if rng.random() < 0.6}
        pre_minor = {k: rng.choice([True, False])
                     for k in FLAG_KEYS if rng.random() < 0.6}
        grid = rng.choice([True, False])
        which = rng.choice(WHICH_CHOICES)
        yield (pre_major, pre_minor, grid, which)


def main():
    rng = random.Random(SEED)
    oracle = make_oracle()
    disagreements = []
    count = 0
    for pre_major, pre_minor, grid, which in fuzz_inputs(N_FUZZ, rng):
        count += 1
        s_major, s_minor = shadow_clear(pre_major, pre_minor, grid, which)
        o_major, o_minor = oracle(pre_major, pre_minor, grid, which)
        if s_major != o_major or s_minor != o_minor:
            disagreements.append((pre_major, pre_minor, grid, which,
                                  (s_major, s_minor), (o_major, o_minor)))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for pmaj, pmin, g, w, sh, orc in disagreements:
            print("  in major=%r minor=%r grid=%r which=%r shadow=%r oracle=%r"
                  % (pmaj, pmin, g, w, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resetAxisTickKeywords agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
