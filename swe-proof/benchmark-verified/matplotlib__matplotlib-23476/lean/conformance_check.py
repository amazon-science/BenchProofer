#!/usr/bin/env python3
"""G-CONF for matplotlib__matplotlib-23476.

The gold patch is already applied to /testbed when this runs, so
`Figure.__getstate__` records `state.get('_original_dpi', state['_dpi'])` into
`state['_dpi']`. We compare the R/I Python shadow of
`implementation_serializedFigureDpi` (the Lean impl, transliterated op-for-op per
refinement.md) against the REAL patched serialization behavior, read off the
dict produced by `Figure.__getstate__`, over >=1e5 fuzzed inputs. Zero
disagreements => exit 0.

Type bijection (mapping.md):
  currentDpi  : Rat          <->  state['_dpi'] at serialization time (the
                                  figure's current working resolution)
  baselineDpi : Option Rat   <->  whether the figure carries a recorded
                                  `_original_dpi` attribute (none => absent;
                                  some d => `_original_dpi == d`)
  result      : Rat          <->  the value written into state['_dpi'] by
                                  __getstate__

We avoid attaching a real GUI/Agg canvas: we drive __getstate__ directly with a
figure whose `_dpi` and (optionally) `_original_dpi` we set, then read the value
the serialized state records.

stdlib-only (besides matplotlib itself); no hypothesis required.
"""
import random
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure


def oracle(current_dpi, baseline):
    """Real patched behavior: build a Figure, set its current working
    resolution and (optionally) its recorded baseline, capture the serialized
    state, and read back the resolution it records.

    current_dpi: float
    baseline:    None | float
    Returns:     float  (state['_dpi'])
    """
    fig = Figure(dpi=current_dpi)
    # Force the current working resolution directly (bypass the property so we
    # don't trigger canvas events); mirrors a figure whose _dpi was rescaled.
    fig._dpi = current_dpi
    if baseline is None:
        # ensure no recorded baseline is present
        if hasattr(fig, "_original_dpi"):
            del fig._original_dpi
    else:
        fig._original_dpi = baseline
    state = fig.__getstate__()
    return state["_dpi"]


def shadow(current_dpi, baseline):
    """R/I transliteration of implementation_serializedFigureDpi (Lean).

    currentDpi  : Rat        -> current_dpi
    baselineDpi : Option Rat -> baseline (None | float)
    """
    value = current_dpi            # let mut value := currentDpi
    if baseline is not None:
        value = baseline           # some d => value := d
    return value                   # return value


DPI_POOL = [42.0, 294.0, 72.0, 100.0, 200.0, 1.0, 0.5, 300.0, 96.0, 150.0]


def rand_dpi(rng):
    if rng.random() < 0.45:
        return rng.choice(DPI_POOL)
    # arbitrary finite positive resolution
    return round(rng.uniform(0.1, 5000.0), 6)


def main():
    rng = random.Random(23476)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        current_dpi = rand_dpi(rng)
        if rng.random() < 0.5:
            baseline = None
        else:
            baseline = rand_dpi(rng)
        o = oracle(current_dpi, baseline)
        s = shadow(current_dpi, baseline)
        if o != s:
            disagreements += 1
            if first is None:
                first = (current_dpi, baseline, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
