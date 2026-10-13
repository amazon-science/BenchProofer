#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24570
(plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`alignSpec`,
              the per-anchor placement) transliterated to Python over the real
              repo types, via the mapping.md bijection:
                  List (Rat × Rat)   <->  hd_list : list[(height, descent)]
                  Option Rat         <->  height  : float | None
                  Anchor             <->  align   : str
                  Aligned{extent, descent, offsets}
                                     <->  (height, descent, offsets) triple
              There are NO axioms / A-tagged callees in this bundle: every op is
              a concrete arithmetic relation (R/I), so the whole impl region is
              in scope for G-CONF (mapping.md §3).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `matplotlib.offsetbox._get_aligned_offsets` applied at base_commit
              (the real correctness oracle, G-RESOLVE). The harness applies the
              gold patch before this runs.

They must agree on every Requires-satisfying input (non-empty hd_list). Exit 0
iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
from fractions import Fraction

SEED = 24570
N_FUZZ = 100_000
TOL = 1e-7

# anchor names the public layout accepts (mapping.md §1): the Lean `Anchor`
# constructors <-> these strings.
ANCHORS = ["baseline", "left", "top", "right", "bottom", "center"]


def _list_max(xs):
    """listMax (Solution.lean pure region): max over a non-empty list."""
    m = xs[0]
    for x in xs[1:]:
        if x > m:
            m = x
    return m


def shadow_align(hd, height, align):
    """alignSpec (Solution.lean pure/impl region) transliterated to Python with
    exact rational arithmetic (Fraction) so the comparison is precision-clean.

    hd      : list[(Fraction, Fraction)]   -- (height, descent) per box
    height  : Fraction | None              -- Option Rat (resolvedExtent)
    align   : str                          -- Anchor
    returns : (extent, descent, offsets)   -- Aligned
    """
    def resolved_extent():
        if height is not None:
            return height
        return _list_max([h for h, d in hd])

    if align == "baseline":
        hdesc = _list_max([h - d for h, d in hd])
        desc = _list_max([d for h, d in hd])
        return (hdesc + desc, desc, [Fraction(0) for _ in hd])
    elif align in ("left", "bottom"):
        h = resolved_extent()
        return (h, Fraction(0), [d for hh, d in hd])
    elif align in ("right", "top"):
        h = resolved_extent()
        return (h, Fraction(0), [h - hh + d for hh, d in hd])
    else:  # center
        h = resolved_extent()
        return (h, Fraction(0), [(h - hh) / 2 + d for hh, d in hd])


def oracle_align(hd_float, height_float, align):
    """patch.diff's behaviour: the patched real callee. Imported lazily so the
    failure mode is a clear ImportError rather than a collection error."""
    from matplotlib.offsetbox import _get_aligned_offsets
    return _get_aligned_offsets(hd_float, height_float, align)


def _close(a, b):
    return abs(float(a) - float(b)) <= TOL


def _triples_agree(shadow, oracle):
    s_ext, s_desc, s_offs = shadow
    o_ext, o_desc, o_offs = oracle
    if not _close(s_ext, o_ext):
        return False
    if not _close(s_desc, o_desc):
        return False
    if len(s_offs) != len(o_offs):
        return False
    return all(_close(a, b) for a, b in zip(s_offs, o_offs))


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): each anchor over a small,
    # hand-picked box list, with height both None and explicit.
    base_boxes = [(20, 0), (30, 0)]      # the F2P test_packers geometry (y1,y2)
    for align in ANCHORS:
        yield (base_boxes, None, align)
        yield (base_boxes, 50, align)
        yield ([(10, 0)], None, align)            # singleton
        yield ([(10, 3), (20, 7), (5, 1)], None, align)   # with descents
        yield ([(10, 3), (20, 7), (5, 1)], 40, align)
    # randomized fuzz over integer-valued boxes (exact under Fraction and float)
    for _ in range(n):
        k = rng.randint(1, 6)
        hd = [(rng.randint(0, 100), rng.randint(0, 50)) for _ in range(k)]
        height = None if rng.random() < 0.4 else rng.randint(0, 200)
        align = rng.choice(ANCHORS)
        yield (hd, height, align)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for hd, height, align in fuzz_inputs(N_FUZZ, rng):
        count += 1
        hd_frac = [(Fraction(h), Fraction(d)) for h, d in hd]
        height_frac = None if height is None else Fraction(height)
        shadow = shadow_align(hd_frac, height_frac, align)

        hd_float = [(float(h), float(d)) for h, d in hd]
        height_float = None if height is None else float(height)
        oracle = oracle_align(hd_float, height_float, align)

        if not _triples_agree(shadow, oracle):
            disagreements.append((hd, height, align, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for hd, height, align, sh, orc in disagreements:
            print("  hd=%r height=%r align=%r shadow=%r oracle=%r"
                  % (hd, height, align, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of alignOffsets agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
