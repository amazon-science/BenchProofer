#!/usr/bin/env python3
"""G-CONF differential conformance for matplotlib__matplotlib-13989 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md: the modeled
option-mapping assembly `buildHistOptions` (a dict construction + one
conditional key write) over its full finite control space plus fuzz.

ORACLE CHOICE — why we transliterate the patched assembly block instead of
driving `Axes.hist` end-to-end:
  The option mapping (`hist_kwargs`) is assembled inside
  `Axes.hist(self, x, ...)`, which requires a live `Figure`/`Axes` plus a
  Matplotlib backend, unit-conversion machinery, and a real numpy data array
  purely to read back WHICH keyword entries survive into the
  `np.histogram(..., **hist_kwargs)` call. Building that context in-container
  only to recover the two dict entries is impractical and would not isolate the
  modeled behavior. So, per the worker prompt, the ORACLE is the **patched**
  assembly block transliterated VERBATIM from the post-image of `Axes.hist`
  (`lib/matplotlib/axes/_axes.py`, lines 6654–6689): start an empty dict, set
  the `'range'` entry when bounds were determined, then — for a density,
  non-stacked computation — ADD the `'density'` entry in place
  (`hist_kwargs['density'] = density`), NOT rebind the dict. The SHADOW is the
  modeled `buildHistOptions` from Solution.lean's `buildHistOptionsM` post-image.

  We differential-test SHADOW vs ORACLE over the full finite control space
  (bounds present/absent × density × stacked) plus seeded fuzz of the opaque
  bounds payload. Exit 0 iff zero disagreements. stdlib only.
"""
import random
import sys

SEED = 13989
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean buildHistOptions, transliterated ----------
# HistOptions is modeled here as a plain dict over the two entries the assembly
# decides: the 'range' (bounds) entry and the 'density' entry. The mapping.md
# bijection: boundsOpt = some (lo, hi)  <->  d['range'] = (lo, hi);
# boundsOpt = none  <->  'range' not in d; densityOpt = some b <-> d['density'] = b.
def shadow(bounds, density, accumulate):
    """buildHistOptions transliterated: start with the bounds entry (if any) and
    no density entry; for a density, non-accumulated computation ADD the density
    entry to that same mapping ({ base with densityOpt := some density }),
    preserving the bounds entry."""
    base = {}
    if bounds is not None:
        base["range"] = bounds  # boundsOpt = some bounds
    # { base with densityOpt := some density } keeps base['range'] untouched.
    if density and not accumulate:
        out = dict(base)
        out["density"] = density
        return out
    return dict(base)


# --- the oracle: the PATCHED assembly block of Axes.hist, transliterated ------
def oracle(bounds, density, accumulate):
    """Post-image of `Axes.hist` lines 6654–6689, transliterated verbatim:

        hist_kwargs = dict()                       # :6654
        ...
        else:
            hist_kwargs['range'] = bin_range       # :6685  (single-dataset path)
        density = bool(density) or bool(normed)    # :6688
        if density and not stacked:
            hist_kwargs['density'] = density        # :6689  POST-IMAGE (fix): ADD

    The fix ADDS the 'density' key in place, so a previously-set 'range' entry
    survives into np.histogram (the bug-fix this instance is about)."""
    hist_kwargs = dict()
    if bounds is not None:
        hist_kwargs["range"] = bounds
    if density and not accumulate:
        hist_kwargs["density"] = density
    return hist_kwargs


def fuzz_payload(rng):
    """An opaque (lo, hi) bounds payload, or None (no bounds entry)."""
    if rng.random() < 0.5:
        return None
    lo = rng.uniform(-1e6, 1e6)
    hi = lo + rng.uniform(0.0, 1e6)
    return (lo, hi)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive over the finite control space: bounds {None, a fixed tuple}
    # x density {T,F} x accumulate {T,F}.
    fixed_bounds = [None, (0.0, 1.0), (-3.5, 7.25)]
    combos = [
        (b, d, a)
        for b in fixed_bounds
        for d in (True, False)
        for a in (True, False)
    ]
    # Plus seeded fuzz of the opaque bounds payload.
    combos += [
        (fuzz_payload(rng), rng.random() < 0.5, rng.random() < 0.5)
        for _ in range(N_FUZZ)
    ]

    for bounds, density, accumulate in combos:
        count += 1
        s = shadow(bounds, density, accumulate)
        o = oracle(bounds, density, accumulate)
        if s != o:
            disagreements.append((bounds, density, accumulate, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of buildHistOptionsM agrees with the patched "
          "Axes.hist option-mapping assembly on %d inputs (12 exhaustive + "
          "fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
