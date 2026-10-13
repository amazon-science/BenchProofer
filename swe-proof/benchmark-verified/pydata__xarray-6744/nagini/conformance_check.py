#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6744 (nagini).

SHADOW: the impl regions of model.py (`block_ends`, `block_begins`), copied
verbatim below with the contract calls (Requires/Ensures/Invariant/Assert)
stripped. The one @Pure helper the impl regions actually call, `end_shift`,
copies over as a plain function. The remaining pure symbols
(end_at/begin_at/ends_from/begins_from and the unfold/index lemmas) are proof
scaffolding referenced only inside stripped contract lines, so no PSeq shim is
needed. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`xarray.core.rolling.DataArrayRolling.__iter__` (the per-position window
index ranges it builds and feeds to its slicing). The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable. This script never applies any diff itself.

Type bridge (mapping.md sections 1-2): the model's inputs map to the rolling
object's parameters — n <-> the size of the rolled dimension, w <-> the window
size (w > 0, enforced by the constructor), center <-> the per-dimension
centred flag. The index arrays themselves are locals of the generator, so
they are observed through the function's public outcome: rolling over a
carrier whose values equal their own positions (arange), with min_periods=1
so no NaN masking fires, makes the i-th yielded window's value list exactly
the carrier slice the i-th index range selects. The shadow's (start_i, stop_i)
are bridged through the same half-open slice semantics (Python list slicing
clips at the sequence end exactly as positional selection does), so the two
sides compare as: yielded values of position i == carrier[start_i : stop_i].
The number of yielded windows must equal n == len(shadow arrays).

Input domain: Requires demands n >= 0 and w > 0; every generated (n, w,
center) triple satisfies both, including n = 0 (empty traversal), w = 1
(centred collapses to trailing), w > n (fully clamped starts), and both
centred flags on every draw.

>= 1e5 Requires-satisfying inputs: an exhaustive boundary product (n in 0..12
plus 21, w in 1..10 plus 21, both flags) + 100000 fuzz triples.
Pinned fuzz seed: 674401.
The oracle is a deterministic pure function of (n, w, center), so its
observation is memoized per distinct triple; the shadow is re-run and diffed
on every input.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + the repo module only.
"""
import json
import random
import sys

import numpy as np
import xarray as xr

SEED = 674401
N_FUZZ = 100_000


# --- @Pure helper called by the impl regions, contracts stripped --------------

def end_shift(w, center):
    if center:
        return (w + 1) // 2
    return 1


# --- impl region of block_ends, verbatim, contract calls stripped -------------

def block_ends(n, w, center):
    shift = end_shift(w, center)
    stops = []
    k = n
    while k > 0:
        stops = [shift + (k - 1)] + stops
        k = k - 1
    return stops


# --- impl region of block_begins, verbatim, contract calls stripped -----------

def block_begins(n, w, center):
    shift = end_shift(w, center)
    starts = []
    k = n
    while k > 0:
        raw = (shift + (k - 1)) - w
        if raw > 0:
            starts = [raw] + starts
        else:
            starts = [0] + starts
        k = k - 1
    return starts


# --- oracle: the real patched generator, observed via public iteration --------

_oracle_cache = {}


def oracle_blocks(n, w, center):
    """Run the REAL patched __iter__ over a position-valued carrier and
    return (number of yielded windows, per-position value lists).
    Deterministic in (n, w, center), hence memoized."""
    key = (n, w, center)
    hit = _oracle_cache.get(key)
    if hit is not None:
        return hit
    da = xr.DataArray(np.arange(n, dtype=float), dims=("x",))
    blocks = []
    for _label, window in da.rolling(x=w, center=center, min_periods=1):
        blocks.append(window.values.tolist())
    out = (len(blocks), blocks)
    _oracle_cache[key] = out
    return out


def check_one(n, w, center):
    """Diff shadow against oracle on one Requires-satisfying input.
    Returns None on agreement, else a diagnostic string."""
    starts = block_begins(n, w, center)
    stops = block_ends(n, w, center)
    count, blocks = oracle_blocks(n, w, center)
    if not (len(starts) == n and len(stops) == n and count == n):
        return (f"length mismatch n={n} w={w} center={center}: "
                f"shadow lens=({len(starts)},{len(stops)}), oracle count={count}")
    carrier = np.arange(n, dtype=float).tolist()
    for i in range(n):
        expected = carrier[starts[i]:stops[i]]
        got = blocks[i]
        if got != expected:
            return (f"block mismatch n={n} w={w} center={center} i={i}: "
                    f"shadow range [{starts[i]},{stops[i]}) -> {expected}, "
                    f"oracle window values {got}")
    return None


def main():
    checked = 0

    # ---- exhaustive boundary product -----------------------------------------
    boundary_n = list(range(0, 13)) + [21]
    boundary_w = list(range(1, 11)) + [21]
    for n in boundary_n:
        for w in boundary_w:
            for center in (True, False):
                diag = check_one(n, w, center)
                if diag is not None:
                    print(f"DISAGREEMENT: {diag}")
                    return 1
                checked += 1
    boundary = checked

    # ---- randomized fuzz (pinned seed) ----------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 24)
        w = rng.randint(1, 32)
        center = rng.random() < 0.5
        diag = check_one(n, w, center)
        if diag is not None:
            print(f"DISAGREEMENT: {diag}")
            return 1
        checked += 1

    print(f"OK: shadow impl (block_begins/block_ends) == real patched "
          f"iteration on {checked} inputs ({boundary} boundary + {N_FUZZ} "
          f"fuzz, seed {SEED}); zero disagreements.")
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "boundary": boundary, "fuzz": N_FUZZ}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
