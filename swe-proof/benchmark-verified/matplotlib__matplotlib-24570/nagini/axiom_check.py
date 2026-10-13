#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24570.

This bundle consumes NO `@ContractOnly` axiom: the operation under
specification is the per-anchor offset arithmetic of the box-alignment helper,
modelled DEEPLY in model.py (`offset_for` / the `aligned_offsets` loop). G-AX
therefore validates the deep model as an **A-reference**: it executes the REAL
(post-patch) box-alignment helper `matplotlib.offsetbox._get_aligned_offsets`
in-container and asserts that, for every anchor and every box, the offset it
returns equals the deep model's `offset_for` value under the type refinement
(integers ×2 — a uniform positive scaling, refinement.md / mapping.md).

The real helper returns ``(height, descent, offsets)``; the third element is
the per-box lower-edge offset the consumer reads back. We compare the real
offsets against `offset_for` for all six public anchors:

    baseline                 -> 0
    left, bottom (LOWER)     -> descent
    right, top   (UPPER)     -> height_total - height_box + descent
    center                   -> (height_total - height_box)/2 + descent

The model scales every value by 2 so the centre halving is exact in integer
arithmetic; G-AX undoes the scale (real_offset == model_offset / 2) so the
comparison is against the genuine float result of the real helper.

Imports only matplotlib (the repo under test) + stdlib. Exit 0 iff sound.
"""
import random
import sys

from matplotlib.offsetbox import _get_aligned_offsets


# --- model.py reference encodings (kept in lock-step with model.py) ----------

CODE_BASELINE = 0
CODE_LOWER = 1     # the "flush with low edge" group: align in {"left", "bottom"}
CODE_UPPER = 2     # the "flush with high edge" group: align in {"right", "top"}
CODE_CENTER = 3

# public anchor name -> model anchor code (post-fix interpretation)
ANCHOR_CODE = {
    "baseline": CODE_BASELINE,
    "left": CODE_LOWER,
    "bottom": CODE_LOWER,
    "right": CODE_UPPER,
    "top": CODE_UPPER,
    "center": CODE_CENTER,
}


def offset_for_scaled(h, d, total, code):
    """Reference of model.py's deep model `offset_for` (the ×2-scaled offset)."""
    if code == CODE_BASELINE:
        return 0
    if code == CODE_LOWER:
        return 2 * d
    if code == CODE_UPPER:
        return 2 * (total - h) + 2 * d
    # CODE_CENTER
    return (total - h) + 2 * d


def model_offset(h, d, total, code):
    """The genuine (un-scaled) model offset, to compare with the real float."""
    return offset_for_scaled(h, d, total, code) / 2.0


def check_case(hd_list, align):
    """Assert the deep model == the REAL _get_aligned_offsets on one case.

    For the non-baseline anchors the real helper ignores the passed ``height``
    and recomputes nothing for the offsets except via ``height = max(h)`` when
    None is given; we pass height=None so the helper uses ``max(h)`` itself,
    exactly mirroring the packers' call (self.height is None in the F2P test).
    """
    height, descent, offsets = _get_aligned_offsets(hd_list, None, align)

    # total height the helper used for the slack term:
    if align == "baseline":
        total = None  # offsets are all 0; total irrelevant
    else:
        total = max(h for h, d in hd_list)

    code = ANCHOR_CODE[align]
    for (h, d), real_off in zip(hd_list, offsets):
        expected = 0.0 if align == "baseline" else model_offset(h, d, total, code)
        assert abs(real_off - expected) < 1e-9, (
            "deep model unsound: align=%r box=(h=%r,d=%r) total=%r: "
            "real _get_aligned_offsets gave offset %r, model gives %r"
            % (align, h, d, total, real_off, expected))


def main():
    anchors = ["baseline", "left", "bottom", "right", "top", "center"]

    # --- boundary cases -----------------------------------------------------
    boundary = [
        [(30, 0), (60, 0)],            # the F2P test geometry (y1=30, y2=60)
        [(60, 0), (30, 0)],            # reversed order
        [(10, 0)],                     # single box
        [(20, 0), (20, 0)],            # equal heights (no slack)
        [(100, 0), (50, 0), (25, 0)],  # three boxes
        [(40, 5), (80, 10)],           # nonzero descents
        [(2, 1), (4, 2), (6, 3)],      # small even values (centre exact)
        [(0, 0), (10, 0)],             # a zero-height box
    ]
    for hd_list in boundary:
        for align in anchors:
            check_case(hd_list, align)

    # --- randomized fuzz ----------------------------------------------------
    rng = random.Random(24570)
    for _ in range(20000):
        n = rng.randint(1, 6)
        # even heights/descents so the centre halving stays exact under the
        # ×2 integer scale; descent <= height (the real geometry invariant).
        hd_list = []
        for _ in range(n):
            h = 2 * rng.randint(0, 100)
            d = 2 * rng.randint(0, h // 2) if h > 0 else 0
            hd_list.append((h, d))
        for align in anchors:
            check_case(hd_list, align)

    print("G-AX OK: deep model offset_for == real _get_aligned_offsets over "
          "%d boundary + 20000 fuzz layouts x 6 anchors" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
