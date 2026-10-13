#!/usr/bin/env python3
"""G-AX soundness check for pydata__xarray-6744.

This bundle has NO axiomatized library callee (the `axioms` region is empty):
the changed operation -- the per-position window index ranges of a 1-d
moving-window traversal -- is modelled DEEPLY in Solution.lean as exact integer
arithmetic (the pure helpers `endShift`, `endAt`, `beginAt`). The only
out-of-band obligation is therefore an A-reference one: the deep model must
equal the REAL changed operation as the gold patch computes it.

The gold patch computes, with `window0 = int(self.window[0])` and
`n = self.obj.sizes[dim0]`:

    offset = (window0 + 1) // 2 if self.center[0] else 1
    stops  = arange(offset, n + offset)          # stops[i] = offset + i
    starts = stops - window0                       # starts[i] = offset + i - window0
    starts[: window0 - offset] = 0                 # leading clamp

This script reimplements that arithmetic VERBATIM (same arange / subtract /
slice-assign, with plain ints so the numpy integer result matches exactly) and
asserts, on a boundary sweep + fuzz over `(n, window, center)`, that the deep
model's closed forms agree element-by-element:

    model endAt(i)   == gold stops[i]
    model beginAt(i) == gold starts[i]

It also re-checks the algebraic facts the proof leans on
(`endShift(w, True) == ceil(w/2)`, `endShift(w, False) == 1`) and the clamp
identity `beginAt(i) == max(0, endAt(i) - window)`.

Exit 0 iff every observation matches; non-zero (with a diagnostic) otherwise.
stdlib-only imports.
"""
import random
import sys


# ---- the real changed operation, exactly as the gold patch computes it -------
def gold_starts_stops(n, window, center):
    """Reproduce the gold patch's index arrays with plain-int arithmetic
    (numpy arange/subtract/slice-assign over an integer dtype is identical)."""
    window0 = int(window)
    offset = (window0 + 1) // 2 if center else 1
    stops = list(range(offset, n + offset))          # arange(offset, n+offset)
    starts = [s - window0 for s in stops]            # stops - window0
    clamp = window0 - offset                          # starts[:clamp] = 0
    for i in range(min(clamp, len(starts))):
        starts[i] = 0
    return starts, stops


# ---- the deep model's closed forms (mirrors Solution.lean's pure region) -----
def m_end_shift(w, center):
    return (w + 1) // 2 if center else 1


def m_end_at(i, w, center):
    return i + m_end_shift(w, center)


def m_begin_at(i, w, center):
    raw = m_end_at(i, w, center) - w
    return raw if raw > 0 else 0


def ceil_div2(w):
    return -(-w // 2)  # ceil(w / 2)


def check_case(n, window, center):
    starts, stops = gold_starts_stops(n, window, center)
    assert len(stops) == n, f"stops length {len(stops)} != n={n}"
    assert len(starts) == n, f"starts length {len(starts)} != n={n}"
    for i in range(n):
        ms = m_end_at(i, window, center)
        assert ms == stops[i], (
            f"END mismatch n={n} w={window} center={center} i={i}: "
            f"model={ms} gold={stops[i]}")
        mb = m_begin_at(i, window, center)
        assert mb == starts[i], (
            f"BEGIN mismatch n={n} w={window} center={center} i={i}: "
            f"model={mb} gold={starts[i]}")
        assert mb == max(0, ms - window), (
            f"clamp identity broken n={n} w={window} center={center} i={i}")
        assert mb >= 0
    assert m_end_shift(window, False) == 1
    assert m_end_shift(window, True) == ceil_div2(window) == (window + 1) // 2


def main():
    checked = 0

    # ---- boundary sweep ------------------------------------------------------
    for n in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 21]:
        for w in [1, 2, 3, 4, 5, 6, 7, 8, 21]:
            for center in (True, False):
                check_case(n, w, center)
                checked += 1

    # ---- the issue's worked example: n=9, w=3, center=True -------------------
    starts, stops = gold_starts_stops(9, 3, True)
    assert stops == [m_end_at(i, 3, True) for i in range(9)]
    assert starts == [m_begin_at(i, 3, True) for i in range(9)]
    # position 1's centred block is [0,3) (covers values 1,2,3, mean 2.0); the
    # uncentred rule would give [0,2) at position 1.
    assert (starts[1], stops[1]) == (0, 3), (starts[1], stops[1])

    # ---- randomized fuzz -----------------------------------------------------
    rng = random.Random(20220702)
    for _ in range(200000):
        n = rng.randint(0, 60)
        w = rng.randint(1, 60)
        center = rng.random() < 0.5
        check_case(n, w, center)
        checked += 1

    print(f"OK: deep model (endAt/beginAt) == gold patch index arrays on "
          f"{checked} (n,window,center) cases; clamp + ceil(w/2) identities hold.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"AXIOM-CHECK FAILED: {e}", file=sys.stderr)
        sys.exit(1)
