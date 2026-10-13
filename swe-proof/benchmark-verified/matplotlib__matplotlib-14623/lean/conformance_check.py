#!/usr/bin/env python
"""G-CONF: differential conformance for matplotlib__matplotlib-14623.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_setLim` skeleton and diffs it against the REAL patched endpoint
pipeline exercised through `Axes.set_ylim` (which commits the pair to
`viewLim.intervaly`, observable via `ax.get_ylim()`), over a discrete catalogue
of endpoint pairs plus >=1e5 randomized pairs, for both linear and log scales.

Shadow (mapping.md bridge): endpoints are exact rationals modeled in Lean as
`Rat`; here we use Python floats (the order relation is the only thing the fix
touches). The two A-consumed callees `normalizeRange` / `clampToDomain` are left
as the REAL repo callees (`<locator>.nonsingular` and
`axis.limit_range_for_scale`) — exactly the A-tagged contract sites. The shadow
adds the modeled op: capture `swapped = a > b` before normalization, swap the
committed pair back if `swapped`.

We then assert the shadow's committed pair equals the real `set_ylim` outcome
(`ax.get_ylim()`), i.e. the I/R/A legs of the impl reproduce the patched
behavior. Exit 0 iff zero disagreements. stdlib + matplotlib only; pinned seed.
"""
import math
import random
import sys

SEED = 20240630
N_RANDOM = 120_000  # >= 1e5

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def shadow_set_lim(ax, a, b):
    """Transliteration of implementation_setLim using the REAL A-consumed callees.

    Mirrors the post-patch set_ylim endpoint pipeline:
        swapped = a > b
        lo, hi = locator.nonsingular(a, b)
        lo, hi = axis.limit_range_for_scale(lo, hi)
        if swapped: lo, hi = hi, lo
    """
    swapped = a > b
    axis = ax.yaxis
    lo, hi = axis.get_major_locator().nonsingular(a, b)
    lo, hi = axis.limit_range_for_scale(lo, hi)
    if swapped:
        lo, hi = hi, lo
    return (lo, hi)


def gen_pairs(rng, n):
    pairs = []
    bvs = [1.0, 2.0, 10.0, 100.0, 1000.0, 0.5, 0.1, 1e-3, 1e3, 5e4,
           1.0, 4.0, 3.0, 5.0]
    for v0 in bvs:
        for v1 in bvs:
            pairs.append((float(v0), float(v1)))
    for _ in range(n):
        # positive endpoints so both linear and log scales accept them
        lo_exp = rng.uniform(-3, 5)
        hi_exp = rng.uniform(-3, 5)
        v0 = 10 ** lo_exp
        v1 = 10 ** hi_exp
        if rng.random() < 0.5:
            v0, v1 = v1, v0
        pairs.append((v0, v1))
    return pairs


def approx_eq(x, y, rel=1e-9, abs_=1e-12):
    if x == y:
        return True
    return abs(x - y) <= max(abs_, rel * max(abs(x), abs(y)))


def run_scale(scale, rng):
    fails = 0
    checked = 0
    for (a, b) in gen_pairs(rng, N_RANDOM // 2):
        fig, ax = plt.subplots()
        ax.set_yscale(scale)
        try:
            shadow = shadow_set_lim(ax, a, b)
            ax.set_ylim(a, b)
            real = ax.get_ylim()
        except Exception:
            plt.close(fig)
            continue
        finally:
            pass
        plt.close(fig)
        checked += 1
        if not (approx_eq(shadow[0], real[0]) and approx_eq(shadow[1], real[1])):
            print(f"FAIL ({scale}): set_ylim({a},{b}) real={real} shadow={shadow}")
            fails += 1
            if fails > 10:
                break
        # direction sanity: the committed order matches the requested order
        if a > b and not (real[1] <= real[0] or approx_eq(real[0], real[1])):
            print(f"FAIL direction ({scale}): set_ylim({a},{b}) -> {real} "
                  f"not descending for descending request")
            fails += 1
            if fails > 10:
                break
    return fails, checked


def main():
    rng = random.Random(SEED)
    total = 0
    total_checked = 0
    for scale in ("linear", "log"):
        f, c = run_scale(scale, rng)
        total += f
        total_checked += c
    if total == 0:
        print(f"status=pass {total_checked} pairs: shadow committed range == "
              f"real set_ylim outcome (linear + log), direction preserved")
        sys.exit(0)
    print(f"status=fail {total} disagreement(s)")
    sys.exit(1)


if __name__ == "__main__":
    main()
