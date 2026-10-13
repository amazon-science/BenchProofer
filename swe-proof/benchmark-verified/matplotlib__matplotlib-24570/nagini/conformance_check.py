#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24570 (nagini).

SHADOW: the impl region of model.py (`aligned_offsets`), copied verbatim below
with the contract calls (Requires/Ensures/Invariant) stripped, plus the @Pure
helpers (`CODE_*`, `offset_for`) copied as plain functions. The model IS
Python: no transliteration. There are no @ContractOnly callees (the axioms
region is empty); the per-anchor offset arithmetic is the deep model itself.

ORACLE: the REAL patched repo function the model models per mapping.md —
`matplotlib.offsetbox._get_aligned_offsets` (its third return value,
`offsets`, is the per-box lower-edge offset the model's Result() carries).
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2):
  (heights[i], descents[i]) parallel List[int] <-> hd_list[i] = (h, d) pair
  total : int                                  <-> the track height the helper
                                                   uses: the `height` argument,
                                                   or max(h) when None is
                                                   passed (the packers' call)
  code : int in {0,1,2,3}                      <-> align : str, per the anchor
                                                   name -> formula-class map
                                                   in mapping.md section 2
  Result()[i] : int (x2 scale)                 <-> offsets[i] : float
                                                   (real == shadow / 2)
The x2 scale lives in the offset formula (a uniform positive scaling that
makes the centre halving exact in integer arithmetic); every formula is
homogeneous, so integer box geometries feed both sides directly and the
un-scaling `shadow / 2` is exact in binary floating point (all values are
integer-valued sums well below 2**53), hence comparison is exact equality.

Requires-satisfying domain: len(heights) == len(descents) (parallel lists
built from one hd_list) and code in {0,1,2,3} (all six public anchor names).
hd_list is non-empty (the real helper takes max() over it). Both the
height=None call shape (what the packing consumers use) and explicit track
heights (including heights below/above max(h)) are exercised.

>= 1e5 Requires-satisfying inputs: 10 boundary layouts x 6 anchors x 5 height
modes + 8500 fuzz rounds x 6 anchors x 2 height modes = 102,300 cases.
Pinned fuzz seed: 24570.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 24570
N_FUZZ_ROUNDS = 8_500


# --- pure region of model.py, copied as plain functions ------------------------

def CODE_BASELINE():
    return 0


def CODE_LOWER():
    # the "flush with the low edge" anchor group (two synonymous anchor names)
    return 1


def CODE_UPPER():
    # the "flush with the high edge" anchor group (two synonymous anchor names)
    return 2


def CODE_CENTER():
    return 3


def offset_for(h, d, total, code):
    """The (twice-scaled) lower-edge offset of one box of height ``h`` and
    descent ``d`` inside a track of total height ``total`` under anchor
    ``code``. Pins each anchor's placement arithmetic."""
    if code == CODE_BASELINE():
        return 0
    if code == CODE_LOWER():
        return 2 * d
    if code == CODE_UPPER():
        return 2 * (total - h) + 2 * d
    # CODE_CENTER
    return (total - h) + 2 * d


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def aligned_offsets(heights, descents, total, code):
    result = []  # type: list
    i = 0
    while i < len(heights):
        h = heights[i]
        d = descents[i]
        if code == CODE_BASELINE():
            off = 0
        elif code == CODE_LOWER():
            off = 2 * d
        elif code == CODE_UPPER():
            off = 2 * (total - h) + 2 * d
        else:
            off = (total - h) + 2 * d
        result.append(off)
        i = i + 1
    return result


# --- bridge: public anchor name -> model anchor code (mapping.md section 2) ----

ANCHOR_CODE = {
    "baseline": 0,   # CODE_BASELINE
    "left": 1,       # CODE_LOWER
    "bottom": 1,     # CODE_LOWER
    "right": 2,      # CODE_UPPER
    "top": 2,        # CODE_UPPER
    "center": 3,     # CODE_CENTER
}

ANCHORS = ["baseline", "left", "bottom", "right", "top", "center"]


def check_case(real_fn, hd_list, height_arg, align):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None."""
    # total the real helper uses for its slack term: the explicit height, or
    # max box height when None is passed (mirroring the packers' call shape).
    total = height_arg if height_arg is not None else max(h for h, d in hd_list)

    heights = [h for h, d in hd_list]
    descents = [d for h, d in hd_list]
    code = ANCHOR_CODE[align]
    shadow = aligned_offsets(heights, descents, total, code)

    _height, _descent, real_offsets = real_fn(hd_list, height_arg, align)

    inp = ("hd_list=%r height=%r align=%r (total=%r code=%r)"
           % (hd_list, height_arg, align, total, code))
    if len(real_offsets) != len(shadow):
        return ("DISAGREEMENT (length)\n  input: %s\n  shadow=%r\n  real=%r"
                % (inp, shadow, list(real_offsets)))
    for i, (sh, real_off) in enumerate(zip(shadow, real_offsets)):
        expected = sh / 2.0  # undo the model's x2 scale (exact in binary FP)
        if float(real_off) != expected:
            return ("DISAGREEMENT\n  input: %s\n  box index %d\n"
                    "  shadow=%r (un-scaled %r)\n  real=%r"
                    % (inp, i, sh, expected, real_off))
    return None


def boundary_layouts():
    return [
        [(30, 0), (60, 0)],            # two boxes, one shorter than the track
        [(60, 0), (30, 0)],            # reversed order
        [(10, 0)],                     # single box
        [(20, 0), (20, 0)],            # equal heights (no slack)
        [(100, 0), (50, 0), (25, 0)],  # three boxes
        [(40, 5), (80, 10)],           # nonzero descents
        [(2, 1), (4, 2), (6, 3)],      # small values
        [(0, 0), (10, 0)],             # a zero-height box
        [(7, 7), (9, 3)],              # descent equal to height
        [(1000, 100), (999, 0), (1, 1)],  # large values, near-equal heights
    ]


def height_modes(hd_list):
    """Track-height call shapes: the consumers' height=None, plus explicit
    heights at, above and below the tallest box."""
    mx = max(h for h, d in hd_list)
    return [None, mx, mx + 7, 2 * mx + 1, max(mx - 3, 0)]


def main():
    from matplotlib.offsetbox import _get_aligned_offsets  # real patched repo fn

    checked = 0
    for hd_list in boundary_layouts():
        for height_arg in height_modes(hd_list):
            for align in ANCHORS:
                err = check_case(_get_aligned_offsets, hd_list, height_arg, align)
                if err:
                    print(err)
                    return 1
                checked += 1
    n_boundary = checked

    rng = random.Random(SEED)
    for _ in range(N_FUZZ_ROUNDS):
        n = rng.randint(1, 6)
        hd_list = []
        for _ in range(n):
            h = rng.randint(0, 200)
            d = rng.randint(0, h) if h > 0 else 0
            hd_list.append((h, d))
        explicit = rng.randint(0, 250)
        for height_arg in (None, explicit):
            for align in ANCHORS:
                err = check_case(_get_aligned_offsets, hd_list, height_arg, align)
                if err:
                    print(err)
                    return 1
                checked += 1

    print("G-CONF OK: shadow impl == real _get_aligned_offsets offsets on %d "
          "inputs (%d boundary + %d fuzz cases, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; no "
                                "axiomatized callees)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
