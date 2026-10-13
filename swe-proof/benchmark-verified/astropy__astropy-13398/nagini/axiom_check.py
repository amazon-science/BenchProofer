#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-13398.

Validates the facts `model.py` consumes about the unchanged callees.

(1) Orientation-matrix orthogonality (the `orthogonality` axiom). The orthogonal
    orientation matrix `M(S)` — built from the geodetic coordinates of the
    observing site S — applied to a vector and then its TRANSPOSE applied to the
    result returns the original vector componentwise:

        bwd_x(fwd_x(v,S), fwd_y(v,S), fwd_z(v,S), S) == v_x   (and y, z),

    where `fwd_*` is `M(S) @ v` and `bwd_*` is `M(S)^T @ v`, AT ONE AND THE SAME
    site S. The matrices are the REAL ones the new code builds (ITRS->AltAz /
    ITRS->HADec), constructed here from the UNCHANGED callees `rotation_matrix`
    and `matrix_transpose`.

    The axiom claims this only WITHIN one site. A CONTROL confirms the site
    carrier is not decorative: applying the transpose built for a DIFFERENT site
    S' does NOT recover v, so nothing stronger than the single-site fact is true
    of the real callee and the axiom is exactly as weak as the model states it.
    (The site carrier is load-bearing because the gold code builds the matrix
    from the OBSERVER-CENTRED frame's own site at whichever end that frame sits:
    `observed_frame.location` in the forward direction and
    `observed_coo.location` in the backward one.)

(2) Earth-orientation-rotation orthogonality (the `prot_orthogonality` axiom).
    The same transpose-inverts-forward fact for the SECOND orthogonal rotation
    P(e), the Earth-equatorial <-> Earth-rotating matrix built by the UNCHANGED
    callees `cirs_to_itrs_mat` / `tete_to_itrs_mat` for the epoch e:

        prot_inv(prot(v, e), e) == v      -- at ONE AND THE SAME epoch e.

    The axiom claims this only WITHIN one epoch. A CONTROL confirms the epoch
    carrier is not decorative: applying the transpose for a DIFFERENT epoch e'
    does NOT recover v, so nothing stronger than the single-epoch fact is true of
    the real callee and the axiom is exactly as weak as the model states it.

(3) Same-anchoring re-referencing is a no-op (the `same_frame_noop` axiom).
    `offset_*(v, L, esrc, T, etgt)` is bound (mapping.md section 2) to the
    componentwise difference the REAL same-kind re-referencing transform
    introduces on the position v when the frame anchored at site L at epoch esrc
    is referred to the same-kind frame anchored at site T at epoch etgt:

        offset(v, L, esrc, T, etgt)
            = CIRS(v, obstime=esrc, location=L)
                .transform_to(CIRS(obstime=etgt, location=T)).cartesian - v.

    The axiom is the single instance where BOTH anchorings agree:

        offset_*(v, L, e, L, e) == 0.

    Two CONTROLS confirm that instance is the only one that holds, i.e. the site
    carrier and the epoch carrier are both observable rather than decorative:
    changing the target SITE alone, and changing the target EPOCH alone, each
    produce a detectably nonzero offset. So the axiom is the weakest fact the
    round-trip proof needs and cannot be over-read into the differing-anchoring
    domain the postconditions pin.

    The model uses that one offset family in BOTH conversion pairs, so the axiom
    and both controls are validated at BOTH instances mapping.md binds it to: the
    CIRS->CIRS re-referencing the Earth-equatorial pair performs, and the
    ITRS->ITRS re-referencing the direct Earth-fixed <-> observer-centred pair
    performs (`itrs_coo.transform_to(ITRS(obstime=observed_frame.obstime,
    location=observed_frame.location))` forward, and the closing
    `itrs_at_obs_time.transform_to(itrs_frame)` backward).

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
    action inverts the forward-action (the orthogonality axiom). The model's
    identity is EXACT in real arithmetic; the real matrices realise it up to
    floating-point error, so the check uses a relative tolerance (rtol) scaled
    to the vector magnitude — exactly what the F2P comparison tolerances do."""
    MT = matrix_transpose(M)
    # also confirm M is orthogonal directly: M^T M == I
    prod = MT @ M
    assert np.allclose(prod, np.eye(3), atol=1e-12), (
        "%s: M^T M != I (matrix not orthogonal): %r" % (label, prod))
    for v in vectors:
        v = np.asarray(v, dtype=float)
        fwd = M @ v                  # fwd_x/fwd_y/fwd_z   = M @ v
        back = MT @ fwd              # bwd_*(fwd_*(v))     = M^T (M v)
        scale = max(1.0, float(np.max(np.abs(v))))
        assert np.allclose(back, v, atol=1e-9 * scale, rtol=1e-12), (
            "%s: orthogonality axiom violated: M^T(M v) = %r, v = %r"
            % (label, back, v))


def check_cross_site_control():
    """CONTROL for (1): the SITE carrier on `fwd_*` / `bwd_*` / `orthogonality`
    is observable, so the axiom's single-site scope is exactly right and a
    site-free version (M^T built anywhere inverts M built anywhere) would be
    UNSOUND. Applying the transpose of the matrix built for a DIFFERENT site to
    the forward action of the matrix built for this one misses the input by a
    detectable margin.

    This is what makes a rival that builds the orientation matrix from the OTHER
    end of the conversion — the Earth-fixed frame's site instead of the
    observer-centred frame's own — unprovable rather than merely inelegant."""
    v = np.array([6378137.0, 1234567.0, -2345678.0])
    pairs = [((0.0, 0.0), (77.0, -12.0)),
             ((-1.0, 52.0), (123.0, -33.0)),
             ((10.0, 80.0), (-179.9, -89.0)),
             ((45.0, 23.5), (-70.7, -30.2))]
    controls = 0
    worst = None
    for (lon_a, lat_a), (lon_b, lat_b) in pairs:
        Ma = itrs_to_altaz_mat(lon_a * u.deg, lat_a * u.deg)
        Mb = itrs_to_altaz_mat(lon_b * u.deg, lat_b * u.deg)
        mixed = matrix_transpose(Mb) @ (Ma @ v)
        resid = float(np.max(np.abs(mixed - v)))
        assert resid > 1.0, (
            "ITRS->AltAz: cross-site composition (%g,%g)/(%g,%g) is "
            "indistinguishable from the identity (residual %g m): the site "
            "carrier would be decorative"
            % (lon_a, lat_a, lon_b, lat_b, resid))
        worst = resid if worst is None else min(worst, resid)
        controls += 1

        Ha = itrs_to_hadec_mat(lon_a * u.deg)
        Hb = itrs_to_hadec_mat(lon_b * u.deg)
        mixed = matrix_transpose(Hb) @ (Ha @ v)
        resid = float(np.max(np.abs(mixed - v)))
        assert resid > 1.0, (
            "ITRS->HADec: cross-site composition lon %g/%g is "
            "indistinguishable from the identity (residual %g m): the site "
            "carrier would be decorative" % (lon_a, lon_b, resid))
        worst = min(worst, resid)
        controls += 1
    return controls, worst


def check_prot_orthogonality(vectors):
    """Assert P(e)^T(P(e) v) == v for the REAL Earth-orientation matrices P(e)
    that the CIRS<->ITRS and TETE<->ITRS transforms build from the unchanged
    callees `cirs_to_itrs_mat` / `tete_to_itrs_mat`. This is the
    `prot_orthogonality` axiom, whose scope is ONE epoch.

    Also runs the epoch CONTROL: mixing epochs (P(e')^T applied to P(e) v with
    e' != e) does NOT recover v, so the model's epoch carrier on prot_* /
    prot_inv_* is observable and the axiom cannot be over-read across epochs."""
    from astropy.time import Time
    from astropy.coordinates.builtin_frames.intermediate_rotation_transforms import (
        cirs_to_itrs_mat, tete_to_itrs_mat)
    epochs = ["J2000", "J2006", "J2010", "B1950", "2022-06-24T15:22:11"]
    checks = 0
    for tname in epochs:
        t = Time(tname)
        for matfn, label in [(cirs_to_itrs_mat, "CIRS<->ITRS pmat"),
                             (tete_to_itrs_mat, "TETE<->ITRS pmat")]:
            M = matfn(t)
            check_orthogonal(M, vectors, "%s %s" % (label, tname))
            checks += 1

    # CONTROL: the epoch argument matters. P(e') != P(e) for e' != e, and the
    # cross-epoch composition is detectably not the identity, so the axiom's
    # single-epoch scope is exactly right (a quantified cross-epoch version
    # would be UNSOUND).
    controls = 0
    v = np.array([6378137.0, 1234567.0, -2345678.0])
    for matfn, label in [(cirs_to_itrs_mat, "CIRS<->ITRS pmat"),
                         (tete_to_itrs_mat, "TETE<->ITRS pmat")]:
        for a, b in zip(epochs, epochs[1:]):
            Pa = matfn(Time(a))
            Pb = matfn(Time(b))
            mixed = matrix_transpose(Pb) @ (Pa @ v)
            resid = float(np.max(np.abs(mixed - v)))
            assert resid > 1.0, (
                "%s: cross-epoch composition %s/%s is indistinguishable from "
                "the identity (residual %g m): the epoch carrier would be "
                "decorative" % (label, a, b, resid))
            controls += 1
    return checks, controls


def same_kind_offset(vec_m, loc_src, t_src, loc_tgt, t_tgt, cls=None):
    """The REAL re-referencing offset `offset_*` is bound to: the componentwise
    difference (in metres) that referring the position `vec_m` from the same-kind
    frame anchored at (site loc_src, epoch t_src) to the same-kind frame anchored
    at (site loc_tgt, epoch t_tgt) introduces. Driven through the public frame
    API so the registered transform function executes. `cls` selects which frame
    kind "the same kind" is: CIRS (the Earth-equatorial pair's instance) or ITRS
    (the direct Earth-fixed <-> observer-centred pair's instance)."""
    from astropy.coordinates import CIRS, CartesianRepresentation
    if cls is None:
        cls = CIRS
    rep = CartesianRepresentation(vec_m[0] * u.m, vec_m[1] * u.m,
                                  vec_m[2] * u.m)
    src = cls(rep, obstime=t_src, location=loc_src)
    tgt = src.transform_to(cls(obstime=t_tgt, location=loc_tgt))
    return (tgt.cartesian.get_xyz() - rep.get_xyz()).to_value(u.m)


def check_site_offset():
    """Validate the `same_frame_noop` axiom against the REAL gold-patched
    same-kind re-referencing transform: referring a position between two frames
    of IDENTICAL anchoring (same site, same epoch) introduces no offset, i.e.
    offset_*(v, L, e, L, e) == 0.

    Then run the two CONTROLS that show the axiom is the weakest such fact and
    that both new carriers are observable:
      * target SITE changed (same epoch)  -> offset detectably nonzero;
      * target EPOCH changed (same site)  -> offset detectably nonzero.
    Finally confirm the whole gold topocentric round trip (the behaviour the
    issue demands) is the identity, and that referring to the centre of the Earth
    instead of the frame's own site is detectably different.

    Imports only the repo package; uses the F2P-witness geometry."""
    from astropy.coordinates import EarthLocation, ICRS, CIRS, ITRS
    from astropy.coordinates.angle_utilities import golden_spiral_grid
    from astropy.time import Time

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

    # A second site and a second epoch, to vary each carrier ON ITS OWN.
    other_site = EarthLocation(lon=77.0 * u.deg, lat=-12.0 * u.deg,
                              height=1500.0 * u.m)
    epoch = Time("J2000")
    other_epoch = Time("J2006")

    checks = 0
    noop_worst = 0.0
    site_ctl_worst = None
    epoch_ctl_worst = None
    for lon, lat, height in sites:
        loc = EarthLocation(lon=lon * u.deg, lat=lat * u.deg, height=height * u.m)
        cirs_topo = icrs.transform_to(CIRS(obstime=epoch, location=loc))
        vec_m = cirs_topo.cartesian.get_xyz().to_value(u.m)

        # (a) THE AXIOM: identical anchoring on both sides => zero offset.
        noop = float(np.max(np.abs(
            same_kind_offset(vec_m, loc, epoch, loc, epoch))))
        assert noop <= 1e-3, (
            "same_frame_noop VIOLATED at lon=%g lat=%g h=%g: residual %g m"
            % (lon, lat, height, noop))
        noop_worst = max(noop_worst, noop)

        # (b) CONTROL - target SITE changed, epoch held: offset is NOT zero, so
        # the site carrier is observable and the axiom does not extend to it.
        site_ctl = float(np.max(np.abs(
            same_kind_offset(vec_m, loc, epoch, other_site, epoch))))
        assert site_ctl > 1.0, (
            "site carrier looks decorative at lon=%g lat=%g h=%g: changing the "
            "target site moved the position by only %g m"
            % (lon, lat, height, site_ctl))
        site_ctl_worst = site_ctl if site_ctl_worst is None \
            else min(site_ctl_worst, site_ctl)

        # (c) CONTROL - target EPOCH changed, site held: offset is NOT zero, so
        # the epoch carrier is observable too.
        epoch_ctl = float(np.max(np.abs(
            same_kind_offset(vec_m, loc, epoch, loc, other_epoch))))
        assert epoch_ctl > 1.0, (
            "epoch carrier looks decorative at lon=%g lat=%g h=%g: changing the "
            "target epoch moved the position by only %g m"
            % (lon, lat, height, epoch_ctl))
        epoch_ctl_worst = epoch_ctl if epoch_ctl_worst is None \
            else min(epoch_ctl_worst, epoch_ctl)

        # (d) The behaviour the issue demands: the topocentric round trip
        # CIRS@(L,e) -> ITRS@(L,e) -> CIRS@(L,e) is the identity.
        itrs_topo = cirs_topo.transform_to(ITRS(obstime=epoch, location=loc))
        itrs_again = itrs_topo.transform_to(ITRS(obstime=epoch, location=loc))
        rt_itrs = float(np.max(np.abs((itrs_again.x - itrs_topo.x).to_value(u.m))))
        assert rt_itrs <= 1e-3, (
            "same-anchoring ITRS re-reference not a no-op at lon=%g lat=%g "
            "h=%g: residual %g m" % (lon, lat, height, rt_itrs))

        # (d2) THE AXIOM AND BOTH CONTROLS AT THE OTHER INSTANCE. The direct
        # Earth-fixed <-> observer-centred pair re-references between two ITRS
        # frames, so `same_frame_noop` must hold — and must hold ONLY — there
        # too. Same three observations, on the ITRS instance.
        itrs_vec = itrs_topo.cartesian.get_xyz().to_value(u.m)
        i_noop = float(np.max(np.abs(
            same_kind_offset(itrs_vec, loc, epoch, loc, epoch, cls=ITRS))))
        assert i_noop <= 1e-3, (
            "same_frame_noop VIOLATED at the ITRS instance, lon=%g lat=%g h=%g: "
            "residual %g m" % (lon, lat, height, i_noop))
        noop_worst = max(noop_worst, i_noop)

        i_site = float(np.max(np.abs(
            same_kind_offset(itrs_vec, loc, epoch, other_site, epoch,
                             cls=ITRS))))
        assert i_site > 1.0, (
            "site carrier looks decorative at the ITRS instance, lon=%g lat=%g "
            "h=%g: changing the target site moved the position by only %g m"
            % (lon, lat, height, i_site))
        site_ctl_worst = min(site_ctl_worst, i_site)

        i_epoch = float(np.max(np.abs(
            same_kind_offset(itrs_vec, loc, epoch, loc, other_epoch,
                             cls=ITRS))))
        assert i_epoch > 1.0, (
            "epoch carrier looks decorative at the ITRS instance, lon=%g lat=%g "
            "h=%g: changing the target epoch moved the position by only %g m"
            % (lon, lat, height, i_epoch))
        epoch_ctl_worst = min(epoch_ctl_worst, i_epoch)
        cirs_back = itrs_topo.transform_to(CIRS(obstime=epoch, location=loc))
        rt = float(np.max(np.abs((cirs_back.cartesian.xyz
                                  - cirs_topo.cartesian.xyz).to_value())))
        assert rt <= 1e-9, (
            "topocentric round-trip not identity at lon=%g lat=%g h=%g: %g"
            % (lon, lat, height, rt))

        # (e) Referring to the centre of the Earth rather than the frame's own
        # site is a detectably different position whenever the site is off-centre
        # — so a conversion that used a constant site would be observably wrong.
        itrs_geo = cirs_topo.transform_to(ITRS(obstime=epoch))  # default centre
        forced = float(np.max(np.abs((itrs_topo.x - itrs_geo.x).to_value(u.m))))
        is_geocentre = (lon == 0.0 and lat == 0.0 and height == 0.0)
        if not is_geocentre:
            assert forced > 1.0, (
                "constant-centre offset not detectable at lon=%g lat=%g h=%g: "
                "%g m" % (lon, lat, height, forced))
        checks += 1
    return checks, noop_worst, site_ctl_worst, epoch_ctl_worst


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

    # --- CONTROL: the site carrier on fwd_*/bwd_* is observable ------------
    site_controls, site_ctl_worst = check_cross_site_control()

    # --- Earth-orientation-rotation orthogonality (prot_orthogonality) ----
    prot_checks, prot_controls = check_prot_orthogonality(vectors)

    # --- same-anchoring re-referencing no-op (same_frame_noop) ------------
    site_checks, noop_worst, site_ctl, epoch_ctl = check_site_offset()

    print("G-AX OK: orthogonality axiom (M(S)^T(M(S) v) == v at ONE site) sound "
          "for the real ITRS->AltAz / ITRS->HADec / AltAz->HADec orientation "
          "matrices over %d (lon,lat) configurations x %d vectors, with %d "
          "CROSS-SITE controls (worst >= %.3g m of residual) showing the site "
          "carrier is observable so a site-free axiom would be unsound; "
          "prot_orthogonality (P(e)^T(P(e) v) == v at one epoch) sound for the "
          "real CIRS<->ITRS / TETE<->ITRS matrices over %d configs, with %d "
          "cross-epoch controls showing the epoch carrier is observable; "
          "same_frame_noop (offset(v,L,e,L,e) == 0) validated against the real "
          "same-kind re-referencing transform over %d topocentric sites for "
          "BOTH instances the model uses it at (CIRS<->CIRS and ITRS<->ITRS; "
          "worst residual %.3g m), with the target-site control >= %.3g m and "
          "the target-epoch control >= %.3g m of offset on each, so no carrier "
          "is decorative and each axiom holds only where the model claims it"
          % (checks, len(vectors), site_controls, site_ctl_worst,
             prot_checks, prot_controls, site_checks,
             noop_worst, site_ctl, epoch_ctl))
    return 0


if __name__ == "__main__":
    sys.exit(main())
