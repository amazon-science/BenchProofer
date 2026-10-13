#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-13398 (nagini).

SHADOW  — the impl region of model.py, copied VERBATIM below with the
          contract calls (Requires/Ensures/Assert) stripped. The model IS
          Python, so no transliteration. The lemma invocations that remain in
          the impl bodies (`orthogonality`, `prot_orthogonality`,
          `same_frame_noop`) are ghost proof steps; here they are executable
          no-op stubs. The `pure`-region helpers `rebased_x/y/z` are copied
          verbatim too. Every value-producing @ContractOnly callee (`fwd_*`,
          `bwd_*`, `prot_*`, `prot_inv_*`, `offset_*`) calls the REAL repo
          machinery:
            fwd_* / bwd_*       -> the real orientation matrix M(S) built by the
                                   repo's own matrix builders FOR THE SITE the
                                   call names (and its transpose) applied to the
                                   vector, exactly the `crepr.transform(M)` /
                                   `crepr.transform(matrix_transpose(M))`
                                   actions mapping.md binds them to. The site
                                   carrier indexes a registry of real geodetic
                                   sites, so the shadow honours the site
                                   argument rather than a single fixed matrix;
            prot_* / prot_inv_* -> the real Earth-orientation matrix FOR THE
                                   EPOCH the call names (and its transpose):
                                   the epoch carrier indexes a registry of real
                                   obstimes, so the shadow honours the epoch
                                   argument rather than a single fixed matrix;
            offset_*            -> the real same-kind re-referencing transform,
                                   evaluated on the position and BOTH anchorings
                                   the call names -- source (site, epoch) and
                                   target (site, epoch) -- as the componentwise
                                   difference that transform introduces. Which
                                   frame kind is "the same kind" is set by the
                                   conversion the offset occurs in (mapping.md
                                   3.3: ITRS->ITRS for the direct
                                   Earth-fixed <-> observer-centred pair,
                                   CIRS->CIRS for the Earth-equatorial <->
                                   Earth-rotating pair), and the harness binds
                                   it accordingly before each check.

BRIDGE  — mapping.md section 2: the model carries each Cartesian component
          as an exact integer because the modeled behaviour is the exact
          algebraic identity that the comparison tolerances absorb; the real
          code realises it in floats. The shadow therefore runs on the real
          float components, and shadow/oracle agreement is judged with a
          relative tolerance scaled to the vector magnitude — the same
          tolerance discipline the repo test suite applies. `comp` is a pure
          component selector, ranged over {0, 1, 2} for every vector. The site
          carrier (lx, ly, lz) is the site's geocentric position in metres; the
          epoch carrier is an integer tag denoting an obstime (only tag equality
          is modelled, and the shadow resolves each tag to the real Time).

ORACLE  — the REAL patched repo transforms (PYTHONPATH=/testbed, gold patch
          applied by the gate before this script runs), driven through the
          public frame API so the registered transform functions execute:
          ITRS <-> AltAz / HADec (direct pair, no refraction: pressure 0) and
          CIRS <-> ITRS. BOTH pairs are driven between frames whose anchorings
          are taken from the configuration -- including anchorings that DIFFER
          in site only, in epoch only, and in both -- plus both round-trip
          compositions. All positions are batched arrays, so one `transform_to`
          call exercises the real function on the whole batch.

Input domain: every modeled precondition is `comp in {0,1,2}`; positions,
sites and epochs are otherwise free. Sites cover boundary geodetic
configurations plus fuzzed ones; vectors cover axis/zero/large boundary cases
plus fuzz; the source/target anchoring pairs cover all four
same/differing-site x same/differing-epoch combinations, for BOTH conversion
pairs.

>= 1e5 Requires-satisfying inputs: 15 (site, obstime) configurations x
(2 observed-frame kinds x (4 anchoring variants x 2 direct-pair triplet checks
+ 1 round-trip triplet check) + 4 anchoring variants x 2 equ<->rot triplet
checks + 1 round-trip triplet check) x 3 components x 300 vectors
= 15 x 27 x 3 x 300 = 364500.
Pinned seed: 13398.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + the repo package only.
"""
import sys

import numpy as np

SEED = 13398
N_FUZZ_VECTORS = 292          # per configuration, plus 8 boundary vectors

# ---------------------------------------------------------------------------
# Bindings for the axiomatized callees. Set by run_config() before the shadow
# executes; each binding IS the real repo machinery.
# ---------------------------------------------------------------------------

_MREG = {}         # site key -> (M(S), M(S)^T) real orientation matrices
_PMAT = {}         # epoch tag -> (P(e), P(e)^T) real Earth-orientation matrices
_EPOCH = {}        # epoch tag -> real astropy Time
_LOC = {}          # site key -> real astropy EarthLocation
_KIND = "cirs"     # which same-kind frame the re-referencing offset is bound to
_OFF_CACHE = {}    # memo for the real re-referencing transform


def _skey(sx, sy, sz):
    """The site carrier is a geocentric metre triple; round it to a stable key
    so the registry lookup is exact for the values the harness passes in."""
    return (round(float(sx), 3), round(float(sy), 3), round(float(sz), 3))


def fwd_x(x, y, z, sx, sy, sz):
    M = _MREG[_skey(sx, sy, sz)][0]
    return M[0, 0] * x + M[0, 1] * y + M[0, 2] * z


def fwd_y(x, y, z, sx, sy, sz):
    M = _MREG[_skey(sx, sy, sz)][0]
    return M[1, 0] * x + M[1, 1] * y + M[1, 2] * z


def fwd_z(x, y, z, sx, sy, sz):
    M = _MREG[_skey(sx, sy, sz)][0]
    return M[2, 0] * x + M[2, 1] * y + M[2, 2] * z


def bwd_x(x, y, z, sx, sy, sz):
    MT = _MREG[_skey(sx, sy, sz)][1]
    return MT[0, 0] * x + MT[0, 1] * y + MT[0, 2] * z


def bwd_y(x, y, z, sx, sy, sz):
    MT = _MREG[_skey(sx, sy, sz)][1]
    return MT[1, 0] * x + MT[1, 1] * y + MT[1, 2] * z


def bwd_z(x, y, z, sx, sy, sz):
    MT = _MREG[_skey(sx, sy, sz)][1]
    return MT[2, 0] * x + MT[2, 1] * y + MT[2, 2] * z


def prot_x(x, y, z, e):
    P = _PMAT[e][0]
    return P[0, 0] * x + P[0, 1] * y + P[0, 2] * z


def prot_y(x, y, z, e):
    P = _PMAT[e][0]
    return P[1, 0] * x + P[1, 1] * y + P[1, 2] * z


def prot_z(x, y, z, e):
    P = _PMAT[e][0]
    return P[2, 0] * x + P[2, 1] * y + P[2, 2] * z


def prot_inv_x(x, y, z, e):
    PT = _PMAT[e][1]
    return PT[0, 0] * x + PT[0, 1] * y + PT[0, 2] * z


def prot_inv_y(x, y, z, e):
    PT = _PMAT[e][1]
    return PT[1, 0] * x + PT[1, 1] * y + PT[1, 2] * z


def prot_inv_z(x, y, z, e):
    PT = _PMAT[e][1]
    return PT[2, 0] * x + PT[2, 1] * y + PT[2, 2] * z


def _rereference(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    """The REAL same-kind re-referencing transform: hold the position
    (vx, vy, vz) in a frame anchored at (site L, epoch esrc) and refer it to the
    same-kind frame anchored at (site T, epoch etgt); return the componentwise
    difference it introduces, in metres. This is exactly what mapping.md binds
    `offset_*` to; `_KIND` selects which frame kind "the same kind" is for the
    conversion under test (ITRS<->ITRS for the direct pair, exactly the
    `itrs_coo.transform_to(ITRS(obstime=..., location=...))` the gold forward
    performs; CIRS<->CIRS for the Earth-equatorial pair). Memoized per (kind,
    batch, source anchoring, target anchoring) so the three component calls
    share one real transform."""
    from astropy import units as u
    from astropy.coordinates import CIRS, ITRS, CartesianRepresentation
    key = (_KIND, hash(np.asarray(vx).tobytes()), hash(np.asarray(vy).tobytes()),
           hash(np.asarray(vz).tobytes()),
           _skey(lx, ly, lz), esrc, _skey(tx, ty, tz), etgt)
    hit = _OFF_CACHE.get(key)
    if hit is not None:
        return hit
    src_loc = _LOC[_skey(lx, ly, lz)]
    tgt_loc = _LOC[_skey(tx, ty, tz)]
    rep = CartesianRepresentation(np.asarray(vx) * u.m, np.asarray(vy) * u.m,
                                  np.asarray(vz) * u.m)
    cls = ITRS if _KIND == "itrs" else CIRS
    src = cls(rep, obstime=_EPOCH[esrc], location=src_loc)
    tgt = src.transform_to(cls(obstime=_EPOCH[etgt], location=tgt_loc))
    diff = (tgt.cartesian.get_xyz() - rep.get_xyz()).to_value(u.m)
    out = (diff[0], diff[1], diff[2])
    _OFF_CACHE[key] = out
    return out


def offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    return _rereference(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)[0]


def offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    return _rereference(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)[1]


def offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    return _rereference(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)[2]


def orthogonality(x, y, z, sx, sy, sz):
    return None    # ghost lemma (proof step), no runtime content


def prot_orthogonality(x, y, z, e):
    return None    # ghost lemma (proof step), no runtime content


def same_frame_noop(vx, vy, vz, lx, ly, lz, e):
    return None    # ghost lemma (proof step), no runtime content


# ---------------------------------------------------------------------------
# model.py `pure` region, VERBATIM.
# ---------------------------------------------------------------------------


def rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    return vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)


def rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    return vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)


def rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    return vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)


# ---------------------------------------------------------------------------
# model.py impl regions, VERBATIM with contract statement lines
# (Requires/Ensures/Assert) stripped.
# ---------------------------------------------------------------------------


def itrs_to_observed(comp, vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
    # etgt), then rotate the re-referred position with the orientation matrix
    # built from that same output frame's own site T.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return fwd_x(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    return fwd_z(wx, wy, wz, tx, ty, tz)


def observed_to_itrs(comp, ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    # Rotate with the transpose of the orientation matrix built from the INPUT
    # frame's own site L, then refer the rotated position from the input frame's
    # own anchoring to the output frame's anchoring.
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)


def observed_roundtrip(comp, vx, vy, vz, lx, ly, lz, e):
    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
    # them introduces no offset and the re-referred position is the position
    # itself.
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    # The observer-centred components are the orientation matrix for the shared
    # site applied to that re-referred position (each equals the corresponding
    # forward-conversion output by that conversion's postcondition).
    ox = fwd_x(qx, qy, qz, lx, ly, lz)
    oy = fwd_y(qx, qy, qz, lx, ly, lz)
    oz = fwd_z(qx, qy, qz, lx, ly, lz)
    r0 = itrs_to_observed(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r1 = itrs_to_observed(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r2 = itrs_to_observed(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    # RETURN LEG. The transpose-action for that same site undoes the
    # forward-action, recovering the re-referred position and hence the input.
    orthogonality(qx, qy, qz, lx, ly, lz)
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    # The return leg refers between the same anchoring as well, so it introduces
    # no offset either.
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    return observed_to_itrs(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)


def equ_to_rot(comp, vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
    # etgt), then rotate the re-referred position with the Earth-orientation
    # rotation for that same epoch etgt.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return prot_x(wx, wy, wz, etgt)
    if comp == 1:
        return prot_y(wx, wy, wz, etgt)
    return prot_z(wx, wy, wz, etgt)


def rot_to_equ(comp, ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt):
    # Rotate with the transpose of the Earth-orientation rotation for the INPUT
    # frame's epoch esrc, then refer the rotated position from the input frame's
    # own anchoring to the output frame's anchoring.
    wx = prot_inv_x(ox, oy, oz, esrc)
    wy = prot_inv_y(ox, oy, oz, esrc)
    wz = prot_inv_z(ox, oy, oz, esrc)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)


def equ_rot_roundtrip(comp, vx, vy, vz, lx, ly, lz, e):
    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
    # them introduces no offset and the re-referred position is the position
    # itself.
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    # The Earth-rotating components are the rotation, at the shared epoch, of
    # that re-referred position (each equals the corresponding forward-conversion
    # output by that conversion's postcondition).
    ox = prot_x(qx, qy, qz, e)
    oy = prot_y(qx, qy, qz, e)
    oz = prot_z(qx, qy, qz, e)
    # RETURN LEG. The inverse rotation at that same epoch undoes the forward
    # rotation, recovering the re-referred position and hence the input.
    prot_orthogonality(qx, qy, qz, e)
    wx = prot_inv_x(ox, oy, oz, e)
    wy = prot_inv_y(ox, oy, oz, e)
    wz = prot_inv_z(ox, oy, oz, e)
    # The return leg refers between the same anchoring as well, so it introduces
    # no offset either.
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    return rot_to_equ(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)


# ---------------------------------------------------------------------------
# Differential harness.
# ---------------------------------------------------------------------------


def _elementwise_ok(shadow, real, scale):
    """Elementwise agreement: within the scaled tolerance, or both sides
    non-finite (a degenerate input, e.g. the zero-length position, that the real
    library maps to NaN -- the shadow must reproduce that, and it does when both
    are non-finite, but a shadow that produced a NUMBER where the library
    produces NaN, or vice versa, still counts as a disagreement)."""
    sh = np.asarray(shadow, dtype=float)
    re = np.asarray(real, dtype=float)
    both_bad = ~np.isfinite(sh) & ~np.isfinite(re)
    close = np.abs(sh - re) <= 1e-9 * scale + 1e-9
    return close | both_bad


def agree(shadow, real, scale):
    return bool(np.all(_elementwise_ok(shadow, real, scale)))


def first_bad(shadow, real, scale):
    return int(np.argmax(~_elementwise_ok(shadow, real, scale)))


def check_triplet(label, shadow_fn, real_xyz, vx, vy, vz, extra=()):
    """Run shadow_fn(comp, ...) for comp in {0,1,2} against the real
    transform's output components; return an error string on the first
    disagreement, else the number of inputs checked.

    The tolerance is relative to the magnitude of the quantities being
    compared -- the input position AND the transform's own output -- because a
    re-referencing between differing anchorings can move the position by orders
    of magnitude more than its own length (going through the barycentre), and a
    tolerance keyed only to the input would be tighter than the float
    representation of the output allows."""
    finite = [np.asarray(a, dtype=float) for a in (vx, vy, vz)]
    finite += [np.asarray(a, dtype=float) for a in real_xyz]
    mags = [float(np.max(np.abs(a[np.isfinite(a)]))) if np.any(np.isfinite(a))
            else 1.0 for a in finite]
    scale = max([1.0] + mags)
    checked = 0
    for comp in (0, 1, 2):
        sh = shadow_fn(comp, vx, vy, vz, *extra)
        re = real_xyz[comp]
        if not agree(sh, re, scale):
            i = first_bad(sh, re, scale)
            return ("DISAGREEMENT [%s] comp=%d\n"
                    "  input v=(%r, %r, %r)\n  shadow=%r\n  real=%r"
                    % (label, comp, float(vx[i]), float(vy[i]), float(vz[i]),
                       float(np.asarray(sh)[i]), float(np.asarray(re)[i])))
        checked += len(np.atleast_1d(vx))
    return checked


def boundary_vectors():
    return np.array([
        [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [-3.0, 7.0, -11.0],
        [1e9, -2e9, 3e9], [123.0, 456.0, 789.0],
    ])


def make_batch(rng):
    fuzz = rng.uniform(-1e7, 1e7, size=(N_FUZZ_VECTORS, 3))
    batch = np.vstack([boundary_vectors(), fuzz])
    return batch[:, 0], batch[:, 1], batch[:, 2]


def run_config(site, obstime, alt_site, alt_obstime, vx, vy, vz):
    """One configuration: bind the axiomatized callees to the real repo
    machinery, then diff all six modeled functions against the real patched
    frame transforms on the whole batch. BOTH conversion pairs are run against
    FOUR source/target anchoring pairs -- identical, differing site only,
    differing epoch only, differing in both -- so the differing-anchoring domain
    the postconditions pin is actually exercised, not just the same-anchoring
    case the round-trip identities cover."""
    global _MREG, _PMAT, _EPOCH, _LOC, _KIND, _OFF_CACHE
    from astropy import units as u
    from astropy.time import Time
    from astropy.coordinates import (EarthLocation, ITRS, AltAz, HADec, CIRS,
                                     CartesianRepresentation)
    from astropy.coordinates.matrix_utilities import matrix_transpose
    from astropy.coordinates.builtin_frames.itrs_observed_transforms import (
        itrs_to_altaz_mat, itrs_to_hadec_mat)
    from astropy.coordinates.builtin_frames.intermediate_rotation_transforms import (
        cirs_to_itrs_mat)

    lon_d, lat_d, h_m = site
    loc = EarthLocation(lon=lon_d * u.deg, lat=lat_d * u.deg, height=h_m * u.m)
    alon_d, alat_d, ah_m = alt_site
    aloc = EarthLocation(lon=alon_d * u.deg, lat=alat_d * u.deg,
                         height=ah_m * u.m)
    t = Time(obstime)
    at = Time(alt_obstime)
    rep = CartesianRepresentation(vx * u.m, vy * u.m, vz * u.m)
    lx, ly, lz = (float(c.to_value(u.m)) for c in loc.get_itrs().cartesian.xyz)
    tx, ty, tz = (float(c.to_value(u.m)) for c in aloc.get_itrs().cartesian.xyz)

    # Site registry: the site carrier resolves to the real EarthLocation, so
    # both the orientation matrix and the re-referencing transform are built
    # from the site the model call actually names.
    _LOC = {_skey(lx, ly, lz): loc, _skey(tx, ty, tz): aloc}
    # Epoch registry: tag 1 is the source epoch, tag 2 the alternative one.
    # Tag equality is the only thing the model uses, and equal tags denote the
    # same real obstime.
    _EPOCH = {1: t, 2: at}
    _PMAT = {1: (np.asarray(cirs_to_itrs_mat(t)),
                 np.asarray(matrix_transpose(cirs_to_itrs_mat(t)))),
             2: (np.asarray(cirs_to_itrs_mat(at)),
                 np.asarray(matrix_transpose(cirs_to_itrs_mat(at))))}
    _OFF_CACHE = {}

    total = 0
    errs = []

    # (source anchoring is always (L, tag 1); the target anchoring varies)
    variants = [
        ("same-anchoring", (lx, ly, lz), 1),
        ("site-differs", (tx, ty, tz), 1),
        ("epoch-differs", (lx, ly, lz), 2),
        ("both-differ", (tx, ty, tz), 2),
    ]

    # --- direct Earth-fixed <-> observer-centred pair -----------------------
    # The orientation matrix is SITE-INDEXED: one matrix per (kind, site), built
    # from that site's own geodetic coordinates exactly as the gold code does
    # (observed_frame.location forward / observed_coo.location backward).
    # pressure=0 keeps the tested (refraction-free) path. Both directions are
    # driven across all four anchoring variants, so the re-referencing step the
    # gold code performs when the two frames' anchorings differ is exercised.
    _KIND = "itrs"
    for kind in ("altaz", "hadec"):
        _MREG = {}
        for skey, site_loc in _LOC.items():
            slon, slat, _ = site_loc.to_geodetic('WGS84')
            mat = (itrs_to_altaz_mat(slon, slat) if kind == "altaz"
                   else itrs_to_hadec_mat(slon))
            _MREG[skey] = (np.asarray(mat), np.asarray(matrix_transpose(mat)))

        for vname, (gx, gy, gz), etag in variants:
            tgt_loc = _LOC[_skey(gx, gy, gz)]
            tgt_time = _EPOCH[etag]
            obs_tgt = (AltAz(obstime=tgt_time, location=tgt_loc) if kind == "altaz"
                       else HADec(obstime=tgt_time, location=tgt_loc))
            obs_src = (AltAz(obstime=t, location=loc) if kind == "altaz"
                       else HADec(obstime=t, location=loc))

            itrs_in = ITRS(rep, obstime=t, location=loc)
            obs_real = itrs_in.transform_to(
                obs_tgt).cartesian.get_xyz().to_value(u.m)
            r = check_triplet("itrs_to_observed/%s/%s" % (kind, vname),
                              itrs_to_observed, obs_real, vx, vy, vz,
                              extra=(lx, ly, lz, 1, gx, gy, gz, etag))
            if isinstance(r, str):
                errs.append(r)
            else:
                total += r

            obs_in = obs_src.realize_frame(rep)
            back_real = obs_in.transform_to(
                ITRS(obstime=tgt_time,
                     location=tgt_loc)).cartesian.get_xyz().to_value(u.m)
            r = check_triplet("observed_to_itrs/%s/%s" % (kind, vname),
                              observed_to_itrs, back_real, vx, vy, vz,
                              extra=(lx, ly, lz, 1, gx, gy, gz, etag))
            if isinstance(r, str):
                errs.append(r)
            else:
                total += r

        # the direct round trip (identical anchoring on both legs)
        itrs_in = ITRS(rep, obstime=t, location=loc)
        obs_same = (AltAz(obstime=t, location=loc) if kind == "altaz"
                    else HADec(obstime=t, location=loc))
        rt_real = itrs_in.transform_to(obs_same).transform_to(
            ITRS(obstime=t, location=loc)).cartesian.get_xyz().to_value(u.m)
        r = check_triplet("observed_roundtrip/" + kind, observed_roundtrip,
                          rt_real, vx, vy, vz, extra=(lx, ly, lz, 1))
        if isinstance(r, str):
            errs.append(r)
        else:
            total += r

    # --- Earth-equatorial <-> Earth-rotating pair over FOUR anchoring pairs -
    _KIND = "cirs"
    for vname, (gx, gy, gz), etag in variants:
        tgt_loc = _LOC[_skey(gx, gy, gz)]
        tgt_time = _EPOCH[etag]

        cirs_at_L = CIRS(rep, obstime=t, location=loc)
        equ_real = cirs_at_L.transform_to(
            ITRS(obstime=tgt_time,
                 location=tgt_loc)).cartesian.get_xyz().to_value(u.m)
        r = check_triplet("equ_to_rot/" + vname, equ_to_rot, equ_real,
                          vx, vy, vz,
                          extra=(lx, ly, lz, 1, gx, gy, gz, etag))
        if isinstance(r, str):
            errs.append(r)
        else:
            total += r

        itrs_at_L = ITRS(rep, obstime=t, location=loc)
        rot_real = itrs_at_L.transform_to(
            CIRS(obstime=tgt_time,
                 location=tgt_loc)).cartesian.get_xyz().to_value(u.m)
        r = check_triplet("rot_to_equ/" + vname, rot_to_equ, rot_real,
                          vx, vy, vz,
                          extra=(lx, ly, lz, 1, gx, gy, gz, etag))
        if isinstance(r, str):
            errs.append(r)
        else:
            total += r

    # --- the topocentric round trip (identical anchoring on both legs) -----
    cirs_at_L = CIRS(rep, obstime=t, location=loc)
    rt2_real = cirs_at_L.transform_to(ITRS(obstime=t, location=loc)).transform_to(
        CIRS(obstime=t, location=loc)).cartesian.get_xyz().to_value(u.m)
    r = check_triplet("equ_rot_roundtrip", equ_rot_roundtrip, rt2_real,
                      vx, vy, vz, extra=(lx, ly, lz, 1))
    if isinstance(r, str):
        errs.append(r)
    else:
        total += r

    return total, errs


def main():
    from astropy.utils import iers
    iers.conf.auto_download = False   # container is offline; bundled tables

    rng = np.random.RandomState(SEED)

    sites = [
        (0.0, 0.0, 0.0),          # equatorial sea-level boundary site
        (-1.0, 52.0, 10000.0),
        (123.0, -33.0, 500.0),
        (10.0, 80.0, 2000.0),
        (-179.9, -89.0, 0.0),     # near-pole / dateline boundary site
    ]
    obstimes = ["J2000", "J2010", "2014-06-24T15:22:11"]
    # Alternative anchoring (a genuinely different site and a different epoch),
    # so the site carrier and the epoch carrier can each be varied on its own.
    alt_sites = [
        (77.0, -12.0, 1500.0),
        (-70.7, -30.2, 2200.0),
        (139.7, 35.7, 40.0),
    ]
    alt_obstimes = ["J2006", "B1950", "2018-01-02T03:04:05"]

    total = 0
    k = 0
    for site in sites:
        for obstime in obstimes:
            vx, vy, vz = make_batch(rng)
            n, errs = run_config(site, obstime,
                                 alt_sites[k % len(alt_sites)],
                                 alt_obstimes[k % len(alt_obstimes)],
                                 vx, vy, vz)
            k += 1
            if errs:
                print("G-CONF FAIL at site=%r obstime=%r (seed=%d):"
                      % (site, obstime, SEED))
                for e in errs[:5]:
                    print(e)
                return 1
            total += n

    print("G-CONF OK: model.py impl shadow (real-callee bindings per "
          "mapping.md, including the SITE-indexed orientation matrix, the "
          "epoch-indexed Earth-orientation rotation and the position- and "
          "anchoring-dependent re-referencing offset) agrees with the real "
          "patched frame transforms on %d component inputs across %d "
          "configurations, with BOTH conversion pairs driven over 4 "
          "source/target anchoring pairs (identical, site-differs, "
          "epoch-differs, both-differ) (seed=%d), 0 disagreements."
          % (total, len(sites) * len(obstimes), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
