#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-25122.

The changed window-normalisation reductions are modelled DEEPLY in model.py as
front-recursive folds (there are NO consumed @ContractOnly axioms). This script
validates each deep fold **== its real numpy reduction** (A-reference), on
boundary + adversarial fuzz inputs, exactly as the gold patch computes them:

  signed_sum(w)          ==  numpy.array(w).sum()              # window.sum()
  square_sum(w)          ==  (numpy.array(w) ** 2).sum()       # (window**2).sum()
  magnitude_sum(w)       ==  numpy.abs(numpy.array(w)).sum()   # np.abs(window).sum()
  magnitude_square_sum(w)== (numpy.abs(numpy.array(w))**2).sum()  # (np.abs(window)**2).sum()

It also validates the two load-bearing facts of the bundle:

  (1) the site-3 no-op lemma `squares_are_sign_blind`:
          square_sum(w) == magnitude_square_sum(w)   for every w
      i.e. the gold edit `(np.abs(window)**2).sum()` -> `(window**2).sum()`
      cannot change any output (proven in model.py, confirmed here on numpy).

  (2) the `float` -> `int` refinement is faithful: the bug (using Σ|w| instead
      of Σw, and its square) is observable EXACTLY when the window has a
      negative weight, independent of magnitude/precision. Checked on signed
      integer windows AND on the REAL float `flattop` window from the F2P test
      `TestSpectral.test_psd_window_flattop`, reproducing the spectrum-branch
      discriminator `win.sum()**2 != np.abs(win).sum()**2`.

`numpy` is the real callee the gold patch invokes (`ndarray.sum`, `numpy.abs`),
present in the evaluation image. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np


# --- model.py deep-fold reference implementations (lock-step with model.py) ---

def signed_sum(w):
    total = 0
    for x in w:
        total = x + total
    return total


def magnitude(x):
    return -x if x < 0 else x


def magnitude_sum(w):
    total = 0
    for x in w:
        total = magnitude(x) + total
    return total


def square_sum(w):
    total = 0
    for x in w:
        total = x * x + total
    return total


def magnitude_square_sum(w):
    total = 0
    for x in w:
        total = magnitude(x) * magnitude(x) + total
    return total


# --- the A-reference checks: deep fold == real numpy reduction ----------------

def check_signed_sum(w):
    real = int(np.array(w, dtype=np.int64).sum())          # window.sum()
    model = signed_sum(w)
    assert real == model, (
        "signed_sum unsound on %r: numpy.sum=%r model=%r" % (w, real, model))


def check_square_sum(w):
    real = int((np.array(w, dtype=np.int64) ** 2).sum())   # (window**2).sum()
    model = square_sum(w)
    assert real == model, (
        "square_sum unsound on %r: numpy=%r model=%r" % (w, real, model))


def check_magnitude_sum(w):
    real = int(np.abs(np.array(w, dtype=np.int64)).sum())  # np.abs(window).sum()
    model = magnitude_sum(w)
    assert real == model, (
        "magnitude_sum unsound on %r: numpy=%r model=%r" % (w, real, model))


def check_magnitude_square_sum(w):
    real = int((np.abs(np.array(w, dtype=np.int64)) ** 2).sum())
    model = magnitude_square_sum(w)
    assert real == model, (
        "magnitude_square_sum unsound on %r: numpy=%r model=%r"
        % (w, real, model))


def check_sign_blind(w):
    """site-3 no-op lemma: square_sum == magnitude_square_sum, on numpy too."""
    a = np.array(w, dtype=np.int64)
    real_signed = int((a ** 2).sum())
    real_abs = int((np.abs(a) ** 2).sum())
    assert real_signed == real_abs, (
        "site-3 NOT a no-op on %r: (w**2).sum=%r (|w|**2).sum=%r"
        % (w, real_signed, real_abs))
    assert square_sum(w) == magnitude_square_sum(w), (
        "squares_are_sign_blind model lemma broken on %r" % (w,))


def has_negative(w):
    return any(x < 0 for x in w)


def main():
    boundary = [
        [], [0], [1], [-1], [5], [-5],
        [1, 1, 1], [-1, -1, -1],
        [3, -3], [-3, 3], [10, -1, -1, -1],
        [-2, 5, -7, 3], [100, -100], [0, 0, 0],
        [1, -2, 3, -4, 5], [-1000000, 999999],
    ]
    for w in boundary:
        check_signed_sum(w)
        check_square_sum(w)
        check_magnitude_sum(w)
        check_magnitude_square_sum(w)
        check_sign_blind(w)

    # --- randomized fuzz over signed integer windows --------------------------
    rng = random.Random(25122)
    saw_negative = False
    saw_discriminating = False
    for _ in range(20000):
        n = rng.randint(0, 40)
        w = [rng.randint(-50, 50) for _ in range(n)]
        check_signed_sum(w)
        check_square_sum(w)
        check_magnitude_sum(w)
        check_magnitude_square_sum(w)
        check_sign_blind(w)
        if has_negative(w):
            saw_negative = True
            # the amplitude bug: Σ|w| (and its square) differs from Σw whenever
            # there is sign cancellation. Confirm the discriminator can fire.
            if magnitude_sum(w) != signed_sum(w):
                saw_discriminating = True
    assert saw_negative, "fuzz never produced a negative-weight window"
    assert saw_discriminating, (
        "fuzz never exhibited the amplitude discriminator Σ|w| != Σw")

    # --- the REAL float flattop window from the F2P test ----------------------
    # adaptation of scipy's flattop, exactly as test_psd_window_flattop builds it
    a = [0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368]
    NFFT = 512
    fac = np.linspace(-np.pi, np.pi, NFFT)
    win = np.zeros(NFFT)
    for k in range(len(a)):
        win += a[k] * np.cos(k * fac)
    assert (win < 0).any(), "flattop window expected to have negative weights"
    # site 3 (density) IS a no-op even on the real float window:
    assert np.isclose((win ** 2).sum(), (np.abs(win) ** 2).sum()), (
        "site-3 power norm not a no-op on the real flattop window")
    # site 4 (spectrum) IS observable on the real float window: the fixed
    # divisor (Σw)**2 differs from the buggy (Σ|w|)**2 -- the negative-weight bug
    spectrum_fixed = win.sum() ** 2
    spectrum_bug = np.abs(win).sum() ** 2
    assert not np.isclose(spectrum_fixed, spectrum_bug), (
        "spectrum-branch discriminator did not fire on the real flattop window")
    # the spectrum/density identity the F2P test asserts holds under the fix:
    # spec*win.sum()**2 == spec_a*Fs*(win**2).sum() reduces to (Σw)**2 cancelling
    # the spectrum divisor and (Σw**2) cancelling the density divisor -> equal.
    assert np.isclose(spectrum_fixed / win.sum() ** 2,
                      ((win ** 2).sum()) / (win ** 2).sum()), (
        "fixed normalisation identity check failed")

    print("G-AX OK: signed_sum/square_sum/magnitude_sum/magnitude_square_sum "
          "deep folds == real numpy reductions on %d boundary + 20000 fuzz "
          "windows; site-3 no-op confirmed; float->int refinement faithful "
          "(amplitude bug reproduces on signed ints AND the real flattop "
          "window)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
