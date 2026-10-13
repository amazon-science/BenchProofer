#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-13579 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`scatter` /
              `scatterStep`, the per-axis scatter that fills present axes from
              the supplied values in order and absent axes with their own
              reference coordinate) transliterated to Python over the real repo
              types, via the mapping.md bijection (`List Float` ↔ the
              `world_arrays_new` list; `a.1` ↔ `iworld in _world_keep`; `a.2`
              ↔ `sliced_out_world_coords[iworld]`). There are NO A-tagged ops to
              leave alone (no axioms in this bundle); the two callees touched are
              UNCHANGED and supply read-only inputs (mapping.md §3).
  * ORACLE  — patch.diff's behaviour: the REAL patched
              `SlicedLowLevelWCS.world_to_pixel_values` (gold patch applied at
              base_commit by the harness, G-RESOLVE). We instantiate the wrapper
              via `__new__` and stub its read-only callees
              (`_pixel_to_world_values_all` → the reference coordinates;
              `self._wcs.world_to_pixel_values` → a capturing sink) so we observe
              exactly the assembled `world_arrays_new` vector — the data the
              patch changes — and compare it against the shadow's `scatter`.

They must agree on every input the real assembly could produce. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), astropy + numpy
(stdlib `random`). The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

SEED = 13579
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean scatter/scatterStep, transliterated --------
def shadow_scatter(axes, supplied):
    """`scatter axes supplied` = (axes.foldl scatterStep ([], supplied)).1.

    Present axes (a.1 == True) consume the next supplied value in order; absent
    axes (a.1 == False) emit their own reference coordinate (a.2)."""
    out = []
    remaining = list(supplied)
    for present, ref in axes:
        if present:
            out.append(remaining[0] if remaining else 0.0)
            remaining = remaining[1:]
        else:
            out.append(ref)
    return out


# --- the oracle: the REAL patched world_to_pixel_values assembly --------------
def oracle_assembled(axes, supplied):
    """Drive the real patched SlicedLowLevelWCS.world_to_pixel_values and capture
    the assembled `world_arrays_new` it builds (mapping.md §1).

    We bypass __init__ (which needs a real WCS) via __new__ and set only the
    attributes the assembly loop reads. `_pixel_to_world_values_all` is stubbed
    to return the per-axis reference coordinates (a.2 for every axis); the
    downstream `self._wcs.world_to_pixel_values` is a capturing sink. Both are
    UNCHANGED callees (mapping.md §3) — here they only inject the read-only
    inputs and observe the assembled vector."""
    import numpy as np
    from astropy.wcs.wcsapi.wrappers.sliced_wcs import SlicedLowLevelWCS

    world_n_dim = len(axes)
    world_keep = [i for i, (present, _ref) in enumerate(axes) if present]
    ref_coords = [float(ref) for (_present, ref) in axes]

    captured = {}

    class _FakeWCS:
        pass

    fake = _FakeWCS()
    fake.world_n_dim = world_n_dim
    fake.pixel_n_dim = 1  # arbitrary; only used by the post-loop pixel leg

    def _capture_world_to_pixel(*world_arrays_new):
        captured["vec"] = [np.asanyarray(w) for w in world_arrays_new]
        # return one pixel per pixel dim (downstream of the modeled assembly)
        return tuple(np.asarray(0.0) for _ in range(fake.pixel_n_dim))

    fake.world_to_pixel_values = _capture_world_to_pixel

    sl = SlicedLowLevelWCS.__new__(SlicedLowLevelWCS)
    sl._wcs = fake
    sl._world_keep = np.array(world_keep, dtype=int)
    # _pixel_keep: only its length matters ([0]*len(self._pixel_keep)); make it
    # length 1 (we stub _pixel_to_world_values_all anyway).
    sl._pixel_keep = np.array([0], dtype=int)
    # _slices_pixel: the post-loop pixel adjustment reads .start; slice(None)
    # has start None ⇒ no adjustment, no crash.
    sl._slices_pixel = [slice(None)] * fake.pixel_n_dim
    sl._pixel_to_world_values_all = lambda *a: tuple(ref_coords)

    sl.world_to_pixel_values(*supplied)
    return [float(np.asanyarray(v)) for v in captured["vec"]]


# --- fuzzing: axis masks, reference coords, supplied values -------------------
def _gen_case(rng):
    """One fuzzed scenario: (axes, supplied).

    axes is a list of (present: bool, ref: float). At least one present axis and
    at least one absent axis are forced in most cases so the discriminating
    fill (absent → ref, NOT a constant) is exercised; supplied has exactly one
    value per present axis (the require precondition)."""
    n = rng.randint(1, 6)
    mask = [rng.random() < 0.55 for _ in range(n)]
    # ensure at least one present and (often) at least one absent axis
    if not any(mask):
        mask[rng.randrange(n)] = True
    if rng.random() < 0.8 and all(mask) and n > 1:
        mask[rng.randrange(n)] = False
    refs = []
    for _ in range(n):
        # include 1.0 (the legacy placeholder) plus other values so the
        # difference between the fix and the bug is visible
        r = rng.choice([1.0, 0.0, -1.0, 2.44e-15, 1.05, 49.5, 12.0,
                        rng.uniform(-1e3, 1e3)])
        refs.append(float(r))
    axes = list(zip(mask, refs))
    n_present = sum(mask)
    supplied = [float(rng.uniform(-1e3, 1e3)) for _ in range(n_present)]
    return axes, supplied


def _boundary_cases():
    """Deterministic boundary scenarios (plan §4.1 step 4)."""
    cases = []
    # the issue's 3D→2D wavelength slice: axes 0,1 kept (spatial), axis 2 dropped
    # (wavelength) with a non-1 reference coordinate (the bug's symptom).
    cases.append(([(True, 0.0), (True, 0.0), (False, 1.05)], [0.0, 0.0]))
    # single present axis only
    cases.append(([(True, 7.0)], [3.0]))
    # single absent axis among present ones, ref == 1.0 (bug & fix agree here)
    cases.append(([(True, 0.0), (False, 1.0)], [5.0]))
    # absent axis with ref far from 1.0 (bug & fix disagree on the oracle side;
    # shadow must match the FIXED oracle)
    cases.append(([(False, 2.44e-15), (True, 0.0)], [9.0]))
    # all present
    cases.append(([(True, 0.0), (True, 0.0), (True, 0.0)], [1.0, 2.0, 3.0]))
    # multiple absent axes interleaved
    cases.append(([(False, -3.0), (True, 0.0), (False, 4.0), (True, 0.0)],
                  [1.0, 2.0]))
    return cases


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def check(axes, supplied):
        nonlocal count
        count += 1
        shadow = shadow_scatter(axes, supplied)
        oracle = oracle_assembled(axes, supplied)
        ok = (len(shadow) == len(oracle)
              and all(_close(a, b) for a, b in zip(shadow, oracle)))
        if not ok:
            disagreements.append((axes, supplied, shadow, oracle))

    for case in _boundary_cases():
        check(*case)

    for _ in range(N_FUZZ):
        if len(disagreements) >= 5:
            break
        check(*_gen_case(rng))

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for axes, supplied, sh, orc in disagreements:
            print("  axes=%r supplied=%r shadow=%r oracle=%r"
                  % (axes, supplied, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of assembleWorldVector (scatter/scatterStep) "
          "agrees with the real patched world_to_pixel_values assembled vector "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


def _close(a, b, tol=1e-12):
    if a == b:
        return True
    return abs(a - b) <= tol + tol * max(abs(a), abs(b))


if __name__ == "__main__":
    sys.exit(main())
