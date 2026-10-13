#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-26466 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs.

The modeled behaviour is the *copy-on-capture* semantics of two coordinate-
retaining constructors:

  * OffsetFrom.__init__   (captureCoordA)  — patched to copy ref_coord
  * _AnnotationBase.__init__ (captureCoordB) — patched to copy xy

Lean is functional and has no aliasing, so Solution.lean models the retention
behaviour DEEPLY with the `StoredCoord` / `observe` abstraction:

    snapshot x y  -> observing always yields the captured (x, y)
    reference     -> observing yields the source container's CURRENT contents

The single observable that distinguishes the two is: *mutate the source array
AFTER construction, then read the stored coordinate*.  The gold (patched)
constructors store a detached pair (a `snapshot`); the bug stored the array
itself (a `reference`).

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type. Both methods compute
              `snapshot(coords[0], coords[1])`; observing the result after any
              later mutation of the source still yields the capture-time pair.
              There are NO A-tagged callees in the impl region, so the shadow
              is pure R/I (conf_skip = false).
  * ORACLE  — `patch.diff`'s behaviour: construct the REAL patched objects from
              a numpy array, mutate the array, then read back the stored
              coordinate (`obj._ref_coord` / `obj.xy`). The real correctness
              oracle (G-RESOLVE).

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements. Runs in-container (the prebuilt SWE-Bench instance image),
stdlib + numpy (already a matplotlib dependency). The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 26466
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean captureCoordA/B, transliterated -----------
# `observe (snapshot x y) a b = (x, y)` for ALL later (a, b).  The shadow
# returns the capture-time pair regardless of how the source is later mutated.
def shadow_capture(orig_x, orig_y, later_x, later_y):
    """StoredCoord.snapshot(orig_x, orig_y), then observe under the source's
    later contents (later_x, later_y). The snapshot ignores the later state."""
    snap = ("snapshot", orig_x, orig_y)
    # observe:
    if snap[0] == "snapshot":
        return (snap[1], snap[2])
    return (later_x, later_y)


# --- the oracle: the REAL patched constructors -------------------------------
def oracle_offsetfrom(orig_x, orig_y, later_x, later_y):
    """Construct the patched OffsetFrom from a numpy array, mutate the array,
    then read back the stored reference coordinate."""
    import numpy as np
    from matplotlib.text import OffsetFrom
    from matplotlib.transforms import IdentityTransform
    arr = np.array([orig_x, orig_y])
    # artist must be a Transform/Artist/BboxBase; a Transform is the simplest
    # that needs no figure. __init__ only stores ref_coord, so any works.
    of = OffsetFrom(IdentityTransform(), arr, unit="points")
    arr[0] = later_x
    arr[1] = later_y
    x, y = of._ref_coord
    return (x, y)


def oracle_annotationbase(orig_x, orig_y, later_x, later_y):
    """Construct a patched Annotation (subclass of _AnnotationBase) from a numpy
    array xy, mutate the array, then read back the stored xy."""
    import numpy as np
    from matplotlib.text import Annotation
    arr = np.array([orig_x, orig_y])
    an = Annotation("foo", xy=arr)
    arr[0] = later_x
    arr[1] = later_y
    x, y = an.xy
    return (x, y)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    boundary = [
        (0, 0, 0, 0),
        (0, 0, 1, 1),
        (-4, 1, -4, 3),      # the problem_statement reproduction (xy_0)
        (1, 1, 1, 3),
        (5, 5, -5, -5),
        (-2147483, 99, 99, -2147483),
        (0, 0, 1000000, -1000000),
    ]
    for b in boundary:
        yield b
    for _ in range(n):
        yield (rng.randint(-10**6, 10**6), rng.randint(-10**6, 10**6),
               rng.randint(-10**6, 10**6), rng.randint(-10**6, 10**6))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (ox, oy, lx, ly) in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_capture(ox, oy, lx, ly)
        oa = oracle_offsetfrom(ox, oy, lx, ly)
        ob = oracle_annotationbase(ox, oy, lx, ly)
        # both real sites must agree with the shadow's snapshot semantics
        if (shadow[0] != oa[0] or shadow[1] != oa[1]):
            disagreements.append(("OffsetFrom", (ox, oy, lx, ly), shadow, oa))
        if (shadow[0] != ob[0] or shadow[1] != ob[1]):
            disagreements.append(("_AnnotationBase", (ox, oy, lx, ly), shadow, ob))
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for site, inp, sh, orc in disagreements:
            print("  site=%s input=%r shadow=%r oracle=%r" % (site, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of captureCoordA/captureCoordB agrees with "
          "patch.diff behaviour (copy-on-capture at both sites) on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
