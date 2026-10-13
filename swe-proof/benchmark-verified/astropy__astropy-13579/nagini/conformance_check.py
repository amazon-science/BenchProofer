#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-13579 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with contract
calls (Requires/Ensures/Invariant/Assert) stripped. Two modeled functions:
  * assemble_inverse_world — the loop that builds the full-length world
    vector, taking supplied[i] where kept[i] and world_at_slice[i] otherwise;
  * recovered_pixel — assemble, then one scalar component of the opaque
    full-vector function. That callee is @ContractOnly in the model, so here
    it calls the REAL repo function (the underlying full WCS inverse
    transform), per the conformance contract.

ORACLE: the REAL patched repo method the model models per mapping.md —
``SlicedLowLevelWCS.world_to_pixel_values``. The gate applies patch.diff to
/testbed before this script runs (do not apply it here). The exact output of
the modeled assembly loop is observed by monkeypatching the underlying
``self._wcs.world_to_pixel_values`` to CAPTURE the broadcast vector the
patched method hands it; that captured vector is the real loop's product,
exercising the real control flow (kept/dropped dispatch, the running
counter, axis order) rather than a re-derivation.

Type bridge (mapping.md section 2 / refinement.md R0-R1):
  * value carrier int -> float: the shadow is carrier-generic (it only
    selects and appends scalars), so it is run directly on the repo's float
    values; the selection behaviour under test is precision-independent.
  * kept: List[bool] <-> membership in the repo's kept-dimension index set:
    kept[iw] = (iw in world_keep).
  * supplied indexed by full world dimension <-> the repo's dense supplied
    tuple read via a running counter: supplied_full[world_keep[k]] =
    dense[k]; dropped slots of supplied_full carry a filler never read by
    the shadow (the model's contract pins only kept slots to supplied).
  * world_at_slice <-> the vector returned by the unchanged
    ``_pixel_to_world_values_all(*[0]*len(pixel_keep))``, read from the real
    object.

Input domain: the preconditions demand three equal-length lists (length
world_n_dim) and dim >= 0; every generated case satisfies them by
construction. Boundary cases cover all-zero, all-one, and the at-view vector
itself; fuzz draws supplied values uniformly per kept dimension over several
slice configurations (each dropping at least one world dimension so the
dropped-slot branch is always exercised).

>= 1e5 Requires-satisfying inputs: boundary + 100000 fuzz vector checks,
plus a sampled composition check of recovered_pixel through the real full
inverse transform. Pinned seed: 13579.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 13579
N_FUZZ = 100000
N_COMPOSE = 400  # per-config recovered_pixel composition samples


# --- impl region of model.py, verbatim, contract calls stripped --------------

def assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim):
    world_arrays_new = []
    iworld = 0
    while iworld < world_n_dim:
        if kept[iworld]:
            v = supplied[iworld]
        else:
            v = world_at_slice[iworld]
        world_arrays_new.append(v)
        iworld += 1
    return world_arrays_new


def recovered_pixel(kept, supplied, world_at_slice, world_n_dim, dim,
                    full_world_to_pixel):
    # full_world_to_pixel is @ContractOnly in the model: here it is the REAL
    # repo callee (passed in as a closure over the real full WCS).
    assembled = assemble_inverse_world(kept, supplied, world_at_slice,
                                       world_n_dim)
    res = full_world_to_pixel(assembled, dim)
    return res


# --- oracle: the real patched sliced WCS --------------------------------------

class _Captured(Exception):
    def __init__(self, vec):
        self.vec = vec


def make_sliced(header, slices):
    import astropy.wcs
    from astropy.wcs.wcsapi import SlicedLowLevelWCS
    fits_wcs = astropy.wcs.WCS(header=header)
    return SlicedLowLevelWCS(fits_wcs, slices)


def real_assembled_vector(sl, dense_supplied):
    """Run the REAL patched method, capturing the world vector it hands to
    the underlying full inverse (the modeled loop's exact product)."""
    orig = sl._wcs.world_to_pixel_values

    def capture(*vec):
        raise _Captured(vec)

    sl._wcs.world_to_pixel_values = capture
    try:
        sl.world_to_pixel_values(*dense_supplied)
    except _Captured as c:
        return [float(np.asarray(a).reshape(-1)[0]) for a in c.vec]
    finally:
        sl._wcs.world_to_pixel_values = orig
    raise RuntimeError("real method never called the underlying transform")


# Slice configurations over two 3-dim headers: one with coupled (non-diagonal)
# axes, one diagonal; each drops at least one world dimension.
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

CONFIGS = [
    (COUPLED_HEADER, 0),
    (COUPLED_HEADER, 1),
    (DIAG_HEADER, 0),
    (DIAG_HEADER, 1),
    (DIAG_HEADER, 5),
]


def build_config(header, sl_spec):
    sl = make_sliced(header, sl_spec)
    world_n_dim = int(sl._wcs.world_n_dim)
    world_keep = [int(i) for i in sl._world_keep]
    # kept: List[bool] bridge (membership -> per-dimension flag)
    kept = [iw in set(world_keep) for iw in range(world_n_dim)]
    # world_at_slice: the real unchanged callee's at-view coordinates
    world_at_slice = [float(v) for v in
                      sl._pixel_to_world_values_all(*[0] * len(sl._pixel_keep))]
    return sl, world_n_dim, world_keep, kept, world_at_slice


def lift_supplied(world_keep, world_n_dim, dense):
    """R1 bridge: dense supplied values (keep order) -> full-dim indexed list;
    dropped slots carry a filler the shadow never reads."""
    supplied = [0.0] * world_n_dim
    for k, iw in enumerate(world_keep):
        supplied[iw] = dense[k]
    return supplied


def check_vector(sl, kept, supplied, world_at_slice, world_n_dim, dense):
    """Compare the shadow-assembled vector against the real patched loop's
    captured product. Return error string on disagreement, else None."""
    shadow = assemble_inverse_world(kept, supplied, world_at_slice,
                                    world_n_dim)
    try:
        real = real_assembled_vector(sl, dense)
    except Exception as e:
        return ("DISAGREEMENT on dense supplied %r:\n  shadow vector = %r\n"
                "  real method raised %r" % (dense, shadow, e))
    if len(real) != len(shadow) or not np.allclose(
            real, shadow, rtol=1e-12, atol=1e-12):
        return ("DISAGREEMENT on dense supplied %r:\n  shadow vector = %r\n"
                "  real assembled vector = %r" % (dense, shadow, real))
    return None


def check_composition(sl, kept, supplied, world_at_slice, world_n_dim, dense):
    """recovered_pixel leg: shadow assembly composed with the REAL full
    inverse must match the real full inverse at the real assembled vector,
    per pixel component. Return error string on disagreement, else None."""
    full = sl._wcs

    def full_world_to_pixel(vec, dim):
        out = full.world_to_pixel_values(*np.broadcast_arrays(
            *[np.asanyarray(v) for v in vec]))
        return float(np.asarray(out[dim]).reshape(-1)[0])

    real_vec = real_assembled_vector(sl, dense)
    for dim in range(int(full.pixel_n_dim)):
        shadow_px = recovered_pixel(kept, supplied, world_at_slice,
                                    world_n_dim, dim, full_world_to_pixel)
        real_px = full_world_to_pixel(real_vec, dim)
        same = (shadow_px == real_px or
                (np.isnan(shadow_px) and np.isnan(real_px)) or
                np.allclose(shadow_px, real_px, rtol=1e-9, atol=1e-9))
        if not same:
            return ("DISAGREEMENT on dense supplied %r dim %d:\n"
                    "  shadow recovered_pixel = %r\n"
                    "  real (full inverse at real vector) = %r"
                    % (dense, dim, shadow_px, real_px))
    return None


def main():
    rng = random.Random(SEED)
    checked = 0

    built = []
    for header, sl_spec in CONFIGS:
        try:
            built.append(build_config(header, sl_spec))
        except Exception as e:
            print("skip config slice=%r: %r" % (sl_spec, e))
    if not built:
        print("status=fail no slice configuration could be built")
        return 1

    # boundary vectors per config
    for sl, world_n_dim, world_keep, kept, world_at_slice in built:
        n_keep = len(world_keep)
        boundary = [
            [0.0] * n_keep,
            [1.0] * n_keep,
            [-1.0] * n_keep,
            [world_at_slice[iw] for iw in world_keep],  # at-view supplied
            [1e6] * n_keep,
        ]
        for dense in boundary:
            supplied = lift_supplied(world_keep, world_n_dim, dense)
            err = check_vector(sl, kept, supplied, world_at_slice,
                               world_n_dim, dense)
            if err is None:
                err = check_composition(sl, kept, supplied, world_at_slice,
                                        world_n_dim, dense)
            if err:
                print(err)
                return 1
            checked += 1

    # fuzz: 100000 vector checks spread across configs, plus sampled
    # composition checks through the real full inverse
    per_cfg = N_FUZZ // len(built)
    for ci, (sl, world_n_dim, world_keep, kept, world_at_slice) in \
            enumerate(built):
        n_keep = len(world_keep)
        n_here = per_cfg if ci < len(built) - 1 else \
            N_FUZZ - per_cfg * (len(built) - 1)
        for j in range(n_here):
            dense = [rng.uniform(-1e3, 1e3) for _ in range(n_keep)]
            supplied = lift_supplied(world_keep, world_n_dim, dense)
            err = check_vector(sl, kept, supplied, world_at_slice,
                               world_n_dim, dense)
            if err is None and j < N_COMPOSE:
                err = check_composition(sl, kept, supplied, world_at_slice,
                                        world_n_dim, dense)
            if err:
                print(err)
                return 1
            checked += 1

    print("G-CONF OK: shadow impl == real patched assembly/recovery on "
          "%d inputs (seed %d); 0 disagreements." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
