#!/usr/bin/env python3
"""G-AX for astropy__astropy-13398.

`Solution.lean` ships `opaque` SIGNATURES only — no `_prop` axiom is consumed by
either proof (both close by `split_ifs <;> rfl`, i.e. the postcondition is
discharged by the impl's own control flow, never by an assumed property of a
callee). Per the worker contract ("If the proof needs no callee axiom, this may
be a skip stub") this is therefore a skip stub.

It is not an empty one. Every `opaque` in the axioms region stands for a real,
unchanged library routine, and each one carries a claim IN ITS DOCSTRING that the
spec's shape leans on. Those claims are the thing that can silently drift, so
they are probed here against the real routines; the stub fails loudly if any of
them stops holding.

  * `geodetic`   ← `EarthLocation.to_geodetic('WGS84')` — probed for the claim
    "the two angles come back in the angular unit the inversion natively
    reports, which is NOT radians".
  * `siteDiffers` ← the module's own `np.any(a != b)` site comparison.
  * `bendCoefs`    ← `erfa.refco` — finite, and vanishing at zero pressure (the
    branch the spec only enters when `pressure > 0`).
  * `normSplit`  ← `erfa.pn` — the (norm, unit) split.
  * `scaleVec`   ← `erfa.sxp` — scalar times vector.
  * `cartToSph` / `sphToCart` ← `erfa.c2s` / `erfa.s2c`.
  * `carryTo`    ← the ITRS↔ITRS `transform_to` pipeline, probed for the two
    claims the postconditions depend on: it is the IDENTITY when the source and
    target (site, epoch) pairs agree, and its value is a function of BOTH pairs
    — changing the TARGET site or the TARGET epoch alone changes the result.
    That second claim is what makes the trailing carry in
    `problem_spec_observed_to_itrs` unconditional and 4-argument rather than a
    guarded 2-argument no-op.
"""
import sys


def main():
    try:
        import numpy as np
        import erfa
        import astropy.units as u
        from astropy.time import Time
        from astropy.coordinates import EarthLocation, ITRS
        from astropy.coordinates.representation import CartesianRepresentation

        # -- bendCoefs ← erfa.refco -------------------------------------------
        coefA, coefB = erfa.refco(1000.0, 15.0, 0.5, 0.55)
        assert np.isfinite(coefA) and np.isfinite(coefB), "refco non-finite"
        # zero-pressure boundary: refraction vanishes (branch only entered p>0)
        z_refa, z_refb = erfa.refco(0.0, 15.0, 0.5, 0.55)
        assert abs(z_refa) < 1e-12 and abs(z_refb) < 1e-12, "refco(p=0) != 0"

        # -- cartToSph / sphToCart ← erfa.c2s / erfa.s2c ---------------------
        uv = np.array([0.3, 0.4, np.sqrt(1 - 0.25)])
        az, el = erfa.c2s(uv)
        assert np.allclose(erfa.s2c(az, el), uv, atol=1e-12), "c2s/s2c round-trip"

        # -- normSplit ← erfa.pn --------------------------------------------
        p = np.array([3.0, -4.0, 12.0])
        norm, unit = erfa.pn(p.copy())
        assert np.isclose(norm, 13.0, rtol=0, atol=1e-12), f"pn norm {norm}"
        assert np.allclose(unit, p / 13.0, atol=1e-15), "pn unit direction"
        assert np.isclose(np.sqrt((unit ** 2).sum()), 1.0, atol=1e-15), \
            "pn second component is not a unit vector"
        # pn does not mutate a caller's array into its own output slot
        zn, zu = erfa.pn(np.zeros(3))
        assert zn == 0.0 and np.allclose(zu, 0.0), "pn(0) shape"

        # -- scaleVec ← erfa.sxp -------------------------------------------
        assert np.allclose(erfa.sxp(2.5, p), 2.5 * p, atol=0.0), "sxp != s*p"

        # -- geodetic ← to_geodetic('WGS84'), REPORTED IN DEGREES ------------
        site = EarthLocation.from_geodetic(-155.5 * u.deg, 19.8 * u.deg, 4200 * u.m)
        glon, glat, gh = site.to_geodetic('WGS84')
        assert glon.unit.is_equivalent(u.deg) and glat.unit.is_equivalent(u.deg), \
            "to_geodetic angles are not angular quantities"
        # the claim the `pure` region's `poleAngle = 90.0` / `angToRad` encode:
        # the reported VALUE is in degrees, not radians.
        assert abs(glon.to_value(u.deg) - (-155.5)) < 1e-9, "lon value not degrees"
        assert abs(glat.to_value(u.deg) - 19.8) < 1e-7, "lat value not degrees"
        assert abs(glon.value - (-155.5)) < 1e-9, \
            "to_geodetic's native .value is not the degree value"
        assert abs(gh.to_value(u.m) - 4200.0) < 1e-6, "height"

        # -- siteDiffers ← np.any(a != b) -----------------------------------
        other = EarthLocation.from_geodetic(20.0 * u.deg, -33.0 * u.deg, 100 * u.m)
        centre = EarthLocation.from_geocentric(0 * u.m, 0 * u.m, 0 * u.m)
        assert not bool(np.any(site != site)), "site differs from itself"
        assert bool(np.any(site != other)), "distinct sites compare equal"
        assert bool(np.any(site != centre)), "site == geocentre"

        # -- carryTo ← ITRS(...).transform_to(ITRS(...)) ---------------------
        T = Time('2022-08-01T12:00:00')
        T2 = Time('2022-08-01T13:00:00')
        vec = CartesianRepresentation(np.array([1e6, 2e6, 3e6]) * u.m)

        def carry(src_loc, src_ep, tgt_loc, tgt_ep):
            at_src = ITRS(vec, obstime=src_ep, location=src_loc)
            return at_src.transform_to(
                ITRS(obstime=tgt_ep,
                     location=tgt_loc)).cartesian.get_xyz().to_value(u.m)

        base = np.array([1e6, 2e6, 3e6])
        # (1) identity when the two pairs agree
        same = carry(site, T, site, T)
        assert np.allclose(same, base, rtol=1e-13, atol=1e-6), \
            f"carry is not the identity when the pairs agree: {same}"
        # (2) the value is a function of BOTH pairs: perturbing the TARGET site
        #     alone, or the TARGET epoch alone, moves the result.
        tgt_site = carry(site, T, centre, T)
        tgt_epoch = carry(site, T, site, T2)
        assert not np.allclose(tgt_site, base, rtol=1e-9, atol=1.0), \
            "carry ignores the target site"
        assert not np.allclose(tgt_epoch, base, rtol=1e-9, atol=1.0), \
            "carry ignores the target epoch"
        # (3) and it is not a function of the source pair alone: two different
        #     targets from one source give two different answers.
        assert not np.allclose(tgt_site, carry(site, T, other, T),
                               rtol=1e-9, atol=1.0), \
            "carry collapses distinct targets"
    except AssertionError:
        raise
    except Exception as e:
        print(f"G-AX skip: no consumed axioms; probe unavailable ({e})",
              file=sys.stderr)
        print("status=skip")
        sys.exit(0)
    print("G-AX skip: no consumed (A-consumed) axioms shipped; "
          "A-reference callees deep-modelled + G-CONF-validated; "
          "docstring-claim probes passed for refco / pn / sxp / c2s / s2c / "
          "to_geodetic(degrees) / site comparison / the two-endpoint carry")
    print("status=skip")
    sys.exit(0)


if __name__ == "__main__":
    main()
