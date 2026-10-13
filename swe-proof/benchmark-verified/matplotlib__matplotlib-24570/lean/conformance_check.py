#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_alignedOffsets
against the patch.diff behaviour (post-patch alignment-offset selection).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op (the baseline/left|bottom/right|top/center branch
cascade, with the offset formula chosen by exact-rational arithmetic), and we
diff it against an independent reconstruction of the *patched*
`_get_aligned_offsets` align block. Coordinates are exact rationals (Fraction) so
the comparison is bit-exact and matches the Lean `Rat` model.

Zero disagreements required over >=10^5 fuzzed inputs. stdlib-only.
exit 0 iff zero disagreements.
"""
import random
import sys
from fractions import Fraction as F

SEED = 24570          # pinned in mapping.md
N = 120_000           # >= 10^5

ALIGNS = ["baseline", "left", "top", "right", "bottom", "center"]


def max_list(xs):
    """max over a non-empty list; matches Lean `maxList` on non-empty input."""
    m = xs[0]
    for x in xs[1:]:
        if x > m:
            m = x
    return m


def shadow(hd_list, height, align):
    """R/I shadow of implementation_alignedOffsets (exact Rat arithmetic)."""
    if align == "baseline":
        height_descent = max_list([h - d for h, d in hd_list])
        descent = max_list([d for h, d in hd_list])
        h = height_descent + descent
        return (h, descent, [F(0) for _ in hd_list])
    elif align == "left" or align == "bottom":
        return (height, F(0), [d for h, d in hd_list])
    elif align == "right" or align == "top":
        return (height, F(0), [height - h + d for h, d in hd_list])
    else:  # center
        return (height, F(0), [(height - h) / 2 + d for h, d in hd_list])


def patched_render(hd_list, height, align):
    """Independent reconstruction of the PATCHED `_get_aligned_offsets` align
    block (lib/matplotlib/offsetbox.py after the fix), exact arithmetic."""
    if align == "baseline":
        height_descent = max(h - d for h, d in hd_list)
        descent = max(d for h, d in hd_list)
        height = height_descent + descent
        offsets = [F(0) for h, d in hd_list]
    elif align in ["left", "bottom"]:
        descent = F(0)
        offsets = [d for h, d in hd_list]
    elif align in ["right", "top"]:
        descent = F(0)
        offsets = [height - h + d for h, d in hd_list]
    elif align == "center":
        descent = F(0)
        offsets = [(height - h) * F(1, 2) + d for h, d in hd_list]
    return (height, descent, offsets)


def rand_rat(rng):
    return F(rng.randint(-200, 200), rng.randint(1, 12))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases incl. the F2P shape (x1,y1)=(10,30),(x2,y2)=(20,60):
    # the packer feeds cross-axis (height, descent=0) pairs; here height=max(60,30).
    fixed = [
        ([(F(30), F(0)), (F(60), F(0))], F(60), "top"),
        ([(F(30), F(0)), (F(60), F(0))], F(60), "bottom"),
        ([(F(30), F(0)), (F(60), F(0))], F(60), "baseline"),
        ([(F(30), F(0)), (F(60), F(0))], F(60), "left"),
        ([(F(30), F(0)), (F(60), F(0))], F(60), "right"),
        ([(F(30), F(0)), (F(60), F(0))], F(60), "center"),
        ([(F(5), F(2))], F(5), "top"),
        ([(F(5), F(2))], F(5), "bottom"),
    ]

    cases = list(fixed)
    for _ in range(N):
        n = rng.randint(1, 6)
        hd = [(rand_rat(rng), rand_rat(rng)) for _ in range(n)]
        height = rand_rat(rng)
        # oversample top/bottom (the fix discriminator)
        if rng.random() < 0.5:
            align = rng.choice(["top", "bottom"])
        else:
            align = rng.choice(ALIGNS)
        cases.append((hd, height, align))

    for hd, height, align in cases:
        got = shadow(hd, height, align)
        want = patched_render(hd, height, align)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((hd, height, align), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
