# mapping.md — astropy__astropy-13398

## Symbol binding (file:line @ base_commit 6500928dc0e57be8f06d1162eacc3ba5e2eff692)

The modelled behaviour is the headline new module created by the gold patch:
`astropy/coordinates/builtin_frames/itrs_observed_transforms.py` (new file in the
patch; lines below are patch line numbers within that new file).

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_itrs_to_observed` / `problem_spec_itrs_to_observed` | `itrs_to_observed(itrs_coo, observed_frame)` | itrs_observed_transforms.py:106–125 (patch) |
| `implementation_observed_to_itrs` / `problem_spec_observed_to_itrs` | `observed_to_itrs(observed_coo, itrs_frame)` | itrs_observed_transforms.py:128–145 (patch) |
| `altazMat lon lat` | `itrs_to_altaz_mat(lon, lat)` | :18–26 |
| `hadecMat lon` | `itrs_to_hadec_mat(lon)` | :29–35 |
| `poleTiltMat lat` | `altaz_to_hadec_mat(lat)` | :38–46 |
| `toApparent` | `add_refraction(aa_crepr, observed_frame)` | :49–75 |
| `toGeometric` | `remove_refraction(aa_crepr, observed_frame)` | :78–98 |
| `sinAltFloor` / `cosAltFloor` | `sinAltFloor = 0.05` / `cosAltFloor = 1e-6` | :12–14 |
| `poleAngle` | `NORTH_POLE = 90.0*u.deg` | :16 |
| `rotZ θ` / `rotY θ` | `rotation_matrix(θ,'z')` / `rotation_matrix(θ,'y')` | matrix_utilities.py:40–100 |
| `flipX` | `minus_x` (`np.eye(3); [0][0]=-1`) | :20–21 |
| `flipY` | `minus_y` (`np.eye(3); [1][1]=-1`) | :31–32 |
| `flipXY` | `z180` (`np.eye(3); [0][0]=[1][1]=-1`) | :40–42 |
| `mmul` | `@` on two `(3,3)` arrays (left-associated, as written) | :26, :35, :46 |
| `mvmul` | `CartesianRepresentation.transform(M)` (= `erfa.rxp(M, xyz)`) | :117, :121, :124 etc. |
| `ObsFrame.isAltAz` | `isinstance(frame, AltAz)` | :113, :131 |
| `ObsFrame.pressure/temperature/relHumidity/obswl` | the four `AltAz`/`HADec` atmosphere attributes | :52–55, :81–84 |
| `siteDiffers`, `epochDiffers` | `np.any(itrs_coo.location != observed_frame.location)`, `np.any(itrs_coo.obstime != observed_frame.obstime)` | :108–110 |
| `carryTo` | `ITRS(crepr, obstime=src, location=srcLoc).transform_to(ITRS(obstime=tgt, location=tgtLoc))` | :110–112, :144–145 |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Lean type | Python value | bridge |
|---|---|---|
| `Float` | python `float` / numpy `float64` | **identity** — both are IEEE-754 binary64, and `Float.cos/sin/sqrt`, `+ - * /` and the literals are the same binary64 operations. There is no idealisation step in this bridge. |
| `Vec3 = Fin 3 → Float` | `CartesianRepresentation` → `get_xyz()` ndarray `(3,)` of float64, in metres | `i ↦ xyz[i]` |
| `Mat3 = Matrix (Fin 3) (Fin 3) Float` | numpy `(3,3)` float64 matrix | `M i j ↦ A[i,j]` |
| `mvmul M v` | `crepr.transform(A)` i.e. `erfa.rxp(A, xyz)` | left mat-vec |
| `mmul A B` | `A @ B` | matrix product |
| `Mᵀ` | `matrix_transpose(A)` = `A.T` | transpose |
| `geodetic loc` | `location.to_geodetic('WGS84')` → `(lon, lat, height)` | `.1 = lon`, `.2.1 = lat`, `.2.2 = height`. **The two angles are the values in DEGREES**, i.e. `.value` of the returned `Longitude`/`Latitude`; that is the unit `to_geodetic` natively reports and the unit the real callers hand to `rotation_matrix`, which converts internally. The Lean model therefore multiplies by `angToRad = 0.017453292519943295` (= `π/180` rounded to binary64) and uses `poleAngle = 90.0`, mirroring `NORTH_POLE = 90.0*u.deg`. |
| `bendCoefs p t h wl` | `erfa.refco(p, t, h, wl)` → `(coefA, coefB)` | `.1 = coefA`, `.2 = coefB`; units hPa / °C / fraction / µm |
| `normSplit p` | `erfa.pn(p)` → `(norm, unit)` | `.1 = norm`, `.2 = unit vector` |
| `scaleVec s p` | `erfa.sxp(s, p)` | — |
| `cartToSph uv` | `erfa.c2s(uv)` → `(az, el)` | `.1 = az`, `.2 = el` |
| `sphToCart az el` | `erfa.s2c(az, el)` → unit xyz | — |
| `Location` (opaque) | `EarthLocation` | — |
| `ObsFrame.epoch : Float` | `obstime` (a `Time`) | epoch TAG only; the model never does arithmetic on it, it only asks `epochDiffers` whether two tags are the same tag, mirroring `np.any(a != b)` |

## Callee provenance + flag dependencies

A-reference (deep-modelled changed composition; underlying callee unchanged,
G-AX-probed):
- `geodetic` ← `EarthLocation.to_geodetic('WGS84')` — iterative WGS84 ellipsoid
  inversion (erfa `gc2gd`). Pure, deterministic. No flag dependency beyond the
  fixed `'WGS84'` ellipsoid. **Reports degrees** (G-AX probes this explicitly).
- `siteDiffers` ← `np.any(itrs_coo.location != observed_frame.location)` — the
  module's own element-wise site comparison, reduced to one bool. Note the real
  guard is a disjunction with the analogous obstime comparison; the obstime half
  is modelled transparently as `epochDiffers` because the model carries epochs as
  comparable tags.
- `bendCoefs` ← `erfa.refco(pressure_hPa, temperature_degC, rel_humidity, obswl_micron)`
  — empirical two-term refraction fit. Pure. Only reached when `pressure > 0`.
- `normSplit` ← `erfa.pn` — norm-and-unit-direction split at binary64 precision.
  Called twice inside `add_refraction` (the second call's norm is discarded — the
  ORIGINAL norm is what `sxp` restores) and once inside `remove_refraction`.
- `scaleVec` ← `erfa.sxp` — scalar times 3-vector.
- `cartToSph` / `sphToCart` ← `erfa.c2s` / `erfa.s2c` — spherical⇄Cartesian.
- `carryTo` ← `ITRS(crepr, obstime=srcEpoch, location=srcLoc).transform_to(ITRS(obstime=tgtEpoch, location=tgtLoc))`,
  the indirect Earth-fixed carry. It appears in the patch twice: as the guarded
  pre-step of `itrs_to_observed` (:110–112, reached only when the input's site or
  epoch differs from the frame's) and as the UNGUARDED trailing step of
  `observed_to_itrs` (:144–145). **Its value is a function of both endpoint
  pairs**, not of the source pair alone: the route passes through an inertial
  frame, so a different target site or target epoch yields a different Earth-fixed
  answer. Modelled with all four endpoint arguments explicit
  (`carryTo v srcLoc srcEpoch tgtLoc tgtEpoch`) for exactly that reason; G-AX
  probes both the identity-when-the-pairs-agree claim and the
  depends-on-the-target claim, and the bundled reproduction measures the composed
  functions against the real module at three distinct target sites and two target
  epochs.

Flag dependency: the AltAz-vs-HADec split is `isinstance(frame, AltAz)`, modelled
by `ObsFrame.isAltAz`. The atmosphere split is `frame.pressure > 0.0`, modelled
by `ObsFrame.pressure > 0`. Refraction (`bendCoefs`, `toApparent`/
`toGeometric`) is reached ONLY under `pressure > 0`.

## G-CONF fuzz seed
Pinned seed: **13398**. Inputs fuzzed: vector components in [-2e8, 2e8] m,
`lon ∈ [-180, 180]` **degrees**, `lat ∈ [-90, 90]` **degrees** (the reported
unit), `pressure ∈ [1, 1100]` hPa, `temperature ∈ [-40, 50]` °C,
`relHumidity ∈ [0,1]`, `obswl ∈ [0.3, 25]` µm, refraction directions drawn above
the horizon at norms in [1, 1e3]. ≥1e5 draws, tolerance 1e-12 absolute on the
matrices and `rtol=1e-13, atol=1e-12` on the refraction legs — residual only
because the model accumulates products in explicit index order where numpy's `@`
and `erfa.rxp` are free to reassociate, and because the model spells
`d * d` where the patch spells `d ** 2`.
