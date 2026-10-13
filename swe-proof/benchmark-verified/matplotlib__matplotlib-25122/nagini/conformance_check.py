#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-25122 (nagini).

SHADOW: the impl regions of model.py's ``amplitude_loss_divisor`` and
``power_loss_divisor``, copied VERBATIM below with only the contract calls
(Requires / Ensures / Invariant / Assert / MustTerminate) stripped. The @Pure
helpers (``signed_sum`` / ``magnitude`` / ``magnitude_sum`` / ``square_sum`` /
``magnitude_square_sum`` / ``squares_are_sign_blind``) copy over on a small
immutable-tuple PSeq shim and serve as an internal cross-check of the
executable shadow (including the sign-blindness lemma the power divisor's
postcondition states). There is NO @ContractOnly callee in this bundle
(mapping.md section 3: the reductions are modelled deeply, A-reference).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — ``matplotlib.mlab._spectral_helper``. The gate applies patch.diff
to /testbed before this script runs and sets PYTHONPATH=/testbed, so the
import resolves to the patched module. The two contracted divisors are the
window-normalisation divisors of that helper's output; they are observed
through an impulse-response readout:

  feed x = a unit impulse at index j (with window[j] != 0) through ONE
  NFFT=len(window) segment (no overlap, no detrend, onesided, Fs=1, pad_to
  =NFFT). The DC bin of the windowed segment's transform is then exactly
  window[j], so the helper's DC output is

    mode='magnitude'                 : |window[j]|   / D_amp        (site 1)
    mode='complex'                   :  window[j]    / D_amp        (site 2)
    mode='psd', scale_by_freq=True   :  window[j]**2 / D_pow        (site 3)
    mode='psd', scale_by_freq=False  :  window[j]**2 / D_amp**2     (site 4)

  (the onesided scaling factor never touches the DC bin), from which the real
  divisor is recovered by division. The recovered value is rounded to the
  nearest integer and compared EXACTLY against the shadow divisor, guarded by
  a tight relative tolerance (~1e-9; observed FFT rounding is ~1e-12
  relative for the magnitudes generated here). A zero shadow divisor is
  checked as a non-finite real output (division by zero), which a disagreeing
  nonzero real divisor would render finite.

Type bridge (mapping.md section 2, refinement.md R1): the model carrier is
``List[int]`` of window weights; the repo window is a 1-D real ndarray. An
int-valued float array is an EXACT lift (integers of this size are exactly
representable in binary floating point), so the bridge is the documented
weights-list <-> window-array bijection with no precision loss on the input
side.

Input domain: the preconditions demand only a readable list of weights, so
every ``List[int]`` qualifies. Generation stresses sign handling: exhaustive
{+1,-1} sign patterns up to length 10, exhaustive small-value windows,
tapered windows with negative lobes, windows whose signed total is zero
(divide-by-zero locus), all-zero windows, and randomized fuzz over several
value pools with sign-mixed windows over-weighted. The empty window is
covered on the shadow/pure side only (the helper requires NFFT >= 1, so no
oracle point exists for it).

>= 1e5 Requires-satisfying inputs: enumerated boundary + exhaustive sweeps +
100000 fuzz windows, each checked at all four divisor sites. Pinned fuzz
seed: 25122 (the instance number; recorded in mapping.md).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo's own numpy/matplotlib only.
"""
import json
import math
import os
import random
import sys

os.environ.setdefault("MPLBACKEND", "Agg")

SEED = 25122
N_FUZZ = 100000
REL_TOL = 1e-9


# --- PSeq shim: immutable sequence with the operations the pure region uses ---

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, contracts stripped -------------------------------

def signed_sum(w):
    """The signed (algebraic) running total of the window weights."""
    if len(w) == 0:
        return 0
    return w[0] + signed_sum(w.drop(1))


def magnitude(x):
    """The magnitude of a single weight (its sign discarded)."""
    if x < 0:
        return -x
    return x


def magnitude_sum(w):
    """The running total of the weight MAGNITUDES."""
    if len(w) == 0:
        return 0
    return magnitude(w[0]) + magnitude_sum(w.drop(1))


def square_sum(w):
    """The running total of the SQUARES of the window weights."""
    if len(w) == 0:
        return 0
    return w[0] * w[0] + square_sum(w.drop(1))


def magnitude_square_sum(w):
    """The running total of the squares of the weight MAGNITUDES."""
    if len(w) == 0:
        return 0
    return magnitude(w[0]) * magnitude(w[0]) + magnitude_square_sum(w.drop(1))


def squares_are_sign_blind(w):
    """Lemma: the squared-weight total reads the same signed or by magnitude."""
    if len(w) == 0:
        return True
    return squares_are_sign_blind(w.drop(1))


# --- impl regions of model.py, verbatim, contract calls stripped ---------------

def amplitude_loss_divisor(window):
    total = 0
    i = len(window)
    while i > 0:
        weight = window[i - 1]
        total = weight + total
        i = i - 1
    return total


def power_loss_divisor(window):
    total = 0
    i = len(window)
    while i > 0:
        weight = window[i - 1]
        total = weight * weight + total
        i = i - 1
    return total


# --- oracle: the real patched repo function ------------------------------------

def load_oracle():
    import numpy as np
    from matplotlib import mlab
    return np, mlab


def probe(np, mlab, w, j, mode, scale_by_freq):
    """One impulse-response readout of the real helper's DC bin: the window
    lifted exactly to a float ndarray, a unit impulse at index j, one
    NFFT=len(w) segment, Fs=1, no overlap/detrend/padding, onesided."""
    n = len(w)
    win = np.asarray(w, dtype=float)
    x = np.zeros(n)
    x[j] = 1.0
    with np.errstate(all="ignore"):
        res, _freqs, _t = mlab._spectral_helper(
            x, NFFT=n, Fs=1, detrend_func=mlab.detrend_none, window=win,
            noverlap=0, pad_to=n, sides="onesided", mode=mode,
            scale_by_freq=scale_by_freq)
    return complex(res[0, 0])


# --- differential driver --------------------------------------------------------

def _finite(c):
    return math.isfinite(c.real) and math.isfinite(c.imag)


def _recover_matches(numerator, denom_reading, expect_int):
    """recover divisor = numerator / denom_reading; require it to sit within
    REL_TOL of the exact integer the shadow computed."""
    if denom_reading == 0.0:
        return False
    rec = numerator / denom_reading
    return abs(rec - expect_int) <= REL_TOL * max(1.0, abs(float(expect_int)))


def check_window(np, mlab, w, rng):
    """Run shadow and oracle on one window; return an error string on
    disagreement, else None."""
    a_shadow = amplitude_loss_divisor(list(w))
    p_shadow = power_loss_divisor(list(w))

    # internal cross-checks: executable impl regions vs the pure folds, and
    # the sign-blindness lemma the power postcondition states
    s = ToSeq(w)
    if a_shadow != signed_sum(s):
        return "INTERNAL: amplitude impl region and signed fold disagree on %r" % (w,)
    if p_shadow != square_sum(s):
        return "INTERNAL: power impl region and squared fold disagree on %r" % (w,)
    if not squares_are_sign_blind(s) or p_shadow != magnitude_square_sum(s):
        return "INTERNAL: sign-blindness lemma broken on %r" % (w,)

    if len(w) == 0:
        return None  # no oracle point: the helper needs NFFT >= 1

    nz = [k for k in range(len(w)) if w[k] != 0]
    j = rng.choice(nz) if nz else 0

    def fail(site, mode, r, expect_desc):
        return ("DISAGREEMENT on window %r (impulse at j=%d, w[j]=%d), "
                "site %s (mode=%s):\n"
                "  shadow divisors: amplitude=%d power=%d (expected %s)\n"
                "  real (patched _spectral_helper) DC output = %r"
                % (w, j, w[j], site, mode, a_shadow, p_shadow, expect_desc, r))

    # site 1: mode='magnitude' — DC output = |w[j]| / amplitude divisor
    r = probe(np, mlab, w, j, "magnitude", None)
    if a_shadow == 0:
        if _finite(r):
            return fail("1", "magnitude", r, "non-finite (divisor 0)")
    else:
        if not _finite(r) or not _recover_matches(abs(w[j]), r.real, a_shadow):
            return fail("1", "magnitude", r, "|w[j]|/%d" % a_shadow)

    # site 2: mode='complex' — DC output = w[j] / amplitude divisor
    r = probe(np, mlab, w, j, "complex", None)
    if a_shadow == 0:
        if _finite(r):
            return fail("2", "complex", r, "non-finite (divisor 0)")
    else:
        if (not _finite(r)
                or abs(r.imag) > REL_TOL * max(1.0, abs(r.real))
                or not _recover_matches(w[j], r.real, a_shadow)):
            return fail("2", "complex", r, "w[j]/%d" % a_shadow)

    # site 3: mode='psd', density scaling — DC output = w[j]^2 / power divisor
    r = probe(np, mlab, w, j, "psd", True)
    if p_shadow == 0:
        if _finite(r):
            return fail("3", "psd/density", r, "non-finite (divisor 0)")
    else:
        if not _finite(r) or not _recover_matches(w[j] * w[j], r.real, p_shadow):
            return fail("3", "psd/density", r, "w[j]^2/%d" % p_shadow)

    # site 4: mode='psd', spectrum scaling — DC output = w[j]^2 / (amp divisor)^2
    r = probe(np, mlab, w, j, "psd", False)
    if a_shadow == 0:
        if _finite(r):
            return fail("4", "psd/spectrum", r, "non-finite (divisor 0)")
    else:
        if not _finite(r) or not _recover_matches(w[j] * w[j], r.real,
                                                  a_shadow * a_shadow):
            return fail("4", "psd/spectrum", r, "w[j]^2/%d" % (a_shadow * a_shadow))

    return None


def boundary_cases():
    cases = [
        [],                       # shadow/pure side only
        [0], [0, 0, 0], [0, 0, 1, 0, 0],
        [1], [-1], [7], [-7], [99], [-99],
        [1, 1], [1, -1], [-1, 1], [-1, -1],
        [1, -1, 1, -1], [2, -2, 3, -3, 1, -1],      # signed total zero
        [0, 5, 0, -5, 0],                            # zero total with zeros
        [1] * 8, [-1] * 8,
        list(range(1, 9)),
        [(-1) ** k * (k + 1) for k in range(8)],
        [-5, 2, -4],                                 # negative signed total
        [99, -99], [99] * 16 + [-1] * 3,
        # tapered window shapes whose end lobes dip below zero
        [-1, -1, 2, 21, 50, 71, 71, 50, 21, 2, -1, -1],
        [-4, 1, 30, 62, 30, 1, -4],
        [1] * 255, [1] * 256,
        [(-1) ** k for k in range(256)],
    ]
    # exhaustive sign patterns over {+1,-1} up to length 10
    for n in range(1, 11):
        for bits in range(1 << n):
            cases.append([1 if (bits >> k) & 1 else -1 for k in range(n)])
    # exhaustive small windows over {-2..2} up to length 3
    vals = [-2, -1, 0, 1, 2]
    for a in vals:
        cases.append([a])
        for b in vals:
            cases.append([a, b])
            for c in vals:
                cases.append([a, b, c])
    return cases


def fuzz_window(rng, pools):
    r = rng.random()
    if r < 0.85:
        n = rng.randint(1, 32)
    elif r < 0.97:
        n = rng.randint(33, 96)
    else:
        n = rng.randint(97, 128)
    pool = rng.choice(pools)
    w = [rng.choice(pool) for _ in range(n)]
    x = rng.random()
    if x < 0.12:
        # force a zero signed total: append the negated weights, shuffled
        w = w + [-v for v in w]
        rng.shuffle(w)
    elif x < 0.16:
        w = [0] * n
    return w


def main():
    np, mlab = load_oracle()
    rng = random.Random(SEED)

    checked = 0
    boundary = boundary_cases()
    for w in boundary:
        err = check_window(np, mlab, w, rng)
        if err:
            print(err)
            return 1
        checked += 1

    pools = [
        (-1, 0, 1),
        (-3, -2, -1, 0, 1, 2, 3),
        tuple(range(-9, 10)),
        tuple(range(-99, 100)),
        (0, 1, 2, 3, 5, 8),          # non-negative pool (agreeing regime)
        (-9, -5, -1, 1, 5, 9),       # no zeros, sign-mixed
    ]
    for _ in range(N_FUZZ):
        w = fuzz_window(rng, pools)
        err = check_window(np, mlab, w, rng)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow divisors == real patched _spectral_helper "
          "normalisation on %d windows x 4 sites (%d boundary/sweep + %d "
          "fuzz, seed %d); pure-fold cross-checks and the sign-blindness "
          "lemma hold; 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
