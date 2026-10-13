#!/usr/bin/env python
"""G-CONF: differential conformance for astropy__astropy-13579.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_assemble` skeleton (the loop that rebuilds the full-length world
vector `world_arrays_new` inside `SlicedLowLevelWCS.world_to_pixel_values`) and
diffs it against the REAL patched method over a discrete catalogue of slice
configurations plus >=1e5 randomized supplied-world vectors.

How the real loop is observed: we monkeypatch the underlying
`self._wcs.world_to_pixel_values` to CAPTURE the broadcasted `world_arrays_new`
the patched method hands it (and short-circuit before the expensive inverse
transform). That captured vector is the exact output of the edited reassembly
loop, so the comparison exercises the real patched control flow — kept/omitted
dispatch, the `iworld_curr` cursor, axis ordering — not a re-derivation.

A-reference bridge (mapping.md): the reference vector `slicedOut` is the real
`sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(pixel_keep))`,
read from the real object (the unchanged callee), so this is an A-reference test:
we validate that the loop POSITIONS the supplied values and the real reference
values correctly, not that we can re-derive the transform.

Exit 0 iff zero disagreements. stdlib + numpy only; pinned seed.
"""
import random
import sys

SEED = 20240629
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_assemble (post-patch R/I leg) ----------

def shadow_assemble(world_ndim, world_keep, inputs, sliced_out):
    """Transliteration of problem_spec_assemble / implementation_assemble:
    walk underlying world axes; kept axes take the next supplied value,
    omitted axes take their reference value `sliced_out[iworld]`."""
    world_keep = set(int(i) for i in world_keep)
    result = []
    iworld_curr = 0
    for iworld in range(world_ndim):
        if iworld in world_keep:
            result.append(inputs[iworld_curr])
            iworld_curr += 1
        else:
            result.append(sliced_out[iworld])
    return result


# ---- real callee observation ------------------------------------------------

class _Captured(Exception):
    def __init__(self, args):
        self.args_captured = args


def make_sliced(header, slices):
    """Build a real patched SlicedLowLevelWCS for a FITS header + slice spec."""
    import astropy.wcs
    from astropy.wcs.wcsapi import SlicedLowLevelWCS
    fits_wcs = astropy.wcs.WCS(header=header)
    return SlicedLowLevelWCS(fits_wcs, slices)


def real_world_arrays_new(sl, inputs):
    """Run the REAL patched `world_to_pixel_values` but capture the broadcasted
    `world_arrays_new` it passes to the underlying inverse transform, before the
    transform runs. Returns a flat list of floats."""
    import numpy as np
    orig = sl._wcs.world_to_pixel_values

    def capture(*world_arrays_new):
        raise _Captured(world_arrays_new)

    sl._wcs.world_to_pixel_values = capture
    try:
        sl.world_to_pixel_values(*inputs)
    except _Captured as c:
        return [float(np.asarray(a).reshape(-1)[0]) for a in c.args_captured]
    finally:
        sl._wcs.world_to_pixel_values = orig
    raise RuntimeError("real method did not call the underlying transform")


# The coupled header from the issue (drops a coupled world axis under slicing)
# plus diagonal variants exercising different dropped-axis positions.
COUPLED_HEADER = {
    'WCSAXES': 3,
    'CRPIX1': 50.5, 'CRPIX2': 13.0, 'CRPIX3': 1.0,
    'PC1_1': 0.0, 'PC1_2': -1.0, 'PC1_3': 0.0,
    'PC2_1': 1.0, 'PC2_2': 0.0, 'PC2_3': -1.0,
    'CDELT1': 5, 'CDELT2': 5, 'CDELT3': 0.055,
    'CUNIT1': 'arcsec', 'CUNIT2': 'arcsec', 'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN', 'CTYPE2': 'HPLT-TAN', 'CTYPE3': 'WAVE',
    'CRVAL1': 0.0, 'CRVAL2': 0.0, 'CRVAL3': 1.05,
}

DIAG_HEADER = {
    'WCSAXES': 3,
    'CRPIX1': 50.5, 'CRPIX2': 13.0, 'CRPIX3': 1.0,
    'CDELT1': 5, 'CDELT2': 5, 'CDELT3': 0.055,
    'CUNIT1': 'arcsec', 'CUNIT2': 'arcsec', 'CUNIT3': 'Angstrom',
    'CTYPE1': 'HPLN-TAN', 'CTYPE2': 'HPLT-TAN', 'CTYPE3': 'WAVE',
    'CRVAL1': 0.0, 'CRVAL2': 0.0, 'CRVAL3': 1.05,
}


def main():
    import numpy as np

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # Discrete catalogue: (header, slice spec). Each drops >=1 world axis so the
    # else-branch (omitted-axis fill) is exercised.
    configs = [
        (COUPLED_HEADER, 0),    # drop spectral axis (coupled) — the issue case
        (COUPLED_HEADER, 1),
        (DIAG_HEADER, 0),
        (DIAG_HEADER, 1),
        (DIAG_HEADER, 5),
    ]

    built = []
    for header, sl_spec in configs:
        try:
            sl = make_sliced(header, sl_spec)
        except Exception as e:  # pragma: no cover
            print(f"skip config slice={sl_spec}: {e}")
            continue
        world_ndim = int(sl._wcs.world_n_dim)
        world_keep = [int(i) for i in sl._world_keep]
        sliced_out = [float(v) for v in
                      sl._pixel_to_world_values_all(*[0] * len(sl._pixel_keep))]
        built.append((sl, world_ndim, world_keep, sliced_out))

    if not built:
        print("status=fail no slice configuration could be built")
        return 1

    per_cfg = max(1, N_RANDOM // len(built))
    for sl, world_ndim, world_keep, sliced_out in built:
        n_keep = len(world_keep)
        # discrete boundary inputs + random fuzz
        boundary = [
            [0.0] * n_keep,
            [1.0] * n_keep,
            [sliced_out[k] for k in world_keep],  # the slice's own reference
        ]
        for inputs in boundary:
            got = real_world_arrays_new(sl, inputs)
            exp = shadow_assemble(world_ndim, world_keep, inputs, sliced_out)
            checked += 1
            if not np.allclose(got, exp, rtol=1e-9, atol=1e-12):
                disagreements += 1
                if disagreements <= 5:
                    print(f"MISMATCH inputs={inputs}: real={got} shadow={exp}")
        for _ in range(per_cfg):
            inputs = [rng.uniform(-1e3, 1e3) for _ in range(n_keep)]
            got = real_world_arrays_new(sl, inputs)
            exp = shadow_assemble(world_ndim, world_keep, inputs, sliced_out)
            checked += 1
            if not np.allclose(got, exp, rtol=1e-9, atol=1e-12):
                disagreements += 1
                if disagreements <= 5:
                    print(f"MISMATCH inputs={inputs}: real={got} shadow={exp}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
