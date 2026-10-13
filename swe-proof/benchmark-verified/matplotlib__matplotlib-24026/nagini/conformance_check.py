#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24026
(nagini).

SHADOW: the impl region of model.py's `assign_layer_facecolors`, copied
verbatim below with the contract calls (Invariant/Assert lines) stripped.
The @Pure helpers `cyc` / `cyc_prefix` copy over as plain functions on a
tuple-backed PSeq shim; `cyc_prefix` is kept as a redundant internal
cross-check of the loop's output. There is no @ContractOnly callee.

ORACLE: the REAL patched repo function the model models per mapping.md --
`matplotlib.stackplot.stackplot` -- invoked on a live Agg axes with an
explicit non-empty colour sequence (the modelled branch). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes
the patched module importable. Two observables per trial, matching the two
postconditions:

  (1) per-layer facecolour: element i of the returned collection list must
      carry the facecolour of the supplied colour at cyclic position
      (i mod K) -- compared as RGBA tuples;
  (2) the axes' colour-cycle state is left untouched: a CONTROL axes (which
      never receives a stackplot call) and the trial axes draw their next
      default-cycle colour in lockstep after every trial; any perturbation
      of the trial axes' cycle state by the call breaks the lockstep.
      The supplied colour list object is also asserted unmutated
      (read-only input, model directive 5).

Type bridge (mapping.md section 2): a model colour token (opaque int) maps
injectively to a concrete colour spec drawn from a pool of specs with
pairwise-distinct RGBA values (CN aliases, named colours, random hex).
The shadow runs on token indices; its output decodes through the pool to
RGBA for comparison with the real facecolours. The model's `n` (layer
count) maps to the number of data rows passed to the real function; the
data values themselves are irrelevant to the modelled behaviour and are
kept minimal for speed.

Input domain: Requires demands n >= 1 and len(colors) >= 1; fuzzing draws
K in 1..10 (duplicates allowed) and n in 1..6 (larger in boundary cases),
covering n < K, n == K, n > K, exact multiples and non-multiple wraps.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz trials.
Pinned fuzz seed: 24026.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + matplotlib (the repo under test) only.
"""
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.stackplot import stackplot   # REAL patched repo function

SEED = 24026
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def of(cls, iterable):
        s = cls()
        s._t = tuple(iterable)
        return s

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __add__(self, other):
        return PSeq.of(self._t + other._t)

    def take(self, m):
        return PSeq.of(self._t[:m])

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq.of(lst)


# --- pure region of model.py, contracts stripped ------------------------------

def cyc(colors, i):
    return colors[i % len(colors)]


def cyc_prefix(colors, m):
    if m == 0:
        return colors.take(0)
    return cyc_prefix(colors, m - 1) + PSeq(cyc(colors, m - 1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------
# (the routine never writes the axes' cycle field; the shadow therefore has no
#  axes parameter at all -- observable (2) checks the same absence on the real
#  function)

def assign_layer_facecolors(colors, n):
    result = []  # type: List[int]
    i = 0
    while i < n:
        # (Invariant(...) contract calls stripped here)
        c = cyc(ToSeq(colors), i)
        result.append(c)
        # (two Assert(...) contract calls stripped here)
        i = i + 1
        # (two more Assert(...) contract calls stripped here)
    # (three Assert(...) contract calls stripped here)
    return result


# --- bridge: opaque int tokens <-> concrete colour specs -----------------------

def build_pool(rng):
    """Colour-spec pool with pairwise-distinct RGBA values: token i (a model
    int) denotes pool[i]. Injectivity makes the decode well-defined."""
    seen = set()
    pool = []
    candidates = (["C%d" % i for i in range(10)]
                  + ["r", "g", "b", "k", "m", "c", "y", "w"]
                  + ["#%06x" % rng.randrange(0x1000000) for _ in range(300)])
    for spec in candidates:
        rgba = mcolors.to_rgba(spec)
        if rgba not in seen:
            seen.add(rgba)
            pool.append(spec)
    return pool


def run_shadow(tokens, n, pool):
    """Run the shadow on the int carrier; decode its output to RGBA."""
    out = assign_layer_facecolors(list(tokens), n)
    # redundant cross-check against the pure-region helper
    pref = cyc_prefix(ToSeq(tokens), n)
    assert len(out) == len(pref) and all(
        out[i] == pref[i] for i in range(n)), "shadow internal cross-check"
    return [mcolors.to_rgba(pool[t]) for t in out]


# --- oracle plumbing -----------------------------------------------------------

class Driver:
    """One trial axes (receives the real calls) plus one control axes (never
    does): after each trial both draw their next default-cycle colour, which
    must stay in lockstep -- the executable reading of the model's
    cycle-snapshot-unchanged postcondition."""

    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.cfig, self.ctrl = plt.subplots()
        self.x = [0, 1]

    def trial(self, tokens, n, pool):
        specs = [pool[t] for t in tokens]
        specs_before = list(specs)
        rows = [[1, 2]] * n

        colls = stackplot(self.ax, self.x, *rows, colors=specs)  # REAL call
        observed = [tuple(c.get_facecolor()[0]) for c in colls]
        for c in colls:
            c.remove()

        expected = run_shadow(tokens, n, pool)

        if len(observed) != n or observed != expected:
            return ("DISAGREEMENT (per-layer facecolours)\n"
                    "  tokens=%r specs=%r n=%d\n  shadow=%r\n  real=%r"
                    % (tokens, specs_before, n, expected, observed))
        if specs != specs_before:
            return ("DISAGREEMENT (supplied colour list mutated)\n"
                    "  tokens=%r n=%d\n  before=%r\n  after=%r"
                    % (tokens, n, specs_before, specs))
        a = self.ax._get_lines.get_next_color()
        b = self.ctrl._get_lines.get_next_color()
        if a != b:
            return ("DISAGREEMENT (axes colour-cycle state perturbed)\n"
                    "  tokens=%r specs=%r n=%d\n"
                    "  trial-axes next default colour=%r\n"
                    "  control-axes next default colour=%r"
                    % (tokens, specs_before, n, a, b))
        return None

    def close(self):
        plt.close(self.fig)
        plt.close(self.cfig)


BOUNDARY = [
    # (tokens, n) -- tokens 0..9 are the CN aliases in pool order
    ([0, 1, 2], 3),      # the F2P shape: 3 colours, 3 layers
    ([0, 1, 2], 1),      # fewer layers than colours
    ([0, 1, 2], 5),      # more layers than colours -> wrap
    ([0], 1),            # single colour, single layer
    ([0], 7),            # single colour repeated
    ([3, 4], 6),         # exact multiple
    ([3, 4, 5], 7),      # non-multiple wrap
    ([5, 5, 6], 4),      # duplicate tokens in the supplied colours
    (list(range(10)), 10),
    (list(range(4)), 25),   # long draw over a short cycle
    ([9], 30),
]


def main():
    rng = random.Random(SEED)
    pool = build_pool(rng)
    checked = 0
    drv = Driver()
    try:
        for tokens, n in BOUNDARY:
            err = drv.trial(tokens, n, pool)
            if err:
                print(err)
                return 1
            checked += 1
        n_boundary = checked

        for _ in range(N_FUZZ):
            k = rng.randint(1, 10)
            tokens = [rng.randrange(len(pool)) for _ in range(k)]
            n = rng.randint(1, 6)
            err = drv.trial(tokens, n, pool)
            if err:
                print(err)
                return 1
            checked += 1
    finally:
        drv.close()

    print("G-CONF OK: shadow impl == real patched function on %d inputs "
          "(%d boundary + %d fuzz, seed %d); colour-cycle state and supplied "
          "colours untouched on every trial."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
