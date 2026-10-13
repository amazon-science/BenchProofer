#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-13579.

Executes the REAL underlying callee (`self._wcs.world_to_pixel_values`, the
unchanged full WCS inverse transform) on inputs derived from the coupled WCS in
the issue, and asserts that every observation matches the axiom encoded in
model.py for `full_world_to_pixel`:

  (A-consumed) `full_world_to_pixel(world_vec, dim)` is a deterministic function
      of the whole assembled world vector. The proof consumes exactly this:
        * determinism / congruence: equal vectors -> equal results;
        * the round-trip identity that justifies the fix: when the DROPPED world
          slots carry the at-view world coordinate
          (`sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*...)`),
          the recovered kept pixel matches the full WCS's own pixel — whereas the
          pre-patch constant fill (`1.`) does NOT on a coupled axis.

This also re-runs the public reproducer (the FAIL_TO_PASS condition):
`np.allclose(sl.world_to_pixel_values(world[0], world[1])[0], 0)` post-fix.

Imports only `numpy` and the repo's own `astropy.wcs` (the very package the
patch lives in) — no Nagini, nothing model-specific. Exit 0 iff every
obligation holds.
"""
import sys

import numpy as np

import astropy.wcs
from astropy.wcs.wcsapi import SlicedLowLevelWCS


COUPLED_WCS_HEADER = {
    'WCSAXES': 3,
    'CRPIX1': (100 + 1) / 2,
    'CRPIX2': (25 + 1) / 2,
    'CRPIX3': 1.0,
    'PC1_1': 0.0,
    'PC1_2': -1.0,
    'PC1_3': 0.0,
    'PC2_1': 1.0,
    'PC2_2': 0.0,
    'PC2_3': -1.0,
    'CDELT1': 5,
    'CDELT2': 5,
    'CDELT3': 0.055,
    'CUNIT1': 'arcsec',
    'CUNIT2': 'arcsec',
    'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN',
    'CTYPE2': 'HPLT-TAN',
    'CTYPE3': 'WAVE',
    'CRVAL1': 0.0,
    'CRVAL2': 0.0,
    'CRVAL3': 1.05,
}


def assemble(world_keep, supplied_by_keep, world_at_slice, fill, world_n_dim):
    """Mirror model.py's assembly: kept slots take supplied values (in keep
    order), dropped slots take `fill(iworld)`."""
    vec = []
    icurr = -1
    keep = list(world_keep)
    for iworld in range(world_n_dim):
        if iworld in keep:
            icurr += 1
            vec.append(supplied_by_keep[icurr])
        else:
            vec.append(fill(iworld))
    return vec


def main():
    fits_wcs = astropy.wcs.WCS(header=COUPLED_WCS_HEADER)
    sl = SlicedLowLevelWCS(fits_wcs, 0)

    full = sl._wcs
    world_n_dim = full.world_n_dim
    world_keep = list(sl._world_keep)
    pixel_keep = list(sl._pixel_keep)

    # sliced_out_world_coords = the at-view world coordinate of every full dim
    # (this is exactly the value the patch introduces for the dropped slots).
    sliced_out_world_coords = sl._pixel_to_world_values_all(*[0] * len(pixel_keep))
    sliced_out_world_coords = [np.asanyarray(c) for c in sliced_out_world_coords]

    # The supplied kept world values for the reproducer: pixel_to_world at 0,0,0,
    # then take the kept world components (this is what the issue feeds in).
    world_full = fits_wcs.pixel_to_world_values(0, 0, 0)
    supplied_by_keep = [np.asanyarray(world_full[iw]) for iw in world_keep]

    # --- (1) determinism / congruence of the REAL full inverse ---------------
    vec_fix = assemble(world_keep, supplied_by_keep, sliced_out_world_coords,
                       lambda iw: sliced_out_world_coords[iw], world_n_dim)
    out_a = list(full.world_to_pixel_values(*np.broadcast_arrays(*vec_fix)))
    out_b = list(full.world_to_pixel_values(*np.broadcast_arrays(*vec_fix)))
    for da, db in zip(out_a, out_b):
        assert np.array_equal(np.asarray(da), np.asarray(db)), (
            "full_world_to_pixel not deterministic: %r vs %r" % (da, db))

    # equal vectors (independently constructed) give equal results
    vec_fix2 = [np.asanyarray(x) for x in vec_fix]
    out_c = list(full.world_to_pixel_values(*np.broadcast_arrays(*vec_fix2)))
    for da, dc in zip(out_a, out_c):
        assert np.allclose(np.asarray(da), np.asarray(dc)), (
            "full_world_to_pixel congruence violated: %r vs %r" % (da, dc))

    # --- (2) round-trip identity (the property the fix relies on) ------------
    # Feeding the at-view world coordinate into the dropped slot recovers the
    # correct kept pixel: pixel 0 in every kept pixel dimension for this slice.
    pix_fix = list(full.world_to_pixel_values(*np.broadcast_arrays(*vec_fix)))
    for ip in pixel_keep:
        # the supplied world came from pixel (0,0,0); kept pixels must return ~0
        assert np.allclose(np.asarray(pix_fix[ip]), 0, atol=1e-6), (
            "round-trip identity broken at kept pixel %d: got %r (expected ~0); "
            "the at-view fill must recover the slice pixel"
            % (ip, pix_fix[ip]))

    # --- (3) the bug: the constant fill `1.` does NOT round-trip -------------
    vec_bug = assemble(world_keep, supplied_by_keep, sliced_out_world_coords,
                       lambda iw: 1.0, world_n_dim)
    pix_bug = list(full.world_to_pixel_values(*np.broadcast_arrays(*vec_bug)))
    differs = any(
        not np.allclose(np.asarray(pix_bug[ip]), np.asarray(pix_fix[ip]),
                        atol=1e-6)
        for ip in pixel_keep)
    assert differs, (
        "expected the constant-`1.` fill to give a different (wrong) kept pixel "
        "than the at-view fill on this coupled WCS, but they matched — the "
        "discriminating coupling is absent")

    # --- (4) POST-FIX RESOLUTION CHECK (not an axiom-soundness obligation) ----
    # Steps (1)-(3) above are the axiom-soundness checks: they exercise only the
    # UNCHANGED callee `full.world_to_pixel_values` and hold at base_commit (the
    # axiom — determinism — and the executable round-trip evidence do not depend
    # on the patch). Step (4) is different: it is the public FAIL_TO_PASS
    # reproducer run end-to-end through `SlicedLowLevelWCS.world_to_pixel_values`,
    # so it passes only AFTER the gold patch (rc!=0 on base). It is included as a
    # resolution sanity check, not as evidence of axiom soundness.
    world = fits_wcs.pixel_to_world_values(0, 0, 0)
    out_pix = sl.world_to_pixel_values(world[0], world[1])
    assert np.allclose(out_pix[0], 0), (
        "FAIL_TO_PASS reproducer: sl.world_to_pixel_values(...)[0] = %r, "
        "expected ~0" % (out_pix[0],))

    print("G-AX OK: full_world_to_pixel axiom sound (deterministic + round-trip "
          "identity recovers the slice pixel); constant-`1.` fill is "
          "discriminating; FAIL_TO_PASS reproducer passes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
