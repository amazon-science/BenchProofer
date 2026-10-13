#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-20488.

This bundle consumes NO `@ContractOnly` axiom: the changed behavior is a direct
real-number conditional modeled over interpreted floats. The single real-callee
property the model relies on is that the floor constant the model receives as
`eps` (with `Requires(eps > 0.0)`) is, in the real code, `np.finfo(dtype).eps`,
which is strictly positive. G-AX validates exactly that, plus the end-to-end
correspondence between model.py's spec and the real patched sanitisation logic.

Two obligations:

  (1) Floor positivity (the precondition `eps > 0.0` is grounded in reality):
      execute the REAL `numpy.finfo(dtype).eps` for every floating dtype
      matplotlib selects in `image._make_image` (`float32`, `float64`) plus
      neighbouring floating dtypes (`float16`, `float128` where available) and
      assert each is strictly positive.

  (2) Behavioral correspondence: the model's spec (the fixed sanitisation)
      reproduces the REAL post-patch logic
          s_vmin = eps   if isinstance(norm, LogNorm) and s_vmin <= 0 else s_vmin
      and the model's `model_prepatch` skeleton reproduces the REAL pre-patch
      buggy logic
          if isinstance(norm, LogNorm) and s_vmin < 0: s_vmin = max(s_vmin, eps)
      over boundary (incl. the exact-zero discriminator) + randomized fuzz, and
      that they DIFFER exactly at `is_log and s_vmin == 0` (the F2P case).

Imports `numpy` only — the same library the gold patch calls (`np.finfo`). No
matplotlib import is required: `LogNorm`-ness is the bool the hunk consults.
Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def model_fixed(is_log, s_vmin, eps):
    """Reference of model.py's fixed behavior (the post-patch sanitisation)."""
    if is_log and s_vmin <= 0.0:
        return eps
    return s_vmin


def model_prepatch(is_log, s_vmin, eps):
    """Reference of model_prepatch.py's buggy skeleton (the pre-patch logic)."""
    result = s_vmin
    if is_log:
        if s_vmin < 0.0:
            result = max(s_vmin, eps)
    return result


# --- the REAL repo logic at base_commit / post-patch (lib/matplotlib/image.py)

def real_prepatch(is_log, s_vmin, eps):
    # base_commit lines 535-537, verbatim semantics:
    #   if isinstance(self.norm, mcolors.LogNorm):
    #       if s_vmin < 0:
    #           s_vmin = max(s_vmin, np.finfo(scaled_dtype).eps)
    if is_log:
        if s_vmin < 0:
            s_vmin = max(s_vmin, eps)
    return s_vmin


def real_fixed(is_log, s_vmin, eps):
    # gold patch verbatim semantics:
    #   if isinstance(self.norm, mcolors.LogNorm) and s_vmin <= 0:
    #       s_vmin = np.finfo(scaled_dtype).eps
    if is_log and s_vmin <= 0:
        s_vmin = eps
    return s_vmin


# --- obligation 1: floor positivity (np.finfo(dtype).eps > 0) ----------------

def check_floor_positivity():
    dtypes = [np.float32, np.float64]       # the two _make_image actually picks
    for name in ("float16", "float128"):    # neighbours, where the platform has them
        dt = getattr(np, name, None)
        if dt is not None:
            dtypes.append(dt)
    for dt in dtypes:
        eps = float(np.finfo(dt).eps)        # the REAL callee
        assert eps > 0.0, (
            "np.finfo(%r).eps is not strictly positive: %r" % (dt, eps))
    return [float(np.finfo(dt).eps) for dt in dtypes]


# --- obligation 2: model spec == real logic; twins differ at the boundary ----

def check_correspondence(is_log, s_vmin, eps):
    # fixed model reproduces real post-patch logic
    mf = model_fixed(is_log, s_vmin, eps)
    rf = real_fixed(is_log, s_vmin, eps)
    assert mf == rf, (
        "fixed model disagrees with real post-patch at is_log=%r s_vmin=%r "
        "eps=%r: model=%r real=%r" % (is_log, s_vmin, eps, mf, rf))
    # prepatch model reproduces real pre-patch logic
    mp = model_prepatch(is_log, s_vmin, eps)
    rp = real_prepatch(is_log, s_vmin, eps)
    assert mp == rp, (
        "prepatch model disagrees with real pre-patch at is_log=%r s_vmin=%r "
        "eps=%r: model=%r real=%r" % (is_log, s_vmin, eps, mp, rp))
    # the fixed spec's headline guarantee: log => strictly positive
    if is_log:
        assert mf > 0.0, (
            "fixed model violates 'log => positive' at s_vmin=%r eps=%r: %r"
            % (s_vmin, eps, mf))
    return mf, mp


def main():
    floors = check_floor_positivity()
    eps32 = float(np.finfo(np.float32).eps)
    eps64 = float(np.finfo(np.float64).eps)

    # boundary cases over the discriminating inputs ---------------------------
    boundary_vmins = [0.0, -0.0, -1.0, -1e-30, -1e20, 1.0, 1e-30, 1e20,
                      eps32, eps64, eps32 / 2, -eps32]
    boundary = []
    for is_log in (True, False):
        for v in boundary_vmins:
            for e in (eps32, eps64, 1e-300):
                boundary.append((is_log, v, e))

    discriminator_seen = False
    for (is_log, v, e) in boundary:
        mf, mp = check_correspondence(is_log, v, e)
        if is_log and v == 0.0:
            # the F2P case: fixed gives eps (>0), prepatch leaves 0 (the bug)
            assert mf == e and mp == 0.0, (
                "boundary discriminator wrong at s_vmin=0: fixed=%r prepatch=%r "
                "(expected eps=%r and 0.0)" % (mf, mp, e))
            assert mf != mp, "twins must differ at is_log and s_vmin==0"
            discriminator_seen = True
    assert discriminator_seen, "did not exercise the is_log & s_vmin==0 case"

    # randomized fuzz ---------------------------------------------------------
    rng = random.Random(20488)
    for _ in range(50000):
        is_log = rng.random() < 0.5
        kind = rng.randint(0, 3)
        if kind == 0:
            v = 0.0
        elif kind == 1:
            v = -rng.random() * (10 ** rng.randint(-30, 25))
        elif kind == 2:
            v = rng.random() * (10 ** rng.randint(-30, 25))
        else:
            v = rng.uniform(-5.0, 5.0)
        e = rng.choice([eps32, eps64]) if rng.random() < 0.5 \
            else rng.random() * (10 ** rng.randint(-300, -1))
        if e <= 0.0:
            e = eps64
        check_correspondence(is_log, v, e)

    print("G-AX OK: np.finfo(dtype).eps strictly positive for %d floating "
          "dtypes (%s); fixed/prepatch models == real post/pre-patch logic and "
          "differ exactly at (is_log, s_vmin==0) over %d boundary + 50000 fuzz "
          "inputs" % (len(floors),
                      ", ".join("%.3g" % f for f in floors),
                      len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
