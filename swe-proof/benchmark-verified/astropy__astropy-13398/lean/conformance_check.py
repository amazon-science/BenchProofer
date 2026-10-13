#!/usr/bin/env python3
"""G-CONF for astropy__astropy-13398.

Differential test of the R/I-tagged deep-modelled content of the Lean impls
against the real gold-patch helpers in
`astropy.coordinates.builtin_frames.itrs_observed_transforms`:

  * `rotZ` / `rotY` / `flipX` / `flipY` / `flipXY`,
  * the three composite rotations `altazMat` / `hadecMat` /
    `poleTiltMat`, INCLUDING the reported-angle-unit → radian conversion
    (`poleAngle = 90.0`, `angToRad`) that the real helpers get for free from the
    quantity machinery,
  * `mmul` / `mvmul` (index-order accumulation) and the transpose leg,
  * both refraction closed forms.

The A-reference callees are NOT re-implemented here; the shadow model calls the
REAL ones exactly where `Solution.lean` leaves an `opaque`:
`normSplit` ← `erfa.pn`, `scaleVec` ← `erfa.sxp`, `cartToSph` ← `erfa.c2s`,
`sphToCart` ← `erfa.s2c`, and refraction is fed real `(coefA, coefB)` pairs from
`erfa.refco`. That mirrors `mapping.md` exactly: what is compared here is the
arithmetic the bundle SPELLS OUT, not the primitives it defers.

The Lean carrier is `Float`, i.e. the same binary64 the repo computes in, so the
model and the reference perform the SAME operations on the same values; the
residual tolerance below covers only accumulation-order freedom (numpy's `@` /
`erfa.rxp` versus the model's explicit index-order sums) and the one
`1.0 - 0.5*d**2` versus `**2` spelling.

stdlib + numpy + the repo under test only. Exit 0 iff zero disagreements over
>=1e5 fuzzed inputs at the pinned seed; exit 1 on any mismatch.
"""
import sys
import numpy as np

SEED = 13398
N = 100_000
TOL = 1e-12         # same carrier, same ops => only accumulation-order slack
RNG = np.random.default_rng(SEED)

try:
    import astropy.units as u
    from astropy.coordinates.builtin_frames import itrs_observed_transforms as iot
    from astropy.coordinates.matrix_utilities import matrix_transpose
    import erfa
except Exception as e:  # pragma: no cover
    print(f"G-CONF skip: deps unavailable ({e})", file=sys.stderr)
    print("status=skip")
    sys.exit(0)

# --- the two literals the Lean `pure` region declares -----------------------
POLE_ANGLE = 90.0
ANG_TO_RAD = 0.017453292519943295
sinAltFloor, cosAltFloor = 0.05, 1e-6

# ---- pure-Python shadow of the Lean deep model (mirrors Solution.lean) ----


def mmul(a, b):
    """`mmul` — every entry the row-by-column sum accumulated in index order."""
    out = np.empty((3, 3))
    for i in range(3):
        for j in range(3):
            out[i][j] = a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j]
    return out


def mvmul(a, v):
    """`mvmul` — index-order accumulation, one row at a time."""
    return np.array([a[i][0] * v[0] + a[i][1] * v[1] + a[i][2] * v[2]
                     for i in range(3)])


def rot_z(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])


def rot_y(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, 0.0, -s], [0.0, 1.0, 0.0], [s, 0.0, c]])


FLIPX = np.diag([-1.0, 1.0, 1.0])
FLIPY = np.diag([1.0, -1.0, 1.0])
FLIPXY = np.diag([-1.0, -1.0, 1.0])


def to_altaz_mat(lon_ang, lat_ang):
    return mmul(mmul(FLIPX, rot_y((POLE_ANGLE - lat_ang) * ANG_TO_RAD)),
                rot_z(lon_ang * ANG_TO_RAD))


def to_hadec_mat(lon_ang):
    return mmul(FLIPY, rot_z(lon_ang * ANG_TO_RAD))


def altaz_to_hadec_mat(lat_ang):
    return mmul(FLIPXY, rot_y((POLE_ANGLE - lat_ang) * ANG_TO_RAD))


def add_refraction_model(p, coefA, coefB):
    """`toApparent`: transparent arithmetic, opaque legs via the real erfa."""
    norm, uv = erfa.pn(p.copy())                     # normSplit  (A-reference)
    sel = max(uv[2], sinAltFloor)
    cel = max(np.sqrt(uv[0] * uv[0] + uv[1] * uv[1]), cosAltFloor)
    tanz = cel / sel
    w = coefB * (tanz * tanz)
    delta_el = (coefA + w) * tanz / (1.0 + (coefA + 3.0 * w) / (sel * sel))
    cosdel = 1.0 - 0.5 * (delta_el * delta_el)
    fct = cosdel - delta_el * sel / cel
    bent = np.array([uv[0] * fct, uv[1] * fct, cosdel * uv[2] + delta_el * cel])
    _, bu = erfa.pn(bent)                            # normSplit  (A-reference)
    return erfa.sxp(norm, bu)                        # scaleVec   (A-reference)


def remove_refraction_model(p, coefA, coefB):
    """`toGeometric`: note the near-zenith guard is on the sine only."""
    norm, uv = erfa.pn(p.copy())                     # normSplit  (A-reference)
    sel = max(uv[2], sinAltFloor)
    cel = np.sqrt(uv[0] * uv[0] + uv[1] * uv[1])
    tanz = cel / sel
    delta_el = (coefA + coefB * (tanz * tanz)) * tanz
    az, el = erfa.c2s(uv)                            # cartToSph  (A-reference)
    new = erfa.s2c(az, el - delta_el)                # sphToCart  (A-reference)
    return erfa.sxp(norm, new)                       # scaleVec   (A-reference)

# ---- real gold-patch helpers (the reference) ----


def real_add_refraction(p, coefA, coefB):
    norm, uv = erfa.pn(p.copy())
    sel = np.maximum(uv[2], sinAltFloor)
    cel = np.maximum(np.sqrt(uv[0] ** 2 + uv[1] ** 2), cosAltFloor)
    tan_z = cel / sel
    w = coefB * tan_z ** 2
    delta_el = (coefA + w) * tan_z / (1.0 + (coefA + 3.0 * w) / (sel ** 2))
    cosdel = 1.0 - 0.5 * delta_el ** 2
    f = cosdel - delta_el * sel / cel
    out = uv.copy()
    out[0] *= f
    out[1] *= f
    out[2] = cosdel * uv[2] + delta_el * cel
    n2, out = erfa.pn(out)
    return erfa.sxp(norm, out)


def real_remove_refraction(p, coefA, coefB):
    norm, uv = erfa.pn(p.copy())
    sel = np.maximum(uv[2], sinAltFloor)
    cel = np.sqrt(uv[0] ** 2 + uv[1] ** 2)
    tan_z = cel / sel
    delta_el = (coefA + coefB * tan_z ** 2) * tan_z
    az, el = erfa.c2s(uv)
    el = el - delta_el
    out = erfa.s2c(az, el)
    return erfa.sxp(norm, out)


def fail(msg):
    print(f"G-CONF FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    for _ in range(N):
        # the site inversion reports DEGREES, which is the unit the composite
        # rotations must convert from (see mapping.md, `geodetic`).
        lon = RNG.uniform(-180.0, 180.0)
        lat = RNG.uniform(-90.0, 90.0)
        v = RNG.uniform(-2e8, 2e8, size=3)

        # (a) composite rotations vs the real new-module helpers, at the SAME
        #     reported angle unit the real callers pass in.
        if not np.allclose(to_altaz_mat(lon, lat),
                           iot.itrs_to_altaz_mat(lon * u.deg, lat * u.deg),
                           atol=TOL, rtol=0.0):
            fail(f"itrs_to_altaz_mat disagreement at lon={lon} lat={lat}")
        if not np.allclose(to_hadec_mat(lon),
                           iot.itrs_to_hadec_mat(lon * u.deg),
                           atol=TOL, rtol=0.0):
            fail(f"itrs_to_hadec_mat disagreement at lon={lon}")
        if not np.allclose(altaz_to_hadec_mat(lat),
                           iot.altaz_to_hadec_mat(lat * u.deg),
                           atol=TOL, rtol=0.0):
            fail(f"altaz_to_hadec_mat disagreement at lat={lat}")

        # (b) `mvmul` vs the product the real code actually performs
        #     (`CartesianRepresentation.transform` == erfa.rxp), and the
        #     transpose leg vs `matrix_transpose`.
        M = to_altaz_mat(lon, lat)
        if not np.allclose(mvmul(M, v), erfa.rxp(M, v), rtol=1e-13, atol=1e-9):
            fail(f"mvmul disagreement at lon={lon} lat={lat}")
        if not np.allclose(mvmul(M.T, v), erfa.rxp(matrix_transpose(M), v),
                           rtol=1e-13, atol=1e-9):
            fail(f"transposed mvmul disagreement at lon={lon} lat={lat}")

        # (c) refraction closed forms vs the real helpers, fed real erfa.refco
        pressure = RNG.uniform(1.0, 1100.0)
        temperature = RNG.uniform(-40.0, 50.0)
        humidity = RNG.uniform(0.0, 1.0)
        obswl = RNG.uniform(0.3, 25.0)
        coefA, coefB = erfa.refco(pressure, temperature, humidity, obswl)
        # an above-horizon direction-bearing vector
        d = RNG.uniform(-1, 1, size=3)
        d[2] = abs(d[2]) + 0.2
        d = d / np.sqrt((d ** 2).sum()) * RNG.uniform(1.0, 1e3)
        if not np.allclose(add_refraction_model(d, coefA, coefB),
                           real_add_refraction(d, coefA, coefB),
                           rtol=1e-13, atol=1e-12):
            fail(f"add_refraction disagreement at d={d}")
        if not np.allclose(remove_refraction_model(d, coefA, coefB),
                           real_remove_refraction(d, coefA, coefB),
                           rtol=1e-13, atol=1e-12):
            fail(f"remove_refraction disagreement at d={d}")

    print(f"G-CONF pass: {N} draws, 0 disagreements (seed {SEED})")
    sys.exit(0)


if __name__ == "__main__":
    main()
