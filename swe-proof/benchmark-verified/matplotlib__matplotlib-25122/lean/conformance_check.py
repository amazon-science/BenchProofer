#!/usr/bin/env python3
"""G-CONF — differential test of the R shadow of implementation_windowCorrectionFactor
against the patch.diff behaviour (the post-patch window-correction divisor in
`mlab._spectral_helper`).

Runs INSIDE the instance image with the gold patch applied (PYTHONPATH=/testbed).

The impl region is all-R (no A-tagged op), so this is a real fuzz. Two legs:

  (1) PURE DIFFERENTIAL (>=1e5 draws): the Python shadow of
      `implementation_windowCorrectionFactor` (exact Fraction arithmetic, signed
      sums) vs an independent numpy reconstruction of the PATCHED divisor
      expressions from lib/matplotlib/mlab.py:
        magnitude / complex            -> window.sum()
        psd, scale_by_freq=True        -> (window**2).sum()
        psd, scale_by_freq=False       -> window.sum()**2
        angle / phase                  -> 1   (no window correction)
      over fuzzed windows (including NEGATIVE samples) x modes x flags.

  (2) END-TO-END tie to the REAL patched code: drives the installed
      `matplotlib.mlab.psd` on a window with negative samples and checks the
      Bendat-&-Piersol identity that holds iff the divisor is the SIGNED sum:
        psd(scale_by_freq=False) * window.sum()**2
          == psd(scale_by_freq=True) * Fs * (window**2).sum()
      (this is the relationship the F2P flattop test asserts). With the pre-patch
      |window|.sum() divisor this identity is violated for negative windows.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed); numpy is the
repo's own dependency, used only to evaluate the patched expressions / drive psd.
"""
import random
import sys
from fractions import Fraction as F

SEED = 25122          # pinned in mapping.md
N = 120_000           # >= 1e5

MODES = ["magnitude", "complex", "psd", "angle", "phase"]


def shadow(window, mode, scale_by_freq):
    """Exact-Fraction R shadow of implementation_windowCorrectionFactor."""
    if mode in ("magnitude", "complex"):
        s = F(0)
        for w in window:
            s += w
        return s
    if mode == "psd":
        if scale_by_freq:
            sq = F(0)
            for w in window:
                sq += w * w
            return sq
        else:
            s = F(0)
            for w in window:
                s += w
            return s * s
    # angle / phase
    return F(1)


def patched_factor(np, window_np, mode, scale_by_freq):
    """Independent reconstruction of the PATCHED divisor expressions
    (lib/matplotlib/mlab.py after the gold fix), evaluated with numpy exactly as
    the patched source lines write them."""
    if mode in ("magnitude", "complex"):
        return window_np.sum()
    if mode == "psd":
        if scale_by_freq:
            return (window_np ** 2).sum()
        else:
            return window_np.sum() ** 2
    return 1.0


def rand_window(rng):
    """Window with small integer/rational samples, deliberately allowing
    negatives (the bug's discriminator)."""
    n = rng.randint(1, 8)
    return [F(rng.randint(-6, 6), rng.randint(1, 4)) for _ in range(n)]


def pure_differential(np):
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # deterministic boundary cases (incl. all-negative, mixed-sign, zero-sum)
    fixed = [
        ([F(-1), F(2), F(-3)], "magnitude", False),
        ([F(-1), F(2), F(-3)], "complex", False),
        ([F(-1), F(2), F(-3)], "psd", False),
        ([F(-1), F(2), F(-3)], "psd", True),
        ([F(-1), F(2), F(-3)], "angle", False),
        ([F(-1), F(2), F(-3)], "phase", True),
        ([F(2), F(-2)], "psd", False),     # signed sum 0 -> factor 0
        ([F(-1)], "magnitude", False),
        ([F(0)], "psd", True),
    ]

    cases = list(fixed)
    for _ in range(N):
        w = rand_window(rng)
        mode = rng.choice(MODES)
        sbf = rng.random() < 0.5
        cases.append((w, mode, sbf))

    for w, mode, sbf in cases:
        got = shadow(w, mode, sbf)
        # evaluate the patched expression exactly: feed exact rationals as a
        # python-object numpy array so .sum()/**2 stay exact, then compare as
        # Fractions.
        wnp = np.array([F(x) for x in w], dtype=object)
        want = patched_factor(np, wnp, mode, sbf)
        want = F(want) if not isinstance(want, F) else want
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((w, mode, sbf), got, want))

    return disagreements, examples


def end_to_end(np):
    """Drive the REAL patched mlab.psd and confirm the signed-sum divisor via the
    Bendat-&-Piersol identity (the relationship the F2P flattop test checks)."""
    import matplotlib.mlab as mlab

    rng = np.random.RandomState(SEED)
    NFFT = 256
    y = rng.randn(2 * NFFT)
    Fs = 4.0

    failures = []
    # a few windows with negative samples (flattop-like) where |w|.sum != w.sum
    fac = np.linspace(-np.pi, np.pi, NFFT)
    a = [0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368]
    flattop = np.zeros(NFFT)
    for k in range(len(a)):
        flattop += a[k] * np.cos(k * fac)

    windows = [flattop, np.cos(fac), 1.0 - 0.6 * np.cos(2 * fac)]
    for win in windows:
        # ensure the discriminator is live: signed sum differs from abs sum
        if abs(np.abs(win).sum() - win.sum()) < 1e-9:
            continue
        spec, _ = mlab.psd(x=y, NFFT=NFFT, Fs=Fs, noverlap=0,
                           window=win, scale_by_freq=False)
        spec_a, _ = mlab.psd(x=y, NFFT=NFFT, Fs=Fs, noverlap=0,
                             window=win, scale_by_freq=True)
        lhs = spec * win.sum() ** 2
        rhs = spec_a * Fs * (win ** 2).sum()
        if not np.allclose(lhs, rhs, atol=1e-8):
            failures.append(float(np.max(np.abs(lhs - rhs))))
    return failures


def main() -> int:
    import numpy as np

    disagreements, examples = pure_differential(np)
    if disagreements:
        print(f"G-CONF FAIL: {disagreements} pure-differential disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    e2e = end_to_end(np)
    if e2e:
        print(f"G-CONF FAIL: end-to-end identity violated, max abs err={e2e}")
        return 1

    print(f"G-CONF OK: {N}+ pure draws, 0 disagreements; end-to-end identity "
          f"holds (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
