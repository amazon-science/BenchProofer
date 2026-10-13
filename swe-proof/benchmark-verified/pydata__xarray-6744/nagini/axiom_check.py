#!/usr/bin/env python3
"""G-AX soundness check for pydata__xarray-6744.

This bundle has NO axiomatized library callee: the changed operation (the
per-position window index ranges of a 1-d moving-window traversal) is modelled
DEEPLY in model.py as exact integer arithmetic (the pure helpers `end_shift`,
`end_at`, `begin_at`). The only out-of-band obligation is therefore an
A-reference one: the deep model must equal the REAL changed operation as the
gold patch computes it.

The gold patch computes, with `window0 = int(self.window[0])`,
`n = self.obj.sizes[dim0]`:

    offset = (window0 + 1) // 2 if self.center[0] else 1
    stops  = arange(offset, n + offset)          # stops[i] = offset + i
    starts = stops - window0                       # starts[i] = offset + i - window0
    starts[: window0 - offset] = 0                 # leading clamp

This script reimplements that arithmetic VERBATIM (the same arange / subtract /
slice-assign, done with plain ints so it is stdlib-only and matches the numpy
integer result exactly) and asserts, on boundary + fuzz `(n, window, center)`,
that the model's closed forms agree element-by-element:

    model end_at(i)  == gold stops[i]
    model begin_at(i) == gold starts[i]

It also re-checks the two algebraic facts the proof leans on
(`end_shift(w, True) == ceil(w/2)` and `end_shift(w, False) == 1`) and the
clamp identity `begin_at(i) == max(0, end_at(i) - window)`.

Exit 0 iff every observation matches; non-zero (with a diagnostic) otherwise.
stdlib-only imports.
"""
import random
import sys


# ---- the real changed operation, exactly as the gold patch computes it -------
def gold_starts_stops(n, window, center):
    """Reproduce the gold patch's `__iter__` index arrays with plain-int
    arithmetic (numpy arange/subtract/slice-assign over an integer dtype gives
    identical integer values)."""
    window0 = int(window)
    offset = (window0 + 1) // 2 if center else 1
    # stops = np.arange(offset, n + offset)
    stops = list(range(offset, n + offset))
    # starts = stops - window0
    starts = [s - window0 for s in stops]
    # starts[: window0 - offset] = 0
    clamp = window0 - offset
    for i in range(min(clamp, len(starts))):
        starts[i] = 0
    return starts, stops


# ---- the model's deep closed forms (mirrors model.py's pure region) ----------
def m_end_shift(w, center):
    return (w + 1) // 2 if center else 1


def m_stop_at(i, w, center):
    return i + m_end_shift(w, center)


def m_start_at(i, w, center):
    raw = m_stop_at(i, w, center) - w
    return raw if raw > 0 else 0


def ceil_div2(w):
    return -(-w // 2)  # ceil(w / 2)


def check_case(n, window, center):
    starts, stops = gold_starts_stops(n, window, center)
    assert len(stops) == n, f"stops length {len(stops)} != n={n} ({n},{window},{center})"
    assert len(starts) == n, f"starts length {len(starts)} != n={n} ({n},{window},{center})"
    for i in range(n):
        ms = m_stop_at(i, window, center)
        gt = stops[i]
        assert ms == gt, (
            f"STOP mismatch n={n} w={window} center={center} i={i}: "
            f"model={ms} gold={gt}"
        )
        mst = m_start_at(i, window, center)
        gst = starts[i]
        assert mst == gst, (
            f"START mismatch n={n} w={window} center={center} i={i}: "
            f"model={mst} gold={gst}"
        )
        # clamp identity used in the proof
        assert mst == max(0, ms - window), (
            f"clamp identity broken n={n} w={window} center={center} i={i}"
        )
        assert mst >= 0
    # algebraic facts the proof relies on
    assert m_end_shift(window, False) == 1
    assert m_end_shift(window, True) == ceil_div2(window) == (window + 1) // 2


def main():
    checked = 0

    # ---- boundary sweep ------------------------------------------------------
    # sizes including the issue's n=9, the test's n in {21}, edges n in {0,1,2},
    # and the test parametrization windows {1,2,3,7}; both center flags.
    boundary_n = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 21]
    boundary_w = [1, 2, 3, 4, 5, 6, 7, 8, 21]
    for n in boundary_n:
        for w in boundary_w:
            for center in (True, False):
                check_case(n, w, center)
                checked += 1

    # ---- the exact reproduction of the issue's worked example ----------------
    # my_data = arange(1,10) (n=9), window=3, center=True ->
    # centred mean is [nan,2,3,4,5,6,7,8,nan]; manual iteration must match.
    starts, stops = gold_starts_stops(9, 3, True)
    assert stops == [m_stop_at(i, 3, True) for i in range(9)]
    assert starts == [m_start_at(i, 3, True) for i in range(9)]
    # position 1's block is [0,3) (covers values 1,2,3, mean 2.0) under centring;
    # the non-centred (buggy) rule would give block [0,2) at position 1.
    assert (starts[1], stops[1]) == (0, 3), (starts[1], stops[1])

    # ---- randomized fuzz -----------------------------------------------------
    rng = random.Random(20220702)
    for _ in range(200000):
        n = rng.randint(0, 60)
        w = rng.randint(1, 60)
        center = rng.random() < 0.5
        check_case(n, w, center)
        checked += 1

    print(f"OK: deep model (begin_at/end_at) == gold patch index arrays on "
          f"{checked} (n,window,center) cases; clamp + ceil(w/2) identities hold.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"AXIOM-CHECK FAILED: {e}", file=sys.stderr)
        sys.exit(1)
