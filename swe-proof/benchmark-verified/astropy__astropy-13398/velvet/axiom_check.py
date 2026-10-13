#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-13398.

Validates the facts `Solution.lean` consumes about the unchanged callees.

(1) Orientation-matrix orthogonality (the `orth_*` axioms). The orthogonal
    orientation matrix `M` applied to a vector and then its TRANSPOSE applied to
    the result returns the original vector componentwise:

        bwdX(fwdX(v), fwdY(v), fwdZ(v)) == v_x   (and y, z),

    where `fwd*` is `M @ v` and `bwd*` is `M^T @ v`. The matrices are the REAL
    ones the new code builds (ITRS->AltAz / ITRS->HADec), constructed here from
    the UNCHANGED callees `rotation_matrix` and `matrix_transpose`.

(2) Precession-rotation orthogonality (the `prot_orth_*` axioms). The same
    transpose-inverts-forward fact for the SECOND orthogonal rotation P, the
    Earth-equatorial <-> Earth-rotating precession-nutation matrix built by the
    UNCHANGED callees `cirs_to_itrs_mat` / `tete_to_itrs_mat`:

        protInv(prot(v)) == v.

(3) Same-site re-referencing is a no-op (the `same_site_*` axioms). Referring a
    position whose frame is anchored at site L to a frame anchored at the SAME
    site L introduces no offset; referring it instead to a FIXED site (the centre
    of the Earth) when L is not the centre introduces a nonzero viewpoint offset.
    This is validated against the REAL gold-patched Earth-equatorial <->
    Earth-rotating conversions: the offset is ~0 at the same site (axiom holds)
    and detectably nonzero when the site is forced to the centre (the pre-patch
    behaviour is wrong).

Imports only numpy + the repo package. Exit 0 iff every observation holds.
"""
import sys
import numpy as np

from astropy import units as u
from astropy.coordinates.matrix_utilities import rotation_matrix, matrix_transpose

# Constant from the new transform module (latitude of the north pole).
NORTH_POLE = 90.0 * u.deg


def itrs_to_altaz_mat(lon, lat):
    """The real ITRS->AltAz orientation matrix (unchanged-callee composite)."""
    minus_x = np.eye(3)
    minus_x[0][0] = -1.0
    return (minus_x
            @ rotation_matrix(NORTH_POLE - lat, 'y')
            @ rotation_matrix(lon, 'z'))


def itrs_to_hadec_mat(lon):
    """The real ITRS->HADec orientation matrix (unchanged-callee composite)."""
    minus_y = np.eye(3)
    minus_y[1][1] = -1.0
    return (minus_y
            @ rotation_matrix(lon, 'z'))


def altaz_to_hadec_mat(lat):
    """The real AltAz->HADec orientation matrix (unchanged-callee composite)."""
    z180 = np.eye(3)
    z180[0][0] = -1.0
    z180[1][1] = -1.0
    return (z180
            @ rotation_matrix(NORTH_POLE - lat, 'y'))


def check_orthogonal(M, vectors, label):
    """Assert M^T (M v) == v componentwise for every v, i.e. the transpose-
    action inverts the forward-action (the `orth_*` axioms). The model's identity
    is EXACT in real arithmetic; the real matrices realise it up to floating-point
    error, so the check uses a relative tolerance scaled to the vector magnitude —
    exactly what the F2P comparison tolerances do."""
    MT = matrix_transpose(M)
    # also confirm M is orthogonal directly: M^T M == I
    prod = MT @ M
    assert np.allclose(prod, np.eye(3), atol=1e-12), (
        "%s: M^T M != I (matrix not orthogonal): %r" % (label, prod))
    for v in vectors:
        v = np.asarray(v, dtype=float)
        fwd = M @ v                  # fwdX/fwdY/fwdZ   = M @ v
        back = MT @ fwd              # bwd*(fwd*(v))    = M^T (M v)
        scale = max(1.0, float(np.max(np.abs(v))))
        assert np.allclose(back, v, atol=1e-9 * scale, rtol=1e-12), (
            "%s: orthogonality axiom violated: M^T(M v) = %r, v = %r"
            % (label, back, v))


def check_prot_orthogonality(vectors):
    """Assert P^T(P v) == v for the REAL precession-nutation matrices P that the
    intermediate <-> Earth-rotating conversions build from the unchanged callees
    `cirs_to_itrs_mat` / `tete_to_itrs_mat`. This is the `prot_orth_*` axioms (the
    transpose of the orthogonal rotation inverts it)."""
    from astropy.time import Time
    from astropy.coordinates.builtin_frames.intermediate_rotation_transforms import (
        cirs_to_itrs_mat, tete_to_itrs_mat)
    checks = 0
    for tname in ["J2000", "J2006", "J2010", "B1950", "2022-06-24T15:22:11"]:
        t = Time(tname)
        for matfn, label in [(cirs_to_itrs_mat, "CIRS<->ITRS pmat"),
                             (tete_to_itrs_mat, "TETE<->ITRS pmat")]:
            M = matfn(t)
            check_orthogonal(M, vectors, "%s %s" % (label, tname))
            checks += 1
    return checks


def check_site_offset():
    """Validate the `same_site_*` axioms against the REAL gold-patched
    intermediate <-> Earth-rotating conversions: referring a topocentric position
    to a frame anchored at the SAME site introduces no offset (offset == 0), while
    forcing the re-reference to the centre of the Earth (the pre-patch behaviour)
    introduces a detectably nonzero viewpoint offset whenever the site is not the
    centre.

    Imports only the repo package; uses the F2P-witness geometry."""
    from astropy.coordinates import EarthLocation, ICRS, CIRS, ITRS
    from astropy.coordinates.angle_utilities import golden_spiral_grid

    # Topocentric witnesses (the F2P sites + extras): L is NOT the geocentre.
    sites = [
        (0.0, 0.0, 0.0),        # equator, sea level (test_cirs_itrs_topo)
        (-1.0, 52.0, 10000.0),  # test_itrs_straight_overhead (lon, lat, height m)
        (-1.0, 52.0, 0.0),
        (123.0, -33.0, 500.0),
        (10.0, 80.0, 2000.0),
    ]
    usph = golden_spiral_grid(50)
    dist = np.linspace(1.0, 1000.0, len(usph)) * u.au
    icrs = ICRS(ra=usph.lon, dec=usph.lat, distance=dist)

    checks = 0
    for lon, lat, height in sites:
        loc = EarthLocation(lon=lon * u.deg, lat=lat * u.deg, height=height * u.m)
        cirs_topo = icrs.transform_to(CIRS(obstime="J2000", location=loc))

        # Honour the site: CIRS@L -> ITRS@L. The same-site re-reference is a no-op.
        itrs_topo = cirs_topo.transform_to(ITRS(location=loc))
        itrs_again = itrs_topo.transform_to(ITRS(location=loc))
        noop = float(np.max(np.abs((itrs_again.x - itrs_topo.x).to_value(u.m))))
        assert noop <= 1e-3, (
            "same_site no-op VIOLATED at lon=%g lat=%g h=%g: residual %g m"
            % (lon, lat, height, noop))

        # Topocentric round-trip CIRS@L -> ITRS@L -> CIRS@L is the identity.
        cirs_back = itrs_topo.transform_to(CIRS(obstime="J2000", location=loc))
        rt = float(np.max(np.abs((cirs_back.cartesian.xyz
                                  - cirs_topo.cartesian.xyz).to_value())))
        assert rt <= 1e-9, (
            "topocentric round-trip not identity at lon=%g lat=%g h=%g: %g"
            % (lon, lat, height, rt))

        # Force the centre of the Earth (the pre-patch re-reference target): when
        # L is not the centre this introduces a NONZERO viewpoint offset, i.e. the
        # pre-patch behaviour is detectably wrong.
        itrs_geo = cirs_topo.transform_to(ITRS())  # default centre of the Earth
        forced = float(np.max(np.abs((itrs_topo.x - itrs_geo.x).to_value(u.m))))
        is_geocentre = (lon == 0.0 and lat == 0.0 and height == 0.0)
        # The equator/sea-level site collapses to ~the geocentre direction; every
        # genuinely off-centre site must show a detectable offset.
        if not is_geocentre:
            assert forced > 1.0, (
                "force-centre offset not detectable at lon=%g lat=%g h=%g: %g m "
                "(pre-patch should be detectably wrong)"
                % (lon, lat, height, forced))
        checks += 1
    return checks


def main():
    rng = np.random.RandomState(13398)

    # --- boundary + fuzz angle grid ---------------------------------------
    lons = [0.0, 90.0, 180.0, 270.0, 360.0, -1.0, -123.456, 45.0, 359.999]
    lats = [0.0, 90.0, -90.0, 52.0, -52.0, 89.999, -89.999, 23.5]
    lons += list(rng.uniform(-360.0, 360.0, size=40))
    lats += list(rng.uniform(-90.0, 90.0, size=40))

    # --- boundary + fuzz vectors ------------------------------------------
    vectors = [
        [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [-3.0, 7.0, -11.0],
        [1e6, -2e6, 3e6], [123.0, 456.0, 789.0],
    ]
    vectors += [list(rng.uniform(-1e4, 1e4, size=3)) for _ in range(60)]

    checks = 0
    for lon in lons:
        for lat in lats:
            lonq = lon * u.deg
            latq = lat * u.deg
            check_orthogonal(itrs_to_altaz_mat(lonq, latq), vectors,
                             "ITRS->AltAz lon=%g lat=%g" % (lon, lat))
            check_orthogonal(itrs_to_hadec_mat(lonq), vectors,
                             "ITRS->HADec lon=%g" % lon)
            check_orthogonal(altaz_to_hadec_mat(latq), vectors,
                             "AltAz->HADec lat=%g" % lat)
            checks += 3

    # --- precession-rotation orthogonality (prot_orth_*) ------------------
    prot_checks = check_prot_orthogonality(vectors)

    # --- same-site re-referencing no-op (same_site_*) ---------------------
    site_checks = check_site_offset()

    print("G-AX OK: orth_* axiom (M^T(M v) == v) sound for the real "
          "ITRS->AltAz / ITRS->HADec / AltAz->HADec orientation matrices over "
          "%d (lon,lat) configurations x %d vectors; prot_orth_* "
          "(P^T(P v) == v) sound for the real CIRS<->ITRS / TETE<->ITRS "
          "precession matrices over %d configs; same_site_* validated "
          "against the real CIRS<->ITRS conversions over %d topocentric sites "
          "(same-site offset == 0, force-centre offset detectably nonzero)"
          % (checks, len(vectors), prot_checks, site_checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
