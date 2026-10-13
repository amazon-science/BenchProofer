#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14894.

Executes the REAL numeric range-builder the patched assembly calls —
`numpy.arange(start, stop, step)` — on inputs satisfying the `range_step` axiom's
`Requires` (boundary + randomized fuzz, in-container) and asserts that every
observation meets the axiom's `Ensures` as encoded in model.py:

  Requires:  step >= 1,  start == 0,  stop == count*step + 1  (count >= 1)
  Ensures:   len(result) >= 2
             result[k] == k*step           for 0 <= k < len(result)
             (len(result) - 1)*step + 1 == stop

It ALSO fuzzes the partiality the axiom relies on (the `step >= 1` Requires):
on the excluded `step == 0` input the real `numpy.arange(0, stop, 0)` raises
(it cannot enumerate a half-open interval with a non-advancing step) — exactly
the undefined behaviour (a division by zero on the float step) the guarded
construction must avoid, which is why the axiom requires a strictly positive
step.

The real construction forms the row-pointer as `np.arange(0, size+1, step)`
with `size = width*n_rows` and `step = size/n_rows = width` — i.e. `start == 0`,
`step == width`, `stop == n_rows*width + 1 == count*step + 1` with
`count == n_rows`. The fuzz ranges over exactly that family (and beyond) so the
observed `np.arange` is the row-pointer the patch builds.

Imports only `numpy` (the module the patch calls) and the standard library.
Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np


def check_range_step(start, stop, step, count):
    """Assert numpy.arange(start, stop, step) meets the range_step Ensures.

    Precondition (the axiom's Requires): step >= 1, start == 0,
    stop == count*step + 1, count >= 1.
    """
    assert step >= 1 and start == 0 and count >= 1 and stop == count * step + 1

    result = list(np.arange(start, stop, step))   # the REAL callee

    # Ensures: len(result) >= 2  (the assembly's n_class == count is always
    # >= 1, so there is always the leading 0 plus at least the closing one).
    assert len(result) >= 2, (
        "range_step axiom unsound: arange(%r,%r,%r) len=%d < 2"
        % (start, stop, step, len(result)))

    # Ensures: result[k] == k*step for every enumerated boundary.
    for k, v in enumerate(result):
        assert int(v) == k * step, (
            "range_step axiom unsound: arange(%r,%r,%r)[%d] = %r != %d*%d"
            % (start, stop, step, k, v, k, step))

    # Ensures: (len-1)*step + 1 == stop  (the final boundary is the greatest
    # multiple of step below stop; no integer division needed).
    assert (len(result) - 1) * step + 1 == stop, (
        "range_step axiom unsound: arange(%r,%r,%r) len=%d violates "
        "(len-1)*step+1 == stop" % (start, stop, step, len(result)))

    # The final boundary equals the number of stored coefficients = count*step.
    assert int(result[-1]) == count * step, (
        "range_step axiom unsound: arange(%r,%r,%r) last=%r != %d"
        % (start, stop, step, result[-1], count * step))


def check_zero_step_is_undefined(stop):
    """The axiom EXCLUDES step == 0 (Requires step >= 1). Confirm the real
    callee is genuinely undefined there — it must raise rather than return a
    well-formed progression — so the exclusion is sound, not over-claiming."""
    try:
        _ = np.arange(0, stop, 0)
    except Exception:
        return  # raises (ZeroDivisionError / ValueError): undefined, as claimed
    raise AssertionError(
        "range_step axiom unsound: np.arange(0,%r,0) did NOT raise — the "
        "step>=1 Requires would be over-restrictive" % (stop,))


def main():
    # --- boundary cases over the construction's real (width, n_rows) family --
    # step == width (>=1), count == n_rows (>=1): stop == n_rows*width + 1.
    boundary = []
    for width in [1, 2, 3, 4, 5, 7, 16, 100]:
        for n_rows in [1, 2, 3, 4, 10, 50]:
            boundary.append((0, n_rows * width + 1, width, n_rows))
    # extra single-row / single-element edges
    boundary += [
        (0, 1 * 1 + 1, 1, 1),    # smallest non-trivial: [0, 1]
        (0, 1 * 9999 + 1, 9999, 1),
    ]
    for (start, stop, step, count) in boundary:
        check_range_step(start, stop, step, count)

    # --- randomized fuzz over the Requires-satisfying domain -----------------
    rng = random.Random(14894)
    for _ in range(20000):
        step = rng.randint(1, 500)          # n_SV >= 1
        count = rng.randint(1, 500)         # n_class >= 1
        stop = count * step + 1
        check_range_step(0, stop, step, count)

    # --- the excluded zero-step (n_SV == 0): real callee must be undefined ---
    for stop in [1, 2, 5, 17, 101, 1000]:
        check_zero_step_is_undefined(stop)

    print("G-AX OK: range_step axiom sound vs real numpy.arange on %d boundary "
          "+ 20000 fuzz inputs; step==0 confirmed undefined on %d witnesses"
          % (len(boundary), 6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
